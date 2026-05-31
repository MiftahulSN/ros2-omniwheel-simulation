# omni_bringup

Top-level convenience launch files for the omni-wheel robot simulation.

Wraps `omni_gazebo` and `omni_navigation` with a consistent interface.

## Directory Structure

```
omni_bringup/
├── launch/
│   ├── sim.launch.py            # Simulation only
│   ├── slam.launch.py           # Simulation + SLAM mapping
│   └── navigation.launch.py    # Simulation + autonomous navigation
├── CMakeLists.txt
└── package.xml
```

## Launch

All launch files accept the same arguments:

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |
| `world` | `maze2` | Gazebo world name |

---

### Simulation Only

Launches Gazebo simulation with robot, controllers, kinematics, and sensor bridges.

```bash
ros2 launch omni_bringup sim.launch.py
ros2 launch omni_bringup sim.launch.py wheel_config:=4wheel world:=maze1
```

Then drive manually:
```bash
ros2 run omni_controller omni_teleop.py
```

---

### SLAM Mapping

Launches simulation + SLAM Toolbox for building maps.

```bash
ros2 launch omni_bringup slam.launch.py
```

---

### Autonomous Navigation

Launches simulation + Nav2 for autonomous path planning and navigation.

```bash
ros2 launch omni_bringup navigation.launch.py
```

## Dependencies

| Package | Purpose |
|---|---|
| `omni_gazebo` | Simulation launch |
| `omni_navigation` | SLAM and Nav2 launch |
