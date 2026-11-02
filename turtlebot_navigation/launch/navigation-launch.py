"""Navigate the TurtleBot with Nav2, the ROS 2 equivalent of ROS 1's amcl_demo.

Needs the robot running turtlebot_bringup-launch.py and 3dsensor-launch.py.
Can run on the robot or on a workstation on the same ROS network.

With a saved map (localize with AMCL):

  ros2 launch turtlebot_navigation navigation-launch.py map:=$HOME/maps/my_map.yaml

then use "2D Pose Estimate" in RViz to tell AMCL where the robot starts,
and "Nav2 Goal" to send it somewhere.

Without a map (build one with slam_toolbox while navigating):

  ros2 launch turtlebot_navigation navigation-launch.py slam:=true

Velocity commands go to cmd_vel_mux's /input/navigation, so the safety
controller and teleop both override Nav2.
"""

import os

import ament_index_python.packages
import launch
import launch.actions
import launch.conditions
import launch.launch_description_sources
import launch.substitutions
import launch_ros.actions
import launch_ros.descriptions


LOCALIZATION_NODES = ['map_server', 'amcl']

# Only the servers the default behavior trees use. nav2_bringup also starts
# the smoother, route, docking and following servers and Nav2's own
# velocity_smoother, none of which this robot needs (kobuki_velocity_smoother
# in turtlebot_bringup does the smoothing).
NAVIGATION_NODES = [
    'controller_server',
    'planner_server',
    'behavior_server',
    'bt_navigator',
    'waypoint_follower',
    'collision_monitor',
]


def generate_launch_description():
    navigation_share = ament_index_python.packages.get_package_share_directory('turtlebot_navigation')

    map_yaml = launch.substitutions.LaunchConfiguration('map')
    slam = launch.substitutions.LaunchConfiguration('slam')
    use_sim_time = launch.substitutions.LaunchConfiguration('use_sim_time')
    autostart = launch.substitutions.LaunchConfiguration('autostart')
    log_level = launch.substitutions.LaunchConfiguration('log_level')

    # allow_substs expands the $(find-pkg-share ...) in bt_search_directories.
    params = [
        launch_ros.descriptions.ParameterFile(
            launch.substitutions.LaunchConfiguration('params_file'), allow_substs=True),
        {'use_sim_time': use_sim_time},
    ]
    ros_args = ['--ros-args', '--log-level', log_level]

    def nav2_node(package, executable, remappings=()):
        return launch_ros.actions.Node(
            package=package,
            executable=executable,
            name=executable,
            output='screen',
            parameters=params,
            arguments=ros_args,
            remappings=list(remappings))

    def lifecycle_manager(name, node_names):
        return launch_ros.actions.Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name=name,
            output='screen',
            arguments=ros_args,
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'node_names': node_names,
            }])

    # Localization against a saved map, or SLAM - never both, since each
    # publishes the map -> odom transform.
    localization = launch.actions.GroupAction(
        condition=launch.conditions.UnlessCondition(slam),
        actions=[
            launch_ros.actions.Node(
                package='nav2_map_server',
                executable='map_server',
                name='map_server',
                output='screen',
                parameters=params + [{'yaml_filename': map_yaml}],
                arguments=ros_args),
            nav2_node('nav2_amcl', 'amcl'),
            lifecycle_manager('lifecycle_manager_localization', LOCALIZATION_NODES),
        ])

    slam_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(navigation_share, 'launch', 'slam-launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
        condition=launch.conditions.IfCondition(slam))

    # controller_server and behavior_server publish on cmd_vel_nav;
    # collision_monitor forwards it to /input/navigation (see nav2_params.yaml).
    navigation = [
        nav2_node('nav2_controller', 'controller_server',
                  remappings=[('cmd_vel', 'cmd_vel_nav')]),
        nav2_node('nav2_planner', 'planner_server'),
        nav2_node('nav2_behaviors', 'behavior_server',
                  remappings=[('cmd_vel', 'cmd_vel_nav')]),
        nav2_node('nav2_bt_navigator', 'bt_navigator'),
        nav2_node('nav2_waypoint_follower', 'waypoint_follower'),
        nav2_node('nav2_collision_monitor', 'collision_monitor'),
        lifecycle_manager('lifecycle_manager_navigation', NAVIGATION_NODES),
    ]

    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'map', default_value='',
            description='Full path to the map yaml to navigate in (ignored when slam:=true)'),
        launch.actions.DeclareLaunchArgument(
            'slam', default_value='false',
            description='Build the map with slam_toolbox instead of loading one and running AMCL'),
        launch.actions.DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(navigation_share, 'config', 'nav2_params.yaml'),
            description='Nav2 parameters file'),
        launch.actions.DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use the /clock topic (simulation) instead of wall time'),
        launch.actions.DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Configure and activate the Nav2 nodes on startup'),
        launch.actions.DeclareLaunchArgument(
            'log_level', default_value='info',
            description='Log level for the Nav2 nodes'),
        localization,
        slam_launch,
    ] + navigation)
