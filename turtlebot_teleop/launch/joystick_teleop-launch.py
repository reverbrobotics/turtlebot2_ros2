"""Joystick teleop for the TurtleBot.

The ROS 2 equivalent of ROS 1's turtlebot_teleop logitech.launch /
ps3_teleop.launch / xbox360_teleop.launch, in one file:

  ros2 launch turtlebot_teleop joystick_teleop-launch.py                  # PDP pad
  ros2 launch turtlebot_teleop joystick_teleop-launch.py joy_config:=ps3  # or xbox, ps5, ...

Runs joy_node + teleop_twist_joy (via teleop_twist_joy's teleop-launch.py)
into cmd_vel_mux's input/teleop. joy_config:=<name> picks
config/<name>.config.yaml from this package if it has one (pdp: hold LB to
drive, RB for turbo), otherwise teleop_twist_joy's own config of that name
(ps3, ps5, xbox, atk3, xd3, ...).
"""

import os

import ament_index_python.packages
import launch
import launch.actions
import launch.launch_description_sources
import launch.substitutions


def include_teleop(context):
    teleop_share = ament_index_python.packages.get_package_share_directory('turtlebot_teleop')
    joy_share = ament_index_python.packages.get_package_share_directory('teleop_twist_joy')

    joy_config = launch.substitutions.LaunchConfiguration('joy_config').perform(context)
    config_filepath = os.path.join(teleop_share, 'config', joy_config + '.config.yaml')
    if not os.path.exists(config_filepath):
        config_filepath = os.path.join(joy_share, 'config', joy_config + '.config.yaml')

    return [launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(joy_share, 'launch', 'teleop-launch.py')),
        launch_arguments={
            'config_filepath': config_filepath,
            'joy_dev': launch.substitutions.LaunchConfiguration('joy_dev'),
            # cmd_vel_mux only accepts plain Twist; teleop_twist_joy's
            # publish_stamped_twist is left at its default of false.
            'joy_vel': '/input/teleop',
        }.items())]


def generate_launch_description():
    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'joy_config', default_value='pdp',
            description='Joystick config name (pdp, ps3, ps5, xbox, ...)'),
        launch.actions.DeclareLaunchArgument(
            'joy_dev', default_value='0',
            description='Joystick device index'),
        launch.actions.OpaqueFunction(function=include_teleop),
    ])
