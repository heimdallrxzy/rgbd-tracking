# Result fields

`results/run-summary.csv` contains one row per replay. `lost_source_ms` is the sum of source-time deltas for frames in `RECENTLY_LOST` or `LOST`; it is not wall-clock downtime. `track_total_p95_ms` is the per-frame Tracking profile p95. Queue-drop counts and processed-frame counts are included because the 1x queue reached capacity.

`results/lk-events.csv` contains only frames where the optional LK retry ran. `lk_pose_inliers` counts the valid map-point associations left by pose optimization before the ordinary LocalMap pass. `local_map_inliers` and `local_map_result` record the later standard local-map stage. An increase in raw LK associations alone is not counted as recovery.

`results/per_frame/` contains selected per-frame fields for each replay: source timestamp, tracking state/path, motion-model matches and inliers, LK counts, LocalMap outcome, feature hashes, previous-frame association/velocity hashes, and input queue age. The data is trimmed from the full diagnostic CSVs; full console logs and frame images are omitted.
