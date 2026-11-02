"""Build a map with slam_toolbox, the ROS 2 equivalent of ROS 1's gmapping_demo.

Needs the robot running turtlebot_bringup-launch.py and 3dsensor-launch.py
(for odom -> base_footprint, the camera frames and /scan). Can run on the
robot or on a workstation on the same ROS network. Drive the robot around
with teleop, watch the map grow in RViz, then save it:

  ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map

which writes my_map.yaml / my_map.pgm for navigation-launch.py's map:=.

To navigate while mapping, use navigation-launch.py slam:=true instead.
"""

import os

import ament_index_python.packages
import launch
import launch.actions
import launch.launch_description_sources
import launch.substitutions


def generate_launch_description():
    navigation_share = ament_index_python.packages.get_package_share_directory('turtlebot_navigation')
    slam_toolbox_share = ament_index_python.packages.get_package_share_directory('slam_toolbox')

    slam_params_file = launch.substitutions.LaunchConfiguration('slam_params_file')
    use_sim_time = launch.substitutions.LaunchConfiguration('use_sim_time')

    # slam_toolbox's own launch file handles the lifecycle configure/activate
    # sequence. Its use_sim_time defaults to true, so it is always passed.
    slam_toolbox_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_share, 'launch', 'online_async_launch.py')),
        launch_arguments={
            'slam_params_file': slam_params_file,
            'use_sim_time': use_sim_time,
        }.items())

    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'slam_params_file',
            default_value=os.path.join(navigation_share, 'config', 'slam_toolbox_params.yaml'),
            description='slam_toolbox parameters file'),
        launch.actions.DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use the /clock topic (simulation) instead of wall time'),
        slam_toolbox_launch,
    ])
