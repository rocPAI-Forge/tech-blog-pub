# RAX 开抽屉放方块：SO-101 SimStudio 上的非特权 Agent 控制

> RAX Drawer Place: Non-Privileged Agent Control on SO-101 SimStudio

**语言 / Language:** [中文](#中文) · [English](#english) · 📄 技术详解版 / Deep-dive

> ⚡ 只想快速了解？ → [**精简版 / Concise digest**](README.md)

> TL;DR：借鉴 [RAX](https://arxiv.org/abs/2610.22496)（*Scaling Online Exploration for Robot Agents*）的论点与方法，在 [SO-101 SimStudio](https://github.com/rocPAI-Forge/so101-simstudio) **`main`** 的 `labs/rax_drawer/` 上做一次 **部分实践 / 工作流切片**（非复现论文多本体缩放结论）：**工具 API → 编译控制器 → freeze → 一次锁定评测**，开抽屉 → 放绿方块 → 关抽屉。公开观测含顶视 **度量深度**。锁定：**开合 16/20**，**place 15/20**（freeze 3）。方法说明：[RAX_METHOD.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/main/labs/rax_drawer/rax_place/RAX_METHOD.md)。

> 系列上文：[项目介绍](../so101-simstudio/README-details.md) · [Lab 01 抓取放置](../so101-simstudio-lab01-pnp/README-details.md)  
> 论文：[arXiv:2610.22496](https://arxiv.org/abs/2610.22496) · [project](https://robot-agent-exploration.com)

> **配图编号（两版共用）：** 图1 全程录像 · 图2 观测契约 · 图3 可见观测 · 图4 评分协议 · 图5 阶段时间条 · 图6 多阶段分解 · 图7 六布局开合 · 图8 侧视开合（仅详解）

![图1 全程任务录像](assets/gifs/open_place_close_rgbd.gif)

**图 1 / Fig. 1.** 锁定测试场景 1 的全程录像：上排左俯视彩色、右俯视深度，下排侧视。彩色认把手和绿方块，深度量距离并算三维位置，侧视方便看出机械臂姿态。（与精简版图号一致。）

---

## 中文

### 0. 我们借鉴了什么、实践了什么（诚实边界）

机器人学习近年靠**缩放示范数据与模型容量**（VLA / WAM 等）进展很大，但换一个本体或任务，通常仍要重新采 teleop；学到的策略也被示范分布束缚。Huang 等人提出的 **RAX（Robot Agent eXploration）** 把主轴换成 **缩放在线探索**：编码 Agent 经感知与控制 API 试任务，把成功决策**编译**成可执行程序，并维护笔记/技能记忆。论文在多本体、仿真与真机上给出了探索规模与泛化、相对基线约 **+37.4** 等系统结果。

**本篇不声称：** 复现或验证上述论文级结论；也没有做探索预算扫描、多本体对照或官方 RAX harness 全自动发现。

**本篇确实借鉴并部分实践的：**

1. **非特权 API 契约**——控制不用仿真抽屉关节/真值位姿；公开观测含关节、标定、RGB 与**度量深度**（贴合真机、利于 sim2real 形状对齐）。  
2. **explore → 编译程序 → freeze → held-out 锁定评**——开发与正式分数分离。  
3. **长程铰接任务拆成可读子技能**——开 / 放 / 关写成 `controller.py`，而不是一条隐式策略。  
4. **相对 teleop+IL 的动机**：本任务无抽屉示范时，先走 RAX 式工作流往往比硬套 Lab 01 VLA 更务实。

官方 Claude Code / RAX harness 凭证不可用时，由 **Cursor + `tools.Session`** 扮演编码 Agent（人机协作痕迹存在；主机上曾有 `place_close.py`，会话控制器不得 import，但仍有污染风险）。工具面与 `RaxDrawerBackend` 的 `drawer_*` 对齐，便于日后接到真实 RAX service。Lab 已合入上游 **`main`**（PR #21）。

与 Lab 01（teleop → BC）对照——**同一平台，两条学习轴；本轴是 RAX 工作流切片，不是论文翻版**：

| | Lab 01 PnP | 本篇（借鉴 RAX 的切片） |
| --- | --- | --- |
| 数据 | 遥操作示范 | 无该任务示范；explore 迭代 |
| 产出 | 神经网络策略 | 编译后的 Python 程序 |
| 观测 | 相机 + 状态（训练标签含动作） | 工具 API；无布局 / 抽屉关节 / 真值位姿 |
| 评测 | 50 集 spawn 协议 | explore 开发 + **一次** locked 20 场景 |
| 代表分数 | ACT 32/50 等 | place **15/20**；开合 **16/20**（自身协议，非论文基线表） |

### 1. 实践中的 RAX 循环

```
① Explore          ② Compile              ③ Freeze → Locked test
Session(explore)   code/open_place_close/  CONTROLLER_FROZEN_N
短步工具交互        main(ctx) 确定性程序     仅一次跑 manifests/test.json
```

原则：只许 `reset` / `observe` / `step` / `check_success`；explore ≠ test；Freeze 后再计锁定分；交付物是程序。

仿真可轻易读 `drawer_slide`、方块 body、接触数组；我们**不用**这些特权量，因为真机只有关节与相机/深度。非特权是为了与 real API 同构，给 **sim2real** 打基础，而不是在 sim 里走捷径。

![图2 控制与观测契约](assets/images/architecture-rax-flow.png)

**图 2 / Fig. 2.** 控制与观测契约：Agent 只经 Session 四工具与环境交互；公开观测含关节与相机/深度，特权量留在隐藏评估器。

### 2. 场景、成功判据与相机栈

场景：`SO101/scenes/smart_drawer/scene.xml`，下层抽屉约 0–0.08 m，桌上绿方块。

**开合成功**：拉开时把手接触；相对本集基线至少多开 **6 cm**；推回再接触，回到基线 **5 mm** 内。  
**Place 成功**：上述 + 方块在托盘 AABB（评估器；控制器不可用该字段控制）。

| 相机 | 角色 |
| --- | --- |
| `top` | 俯视 RGB + **度量深度**（类 Gemini 336L）；把手/方块 3D 感知主源 |
| `side` | 侧视 RGB；姿态交叉检查与录像 |
| `wrist` | 腕部 RGB；API 提供；本 place 控制器主要用顶视 RGB-D + 关节 FK |

![图3 控制器可见观测](assets/images/cameras-obs-roles.png)

**图 3 / Fig. 3.** 控制器可见的非特权观测：俯视彩色、俯视深度、侧视彩色。

### 2.1 深度相机：为何是一等公民（仿真与真机）

RAX 论文明确：相对「只吃 RGB 的通才策略」，Agent 应能用 **metric depth**（及力）抬升点云、拟合物体甚至铰接模型，再在几何上搜动作。空气炸锅开屉放香蕉等真机例子，核心就是 RGB-D → 3D 模型 → 沿棱柱关节规划拉开。

本 lab 把同一思想压成可教学的最小闭环：

1. **数据形态**：`observe()` 返回 `depth_images["top"]`，**uint16 毫米**；感知转为米，配合标定反投影到世界系。  
2. **仿真价值**：MuJoCo `enable_depth_rendering` 给出近似理想深度——用来证明**算法与 API 契约**，而不是用 `drawer_slide` 作弊。柜子随机平移 / 偏航时，深度让「把手线 + 拉开法向」可估计。  
3. **真机迁移**：真实深度噪声、孔洞、反光更多，但程序仍应对「云 + 内参/外参」负责；真机可加接触探询等补偿（论文亦观察到力/接触补深度误差）。Sim 先把非特权几何管线跑通，再换传感器实现。  
4. **没有深度会怎样**：颜色分割仍可找绿块，但 **放置点 = 把手沿 pull 再进 5.5 cm**、拉开行程度量、关屉对准都失去稳定尺度；仅 RGB 的像素启发式在布局一变就碎。

所以 **图 1**（全程录像）和 **图 3**（观测拆解）才会把画面拼成三块：**俯视彩色 | 俯视深度 | 侧视彩色**。彩色用来认把手和绿方块；深度用来量远近、算三维位置；侧视方便人眼看清机械臂姿态。深度不是好看的配图，而是程序算抓取/放置点时真正用到的输入。

### 3. 模块地图

```
labs/rax_drawer/          # 已在 so101-simstudio main
  environment.py          RaxDrawerEnv：步进、深度渲染、成功判定
  backend.py              RaxDrawerBackend：RAX 服务形态 + PNG 打包
  open_close.py           非特权仅开合（报告 16/20）
  place_close.py          早期直连 env 变体（非报告程序）
  manifests/{explore,test}.json
  rax_place/
    tools.py              Session：剥特权字段、审计
    code/open_place_close/  编译控制器（报告 15/20）
    RAX_METHOD.md  PROCESS.md  PROTOCOL.md
    eval_locked.cmd
```

### 4. 多阶段分解与控制代码（freeze 3）

RAX 的交付物不是「一次 chat 里点几下」，而是把探索中验证过的决策**编译**成可复用程序。对本任务，Agent（本实践中为 Cursor + `Session`）最终落成：

```
code/open_place_close/
  perceive.py     # 顶视 RGB-D → 把手 / 方块
  motion.py       # 速度域：approach_xy / move_xy / slide
  kinematics.py   # 关节观测 → EE（FK）
  ik.py           # 阻尼雅可比 servo_to（关节 *.pos）
  controller.py   # open_drawer → pick_and_place → close_drawer
```

入口把长程拆成三个函数（见 [`assets/code/controller_stages_snippet.py`](assets/code/controller_stages_snippet.py)），再细分为 A–F（见图 6）：

![图6 多阶段分解](assets/images/stage-decomposition.png)

**图 6 / Fig. 6.** 编译技能的多阶段分解（A–F）；开屉记下的 `pull` / `grasp_xy` 交给关屉复用。

**为何要拆阶段：** 开屉要接触柔顺（速度域），抓放要厘米级到位（位置域 IK），关屉要在托盘被占用后仍对准把手。混在一个大循环里难调试；RAX 风格是先在 explore 上把子技能跑通，再在 `main` 里组合，阶段之间只传递 **`pull` / `grasp_xy` / 开后把手点`**——评估器里的抽屉关节始终不可见。

#### 4.1 感知公共件（`perceive.py`）

- 深度 mm→m，用 `top` 标定反投影有效像素 → 世界点云。  
- **下层把手**：ROI 内暗色横杆拟合直线，水平法向取朝向固定臂座的 `pull`（单位向量）。  
- **绿方块**：颜色掩码 + 点云质心。  
失败则 `RuntimeError`，该 episode 放弃——不回退读 MuJoCo geom。

#### 4.2 A–B：`open_drawer`（速度域）

1. `observe(cameras=True)` → `find_lower_handle`。  
2. `slide` / `wrist_flex` 俯身；`approach_xy` 到把手前 `GRASP_CLEARANCE_M`（约 1.2 cm），夹紧后再小拉。  
3. **确认抓住**：再次感知把手是否沿 `pull` 移动 ≥1 cm，或夹爪捏点移动 ≥1 cm（把手看不见时的后备）。失败则松爪后退换 clearance 重试。  
4. 沿 `pull` 再拉到约 `PULL_DISTANCE_M=0.075`（成功门槛 ≥6 cm）。  
5. 松爪；返回 `{"point", "pull", "grasp_xy"}` 给后续阶段。  
**B 清空**：`pick_and_place` 开头再沿 `pull` 滑开一段，避免夹爪挡顶视。

#### 4.3 C–E：`pick_and_place`（位置域为主）

**C fold-then-face（关键）**  
开完后若直接 `go_home`，关节插值会横扫开着的托盘把它顶回去。`_ready_for_pick` 改为两段关节种子：先收臂上折，再 yaw 朝前——托盘保持打开。这是 explore 里用失败反推写进代码的典型 RAX 修订。

**D 抓取**  
1. 再感知方块；`servo_to` 走若干路点落到 `GRASP_Z`。  
2. `servo_to`（`ik.py`）：用机器人模型雅可比，在观测关节上迭代，经 `shoulder_pan.pos` … 等 **位置动作** 下发（`duration_s≈1/30`）。  
3. 夹紧后读 `gripper.position_rad`：若 ≤ −0.05 视为空抓失败。  
4. 抬到 `LIFT_Z`；可选再看方块高度确认「在手里」。

**E 放置**  
1. 再估把手（失败则用开屉记录的 `point`）。  
2. `place_xy = handle_xy - pull * PLACE_BEHIND_M`（**0.055 m**）——落在托盘内，而不是压在横杆上（压杆会关屉或掉外面）。  
3. 先抬高再平移再落到 `PLACE_Z`；**全程保持位置域**（中途切回速度曾抖掉方块）。打开夹爪。

#### 4.4 F：`close_drawer`（腕锁伺服）

放完后腕部姿态常已偏离开屉时的俯身角；纯速度爬升容易「摸空」。程序：

1. 抬高并沿 `pull` 退到托盘机器人一侧。  
2. 一次 `wrist_flex_rate` 俯身，**锁住**此时腕关节角。  
3. 在 `lock_wrist=True` 下 `servo_to` 对准开后把手附近 → 夹紧 → 再伺服到开屉记录的 `grasp_xy`，必要时 `move_xy` 挤握收尾。  
4. 短速度推一下；`check_success` 看回位 + 方块在屉内。

#### 4.5 双动作模式小结

| 模式 | 工具动作 | 用在 |
| --- | --- | --- |
| 速度 | `vx/vy/vz`, `wrist_flex_rate`, `gripper_delta` | 开屉接触、清空、关屉末推 |
| 位置 | `*.pos`（经 `servo_to` / `_send`） | 收臂、抓取、搬运、腕锁关屉 |

同一 `Session.step`；环境按 key 名分流。这与 RAX「程序里显式写感知—规划—控制」一致：模式切换是可读的工程决策，不是隐式策略网络。

![图5 阶段时间条](assets/images/phase-strip-place.png)

**图 5 / Fig. 5.** 成功轨迹时间切片：reset → open → pick → place → close。

![图8 侧视开合样例](assets/gifs/open_close.gif)

**图 8 / Fig. 8.** 仅开合任务的侧视样例（explore scene 0）；详解版增补，精简版未单列。

![图7 六布局开合](assets/gifs/open_close_grid_en.gif)

**图 7 / Fig. 7.** 同一开合程序在六种柜子布局下的表现。

### 5. 分数轨迹与失败复盘

| 轮次 | Explore / 诊断 | 锁定 |
| --- | --- | --- |
| Round 1 | 自测约 9/12 | **4 / 20** |
| Round 2 | fold-then-pick（explore 4/12） | **3 / 20** |
| Round 3 | 放置 5.5 cm；腕锁关；explore 自检见下 | **15 / 20** |

**分数怎么读：** 开发只改 explore 清单上的程序；`test.json` 的 20 个布局冻结后只评一次，**禁止**用锁定失败再调参。Round 3 冻结前的 explore 自检：前 24 景 **18/24**；另 20 个未参与当轮调试的 explore 景 **13/20**（只判断「能否冻结」）。对外报告的是锁定 **15/20**（见图 4）。

![图4 评分协议](assets/images/explore-freeze-test.png)

**图 4 / Fig. 4.** explore → freeze → 锁定 test 只评一次；18/24、13/20 是冻结前自检，15/20 是对外成绩。

常见失败：搬运推关抽屉；放置压把手；关屉错抓；个别布局不可达。非 RAX 的 `place_close` 对照约 **6/20**。勿把旧 `place_close.py` import 进会话控制器。

### 6. 复现（`main`）

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
make rocm-sync && source .venv-rocm/bin/activate

./labs/rax_drawer/rax_place/eval_locked.cmd

MUJOCO_GL=egl python -m labs.rax_drawer.rax_place.render_place_gif \
  --split test --scene 1

MUJOCO_GL=egl python -m labs.rax_drawer.smoke --with-cameras
```

- 方法：[RAX_METHOD.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/main/labs/rax_drawer/rax_place/RAX_METHOD.md)  
- 过程：`PROCESS.md` · 冻结：`session/CONTROLLER_FROZEN_3` · 结果：`logs/locked_test_3.json`  
- 论文：[arXiv:2610.22496](https://arxiv.org/abs/2610.22496)

### 7. 刻意没用什么

SmolVLA / pi0.5（无示范、布局不匹配）；特权抽屉关节伺服；读锁定失败后再改控制器。

### 8. 引用与链接

```
Huang et al., Scaling Online Exploration for Robot Agents, arXiv:2610.22496, 2026.
https://arxiv.org/abs/2610.22496
```

- 代码：[rocPAI-Forge/so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer)  
- 精简版：[README.md](README.md) · 系列：[介绍](../so101-simstudio/README.md) · [Lab 01](../so101-simstudio-lab01-pnp/README.md)

---

## English

### 0. What we borrow vs what we claim (honest scope)

**RAX** ([Huang et al., arXiv:2610.22496](https://arxiv.org/abs/2610.22496)) argues for scaling **online exploration**: coding agents interact through perception/control APIs, compile successful decisions into programs, and keep notes/skills. The paper’s multi-embodiment scaling numbers (including roughly **+37.4** vs strong baselines) are **not** reproduced or validated here.

**This post borrows and partially practices:** non-privileged API sensing (including metric depth); explore → compile → freeze → held-out locked eval; long-horizon articulated skills as readable code; a pragmatic alternative to teleop+IL when drawer demos are missing.

**This post does not claim:** a full RAX empirical twin, exploration-budget scaling curves, or fully autonomous discovery under the official harness. Cursor + `Session` stood in for the coding agent (human–agent co-authorship; prior `place_close.py` is a contamination risk even if unused). Lab is on upstream **`main`** (PR #21).

| | Lab 01 PnP | This lab (RAX-inspired slice) |
| --- | --- | --- |
| Data | Teleop demos | No task demos; explore iteration |
| Artifact | Neural policy | Compiled Python program |
| Observations | Cameras + state | Tool API; no layout / drawer joint / GT poses |
| Eval | 50-ep spawn protocol | Explore + **one** locked 20-scene run |
| Headline score | e.g. ACT 32/50 | place **15/20**; open/close **16/20** (our protocol, not the paper’s tables) |

### 1. RAX loop in this practice

```
① Explore → ② Compile → ③ Freeze → Locked test (once)
```

Tool-only control; explore ≠ test; deliver a program. We refuse sim privileges (`drawer_slide`, GT poses, contacts) so the pipeline matches a real robot API and supports **sim2real**. See **Fig. 2**.

![Fig. 2 control and observation contract](assets/images/architecture-rax-flow.png)

**Fig. 2** (same as 图 2). Control and observation contract.

### 2. Scene, success, camera stack

`smart_drawer`: lower slide ~0–0.08 m, green table cube. Open/close needs handle contact, ≥6 cm past baseline, return within 5 mm; place also needs the cube in the tray AABB (evaluator-only).

| Camera | Role |
| --- | --- |
| `top` | Overhead RGB + **metric depth**; primary 3D perception |
| `side` | Side RGB; posture cross-check / footage |
| `wrist` | Gripper RGB; API-available; place path leans on top RGB-D + FK |

![Fig. 3 controller observations](assets/images/cameras-obs-roles.png)

**Fig. 3** (same as 图 3). Non-privileged views available to the controller.

### 2.1 Depth as a first-class citizen (sim and real)

RAX argues agents should lift **metric depth** (and force) into point clouds and object / articulated models, then plan in geometry — as in real air-fryer drawer examples in the paper. This lab compresses that into a teaching loop:

1. **Format:** `depth_images["top"]` as uint16 **millimeters**; convert to meters and unproject with calibration.  
2. **Sim:** MuJoCo depth rendering validates the **non-privileged geometric pipeline**, not `drawer_slide` cheats; depth keeps handle-line + pull normal estimable under layout randomization.  
3. **Real:** Noisier depth, same program ownership of cloud + extrinsics; contact probing can patch depth error (also noted in RAX).  
4. **Without depth:** color still finds the cube, but place offsets (**5.5 cm behind the handle along pull**), open stroke, and close alignment lose stable metric scale.

That is why **Fig. 1** (full-episode clip) and **Fig. 3** (observation breakdown) lay out **overhead color | overhead depth | side color**. Color finds the handle and green cube; depth measures distance for 3D place/grasp; the side view helps humans read arm posture. Depth is a control input, not decoration.

### 3. Module map

Same layout as the Chinese §3: `labs/rax_drawer/` on `main`, with `rax_place/code/open_place_close/` holding the reported freeze-3 controller.

### 4. Multi-stage decomposition & control code (freeze 3)

RAX delivers a **compiled program**, not a one-off chat trace. The agent (here Cursor + `Session`) landed:

`perceive.py` · `motion.py` · `kinematics.py` · `ik.py` · `controller.py`

`main(ctx)` chains `open_drawer` → `pick_and_place` → `close_drawer`, refined as stages **A–F** (see **Fig. 6**). Stages hand off **`pull` / `grasp_xy` / opened handle point`** — never the drawer joint.

![Fig. 6 stage decomposition](assets/images/stage-decomposition.png)

**Fig. 6** (same as 图 6). Multi-stage skill A–F.

**A–B Open (velocity):** RGB-D lower handle; approach / squeeze / pull along `pull`; confirm by re-perceiving handle or pinch motion; record geometry; clear aside.

**C Fold-face:** two joint seeds instead of `go_home` so the arm does not sweep the open tray shut (an explore failure written into code).

**D Pick:** Jacobian `servo_to` via joint `*.pos`; gripper angle rejects empty grasps; lift and verify.

**E Place:** `place_xy = handle_xy - pull * 0.055`; stay in position mode while carrying; open gripper.

**F Close:** pitch away on the robot side of the tray; **wrist-lock** and servo onto the open-time axis back to `grasp_xy`; short velocity finish; `check_success`.

Velocity keys (`vx`/`vy`/…) vs position keys (`*.pos`) share one `Session.step`; the env routes by key name — an explicit engineering choice in the RAX program.

Entry sketch: [`assets/code/controller_stages_snippet.py`](assets/code/controller_stages_snippet.py). Full Chinese narrative: §4 above.

![Fig. 5 phase strip](assets/images/phase-strip-place.png)

**Fig. 5** (same as 图 5). Time strip of one successful episode.

![Fig. 8 side open/close](assets/gifs/open_close.gif)

**Fig. 8** (same as 图 8). Side-view open/close sample (details-only extra).

![Fig. 7 open/close grid](assets/gifs/open_close_grid_en.gif)

**Fig. 7** (same as 图 7). Open/close across six cabinet layouts.

### 5. Score path and failures

Locked **15/20** after rounds 4/20 → 3/20 → 15/20. Pre-freeze explore self-checks (18/24 and 13/20) only decide readiness to freeze; the locked score was not used for retuning (see **Fig. 4**).

![Fig. 4 scoring protocol](assets/images/explore-freeze-test.png)

**Fig. 4** (same as 图 4). Explore → freeze → one locked test.

Failure modes: carrying shuts the drawer; drop onto the handle; miss on close; unreachable layouts. Non-RAX `place_close` ≈ 6/20 on the same locked set.

### 6. Reproduce (`main`)

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
make rocm-sync && source .venv-rocm/bin/activate

./labs/rax_drawer/rax_place/eval_locked.cmd

MUJOCO_GL=egl python -m labs.rax_drawer.rax_place.render_place_gif \
  --split test --scene 1
```

[RAX_METHOD.md](https://github.com/rocPAI-Forge/so101-simstudio/blob/main/labs/rax_drawer/rax_place/RAX_METHOD.md) · [arXiv:2610.22496](https://arxiv.org/abs/2610.22496)

### 7. Intentionally unused

No SmolVLA / pi0.5 for this task; no privileged drawer-joint servoing; no retuning from locked failures.

### 8. Citation and links

```
Huang et al., Scaling Online Exploration for Robot Agents, arXiv:2610.22496, 2026.
https://arxiv.org/abs/2610.22496
```

- Code: [so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer)  
- Concise: [README.md](README.md) · Series: [intro](../so101-simstudio/README.md) · [Lab 01](../so101-simstudio-lab01-pnp/README.md)
