# omni_gazebo

Gazebo Fortress simulation launch, worlds, and ROS2-Gazebo bridge config.

Launches the full simulation pipeline: Gazebo, robot spawning, controllers, kinematics, and sensor bridges.

## Directory Structure

```
omni_gazebo/
├── config/
│   └── bridge.yaml              # Gazebo-to-ROS2 topic bridge
├── launch/
│   └── gazebo.launch.py
├── worlds/
│   ├── maze1.sdf                # Complex maze (2.5m tall walls)
│   └── maze2.sdf                # Simpler maze (0.3m tall walls)
├── CMakeLists.txt
└── package.xml
```

## Launch

### `gazebo.launch.py`

Launches the complete simulation.

```bash
ros2 launch omni_gazebo gazebo.launch.py
ros2 launch omni_gazebo gazebo.launch.py wheel_config:=4wheel world:=maze1
```

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |
| `world` | `maze2` | World name (matches `worlds/<name>.sdf`) |

**What it launches (in order):**

| Step | Node/Action | Description |
|---|---|---|
| 1 | `SetEnvironmentVariable` | Sets `IGN_GAZEBO_RESOURCE_PATH` for mesh loading |
| 2 | `robot_state_publisher` | Publishes URDF (use_sim_time=True) |
| 3 | `ros_gz_sim/gz_sim.launch.py` | Starts Gazebo with world file |
| 4 | `ros_gz_sim/create` | Spawns robot at z=0.1 |
| 5 | `ros_gz_bridge` | Bridges Gazebo topics to ROS2 |
| 6 | `controller_manager/spawner` | Spawns all controllers |
| 7 | `kinematics` | Kinematics node (OMNI_ROBOT_MODEL=wheel_config) |

## Topic Bridge

`config/bridge.yaml` maps Gazebo topics to ROS2:

| ROS2 Topic | Gazebo Topic | Type |
|---|---|---|
| `clock` | `clock` | `rosgraph_msgs/Clock` |
| `/imu` | `/imu` | `sensor_msgs/Imu` |
| `/scan` | `/scan` | `sensor_msgs/LaserScan` |
| `/camera` | `/camera` | `sensor_msgs/Image` |
| `/camera_info` | `/camera_info` | `sensor_msgs/CameraInfo` |
| `/depth` | `/depth` | `sensor_msgs/Image` |
| `/depth/camera_info` | `/depth/camera_info` | `sensor_msgs/CameraInfo` |

## Worlds

| World | Description |
|---|---|
| `maze1` | Complex maze with 2.5m tall walls, 12 wall segments |
| `maze2` | Simpler maze with 0.3m tall walls, 15 wall segments |

## Dependencies

| Package | Purpose |
|---|---|
| `omni_description` | Robot URDF and meshes |
| `omni_controller` | Kinematics node and controller configs |
| `ros_gz_sim` | Gazebo simulation launch + robot spawning |
| `ros_gz_bridge` | Gazebo-ROS2 topic bridging |
| `robot_state_publisher` | URDF publishing |
| `controller_manager` | Controller spawning |
| `xacro` | URDF processing |
