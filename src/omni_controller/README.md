# omni_controller

Kinematics node, teleop node, and ros2_control configs for the omni-wheel robot.

## Directory Structure

```
omni_controller/
├── config/
│   ├── 3wheel.yaml              # 3-wheel controller config
│   └── 4wheel.yaml              # 4-wheel controller config
├── launch/
│   └── controllers.launch.py
├── scripts/
│   └── omni_teleop.py           # Keyboard teleop (curses-based)
├── src/
│   └── kinematics.cpp           # Inverse kinematics + odometry
├── CMakeLists.txt
└── package.xml
```

## Nodes

### `kinematics` (C++)

Inverse kinematics and odometry using Eigen3 SVD pseudo-inverse.

**Environment Variable:**

| Variable | Default | Description |
|---|---|---|
| `OMNI_ROBOT_MODEL` | `3wheel` | Robot variant (`3wheel` or `4wheel`) |

**Robot Constants:**

| Constant | Value |
|---|---|
| `WHEEL_RADIUS` | 0.03 m |
| `ROBOT_RADIUS` | 0.088 m |
| Heading offset (3wheel) | 0 deg |
| Heading offset (4wheel) | -45 deg |

**Subscriptions:**

| Topic | Type | Description |
|---|---|---|
| `cmd_vel` | `geometry_msgs/Twist` | Desired velocity (vx, vy, omega) |
| `joint_states` | `sensor_msgs/JointState` | Wheel encoder readings |
| `imu` | `sensor_msgs/Imu` | IMU orientation |

**Publications:**

| Topic | Type | Description |
|---|---|---|
| `wheel{N}_controller/commands` | `std_msgs/Float64MultiArray` | Per-wheel velocity command |
| `odom` | `nav_msgs/Odometry` | Robot odometry |

**TF:**

| Parent | Child |
|---|---|
| `odom` | `base_footprint` |

**Algorithm:**

1. Builds Nx3 transform matrix from wheel angles and heading offset
2. SVD pseudo-inverse maps `cmd_vel -> wheel speeds` (inverse kinematics)
3. SVD pseudo-inverse maps `wheel speeds -> robot velocity` (forward kinematics)
4. Integrates pose from wheel odometry, fuses IMU yaw for orientation
5. Publishes `odom` + `odom->base_footprint` TF at encoder rate

---

### `omni_teleop.py` (Python)

Keyboard teleoperation with **joystick-style** hold-to-move behavior.

Uses `curses` for clean terminal rendering (immune to ROS 2 log interference).

**Publications:**

| Topic | Type | Rate |
|---|---|---|
| `cmd_vel` | `geometry_msgs/Twist` | ~50 Hz |

**Key Mapping:**

| Key | Action |
|---|---|
| `W` / `S` | Forward / Backward |
| `A` / `D` | Strafe left / Strafe right |
| `Q` / `E` | Rotate left / Rotate right |
| `C` / `Z` | Increase / Decrease linear speed (step 0.1) |
| `V` / `X` | Increase / Decrease angular speed (step 0.2) |
| `Space` | Emergency stop |
| `Ctrl+C` | Quit |

**Speed Control:**

| Parameter | Default | Range |
|---|---|---|
| Linear speed | 0.5 m/s | 0.1 - 2.0 |
| Angular speed | 1.0 rad/s | 0.2 - 4.0 |

**Behavior:**

- Hold movement keys for continuous motion (auto-repeat based)
- 500ms timeout detects key release (no key-up events in terminals)
- Velocity ramping at 8.0 units/s for smooth acceleration/deceleration
- Hold multiple keys for combined motion (e.g., `W`+`A` = diagonal)
- ROS 2 logs suppressed to prevent terminal corruption

## Controller Configs

`config/{3wheel,4wheel}.yaml` define the ros2_control controllers:

| Controller | Type | Joint |
|---|---|---|
| `joint_state_broadcaster` | `JointStateBroadcaster` | All wheel joints |
| `wheel{N}_controller` | `JointGroupVelocityController` | `omni_wheel_joint_N` |

Update rate: **50 Hz**

## Launch

### `controllers.launch.py`

Spawns ros2_control controllers (called internally by `omni_gazebo`).

```bash
ros2 launch omni_controller controllers.launch.py
ros2 launch omni_controller controllers.launch.py wheel_config:=4wheel
```

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |

## Usage

```bash
# Teleop (run in a separate terminal from simulation)
ros2 run omni_controller omni_teleop.py
```
