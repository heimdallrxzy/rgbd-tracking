#!/usr/bin/env python3
"""Summarize the normal1 ORB-vs-LK-retry ROS A/B runs."""

import csv
import math
import pathlib
import sys


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def number(value, default=math.nan):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def percentile(values, fraction):
    values = sorted(value for value in values if math.isfinite(value))
    if not values:
        return math.nan
    index = max(0, math.ceil(fraction * len(values)) - 1)
    return values[index]


def summarize_run(run_dir, condition):
    decisions = read_csv(run_dir / "tracking_decisions.csv")
    evaluation = read_csv(run_dir / "eval_metrics.csv")
    profile = read_csv(run_dir / "slam_profile.csv")
    mapping = read_csv(run_dir / "local_mapping.csv")
    ingress = read_csv(run_dir / "input_summary.csv")[0]

    valid_evaluation = [row for row in evaluation if row.get("frame_context_valid") == "1"]
    state_counts = {
        state: sum(row.get("state_name") == state for row in valid_evaluation)
        for state in ("OK", "RECENTLY_LOST", "LOST")
    }
    lost_source_ms = sum(
        number(row.get("timestamp_delta_ms"), 0.0)
        for row in valid_evaluation
        if row.get("state_name") in ("RECENTLY_LOST", "LOST")
    )
    lost_intervals = 0
    previous_lost = False
    for row in valid_evaluation:
        current_lost = row.get("state_name") in ("RECENTLY_LOST", "LOST")
        if current_lost and not previous_lost:
            lost_intervals += 1
        previous_lost = current_lost

    processing_ms = [number(row.get("total_ms")) for row in profile]
    decision_wait_ms = [number(row.get("input_queue_wait_ms")) for row in decisions]
    mapping_wait_ms = [number(row.get("queue_wait_ms")) for row in mapping]
    mapping_depth = [number(row.get("queue_depth_at_pop")) for row in mapping]
    lk_events = [row for row in decisions if row.get("lk_retry_attempted") == "1"]

    summary = {
        "condition": condition,
        "run": run_dir.name,
        "processed_frames": len(valid_evaluation),
        "ok_frames": state_counts["OK"],
        "recently_lost_frames": state_counts["RECENTLY_LOST"],
        "lost_frames": state_counts["LOST"],
        "lost_source_ms": round(lost_source_ms, 3),
        "lost_intervals": lost_intervals,
        "map_ids": ";".join(sorted({row.get("map_id", "") for row in valid_evaluation})),
        "keyframes_created": sum(row.get("keyframe_created") == "1" for row in decisions),
        "queue_dropped": int(number(ingress.get("queue_dropped"), 0)),
        "queue_max_depth": int(number(ingress.get("max_queue_depth"), 0)),
        "track_calls": int(number(ingress.get("track_calls"), 0)),
        "track_total_median_ms": round(percentile(processing_ms, 0.5), 4),
        "track_total_p95_ms": round(percentile(processing_ms, 0.95), 4),
        "input_wait_p95_ms": round(percentile(decision_wait_ms, 0.95), 4),
        "local_mapping_tasks": len(mapping),
        "local_mapping_wait_median_ms": round(percentile(mapping_wait_ms, 0.5), 4),
        "local_mapping_wait_p95_ms": round(percentile(mapping_wait_ms, 0.95), 4),
        "local_mapping_queue_depth_p95": round(percentile(mapping_depth, 0.95), 4),
        "lk_attempts": len(lk_events),
        "lk_accepted": sum(row.get("lk_retry_accepted") == "1" for row in lk_events),
        "lk_local_map_passes": sum(
            row.get("lk_retry_accepted") == "1" and row.get("local_map_result") == "1"
            for row in lk_events
        ),
    }

    target_fields = (
        "condition", "run", "frame_id", "timestamp", "state_before", "state_after",
        "track_path", "motion_initial_matches", "motion_projection_matches",
        "motion_postopt_inliers", "lk_seed_map_points", "lk_valid_tracks",
        "lk_orb_keypoint_matches", "lk_pose_inliers", "lk_retry_accepted",
        "local_map_executed", "local_map_matches", "local_map_inliers",
        "local_map_result", "keyframe_created", "reference_kf_frame_id",
        "last_kf_frame_id", "keypoint_hash", "descriptor_hash",
        "last_frame_association_hash", "motion_velocity_hash",
        "motion_current_source_interval_s", "motion_previous_source_interval_s",
        "input_queue_depth", "input_queue_wait_ms", "lk_retry_ms",
    )
    events = []
    for row in lk_events:
        event = {key: row.get(key, "") for key in target_fields if key not in ("condition", "run")}
        event["condition"] = condition
        event["run"] = run_dir.name
        events.append({key: event.get(key, "") for key in target_fields})
    return summary, events


def write_rows(path, rows):
    if not rows:
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(
        "debug_visualization/normal1_lk_retry_ab_20261027"
    )
    summaries, events = [], []
    for condition in ("baseline", "lk_retry"):
        for run_dir in sorted((root / condition).glob("run*")):
            summary, run_events = summarize_run(run_dir, condition)
            summaries.append(summary)
            events.extend(run_events)
    write_rows(root / "summary.csv", summaries)
    write_rows(root / "lk_retry_events.csv", events)
    print(f"Wrote {root / 'summary.csv'} ({len(summaries)} runs)")
    print(f"Wrote {root / 'lk_retry_events.csv'} ({len(events)} LK attempts)")


if __name__ == "__main__":
    main()
