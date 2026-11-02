"""Start the TurtleBot's depth camera and turn it into a laser scan.

The ROS 2 equivalent of ROS 1's turtlebot_bringup 3dsensor.launch, for an
OpenNI2 camera (Asus Xtion Pro / Orbbec Astra). Run it on the robot, next to
turtlebot_bringup-launch.py, which publishes the camera frames:

  openni2_camera (/camera/driver)
        |  /camera/depth_raw/image, /camera/depth_raw/camera_info
        v
  depthimage_to_laserscan --> /scan  (frame: camera_depth_frame)

/scan is what slam_toolbox, AMCL and the Nav2 costmaps consume.
"""

import os

import ament_index_python.packages
import launch
import launch_ros.actions


def generate_launch_description():
    bringup_share = ament_index_python.packages.get_package_share_directory('turtlebot_bringup')

    # The camera frames come from turtlebot_description via
    # turtlebot_bringup-launch.py's robot_state_publisher, so openni2_camera's
    # own tfs.launch.py is deliberately not included here.
    camera_driver_node = launch_ros.actions.Node(
        package='openni2_camera',
        executable='openni2_camera_driver',
        name='driver',
        namespace='camera',
        output='both',
        parameters=[os.path.join(bringup_share, 'config', 'openni2_params.yaml')])

    depthimage_to_laserscan_node = launch_ros.actions.Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depthimage_to_laserscan',
        output='both',
        parameters=[os.path.join(bringup_share, 'config', 'depthimage_to_laserscan_params.yaml')],
        remappings=[
            ('depth', '/camera/depth_raw/image'),
            ('depth_camera_info', '/camera/depth_raw/camera_info'),
            ('scan', '/scan'),
        ])

    return launch.LaunchDescription([
        camera_driver_node,
        depthimage_to_laserscan_node,
    ])
