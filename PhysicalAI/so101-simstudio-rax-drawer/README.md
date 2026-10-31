# RAX 开抽屉放方块：SO-101 SimStudio 上的非特权 Agent 控制

> RAX Drawer Place: Non-Privileged Agent Control on SO-101 SimStudio

**语言 / Language:** [中文](#中文) · [English](#english) · ⏱️ ~3 min read

> 📖 **精简版**只讲：借鉴了什么、做了什么任务、锁定成绩、怎么复现。  
> 工具 API、深度细节、A–F 控制代码、失败复盘 → [**技术详解版 / Deep-dive**](README-details.md)

> 系列上文：[SO-101 SimStudio 项目介绍](../so101-simstudio/README.md) · [Lab 01 抓取放置](../so101-simstudio-lab01-pnp/README.md)  
> 论文 / Paper：[RAX — *Scaling Online Exploration for Robot Agents*](https://arxiv.org/abs/2610.22496)

![图1 全程任务录像](assets/gifs/open_place_close_rgbd.gif)

**图 1.** 锁定测试场景 1：俯视彩色 | 俯视深度 + 侧视。彩色认目标，深度量距离。

---

## 中文

### 故事一句话

[Lab 01](../so101-simstudio-lab01-pnp/README.md) 走的是 **teleop → 模仿学习**。本篇换一条路：借鉴 [RAX](https://arxiv.org/abs/2610.22496) 的论点与方法，在仿真里用**非特权观测**（关节 + 相机 + 度量深度，不读抽屉关节/真值位姿）探索，把 **开抽屉 → 放绿方块 → 关抽屉** 编译成 Python 控制器，再锁定评测。

**诚实边界：** 这是 RAX **工作流的可复现切片**（人 + 编码 Agent），**不是**复现论文的多本体缩放或 +37.4 等结论。我们实践的是：API 契约、RGB-D、explore → 编译 → freeze → held-out 评测。

```
explore → compile → freeze → locked test（一次）
```

![图2 控制与观测契约](assets/images/architecture-rax-flow.png)

**图 2.** Agent 只经工具驱动环境；特权量留在评估器。（观测拆解与深度为何重要 → [详解 §2](README-details.md#2-场景成功判据与相机栈)）

### 锁定成绩

| 任务 | 锁定 `test.json` |
| --- | --- |
| 仅开合 | **16 / 20** |
| 开 → 放 → 关（freeze 3） | **15 / 20** |

分数怎么读、为何不能拿 test 再调参 → [详解 §5](README-details.md#5-分数轨迹与失败复盘) 与 **图 4**。

![图6 多阶段分解](assets/images/stage-decomposition.png)

**图 6.** 编译出的技能拆成开屉 / 清空 / 收臂 / 抓取 / 放置 / 关屉；阶段间传递几何量 `pull`、`grasp_xy`。各阶段用速度域还是关节 `.pos`、为何禁止直 `go_home` → [详解 §4](README-details.md#4-多阶段分解与控制代码freeze-3)。

### 从哪里开始

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio   # labs/rax_drawer 已在 main
make rocm-sync && source .venv-rocm/bin/activate
./labs/rax_drawer/rax_place/eval_locked.cmd
```

- **代码：** [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer) · **论文：** [arXiv:2610.22496](https://arxiv.org/abs/2610.22496)  
- **技术详解：** [README-details.md](README-details.md)（图 3–5、7–8 与模块/复现命令也在那里）

---

## English

### One-line story

[Lab 01](../so101-simstudio-lab01-pnp/README.md) is **teleop → imitation learning**. This post takes another path: we **borrow and partially practice** [RAX](https://arxiv.org/abs/2610.22496) — non-privileged observations (joints + cameras + metric depth; no drawer joint / GT poses), explore, compile an **open → place cube → close** Python controller, then freeze and score once.

**Honest scope:** a **reproducible RAX-workflow slice** (human + coding agent), **not** a reproduction of the paper’s multi-embodiment scaling or +37.4-style claims. What we practice: API contract, RGB-D, explore → compile → freeze → held-out eval.

```
explore → compile → freeze → locked test (once)
```

![Fig. 2 control and observation contract](assets/images/architecture-rax-flow.png)

**Fig. 2.** Tool-only control; privileges stay in the evaluator. (Camera/depth detail → [deep-dive §2](README-details.md#2-scene-success-camera-stack).)

### Locked scores

| Task | Locked `test.json` |
| --- | --- |
| Open/close only | **16 / 20** |
| Open → place → close (freeze 3) | **15 / 20** |

How to read explore vs locked scores → [deep-dive §5](README-details.md#5-score-path-and-failures) and **Fig. 4**.

![Fig. 6 stage decomposition](assets/images/stage-decomposition.png)

**Fig. 6.** Compiled skill stages A–F; hand off `pull` / `grasp_xy`. Velocity vs joint `.pos`, fold-then-face, wrist-lock close → [deep-dive §4](README-details.md#4-multi-stage-decomposition--control-code-freeze-3).

### Where to start

```bash
git clone --recursive https://github.com/rocPAI-Forge/so101-simstudio.git
cd so101-simstudio   # labs/rax_drawer is on main
make rocm-sync && source .venv-rocm/bin/activate
./labs/rax_drawer/rax_place/eval_locked.cmd
```

- **Code:** [`labs/rax_drawer/`](https://github.com/rocPAI-Forge/so101-simstudio/tree/main/labs/rax_drawer) · **Paper:** [arXiv:2610.22496](https://arxiv.org/abs/2610.22496)  
- **Deep-dive:** [README-details.md](README-details.md) (Figs. 3–5, 7–8, modules, reproduce commands)
