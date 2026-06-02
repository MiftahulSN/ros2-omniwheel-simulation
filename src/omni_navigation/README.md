# omni_navigation

Nav2 and SLAM configuration files for the omni-wheel robot.

This package contains only config, maps, and RViz files. Launch is handled by `omni_bringup`.

## Directory Structure

```
omni_navigation/
├── config/
│   ├── nav2_params.yaml         # Nav2 parameter config (AMCL + DWB + costmaps)
│   └── slam_params.yaml         # SLAM Toolbox online async config
├── maps/
│   ├── maze1.yaml + maze1.pgm
│   └── maze2.yaml + maze2.pgm
├── rviz/
│   ├── navigation.rviz
│   └── slam.rviz
├── CMakeLists.txt
└── package.xml
```

## Config Files

### `nav2_params.yaml`

Full Nav2 parameter configuration.

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

### `slam_params.yaml`

SLAM Toolbox online async configuration.

| Setting | Value |
|---|---|
| Solver | Ceres (SPARSE_NORMAL_CHOLESKY) |
| Resolution | 0.05 m |
| Max laser range | 20.0 m |
| Map update interval | 5.0 s |
| Loop closing | enabled |
| Base frame | `base_footprint` |

## Maps

| Map | Resolution | Origin |
|---|---|---|
| `maze1` | 0.05 m/px | (-4.85, -7.64) |
| `maze2` | 0.05 m/px | (-3.97, -0.84) |

Maps are selected by the `world` launch argument in `omni_bringup`.
