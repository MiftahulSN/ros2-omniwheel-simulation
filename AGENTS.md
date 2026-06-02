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

### System Quirks

- `gnome-terminal` has snap/libc conflict — do NOT use terminal prefixes in launch files.
- Teleop uses `curses` (not `termios`/`xterm`), run manually via `ros2 run omni_controller omni_teleop.py`.

---

## Project Conventions

### Package Naming

All packages use `omni_` prefix.

### Build System

- All packages use `ament_cmake` (data-only packages use simple `install(DIRECTORY ...)` pattern).
- `package.xml` format 3.
- Build command: `colcon build` (no symlink-install needed, no generated messages)

### Launch File Patterns

Two patterns used:

1. **Simple pattern** (no runtime argument resolution):
   ```python
   def generate_launch_description():
       return LaunchDescription([
           DeclareLaunchArgument(...),
           Node(...),
       ])
   ```

2. **OpaqueFunction pattern** (when arguments need runtime resolution):
   ```python
   def launch_setup(context, *args, **kwargs):
       arg = context.launch_configurations['arg_name']
       return [node1, node2]

   def generate_launch_description():
       return LaunchDescription([
           DeclareLaunchArgument(...),
           OpaqueFunction(function=launch_setup),
       ])
   ```

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
│   └── description.launch.py           # Robot state publisher only
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
│   └── kinematics.cpp              # Omni kinematics + odometry node
├── scripts/
│   └── omni_teleop.py              # Curses teleop script
├── config/
│   ├── 3wheel.yaml                 # ros2_control: 3 velocity controllers
│   └── 4wheel.yaml                 # ros2_control: 4 velocity controllers
├── launch/
│   └── controllers.launch.py       # Controller spawner
└── CMakeLists.txt
```

### Kinematics Node (`kinematics.cpp`)

The core node that handles forward/inverse kinematics, odometry, and TF broadcasting.

**Algorithm:**
1. Build transform matrix `tM` (N x 3) mapping `(vx, vy, w)` to N wheel speeds
2. Compute pseudo-inverse `tMI` (2 x N) for odometry (only first 2 rows for x,y)
3. `cmd_vel` callback: multiply `tM * [vx, vy, w]` → wheel speeds → publish to each `wheelN_controller/commands`
4. `joint_states` callback: compute odometry via `rM * tMI * wheel_velocities * dt`
5. `imu` callback: extract yaw from IMU quaternion for rotation compensation

**Odometry:**
- Position: accumulated from wheel velocities with IMU-based rotation compensation
- Velocity: computed as `dp/dt` from wheel odometry
- Orientation: from IMU quaternion (yaw only)
- Publishes: `/odom` (nav_msgs/Odometry) + TF `odom → base_footprint`

**Key constants:**
- `WHEEL_RADIUS = 0.03`, `ROBOT_RADIUS = 0.088`
- Configured via `OMNI_ROBOT_MODEL` env var (set by launch file)

### Controller Config

Each wheel has its own `JointGroupVelocityController`:
- Joint name: `omni_wheel_joint_N`
- Topic: `wheelN_controller/commands` (Float64MultiArray)
- Update rate: 50Hz

### Teleop Script

- Run: `ros2 run omni_controller omni_teleop.py`
- Uses `curses` for key input
- Publishes `Twist` to `cmd_vel`

---

## Package: omni_gazebo

### Structure

```text
src/omni_gazebo/
├── launch/
│   └── gazebo.launch.py            # Full sim pipeline (OpaqueFunction)
├── config/
│   └── bridge.yaml                 # 7 GZ-to-ROS2 topic bridges
├── worlds/
│   ├── maze1.sdf
│   └── maze2.sdf
└── CMakeLists.txt
```

### Launch Pipeline (gazebo.launch.py)

1. Set `IGN_GAZEBO_RESOURCE_PATH` for mesh loading
2. `robot_state_publisher` with `use_sim_time: True`
3. `ros_gz_sim/gz_sim.launch.py` with world file (default: maze2)
4. `ros_gz_sim/create` to spawn robot at z=0.1m
5. `ros_gz_bridge` with bridge.yaml
6. `controller_manager/spawner` for `joint_state_broadcaster` + `wheelN_controller`s
7. `omni_controller/kinematics` node with `OMNI_ROBOT_MODEL` env var

### Launch Arguments

| Argument | Default | Choices | Description |
|---|---|---|---|
| `wheel_config` | `3wheel` | `3wheel`, `4wheel` | Wheel configuration |
| `world` | `maze2` | any | Gazebo world name (without .sdf) |

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
- Launch: `omni_bringup/slam_sim.launch.py`

---

## Package: omni_bringup

### Structure

```text
src/omni_bringup/
├── launch/
│   ├── nav_sim.launch.py           # Gazebo + Nav2 bringup (AMCL + planning)
│   └── slam_sim.launch.py          # Gazebo + SLAM Toolbox
└── CMakeLists.txt
```

Both launch files accept `wheel_config` and `world` arguments.

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
  │     └── omni_controller (config + kinematics node)
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
    → tM * [vx, vy, wz] → wheel speeds
      → wheelN_controller/commands (Float64MultiArray)
        → velocity_controllers/JointGroupVelocityController
          → gz_ros2_control/GazeboSimSystem
            → Gazebo simulation

joint_states + imu
  → omni_kinematics node
    → rM * tMI * wheel_vel * dt → position delta
      → accumulate pos_x, pos_y
      → publish /odom + TF (odom → base_footprint)
```

---

## How to Run the Full Simulation

```bash
# Terminal 1: Build and launch simulation
source /opt/ros/humble/setup.bash
cd /home/mift/Projects/Simulation/Omni-Wheel/ros2_ws
colcon build
source install/setup.bash
ros2 launch omni_gazebo gazebo.launch.py

# Terminal 2: Teleop (wait for simulation to load)
source /opt/ros/humble/setup.bash
source /home/mift/Projects/Simulation/Omni-Wheel/ros2_ws/install/setup.bash
ros2 run omni_controller omni_teleop.py
```

### With 4-wheel configuration

```bash
ros2 launch omni_gazebo gazebo.launch.py wheel_config:=4wheel
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
