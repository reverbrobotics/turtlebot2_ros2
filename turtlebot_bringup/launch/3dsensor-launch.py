"""Start the TurtleBot's depth camera and turn it into a laser scan.

The ROS 2 equivalent of ROS 1's turtlebot_bringup 3dsensor.launch, for an
OpenNI2 camera (Asus Xtion Pro / Orbbec Astra). Run it on the robot, next to
turtlebot_bringup-launch.py, which publishes the camera frames:

  openni2_camera (/camera/driver)
        |  /camera/depth_raw/image, /camera/depth_raw/camera_info
        v
  depthimage_to_laserscan --> /scan  (frame: camera_depth_frame)

/scan is what slam_toolbox, AMCL and the Nav2 costmaps consume.

Orbbec Astra: Ubuntu's OpenNI2 has no Orbbec driver, and Orbbec's driver
crashes inside Ubuntu's OpenNI2 library. If Orbbec's own OpenNI2 library and
driver are installed in ORBBEC_OPENNI2_DIR (see the README), the camera
driver is started with that directory first on LD_LIBRARY_PATH, so it loads
Orbbec's libOpenNI2.so.0 instead of Ubuntu's. Otherwise (e.g. an Xtion) the
system OpenNI2 is used as before.
"""

import os

import ament_index_python.packages
import launch
import launch_ros.actions

ORBBEC_OPENNI2_DIR = '/opt/orbbec_openni2'


def generate_launch_description():
    bringup_share = ament_index_python.packages.get_package_share_directory('turtlebot_bringup')

    camera_env = {}
    if os.path.isfile(os.path.join(ORBBEC_OPENNI2_DIR, 'libOpenNI2.so.0')):
        camera_env['LD_LIBRARY_PATH'] = os.pathsep.join(
            p for p in (ORBBEC_OPENNI2_DIR, os.environ.get('LD_LIBRARY_PATH')) if p)

    # The camera frames come from turtlebot_description via
    # turtlebot_bringup-launch.py's robot_state_publisher, so openni2_camera's
    # own tfs.launch.py is deliberately not included here.
    camera_driver_node = launch_ros.actions.Node(
        package='openni2_camera',
        executable='openni2_camera_driver',
        name='driver',
        namespace='camera',
        output='both',
        additional_env=camera_env,
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
