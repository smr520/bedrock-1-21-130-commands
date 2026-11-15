# Bedrock 1.21.130 Command Blocks Skill

这是一个面向 Minecraft 基岩版 1.21.130 的命令方块技能包，用于设计、现代化、排错和审计不使用行为包、资源包、函数或 `tick.json` 的纯命令方块系统。

它把要求落实为可直接复制的命令、四段式方块标注、CB 预算、多人状态清理和测试清单。默认优先减少命令方块数量，同时保留多人选择、交易保护、持久化和可维护性。

作者：**一个高质量的神秘人**  
GitHub：[@smr520](https://github.com/smr520)  
QQ 交流群：**1031096520**  
项目地址：<https://github.com/smr520/bedrock-1-21-130-commands>

## 包含内容

- 1.19.50+ 现代 `execute ... run` 语法与 Java 差异检查。
- 菜单、商店、撤离、HUD、欢迎、计时、冷却、交易锁和 BOSS 状态模板。
- 3 格动作栏优先级仲裁，可在普通 HUD、撤离进度和菜单之间只显示一项。
- 命令级、链级、配方预算和 skill 整包校验脚本。
- 6 个可直接搭建的精简示例。
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

## 示例

| 示例 | 命令方块 |
| --- | ---: |
| 雪球菜单 | 11 |
| 金币商店 / 回收 | 6 |
| 撤离点 | 5 |
| 玩家 HUD | 1 |
| 欢迎 + 延迟公告 | 4 |
| 多系统 HUD 仲裁层 | 3 |

聊天栏一次性执行的目标创建命令计入 0 CB。每个示例都说明准备命令、方块类型、条件、红石状态、延迟、摆放和测试步骤。

HUD 仲裁的 3 格只统计仲裁链本身。接入现有菜单、撤离或 HUD 时，要删除原来的独立动作栏块，再按“状态与动作格 + 仲裁格”重新统计总数。

## 使用边界

- 目标版本固定为国际版基岩 1.21.130；旧客户端和网易版本需要单独核对 ID 与语法。
- `titleraw` 读取的是记分板值，不是玩家真实生命、饥饿或经验。
- 纯指令不能可靠读取任意实体真实生命值，也不能精确识别每次离线或重新登录。
- `@p`、雪球落点和投射物附近选择在多人拥挤时可能选错玩家。
- 服务器性能取决于玩家数、每刻选择器范围和实体数量；通过静态检查不代表已经完成性能压测。
- 结构文件、行为包、资源包、函数、`schedule`、`reload` 和脚本不会作为纯命令方块方案的隐式依赖。

## 验证状态

`v1.0.0` 已通过文档结构、命令语法、链级结构、配方预算、脚本自测和敏感信息审计。发布环境未安装 Minecraft 客户端，因此所有配方仍标记为 `static-only`，没有宣称完成 1.21.130 实机验收。

详细结果见 [VALIDATION.md](VALIDATION.md)。

## 许可证

本发布版采用 [Apache License 2.0](LICENSE)。它允许个人和商业使用、修改与再分发，并提供明确的贡献者专利授权。第三方指令教程、压缩包和地图资产没有包含在本发布包中，适用条款见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

Minecraft 是 Microsoft 的商标。本项目与 Microsoft、Mojang 或 Minecraft 官方无隶属或背书关系。
