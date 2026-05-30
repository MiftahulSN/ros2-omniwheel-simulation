import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('omni_description')
    wheel_config = context.launch_configurations['wheel_config']

    xacro_file = os.path.join(pkg_share, 'urdf', wheel_config, 'robot.urdf.xacro')
    rviz_config = os.path.join(pkg_share, 'rviz', 'description.rviz')

    robot_description_content = Command(['xacro ', xacro_file])

    return [
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description_content}],
            output='screen',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            condition=IfCondition(LaunchConfiguration('rviz')),
            output='screen',
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'wheel_config',
            default_value='3wheel',
            choices=['3wheel', '4wheel'],
            description='Wheel configuration',
        ),
        DeclareLaunchArgument(
            'rviz',
            default_value='true',
            description='Launch RViz2',
        ),
        OpaqueFunction(function=launch_setup),
    ])
