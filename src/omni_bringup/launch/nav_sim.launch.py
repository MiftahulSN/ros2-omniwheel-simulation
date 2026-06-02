import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


ARGUMENTS = [
    DeclareLaunchArgument(
        'wheel_config',
        default_value='3wheel',
        choices=['3wheel', '4wheel'],
        description='Wheel configuration',
    ),
    DeclareLaunchArgument(
        'world',
        default_value='maze2',
        description='Gazebo world name',
    ),
]


def generate_launch_description():
    pkg_nav = get_package_share_directory('omni_navigation')

    gazebo_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                get_package_share_directory('omni_gazebo'),
                'launch', 'gazebo.launch.py',
            ])
        ),
        launch_arguments={
            'wheel_config': LaunchConfiguration('wheel_config'),
            'world': LaunchConfiguration('world'),
        }.items(),
    )

    world = LaunchConfiguration('world')
    map_path = [PathJoinSubstitution([pkg_nav, 'maps', world]), '.yaml']
    param_file_path = os.path.join(pkg_nav, 'config', 'nav2_params.yaml')

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                get_package_share_directory('nav2_bringup'),
                'launch', 'bringup_launch.py',
            ])
        ),
        launch_arguments={
            'map': map_path,
            'params_file': param_file_path,
            'use_sim_time': 'true',
        }.items(),
    )

    delayed_nav2 = TimerAction(
        period=5.0,
        actions=[nav2_launch],
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=[
            '-d',
            PathJoinSubstitution([pkg_nav, 'rviz', 'navigation.rviz']),
        ],
        parameters=[{'use_sim_time': True}],
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(gazebo_sim)
    ld.add_action(delayed_nav2)
    ld.add_action(rviz2)
    return ld
