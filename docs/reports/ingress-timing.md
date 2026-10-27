# normal1 图像输入与 ORB-SLAM3 耗时评测

## 方法

对同一个 normal1 rosbag 测了四组：同步回调直接跟踪与容量 32 的 FIFO，各跑 1× 和 0.25×。开始播放前确认 RGB、Depth 两个订阅都已在 ROS graph 中出现。每组的收包数均为 RGB 833、Depth 833；`cv_bridge` 失败为 0。计时使用 steady clock。

节点按帧把接收、ApproximateTime 配对、FIFO 入队/出队、cv_bridge、TrackRGBD、位姿发布、丢弃事件保存在内存中；SLAM 内部 ORB、跟踪、LocalMapping 阶段也只入内存日志队列。独立后台线程负责 CSV 写盘，写文件和刷新文件流不占用采集线程的队列锁，也不计入帧的阶段时间。节点侧 TrackRGBD 时长包含 SLAM 调用与少量内存日志入队开销，不包含磁盘 I/O。

## 收包、配对和队列结果

| 模式 | ApproximateTime 配对 / TrackRGBD | 同步器未配对消息 | FIFO 峰值 / 容量 | FIFO 丢帧 | FIFO 等待 p95 / 最大 |
|---|---:|---:|---:|---:|---:|
| 同步直通，1× | 830 / 830 | 6 条（3 RGB、3 Depth） | 不适用 | 不适用 | 不适用 |
| 同步直通，0.25× | 832 / 832 | 2 条（1 RGB、1 Depth） | 不适用 | 不适用 | 不适用 |
| FIFO 32，1× | 832 / 832 | 2 条（1 RGB、1 Depth） | 7 / 32 | 0 | 118.7 / 225.3 ms |
| FIFO 32，0.25× | 832 / 832 | 2 条（1 RGB、1 Depth） | 1 / 32 | 0 | 0.3 / 43.2 ms |

四组的 RGB、Depth 订阅都收到了全部 833 条消息，因此没有证据表明源话题或 DDS 接收端漏收。常见的 2 条未配对消息是每组相同的一条首帧 RGB 与一条尾帧 Depth。同步直通 1× 另外有两对中段图像未形成同步对：RGB 时间戳 `1792225266598732074`、`1792225266630746857`，Depth 时间戳 `1792225266594628840`、`1792225266628085411`。FIFO 1× 收到并处理了这两对。

这些额外图像在同步阶段没有形成 pair，所以没有进入 TrackRGBD；它们不是 FIFO 满后丢弃。ROS 2 的 ApproximateTime 策略没有提供被删消息的 drop callback，因此记录能确认“消息已到订阅，但同步器未产出 pair”，不能从公开 API 精确区分它们是同步器内部队列淘汰，还是候选配对策略淘汰。事件中的 `unmatched_at_shutdown` 保留了每条未配对消息的时间戳。所有四组 FIFO 的 `frame_queue_capacity_drop_newest` 数均为 0，cv_bridge 丢弃也为 0。

## 主要处理耗时

| 阶段均值 | 同步直通 1× | 同步直通 0.25× | FIFO 32，1× | FIFO 32，0.25× |
|---|---:|---:|---:|---:|
| TrackRGBD | 29.3 ms | 42.2 ms | 28.0 ms | 37.7 ms |
| ORB 提取 | 13.8 ms | 21.1 ms | 13.2 ms | 18.5 ms |
| ORB 金字塔 | 1.35 ms | 2.12 ms | 1.25 ms | 1.88 ms |
| ORB 角点检测、分布与方向 | 7.05 ms | 11.01 ms | 6.56 ms | 9.56 ms |
| ORB 描述子 | 5.39 ms | 7.99 ms | 5.36 ms | 7.13 ms |
| 局部地图跟踪 | 7.25 ms | 10.78 ms | 6.99 ms | 9.96 ms |
| 位姿估计 | 4.23 ms | 5.14 ms | 4.04 ms | 4.52 ms |

1× 同步直通 TrackRGBD 的 p95 为 39.0 ms、最大 70.8 ms；输入图像时间戳的中位间隔约 32–33 ms。FIFO 1× 仍有短时积压，等待 p95 为 118.7 ms，但容量峰值 7/32，未发生队列满丢弃。ORB 提取是单帧最主要的耗时，角点阶段与描述子阶段占比最大。LocalMapping 也会有明显长任务：1× 同步直通的 Local BA p95 约 181 ms；FIFO 1× 的 Local BA p95 约 204 ms。LocalMapping 在独立线程运行，因此它的耗时主要表现为后台地图更新延迟，不等于每帧 TrackRGBD 的串行耗时。

阶段时间有父子嵌套，例如 `frame_construct_ms` 包含 Frame 构造期间的 ORB 工作，`orb_extract_ms` 是其中的子阶段，不能把所有列直接相加。完整 p50/p95/p99 和每帧值在各组 `slam_profile.csv`、`local_mapping.csv` 与 `comparison.txt` 中。

0.25× 的 TrackRGBD 均值反而更高，不是慢放让算法增加了工作量。tegrastats 中 1× 的平均核心频率约 1655–1733 MHz，0.25× 约 1356–1380 MHz，设备 DVFS 与运行负载影响了绝对耗时；比较阶段应结合时钟和同一输入时间戳，而不是只看处理均值。

## 同图像特征与定位结果

同时间戳图像的 ORB 特征数量逐帧一致：与 0.25× 同步直通相比，1× 同步直通共有 830 帧，FIFO 1× 和 FIFO 0.25× 各有 832 帧，特征数量全部一致。这确认角点提取没有因播放速率或 FIFO 改变。

地图匹配却会改变。1× 同步直通与 0.25× 同步直通比较时，738 个有局部地图匹配统计的共同帧中，716 帧匹配数不同、714 帧内点数不同；同步直通 1× 的跟踪状态有 91/830 帧与 0.25× 不同。FIFO 1× 对 0.25× 的 832 帧比较中，跟踪状态同样有 91 帧不同。相反，在相同 1× 播放速度下，FIFO 与直通的 830 个共同帧跟踪状态一致，但地图匹配数仍有 695 帧、内点数有 710 帧不同。

这组结果把“角点是否提取出来”和“地图里是否有可匹配点”分开了：ORB 数量稳定，地图匹配和跟踪状态随处理速率改变，说明当前地图/LocalMapping 的并发进度与跟踪历史会影响定位。FIFO 能改善 1× 同步配对覆盖（本次多配出两对图像），但没有消除 1× 下约 90 帧的 `RECENTLY_LOST`；它也会改变 Tracking 与 LocalMapping 的调度，不能视作对原始同步执行逐帧等价的实现。

## 文件索引

- `comparison.txt`：四组统计、每阶段 p50/p95/p99、LocalMapping 子阶段与 tegrastats 汇总。
- 每组 `input_summary.csv.events.csv`：逐条 ROS 收包、配对、入队/出队、跟踪起止、位姿发布和未配对/丢弃事件。
- 每组 `per_pair_timeline.csv`：按图像 pair 汇总的接收时间、队列等待、cv_bridge、TrackRGBD 和地图指标。
- 每组 `slam_profile.csv`、`eval_metrics.csv`、`local_mapping.csv`、`tegrastats.log`：各自详细阶段值、匹配/内点/状态、关键帧处理时间和设备采样。
- `same_rate_1x_direct_vs_fifo32.csv`、`same_rate_025x_direct_vs_fifo32.csv`：相同播放速度下的逐帧匹配与状态对比。
- 各组 `algorithm_deltas_vs_direct_025x.csv`：逐帧对比 0.25× 同步直通结果。

## 结论

本次 normal1 测试没有发生本地 FIFO 容量溢出。1× 同步直通确实有两对中段图像到达 ROS 订阅但未进入同步回调；容量 32 的 FIFO 模式处理了这些 pair。固定 FIFO 可减少这类同步回调阻塞期间的配对缺失，但本次还不足以支持动态调节队列容量：队列峰值仅 7，状态仍会在 1× 与 0.25× 间变化。下一步如果要确认 ApproximateTime 丢消息的内部具体分支，需要单独为该策略增加内部 drop 计数；当前 ROS 公开接口只能观测未配对结果。
