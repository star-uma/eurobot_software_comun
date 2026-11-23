import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_xbox = get_package_share_directory('eurobot_software_xbox')

    # En simulación el nodo debe usar el reloj de /clock; en el robot real
    # se lanza con use_sim_time:=false.
    use_sim_time = LaunchConfiguration('use_sim_time')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Usar /clock (simulación) en lugar del reloj del sistema'
    )

    # Driver del mando Xbox: publica los datos crudos en /joy
    # Nota: usa el paquete 'joy'. Si tu sistema usa 'joy_linux',
    # cambia package='joy', executable='joy_node' por
    # package='joy_linux', executable='joy_linux_node'.
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[{
            'dev': '/dev/input/js0',
            'deadzone': 0.05,
            'autorepeat_rate': 20.0,
        }]
    )

    # Nodo de control por mando Xbox: lee /joy y publica /cmd_vel
    xbox_teleop_node = Node(
        package='eurobot_software_xbox',
        executable='xbox_teleop_node',
        name='xbox_teleop_node',
        output='screen',
        parameters=[
            os.path.join(pkg_xbox, 'config', 'joy_teleop.yaml'),
            {'use_sim_time': use_sim_time},
        ]
    )

    return LaunchDescription([
        declare_use_sim_time,
        joy_node,
        xbox_teleop_node
    ])