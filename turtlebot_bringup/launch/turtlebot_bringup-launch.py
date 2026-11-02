"""Bring up a Kobuki-based TurtleBot 2 the way ROS 1's turtlebot_bringup did.

Starts the base driver (kobuki_node), the cmd_vel multiplexer, the safety
controller and the velocity smoother, and wires them together. Also starts
robot_state_publisher with the TurtleBot URDF (turtlebot_description), so the
base_footprint -> base_link -> camera_* frames that SLAM and navigation need
are on /tf_static; kobuki_node itself provides odom -> base_footprint and the
wheel joint_states.

  teleop / nav (input/teleop, input/navigation, ...)
        |
        v
  cmd_vel_mux --(cmd_vel)--> velocity_smoother --(commands/velocity)--> kobuki_node
        ^                          ^
        |                          |
  safety_controller ---------------+--(feedback/cmd_vel, self-loop)
  (input/safety)         (commands/velocity is also read back as feedback)

To drive the robot with teleop_twist_keyboard, remap its output topic to
the mux's teleop input:

  ros2 run teleop_twist_keyboard teleop_twist_keyboard \
      --ros-args -r cmd_vel:=/input/teleop

The depth camera / laser scan is started separately by 3dsensor-launch.py.
"""

import os

import ament_index_python.packages
import launch
import launch.actions
import launch.launch_description_sources
import launch_ros.actions

import xacro
import yaml


def generate_launch_description():
    kobuki_node_share = ament_index_python.packages.get_package_share_directory('kobuki_node')
    bringup_share = ament_index_python.packages.get_package_share_directory('turtlebot_bringup')
    smoother_share = ament_index_python.packages.get_package_share_directory('kobuki_velocity_smoother')
    safety_share = ament_index_python.packages.get_package_share_directory('kobuki_safety_controller')
    description_share = ament_index_python.packages.get_package_share_directory('turtlebot_description')

    # Base driver: unchanged, its default topics (commands/velocity, odom)
    # are exactly what the smoother is wired up to use below.
    kobuki_node_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(kobuki_node_share, 'launch', 'kobuki_node-launch.py')))

    # cmd_vel multiplexer: arbitrates between teleop/nav/safety sources and
    # publishes the winner on "cmd_vel".
    with open(os.path.join(bringup_share, 'config', 'cmd_vel_mux_params.yaml'), 'r') as f:
        mux_params = yaml.safe_load(f)['cmd_vel_mux']['ros__parameters']
    cmd_vel_mux_node = launch_ros.actions.Node(
        package='cmd_vel_mux',
        executable='cmd_vel_mux_node',
        output='both',
        parameters=[mux_params])

    # Safety controller: stops the robot on bumper/cliff/wheel-drop events.
    # Its events/* subscriptions already match kobuki_node's topic names, so
    # only its cmd_vel output needs remapping, into the mux's top-priority input.
    with open(os.path.join(safety_share, 'config', 'safety_controller_params.yaml'), 'r') as f:
        safety_params = yaml.safe_load(f)['kobuki_safety_controller_node']['ros__parameters']
    safety_controller_node = launch_ros.actions.Node(
        package='kobuki_safety_controller',
        executable='kobuki_safety_controller_node',
        output='both',
        parameters=[safety_params],
        remappings=[
            ('cmd_vel', '/input/safety'),
        ])

    # Velocity smoother: takes the mux's output, bounds velocity/acceleration,
    # and publishes onto the base driver's command topic. Its feedback input
    # is remapped to that same command topic, so it knows what was actually
    # last commanded (feedback: 2 in velocity_smoother_params.yaml).
    with open(os.path.join(smoother_share, 'config', 'velocity_smoother_params.yaml'), 'r') as f:
        smoother_params = yaml.safe_load(f)['kobuki_velocity_smoother']['ros__parameters']
    velocity_smoother_node = launch_ros.actions.Node(
        package='kobuki_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='both',
        parameters=[smoother_params],
        remappings=[
            ('~/input', '/cmd_vel'),
            ('~/feedback/cmd_vel', '/commands/velocity'),
            ('~/feedback/odometry', '/odom'),
            ('~/smoothed', '/commands/velocity'),
        ])

    # Robot model: publishes the static frames of the base and camera mount,
    # and the wheel frames from kobuki_node's joint_states. Edit the camera_*
    # defaults in turtlebot.urdf.xacro if your camera is mounted differently.
    robot_description = xacro.process_file(
        os.path.join(description_share, 'urdf', 'turtlebot.urdf.xacro')).toxml()
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': robot_description}])

    return launch.LaunchDescription([
        kobuki_node_launch,
        robot_state_publisher_node,
        cmd_vel_mux_node,
        safety_controller_node,
        velocity_smoother_node,
    ])
