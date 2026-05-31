# omni_navigation

SLAM and Nav2 autonomous navigation configs for the omni-wheel robot.

## Directory Structure

```
omni_navigation/
├── config/
│   └── nav2_params.yaml         # Nav2 parameter config
├── launch/
│   ├── nav2.launch.py           # Nav2 bringup wrapper
│   ├── slam_gazebo_sim.launch.py
│   └── navigation_gazebo_sim.launch.py
├── maps/
│   ├── maze1.yaml + maze1.pgm   # maze1 map
│   └── maze2.yaml + maze2.pgm   # maze2 map
├── rviz/
│   ├── slam.rviz
│   └── navigation.rviz
├── CMakeLists.txt
└── package.xml
```

## Launch

### SLAM Mapping

Launches Gazebo simulation + SLAM Toolbox + RViz for building maps.

```bash
ros2 launch omni_navigation slam_gazebo_sim.launch.py
ros2 launch omni_navigation slam_gazebo_sim.launch.py wheel_config:=4wheel world:=maze1
```

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |
| `world` | `maze2` | Gazebo world name |

**What it launches:**

| Step | Description |
|---|---|
| 1 | Gazebo simulation (`omni_gazebo`) |
| 2 | SLAM Toolbox (online async) |
| 3 | RViz2 with `slam.rviz` config |

---

### Autonomous Navigation

Launches Gazebo simulation + Nav2 + RViz for autonomous navigation.

```bash
ros2 launch omni_navigation navigation_gazebo_sim.launch.py
ros2 launch omni_navigation navigation_gazebo_sim.launch.py world:=maze1
```

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |
| `world` | `maze2` | Gazebo world name (selects map file) |

**What it launches:**

| Step | Description |
|---|---|
| 1 | Gazebo simulation (`omni_gazebo`) |
| 2 | Nav2 bringup (5s delay for sim init) |
| 3 | RViz2 with `navigation.rviz` config |

---

### Nav2 Standalone

Wraps `nav2_bringup` with the correct map and parameters.

```bash
ros2 launch omni_navigation nav2.launch.py world:=maze1
```

| Argument | Default | Description |
|---|---|---|
| `world` | `maze2` | Map name (matches `maps/<name>.yaml`) |

## Nav2 Configuration

`config/nav2_params.yaml` key settings:

| Component | Setting | Value |
|---|---|---|
| AMCL | Robot model | `OmniMotionModel` |
| AMCL | Particles | 500-2000 |
| Planner | Algorithm | Navfn (Dijkstra) |
| Controller | Plugin | DWB Local Planner |
| Controller | Max velocity | 1.5 m/s linear, 2.0 rad/s angular |
| Costmap | Robot radius | 0.1 m |
| Costmap | Resolution | 0.05 m |
| Costmap | Inflation radius | 0.3 m |
| BT Navigator | Behavior tree | `navigate_w_replanning_and_recovery.xml` |
| Recovery | Plugins | spin, backup, wait |

## Maps

| Map | Resolution | Origin |
|---|---|---|
| `maze1` | 0.05 m/px | (-4.85, -7.64) |
| `maze2` | 0.05 m/px | (-3.97, -0.84) |

## Dependencies

| Package | Purpose |
|---|---|
| `omni_gazebo` | Simulation launch |
| `nav2_bringup` | Nav2 navigation stack |
| `slam_toolbox` | SLAM mapping |
| `rviz2` | Visualization |
