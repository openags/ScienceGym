# 宇树本体与公开灵巧手资源选型

2026-10-24：项目负责人保留宇树本体约束，允许自行选择其他厂商公开、成熟的手部方案。
此前 H2 + Dex5-S Pro 的固定选型被替代；先验收资产与场景、再开发操作序列的顺序继续有效。

当前选择 **Unitree G1 29DoF rev 1.0 + Inspire FTP 左右五指手**，用于下一轮资产集成。
备选为 **G1 + Dex3-1 三指手**。选择依据是完整模型、官方安装关系和可复用软件资源，
不是关节数量最多或型号最新。细线处理、接线、薄膜操作和工具使用能力仍须逐项验证。

| 组合 | 已确认的官方资源 | 本项目处理 |
| --- | --- | --- |
| G1 + Inspire FTP | 宇树完整 URDF、左右手网格、腕部固定变换、惯性与 mimic 联动；NVIDIA Isaac Lab 的 FTP 抓放环境 | 当前首选，已下载并做结构检查 |
| G1 + Inspire DFQ | 宇树另一个完整 URDF；宇树 Isaac Lab 配置使用 DFQ 风格关节名称，含整身移动示例 | 单独候选，不能与 FTP 配置混用 |
| G1 + Dex3-1 | 宇树完整 URDF / MJCF；宇树 Isaac Lab 含 Dex3 抓放与全身示例 | 三指备选，需重新评估精细任务抓取方式 |
| H2 + Dex5-S Pro | 之前已保留本体与有据重建的手部草稿，但完整安装和物理参数未核实 | 历史候选，取消关键路径依赖 |

## 固定来源与实际获取范围

- [宇树官方 G1 描述](https://github.com/unitreerobotics/unitree_ros/tree/15ebe53f4cd77e7d745ae83b9d7ff90e685e8998/robots/g1_description)：commit `15ebe53f4cd77e7d745ae83b9d7ff90e685e8998`。下载 FTP URDF 及其引用的全部 **93 个网格**，保留原始字节、比例和 BSD-3-Clause 许可证。
- [NVIDIA Isaac Lab 机器人配置](https://github.com/isaac-sim/IsaacLab/blob/3c6e67bb5c7ada942a6d1884ab69338f57596f77/source/isaaclab_assets/isaaclab_assets/robots/unitree.py)：固定到 **v2.3.0**，commit `3c6e67bb5c7ada942a6d1884ab69338f57596f77`，包含 `G1_INSPIRE_FTP_CFG`。
- [NVIDIA 抓放环境](https://github.com/isaac-sim/IsaacLab/blob/3c6e67bb5c7ada942a6d1884ab69338f57596f77/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/pick_place/pickplace_unitree_g1_inspire_hand_env_cfg.py)：环境 ID 为 `Isaac-PickPlace-G1-InspireFTP-Abs-v0`。[集成 PR #3242](https://github.com/isaac-sim/IsaacLab/pull/3242) 已合入官方仓库。
- [宇树 Isaac Lab 环境](https://github.com/unitreerobotics/unitree_sim_isaaclab/tree/e30c25b1dffdf92ada1d6c8c1fe9a47bdde0fecc)：包含 G1 + Inspire、G1 + Dex3、H1-2 + Inspire，以及 `Isaac-Move-Cylinder-G129-Inspire-Wholebody`。已保留 README、机器人配置、关节模板、许可证和资产下载脚本供核对。

本地共保存 **105 个来源文件**，逐个记录 URL、commit、字节数、SHA-256 和许可证。
NVIDIA 外部 USD 与宇树 Hugging Face USD 包尚未下载或验证；它们的条款不能由代码许可证代替。
没有执行上游安装或资产清理脚本。

## 模型审计与示例适用范围

FTP URDF 有 97 个链接、96 个关节，其中 53 个可动关节、12 个 mimic 从动关节，
合计 41 个独立关节坐标：身体 29，加每手 6。每手的 12 个活动关节不是 12 个独立命令。
已检查来源哈希、完整网格、链接树、mimic 引用和无环性、有限关节限位、腕部关系，以及惯性张量基本条件。
四个固定传感器参考链接没有惯性元素，已如实记录；这不等同于传感器已经运行。

静态 GLB 直接从官方视觉网格、URDF 安装变换与颜色生成；只整体平移到地面，未缩放。
零关节角姿态用于外形检查，未经动力学平衡求解。材质粗糙度是显示默认值。

**NVIDIA 的上述示例设置了 `fix_root_link=True` 和 `disable_gravity=True`。**
其增益、力矩限制和接触设置是示例仿真参数，不是已核实的硬件能力；不可直接作为项目的
站立、行走、携物或完整操作证据。NVIDIA USD 的关节命名与本次宇树 URDF 不完全相同，
例如 `pinky` / `little`，需显式映射并核对实际 USD，不能仅凭相同商品名称直接套控制器。
宇树整身 Inspire 示例的 `L_index_proximal_joint` 等名称属于 DFQ 风格，也须单独审计。

## 后续集成顺序

当前已完成官方全身模型入场、MJCF 源坐标与联动映射、手掌碰撞分块，
以及 G1 专属静态空间筛查。实验室网页可查看 47 个工位接近点的候选姿态与
剩余冲突。详细范围见[集成记录](../../assets/unitree_g1_inspire_v1/README.md)。
这些资产检查不代表站立、抓取或完整操作已通过验证；下列验收顺序继续有效。

1. 以固定版本 URDF 为源，核对模拟器中的惯性、碰撞、联动约束、关节限位与驱动器；保留来源参数与推断参数的区别。
2. 对 G1 重新检查实验室台面可达性、双手操作空间、搬运包络、通道、相机和线缆安装。旧 H2 几何检查不迁移为 G1 的合格结论。
3. 让负责人验收这一版资产与场景。随后才开发传感器闭环的抓取、用工具和双手操作序列。
4. 独立验证重力、支撑接触、平衡、操作和完整分支；不以遥操作演示代替自主传感器闭环验收。

源文件与检查：[SOURCE.json](../../assets/unitree_g1_inspire_v1/SOURCE.json)、
[VERIFICATION.json](../../assets/unitree_g1_inspire_v1/VERIFICATION.json)、
[selection.json](../../assets/unitree_g1_inspire_v1/selection.json)。
本地模型检查页：[G1 + Inspire FTP](../../viewer/robot_resource_review_v1/index.html)。

离线复核：`OPENBLAS_NUM_THREADS=1 python assets/unitree_g1_inspire_v1/audit.py`。
重新从固定 commit 获取源文件：`python assets/unitree_g1_inspire_v1/fetch_sources.py`。
