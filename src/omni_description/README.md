# omni_description

URDF description, meshes, and RViz config for the omni-wheel robot.

Supports **3-wheel** and **4-wheel** configurations via xacro macros.

## Directory Structure

```
omni_description/
├── launch/
│   └── description.launch.py
├── meshes/
│   ├── 3wheel/                  # 3-wheel DAE/STL meshes
│   └── 4wheel/                  # 4-wheel DAE/STL meshes
├── rviz/
│   └── description.rviz
└── urdf/
    ├── 3wheel/                  # 3-wheel robot (base_link, ros2_control)
    ├── 4wheel/                  # 4-wheel robot (base_link, ros2_control)
    └── common/                  # Shared xacro macros
        ├── sensors/
        │   ├── camera.urdf.xacro
        │   ├── lidar.urdf.xacro
        │   └── imu.urdf.xacro
        ├── omni_wheel.urdf.xacro
        ├── roller.urdf.xacro
        ├── heading.urdf.xacro
        └── gazebo_plugins.urdf.xacro
```

## URDF Architecture

### Common Macros (`urdf/common/`)

| File | Description |
|---|---|
| `omni_wheel.urdf.xacro` | Single omni wheel with 6 rollers (continuous joint) |
| `roller.urdf.xacro` | Single roller (continuous joint, friction configured) |
| `heading.urdf.xacro` | Red arrow indicator for robot heading |
| `gazebo_plugins.urdf.xacro` | Gazebo system plugins (sensors, IMU, ros2_control) |
| `sensors/camera.urdf.xacro` | RGB + depth camera (640x480, 320x240) |
| `sensors/lidar.urdf.xacro` | GPU lidar (360 samples, 10m range, 5Hz) |
| `sensors/imu.urdf.xacro` | IMU sensor (50Hz) |

### Wheel Variants

| Variant | Wheels | Positions |
|---|---|---|
| `3wheel` | 3 wheels | 120-degree spacing |
| `4wheel` | 4 wheels | 90-degree spacing |

### Sensors (both variants)

| Sensor | Position (x, y, z) | Topic |
|---|---|---|
| Camera | `(0.104, 0, 0.063)` | `/camera`, `/depth` |
| Lidar | `(0, 0, 0.101)` | `/scan` |
| IMU | `(0, 0, 0)` | `/imu` |

### Gazebo Plugins

| Plugin | Purpose |
|---|---|
| `libignition-gazebo-sensors-system.so` | Sensor rendering (ogre2) |
| `libignition-gazebo-imu-system.so` | IMU system |
| `libgz_ros2_control-system.so` | ros2_control bridge |

### Hardware Interface

| Property | Value |
|---|---|
| Plugin | `gz_ros2_control/GazeboSimSystem` |
| Command interface | `velocity` (per joint, range: -10 to 10) |
| State interfaces | `position`, `velocity` |

## Launch

### `description.launch.py`

Publishes the robot description and optionally opens RViz.

```bash
ros2 launch omni_description description.launch.py
ros2 launch omni_description description.launch.py wheel_config:=4wheel rviz:=false
```

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |
| `rviz` | `true` | Launch RViz2 |
