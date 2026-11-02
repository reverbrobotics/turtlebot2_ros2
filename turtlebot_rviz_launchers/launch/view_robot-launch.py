"""RViz view of the robot alone, run on the workstation.

The ROS 2 equivalent of ROS 1's `roslaunch turtlebot_rviz_launchers
view_robot.launch`. Shows the robot model, TF frames and laser scan in the
odom frame, which is enough to check minimal-launch.py and the camera before
mapping.
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
            arguments=['-d', os.path.join(rviz_share, 'rviz', 'robot.rviz')]),
    ])
