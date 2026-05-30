from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
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
    gazebo = IncludeLaunchDescription(
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

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(gazebo)
    return ld
