"""Navigate in a saved map, all on the robot.

The ROS 2 equivalent of ROS 1's `roslaunch turtlebot_navigation
amcl_demo.launch map_file:=...`: the 3D sensor, map_server, AMCL and Nav2.
Run it on the robot after minimal-launch.py:

  ros2 launch turtlebot_bringup minimal-launch.py
  ros2 launch turtlebot_navigation amcl_demo-launch.py map:=$HOME/maps/my_map.yaml

and on the workstation:

  ros2 launch turtlebot_rviz_launchers view_navigation-launch.py

then give AMCL the robot's pose with "2D Pose Estimate" and send goals with
"Nav2 Goal".

Arguments:
  map:=<file.yaml>   the map to navigate in (required)
  3d_sensor:=false   don't start the camera (if 3dsensor-launch.py runs separately)
"""

import os

import ament_index_python.packages
import launch
import launch.actions
import launch.conditions
import launch.launch_description_sources
import launch.substitutions


def generate_launch_description():
    bringup_share = ament_index_python.packages.get_package_share_directory('turtlebot_bringup')
    navigation_share = ament_index_python.packages.get_package_share_directory('turtlebot_navigation')

    three_d_sensor_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', '3dsensor-launch.py')),
        condition=launch.conditions.IfCondition(launch.substitutions.LaunchConfiguration('3d_sensor')))

    navigation_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(navigation_share, 'launch', 'navigation-launch.py')),
        launch_arguments={'map': launch.substitutions.LaunchConfiguration('map')}.items())

    return launch.LaunchDescription([
        # No default: without a map there is nothing for AMCL to localize in
        # (use slam_demo-launch.py to build one), so launch refuses to start.
        launch.actions.DeclareLaunchArgument(
            'map',
            description='Full path to the map yaml to navigate in, e.g. ~/maps/my_map.yaml'),
        launch.actions.DeclareLaunchArgument(
            '3d_sensor', default_value='true',
            description='Start the depth camera and laser scan (3dsensor-launch.py)'),
        three_d_sensor_launch,
        navigation_launch,
    ])
