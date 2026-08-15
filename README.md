# tech-blog-pub

技术实践笔记的**公开仓库（唯一来源）**。每个主题维护两个共存版本：**精简版**
（`README.md`，~3 分钟中英双语，面向 LinkedIn / X / 微信转发）与**技术详解版**
（`README-details.md`，完整工程细节与复现）。读者可快速了解，也可深入复现。

The public home (single source of truth) for my engineering practice notes. Each topic
keeps two coexisting versions: a **concise** `README.md` (~3-min bilingual digest for
LinkedIn / X / WeChat) and a **deep-dive** `README-details.md` (full engineering detail
and reproduction). **Authoring and publishing:** see [`AGENTS.md`](AGENTS.md) (single
source for agents — no other docs required).

## PhysicalAI

| 文章 / Post | 一句话 / One-liner |
| --- | --- |
| [openarm-rl-grasp](PhysicalAI/openarm-rl-grasp/) （[精简](PhysicalAI/openarm-rl-grasp/README.md) · [详解](PhysicalAI/openarm-rl-grasp/README-details.md)） | 我们教机械臂捡方块，它却自己发明了一种我们没教的抓法。 / We taught a robot arm to pick up a cube — and it invented a grip we never taught it. |
| [openarm-traj-gen-for-vla](PhysicalAI/openarm-traj-gen-for-vla/) （[精简](PhysicalAI/openarm-traj-gen-for-vla/README.md) · [详解](PhysicalAI/openarm-traj-gen-for-vla/README-details.md)） | 在 AMD ROCm 上把 OpenArm 的抓-放变成一台"专家轨迹数据引擎"，为 VLA 训练批量造数据。 / On AMD ROCm, turning OpenArm pick-and-place into an "expert trajectory data engine" that mass-produces data for VLA training. |
| [so101-simstudio](PhysicalAI/so101-simstudio/) （[精简](PhysicalAI/so101-simstudio/README.md) · [详解](PhysicalAI/so101-simstudio/README-details.md)） | 把 SO-101、MuJoCo 与 LeRobot 整合到 ROCm 仿真环境，用一台 Ryzen AI 笔记本就能开始机器人物理 AI。 / SO-101, MuJoCo, and LeRobot on ROCm — start robot physical AI from simulation on an AMD Ryzen AI laptop. |
| [so101-simstudio-lab01-pnp](PhysicalAI/so101-simstudio-lab01-pnp/) （[精简](PhysicalAI/so101-simstudio-lab01-pnp/README.md) · [详解](PhysicalAI/so101-simstudio-lab01-pnp/README-details.md)） | 闭环打通：Lab 01 抓取放置——仿真示范 → ACT/SmolVLA 训练 → MuJoCo 评估（ROCm / v0.1.3）。 / Closing the loop: Lab 01 pick-and-place — sim demos → ACT/SmolVLA train → MuJoCo eval on ROCm (v0.1.3). |
