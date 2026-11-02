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
  turtlebot_bringup, turtlebot_description, turtlebot_navigation,
  turtlebot_rviz_launchers, turtlebot_teleop, ecl_core, ecl_lite and ecl_tools
  packages):

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

  No extra `--cmake-args` are required. The build is clean — 53 packages, zero
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

- Open an ssh connection to the robot then start the robot, exactly like ROS 1's
  `roslaunch turtlebot_bringup minimal.launch`. It starts `kobuki_node`
  alongside `cmd_vel_mux`, `kobuki_safety_controller`,
  `kobuki_velocity_smoother` and `robot_state_publisher`, wired together so that
  all velocity commands are multiplexed, bump/cliff/wheel-drop-safe, and
  acceleration-limited before reaching the base — rather than talking to
  `kobuki_node` directly (`turtlebot_bringup-launch.py` is the same thing under
  its original name):

```bash
ros2 launch turtlebot_bringup minimal-launch.py
```

- Run keyboard teleoperation (to drive the robot using a keyboard), the
  equivalent of ROS 1's `turtlebot_teleop keyboard_teleop.launch`. It is a
  `ros2 run` command rather than a launch file because keyboard teleop needs the
  terminal, which `ros2 launch` does not pass to its nodes. It starts at
  0.2 m/s and 1.0 rad/s; `q`/`z` change the speed:

```bash
ros2 run turtlebot_teleop keyboard_teleop
```

- Alternatively, run joystick teleoperation (to drive the robot using a
  joystick). The default is this repository's PDP config (hold `LB` to drive,
  `RB` for turbo):

```bash
ros2 launch turtlebot_teleop joystick_teleop-launch.py
```

  If you're using a different joystick, pick one of `teleop_twist_joy`'s configs
  (`ps3`, `ps5`, `xbox`, `atk3`, `xd3`, or its own `pdp`, which enables on
  button 2) by name:

```bash
ros2 launch turtlebot_teleop joystick_teleop-launch.py joy_config:=ps3
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

This works like ROS 1's TurtleBot: the robot runs the drivers, SLAM and
navigation, and the workstation runs RViz and teleop. The depth camera's image
is turned into a laser scan,
[slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) builds the map (it
replaces gmapping), and [Nav2](https://docs.nav2.org/) localizes with AMCL and
drives the robot (it replaces move_base).

| ROS 1 | ROS 2 (this repository) | runs on |
|---|---|---|
| `roslaunch turtlebot_bringup minimal.launch` | `ros2 launch turtlebot_bringup minimal-launch.py` | robot |
| `roslaunch turtlebot_navigation gmapping_demo.launch` | `ros2 launch turtlebot_navigation slam_demo-launch.py` | robot |
| `roslaunch turtlebot_navigation amcl_demo.launch map_file:=...` | `ros2 launch turtlebot_navigation amcl_demo-launch.py map:=...` | robot |
| `roslaunch turtlebot_rviz_launchers view_navigation.launch` | `ros2 launch turtlebot_rviz_launchers view_navigation-launch.py` | workstation |
| `roslaunch turtlebot_rviz_launchers view_robot.launch` | `ros2 launch turtlebot_rviz_launchers view_robot-launch.py` | workstation |
| `roslaunch turtlebot_teleop keyboard_teleop.launch` | `ros2 run turtlebot_teleop keyboard_teleop` | workstation |
| `roslaunch turtlebot_teleop logitech.launch` (etc.) | `ros2 launch turtlebot_teleop joystick_teleop-launch.py joy_config:=...` | workstation |
| `rosrun map_server map_saver -f ...` | `ros2 run nav2_map_server map_saver_cli -f ...` | either |

As in ROS 1, the `*_demo` launch files also start the depth camera
(`3dsensor-launch.py`), so there is nothing else to run on the robot.
Navigation's velocity commands go to `cmd_vel_mux`'s `input/navigation`, so the
safety controller (bumpers/cliffs/wheel drops) and teleop both override it,
and `kobuki_velocity_smoother` still applies the acceleration limits.

### Install

On the robot (camera driver, scan conversion, SLAM and Nav2):

```bash
sudo apt install -y ros-lyrical-openni2-camera ros-lyrical-depthimage-to-laserscan ros-lyrical-robot-state-publisher ros-lyrical-navigation2 ros-lyrical-slam-toolbox
```

On the workstation (RViz with the Nav2 plugins, teleop):

```bash
sudo apt install -y ros-lyrical-rviz2 ros-lyrical-nav2-rviz-plugins ros-lyrical-nav2-map-server ros-lyrical-teleop-twist-keyboard ros-lyrical-teleop-twist-joy ros-lyrical-joy
```

`rosdep install -i --from-path src --rosdistro lyrical -y` installs all of
these too, since they are declared in the packages' `package.xml`. Rebuild
afterwards with `colcon build --symlink-install`. Both machines need this
workspace built; the workstation uses it for the robot model's meshes, the
RViz configs and the teleop commands.

Check that the camera is visible to OpenNI2 (plug it into the robot first):

```bash
ros2 run openni2_camera list_devices
```

### Orbbec Astra

An Asus Xtion works with the steps above. An Orbbec Astra (`lsusb` shows
`2bc5:0401`, or `0402`/`0404`/`0407` for the Astra S / Mini / Mini S) needs
Orbbec's own OpenNI2 build: Ubuntu's OpenNI2 has no Orbbec driver, and
Orbbec's driver crashes when loaded into Ubuntu's library. Install Orbbec's
library and driver side by side in `/opt/orbbec_openni2`, plus Orbbec's udev
rules (arm64 files shown; use `x64` instead of `arm64` on a PC):

```bash
B=https://raw.githubusercontent.com/orbbec/ros_astra_camera/main
sudo mkdir -p /opt/orbbec_openni2/OpenNI2/Drivers
sudo curl -fL -o /opt/orbbec_openni2/libOpenNI2.so.0 $B/include/openni2_redist/arm64/libOpenNI2.so
sudo curl -fL -o /opt/orbbec_openni2/OpenNI.ini $B/include/openni2_redist/arm64/OpenNI.ini
sudo curl -fL -o /opt/orbbec_openni2/OpenNI2/Drivers/liborbbec.so $B/include/openni2_redist/arm64/OpenNI2/Drivers/liborbbec.so
sudo curl -fL -o /opt/orbbec_openni2/OpenNI2/Drivers/orbbec.ini $B/include/openni2_redist/arm64/OpenNI2/Drivers/orbbec.ini
sudo curl -fL -o /etc/udev/rules.d/56-orbbec-usb.rules $B/56-orbbec-usb.rules
sudo udevadm control --reload && sudo udevadm trigger
```

Then replug the camera. `3dsensor-launch.py` (and so `slam_demo` /
`amcl_demo`) automatically starts the camera driver with
`/opt/orbbec_openni2` first on `LD_LIBRARY_PATH` when that directory exists.
Standalone tools need it set by hand:

```bash
LD_LIBRARY_PATH=/opt/orbbec_openni2:$LD_LIBRARY_PATH ros2 run openni2_camera list_devices
```

Don't copy `liborbbec.so` into Ubuntu's `/usr/lib/*/OpenNI2/Drivers`: the
camera is then listed but the driver segfaults when opening it.

If the driver instead dies with `undefined symbol: has_buffer_fields_...`,
the apt `openni2_camera` was built against newer ROS message libraries than
the ones installed. Either bring the ROS packages up to date, or build
`openni2_camera` in the workspace against what is installed:

```bash
sudo apt install libopenni2-dev
git -C src clone -b 2.3.0 https://github.com/ros-drivers/openni2_camera.git
colcon build --symlink-install --packages-select openni2_camera
```

### Robot and workstation on one ROS network

On both machines:

- use the same `ROS_DOMAIN_ID` (e.g. `export ROS_DOMAIN_ID=30` in `~/.bashrc`),
  and stay on the same subnet (the default discovery range);
- **synchronise the clocks** (e.g. install `chrony` on both and point the robot
  at the workstation). The scan and transforms are timestamped on the robot,
  and a clock offset of more than a fraction of a second makes RViz and
  anything else on the workstation drop them with "extrapolation into the
  future" errors.

### Camera mount

`turtlebot_description/urdf/turtlebot.urdf.xacro` places the camera where
ROS 1's turtlebot_description did on the standard hexagon stack
(`camera_x=-0.087`, `camera_z=0.287` m from `base_link`). If yours sits
elsewhere, measure it and change the `camera_*` defaults at the top of that
file. A wrong height or forward offset shows up as walls being drawn in the
wrong place. `view_robot-launch.py` is a quick way to check the robot model,
frames and scan before mapping.

### Build a map

On the robot (two ssh sessions):

```bash
ros2 launch turtlebot_bringup minimal-launch.py
```

```bash
ros2 launch turtlebot_navigation slam_demo-launch.py
```

On the workstation:

```bash
ros2 launch turtlebot_rviz_launchers view_navigation-launch.py
```

```bash
ros2 run turtlebot_teleop keyboard_teleop
```

Drive slowly around the area, turning in place now and then so the camera sees
the walls in every direction, until the map is complete. As with ROS 1's
gmapping_demo you can also send **Nav2 Goal**s in RViz, but only inside the
part of the map already explored. Then save the map (from either machine):

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
```

`slam_demo-launch.py navigation:=false` maps without starting Nav2, for a
lighter load on the robot.

### Navigate

On the robot, copy the map there if you saved it on the workstation, then:

```bash
ros2 launch turtlebot_bringup minimal-launch.py
```

```bash
ros2 launch turtlebot_navigation amcl_demo-launch.py map:=$HOME/maps/my_map.yaml
```

On the workstation:

```bash
ros2 launch turtlebot_rviz_launchers view_navigation-launch.py
```

As in ROS 1, AMCL starts out assuming the robot is at the map's origin (where
mapping began). If it isn't, click **2D Pose Estimate** in RViz and drag out
where the robot is and which way it faces. Then send it somewhere with
**Nav2 Goal**.

### Running SLAM or navigation on the workstation instead

The demo launch files are thin wrappers. To keep the robot's load down to the
drivers, run the pieces separately: `3dsensor-launch.py` on the robot, and
`slam-launch.py` or `navigation-launch.py` (`map:=...` or `slam:=true`) on the
workstation:

```bash
ros2 launch turtlebot_bringup 3dsensor-launch.py
```

```bash
ros2 launch turtlebot_navigation navigation-launch.py slam:=true
```

Only `/scan`, `/odom`, `/tf` and velocity commands then cross the network.
The controller is Regulated Pure Pursuit rather than Nav2's default MPPI
because it is light enough for a Raspberry Pi, so running it all on the robot
is the default here, as in ROS 1.

### Limits of a depth-camera "laser"

The Xtion/Astra sees a ~58° wedge from 0.45 m to about 4 m, compared with
a lidar's 360° and 10 m or more. The configs in `turtlebot_navigation/config/`
are tuned for that (slam_toolbox adds a scan every 0.2 m or 0.2 rad of turn,
the ranges match `depthimage_to_laserscan`, and the robot turns in place
towards its path before driving and never reverses), but expect the following:

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
