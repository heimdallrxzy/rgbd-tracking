# RGB-D Visual Tracking Under Frame Drops

This repository records a set of experiments I ran on ORB-SLAM3 with the `normal1` RGB-D sequence on a Jetson Orin NX. The starting question was straightforward: if two runs extract the same ORB features from a frame, why can one keep tracking while the other loses the map?

I compared the input paths, logged the tracking decisions and map-point matches, then tried several recovery ideas. The latest prototype adds an optional pyramidal Lucas–Kanade (LK) retry after motion-model matching collapses.

## What the experiment showed

In three 1x FIFO32 replay runs per condition, the LK retry activated five times. Three attempts produced enough pose inliers to enter LocalMapping and pass the existing acceptance checks. A representative frame stayed tracked with LK where the baseline entered `RECENTLY_LOST`.

That frame-level result did not turn into a whole-run improvement:

| Measure | ORB baseline | LK retry |
|---|---:|---:|
| Median `RECENTLY_LOST` source time | 3032.6 ms | 3032.7 ms |
| Median processed frames | 793 | 774 |
| Median input queue drops | 38 | 57 |
| Median Tracking time, p95 | 45.72 ms | 49.67 ms |

The replay queues were full and the processed frame sets differed between runs. These figures do not establish that LK caused the extra drops, but they also give no evidence of a system-level gain. The result is best described as **occasional frame recovery, with no measured reduction in run-level lost time**.

The strongest diagnostic finding came from a different target frame. Its ORB keypoint and descriptor hashes matched across runs, yet one heavily loaded 1x run reached the frame after a 132 ms processing gap and retained only 2 motion-model inliers from 41 matches. It never reached LocalMap tracking. A continuous-frame run reached the same image after about 32 ms and retained dozens of inliers. Earlier-frame associations, motion prediction and the evolving map had already diverged before the target image was matched.

## What is included

- `docs/experiment-history-zh.md`: the earlier queue, relocalization, matching, prediction, map-point and optical-flow experiments, with their limits.
- `docs/application-summary-zh.md`: a Chinese summary suitable for an internship or research application.
- `docs/lk-retry-report-zh.md`: detailed report for the LK retry experiment.
- `patches/lk-optical-flow-retry.patch`: focused implementation patch against the source snapshot recorded in `docs/reproduction.md`.
- `tools/run_normal1_lk_retry_ab.sh`: configurable ROS 2 replay runner. It expects an instrumented SLAM node and a locally available bag.
- `tools/summarize_normal1_lk_retry_ab.py`: summarizes the per-run CSV files produced by the instrumented node.
- `tools/export_public_results.py`: extracts the result tables and selected per-frame fields into `results/`.
- `results/`: compact summaries and selected per-frame records; see its [data guide](results/README.md).

The ROS bag, ORB vocabulary, camera settings, build products and full console logs are not included. The bag is not redistributed with this repository.

## Reproducing the LK experiment

See [reproduction notes](docs/reproduction.md). In brief, the runner compares the baseline and LK-enabled paths while keeping Tracking and LocalMapping parallel and preserving the original geometric acceptance checks. Set `ORB_SLAM3_OPTICAL_FLOW_RETRY=1` to enable the retry; it is off by default.

The patch isolates the LK behavior. The reported CSV telemetry was collected from an instrumented version of the working tree; the patch by itself does not add the full decision/profile logging layer. This distinction is documented so the patch is not mistaken for a turnkey recreation of every recorded diagnostic.

## Limits

- There is no independently verified ground-truth trajectory for this sequence, so this repository does not claim an ATE/RPE or trajectory-accuracy improvement.
- Replays used the same bag, but a full 1x run did not process exactly the same frames in every condition. Parallel LocalMapping also produced different map states across repeated runs.
- Three 1x repetitions are enough to describe these runs, not to estimate a reliable LOST probability.
- The LK retry still computes ORB features on every frame. It is a recovery path, not a lightweight front end or an ORB acceleration result.

The experiment did not produce a finished localization improvement. It did produce a concrete failure analysis, a bounded recovery prototype and a record of where that prototype helped and where it did not.

## License and source

The implementation patch is derived from the GPL-licensed ORB-SLAM3 code. See [LICENSE](LICENSE) and the source snapshot information in [reproduction notes](docs/reproduction.md).
