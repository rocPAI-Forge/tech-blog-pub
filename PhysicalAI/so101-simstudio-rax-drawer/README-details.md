# RAX 开抽屉放方块：SO-101 SimStudio 上的非特权 Agent 控制

> RAX Drawer Place: Non-Privileged Agent Control on SO-101 SimStudio

**语言 / Language:** [中文](#中文) · [English](#english) · 📄 技术详解版 / Deep-dive

> ⚡ 只想快速了解？ → [**精简版 / Concise digest**](README.md)

> TL;DR：在 [SO-101 SimStudio](https://github.com/rocPAI-Forge/so101-simstudio) 的 `labs/rax_drawer/` 上，用 RAX 风格（工具 API → 编译控制器 → freeze → 一次锁定评测）完成 **开抽屉 → 放绿方块 → 关抽屉**。公开观测仅有关节 + 标定 + 顶视 RGB-D + 侧视/腕部 RGB。锁定测试：**开合 16/20**，**place 15/20**（freeze 3）。权威方法说明：[labs/rax_drawer/rax_place/RAX_METHOD.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/rax-drawer/labs/rax_drawer/rax_place/RAX_METHOD.md)。

> 系列上文：[项目介绍](../so101-simstudio/README-details.md) · [Lab 01 抓取放置](../so101-simstudio-lab01-pnp/README-details.md)

![Open → place → close with top RGB, top depth, and side view](assets/gifs/open_place_close_rgbd.gif)

---

## 中文

### 0. 这篇相对 Lab 01 多了什么

Lab 01 回答的是：**有专家示范时，如何训 ACT / SmolVLA 并闭环评估**。  
本篇回答的是：**没有抽屉开合/放置示范时，编码 Agent 如何在非特权观测下写出可复现的长程控制器，并诚实计分。**

| | Lab 01 PnP | RAX drawer place |
| --- | --- | --- |
| 数据 | 遥操作示范 | 无示范；Agent 探索 |
| 产出 | 神经网络策略 | 编译后的 Python 程序 |
| 观测 | 相机 + 状态（训练标签含动作） | 工具 API；无布局 / 抽屉关节 / 真值位姿 |
| 评测 | 50 集 spawn 协议 | explore 开发 + **一次** locked 20 场景 |
| 代表分数 | ACT 32/50 等 | place **15/20**；开合 **16/20** |

本机官方 Claude Code / RAX harness 凭证不可用时，由 Cursor 通过 `tools.Session` 扮演编码 Agent；工具面与 `RaxDrawerBackend` 的 `drawer_*` 对齐，便于日后接到真实 RAX robot service。

### 1. RAX 在本实践中的含义

```
① Explore          ② Compile              ③ Freeze → Locked test
Session(explore)   code/open_place_close/  CONTROLLER_FROZEN_N
短步工具交互        main(ctx) 确定性程序     仅一次跑 manifests/test.json
```

原则：

1. **只许四工具**：`reset` / `observe` / `step` / `check_success`。  
2. **explore ≠ test**：开发只用 `manifests/explore.json`；`test.json` 不用于调参。  
3. **Freeze 后再计锁定分**；锁定失败不得回流改代码（协议）。  
4. **交付物是程序**，不是聊天记录。

![RAX control and observation contract](assets/images/architecture-rax-flow.png)

### 2. 场景、成功判据与相机

场景：`SO101/scenes/smart_drawer/scene.xml`，下层抽屉滑动关节约 0–0.08 m，桌上绿方块。

**开合成功**：拉开过程中把手接触；相对本集复位基线至少多开 **6 cm**；推回时再次接触，回到基线 **5 mm** 内。  
**Place 成功**：上述开合条件 + 方块落在托盘 AABB 内（评估器判定；控制器拿不到该字段做控制）。

控制相机：

| 相机 | 角色 |
| --- | --- |
| `top` | 俯视 RGB + **度量深度**（类 Gemini 336L）；把手/方块感知主源 |
| `side` | 侧视 RGB；姿态交叉检查与录像 |
| `wrist` | 腕部 RGB；API 提供，本 place 控制器主要依赖顶视 RGB-D + 关节 FK |

![What the controller sees](assets/images/cameras-obs-roles.png)

深度在观测里是 **uint16 毫米**；感知代码转为米后，用标定反投影到世界系。

### 3. 模块地图

```
labs/rax_drawer/
  environment.py      RaxDrawerEnv：步进、深度渲染、成功判定
  backend.py          RaxDrawerBackend：RAX 服务形态 + PNG 打包
  open_close.py       非特权仅开合（报告 16/20）
  place_close.py      早期直连 env 变体（非报告程序；污染风险）
  manifests/{explore,test}.json
  rax_place/
    tools.py          Session：剥特权字段、审计 mcp*.jsonl
    code/open_place_close/   编译控制器（报告 15/20）
      perceive.py  ik.py  kinematics.py  motion.py  controller.py
    RAX_METHOD.md     PROCESS.md  PROTOCOL.md  AGENTS.md
    eval_locked.cmd   run_explore.py  run_test.py
```

### 4. 感知与控制设计（freeze 3）

**感知（`perceive.py`）**  
顶视 RGB-D → 有效点云 → 暗色横杆拟合下层把手并估水平拉开方向；绿色掩码取方块质心。无 MuJoCo geom ID。

**开抽屉**  
速度域靠近、夹紧、沿 `pull` 拉约 7.5 cm；用**再感知把手位移**或夹爪位移确认拉开（不读 `drawer_slide`）；松爪并清空托盘前方。

**抓放**  
关键失败模式：开完后直 `go_home` 会扫关抽屉。Freeze 3 用 **fold-then-face**，再用雅可比关节 `.pos` 伺服抓取；搬运保持位置域（中途切回速度曾掉方块）。放置点：把手沿 `pull` **再进 5.5 cm**（`PLACE_BEHIND_M`）。

**关抽屉**  
侧向抬腕 → 腕锁伺服对齐拉开轴 → 挤握推回记录抓握点，直到评估器接受「回位 + 方块在屉内」。

![Phase strip](assets/images/phase-strip-place.png)

侧视全程开合样例（explore scene 0）：

![Open and close side view](assets/gifs/open_close.gif)

六布局网格（偏航约 −10°～+9.4°，平移约 2–3 cm）：

![Open/close grid](assets/gifs/open_close_grid_en.gif)

### 5. 分数轨迹与失败复盘

| 轮次 | Explore / 诊断 | 锁定 |
| --- | --- | --- |
| Round 1 | 自测约 9/12 | **4 / 20** |
| Round 2 | fold-then-pick 保开屉，但抓/关不稳（explore 4/12） | **3 / 20** |
| Round 3 | 放置 5.5 cm；腕锁关；explore 0–23: 18/24；held-out 24–43: 13/20 | **15 / 20** |

常见失败：搬运推关抽屉；放置压到把手；关抽屉时错抓边缘；个别布局不可达（开合集上 scene 0）。  
对比（**非 RAX**）：早期特权/直连 `place_close` 路径在同一锁定集约 **6/20**——说明长程 place 本身难，而非「换个 harness 就过」。

**污染说明**：主机上已有手调 `place_close.py`。会话控制器**不得** import 它；审计日志与「不在 test 上调参」仍适用。

### 6. 复现

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
# checkout 含 labs/rax_drawer 与 freeze 3 的分支（如 rax-drawer）
make rocm-sync && source .venv-rocm/bin/activate

# 锁定 place 15/20
./labs/rax_drawer/rax_place/eval_locked.cmd

# 重渲 RGB-D GIF（EGL/OSMesa）
MUJOCO_GL=egl python -m labs.rax_drawer.rax_place.render_place_gif \
  --split test --scene 1

# 合同冒烟
MUJOCO_GL=egl python -m labs.rax_drawer.smoke --with-cameras
```

方法长文与模块说明：仓库内 `labs/rax_drawer/rax_place/RAX_METHOD.md`。  
过程日志：`PROCESS.md`；冻结标记：`session/CONTROLLER_FROZEN_3`；结果：`logs/locked_test_3.json`。

### 7. 刻意没用什么

- **SmolVLA / pi0.5 / 其它 VLA**：无抽屉开→放示范；相机与动作布局也不匹配 Lab 01 数据集。  
- **用抽屉关节 Y 伺服的「特权脚本」**。  
- **读锁定失败后再改控制器**（违反协议）。

### 8. 链接

- 代码：[rocPAI-Forge/so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio)  
- Lab：`labs/rax_drawer/` · Session：`rax_place/tools.py`  
- 精简版：[README.md](README.md)  
- 系列：[SimStudio 介绍](../so101-simstudio/README.md) · [Lab 01](../so101-simstudio-lab01-pnp/README.md)

---

## English

### 0. What this adds beyond Lab 01

Lab 01 answers: **with expert demos, how do we train ACT / SmolVLA and eval closed-loop?**  
This post answers: **without open/place demos, how does a coding agent write a reproducible long-horizon controller under non-privileged observations — and score it honestly?**

| | Lab 01 PnP | RAX drawer place |
| --- | --- | --- |
| Data | Teleop demos | No demos; agent exploration |
| Artifact | Neural policy | Compiled Python program |
| Observations | Cameras + state (actions as labels) | Tool API; no layout / drawer joint / GT poses |
| Eval | 50-ep spawn protocol | Explore + **one** locked 20-scene run |
| Headline score | e.g. ACT 32/50 | place **15/20**; open/close **16/20** |

When official Claude Code / RAX harness credentials were unavailable, Cursor acted as the coding agent through `tools.Session`. The tool surface matches `RaxDrawerBackend`'s `drawer_*` calls so a real RAX robot service can plug in later.

### 1. What RAX means in this practice

```
① Explore          ② Compile              ③ Freeze → Locked test
Session(explore)   code/open_place_close/  CONTROLLER_FROZEN_N
short tool traces  deterministic main(ctx) one pass on manifests/test.json
```

Rules: tool-only control; explore ≠ test; freeze before locked scoring; deliver a program, not a chat log.

![RAX control and observation contract](assets/images/architecture-rax-flow.png)

### 2. Scene, success, cameras

Scene: `smart_drawer` with a lower sliding drawer (~0–0.08 m) and a green table cube.

**Open/close success:** handle contact on the pull; ≥ **6 cm** beyond the episode baseline; contact on return within **5 mm** of baseline.  
**Place success:** the above plus the cube inside the tray AABB (evaluator-only).

| Camera | Role |
| --- | --- |
| `top` | Overhead RGB + **metric depth**; primary handle/cube perception |
| `side` | Side RGB; posture cross-check and footage |
| `wrist` | Gripper RGB; available on the API; place controller leans on top RGB-D + joint FK |

![What the controller sees](assets/images/cameras-obs-roles.png)

Depth arrives as **uint16 millimeters**; perception converts to meters and unprojects with calibration.

### 3. Module map

Same layout as the Chinese section: `environment.py` / `backend.py` / `open_close.py` / `rax_place/{tools,code,RAX_METHOD.md,eval_locked.cmd}`. The reported place program is only `rax_place/code/open_place_close/` after freeze 3 — not `place_close.py`.

### 4. Perception and control (freeze 3)

Perceive the lower handle and green cube from top RGB-D. Open with velocity contact along the estimated pull axis; confirm opening by **re-perceiving** motion, not by reading `drawer_slide`. Pick with Jacobian `.pos` servos after **fold-then-face** (a direct home sweep shuts the tray). Drop **5.5 cm behind** the handle along `pull`. Close with a pitch-away then **wrist-locked** servo back to the recorded grasp.

![Phase strip](assets/images/phase-strip-place.png)

![Open and close side view](assets/gifs/open_close.gif)

![Open/close grid](assets/gifs/open_close_grid_en.gif)

### 5. Score path and failures

Rounds 1→3 locked scores: **4/20 → 3/20 → 15/20**. Pre-freeze explore checks for round 3: 18/24 (0–23) and 13/20 (24–43). Failure modes: carrying the cube shuts the drawer; dropping onto the handle; missing the handle on close; occasional unreachable layouts. A non-RAX direct `place_close` path scored about **6/20** on the same locked set — the horizon is hard even outside the harness. Contamination: do not import the pre-existing hand-tuned `place_close.py` into the session controller.

### 6. Reproduce

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
# checkout the branch/commit with labs/rax_drawer and freeze 3 (e.g. rax-drawer)
make rocm-sync && source .venv-rocm/bin/activate

./labs/rax_drawer/rax_place/eval_locked.cmd

MUJOCO_GL=egl python -m labs.rax_drawer.rax_place.render_place_gif \
  --split test --scene 1

MUJOCO_GL=egl python -m labs.rax_drawer.smoke --with-cameras
```

See `labs/rax_drawer/rax_place/RAX_METHOD.md`, `PROCESS.md`, `session/CONTROLLER_FROZEN_3`, and `logs/locked_test_3.json`.

### 7. Intentionally unused

No SmolVLA / pi0.5 for this task (no demos; layout mismatch). No privileged drawer-joint servoing. No retuning from locked failures.

### 8. Links

- Code: [rocPAI-Forge/so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio)  
- Lab: `labs/rax_drawer/` · Session: `rax_place/tools.py`  
- Concise: [README.md](README.md)  
- Series: [SimStudio intro](../so101-simstudio/README.md) · [Lab 01](../so101-simstudio-lab01-pnp/README.md)
