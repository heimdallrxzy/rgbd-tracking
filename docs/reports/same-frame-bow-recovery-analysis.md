# normal1：判失跟前同帧重定位实验

原算法已经有运动模型失败→参考关键帧回退。本实验在初始位姿估计失败时，为 RGB-D 增加一次同帧重定位，沿用原有 PnP/优化后至少 50 内点条件，之后仍须通过局部地图验收。额外重定位默认采用 20 ms 协作式预算（各次预算见事件表）；单次 BoW 查询、匹配或优化不能中途抢占，实际用时可能超出预算。

逐帧结果按源时间戳对齐；回放间地图与调度可分叉，整体差异不等于同帧因果。数据无独立位姿真值，状态恢复只说明通过几何门限，不能直接证明定位精度提高。

| 条件 | 组别 | 处理/配对 | 队列丢弃 | 非OK帧 | 非OK源时间 s | OK→失跟 | 平均调用 ms | 额外尝试/通过PnP/最终OK |
|---|---|---:|---:|---:|---:|---:|---:|---|
| direct_sync/rate_1x | baseline | 620/620 | 0 | 90 | 3.037 | 1 | 36.760 | 0/0/0 |
| direct_sync/rate_1x | recovery | 701/701 | 0 | 90 | 3.037 | 1 | 38.583 | 1/0/0 |
| direct_sync/rate_025x | baseline | 832/832 | 0 | 0 | 0.000 | 0 | 51.418 | 0/0/0 |
| direct_sync/rate_025x | recovery | 832/832 | 0 | 90 | 3.033 | 1 | 51.692 | 0/0/0 |
| fifo32/rate_1x | baseline | 756/832 | 76 | 73 | 3.037 | 1 | 37.295 | 0/0/0 |
| fifo32/rate_1x | recovery | 780/832 | 52 | 74 | 3.033 | 1 | 35.397 | 1/0/0 |
| fifo32/rate_025x | baseline | 832/832 | 0 | 90 | 3.033 | 1 | 44.583 | 0/0/0 |
| fifo32/rate_025x | recovery | 832/832 | 0 | 90 | 3.033 | 1 | 44.069 | 0/0/0 |

direct_sync/rate_1x/baseline: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。
direct_sync/rate_1x/recovery: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。
direct_sync/rate_025x/recovery: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。
fifo32/rate_1x/baseline: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。
fifo32/rate_1x/recovery: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。
fifo32/rate_025x/baseline: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。
fifo32/rate_025x/recovery: 1 条建新地图时 Frame 被清空的决策行，未纳入源时间积分及图像对齐；处理帧数仍取输入统计。

## 额外恢复尝试

- case=direct_sync/rate_1x; group=recovery; timestamp=1792225266.830730438; frame_id=472; motion_postopt_inliers=4; reference_bow_matches=0; reference_postopt_inliers=-1; same_frame_recovery_candidates=3; same_frame_recovery_best_bow=27; same_frame_recovery_best_inliers=0; same_frame_recovery_timeout=1; same_frame_recovery_ms=37.916005000; same_frame_recovery_result=0; local_map_inliers=0; local_map_result=0; state_after=3; same_frame_recovery_budget_ms=20; consecutive_ok_up_to_11=0
- case=fifo32/rate_1x; group=recovery; timestamp=1792225267.666954994; frame_id=578; motion_postopt_inliers=5; reference_bow_matches=0; reference_postopt_inliers=-1; same_frame_recovery_candidates=5; same_frame_recovery_best_bow=7; same_frame_recovery_best_inliers=0; same_frame_recovery_timeout=0; same_frame_recovery_ms=6.993527000; same_frame_recovery_result=0; local_map_inliers=0; local_map_result=0; state_after=3; same_frame_recovery_budget_ms=20; consecutive_ok_up_to_11=0

## 未触发额外恢复的失跟出口

这些帧没有执行额外恢复；其中基线/实验的状态差异不能解释为新增恢复分支造成。
- direct_sync/rate_025x/1792225267.798985004: motion=16, initial_pose_ok=1, local_executed=1, local_inliers=26, local_result=0。
- fifo32/rate_025x/1792225267.798985004: motion=11, initial_pose_ok=1, local_executed=1, local_inliers=26, local_result=0。

## 相同源图像的状态对齐

- direct_sync/rate_1x: 共同源图像 518，ORB 指纹一致 518；基线非OK→实验OK 26，反向 15。
- direct_sync/rate_025x: 共同源图像 831，ORB 指纹一致 831；基线非OK→实验OK 0，反向 90。
- fifo32/rate_1x: 共同源图像 718，ORB 指纹一致 718；基线非OK→实验OK 1，反向 1。
- fifo32/rate_025x: 共同源图像 831，ORB 指纹一致 831；基线非OK→实验OK 0，反向 0。

## 失跟源图像在慢速基线中的支持

| 方法/源时间戳 | 1x 运动内点 | 1x 参考BoW | 0.25x 运动内点 | 0.25x 局部内点 | ORB指纹一致 |
|---|---:|---:|---:|---:|---|
| direct_sync/1792225266.830730438 | 4 | 0 | 73 | 109 | True |
| fifo32/1792225267.666954994 | 5 | 0 | 41 | 72 | True |
