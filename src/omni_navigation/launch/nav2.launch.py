import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


ARGUMENTS = [
    DeclareLaunchArgument(
        'world',
        default_value='maze2',
        description='Gazebo World',
    ),
]


def generate_launch_description():
    pkg_nav = get_package_share_directory('omni_navigation')

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

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(nav2_launch)
    return ld
