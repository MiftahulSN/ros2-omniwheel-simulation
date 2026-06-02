from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
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

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                get_package_share_directory('slam_toolbox'),
                'launch', 'online_async_launch.py',
            ])
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'slam_params_file': PathJoinSubstitution([
                pkg_nav, 'config', 'slam_params.yaml',
            ]),
        }.items(),
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=[
            '-d',
            PathJoinSubstitution([pkg_nav, 'rviz', 'slam.rviz']),
        ],
        parameters=[{'use_sim_time': True}],
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(gazebo_sim)
    ld.add_action(slam_launch)
    ld.add_action(rviz2)
    return ld
