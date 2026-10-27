#!/usr/bin/env python3
"""Export compact replay summaries and selected per-frame fields."""

import argparse
import csv
from pathlib import Path


FRAME_FIELDS = [
    "frame_id", "timestamp", "state_before", "state_after", "track_path",
    "motion_initial_matches", "motion_projection_matches", "motion_postopt_inliers",
    "reference_bow_matches", "reference_postopt_inliers", "local_map_executed",
    "local_map_matches", "local_map_inliers", "local_map_result", "keyframe_created",
    "keypoint_hash", "descriptor_hash", "last_frame_association_hash",
    "motion_velocity_hash", "motion_current_source_interval_s",
    "motion_previous_source_interval_s", "input_queue_depth", "input_queue_capacity",
    "input_queue_wait_ms", "lk_retry_attempted", "lk_seed_map_points",
    "lk_valid_tracks", "lk_orb_keypoint_matches", "lk_pose_inliers",
    "lk_retry_accepted", "lk_retry_ms",
]


def read_rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_rows(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_condition(source_root, rate, output_root, summaries, events):
    if not source_root:
        return
    for condition in ("baseline", "lk_retry"):
        condition_dir = source_root / condition
        for run_dir in sorted(condition_dir.glob("run*")):
            summary_file = source_root / "summary.csv"
            match = next(
                (row for row in read_rows(summary_file)
                 if row.get("condition") == condition and row.get("run") == run_dir.name),
                None,
            )
            if match is not None:
                summaries.append({"rate": rate, **match})

            decisions_file = run_dir / "tracking_decisions.csv"
            if decisions_file.exists():
                rows = read_rows(decisions_file)
                selected = [
                    {"condition": condition, "run": run_dir.name, **{
                        field: row.get(field, "") for field in FRAME_FIELDS
                    }}
                    for row in rows
                ]
                target = output_root / "per_frame" / rate / f"{condition}_{run_dir.name}.csv"
                write_rows(target, selected)

            event_file = source_root / "lk_retry_events.csv"
            if event_file.exists():
                events.extend({"rate": rate, **row} for row in read_rows(event_file)
                              if row.get("condition") == condition and row.get("run") == run_dir.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--one-x", type=Path, required=True)
    parser.add_argument("--quarter-x", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summaries, events = [], []
    export_condition(args.one_x, "1x", args.output, summaries, events)
    export_condition(args.quarter_x, "0.25x", args.output, summaries, events)
    write_rows(args.output / "run-summary.csv", summaries)
    write_rows(args.output / "lk-events.csv", events)


if __name__ == "__main__":
    main()
