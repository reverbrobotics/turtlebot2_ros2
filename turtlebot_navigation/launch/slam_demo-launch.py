"""Map with slam_toolbox and navigate at the same time, all on the robot.

The ROS 2 equivalent of ROS 1's `roslaunch turtlebot_navigation
gmapping_demo.launch`, which likewise started the 3D sensor, the SLAM node and
move_base together. Run it on the robot after minimal-launch.py:

  ros2 launch turtlebot_bringup minimal-launch.py
  ros2 launch turtlebot_navigation slam_demo-launch.py

and on the workstation:

  ros2 launch turtlebot_rviz_launchers view_navigation-launch.py
  ros2 run turtlebot_teleop keyboard_teleop

Drive around with teleop (or send "Nav2 Goal"s inside the explored area), then
save the map from either machine:

  ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map

Arguments:
  navigation:=false  only map (slam_toolbox without Nav2), for a lighter load
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

    navigation = launch.substitutions.LaunchConfiguration('navigation')

    three_d_sensor_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', '3dsensor-launch.py')),
        condition=launch.conditions.IfCondition(launch.substitutions.LaunchConfiguration('3d_sensor')))

    # navigation-launch.py slam:=true runs slam_toolbox in place of
    # map_server + AMCL, alongside the Nav2 servers.
    slam_navigation_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(navigation_share, 'launch', 'navigation-launch.py')),
        launch_arguments={'slam': 'true'}.items(),
        condition=launch.conditions.IfCondition(navigation))

    slam_only_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(navigation_share, 'launch', 'slam-launch.py')),
        condition=launch.conditions.UnlessCondition(navigation))

    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'navigation', default_value='true',
            description='Also run Nav2, so goals can be sent while mapping'),
        launch.actions.DeclareLaunchArgument(
            '3d_sensor', default_value='true',
            description='Start the depth camera and laser scan (3dsensor-launch.py)'),
        three_d_sensor_launch,
        slam_navigation_launch,
        slam_only_launch,
    ])
