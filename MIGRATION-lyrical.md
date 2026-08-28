# Migrating turtlebot2_ros2 from ROS 2 Humble to ROS 2 Lyrical (Ubuntu 26.04)

This repository was written against ROS 2 Humble on Ubuntu 22.04. This document
records everything that had to change to build and run it on **ROS 2 Lyrical /
Ubuntu 26.04 "resolute"**, and why.

Verified against:

| | |
|---|---|
| OS | Ubuntu 26.04 LTS (resolute) |
| ROS | Lyrical (`/opt/ros/lyrical`) |
| Compiler | GCC 15.2.0 |
| CMake | 4.2.3 (system) — also verified on 3.29.3 |
| Python | 3.14.4 |

All 45 packages configure, compile, install and launch cleanly from a clean
`build/`, `install/`, `log/`.

---

## 1. Dependencies

### 1.1 apt packages

```bash
sudo apt update
sudo apt install -y \
  ros-lyrical-ecl-build ros-lyrical-ecl-license \
  ros-lyrical-sophus ros-lyrical-diagnostic-updater \
  ros-lyrical-joint-state-publisher ros-lyrical-xacro \
  ros-lyrical-ros-testing \
  ros-lyrical-teleop-twist-keyboard ros-lyrical-teleop-twist-joy \
  ros-lyrical-teleop-tools \
  libusb-1.0-0-dev libftdi1-dev
```

`ros-lyrical-sophus` is the piece that changed the most. Humble's Sophus was
header-only against Eigen; the Lyrical package (1.22.9102) declares
`find_dependency(Ceres 2.2.0)` and `find_dependency(fmt 10.1.0)` in its
`SophusConfig.cmake`, so `find_package(Sophus REQUIRED)` in `ecl_linear_algebra`
now pulls in Ceres → SuiteSparse → glog → gflags → libunwind. apt resolves that
whole tree automatically; it is called out here only because the failure mode
("Could not find a package configuration file provided by Ceres") is confusing
if you install `sophus` by hand.

Then initialise rosdep (once per machine) and let it check the rest:

```bash
sudo rosdep init
rosdep update
rosdep install -i --from-path src --rosdistro lyrical -y
```

### 1.2 `kobuki_velocity_smoother` has no Lyrical binary

`kobuki_keyop` declares `<exec_depend>kobuki_velocity_smoother</exec_depend>`.
rosdep resolves that key to `ros-lyrical-kobuki-velocity-smoother`, which **does
not exist** — the package has not been released for Lyrical, so
`rosdep install` fails at the apt step.

It has been added to the workspace as a source submodule instead:

```
[submodule "kobuki_velocity_smoother"]
	path = kobuki_velocity_smoother
	url = https://github.com/kobuki-base/velocity_smoother.git
```

and to `turtlebot2_ros2_demo/turtlebot2_ros2_demo.repos`. Its C++ needed no
changes; two of its launch files did (see §5.3).

### 1.3 Packages that are *not* built

`kobuki_ros/kobuki_controller_tutorial` and `kobuki_ros/kobuki_testsuite` were
never ported from ROS 1 — they still declare `catkin`, `roscpp`, `nodelet`,
`message_generation` and `yocs_controllers`. They carry (upstream, pre-existing)
empty `COLCON_IGNORE` files, so colcon skips them and `rosdep` never sees their
ROS 1 keys. Left as-is.

---

## 2. Build configuration

### 2.1 CMake 4 rejects `cmake_minimum_required(VERSION 2.8)`

Ubuntu 26.04 ships **CMake 4.2.3**, which removed compatibility with
`cmake_minimum_required` values below 3.5. `cotire.cmake` — shipped *inside the
binary* `ros-lyrical-ecl-build` package, not in this repo — still declares 2.8:

```
CMake Error at .../share/ecl_build/cmake/cotire.cmake:45 (cmake_minimum_required):
  Compatibility with CMake < 3.5 has been removed from CMake.
```

Every ecl package does `find_package(ecl_build)`, so this stops the build at
`ecl_config`. Since the file belongs to an apt-installed package, patching it is
not durable across upgrades. The fix is to configure with:

```
-DCMAKE_POLICY_VERSION_MINIMUM=3.5
```

The repo's own `cmake_minimum_required(VERSION 3.5)` calls are fine — 3.5 is
exactly the boundary CMake 4 still accepts. They emit a deprecation warning
("Compatibility with CMake < 3.10 will be removed") but nothing more.

### 2.2 How to pass that flag on this machine

**Do not** pass `--cmake-args` on the command line here. `~/.colcon/defaults.yaml`
already supplies `-DPython3_EXECUTABLE=/usr/bin/python3` (because a uv-managed
CPython 3.12 in `~/.local/bin` otherwise wins `FindPython3` and has no
`catkin_pkg`), and colcon-defaults **replaces** rather than merges the
`cmake-args` list — so a command-line `--cmake-args` silently drops it and the
build fails with `ModuleNotFoundError: No module named 'catkin_pkg'`.

`-DCMAKE_POLICY_VERSION_MINIMUM=3.5` has therefore been added to
`~/.colcon/defaults.yaml` alongside the existing entries, keeping a bare
`colcon build` the complete command.

### 2.3 `ament_target_dependencies()` was removed

This is the single biggest source-level change. `ament_target_dependencies()` no
longer exists in Lyrical (the `ament_cmake_target_dependencies` package still
ships, but only provides `ament_get_recursive_properties`):

```
CMake Error at CMakeLists.txt:25 (ament_target_dependencies):
  Unknown CMake command "ament_target_dependencies".
```

Every call was replaced with `target_link_libraries(<target> PUBLIC ...)` against
the modern namespaced targets. The mapping used:

| dependency | target |
|---|---|
| `rclcpp` | `rclcpp::rclcpp` |
| `rclcpp_action` | `rclcpp_action::rclcpp_action` |
| `rclcpp_components` | `rclcpp_components::component` |
| `rcpputils` | `rcpputils::rcpputils` |
| `angles` | `angles::angles` |
| `message_filters` | `message_filters::message_filters` |
| `diagnostic_updater` | `diagnostic_updater::diagnostic_updater` |
| `tf2` / `tf2_ros` / `tf2_geometry_msgs` | `tf2::tf2`, `tf2_ros::tf2_ros`, `tf2_geometry_msgs::tf2_geometry_msgs` |
| `kobuki_core` | `kobuki_core::kobuki_core` |
| any message/interface package | `<pkg>::<pkg>__rosidl_typesupport_cpp` |

Files changed:

- `cmd_vel_mux/CMakeLists.txt`
- `kobuki_ros/kobuki_bumper2pc/CMakeLists.txt`
- `kobuki_ros/kobuki_random_walker/CMakeLists.txt`
- `kobuki_ros/kobuki_keyop/CMakeLists.txt`
- `kobuki_ros/kobuki_safety_controller/CMakeLists.txt`
- `kobuki_ros/kobuki_auto_docking/CMakeLists.txt`
- `kobuki_ros/kobuki_node/CMakeLists.txt`

`kobuki_auto_docking` and `kobuki_node` already had a plain
`target_link_libraries(<target> ecl_...)` for their ecl dependencies. Those were
folded into the new keyword-signature call — CMake forbids mixing the keyword
(`PUBLIC/PRIVATE`) and plain signatures on the same target.

Everything else in the ament CMake API (`ament_export_dependencies`,
`ament_export_include_directories`, `ament_export_libraries`,
`ament_export_targets`, `ament_package`) is unchanged.

---

## 3. GCC 15 / C++ changes

### 3.1 `-Woverloaded-virtual` on `ecl::Error`

`ecl_build`'s `ecl_enable_cxx_warnings()` adds `-Wall -Wextra -Werror -Wpedantic`.
GCC ≥ 14 diagnoses an implicitly declared copy-assignment operator that hides a
virtual `operator=` in a base class, which `ecl::Error` has:

```
error: 'virtual void ecl::Error::operator=(const ecl::ErrorFlag&)' was hidden
       [-Werror=overloaded-virtual=]
note:   by 'constexpr ecl::SocketError& ecl::SocketError::operator=(const ecl::SocketError&)'
```

Added `using Error::operator=;` to each class deriving from `ecl::Error`:

- `ecl_lite/ecl_io/include/ecl/io/sockets.hpp` (`SocketError`)
- `ecl_lite/ecl_time_lite/include/ecl/time_lite/errors.hpp` (`TimeError`)
- `ecl_core/ecl_filesystem/include/ecl/filesystem/errors.hpp` (`TimeError`)

This preserves the existing API rather than disabling the warning.

### 3.2 `-Wpessimizing-move`

`kobuki_ros/kobuki_node/src/kobuki_ros.cpp:598`

```cpp
- odom_publisher_->publish(std::move(odometry_->getOdometry()));
+ odom_publisher_->publish(odometry_->getOdometry());
```

`getOdometry()` already returns a prvalue; the `std::move` defeated copy elision
and is an error under `-Werror`.

---

## 4. ROS 2 API changes

### 4.1 `.h` → `.hpp` headers

`tf2`, `tf2_ros` and `message_filters` deprecated their `.h` headers in Jazzy and
removed them in Kilted/Lyrical.

`kobuki_ros/kobuki_node`:
- `tf2/LinearMath/Quaternion.h` → `.hpp` (`src/kobuki_ros.cpp`, `src/odometry.cpp`)
- `tf2_ros/transform_broadcaster.h` → `.hpp` (`src/kobuki_ros.cpp`, `include/kobuki_node/kobuki_ros.hpp`)

`kobuki_ros/kobuki_auto_docking`:
- `message_filters/subscriber.h`, `synchronizer.h`, `time_synchronizer.h`,
  `sync_policies/approximate_time.h` → `.hpp`
  (`src/auto_docking_ros.cpp`, `include/kobuki_auto_docking/auto_docking_ros.hpp`)

### 4.2 `message_filters::Subscriber` requires a QoS

The `(node, topic)` two-argument constructor is gone; every overload now takes a
QoS. `kobuki_ros/kobuki_auto_docking/src/auto_docking_ros.cpp`:

```cpp
- std::make_shared<message_filters::Subscriber<T>>(this, "odom");
+ std::make_shared<message_filters::Subscriber<T>>(this, "odom", rclcpp::QoS(10));
```

`rclcpp::QoS(10)` reproduces the old default (KEEP_LAST 10, RELIABLE) for all
three subscribers (`odom`, `sensors/core`, `sensors/dock_ir`).

### 4.3 `actionlib_msgs` no longer exists

`kobuki_auto_docking/package.xml` declared `<depend>actionlib_msgs</depend>`.
The key is gone from the Lyrical rosdistro, so `rosdep install` fails on it, and
nothing in the package ever used it (its action definitions live in
`kobuki_ros_interfaces`). Removed, and the two dependencies the CMakeLists
actually `find_package`es but the manifest omitted — `rcl_interfaces` and
`tf2_ros` — were added.

---

## 5. Launch file fixes

These were already broken before Lyrical (the `node_*` keyword arguments were
removed back in Foxy), but they have to be fixed for anything to actually run.

### 5.1 Legacy `launch_ros` keyword arguments

`node_executable=` → `executable=`, `node_name=` → `name=`,
`node_namespace=` → `namespace=`, `node_plugin=` → `plugin=` in:

- `kobuki_ros/kobuki_safety_controller/launch/safety_controller-launch.py`
- `kobuki_ros/kobuki_safety_controller/launch/safety_controller-composed-launch.py`
- `kobuki_ros/kobuki_bumper2pc/launch/kobuki_bumper2pc-launch.py`

Symptom: `TypeError: Node.__init__() missing 1 required keyword-only argument: 'executable'`.

### 5.2 `kobuki_bumper2pc`

Two bugs:

- `executable='kobuki_bumper2pc'` named the *library*, not the node. The
  executable generated by `rclcpp_components_register_node` is
  `kobuki_bumper2pc_node`.
- `CMakeLists.txt` installed only `launch/`, while the launch file reads
  `config/kobuki_bumper2pc_params.yaml` from the install space →
  `FileNotFoundError`. Changed to `install(DIRECTORY config launch ...)`.

### 5.3 `kobuki_velocity_smoother`

Both launch files refer to a package named `velocity_smoother`; the package is
`kobuki_velocity_smoother` (the *repository* is `velocity_smoother`). Fixed the
share-directory lookup, the YAML top-level key, `package=` and the component
`plugin=` (`kobuki_velocity_smoother::VelocitySmoother`). The node name and
executable name are genuinely `velocity_smoother` and were left alone.

---

## 6. Things that did *not* need changing

Worth recording, because they are the usual suspects:

- **`kobuki_core`** builds unmodified. Its FTDI/USB code, `ecl` usage and the
  `kobuki-version-info` / `kobuki-simple-keyop` tools are all fine on GCC 15.
- **`kobuki_ros_interfaces`** builds unmodified (a `ros-lyrical-kobuki-ros-interfaces`
  binary also exists, but the source package takes precedence in the overlay).
- **`kobuki_description`** builds and launches unmodified; `robot_state_publisher`
  and `joint_state_publisher` both come up.
- **Teleop still uses plain `geometry_msgs/Twist`.** Lyrical's
  `teleop_twist_keyboard` (`stamped` parameter) and `teleop_twist_joy`
  (`publish_stamped_twist` launch argument) both default to `false`, so the
  README's `--remap cmd_vel:=commands/velocity` still lines up with
  `kobuki_node`'s `Twist` subscriber. If either is ever switched to stamped,
  `kobuki_node` will silently stop receiving commands.
- **`configs/pdp.config.yaml`** is still valid, and Lyrical's `teleop_twist_joy`
  now ships its own `pdp.config.yaml`, so `joy_config:='pdp'` works without
  `config_filepath`. Note that the upstream one uses `enable_button: 2` where
  this repo's uses `4`.
- **`package.xml` format 2** is still accepted; no need to move to format 3.
- **`60-kobuki.rules`** is unchanged and still has to be installed by hand
  (`kobuki_core` does not install it):
  ```bash
  sudo cp src/turtlebot2_ros2/kobuki_core/60-kobuki.rules /etc/udev/rules.d/
  sudo udevadm control --reload-rules && sudo udevadm trigger
  ```

---

## 7. Complete list of modified files

```
 .gitmodules                                                             (+ kobuki_velocity_smoother)
 turtlebot2_ros2_demo/turtlebot2_ros2_demo.repos                         (+ velocity_smoother)
 cmd_vel_mux/CMakeLists.txt
 ecl_core/ecl_filesystem/include/ecl/filesystem/errors.hpp
 ecl_lite/ecl_io/include/ecl/io/sockets.hpp
 ecl_lite/ecl_time_lite/include/ecl/time_lite/errors.hpp
 kobuki_ros/kobuki_auto_docking/CMakeLists.txt
 kobuki_ros/kobuki_auto_docking/package.xml
 kobuki_ros/kobuki_auto_docking/include/kobuki_auto_docking/auto_docking_ros.hpp
 kobuki_ros/kobuki_auto_docking/src/auto_docking_ros.cpp
 kobuki_ros/kobuki_bumper2pc/CMakeLists.txt
 kobuki_ros/kobuki_bumper2pc/launch/kobuki_bumper2pc-launch.py
 kobuki_ros/kobuki_keyop/CMakeLists.txt
 kobuki_ros/kobuki_node/CMakeLists.txt
 kobuki_ros/kobuki_node/include/kobuki_node/kobuki_ros.hpp
 kobuki_ros/kobuki_node/src/kobuki_ros.cpp
 kobuki_ros/kobuki_node/src/odometry.cpp
 kobuki_ros/kobuki_random_walker/CMakeLists.txt
 kobuki_ros/kobuki_safety_controller/CMakeLists.txt
 kobuki_ros/kobuki_safety_controller/launch/safety_controller-composed-launch.py
 kobuki_ros/kobuki_safety_controller/launch/safety_controller-launch.py
 kobuki_velocity_smoother/launch/velocity_smoother-launch.py             (new submodule)
 kobuki_velocity_smoother/launch/velocity_smoother-composed-launch.py    (new submodule)
```

Outside the repo: `~/.colcon/defaults.yaml` gained
`-DCMAKE_POLICY_VERSION_MINIMUM=3.5`.

---

## 8. Verification performed

Clean `colcon build` (no warnings-as-errors, no failures) with both CMake 3.29.3
and CMake 4.2.3 — 45 packages.

Every launch file was started and checked for clean startup:

| launch | result |
|---|---|
| `kobuki_node kobuki_node-launch.py` | node up, polls `/dev/ttyUSB0` |
| `kobuki_node kobuki_node-composed-launch.py` | component loaded |
| `cmd_vel_mux cmd_vel_mux-launch.py` / `-composed-` | "CmdVelMux : (re)configured" |
| `kobuki_safety_controller safety_controller-launch.py` / `-composed-` | component loaded |
| `kobuki_bumper2pc kobuki_bumper2pc-launch.py` | pointcloud configured |
| `kobuki_auto_docking compact.launch.py` | component loaded |
| `kobuki_description robot_description.launch.py` | URDF published, joint_state_publisher got description |
| `kobuki_velocity_smoother velocity_smoother-launch.py` / `-composed-` | component loaded |

No Kobuki hardware was attached, so the driver's serial path
(`kobuki-version-info`, `kobuki-simple-keyop`, odometry, bumpers, docking) is
**not** covered by this. Those are the first things to check on the robot.
