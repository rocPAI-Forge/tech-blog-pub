# RAX 开抽屉放方块：SO-101 SimStudio 上的非特权 Agent 控制

> RAX Drawer Place: Non-Privileged Agent Control on SO-101 SimStudio

**语言 / Language:** [中文](#中文) · [English](#english) · ⏱️ ~4 min read

> 📖 想看工具 API、RGB-D 感知、失败复盘与复现命令？ → [**技术详解版 / Deep-dive**](README-details.md)

> 系列上文：[SO-101 SimStudio 项目介绍](../so101-simstudio/README.md) · [Lab 01 抓取放置](../so101-simstudio-lab01-pnp/README.md) · [站上英文版 Lab 01](https://rocpai-forge.github.io/en/posts/so101-simstudio-lab01/)

![Open → place → close with top RGB, top depth, and side view](assets/gifs/open_place_close_rgbd.gif)

---

## 中文

### 从「能训策略」到「能写控制器」

[第一篇](../so101-simstudio/README.md)解决 ROCm 上的遥操作与录制；[Lab 01](../so101-simstudio-lab01-pnp/README.md) 打通了示范 → ACT / SmolVLA → 闭环评估。

抽屉任务更长：**拉开下层抽屉 → 把绿色方块放进托盘 → 再关上**。没有现成 teleop 示范时，默认上 VLA 并不划算。本篇走另一条路——**RAX 风格**：编码 Agent 只通过工具 API 探索场景，把经验**编译成确定性控制器**，再在锁定测试集上评一次分。

实践定义里的 RAX 不是「再训一个大模型」，而是：

```
explore（工具交互） → compile（Python 控制器） → freeze → locked test（一次）
```

### 非特权观测：相机与深度，而不是抽屉关节

Agent / 控制器**不能**读柜子布局、抽屉关节、方块真值位姿或接触标志——那些只留给评估器。公开观测是关节状态、相机标定、**顶视 RGB + 深度**、侧视 / 腕部 RGB。把手与方块必须从顶视 RGB-D 感知出来。

![RAX control and observation contract](assets/images/architecture-rax-flow.png)

![What the controller sees: top RGB, top depth, side RGB](assets/images/cameras-obs-roles.png)

### 结果（锁定测试，证据）

| 任务 | 程序 | 锁定 `test.json` |
| --- | --- | --- |
| 仅开合 | `labs/rax_drawer/open_close.py` | **16 / 20** |
| 开 → 放 → 关 | `labs/rax_drawer/rax_place/` freeze 3 | **15 / 20** |

Place 在 freeze 前：explore 0–23 为 18/24，held-out explore 24–43 为 13/20。锁定 15/20 **未**用于再调参。

![Phase strip: reset → open → pick → place → close](assets/images/phase-strip-place.png)

### 三条工程教训（精简）

1. 拉开后不要直 `go_home`——关节扫掠会把开着的抽屉顶回去；要 **fold-then-face** 再抓方块。  
2. 放置点在感知到的把手沿拉开方向 **再进 5.5 cm**，落在托盘内，而不是压在把手上。  
3. 放完再关：先侧向抬腕，再 **腕锁伺服** 对齐拉开轴，推回记录的抓握点。

仅开合在多种柜子平移 / 偏航下的泛化见下（顶视 + 侧视网格）：

![Open/close across six cabinet layouts](assets/gifs/open_close_grid_en.gif)

### 从哪里开始

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
# 使用含 labs/rax_drawer 的分支 / commit
make rocm-sync && source .venv-rocm/bin/activate

./labs/rax_drawer/rax_place/eval_locked.cmd
# 方法说明：labs/rax_drawer/rax_place/RAX_METHOD.md
```

- **代码：** [rocPAI-Forge/so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · lab：`labs/rax_drawer/`
- **技术详解：** [README-details.md](README-details.md)

---

## English

### From “can train a policy” to “can compile a controller”

The [intro post](../so101-simstudio/README.md) covered teleop and recording on ROCm; [Lab 01](../so101-simstudio-lab01-pnp/README.md) closed the imitation-learning loop (demos → ACT / SmolVLA → eval).

The drawer task is longer: **open the lower drawer → place a green cube in the tray → close**. With no teleop demos for that horizon, jumping to a VLA is a poor default. This post takes another path — **RAX-style**: a coding agent explores only through a tool API, **compiles a deterministic controller**, freezes it, and scores **once** on a locked test set.

RAX here is not “train another foundation model.” It is:

```
explore (tool use) → compile (Python controller) → freeze → locked test (once)
```

### Non-privileged observations: cameras and depth, not the drawer joint

The agent / controller must **not** read cabinet layout, the drawer joint, ground-truth cube pose, or contact flags — those stay in the evaluator. Public observations are joint state, calibration, **overhead RGB + depth**, and side / wrist RGB. The handle and cube must be perceived from top RGB-D.

![RAX control and observation contract](assets/images/architecture-rax-flow.png)

![What the controller sees: top RGB, top depth, side RGB](assets/images/cameras-obs-roles.png)

### Results (locked test, evidence)

| Task | Program | Locked `test.json` |
| --- | --- | --- |
| Open/close only | `labs/rax_drawer/open_close.py` | **16 / 20** |
| Open → place → close | `labs/rax_drawer/rax_place/` freeze 3 | **15 / 20** |

Before the place freeze: explore 0–23 scored 18/24; held-out explore 24–43 scored 13/20. The locked **15 / 20** was **not** used for further tuning.

![Phase strip: reset → open → pick → place → close](assets/images/phase-strip-place.png)

### Three engineering lessons (short)

1. After opening, do not go straight `go_home` — the joint sweep can shove the open tray shut; **fold-then-face** before the pick.  
2. Drop **5.5 cm behind** the perceived handle along the pull axis so the cube lands in the tray, not on the bar.  
3. After place: pitch away, then **wrist-locked servo** onto the pull axis and push back to the recorded grasp.

Open/close generalization across cabinet shifts / yaws (overhead + side grid):

![Open/close across six cabinet layouts](assets/gifs/open_close_grid_en.gif)

### Where to start

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
# use a branch / commit that includes labs/rax_drawer
make rocm-sync && source .venv-rocm/bin/activate

./labs/rax_drawer/rax_place/eval_locked.cmd
# method write-up: labs/rax_drawer/rax_place/RAX_METHOD.md
```

- **Code:** [rocPAI-Forge/so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · lab: `labs/rax_drawer/`
- **Deep-dive:** [README-details.md](README-details.md)
