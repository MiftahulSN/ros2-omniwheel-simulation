import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


class NavSimConfig:
    def __init__(self):
        self.pkg_nav = get_package_share_directory('omni_navigation')
        self.pkg_gazebo = get_package_share_directory('omni_gazebo')
        self.pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    def _get_config_paths(self) -> dict:
        return {
            'nav2_params': os.path.join(self.pkg_nav, 'config', 'nav2_params.yaml'),
            'navigation_rviz': os.path.join(self.pkg_nav, 'rviz', 'navigation.rviz'),
        }


class NavSimNodeFactory:
    def __init__(self, config: NavSimConfig):
        self.config = config

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
                description='Gazebo world name',
            ),
            DeclareLaunchArgument(
                'teleop',
                default_value='auto',
                choices=['auto', 'joy', 'keyboard'],
                description='Teleop mode: auto (detect joystick), joy, or keyboard',
            ),
        ]

    def create_core_nodes(self, context):
        paths = self.config._get_config_paths()

        gazebo_sim = self._create_gazebo_sim()
        delayed_nav2 = self._create_nav2(paths)
        rviz2 = self._create_rviz(paths['navigation_rviz'])

        return [gazebo_sim, delayed_nav2, rviz2]

    def _create_gazebo_sim(self):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    self.config.pkg_gazebo,
                    'launch', 'gazebo.launch.py',
                ])
            ),
            launch_arguments={
                'wheel_config': LaunchConfiguration('wheel_config'),
                'world': LaunchConfiguration('world'),
                'teleop': LaunchConfiguration('teleop'),
            }.items(),
        )

    def _create_nav2(self, paths):
        world = LaunchConfiguration('world')
        map_path = [PathJoinSubstitution([self.config.pkg_nav, 'maps', world]), '.yaml']

        nav2_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    self.config.pkg_nav2_bringup,
                    'launch', 'bringup_launch.py',
                ])
            ),
            launch_arguments={
                'map': map_path,
                'params_file': paths['nav2_params'],
                'use_sim_time': 'true',
            }.items(),
        )

        return TimerAction(period=5.0, actions=[nav2_launch])

    def _create_rviz(self, rviz_config):
        return Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': True}],
        )


def generate_launch_description():
    config = NavSimConfig()
    factory = NavSimNodeFactory(config)

    launch_entities = list(factory.create_launch_arguments())
    launch_entities.append(
        OpaqueFunction(function=factory.create_core_nodes))
    return LaunchDescription(launch_entities)
