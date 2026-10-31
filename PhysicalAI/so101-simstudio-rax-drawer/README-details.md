# RAX 开抽屉放方块：SO-101 SimStudio 上的非特权 Agent 控制

> RAX Drawer Place: Non-Privileged Agent Control on SO-101 SimStudio

**语言 / Language:** [中文](#中文) · [English](#english) · 📄 技术详解版

> ⚡ 只想快速看故事和分数？ → [**精简版**](README.md)（只有图 1、2、6）

> **这篇详解写什么：** 我们**借鉴了 RAX 的哪些想法**、在仿真里**具体怎么做**、为了柜子挪一点还能用**改了哪些细节**、分数怎么算、怎么自己复现。  
> **这篇不写什么：** 不宣称我们重新证明了 RAX 论文里大规模、多机器人的那些数字。

> 系列：[项目介绍](../so101-simstudio/README-details.md) · [Lab 01](../so101-simstudio-lab01-pnp/README-details.md) · 论文：[arXiv:2610.22496](https://arxiv.org/abs/2610.22496)

> **配图：** 图1 全程录像 · 图2 谁能看什么 · 图3 相机画面 · 图4 怎么打分 · 图5 时间切片 · 图6 分几步做 · 图7 六种柜子摆法 · 图8 侧面开合

![图1 全程任务录像](assets/gifs/open_place_close_rgbd.gif)

**图 1.** 保密测试里第 1 个场景的完整录像。上排：左彩色、右深度；下排：侧面。彩色认东西，深度量远近。

---

## 中文

### 0. 先把话说清楚：我们借鉴了什么

这两年机器人学习很火的一条路是：多采人的示范、把模型做大（各种 VLA）。可一换手臂或换任务，往往又要重新采数据；学出来的策略也容易只会「示范里见过的样子」。

[RAX 论文](https://arxiv.org/abs/2610.22496)换了个思路：让**会写代码的 Agent**直接对着机器人接口去试，把试成功的做法**写成程序**留下，而不是先堆示范再训练。论文在很多机器人和真机上做了系统实验，也报了相对基线大约 +37.4 分这类结果。

**我们这篇不打算复现那些大实验。** 没有官方 RAX 全套工具链时，是用 **Cursor + 自写的 Session 接口** 在 SO-101 仿真里做了一小段：**开抽屉 → 放绿方块 → 关上**。人也会改代码，所以这是「人机一起写程序」的实践，不是论文级「纯 Agent 从零发现」的复刻。

我们真正学过来、并落到代码里的，主要是这几条：

1. **控制时别偷看仿真特权**——不能读「抽屉滑了几厘米、方块真实坐标」；只能看关节、相机、深度（和真机更像，也方便以后换真相机）。  
2. **先练习、再冻结、再保密考试**——开发用一批场景，正式分数用另一批，考完不能再为了分数改程序。  
3. **长动作拆成几段可读代码**——开、抓、放、关写清楚，而不是一个黑盒网络。  
4. **这个任务没有现成遥操作示范**——硬套 Lab 01 的 VLA 不合适，先走「试 → 写成程序」更务实。

Lab 已合进 so101-simstudio 的 **`main`**。

和 Lab 01 对比（同一仓库，两条路）：

| | Lab 01 | 这篇 |
| --- | --- | --- |
| 数据从哪来 | 人遥操作示范 | 没有该任务示范；在练习场景里试 |
| 最后留下什么 | 神经网络策略 | 一段 Python 控制程序 |
| 控制时能看什么 | 相机 + 状态（训练时还有动作标签） | 工具接口；看不到柜子布局/抽屉关节真值 |
| 怎么打分 | 约定好的 spawn 评测 | 练习场景开发 + **一次**保密 20 场景 |
| 报告的数 | 如 ACT 32/50 | 开合 16/20；开放关 15/20（按我们自己的规矩，不是论文那张表） |

### 1. 实际怎么跑这一圈

```
① 在练习场景里试几次
② 把靠谱做法写成程序（compile）
③ 冻结：不再为测试分改代码
④ 在保密场景上只跑一轮打分
```

能动胳膊的接口只有四个：`reset`（重置）、`observe`（看）、`step`（动一下）、`check_success`（问成没成功）。

仿真里其实很容易作弊：直接读抽屉关节、方块坐标。我们**故意不用**。真机上也没有这些「上帝视角」，只有电机角度和相机。仿真里坚持同一套规则，是为了以后换真机时接口还能对得上，而不是在仿真里走捷径。

![图2 控制与观测契约](assets/images/architecture-rax-flow.png)

**图 2.** 谁能看什么：写程序的一边只能通过工具拿公开观测；打分用的抽屉真值等藏在评估器里。

### 2. 场景长什么样、怎样算成功

场景是带下层抽屉的柜子，桌上有一块绿方块。抽屉大概能拉出 0～8 厘米。

**只开合：** 拉开时要碰到把手；比这一局开始时至少多拉开约 **6 厘米**；推回去时再碰到把手，并回到开始位置附近（约 **5 毫米**以内）。  
**开+放+关：** 上面都要满足，并且方块最后躺在抽屉托盘里（这个由打分程序判断；控制程序读不到「方块是否已在屉里」当作弊信号）。

| 相机 | 干什么用 |
| --- | --- |
| 俯视 `top` | 彩色 + **能测距离的深度**；找把手和绿方块主要靠它 |
| 侧面 `side` | 彩色；方便人看姿势，也用于录像 |
| 腕部 `wrist` | 夹爪附近的画面；接口有，但本程序主要靠俯视 + 关节推算 |

![图3 控制器可见观测](assets/images/cameras-obs-roles.png)

**图 3.** 控制时能看到的画面：俯视彩色、俯视深度、侧面彩色。

#### 2.1 为什么要认真对待深度

光看彩色照片，能认出「那是绿方块、那是黑把手」，但柜子往旁边挪一点、转一点，像素大小就变了，很难稳定知道「在真实空间里离我多远」。

RAX 论文也强调：Agent 应该能用**带真实尺度的深度**把画面变成三维点，再规划抓和拉。我们在仿真里做了同一件事的缩小版：

1. 深度图按**毫米**存，程序先换成米，再用相机标定算到空间坐标。  
2. 仿真深度比较干净，用来验证「不偷看抽屉关节，只靠看也能干活」。  
3. 真机深度会更吵、有空洞，但程序仍然应该对自己算出来的点云负责——接口形状先对齐，以后再换 RealSense / Gemini 一类相机。  
4. 没有深度时，还能靠颜色碰运气找绿块；但「在把手后面再往里放 5.5 厘米」这种要靠真实距离的动作，就很难稳。

所以 **图 1** 和 **图 3** 才会把深度和彩色并排放：深度不是好看的滤镜，而是算抓取、放置位置时真用到的数。

### 3. 代码大致放在哪

```
labs/rax_drawer/
  environment.py     仿真环境、深度、打分
  backend.py         对接「机器人服务」形态
  open_close.py      只开合（成绩 16/20）
  manifests/         练习场景 / 保密测试场景列表
  rax_place/
    tools.py         Session：挡住特权信息
    code/open_place_close/   开→放→关的正式程序（15/20）
    eval_locked.cmd  一键跑保密测试
```

### 4. 长任务怎么拆成几步（冻结第 3 版）

探索阶段试出来的做法，最后收成几个文件：感知、速度移动、正运动学、用雅可比做位置伺服、以及总控 `controller.py`。入口大致是：先开抽屉，再抓放，再关上（见 [`controller_stages_snippet.py`](assets/code/controller_stages_snippet.py)）。

![图6 多阶段分解](assets/images/stage-decomposition.png)

**图 6.** 步骤 A～F。开抽屉时记下「往哪拉」和「手抓在哪」，关的时候还用这两样——始终不读抽屉关节。

为什么要拆开写？开抽屉要软接触（用速度更好调），抓放要厘米级准（用关节位置伺服更好调），关抽屉时托盘里已经有东西、姿势也乱了。拆开以后，练习场景里可以一段一段修；总控里只传递「拉开方向、抓点」这类几何量。

#### 4.1 怎么「看见」把手和方块

俯视彩色 + 深度 → 算出一堆空间点。暗色横杆拟合出下层把手，并估计水平拉开方向；绿色区域找出方块中心。找不到就本局失败——不会偷偷去读仿真物体 ID。

#### 4.2 开抽屉（偏速度控制）

靠近把手 → 夹紧 → 顺着拉开方向拉；再看一眼把手（或夹爪）是不是真的动了，确认抓住。大约再拉到 7.5 厘米量级（成功要求至少多开 6 厘米）。松手后往旁边让一点，别挡着俯视看方块。

#### 4.3 抓起来再放进去（偏位置控制）

**收臂再转正（很重要）：** 开完抽屉如果直接「回默认姿势」，胳膊扫过去常会把开着的抽屉顶回去。改成先收起来、再转到面对方块，托盘才不容易被关掉。这是练习时翻车后改出来的。

然后用关节位置一点点伺服到方块上方、夹紧；夹爪角度太「空」就当没抓住。抬起来后，在**当前看到的把手位置**沿拉开方向**再往里 5.5 厘米**放下——落在托盘里，而不是压在把手横杆上。搬运过程中保持位置控制；中途改回速度曾经把方块抖掉。

#### 4.4 再关上

放完后手腕姿势往往已经歪了。先退到抽屉靠机器人一侧，俯一下腕并**锁住这个腕角**，再对准开抽屉时记下的位置推回去，最后短推一下，问打分程序成没成功。

#### 4.5 两种「动手方式」

| 方式 | 大概在说什么 | 用在哪 |
| --- | --- | --- |
| 速度 | 往哪边滑、腕转多快、夹爪开合快慢 | 开抽屉、让开、关抽屉末一下 |
| 位置 | 每个关节转到多少度 | 收臂、抓、搬运、腕锁着关 |

都走同一个 `step` 接口，只是动作字段不一样。这样写清楚，以后改某一段不会整锅糊。

![图5 阶段时间条](assets/images/phase-strip-place.png)

**图 5.** 同一成功局里，从开始到结束的几张「快照」。

![图8 侧视开合](assets/gifs/open_close.gif)

**图 8.** 只开合时的侧面样子（练习场景 0）。

### 4.6 为了「柜子挪一点还能用」，我们改了什么

这里说的泛化，主要指：**柜子平移几厘米、转几度，同一套程序还能干活**。不是换灯光、换贴图，也还没上真机。

**规矩上：**

- 练习场景和保密测试场景分开抽；开发时看不到测试列表。  
- 每一局柜子摆哪、转多少，对控制程序保密。  
- 冻结前还在练习列表里留出一段「当轮没用来抠细节」的场景做自检（大约 13/20），减少「只会刚改过的那几局」。

**看的方式上：**

- 每一局重新用俯视彩色+深度估把手方向和方块位置，不写死世界坐标。  
- 放置点相对「这一局看到的把手」再往里 5.5 厘米。  
- 开合是否抓住，靠再看一眼有没有动，而不是读抽屉关节。

**动作上（练习里翻车后改的）：**

| 改动 | 为了解决什么 |
| --- | --- |
| 收臂再转正，禁止硬回默认姿势 | 有的摆法下一回姿势会扫关抽屉 |
| 夹爪角度过滤「空抓」 | 不同位置下「以为抓到了」 |
| 搬运一直用位置控制 | 换布局后用速度容易抖掉方块 |
| 关抽屉时锁腕 + 复用开抽屉时的抓点 | 放完后姿势乱、把手相对位置变了 |
| 靠近距离试两次（约 1.2 cm / 0.5 cm） | 接触远近对摆法敏感 |

**看得见的证据：** 图 7 是同一开合程序在六种柜子摆法下的格子图；开→放→关在保密测试上是 **15/20**。仍有失败（够不着、关不严等），所以是**部分**泛化。

**还没做：** 光照/材质随机、深度噪声仿真、真机迁移实验、以及论文那种「探索越多分数越高」的曲线。

![图7 六布局开合](assets/gifs/open_close_grid_en.gif)

**图 7.** 同一开合程序，六种平移/偏航摆法（每格上俯视、下侧面）。

### 5. 分数是怎么来的、翻过哪些车

| 轮次 | 练习里大致情况 | 保密测试 |
| --- | --- | --- |
| 第 1 轮 | 自测大约 9/12 | **4 / 20** |
| 第 2 轮 | 改成收臂再抓，练习 4/12 | **3 / 20** |
| 第 3 轮 | 放置偏后 5.5 cm、腕锁关；练习自检见下 | **15 / 20** |

**怎么读这些数：** 平时只在练习清单上改程序；保密的 20 个场景冻结后只考一次，**不能**看了不及格再改（否则等于对着答案改）。第 3 轮冻结前：练习前 24 局大约 **18/24**；另抽 20 局练习场景大约 **13/20**（只用来判断「能不能冻」）。对外说的是保密测试 **15/20**。

![图4 评分协议](assets/images/explore-freeze-test.png)

**图 4.** 练习 → 冻结 → 保密测试只考一次。

常见翻车：搬方块时顶上抽屉；放在把手上；关上时没抓准；个别摆法手臂够不着。以前那条「不太守规矩」的放置脚本，在同一保密集上大约只有 6/20——说明这任务本身就难。旧脚本不能 import 进现在的会话控制器。

### 6. 怎么自己复现

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
make rocm-sync && source .venv-rocm/bin/activate

./labs/rax_drawer/rax_place/eval_locked.cmd

MUJOCO_GL=egl python -m labs.rax_drawer.rax_place.render_place_gif \
  --split test --scene 1
```

更多说明在仓库里的 `labs/rax_drawer/rax_place/RAX_METHOD.md`、`PROCESS.md`。冻结标记：`CONTROLLER_FROZEN_3`；结果：`locked_test_3.json`。

### 7. 刻意没用的东西

没拿 SmolVLA / pi0.5 硬套这个抽屉任务（没有示范，相机也不匹配）；没用抽屉关节直接伺服；没在看过保密测试失败后再改程序。

### 8. 引用

```
Huang et al., Scaling Online Exploration for Robot Agents, arXiv:2610.22496, 2026.
https://arxiv.org/abs/2610.22496
```

- 代码：[so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer)  
- 精简版：[README.md](README.md)

---

## English

### 0. Honest scope

We **borrow and partially practice** [RAX](https://arxiv.org/abs/2610.22496): tool-only sensing (including metric depth), explore → compile → freeze → one locked test, and a long drawer skill as readable code. We do **not** redo the paper’s multi-robot scaling study or its +37.4-style tables. Human + Cursor co-wrote the controller when the official harness was unavailable. Lab is on **`main`**.

Compared with Lab 01 (teleop → BC): same platform, different path — **15/20** place and **16/20** open/close under **our** protocol.

### 1–2. Loop, scene, cameras, depth

Four tools only; no privileged drawer joint / GT poses for control (Fig. 2–3). Success needs handle contact, ≥6 cm open, return within ~5 mm; place also needs the cube in the tray (scorer-only). Overhead RGB-D is the main sense for handle and cube; depth gives metric distance so offsets like “5.5 cm behind the handle” stay meaningful when the cabinet moves (Fig. 1, 3).

### 3–4. Code layout and stages A–F

Packages under `labs/rax_drawer/rax_place/code/open_place_close/`. Stages: velocity open with re-perception; fold-then-face (no sweeping `go_home`); Jacobian pick; place 5.5 cm behind perceived handle; wrist-locked close reusing open-time `pull` / `grasp_xy` (Fig. 5–6, 8).

### 4.6 Layout generalization (what we actually did)

**Target:** same program under cabinet **xy / yaw** shifts—not lighting/texture/real-robot domain.

**Protocol:** explore vs locked test manifests; layout hidden from the controller; held-out explore self-check before freeze (~13/20).  
**Perception:** re-estimate handle/`pull`/cube each episode from RGB-D; relative place offset; confirm open by re-seeing motion.  
**Control fixes from explore failures:** fold-then-face; empty-grasp filter; stay in position mode while carrying; wrist-lock close; clearance retries.  
**Evidence:** Fig. 7 (six open/close layouts); locked place **15/20**. Still partial; no visual-domain random, no real robot, no exploration-scaling curve.

### 5–8. Scores, reproduce, citation

Rounds locked 4/20 → 3/20 → **15/20**; Fig. 4 explains explore vs freeze vs test. Reproduce with `eval_locked.cmd` on `main`. Cite Huang et al., arXiv:2610.22496. Concise digest: [README.md](README.md).
