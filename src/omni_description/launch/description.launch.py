import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


class DescriptionConfig:
    def __init__(self):
        self.pkg_share = get_package_share_directory('omni_description')

    def _get_config_paths(self) -> dict:
        return {
            'rviz': os.path.join(self.pkg_share, 'rviz', 'description.rviz'),
        }


class DescriptionNodeFactory:
    def __init__(self, config: DescriptionConfig):
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
                'rviz',
                default_value='true',
                description='Launch RViz2',
            ),
        ]

    def create_core_nodes(self, context):
        wheel_config = context.launch_configurations['wheel_config']
        paths = self.config._get_config_paths()

        xacro_file = os.path.join(
            self.config.pkg_share, 'urdf', wheel_config, 'robot.urdf.xacro')

        robot_state_publisher = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': self._load_urdf_content(xacro_file),
            }],
            output='screen',
        )

        rviz2 = Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', paths['rviz']],
            condition=IfCondition(LaunchConfiguration('rviz')),
            output='screen',
        )

        return [robot_state_publisher, rviz2]


def generate_launch_description():
    config = DescriptionConfig()
    factory = DescriptionNodeFactory(config)

    launch_entities = list(factory.create_launch_arguments())
    launch_entities.append(
        OpaqueFunction(function=factory.create_core_nodes))
    return LaunchDescription(launch_entities)
