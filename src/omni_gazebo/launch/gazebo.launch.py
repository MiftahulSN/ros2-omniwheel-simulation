import os
import re
import subprocess
from pathlib import Path

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


class GazeboConfig:
    def __init__(self):
        self.pkg_description = get_package_share_directory('omni_description')
        self.pkg_gazebo = get_package_share_directory('omni_gazebo')
        self.pkg_controller = get_package_share_directory('omni_controller')
        self.pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    def _get_config_paths(self) -> dict:
        return {
            'bridge': os.path.join(self.pkg_gazebo, 'config', 'bridge.yaml'),
        }

    def get_world_file(self, world_name: str) -> str:
        return os.path.join(self.pkg_gazebo, 'worlds', f'{world_name}.sdf')

    def get_xacro_file(self, wheel_config: str) -> str:
        return os.path.join(
            self.pkg_description, 'urdf', wheel_config, 'robot.urdf.xacro')

    @staticmethod
    def parse_sdf_world_name(world_file: str) -> str:
        with open(world_file, 'r') as f:
            match = re.search(r'<world\s+name\s*=\s*["\']([^"\']+)["\']', f.read())
        return match.group(1) if match else os.path.splitext(os.path.basename(world_file))[0]


class GazeboNodeFactory:
    def __init__(self, config: GazeboConfig):
        self.config = config

    def _load_urdf_content(self, urdf_path: str) -> str:
        return Command(['xacro ', urdf_path])

    def create_launch_arguments(self):
        return [
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
            DeclareLaunchArgument(
                'teleop',
                default_value='auto',
                choices=['auto', 'joy', 'keyboard'],
                description='Teleop mode: auto (detect joystick), joy, or keyboard',
            ),
        ]

    def create_core_nodes(self, context):
        wheel_config = context.launch_configurations['wheel_config']
        world_name = context.launch_configurations['world']
        paths = self.config._get_config_paths()

        world_file = self.config.get_world_file(world_name)
        sdf_world = self.config.parse_sdf_world_name(world_file)

        nodes = []
        nodes.append(self._create_env_setup())
        nodes.append(self._create_robot_state_publisher(wheel_config))
        nodes.append(self._create_gazebo(world_file))
        nodes.append(self._create_spawn_robot())
        nodes.append(self._create_bridge(paths['bridge']))
        nodes.append(self._create_controller_spawner(wheel_config))
        nodes.append(self._create_kinematics(wheel_config))
        nodes.extend(self._create_teleop_nodes(context, sdf_world))
        return nodes

    def _create_env_setup(self):
        return SetEnvironmentVariable(
            name='IGN_GAZEBO_RESOURCE_PATH',
            value=str(Path(self.config.pkg_description).parent.resolve()),
        )

    def _create_robot_state_publisher(self, wheel_config):
        xacro_file = self.config.get_xacro_file(wheel_config)
        return Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': self._load_urdf_content(xacro_file),
                'use_sim_time': True,
            }],
            output='screen',
        )

    def _create_gazebo(self, world_file):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(self.config.pkg_ros_gz_sim,
                             'launch', 'gz_sim.launch.py')),
            launch_arguments=[
                ('gz_args', [world_file, ' -r', ' -v 4']),
            ],
        )

    def _create_spawn_robot(self):
        return Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-topic', 'robot_description',
                '-name', 'omni_robot',
                '-z', '0.1',
            ],
            output='screen',
        )

    def _create_bridge(self, bridge_config):
        return Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '--ros-args',
                '-p', f'config_file:={bridge_config}',
            ],
            parameters=[{'use_sim_time': True}],
            output='screen',
        )

    def _create_controller_spawner(self, wheel_config):
        wheel_count = 3 if wheel_config == '3wheel' else 4
        args = ['joint_state_broadcaster']
        for i in range(1, wheel_count + 1):
            args.append(f'wheel{i}_controller')
        args.extend(['--controller-manager', '/controller_manager'])

        return Node(
            package='controller_manager',
            executable='spawner',
            arguments=args,
            parameters=[{'use_sim_time': True}],
            output='screen',
        )

    def _create_kinematics(self, wheel_config):
        return Node(
            package='omni_controller',
            executable='kinematics',
            parameters=[{'use_sim_time': True}],
            additional_env={'OMNI_ROBOT_MODEL': wheel_config},
            output='screen',
        )

    def _create_teleop_nodes(self, context, world_name):
        teleop_arg = context.launch_configurations.get('teleop', 'auto')

        if teleop_arg == 'auto':
            use_joy = self._joystick_detected()
        elif teleop_arg == 'joy':
            use_joy = True
        else:
            use_joy = False

        if use_joy:
            return [
                Node(
                    package='joy',
                    executable='joy_node',
                    parameters=[{'use_sim_time': True}],
                    output='screen',
                ),
                Node(
                    package='omni_controller',
                    executable='teleop_joy.py',
                    parameters=[{'use_sim_time': True, 'world': world_name}],
                    output='screen',
                ),
            ]
        else:
            return [
                Node(
                    package='omni_controller',
                    executable='teleop_keyboard.py',
                    parameters=[{'use_sim_time': True}],
                    output='screen',
                ),
            ]

    @staticmethod
    def _joystick_detected():
        try:
            result = subprocess.run(
                ['/opt/ros/humble/lib/joy/joy_enumerate_devices'],
                capture_output=True, text=True, timeout=5,
            )
            lines = [l for l in result.stdout.strip().splitlines()
                     if l.strip() and 'GUID' not in l and '---' not in l]
            return len(lines) > 0
        except Exception:
            return False


def generate_launch_description():
    config = GazeboConfig()
    factory = GazeboNodeFactory(config)

    launch_entities = list(factory.create_launch_arguments())
    launch_entities.append(
        OpaqueFunction(function=factory.create_core_nodes))
    return LaunchDescription(launch_entities)
