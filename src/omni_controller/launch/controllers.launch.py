import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from controller_manager.launch_utils import generate_controllers_spawner_launch_description


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('omni_controller')
    wheel_config = context.launch_configurations['wheel_config']

    controller_config = os.path.join(pkg_share, 'config', f'{wheel_config}.yaml')

    wheel_count = 3 if wheel_config == '3wheel' else 4

    controller_names = ['joint_state_broadcaster']
    for i in range(1, wheel_count + 1):
        controller_names.append(f'wheel{i}_controller')

    spawner_actions = generate_controllers_spawner_launch_description(
        controller_names=controller_names,
        controller_params_files=[controller_config],
    )

    return [action for action in spawner_actions]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'wheel_config',
            default_value='3wheel',
            choices=['3wheel', '4wheel'],
            description='Wheel configuration',
        ),
        OpaqueFunction(function=launch_setup),
    ])
