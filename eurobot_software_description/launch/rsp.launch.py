import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue  # <-- IMPORTANTE: Importar esta clase

def generate_launch_description():
    use_sim = LaunchConfiguration('use_sim')
    use_sim_time = LaunchConfiguration('use_sim_time')
    controllers_yaml = LaunchConfiguration('controllers_yaml')

    pkg_description = get_package_share_directory('eurobot_software_description')
    xacro_file = os.path.join(pkg_description, 'urdf', 'robot.urdf.xacro')

    # Convertir explícitamente el XML de xacro a un string de parámetros
    robot_description_config = ParameterValue(
        Command([
            'xacro ', xacro_file,
            ' use_sim:=', use_sim,
            ' controllers_yaml:=', controllers_yaml
        ]),
        value_type=str
    )

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_config,
            'use_sim_time': use_sim_time
        }]
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('controllers_yaml', default_value=os.path.join(pkg_description, 'config', 'controllers.yaml')),
        node_robot_state_publisher
    ])