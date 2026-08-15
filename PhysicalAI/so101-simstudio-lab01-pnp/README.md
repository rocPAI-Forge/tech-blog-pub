# 闭环打通：SO-101 SimStudio Lab 01 抓取放置（ROCm）

> Closing the Loop: SO-101 SimStudio Lab 01 Pick-and-Place on ROCm

**语言 / Language:** [中文](#中文) · [English](#english) · ⏱️ ~4 min read

> 📖 想看复现命令、参考成功率与 `reset_arm` 协议细节？ → [**技术详解版 / Deep-dive**](README-details.md)

> 系列上文：[SO-101 SimStudio 项目介绍（v0.1.2）](../so101-simstudio/README.md) · [站上英文版](https://rocpai-forge.github.io/en/posts/so101-simstudio/)

---

## 中文

### 从「能录」到「能训、能评」

[第一篇](../so101-simstudio/README.md)把 SO-101、MuJoCo 与 LeRobot 接到 **AMD ROCm** 上，解决的是：**在仿真里遥操作并采专家轨迹**。

**v0.1.3**（tag [`release-v0.1.3`](https://github.com/rocPAI-Forge/so101-simstudio/releases/tag/release-v0.1.3)）把链路再往前推一步——**Lab 01 抓取放置**：仿真示范 → ACT / SmolVLA 训练 → MuJoCo 闭环评估，并给出可下载的 Hub 参考资产。

示范可以用 **键盘 / Joy-Con / Leader** 任一遥操作（同一套 LeRobot v3.0 录制管线）。Lab 01 公开参考数据用 Leader 采集；你本地完全可以用键盘或 Joy-Con 走同一套 lab 脚本。

### 模仿学习在做什么

**模仿学习（Imitation Learning / 行为克隆）**的目标不是手写抓取规则，而是让策略从**专家示范**里学会「看见什么 → 做什么」。人（或遥操作者）完成若干次成功抓取放置；策略在观测（关节角、相机画面等）上拟合专家动作，再在仿真里闭环 rollout，用成功率检验是否真的学会了任务。

和强化学习不同：这里**不依赖奖励函数**，数据质量与覆盖面直接决定上限。Lab 01 把这条工业界常用的入门路径拆成三步：

| 阶段 | 作用 |
| --- | --- |
| **1. 数据抓取** | 遥操作采专家轨迹 → LeRobot v3.0 数据集（状态 + 图像 + 动作） |
| **2. Policy 训练** | 行为克隆：最小化预测动作与示范动作的差距（ACT / SmolVLA） |
| **3. Eval** | 策略接管机械臂，在 MuJoCo 里闭环跑任务，统计成功/失败 |

```
teleop demos  →  dataset  →  train (BC)  →  closed-loop eval
```

### Lab 01 一条线

| 阶段 | 做什么 |
| --- | --- |
| **录制** | `labs/lab01_pnp/record.cmd`（或换你的 teleop 配置） |
| **训练** | `train.cmd`（SmolVLA）/ `train_act.cmd`（ACT） |
| **评估** | 统一 `eval.cmd` + lab 内 YAML（全范围 / demo / 固定位姿） |
| **Hub** | 数据集 + ACT / SmolVLA 参考权重（可改成自己的 HF 账号） |

旋钮集中在 `_env.sh`，用 `LAB01_*` 覆盖；详细约定见仓库 [labs/README.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/main/labs/README.md)。

### 参考结果（同一 50 集数据）

在 **MI300X 50K** 检查点、全范围随机方块上（详见详解版）：

| 策略 | 成功率（示意） |
| --- | --- |
| **ACT** | **32/50（64%）** |
| **SmolVLA** | **11/50（22%）** |

固定位姿 demo 下 ACT 更高、SmolVLA 仍不稳定——说明「会训」≠「课堂演示一定稳」。成功标准与失败模式写在 lab runbook §6。

### Eval 实拍（ACT 固定位姿）

MuJoCo GUI 闭环评估片段（裁剪并约 1.5× 加速；完整 mp4 见 `assets/videos/`）：

![ACT pick-and-place eval in MuJoCo](assets/gifs/eval-act-pnp.gif)

![ACT 50K 训练损失（MI300X）](assets/images/act-loss-mi300x-50k.png)

### 从哪里开始

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
git checkout release-v0.1.3
make rocm-sync && source .venv-rocm/bin/activate

# 读 runbook，或直接拉 Hub 数据/权重做 eval（见 Lab 01 §7）
./labs/lab01_pnp/eval.cmd
```

- **代码 / Release：** [rocPAI-Forge/so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · [v0.1.3](https://github.com/rocPAI-Forge/so101-simstudio/releases/tag/release-v0.1.3)
- **Lab runbook：** [labs/lab01_pnp/lab01_pnp.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/main/labs/lab01_pnp/lab01_pnp.md)
- **技术详解：** [README-details.md](README-details.md)

---

## English

### From “can record” to “can train & eval”

The [intro post](../so101-simstudio/README.md) wired SO-101, MuJoCo, and LeRobot on **AMD ROCm** so you can **teleoperate in sim and collect expert trajectories**.

**v0.1.3** ([`release-v0.1.3`](https://github.com/rocPAI-Forge/so101-simstudio/releases/tag/release-v0.1.3)) closes the next loop — **Lab 01 pick-and-place**: sim demos → ACT / SmolVLA training → MuJoCo closed-loop eval, plus downloadable Hub reference assets.

Demos work with **keyboard, Joy-Con, or leader** on the same LeRobot v3.0 record path. The published Lab 01 reference set was collected with a leader arm; you can run the same lab scripts with keyboard or Joy-Con locally.

### What imitation learning is doing here

**Imitation learning (behavior cloning)** does not hand-code a grasp planner. A policy learns **observation → action** from **expert demos**: a human teleoperates successful pick-and-place episodes; the network fits those actions given joint state and camera frames; then you run closed-loop rollouts in sim and score success.

Unlike RL, there is **no reward function** to tune — data quality and coverage set the ceiling. Lab 01 packages the usual industry starter loop in three steps:

| Stage | Role |
| --- | --- |
| **1. Data collection** | Teleop expert trajectories → LeRobot v3.0 dataset (state + images + actions) |
| **2. Policy training** | Behavior cloning: match predicted actions to demos (ACT / SmolVLA) |
| **3. Eval** | Policy drives the arm in MuJoCo closed loop; count success / failure |

```
teleop demos  →  dataset  →  train (BC)  →  closed-loop eval
```

### One Lab 01 line

| Stage | What |
| --- | --- |
| **Record** | `labs/lab01_pnp/record.cmd` (or your teleop config) |
| **Train** | `train.cmd` (SmolVLA) / `train_act.cmd` (ACT) |
| **Eval** | Single `eval.cmd` + lab YAMLs (full-range / demo / fixed pose) |
| **Hub** | Dataset + ACT / SmolVLA reference weights (override to your HF id) |

Knobs live in `_env.sh` (`LAB01_*` overrides). Shared lab conventions: [labs/README.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/main/labs/README.md).

### Reference results (same 50-episode set)

On **MI300X 50K** checkpoints with full-range random cube spawn (details in the deep-dive):

| Policy | Success (indicative) |
| --- | --- |
| **ACT** | **32/50 (64%)** |
| **SmolVLA** | **11/50 (22%)** |

Fixed-pose demos raise ACT further; SmolVLA stays brittle — “trainable” ≠ “classroom-stable.” Success criteria and failure modes are in the lab runbook §6.

### Eval footage (ACT fixed pose)

Closed-loop MuJoCo GUI clip (trimmed, ~1.5× speed; full mp4 under `assets/videos/`):

![ACT pick-and-place eval in MuJoCo](assets/gifs/eval-act-pnp.gif)

![ACT 50K training loss (MI300X)](assets/images/act-loss-mi300x-50k.png)

### Where to start

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
git checkout release-v0.1.3
make rocm-sync && source .venv-rocm/bin/activate

# Read the runbook, or download Hub assets and eval (Lab 01 §7)
./labs/lab01_pnp/eval.cmd
```

- **Code / Release:** [rocPAI-Forge/so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · [v0.1.3](https://github.com/rocPAI-Forge/so101-simstudio/releases/tag/release-v0.1.3)
- **Lab runbook:** [labs/lab01_pnp/lab01_pnp.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/main/labs/lab01_pnp/lab01_pnp.md)
- **Deep-dive:** [README-details.md](README-details.md)
