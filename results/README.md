# 精简结果数据

这些 CSV 来自 2026-10-27 在 Jetson Orin NX 上进行的 `normal1` RGB-D FIFO32 回放。逐帧表只保留用于解释跟踪分叉的字段；完整日志、输入 bag、相机配置、词汇文件和轨迹文件未纳入公开包。

| 文件 | 内容 |
|---|---|
| [`run-summary.csv`](run-summary.csv) | 每次回放的处理帧数、失跟源时间、丢帧、耗时和 LK 触发统计。 |
| [`lk-events.csv`](lk-events.csv) | LK 重试触发时的种子点数、有效光流、ORB 关联、位姿内点和 LocalMap 结果。0.25x 没有触发事件。 |
| [`per_frame/1x/`](per_frame/1x/) | 三轮 1x 基线与 LK 条件的筛选后逐帧决策数据。 |
| [`per_frame/0.25x/`](per_frame/0.25x/) | 基线与 LK 条件各一轮 0.25x 的筛选后逐帧决策数据。 |

`keypoint_hash` 与 `descriptor_hash` 用于识别相同图像特征输入；`last_frame_association_hash`、`motion_velocity_hash` 等字段用于辨别前序跟踪上下文。哈希只用于比对是否变化，不包含可重建图像或地图点的内容。

这些文件支持描述此次回放观察到的结果，不构成独立真值评测。各次 1x 运行因输入 FIFO 饱和而处理了不同的帧集合，运行间地图状态也不同。
