# ROS2 Omni-Wheel Robot Simulation

A ROS2 Humble simulation of an omnidirectional mobile robot.

Supports **3-wheel** (120-degree) and **4-wheel** (X-configuration) omni-wheel variants.

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

## License

TODO
