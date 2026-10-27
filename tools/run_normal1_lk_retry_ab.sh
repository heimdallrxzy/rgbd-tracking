#!/usr/bin/env bash
set -euo pipefail

: "${BAG_PATH:?Set BAG_PATH to the normal1 ROS 2 bag directory}"
: "${SLAM_NODE:?Set SLAM_NODE to the instrumented RGB-D SLAM executable}"
: "${VOCABULARY:?Set VOCABULARY to ORBvoc.txt}"
: "${SETTINGS:?Set SETTINGS to the RGB-D camera settings file}"

ros_setup="${ROS_SETUP:-/opt/ros/humble/setup.bash}"
overlay_setup="${ROS_OVERLAY_SETUP:-}"
output_root="${OUTPUT_ROOT:-$PWD/results/lk_retry_$(date +%Y%m%d_%H%M%S)}"
repeats="${REPEATS:-3}"
playback_rate="${PLAYBACK_RATE:-1.0}"

source "$ros_setup"
if [[ -n "$overlay_setup" ]]; then
    source "$overlay_setup"
fi

mkdir -p "$output_root"

run_case() {
    local condition="$1"
    local repeat="$2"
    local lk_enabled="$3"
    local output="$output_root/$condition/run$(printf '%02d' "$repeat")"
    local slam_pid
    mkdir -p "$output"

    ORB_LOWLIGHT_MODE=0 \
    ORB_SLAM3_USE_VIEWER=0 \
    ORB_SLAM3_FRAME_QUEUE_CAPACITY=32 \
    ORB_SLAM3_OPTICAL_FLOW_RETRY="$lk_enabled" \
    ORB_SLAM3_LAST_OBSERVATION_RETRY=0 \
    ORB_SLAM3_SAME_FRAME_RECOVERY=0 \
    ORB_SLAM3_ADAPTIVE_OVERLOAD=0 \
    ORB_SLAM3_TIME_AWARE_PREDICTION=0 \
    ORB_SLAM3_PROFILE_CSV="$output/slam_profile.csv" \
    ORB_SLAM3_LOCAL_MAPPING_CSV="$output/local_mapping.csv" \
    ORB_SLAM3_DECISION_TRACE_CSV="$output/tracking_decisions.csv" \
    ORB_SLAM3_INPUT_DIAG_CSV="$output/input_summary.csv" \
    ORB_EVAL_CSV="$output/eval_metrics.csv" \
    "$SLAM_NODE" "$VOCABULARY" "$SETTINGS" "$output/trajectory" \
        >"$output/slam.log" 2>&1 &
    slam_pid=$!

    stop_slam() {
        kill -INT "$slam_pid" 2>/dev/null || true
        wait "$slam_pid" 2>/dev/null || true
    }
    trap stop_slam RETURN

    local ready=0
    for _ in $(seq 1 90); do
        if ros2 node list 2>/dev/null | grep -Fxq /astra_rgbd_slam; then
            local rgb_info depth_info
            rgb_info=$(ros2 topic info /camera/color/image_raw --no-daemon 2>/dev/null || true)
            depth_info=$(ros2 topic info /camera/depth/image_raw --no-daemon 2>/dev/null || true)
            if grep -Eq 'Subscription count: [1-9]' <<<"$rgb_info" &&
               grep -Eq 'Subscription count: [1-9]' <<<"$depth_info"; then
                ready=1
                break
            fi
        fi
        sleep 1
    done
    if [[ "$ready" != 1 ]]; then
        cat "$output/slam.log" >&2
        return 1
    fi

    ros2 bag play "$BAG_PATH" --rate "$playback_rate" --read-ahead-queue-size 1000 \
        --disable-keyboard-controls --topics /camera/color/image_raw \
        /camera/depth/image_raw >"$output/bag.log" 2>&1
    stop_slam
    trap - RETURN
    printf 'Finished %s/run%s (LK retry=%s)\n' "$condition" "$repeat" "$lk_enabled"
}

for repeat in $(seq 1 "$repeats"); do
    if (( repeat % 2 == 1 )); then
        run_case baseline "$repeat" 0
        run_case lk_retry "$repeat" 1
    else
        run_case lk_retry "$repeat" 1
        run_case baseline "$repeat" 0
    fi
done

cat >"$output_root/experiment_manifest.txt" <<EOF
Dataset: normal1 RGB-D; playback rate $playback_rate; FIFO capacity 32.
Conditions: baseline ORB-SLAM3 and optional RGB-D optical-flow retry.
Tracking and LocalMapping stay parallel. Original pose and LocalMap acceptance checks stay enabled.
Repeats per condition: $repeats; run order alternates.
EOF
printf 'Results: %s\n' "$output_root"
