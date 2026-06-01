# ROS2 Omni-Wheel Robot Simulation

A ROS2 Humble simulation of an omnidirectional mobile robot.

Supports **3-wheel** (120-degree) and **4-wheel** (X-configuration) omni-wheel variants.

> **Note**: This project is a personal learning and educational exercise. It was built from scratch to understand the full ROS2 simulation stack (URDF, Gazebo, ros2_control, SLAM, Nav2) by studying and re-implementing concepts from the reference listed below. It is not intended for production use.

---

## Prerequisites

| Component | Version |
|---|---|
| ROS2 | Humble |
| Gazebo | Ignition Fortress 6 |
| ros2_control | 2.54+ |
| gz_ros2_control | 0.7+ |
| SLAM Toolbox | 2.6+ |
| Nav2 | 1.1+ |

---

## Architecture

```text
ros2_ws/
└── src/
    ├── omni_description/     # Robot model (URDF/Xacro, meshes, RViz)
    ├── omni_controller/      # Controller configs & omni kinematics node
    ├── omni_gazebo/          # Gazebo worlds, spawn, sensor bridges
    ├── omni_navigation/      # SLAM Toolbox & Nav2 configs
    └── omni_bringup/         # Top-level launch orchestration
```

### Package Responsibilities

| Package | Role |
|---|---|
| `omni_description` | URDF/Xacro robot model, meshes, shared sensor macros |
| `omni_controller` | ros2_control configs, omni-directional kinematics node |
| `omni_gazebo` | Gazebo world files, robot spawning, sensor topic bridges |
| `omni_navigation` | SLAM Toolbox mapping, Nav2 autonomous navigation |
| `omni_bringup` | Top-level launch files composing the full stack |

### Dependency Graph

```text
                        omni_bringup
        |                   |                   |
        v                   v                   v
    omni_gazebo         omni_controller     omni_navigation
        |                   |                   |
        v                   v                   v
    omni_description    omni_description    omni_description
```

### URDF Structure (DRY Design)

Shared xacro macros live in `urdf/common/` and are parameterized so both wheel variants reuse the same sensor, roller, and wheel definitions:

```text
omni_description/urdf/
├── common/                 # Shared macros (lidar, camera, imu, roller, wheel)
│   └── sensors/
├── 3wheel/                 # 3-wheel variant (base_link positions, 3-joint ros2_control)
└── 4wheel/                 # 4-wheel variant (base_link positions, 4-joint ros2_control)
```

---

## Build

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

## Usage

```bash
# Visualize robot model in RViz
ros2 launch omni_description description.launch.py wheel_config:=3wheel

# Launch Gazebo simulation
ros2 launch omni_bringup sim.launch.py wheel_config:=3wheel

# SLAM mapping
ros2 launch omni_bringup slam.launch.py wheel_config:=3wheel

# Autonomous navigation
ros2 launch omni_bringup navigation.launch.py wheel_config:=3wheel
```

Replace `3wheel` with `4wheel` for the 4-wheel variant.

### Teleop (run in a separate terminal)

```bash
ros2 run omni_controller omni_teleop.py

# Or via launch
ros2 launch omni_bringup teleop.launch.py
```

| Key | Action | | Key | Action |
|---|---|---|---|---|
| `W` / `S` | Forward / Backward | | `Q` / `E` | Rotate left / right |
| `A` / `D` | Strafe left / right | | `Space` | Stop all |
| `C` / `Z` | Linear speed +/- | | `V` / `X` | Angular speed +/- |

---

## Pipeline

```text
Robot Description →  RViz Visualization  →  Gazebo Simulation
      ↓                                       ↓
    URDF/Xacro                              Sensor Integration
                                              ↓
                                            Robot Control (omni kinematics)
                                              ↓
                                            SLAM Mapping (SLAM Toolbox)
                                              ↓
                                            Nav2 Navigation (MPPI Omni)
                                              ↓
                                            Autonomous Omnidirectional Robot
```

---

## Outcome

A fully functional ROS2 simulation stack where an omnidirectional robot can:

- Move in any direction (strafe, rotate, diagonal)
- Simulate realistic physics in Gazebo Fortress
- Sense the environment (LiDAR, IMU, RGB-D camera)
- Build occupancy grid maps using SLAM Toolbox
- Navigate autonomously using Nav2 with holonomic planning

---

## Acknowledgements

This project would not have been possible without the following reference:

### [YePeOn7/ros2_omni_robot_sim](https://github.com/YePeOn7/ros2_omni_robot_sim)

A huge thank you to **[YePeOn7](https://github.com/YePeOn7)** for creating an excellent omnidirectional robot Gazebo simulation with ROS2. Their project was the primary reference and inspiration for this entire learning exercise. Specifically, the following concepts and techniques were learned and adapted from their work:

- Omnidirectional kinematics (forward/inverse via matrix transform + SVD pseudo-inverse)
- URDF/Xacro robot modeling with shared sensor macros
- Gazebo Ignition simulation integration (`gz_ros2_control`, sensor bridges)
- ros2_control hardware interface setup (velocity controllers)
- SLAM Toolbox mapping pipeline
- Nav2 autonomous navigation configuration

Their original repo supports 3 to 6 wheel variants on **ROS2 Jazzy + Gazebo Harmonic**, while this project was rewritten from the ground up for **ROS2 Humble + Gazebo Fortress** with a different multi-package architecture and some modifications along the way.

---

## License

MIT
