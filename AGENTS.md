# AGENTS.md - Omni-Wheel Project Knowledge Base

This document serves as a knowledge transfer reference for the Omni-Wheel Robot simulation project.

---

## Project Overview

3-wheel / 4-wheel omnidirectional robot simulation using ROS2 Humble + Gazebo Fortress (Ignition Gazebo 6).
Workspace: `/home/mift/Projects/Simulation/Omni-Wheel/ros2_ws`
Based on: [YePeOn7/ros2_omni_robot_sim](https://github.com/YePeOn7/ros2_omni_robot_sim)

---

## System Environment

| Component | Installed Package | Version |
|---|---|---|
| OS | Ubuntu | 22.04.5 LTS |
| ROS2 | `ros-humble-ros-base` | 0.10.0 |
| Gazebo Sim | `libignition-gazebo6` | 6.16.0 (Fortress) |
| ros2_control | `ros-humble-ros2-control` | 2.54.0 |
| gz_ros2_control | `ros-humble-gz-ros2-control` | 0.7.19 |
| ros_gz_sim | `ros-humble-ros-gz-sim` | 0.244.24 |
| Nav2 | `ros-humble-navigation2` | 1.1.20 |
| SLAM Toolbox | `ros-humble-slam-toolbox` | 2.6.10 |
| Joy | `ros-humble-joy` | 3.3.0 |

### Key Notes on Gazebo Setup

- Uses **Ignition Gazebo 6 (Fortress)**, NOT Gazebo Classic 11.
- Hardware interface plugin: `gz_ros2_control/GazeboSimSystem`
- Gazebo system plugins in URDF use `gz` naming:
  - `libgz-sim-sensors-system.so` (`gz::sim::systems::Sensors`)
  - `libgz-sim-imu-system.so` (`gz::sim::systems::Imu`)
  - `libgz_ros2_control-system.so`
- Sensor bridge: `ros_gz_bridge` (config via YAML bridge files)
- Robot spawning: `ros_gz_sim/create`
- Gazebo launch: `ros_gz_sim/gz_sim.launch.py`
- Sensor format: SDF-style `<gazebo><sensor>` tags in URDF
- Gazebo CLI uses `ign` (not `gz`) for service calls in Fortress: `ign service -s /world/<name>/set_pose --reqtype ignition.msgs.Pose ...`
- SDF world name (inside `<world name="...">`) may differ from filename — parsed at launch time

### System Quirks

- `gnome-terminal` has snap/libc conflict — do NOT use terminal prefixes in launch files.
- Teleop has two modes: keyboard (`teleop_keyboard.py`, curses-based) and joystick (`teleop_joy.py`). Auto-detected via `joy_enumerate_devices` in launch files. Override with `teleop:=keyboard` or `teleop:=joy`.

---

## Project Conventions

### Package Naming

All packages use `omni_` prefix.

### Build System

- All packages use `ament_cmake` (data-only packages use simple `install(DIRECTORY ...)` pattern).
- `package.xml` format 3.
- Build command: `colcon build` (no symlink-install needed, no generated messages)

### Code Style

- Python: OOP-based classes, `snake_case` methods and variables
- C++: OOP-based classes with `snake_case_` trailing underscore for private members, `kCamelCase` for constants
- All teleop scripts use `TeleopXxx` class pattern with `run()` / `stop()` lifecycle methods
- `kinematics.cpp` uses `OmniKinematics` class extending `rclcpp::Node`

### Launch File Pattern

All launch files use a **class-based OOP template** with `OpaqueFunction` for runtime argument resolution:

```python
class XxxConfig:
    def __init__(self):
        # resolve package share directories
    def _get_config_paths(self) -> dict:
        # return dict of config file paths

class XxxNodeFactory:
    def __init__(self, config: XxxConfig):
        self.config = config
    def _load_urdf_content(self, urdf_path: str) -> str:
        return Command(['xacro ', urdf_path])
    def create_launch_arguments(self) -> list:
        return [DeclareLaunchArgument(...), ...]
    def create_core_nodes(self, context) -> list:
        # use context.launch_configurations for runtime args
        return [node1, node2, ...]

def generate_launch_description():
    config = XxxConfig()
    factory = XxxNodeFactory(config)
    launch_entities = list(factory.create_launch_arguments())
    launch_entities.append(OpaqueFunction(function=factory.create_core_nodes))
    return LaunchDescription(launch_entities)
```

Named variants per package: `DescriptionConfig/DescriptionNodeFactory`, `ControllerConfig/ControllerNodeFactory`, `GazeboConfig/GazeboNodeFactory`, `NavSimConfig/NavSimNodeFactory`, `SlamSimConfig/SlamSimNodeFactory`.

### URDF/Xacro Conventions

- Xacro includes use `$(find omni_description)/urdf/...` syntax.
- Mesh references use `package://omni_description/meshes/...` syntax.
- Sensor macros accept `suffix parent xyz rpy` params.
- `${mesh_prefix}` property set in `robot.urdf.xacro` for per-variant mesh selection.
- Sensor Gazebo tags use SDF format: `<gazebo reference="link_name"><sensor type="..." name="...">`.

### Wheel Configuration

- Two configs: `3wheel` (3 omnidirectional wheels at 120deg spacing) and `4wheel` (4 wheels at 90deg spacing, -45deg heading offset)
- Selected via `wheel_config` launch argument (default: `3wheel`)
- Environment variable `OMNI_ROBOT_MODEL` set by launch file for kinematics node

---

## Package: omni_description

### Structure

```text
src/omni_description/
├── meshes/
│   ├── 3wheel/    # base_link.dae, base_link.stl, omni_frame.stl, roller.stl, camera.stl
│   └── 4wheel/    # same files, different geometry
├── urdf/
│   ├── common/
│   │   ├── gazebo_plugins.urdf.xacro   # gz-sim system plugins + gz_ros2_control
│   │   ├── heading.urdf.xacro          # Red arrow heading indicator
│   │   ├── omni_wheel.urdf.xacro       # Wheel link + joint + 6 rollers
│   │   ├── roller.urdf.xacro           # Single roller sub-wheel
│   │   └── sensors/
│   │       ├── camera.urdf.xacro       # RGB + depth camera (SDF format)
│   │       ├── imu.urdf.xacro          # IMU sensor
│   │       └── lidar.urdf.xacro        # GPU LiDAR (360 samples, 10m range)
│   ├── 3wheel/
│   │   ├── robot.urdf.xacro            # Top-level 3-wheel robot
│   │   ├── base_link.urdf.xacro        # 3 wheels + sensors + heading
│   │   └── ros2_control.urdf.xacro     # 3 velocity joints
│   └── 4wheel/
│       ├── robot.urdf.xacro            # Top-level 4-wheel robot
│       ├── base_link.urdf.xacro        # 4 wheels + sensors + heading
│       └── ros2_control.urdf.xacro     # 4 velocity joints
├── launch/
│   └── description.launch.py           # Class-based: DescriptionConfig + DescriptionNodeFactory
└── rviz/
    └── description.rviz
```

### Physical Constants

| Parameter | Value |
|---|---|
| Wheel radius | 0.03 m |
| Robot radius | 0.088 m |
| Base mass | 3.0 kg |
| Wheel mass | 0.5 kg |
| Camera mass | 0.5 kg |
| Heading offset (3wheel) | 0 deg |
| Heading offset (4wheel) | -45 deg |

### Sensors

| Sensor | Link | Type | Rate | Details |
|---|---|---|---|---|
| IMU | `imu_link_1` (base_link) | IMU | 100Hz | Gazebo IMU system |
| Camera | `camera_link_1` (base_link) | RGB | 30Hz | 640x480, HFOV 1.5 |
| Depth | `camera_link_1` (base_link) | Depth | 10Hz | 320x240, HFOV 1.5 |
| LiDAR | `lidar_link_1` (base_link) | GPU LiDAR | 5Hz | 360 samples, 360deg, 10m range |

---

## Package: omni_controller

### Structure

```text
src/omni_controller/
├── src/
│   └── kinematics.cpp              # OmniKinematics class (OOP-based)
├── scripts/
│   ├── teleop_keyboard.py          # TeleopKeyboard class (curses-based)
│   └── teleop_joy.py               # TeleopJoy class (joystick)
├── config/
│   ├── 3wheel.yaml                 # ros2_control: 3 velocity controllers
│   ├── 4wheel.yaml                 # ros2_control: 4 velocity controllers
│   └── joystick.yaml               # Joystick axis/button mapping
├── launch/
│   └── controllers.launch.py       # Class-based: ControllerConfig + ControllerNodeFactory
└── CMakeLists.txt
```

### Kinematics Node (`kinematics.cpp`)

OOP-based `OmniKinematics` class extending `rclcpp::Node`.

**Algorithm:**
1. Build transform matrix (N x 3) mapping `(vx, vy, w)` to N wheel speeds
2. Compute SVD pseudo-inverse, extract first 2 rows for odometry
3. `cmd_vel` callback: `transform_matrix * [vx, vy, w]` → wheel speeds → publish
4. `joint_state` callback: `rotation * odom_matrix * wheel_vel * dt` → accumulate position
5. `imu` callback: extract yaw from quaternion for rotation compensation

**Key design:**
- Robot config stored in `kRobotModels` struct map (not global variables)
- Constants as `static constexpr` class members: `kWheelRadius = 0.03`, `kRobotRadius = 0.088`
- Configured via `OMNI_ROBOT_MODEL` env var (set by launch file)
- Publishes: `/odom` (nav_msgs/Odometry) + TF `odom → base_footprint`

### Controller Config

Each wheel has its own `JointGroupVelocityController`:
- Joint name: `omni_wheel_joint_N`
- Topic: `wheelN_controller/commands` (Float64MultiArray)
- Update rate: 50Hz

### Teleop Scripts

Both are OOP-based classes with velocity ramping.

**TeleopKeyboard:**
- `TeleopKeyboard(node)` class with `_loop()`, `_update_velocity()`, `_handle_key()`, `_draw_speed()` methods
- Uses `curses` for terminal rendering
- WASD + QE layout, speed adjustable with C/Z/V/X keys

**TeleopJoy:**
- `TeleopJoy(node)` class with `_joy_callback()`, `_handle_buttons()`, `_update_velocity()`, `_respawn()`, `_compute_dt()` methods
- Subscribes to `joy` topic, publishes `cmd_vel`
- Auto-detects joystick via `joy_enumerate_devices` in launch files
- Override with `teleop:=keyboard` or `teleop:=joy` launch argument
- Parameters: `world` (for respawn), `spawn_z` (default 0.1)

**Joystick mapping** (DragonRise Inc. Generic USB Joystick):

| Input | Index | Action |
|---|---|---|
| Left stick roll | axis 0 | Rotate left / right |
| Right stick pitch | axis 3 | Forward / backward |
| Right stick roll | axis 2 | Strafe left / right |
| R1 | btn 5 | Increase linear speed |
| L1 | btn 4 | Decrease linear speed |
| R2 | btn 7 | Increase angular speed |
| L2 | btn 6 | Decrease angular speed |
| Start | btn 9 | Toggle enable (starts enabled) |
| Select | btn 8 | Respawn at origin via `ign service` |

**Config:** `config/joystick.yaml`

---

## Package: omni_gazebo

### Structure

```text
src/omni_gazebo/
├── launch/
│   └── gazebo.launch.py            # Class-based: GazeboConfig + GazeboNodeFactory
├── config/
│   └── bridge.yaml                 # 7 GZ-to-ROS2 topic bridges
├── worlds/
│   ├── maze1.sdf                   # World name: "default"
│   └── maze2.sdf                   # World name: "simple_world"
└── CMakeLists.txt
```

### Launch Pipeline (gazebo.launch.py)

`GazeboConfig` resolves package paths, parses SDF world name, provides xacro/bridge paths.
`GazeboNodeFactory` creates nodes via private `_create_*` methods:

1. `_create_env_setup()` — set `IGN_GAZEBO_RESOURCE_PATH`
2. `_create_robot_state_publisher()` — URDF from xacro
3. `_create_gazebo()` — `ros_gz_sim/gz_sim.launch.py`
4. `_create_spawn_robot()` — `ros_gz_sim/create` at z=0.1m
5. `_create_bridge()` — `ros_gz_bridge` with bridge.yaml
6. `_create_controller_spawner()` — joint_state_broadcaster + wheel controllers
7. `_create_kinematics()` — omni kinematics node
8. `_create_teleop_nodes()` — auto-detect or override joystick/keyboard

### Launch Arguments

| Argument | Default | Choices | Description |
|---|---|---|---|
| `wheel_config` | `3wheel` | `3wheel`, `4wheel` | Wheel configuration |
| `world` | `maze2` | any | Gazebo world name (without .sdf) |
| `teleop` | `auto` | `auto`, `joy`, `keyboard` | Teleop mode |

### Sensor Bridge Topics

| GZ Topic | ROS2 Topic | GZ Type | ROS2 Type |
|---|---|---|---|
| `clock` | `clock` | `gz.msgs.Clock` | `rosgraph_msgs/msg/Clock` |
| `/imu` | `/imu` | `gz.msgs.IMU` | `sensor_msgs/msg/Imu` |
| `/scan` | `/scan` | `gz.msgs.LaserScan` | `sensor_msgs/msg/LaserScan` |
| `/camera` | `/camera` | `gz.msgs.Image` | `sensor_msgs/msg/Image` |
| `/camera_info` | `/camera_info` | `gz.msgs.CameraInfo` | `sensor_msgs/msg/CameraInfo` |
| `/depth` | `/depth` | `gz.msgs.Image` | `sensor_msgs/msg/Image` |
| `/depth/camera_info` | `/depth/camera_info` | `gz.msgs.CameraInfo` | `sensor_msgs/msg/CameraInfo` |

---

## Package: omni_navigation

### Structure

```text
src/omni_navigation/
├── config/
│   ├── nav2_params.yaml                # Nav2 parameters (DWB controller)
│   └── slam_params.yaml                # SLAM Toolbox online async parameters
├── maps/
│   ├── maze1.pgm + maze1.yaml
│   └── maze2.pgm + maze2.yaml
├── rviz/
│   ├── navigation.rviz
│   └── slam.rviz
└── CMakeLists.txt
```

Data-only package (no launch files, no compiled targets). Config and maps are consumed by `omni_bringup`.

### Nav2 Configuration

- **AMCL**: `OmniMotionModel`, `base_footprint` frame
- **Controller**: DWB Local Planner with **omnidirectional movement enabled**
  - `max_vel_x: 1.5`, `max_vel_y: 1.5`, `max_vel_theta: 2.0`
  - `vx_samples: 10`, `vy_samples: 10`, `vtheta_samples: 20`
  - Critics: RotateToGoal, Oscillation, BaseObstacle, PathDist, GoalAlign, GoalDist, PathAlign
- **Planner**: Navfn (Dijkstra)
- **Costmap**: Robot radius 0.1m, inflation 0.3m, LaserScan obstacle/voxel layers
- **Frames**: `odom` (local), `map` (global), `base_footprint` (robot)

### SLAM

- Uses SLAM Toolbox online async mode with `slam_params.yaml`
- Config: Ceres solver, 0.05m resolution, loop closing enabled

---

## Package: omni_bringup

### Structure

```text
src/omni_bringup/
├── launch/
│   ├── nav_sim.launch.py           # Class-based: NavSimConfig + NavSimNodeFactory
│   └── slam_sim.launch.py          # Class-based: SlamSimConfig + SlamSimNodeFactory
└── CMakeLists.txt
```

Both launch files accept `wheel_config`, `world`, and `teleop` arguments. They include `omni_gazebo` and add Nav2 or SLAM respectively.

---

## Architecture

```text
ros2_ws/
└── src/
    ├── omni_description/    # URDF/Xacro, meshes, sensors, ros2_control
    ├── omni_controller/     # Kinematics node + velocity controllers + teleop
    ├── omni_gazebo/         # Gazebo worlds, spawn, sensor bridges, controller spawner
    ├── omni_navigation/     # Nav2 + SLAM config, maps, RViz
    └── omni_bringup/        # Top-level launch (nav_sim, slam_sim)
```

### Dependency Graph

```text
omni_bringup
  ├── omni_gazebo
  │     ├── omni_description (URDF)
  │     ├── omni_controller (config + kinematics node)
  │     └── joy (joystick driver)
  ├── omni_navigation (config + maps + rviz)
  ├── nav2_bringup
  └── slam_toolbox

omni_controller
  └── omni_description (URDF for ros2_control hardware interface)
```

---

## Control Pipeline

```text
cmd_vel (Twist)
  → omni_kinematics node
    → transform_matrix * [vx, vy, wz] → wheel speeds
      → wheelN_controller/commands (Float64MultiArray)
        → velocity_controllers/JointGroupVelocityController
          → gz_ros2_control/GazeboSimSystem
            → Gazebo simulation

joint_states + imu
  → omni_kinematics node
    → rotation * odom_matrix * wheel_vel * dt → position delta
      → accumulate pos_x, pos_y
      → publish /odom + TF (odom → base_footprint)
```

---

## How to Run the Full Simulation

```bash
# Build and launch simulation (teleop auto-detected)
source /opt/ros/humble/setup.bash
cd /home/mift/Projects/Simulation/Omni-Wheel/ros2_ws
colcon build
source install/setup.bash
ros2 launch omni_gazebo gazebo.launch.py

# Force keyboard teleop:
ros2 launch omni_gazebo gazebo.launch.py teleop:=keyboard

# Force joystick teleop:
ros2 launch omni_gazebo gazebo.launch.py teleop:=joy

# 4-wheel configuration:
ros2 launch omni_gazebo gazebo.launch.py wheel_config:=4wheel
```

### Manual teleop (without simulation launch)

```bash
ros2 run omni_controller teleop_keyboard.py
ros2 run omni_controller teleop_joy.py
```

### SLAM mapping

```bash
ros2 launch omni_bringup slam_sim.launch.py
```

### Navigation with existing map

```bash
ros2 launch omni_bringup nav_sim.launch.py
```

### Useful debugging commands

```bash
ros2 control list_controllers
ros2 topic echo /joint_states
ros2 topic echo /odom
ros2 topic echo /scan
ros2 topic echo /joy
ros2 run tf2_tools view_frames
```

---

## Code Review Fixes Applied

### B1: Dead code removed from kinematics.cpp

- Removed unused `mOd[2][3]` matrix (was computed but never referenced)
- Fixed `vx`/`vy` always being 0 — now computed as `dp/dt` from actual wheel odometry
- Files: `src/omni_controller/src/kinematics.cpp`

### B2: Y-axis movement enabled in Nav2 params

- Changed `min_vel_y: 0.0` → `min_vel_y: -1.5`
- Changed `max_vel_y: 0.0` → `max_vel_y: 1.5`
- Changed `acc_lim_y: 0.0` → `acc_lim_y: 1.5`
- Changed `decel_lim_y: 0.0` → `decel_lim_y: -1.5`
- Changed `vy_samples: 0` → `vy_samples: 10`
- Changed `min_y_velocity_threshold: 0.5` → `min_y_velocity_threshold: 0.001`
- Files: `src/omni_navigation/config/nav2_params.yaml`

### B3: Consistent gz.msgs naming in bridge.yaml and gazebo_plugins

- Standardized all `ignition.msgs.*` → `gz.msgs.*` in bridge.yaml
- Updated `libignition-gazebo-*-system.so` → `libgz-sim-*-system.so` in gazebo_plugins.urdf.xacro
- Updated `ignition::gazebo::systems::*` → `gz::sim::systems::*` in gazebo_plugins.urdf.xacro
- Files: `src/omni_gazebo/config/bridge.yaml`, `src/omni_description/urdf/common/gazebo_plugins.urdf.xacro`

### Verified NOT bugs

- **B4**: Camera/lidar mesh files exist for both 3wheel and 4wheel configs; lidar uses primitive geometry (no mesh needed)
- **B5**: 4wheel base_link.urdf.xacro already includes heading.urdf.xacro and `heading_indicator` macro

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Joint command interface | `velocity` | Simple omni drive: kinematics outputs wheel speeds directly |
| Controller type | `JointGroupVelocityController` per wheel | Individual wheel velocity control |
| Odometry source | Custom (kinematics node) | Uses wheel encoders + IMU, not ros2_control odometry |
| Nav2 motion model | OmniMotionModel | Omnidirectional robot can strafe |
| Nav2 controller | DWB with Y-axis enabled | Allows lateral movement in path planning |
| Bridge msg format | `gz.msgs.*` (not `ignition.msgs.*`) | Fortress supports both; `gz` is the current standard |
| Gazebo CLI | `ign` for service calls | Fortress `gz` CLI returns "Invalid arguments" for service calls |
| Teleop integration | Auto-detect via `joy_enumerate_devices` | Seamless UX: plug in joystick and it works |
| Launch file pattern | Class-based OOP with Config + NodeFactory | Separation of config resolution from node creation |
| Code style | OOP-based classes throughout | Consistent pattern across Python scripts, C++ node, and launch files |
