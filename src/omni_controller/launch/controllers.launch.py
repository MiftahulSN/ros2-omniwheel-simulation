import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from controller_manager.launch_utils import generate_controllers_spawner_launch_description


class ControllerConfig:
    def __init__(self):
        self.pkg_share = get_package_share_directory('omni_controller')

    def _get_config_paths(self) -> dict:
        return {
            '3wheel': os.path.join(self.pkg_share, 'config', '3wheel.yaml'),
            '4wheel': os.path.join(self.pkg_share, 'config', '4wheel.yaml'),
        }


class ControllerNodeFactory:
    def __init__(self, config: ControllerConfig):
        self.config = config

    def create_launch_arguments(self):
        return [
            DeclareLaunchArgument(
                'wheel_config',
                default_value='3wheel',
                choices=['3wheel', '4wheel'],
                description='Wheel configuration',
            ),
        ]

    def create_core_nodes(self, context):
        wheel_config = context.launch_configurations['wheel_config']
        paths = self.config._get_config_paths()

        wheel_count = 3 if wheel_config == '3wheel' else 4
        controller_names = ['joint_state_broadcaster']
        for i in range(1, wheel_count + 1):
            controller_names.append(f'wheel{i}_controller')

        spawner_actions = generate_controllers_spawner_launch_description(
            controller_names=controller_names,
            controller_params_files=[paths[wheel_config]],
        )

        return [action for action in spawner_actions]


def generate_launch_description():
    config = ControllerConfig()
    factory = ControllerNodeFactory(config)

    launch_entities = list(factory.create_launch_arguments())
    launch_entities.append(
        OpaqueFunction(function=factory.create_core_nodes))
    return LaunchDescription(launch_entities)
