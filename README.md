# OMNI-WHEEL ROBOT SIMULATION

Omnidirectional mobile robot simulation on **ROS2 Humble + Gazebo Fortress**.

Supports **3-wheel** (120° spacing) and **4-wheel** (X-configuration, 90° spacing) variants with teleop, SLAM mapping, and autonomous navigation.

> personal learning projects.

---

## 📋 Prerequisites

| Component | Version |
|---|---|
| ROS2 | Humble |
| Gazebo | Ignition Fortress 6 |
| ros2_control | 2.54+ |
| gz_ros2_control | 0.7+ |
| Nav2 | 1.1+ |
| SLAM Toolbox | 2.6+ |
| joy (optional) | 3.3+ |

---

## 🚀 Quick Start

```bash
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build
source install/setup.bash

# Launch simulation (teleop auto-detects joystick)
ros2 launch omni_gazebo gazebo.launch.py
```

---

## 🔨 Build

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

---

## 🎮 Usage

### Robot Model Visualization

```bash
ros2 launch omni_description description.launch.py
```

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |
| `rviz` | `true` | Launch RViz2 |

### Simulation + Teleop

```bash
ros2 launch omni_gazebo gazebo.launch.py
```

| Argument | Default | Choices | Description |
|---|---|---|---|
| `wheel_config` | `3wheel` | `3wheel`, `4wheel` | Wheel configuration |
| `world` | `maze2` | any | Gazebo world name (without `.sdf`) |
| `teleop` | `auto` | `auto`, `joy`, `keyboard` | Teleop mode |

### SLAM Mapping

```bash
ros2 launch omni_bringup slam_sim.launch.py
```

Accepts `wheel_config`, `world`, and `teleop` arguments.

### Autonomous Navigation

```bash
ros2 launch omni_bringup nav_sim.launch.py
```

Accepts `wheel_config`, `world`, and `teleop` arguments.

### Manual Teleop (without simulation)

```bash
ros2 run omni_controller teleop_keyboard.py
ros2 run omni_controller teleop_joy.py        # requires joy_node
```

---

## 🕹️ Teleop Controls

### Keyboard

| Key | Action | | Key | Action |
|---|---|---|---|---|
| `W` / `S` | Forward / Backward | | `Q` / `E` | Rotate left / right |
| `A` / `D` | Strafe left / right | | `Space` | Stop all |
| `C` / `Z` | Linear speed +/- | | `V` / `X` | Angular speed +/- |
| `Ctrl+C` | Quit | | | |

### Joystick

| Input | Action |
|---|---|
| Right stick pitch | Forward / backward |
| Right stick roll | Strafe left / right |
| Left stick roll | Rotate left / right |
| R1 | Increase linear speed |
| L1 | Decrease linear speed |
| R2 | Increase angular speed |
| L2 | Decrease angular speed |
| Start | Toggle enable (starts enabled) |
| Select | Respawn robot at origin |

---

## 🏗️ Architecture

```text
ros2_ws/
└── src/
    ├── omni_description/     # URDF/Xacro robot model, meshes, sensors
    ├── omni_controller/      # Kinematics node, teleop, ros2_control configs
    ├── omni_gazebo/          # Gazebo worlds, spawn, sensor bridges
    ├── omni_navigation/      # Nav2 + SLAM configs, maps, RViz
    └── omni_bringup/         # Top-level launch files
```

### Dependency Graph

```text
omni_bringup
  ├── omni_gazebo
  │     ├── omni_description
  │     └── omni_controller
  ├── omni_navigation
  ├── nav2_bringup
  └── slam_toolbox
```

### Control Pipeline

```text
cmd_vel → omni_kinematics → tM * [vx, vy, wz] → wheel speeds → gz_ros2_control → Gazebo

joint_states + imu → omni_kinematics → wheel odometry → /odom + TF (odom → base_footprint)
```

---

## 📦 Package Details

### omni_description

URDF/Xacro robot model with DRY design — shared macros in `urdf/common/` parameterized for both wheel variants.

**Sensors:**

| Sensor | Type | Rate | Details |
|---|---|---|---|
| IMU | Gazebo IMU | 100 Hz | Orientation + angular velocity |
| Camera | RGB | 30 Hz | 640×480 |
| Depth | Depth | 10 Hz | 320×240 |
| LiDAR | GPU LiDAR | 5 Hz | 360 samples, 10 m range |

**Physical constants:** wheel radius 0.03 m, robot radius 0.088 m, base mass 3.0 kg.

### omni_controller

**Kinematics node** (`kinematics.cpp`): OOP-based `OmniKinematics` class. Computes inverse kinematics via SVD pseudo-inverse of the wheel transform matrix. Fuses wheel odometry with IMU yaw for pose estimation.

**Teleop scripts:** OOP-based `TeleopKeyboard` and `TeleopJoy` classes with velocity ramping and configurable speed limits. Joystick teleop supports respawn via Gazebo's `set_pose` service.

**Controllers:** Per-wheel `JointGroupVelocityController` at 50 Hz.

### omni_gazebo

Spawns the full simulation pipeline: Gazebo Fortress + robot state publisher + sensor bridges + controller spawner + kinematics + teleop. Teleop auto-detects joystick via `joy_enumerate_devices`.

### omni_navigation

Data-only package with Nav2 and SLAM Toolbox configs. Nav2 uses DWB controller with omnidirectional movement enabled (`max_vel_y: 1.5`). SLAM Toolbox in online async mode with Ceres solver.

### omni_bringup

Top-level launch files composing Gazebo + Nav2 or Gazebo + SLAM. Passes all arguments through to `omni_gazebo`.

---

## 🔍 Debugging

```bash
ros2 control list_controllers
ros2 topic echo /cmd_vel
ros2 topic echo /odom
ros2 topic echo /scan
ros2 topic echo /joy
ros2 run tf2_tools view_frames
```

---

## 🙏 Acknowledgements

Big thanks to [YePeOn7/ros2_omni_robot_sim](https://github.com/YePeOn7/ros2_omni_robot_sim) 

Rewritten from scratch for ROS2 Humble + Gazebo Fortress with a different multi-package architecture.
