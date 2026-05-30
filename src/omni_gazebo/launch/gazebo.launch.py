import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from pathlib import Path


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
        description='Gazebo world name (without .sdf)',
    ),
]


def launch_setup(context, *args, **kwargs):
    wheel_config = context.launch_configurations['wheel_config']
    world_name = context.launch_configurations['world']

    pkg_description = get_package_share_directory('omni_description')
    pkg_gazebo = get_package_share_directory('omni_gazebo')
    pkg_controller = get_package_share_directory('omni_controller')

    ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=str(Path(pkg_description).parent.resolve()),
    )

    xacro_file = os.path.join(pkg_description, 'urdf', wheel_config, 'robot.urdf.xacro')
    robot_description_content = Command(['xacro ', xacro_file])

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': True,
        }],
        output='screen',
    )

    world_file = os.path.join(pkg_gazebo, 'worlds', f'{world_name}.sdf')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments=[
            ('gz_args', [world_file, ' -r', ' -v 4']),
        ],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'omni_robot',
            '-z', '0.1',
        ],
        output='screen',
    )

    bridge_config = os.path.join(pkg_gazebo, 'config', 'bridge.yaml')
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p', f'config_file:={bridge_config}',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    wheel_count = 3 if wheel_config == '3wheel' else 4

    spawner_args = ['joint_state_broadcaster']
    for i in range(1, wheel_count + 1):
        spawner_args.append(f'wheel{i}_controller')
    spawner_args.extend(['--controller-manager', '/controller_manager'])

    controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=spawner_args,
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    kinematics = Node(
        package='omni_controller',
        executable='kinematics',
        parameters=[{'use_sim_time': True}],
        additional_env={'OMNI_ROBOT_MODEL': wheel_config},
        output='screen',
    )

    return [
        ign_resource_path,
        robot_state_publisher,
        gazebo,
        spawn_robot,
        ros_gz_bridge,
        controller_spawner,
        kinematics,
    ]


def generate_launch_description():
    return LaunchDescription(ARGUMENTS + [OpaqueFunction(function=launch_setup)])
