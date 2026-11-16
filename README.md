# NetEase 1.21.130 Command Blocks Skill

[![Validate skill](https://github.com/smr520/bedrock-1-21-130-commands/actions/workflows/validate.yml/badge.svg)](https://github.com/smr520/bedrock-1-21-130-commands/actions/workflows/validate.yml)

这是一个面向 Minecraft 网易中国版 3.10 / BE 1.21.130 的命令方块技能包，用于设计、现代化、排错和审计不使用行为包、资源包、函数或 `tick.json` 的纯命令方块系统。国际版 1.21.130 作为兼容与交叉核对层。

它把要求落实为可直接复制的命令、四段式方块标注、CB 预算、选择器分叉成本、多人状态清理和测试清单。默认优先减少命令方块数量，同时保留多人选择、交易保护、持久化和可维护性。

作者：**一个高质量的神秘人**  
GitHub：[@smr520](https://github.com/smr520)  
QQ 交流群：**1031096520**  
项目地址：<https://github.com/smr520/bedrock-1-21-130-commands>

## 包含内容

- 网易 3.10 / BE1.21.130 命令边界：官方命令表、客户端 `/help`、真实语料观察和默认关闭的未验证命令。
- 1.19.50+ 现代 `execute ... run` 语法、`if score` 单目标约束、执行分叉预算与 Java 差异检查。
- 复杂系统建模层：行为契约、状态表、状态机/事务/队列/调度器、幂等和原子性。
- 条件链传播、成功次数、延迟 0/1、首刻执行、C-tick 与共享循环根语义。
- 菜单、商店、撤离、HUD、欢迎、计时、冷却、交易锁和 BOSS 状态模板。
- 网易高级玩法路由：FMBE/MBE、数据化 RPG、T 显、武器触发、UID 和二进制坐标。
- 1 格同分双人互传示例，含按钮归属、在线检查和同分失败路径。
- 3 格动作栏优先级仲裁，可在普通 HUD、撤离进度和菜单之间只显示一项。
- Wiki 来源矩阵，区分官方文档、社区技术 Wiki、版本交叉核对和用户语料，并记录许可与按需检索入口。
- 4 格“世界运行期间断开再进”事件状态，以及 5 格进服欢迎加延迟公告示例。
- 命令级、链级、JSON 链 spec、配方预算、传送目的地和 skill 整包校验脚本。
- 7 个可直接搭建的精简示例，以及 1 个机器可读链 spec。
- GitHub Actions 自动运行完整校验，主分支和拉取请求使用同一验收标准。
- 无第三方运行时依赖；校验工具只使用 Node.js 标准库和可选的 Python 标准库。

## 安装

把 `bedrock-1-21-130-commands` 目录复制到 Codex 的 skills 目录：

```text
$CODEX_HOME/skills/bedrock-1-21-130-commands
```

未设置 `CODEX_HOME` 时，默认位置通常是：

```text
~/.codex/skills/bedrock-1-21-130-commands
```

技能正文位于 `bedrock-1-21-130-commands/SKILL.md`。目录只包含 Markdown、JSON、YAML、Node.js 和 Python 文本文件。

## 快速校验

在 `bedrock-1-21-130-commands` 目录运行：

```powershell
node scripts\validate-skill.mjs
node scripts\selftest.mjs
python -B -X utf8 scripts\scan-corpora.py --self-test
```

规划多个系统的预算和共用状态：

```powershell
node scripts\plan-recipes.mjs server-starter-core player-hud hud-arbiter
```

校验结构化命令链并生成构建表：

```powershell
node scripts\validate-chain-spec.mjs examples\same-score-pair-teleport.spec.json --write same-score-plan.md
```

## 示例

| 示例 | 命令方块 |
| --- | ---: |
| 雪球菜单 | 11 |
| 金币商店 / 回收 | 6 |
| 撤离点 | 5 |
| 玩家 HUD | 1 |
| 运行中重进欢迎 + 延迟公告 | 5 |
| 多系统 HUD 仲裁层 | 3 |
| 同分双人互传 | 1 |
| 同分双人互传 spec | 1 |

聊天栏一次性执行的目标创建命令计入 0 CB。每个示例都说明准备命令、方块类型、条件、红石状态、延迟、摆放和测试步骤。

HUD 仲裁的 3 格只统计仲裁链本身。接入现有菜单、撤离或 HUD 时，要删除原来的独立动作栏块，再按“状态与动作格 + 仲裁格”重新统计总数。

## 使用边界

- 默认版本为网易中国版 3.10 / BE1.21.130；国际版、旧客户端和其他网易版本需要单独核对 ID 与语法。
- `schedule`、`function` 和 `reload` 在网易命令表中存在，但依赖 Add-on 函数或资源重载，不属于默认纯命令方块方案。
- `camera`、`inputpermission`、`dialogue`、`loot`、`place`、`recipe`、`scriptevent`、`hud` 和 `fog` 默认视为未验证或证据冲突；先 `/help`，再在目标客户端测试。
- `titleraw` 读取的是记分板值，不是玩家真实生命、饥饿或经验。
- `@a` 只选择在线玩家。专用事件记分项配合 `reset *` 可在 4 格识别世界运行期间的断开再进；完整退出世界再打开没有独立载入信号，需要实机确认首个玩家行为。玩家离线后不能对其本人执行命令。
- 前后在线人数差可以检测总人数净减少，但不能指出具体是谁离开；同一游戏刻有人进入又有人离开时可能互相抵消。
- `@p`、雪球落点和投射物附近选择在多人拥挤时可能选错玩家。
- 红石按钮不会把“按压者”传给命令方块；`@p` 只是位置近似，`@initiator` 只在 NPC 对话中有效。
- `as @a`、`at @a` 会复制执行实例，方块少不代表性能低；方案必须报告来源数、目标数和触发频率。
- 服务器性能取决于玩家数、每刻选择器范围和实体数量；通过静态检查不代表已经完成性能压测。
- 结构文件、行为包、资源包、函数、`schedule`、`reload` 和脚本不会作为纯命令方块方案的隐式依赖。
- FMBE/MBE 是实体加客户端动画的显示层，不是真实方块、碰撞体或红石检测对象。
- 外部仓库、旧教程或样本地图里出现过某条命令，不代表当前网易客户端已经验证；证据等级会保留在交付中。

## 反馈与支持

- 可复现的缺陷和明确的功能请求：[GitHub Issues](https://github.com/smr520/bedrock-1-21-130-commands/issues)
- 使用方法、命令思路和开放式讨论：[GitHub Discussions](https://github.com/smr520/bedrock-1-21-130-commands/discussions)
- 快速交流：QQ 群 **1031096520**
- 安全漏洞：使用仓库的 [Private vulnerability reporting](https://github.com/smr520/bedrock-1-21-130-commands/security/advisories/new)，不要在公开 Issue 中发布密钥或可利用细节

提问时请写出目标基岩版本、客户端平台、命令方块设置、预期结果、实际结果和最小复现步骤。命令文本和完整报错越具体，越容易定位。

## 验证状态

`v2.0.0` 已通过 21 份运行文档、25 份 Markdown 内部链接、命令语法、链级结构、JSON 链 spec、`if score` 单目标、传送目的地、配方预算、回归测试和敏感信息审计。发布环境未安装 Minecraft 客户端，因此所有配方仍标记为 `static-only`，没有宣称完成网易 1.21.130 实机验收。

详细结果见 [VALIDATION.md](VALIDATION.md)。

## 许可证

本发布版采用 [Apache License 2.0](LICENSE)。它允许个人和商业使用、修改与再分发，并提供明确的贡献者专利授权。第三方指令教程、压缩包和地图资产没有包含在本发布包中。链 spec 工作流参考的 MIT 项目归属见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

Minecraft 是 Microsoft 的商标。本项目与 Microsoft、Mojang 或 Minecraft 官方无隶属或背书关系。
