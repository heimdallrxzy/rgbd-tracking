# normal1：判失跟前同帧重定位实验

原算法已经有运动模型失败→参考关键帧回退。本实验在初始位姿估计或局部地图验收失败时，为 RGB-D 增加一次同帧重定位，沿用原有 PnP/优化后至少 50 内点条件，之后仍须通过局部地图验收。额外重定位默认采用 20 ms 协作式预算（各次预算见事件表）；单次 BoW 查询、匹配或优化不能中途抢占，实际用时可能超出预算。

逐帧结果按源时间戳对齐；回放间地图与调度可分叉，整体差异不等于同帧因果。数据无独立位姿真值，状态恢复只说明通过几何门限，不能直接证明定位精度提高。

| 条件 | 组别 | 处理/配对 | 队列丢弃 | 非OK帧 | 非OK源时间 s | OK→失跟 | 平均调用 ms | 额外尝试/通过PnP/最终OK |
|---|---|---:|---:|---:|---:|---:|---:|---|
| direct_sync/rate_1x | recovery | 713/713 | 0 | 90 | 3.037 | 1 | 37.806 | 1/0/0 |
| direct_sync/rate_025x | recovery | 832/832 | 0 | 0 | 0.000 | 0 | 50.412 | 0/0/0 |
| fifo32/rate_1x | recovery | 781/832 | 51 | 75 | 3.037 | 1 | 35.564 | 1/0/0 |
| fifo32/rate_025x | recovery | 832/832 | 0 | 0 | 0.000 | 0 | 43.927 | 0/0/0 |

direct_sync/rate_1x/recovery: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。
fifo32/rate_1x/recovery: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。

## 额外恢复尝试

- case=direct_sync/rate_1x; group=recovery; timestamp=1792225267.030796051; frame_id=490; motion_postopt_inliers=9; reference_bow_matches=0; reference_postopt_inliers=-1; same_frame_recovery_candidates=1; same_frame_recovery_best_bow=21; same_frame_recovery_best_inliers=0; same_frame_recovery_timeout=0; same_frame_recovery_ms=5.060884000; same_frame_recovery_result=0; local_map_inliers=0; local_map_result=0; state_after=3; same_frame_recovery_budget_ms=100.000000000; consecutive_ok_up_to_11=0
- case=fifo32/rate_1x; group=recovery; timestamp=1792225267.630925655; frame_id=577; motion_postopt_inliers=4; reference_bow_matches=0; reference_postopt_inliers=-1; same_frame_recovery_candidates=3; same_frame_recovery_best_bow=9; same_frame_recovery_best_inliers=0; same_frame_recovery_timeout=0; same_frame_recovery_ms=3.796947000; same_frame_recovery_result=0; local_map_inliers=0; local_map_result=0; state_after=3; same_frame_recovery_budget_ms=100.000000000; consecutive_ok_up_to_11=0

## 相同源图像的状态对齐


## 失跟源图像在慢速基线中的支持

| 方法/源时间戳 | 1x 运动内点 | 1x 参考BoW | 0.25x 运动内点 | 0.25x 局部内点 | ORB指纹一致 |
|---|---:|---:|---:|---:|---|
