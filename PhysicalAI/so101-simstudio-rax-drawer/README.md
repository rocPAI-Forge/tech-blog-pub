# RAX 开抽屉放方块：SO-101 SimStudio 上的非特权 Agent 控制

> RAX Drawer Place: Non-Privileged Agent Control on SO-101 SimStudio

**语言 / Language:** [中文](#中文) · [English](#english) · ⏱️ ~3 min read

> 📖 **精简版**只讲：我们借鉴了什么、任务是什么、成绩多少、怎么跑起来。  
> 想看深度相机、分步控制代码、怎么防「背题」、失败复盘 → [**技术详解版**](README-details.md)

> 系列上文：[项目介绍](../so101-simstudio/README.md) · [Lab 01 抓取放置](../so101-simstudio-lab01-pnp/README.md)  
> 论文：[RAX](https://arxiv.org/abs/2610.22496)

![图1 全程任务录像](assets/gifs/open_place_close_rgbd.gif)

**图 1.** 一次成功全过程：上面左边是俯视彩色，右边是俯视深度；下面是侧面看。彩色用来认「绿方块 / 把手」，深度用来量远近。

---

## 中文

### 我们在做什么

上一篇 [Lab 01](../so101-simstudio-lab01-pnp/README.md) 的路子是：人遥操作录示范 → 训练策略。  
这篇换一条路：参考 [RAX 论文](https://arxiv.org/abs/2610.22496) 的想法——让**会写代码的 Agent**在仿真里试，把试成功的做法写成**固定程序**，而不是先采一大包示范再训练。

具体任务是一长串动作：**拉开下层抽屉 → 把桌上的绿方块放进去 → 再把抽屉关上**。

程序**不能偷看**仿真里的「作弊信息」（比如抽屉滑了多少、方块的真实坐标），只能看关节角度、相机画面和深度图——和真机上能拿到的东西更接近。

先说清楚：我们是**借鉴并做了一小段实践**，不是把论文里多机器人、大规模探索的结论重新证明一遍。人 + Cursor 一起写代码，官方 RAX 工具链当时也没用上。

流程很简单：

```
先在练习场景里试（explore）→ 写成程序 → 冻结 → 在保密测试场景上只评一次
```

![图2 控制与观测契约](assets/images/architecture-rax-flow.png)

**图 2.** 程序只能通过几个工具接口动胳膊；抽屉真值之类的信息留给打分用，控制时拿不到。更细的相机说明见 [详解](README-details.md)。

### 成绩

| 任务 | 保密测试（20 个场景） |
| --- | --- |
| 只开合抽屉 | **16 / 20** |
| 开 → 放方块 → 关 | **15 / 20** |

为什么练习分和测试分要分开算 → 见详解里的 **图 4** 和说明。

![图6 多阶段分解](assets/images/stage-decomposition.png)

**图 6.** 长任务被拆成几步：开抽屉、让开、收臂、抓方块、放进去、再关上。每一步怎么写代码、怎么让柜子挪一点还能用 → 见 [详解](README-details.md)。

### 自己跑一遍

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
make rocm-sync && source .venv-rocm/bin/activate
./labs/rax_drawer/rax_place/eval_locked.cmd
```

代码在 [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer)（已在 `main`）。完整说明：[详解版](README-details.md)。

---

## English

### What this post is

[Lab 01](../so101-simstudio-lab01-pnp/README.md) collects teleop demos and trains a policy.  
Here we **borrow ideas from [RAX](https://arxiv.org/abs/2610.22496)**: a coding agent tries in sim and we **compile** a fixed program for **open drawer → place green cube → close**, without peeking at privileged sim state (drawer joint, true cube pose)—only joints, cameras, and depth.

**Scope:** a small, reproducible practice of that workflow (human + Cursor)—**not** a redo of the paper’s big multi-robot scaling study.

```
explore → compile → freeze → score once on a locked test set
```

![Fig. 2](assets/images/architecture-rax-flow.png)

**Fig. 2.** Tool-only control; scoring secrets stay hidden. More camera/depth detail in the [deep-dive](README-details.md).

### Scores

| Task | Locked test (20 scenes) |
| --- | --- |
| Open/close only | **16 / 20** |
| Open → place → close | **15 / 20** |

![Fig. 6](assets/images/stage-decomposition.png)

**Fig. 6.** The long task is split into stages. How each stage is coded, and what we did for layout generalization → [deep-dive](README-details.md).

### Run it

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio
make rocm-sync && source .venv-rocm/bin/activate
./labs/rax_drawer/rax_place/eval_locked.cmd
```

Code: [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer) on `main`. Full write-up: [README-details.md](README-details.md).
