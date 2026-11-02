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

### 0. What we borrowed, and what we wrote ourselves

A popular path in robot learning is to collect more human demos and scale the model (all kinds of VLAs). Change the arm or the task, and you often have to collect again. The policy also tends to work only on scenes that look like the demos.

[RAX](https://arxiv.org/abs/2610.22496) takes another path: a **coding agent** tries against the robot interface, and the attempts that work are **kept as a program**, instead of stacking demos and then training. The paper runs a broad study across robots and real hardware, and reports results on the order of +37.4 over a baseline.

**This note does not rerun those large experiments.** With no official RAX toolchain available, we used **Cursor plus a Session API we wrote ourselves** and practiced one short skill in the SO-101 sim: **open the drawer → place the green cube → close**. People also edited the code, so this is a human-and-agent programming practice. It is not a paper-scale replay of “a pure agent discovers the skill from scratch,” and it does not reuse official RAX code.

What we actually took from the paper, and put into our own code, is mainly this:

1. **No privileged sim state at control time.** The program cannot read “how many centimeters the drawer has slid” or the cube’s true pose. It may use joints, cameras, and depth. That is closer to a real robot, and it leaves room to swap in a real camera later.
2. **Practice, then freeze, then a closed-book test.** Development uses one set of scenes. The reported score uses another. After the test starts, the program is not edited to chase the score.
3. **A long skill as readable stages.** Open, grasp, place, and close stay explicit, instead of disappearing into a black-box network.
4. **This task has no ready teleop demos.** Forcing Lab 01’s VLA onto it is a poor fit. “Try, then write it down as a program” is the practical path.

The lab is on so101-simstudio **`main`**.

Same repo, two paths, next to Lab 01:

| | Lab 01 | This note |
| --- | --- | --- |
| Where the behavior comes from | Human teleop demos | No demos for this task; trials in practice scenes |
| What is left at the end | A neural policy | A Python controller |
| What control can see | Cameras + state (action labels exist at train time) | Tool API; cabinet layout and the drawer joint stay hidden |
| How it is scored | An agreed spawn evaluation | Develop on practice scenes + **one** locked test of 20 scenes |
| Number we report | e.g. ACT 32/50 | Open/close 16/20; open-place-close 15/20 (our rules, not the paper’s table) |

### 1. How one cycle actually runs

```
① Try a few times in practice scenes
② Write the reliable behavior down as a program (compile)
③ Freeze: stop editing the code to chase the test score
④ Score once on the locked scenes
```

Only four calls can move the arm: `reset`, `observe`, `step`, and `check_success`.

Cheating in sim is easy: read the drawer joint and the cube pose directly. We **leave those unread**. A real robot has no god view either, only motor angles and cameras. Keeping the same rule in sim is so the interface can still line up when we later swap in hardware, instead of taking a sim shortcut.

![Fig. 2 control and observation contract](assets/images/architecture-rax-flow.png)

**Fig. 2.** Who can see what: the side that writes the program gets public observations only through the tools. Drawer ground truth used for scoring stays inside the evaluator.

### 2. The scene, and what counts as success

The scene is a cabinet with a lower drawer and a green cube on the table. The drawer travels about 0–8 cm.

**Open/close only:** the open must touch the handle; the drawer must end at least about **6 cm** farther out than at the start of the episode; the close must touch the handle again and return to about **5 mm** of the start pose.  
**Open + place + close:** all of the above, and the cube must end in the drawer tray. The scorer decides that. The controller cannot read “is the cube already in the tray?” as a cheat signal.

| Camera | What it is for |
| --- | --- |
| Overhead `top` | RGB + **metric depth**. Finding the handle and the green cube relies on this view |
| Side `side` | RGB. Useful for watching the pose, and for the recording |
| Wrist `wrist` | A view near the gripper. The API exposes it; this program mostly uses the overhead view plus joint estimates |

![Fig. 3 observations the controller can see](assets/images/cameras-obs-roles.png)

**Fig. 3.** What control can see: overhead RGB, overhead depth, side RGB.

#### 2.1 Why depth has to be taken seriously

RGB alone can tell “that is the green cube, that is the black handle.” Shift or yaw the cabinet a little, and pixel size changes, so “how far is this in real space?” stops being stable.

RAX also stresses that an agent should turn **metric depth** into 3D points, then plan the grasp and the pull. We did a smaller version of that in sim:

1. Depth is stored in **millimeters**. The program converts to meters, then uses the camera calibration to get spatial coordinates.
2. Sim depth is fairly clean. It is there to check that the skill can run by looking, without reading the drawer joint.
3. Real depth will be noisier and have holes. The program should still own the point cloud it computes. The interface shape is aligned first; a RealSense / Gemini-class camera can replace the source later.
4. Without depth, color can still luck into the green cube. An action that needs a real distance, such as “place **5.5 cm** farther in, behind the handle,” is hard to keep stable.

That is why **Fig. 1** and **Fig. 3** put depth next to RGB. Depth is a number used for grasp and place, not a cosmetic filter.

### 3. Where the code lives

```
labs/rax_drawer/
  environment.py     sim, depth, scoring
  backend.py         robot-service shaped adapter
  open_close.py      open/close only (16/20)
  manifests/         practice scenes / locked test scenes
  rax_place/
    tools.py         Session: hides privileged state
    code/open_place_close/   the frozen open→place→close program (15/20)
    eval_locked.cmd  one command for the locked test
```

### 4. How the long task is split (frozen round 3)

What the explore phase tried out was compiled into a few files: perception, velocity moves, forward kinematics, Jacobian position servo, and the top-level `controller.py`. The entry is roughly: open the drawer, then pick and place, then close (see [`controller_stages_snippet.py`](assets/code/controller_stages_snippet.py)).

![Fig. 6 stage split](assets/images/stage-decomposition.png)

**Fig. 6.** Stages A–F. While opening, the program records “which way to pull” and “where the hand grasped.” Closing still uses those two, and never reads the drawer joint.

Why split it? Opening wants soft contact (velocity is easier to tune). Pick-and-place wants centimeter accuracy (joint position servo is easier to tune). After the place, the tray already holds the cube and the pose is messy. Split stages can be repaired one at a time on practice scenes. The top-level controller only passes geometric quantities such as pull direction and grasp point.

#### 4.1 How it “sees” the handle and the cube

Overhead RGB + depth becomes a cloud of points. A dark bar is fit as the lower handle, and the horizontal pull direction is estimated from it. The green region gives the cube center. If either is missing, the episode fails. The program does not fall back to a simulator object id.

#### 4.2 Open the drawer (mostly velocity)

Approach the handle → close the gripper → pull along the open direction. Look again at the handle (or the gripper) to confirm it actually moved, so the grasp is real. Pull on the order of another 7.5 cm (success requires at least 6 cm of extra opening). After release, step aside so the overhead view can see the cube.

#### 4.3 Pick it up and put it in (mostly position)

**Fold the arm, then face the cube (this matters).** After the open, a direct “return to the default pose” often sweeps the arm through the open drawer and shuts it. Folding first, then turning to face the cube, keeps the tray from being closed. That change came from a failure during practice.

Then servo the joints a little at a time to a pose above the cube and close the gripper. A gripper angle that is too “empty” counts as a miss. After the lift, place the cube **5.5 cm farther in** along the pull direction, measured from the **handle seen in this episode**. It should land in the tray, not on the handle bar. Carrying stays in position control. Switching back to velocity mid-carry once shook the cube off.

#### 4.4 Close it again

After the place, the wrist is often crooked. Retreat to the robot side of the drawer, pitch the wrist down, and **lock that wrist angle**. Push back toward the grasp position recorded at open time, finish with a short push, and ask the scorer whether it succeeded.

#### 4.5 Two ways of moving

| Mode | Roughly | Used for |
| --- | --- | --- |
| Velocity | Which way to slide, how fast the wrist turns, how fast the gripper opens or closes | Opening, stepping aside, the last bit of the close |
| Position | Which angle each joint should reach | Folding, grasping, carrying, the wrist-locked close |

Both go through the same `step` call. Only the action fields differ. A later edit to one stage does not have to smear across the whole program.

![Fig. 5 phase strip](assets/images/phase-strip-place.png)

**Fig. 5.** Snapshots from the start to the end of one successful episode.

![Fig. 8 side view of open/close](assets/gifs/open_close.gif)

**Fig. 8.** Side view of open/close only (practice scene 0).

### 4.6 What we changed so a small cabinet shift still works

“Generalization” here means: **the cabinet can shift a few centimeters and yaw a few degrees, and the same program still runs.** It does not mean new lighting, new textures, or a real robot. That work is not in this note.

**On the rules:**

- Practice scenes and locked-test scenes are drawn apart. The test list is not visible during development.
- Where the cabinet sits, and how much it yaws, stays hidden from the controller on every episode.
- Before the freeze, a slice of the practice list that was not used to tune details is kept as a self-check (about 13/20). That cuts “it only works on the episodes we just edited.”

**On seeing:**

- Every episode re-estimates handle direction and cube position from overhead RGB-D. World coordinates are not hard-coded.
- The place point is 5.5 cm farther in from the handle seen in this episode.
- Whether the open actually grasped is confirmed by looking again for motion, not by reading the drawer joint.

**On motion (changed after practice failures):**

| Change | What it was for |
| --- | --- |
| Fold, then face the cube; do not snap back to the default pose | Some layouts made the return sweep shut the drawer |
| Gripper-angle filter for an empty grasp | “I thought I had it” depended on where the cube sat |
| Stay in position control while carrying | Velocity after a layout change shook the cube off |
| Lock the wrist on the close, and reuse the grasp point from the open | After the place the pose was messy and the handle had moved relative to the hand |
| Two approach clearances (about 1.2 cm / 0.5 cm) | Contact distance was sensitive to the layout |

**Visible evidence:** Fig. 7 is the same open/close program on six cabinet layouts. Open → place → close on the locked test is **15/20**. Failures remain (out of reach, not fully closed, and so on), so this is **partial** generalization.

**Not in this note:** lighting or material randomization, simulated depth noise, a real-robot transfer, and the paper’s “more exploration, higher score” curves.

![Fig. 7 six layouts](assets/gifs/open_close_grid_en.gif)

**Fig. 7.** The same open/close program, six translation/yaw layouts (overhead on top, side view below, in each cell).

### 5. Where the scores come from, and what failed

| Round | Roughly, on practice scenes | Locked test |
| --- | --- | --- |
| Round 1 | self-check about 9/12 | **4 / 20** |
| Round 2 | fold-then-grasp; practice 4/12 | **3 / 20** |
| Round 3 | place 5.5 cm farther in, wrist-locked close; practice self-check below | **15 / 20** |

**How to read the numbers:** day-to-day edits happen only on the practice list. The locked 20 scenes are scored once after the freeze. The program is **not** edited after seeing a failing test (that would be editing against the answer). Before the round-3 freeze: about **18/24** on the first 24 practice episodes, and about **13/20** on another 20 practice scenes (used only to decide “can we freeze?”). The number we report outside is the locked test, **15/20**.

![Fig. 4 scoring protocol](assets/images/explore-freeze-test.png)

**Fig. 4.** Practice → freeze → one pass on the locked test.

Usual failures: the arm knocks the drawer shut while carrying the cube; the cube lands on the handle; the close misses the handle; a few layouts are out of reach. An earlier, less disciplined place script scored only about 6/20 on the same locked set, which is evidence that the task itself is hard. That old script cannot be imported into the current session controller.

### 6. Reproduce

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
make rocm-sync && source .venv-rocm/bin/activate

./labs/rax_drawer/rax_place/eval_locked.cmd

MUJOCO_GL=egl python -m labs.rax_drawer.rax_place.render_place_gif \
  --split test --scene 1
```

More notes in the repo: `labs/rax_drawer/rax_place/RAX_METHOD.md` and `PROCESS.md`. Freeze tag: `CONTROLLER_FROZEN_3`. Result file: `locked_test_3.json`.

### 7. What we deliberately left unused

We did not force SmolVLA / pi0.5 onto this drawer task (no demos, and the cameras do not match). We did not servo the drawer joint directly. We did not edit the program after looking at locked-test failures.

### 8. References

```
Huang et al., Scaling Online Exploration for Robot Agents, arXiv:2610.22496, 2026.
https://arxiv.org/abs/2610.22496
```

- Code: [so101-simstudio](https://github.com/rocPAI-Forge/so101-simstudio) · [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer)
- Concise digest: [README.md](README.md)
