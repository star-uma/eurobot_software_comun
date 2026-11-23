import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy, JointState
from geometry_msgs.msg import Twist
from builtin_interfaces.msg import Duration, Time
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class XboxTeleopNode(Node):
    """Nodo de teleoperación por mando Xbox para Eurobot 2027.

    Lee los mensajes del topic /joy (producido por el nodo joy de ROS 2)
    y publica:
      - /cmd_vel (geometry_msgs/Twist) para el controlador diferencial diff_cont.
      - /actuator_cont/joint_trajectory (trajectory_msgs/JointTrajectory) para
        subir/bajar el elevator_joint del actuador con la flecha del mando.

    Mapeo del mando Xbox (según config/joy_teleop.yaml):
      - Botón RB (índice 7): habilitador de seguridad (enable_button).
      - Eje Y del joystick izquierdo (índice 1): velocidad lineal (adelante/atrás).
      - Eje X del joystick izquierdo (índice 0): velocidad angular (giro).
      - Flecha arriba/abajo (eje 7): subir/bajar el actuador prismático.
    """

    def __init__(self):
        super().__init__('xbox_teleop_node')
        
        # ############################################
        # ################ Parámetros ################
        # ############################################
        
        # Movimiento del robot
        self.declare_parameter('require_enable_button', True)
        self.declare_parameter('enable_button', 7)
        self.declare_parameter('axis_linear_x', 1)
        self.declare_parameter('scale_linear_x', 0.5)
        self.declare_parameter('axis_angular_yaw', 0)
        self.declare_parameter('scale_angular_yaw', 1.0)

        # Actuador (elevator_joint)
        self.declare_parameter('actuator_axis', 7)
        self.declare_parameter('actuator_velocity', 0.1)
        self.declare_parameter('actuator_min', 0.0)
        self.declare_parameter('actuator_max', 0.38)
        self.declare_parameter('actuator_deadzone', 0.5)
        self.declare_parameter('actuator_rate', 20.0)

        # Movimiento del robot
        self.require_enable_button = self.get_parameter(
            'require_enable_button').get_parameter_value().bool_value
        self.enable_button = self.get_parameter(
            'enable_button').get_parameter_value().integer_value
        self.axis_linear_x = self.get_parameter(
            'axis_linear_x').get_parameter_value().integer_value
        self.scale_linear_x = self.get_parameter(
            'scale_linear_x').get_parameter_value().double_value
        self.axis_angular_yaw = self.get_parameter(
            'axis_angular_yaw').get_parameter_value().integer_value
        self.scale_angular_yaw = self.get_parameter(
            'scale_angular_yaw').get_parameter_value().double_value

        # Actuador
        self.actuator_axis = self.get_parameter(
            'actuator_axis').get_parameter_value().integer_value
        self.actuator_velocity = self.get_parameter(
            'actuator_velocity').get_parameter_value().double_value
        self.actuator_min = self.get_parameter(
            'actuator_min').get_parameter_value().double_value
        self.actuator_max = self.get_parameter(
            'actuator_max').get_parameter_value().double_value
        self.actuator_deadzone = self.get_parameter(
            'actuator_deadzone').get_parameter_value().double_value
        self.actuator_rate = self.get_parameter(
            'actuator_rate').get_parameter_value().double_value

        # #############################################################
        # ################ Publicadores / suscriptores ################
        # #############################################################


        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10
        )
        self.publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # Actuador: trayectoria de posición para actuator_cont
        self.actuator_pub = self.create_publisher(
            JointTrajectory,
            '/actuator_cont/joint_trajectory',
            10
        )
        self.trajectory_msg = JointTrajectory()
        self.trajectory_msg.joint_names = ['elevator_joint']
        point = JointTrajectoryPoint()
        point.time_from_start = Duration(sec=0, nanosec=100_000_000)
        point.positions = [0.0]
        self.trajectory_msg.points = [point]

        # Estado del actuador
        self.actuator_input = 0.0
        self.elevator_target = 0.0
        self.elevator_initialized = False
        self.last_published_target = None

        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        self.actuator_timer = self.create_timer(
            1.0 / self.actuator_rate,
            self.actuator_timer_callback
        )

        self.get_logger().info(
            "Nodo de control Xbox iniciado. "
            f"Botón habilitador: {self.enable_button}, "
            f"Eje lineal: {self.axis_linear_x}, Eje angular: {self.axis_angular_yaw}, "
            f"Eje actuador: {self.actuator_axis}"
        )

    def joy_callback(self, msg: Joy):
        twist = Twist()

        # Leer eje del actuador (flecha arriba/abajo)
        if self.actuator_axis < len(msg.axes):
            self.actuator_input = msg.axes[self.actuator_axis]
        else:
            self.actuator_input = 0.0

        # Si se requiere botón de habilitación y no está presionado, no mover el robot
        if self.require_enable_button:
            if self.enable_button >= len(msg.buttons) or not msg.buttons[self.enable_button]:
                twist.linear.x = 0.0
                twist.angular.z = 0.0
                self.publisher.publish(twist)
                return

        # Leer ejes del joystick con protección contra índices fuera de rango
        linear = 0.0
        angular = 0.0

        if self.axis_linear_x < len(msg.axes):
            linear = msg.axes[self.axis_linear_x] * self.scale_linear_x
        if self.axis_angular_yaw < len(msg.axes):
            angular = msg.axes[self.axis_angular_yaw] * self.scale_angular_yaw

        twist.linear.x = linear
        twist.angular.z = angular

        self.publisher.publish(twist)

    def joint_state_callback(self, msg: JointState):
        """Inicializa el objetivo del actuador en la posición actual."""
        if self.elevator_initialized:
            return
        if 'elevator_joint' in msg.name:
            idx = msg.name.index('elevator_joint')
            self.elevator_target = msg.position[idx]
            self.last_published_target = self.elevator_target
            self.elevator_initialized = True
            self.get_logger().info(
                f"Actuador inicializado en {self.elevator_target:.3f} m"
            )

    def actuator_timer_callback(self):
        """Integra la flecha del mando y publica el objetivo del actuador."""
        if not self.elevator_initialized:
            return

        dt = 1.0 / self.actuator_rate

        if abs(self.actuator_input) >= self.actuator_deadzone:
            self.elevator_target += self.actuator_input * self.actuator_velocity * dt
            self.elevator_target = max(
                self.actuator_min,
                min(self.actuator_max, self.elevator_target)
            )

        if (self.last_published_target is None or
                abs(self.elevator_target - self.last_published_target) > 1e-6):
            # Sello en cero: el JointTrajectoryController lo interpreta como
            # "empieza ahora". Así no depende de que el reloj del nodo (pared)
            # coincida con el del controlador (simulación / /clock).
            self.trajectory_msg.header.stamp = Time(sec=0, nanosec=0)
            self.trajectory_msg.points[0].positions = [self.elevator_target]
            self.actuator_pub.publish(self.trajectory_msg)
            self.last_published_target = self.elevator_target


def main(args=None):
    rclpy.init(args=args)
    node = XboxTeleopNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
