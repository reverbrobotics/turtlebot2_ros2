# turtlebot2_ros2

This project contains a minimal example for setting up ROS 2 on the Kobuki
[TurtleBot 2 platform](https://www.turtlebot.com/). Teleoperation using the
keyboard and a joystick controller is demonstrated, as well as
[SLAM and autonomous navigation](#slam-and-navigation) with the TurtleBot's
Asus Xtion / Orbbec Astra depth camera.
For a comprehensive guide, see [idorobotics.com](https://idorobotics.com/2024/02/20/ros2-on-kobuki-turtlebot/).

Supported distributions:

- **ROS 2 Lyrical / Ubuntu 26.04** — current, see below.
- **ROS 2 Humble / Ubuntu 22.04** — the original target; see
  [Humble setup](#humble-setup) at the bottom.

If you are porting an existing Humble workspace, [MIGRATION-lyrical.md](MIGRATION-lyrical.md)
explains every change and why it was needed.

## Setup (Lyrical)

To setup the TurtleBot 2 mobile robot base:

- Install the build and runtime dependencies. Note that `sophus` now pulls in
  Ceres, and that `kobuki_velocity_smoother` is **not** released for Lyrical —
  it is built from source as part of this repository instead.

```bash
sudo apt update && sudo apt install -y ros-lyrical-sophus ros-lyrical-diagnostic-updater ros-lyrical-joint-state-publisher ros-lyrical-xacro ros-lyrical-ros-testing libusb-1.0-0-dev libftdi1-dev
```

  `ros-lyrical-ecl-build` and `ros-lyrical-ecl-license` are deliberately **not**
  in that list — `ecl_tools` is built from source here instead, because its
  `cotire.cmake` needs a one-line fix to configure under CMake 4 (see
  [MIGRATION-lyrical.md](MIGRATION-lyrical.md) §2). Having them installed as well
  does no harm; the workspace overlay takes precedence.

- In a ROS 2 workspace, clone this repository (which contains the kobuki_core,
  kobuki_ros, kobuki_ros_interfaces, kobuki_velocity_smoother, cmd_vel_mux,
  turtlebot_bringup, turtlebot_description, turtlebot_navigation, ecl_core,
  ecl_lite and ecl_tools packages):

```bash
git clone https://github.com/reverbrobotics/turtlebot2_ros2.git
```

- Install any missing dependencies (run `sudo rosdep init && rosdep update`
  first if you have never used rosdep on this machine):

```bash
rosdep install -i --from-path src --rosdistro lyrical -y
```

- Build the workspace:

```bash
colcon build --symlink-install --executor sequential
```

  No extra `--cmake-args` are required. The build is clean — 51 packages, zero
  compiler or CMake warnings — on both CMake 4.2.3 (the Ubuntu 26.04 default) and
  CMake 3.29.

- Install the udev rules, then check version information and run the
  kobuki-simple-keyop test noted in the
  [official guide](https://kobuki.readthedocs.io/en/release-1.0.x/software.html):

```bash
sudo cp src/turtlebot2_ros2/kobuki_core/60-kobuki.rules /etc/udev/rules.d/ && sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Testing

To test this setup, run remote teleoperation to control (drive around) the robot
from a workstation (laptop) computer following the steps below:

- Install the teleop packages:

```bash
sudo apt-get install ros-lyrical-teleop-twist-keyboard ros-lyrical-teleop-tools ros-lyrical-teleop-twist-joy
```

- Open an ssh connection to the robot then start the robot with `turtlebot_bringup`.
  This is the ROS 2 equivalent of ROS 1's `turtlebot_bringup minimal.launch`: it
  starts `kobuki_node` alongside `cmd_vel_mux`, `kobuki_safety_controller` and
  `kobuki_velocity_smoother`, wired together so that all velocity commands are
  multiplexed, bump/cliff/wheel-drop-safe, and acceleration-limited before
  reaching the base — rather than talking to `kobuki_node` directly:

```bash
ros2 launch turtlebot_bringup turtlebot_bringup-launch.py
```

- Run keyboard teleoperation (to drive the robot using a keyboard):

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=input/teleop
```

- Alternatively, run joystick teleoperation (to drive the robot using a
  joystick). Lyrical's `teleop_twist_joy` now ships a `pdp` config of its own,
  so you can select it by name:

```bash
ros2 launch teleop_twist_joy teleop-launch.py joy_config:='pdp' joy_vel:='input/teleop'
```

  To use this repository's copy instead (it enables on button 4 rather than 2):

```bash
ros2 launch teleop_twist_joy teleop-launch.py config_filepath:='/path/to/ros2_ws/src/turtlebot2_ros2/configs/pdp.config.yaml' joy_vel:='input/teleop'
```

  If you're using a different joystick like PS3 then run:

```bash
ros2 launch teleop_twist_joy teleop-launch.py joy_config:='ps3' joy_vel:='input/teleop'
```

Both teleop nodes publish plain `geometry_msgs/Twist` by default on Lyrical,
which is what `cmd_vel_mux`'s `input/teleop` subscriber expects. If you set
`teleop_twist_keyboard`'s `stamped` parameter or `teleop_twist_joy`'s
`publish_stamped_twist` launch argument to `true`, the robot will stop
responding.

If you need to talk to the base driver directly (e.g. for low-level
debugging, bypassing the mux/smoother/safety controller), you can still run
`ros2 launch kobuki_node kobuki_node-launch.py` on its own and remap teleop's
`cmd_vel` to `commands/velocity` instead — but `turtlebot_bringup` is the
recommended way to drive the robot.

## SLAM and navigation

This is the ROS 2 equivalent of ROS 1's `turtlebot_navigation`
`gmapping_demo.launch` / `amcl_demo.launch`: the depth camera's image is
turned into a laser scan, [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox)
builds the map (it replaces gmapping), and [Nav2](https://docs.nav2.org/)
localizes with AMCL and drives the robot.

| package | runs on | what it does |
|---|---|---|
| `turtlebot_description` | — | URDF: the Kobuki plus the camera frames on the top plate |
| `turtlebot_bringup` | robot | `turtlebot_bringup-launch.py` now also runs `robot_state_publisher`; `3dsensor-launch.py` runs `openni2_camera` + `depthimage_to_laserscan` → `/scan` |
| `turtlebot_navigation` | robot or workstation | `slam-launch.py` (slam_toolbox), `navigation-launch.py` (Nav2, with a saved map or `slam:=true`), tuned configs in `config/` |

Nav2's output goes to `cmd_vel_mux`'s `input/navigation`, so the safety
controller (bumpers/cliffs/wheel drops) and teleop both override it, and
`kobuki_velocity_smoother` still applies the acceleration limits.

### Install

On the robot (the camera driver and scan conversion):

```bash
sudo apt install -y ros-lyrical-openni2-camera ros-lyrical-depthimage-to-laserscan ros-lyrical-robot-state-publisher
```

On whichever machine runs SLAM/navigation (the workstation, the robot, or
both), plus `nav2-bringup` wherever you run RViz, for its Nav2 RViz config:

```bash
sudo apt install -y ros-lyrical-navigation2 ros-lyrical-slam-toolbox ros-lyrical-nav2-bringup
```

`rosdep install -i --from-path src --rosdistro lyrical -y` installs all of
these too, since they are declared in the packages' `package.xml`. Rebuild
afterwards with `colcon build --symlink-install`.

Check that the camera is visible to OpenNI2 (plug it into the robot first):

```bash
ros2 run openni2_camera list_devices
```

### Robot and workstation on one ROS network

The heavy parts (SLAM, Nav2, RViz) can run on a workstation while the robot
runs only the drivers. Only `/scan`, `/odom`, `/tf` and velocity commands
cross the network. On both machines:

- use the same `ROS_DOMAIN_ID` (e.g. `export ROS_DOMAIN_ID=30` in `~/.bashrc`),
  and stay on the same subnet (the default discovery range);
- **synchronise the clocks** (e.g. install `chrony` on both and point the robot
  at the workstation). The scan and transforms are timestamped on the robot,
  and a clock offset of more than a fraction of a second makes SLAM, AMCL and
  the costmaps drop data with "extrapolation into the future" errors.

Everything also runs on the robot alone if you prefer. The controller is
Regulated Pure Pursuit rather than Nav2's default MPPI because it is light
enough for a Raspberry Pi.

### Camera mount

`turtlebot_description/urdf/turtlebot.urdf.xacro` places the camera where
ROS 1's turtlebot_description did on the standard hexagon stack
(`camera_x=-0.087`, `camera_z=0.287` m from `base_link`). If yours sits
elsewhere, measure it and change the `camera_*` defaults at the top of that
file. A wrong height or forward offset shows up as walls being drawn in the
wrong place.

### Build a map

On the robot:

```bash
ros2 launch turtlebot_bringup turtlebot_bringup-launch.py
```

```bash
ros2 launch turtlebot_bringup 3dsensor-launch.py
```

On the workstation (or robot):

```bash
ros2 launch turtlebot_navigation slam-launch.py
```

```bash
ros2 launch nav2_bringup rviz_launch.py
```

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=input/teleop
```

Drive slowly around the area until the map is complete, then save it:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
```

### Navigate

With the robot running the two launch files above:

```bash
ros2 launch turtlebot_navigation navigation-launch.py map:=$HOME/maps/my_map.yaml
```

```bash
ros2 launch nav2_bringup rviz_launch.py
```

In RViz, click **2D Pose Estimate** and drag out where the robot is and which
way it faces. Navigation becomes active once AMCL has a pose. Then send it
somewhere with **Nav2 Goal**.

To navigate and map at the same time (no saved map; goals must be inside the
part of the map already explored):

```bash
ros2 launch turtlebot_navigation navigation-launch.py slam:=true
```

### Limits of a depth-camera "laser"

The Xtion/Astra sees a ~58° wedge from 0.45 m to about 4 m, compared with
a lidar's 360° and 10 m or more. The configs in `turtlebot_navigation/config/`
are tuned for that (slam_toolbox adds scans every 0.2 m, the ranges match
`depthimage_to_laserscan`, and the robot turns in place towards its path
before driving and never reverses), but expect the following:

- Map by driving slowly, and turn in place now and then so walls are seen
  from several angles. Featureless corridors and big open rooms are hard
  for scan matching with this little range.
- Obstacles closer than 0.45 m, or above or below the camera's
  scan rows, are invisible. The bumpers (safety controller) are the last
  line of defence.
- AMCL needs walls within ~4 m to localize. Give it a good initial pose.

If you later add a 2D lidar, publish its scan on `/scan` (in a z-up frame
added to the URDF), and raise the range settings (`max_laser_range`,
`laser_max_range`, `obstacle_max_range`/`raytrace_max_range`) to match.

## Humble setup

The original Humble instructions, for reference:

- Install the velocity smoother and sophus packages:
  `sudo apt-get install ros-humble-kobuki-velocity-smoother ros-humble-sophus`
- Clone this repository into a ROS 2 workspace.
- `rosdep install -i --from-path src --rosdistro humble -y`
- `colcon build --symlink-install --executor sequential`
- Teleop packages: `sudo apt-get install ros-humble-teleop-twist-keyboard ros-humble-joy-teleop ros-humble-teleop-twist-joy`

The source changes described in [MIGRATION-lyrical.md](MIGRATION-lyrical.md) have
not been re-tested against Humble. The `.hpp` header renames in particular will
not work there — Humble still ships the `.h` names.
