# omni_bringup

Top-level launch files for the omni-wheel robot simulation.

## Directory Structure

```
omni_bringup/
├── launch/
│   ├── nav_sim.launch.py        # Gazebo + Nav2 autonomous navigation
│   └── slam_sim.launch.py       # Gazebo + SLAM mapping
├── CMakeLists.txt
└── package.xml
```

## Launch

All launch files accept the same arguments:

| Argument | Default | Description |
|---|---|---|
| `wheel_config` | `3wheel` | `3wheel` or `4wheel` |
| `world` | `maze2` | Gazebo world name (also selects map for Nav2) |

---

### `nav_sim.launch.py`

Gazebo simulation + Nav2 bringup (AMCL localization + path planning + RViz).

```bash
ros2 launch omni_bringup nav_sim.launch.py
ros2 launch omni_bringup nav_sim.launch.py wheel_config:=4wheel world:=maze1
```

**What it launches:**

| Step | Description |
|---|---|
| 1 | Gazebo simulation (`omni_gazebo`) |
| 2 | Nav2 bringup (`nav2_bringup/bringup_launch.py`, 5s delay) |
| 3 | RViz2 with `navigation.rviz` |

Requires an existing map in `omni_navigation/maps/<world>.yaml`.

---

### `slam_sim.launch.py`

Gazebo simulation + SLAM Toolbox (online async) + RViz for building maps.

```bash
ros2 launch omni_bringup slam_sim.launch.py
ros2 launch omni_bringup slam_sim.launch.py world:=maze1
```

**What it launches:**

| Step | Description |
|---|---|
| 1 | Gazebo simulation (`omni_gazebo`) |
| 2 | SLAM Toolbox (online async, with `slam_params.yaml`) |
| 3 | RViz2 with `slam.rviz` |

---

### Simulation Only (no navigation)

To launch Gazebo without Nav2/SLAM:

```bash
ros2 launch omni_gazebo gazebo.launch.py
```

Then drive manually:
```bash
ros2 run omni_controller omni_teleop.py
```

## Dependencies

| Package | Purpose |
|---|---|
| `omni_gazebo` | Simulation launch |
| `omni_navigation` | Config files, maps, RViz configs |
| `nav2_bringup` | Nav2 navigation stack |
| `slam_toolbox` | SLAM mapping |
| `rviz2` | Visualization |
