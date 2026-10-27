# Reproduction notes

## Tested setup

- Sensor mode: RGB-D
- Sequence: `normal1_20261017_162037`
- Device: Jetson Orin NX
- Middleware: ROS 2 Humble
- Input topics: `/camera/color/image_raw` and `/camera/depth/image_raw`
- Queue: FIFO, capacity 32
- Playback rates: 1x for three runs per condition; 0.25x for one supplemental run per condition
- Tracking and LocalMapping: parallel
- Build command recorded for the experiment: `cmake --build build -j8`

The tested workspace source snapshot was commit `c934c599c9c081aafeb77fc54f8b89a275512a87` of `heimdallrxzy/jetson-orbslam3-ws`. The patch in this repository is based on that snapshot and only adds the LK recovery path plus the grayscale-frame copy needed by it.

## Inputs the user must provide locally

The bag and camera configuration are not included. Before running, make the following available:

```bash
export BAG_PATH=/path/to/normal1_rosbag2
export SLAM_NODE=/path/to/rgbd_slam_node
export VOCABULARY=/path/to/ORBvoc.txt
export SETTINGS=/path/to/astra_pro_plus.yaml
export ROS_SETUP=/opt/ros/humble/setup.bash
export ROS_OVERLAY_SETUP=/path/to/ros2_workspace/install/setup.bash
```

`ROS_OVERLAY_SETUP` is optional when the node is already available in the ROS environment. Then run:

```bash
tools/run_normal1_lk_retry_ab.sh
```

The runner alternates the baseline and treatment order between repeats. Each run writes to its own output folder. It sets the LK retry to `0` for baseline and `1` for treatment, and turns off the other experimental recovery and overload switches.

## Apply the focused code patch

The patch paths are relative to the root of the recorded workspace checkout:

```bash
git checkout c934c599c9c081aafeb77fc54f8b89a275512a87
git apply /path/to/normal1-rgbd-tracking-study/patches/lk-optical-flow-retry.patch
```

Then rebuild ORB-SLAM3 and the ROS 2 node. To enable the experimental branch in another launch path, set:

```bash
ORB_SLAM3_OPTICAL_FLOW_RETRY=1
```

Unset the variable or set it to `0` to keep the baseline behavior.

## What the patch changes

The retry runs only for RGB-D map tracking. It starts from valid MapPoints observed in the previous processed frame, tracks their image locations with pyramidal LK in both directions, rejects tracks with forward/backward error over 1.5 pixels, then associates surviving tracks to current-frame ORB keypoints within 4 pixels. Duplicate MapPoints and keypoints are removed. At least 20 associations are needed before pose optimization; at least 10 valid inliers and a finite pose are required before the retry succeeds. A failed attempt restores the frame state from before the retry. A successful attempt still goes through the normal LocalMap path and its original acceptance thresholds.

The retry adds no MapPoints or keyframes. ORB extraction still runs on every image. The grayscale image is copied by OpenCV's reference-counted `cv::Mat` handle when a `Frame` is copied.

## Telemetry requirement

The archived experiment was run with asynchronous CSV diagnostics for the input queue, per-frame tracking path, pose optimization, LocalMapping and LK attempt counters. The focused patch intentionally does not include that wider instrumentation layer. The runner's CSV environment variables are read by the instrumented ROS-SLAM build used for the archived results. If running against a clean source tree with only this patch, the tracking behavior is available but those experiment CSVs will not all be produced.

Summarize an instrumented run with:

```bash
python3 tools/summarize_normal1_lk_retry_ab.py /path/to/output_root
```

The result exporter used to assemble this repository is:

```bash
python3 tools/export_public_results.py \
  --one-x /path/to/normal1_lk_retry_ab_20261027 \
  --quarter-x /path/to/normal1_lk_retry_ab_025x_20261027 \
  --output results
```

## Data handling

No bag file, vocabulary, camera calibration file, trajectory ground truth or user credentials are stored here. `results/` contains compact CSV evidence derived from the recorded runs, not a substitute for the original ROS bag.
