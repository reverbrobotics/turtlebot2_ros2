"""ROS 1-style name for turtlebot_bringup-launch.py.

  ros2 launch turtlebot_bringup minimal-launch.py

is the equivalent of ROS 1's `roslaunch turtlebot_bringup minimal.launch`:
the base driver, cmd_vel mux, safety controller, velocity smoother and robot
model. See turtlebot_bringup-launch.py for how they are wired together.
"""

import os

import ament_index_python.packages
import launch
import launch.actions
import launch.launch_description_sources


def generate_launch_description():
    bringup_share = ament_index_python.packages.get_package_share_directory('turtlebot_bringup')

    return launch.LaunchDescription([
        launch.actions.IncludeLaunchDescription(
            launch.launch_description_sources.PythonLaunchDescriptionSource(
                os.path.join(bringup_share, 'launch', 'turtlebot_bringup-launch.py'))),
    ])
