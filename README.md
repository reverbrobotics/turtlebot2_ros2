# turtlebot2_ros2

This project contains a minimal example for setting up ROS 2 on the Kobuki
[TurtleBot 2 platform](https://www.turtlebot.com/). Teleoperation using the
keyboard and a joystick controller is demonstrated.
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
  turtlebot_bringup, ecl_core, ecl_lite and ecl_tools packages):

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

  No extra `--cmake-args` are required. The build is clean — 48 packages, zero
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

The Kobuki TurtleBot 2 is now fully migrated to ROS 2 and is ready for more
complex navigation tasks.

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
