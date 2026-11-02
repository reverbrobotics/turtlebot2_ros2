"""RViz for SLAM and navigation, run on the workstation.

The ROS 2 equivalent of ROS 1's `roslaunch turtlebot_rviz_launchers
view_navigation.launch`. Shows the map, laser scan, costmaps, plans and AMCL
particles, with the "2D Pose Estimate" and "Nav2 Goal" tools and the Nav2
panel. Use it with slam_demo-launch.py or amcl_demo-launch.py on the robot.
"""

import os

import ament_index_python.packages
import launch
import launch_ros.actions


def generate_launch_description():
    rviz_share = ament_index_python.packages.get_package_share_directory('turtlebot_rviz_launchers')

    return launch.LaunchDescription([
        launch_ros.actions.Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            arguments=['-d', os.path.join(rviz_share, 'rviz', 'navigation.rviz')]),
    ])
