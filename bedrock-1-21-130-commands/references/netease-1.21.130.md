# 网易中国版 1.21.130 渠道说明

本 skill 的默认目标是**网易中国版 3.10 / BE 1.21.130**。国际版 1.21.130 只在用户明确指定或需要交叉核对时作为第二目标。命令列表、客户端 `/help` 和实际地图语料都不能互相替代。

## 版本与证据

- 网易开发者官网将 3.10 标为 **V3.10 BE1.21.130**。
- 官网 3.10 更新时间表写明 2026-10-28 上线稳定版，2026-10-30 起玩家包体逐步更新。
- “BE1.21.130”不等于所有国际版命令、实体 ID、粒子和修复都已经同步到网易。命令能力仍以网易官方列表、目标客户端 `/help` 和实际测试为准。
- 用户提供的真实地图语料属于 `corpus-observed`：它能说明某种写法在样本中出现过，不能单独证明现在所有设备都有同一行为。

## 证据等级

| 等级 | 含义 | 交付规则 |
| --- | --- | --- |
| `official` | 网易开发者命令列表或版本说明明确给出 | 可以作为实现基线，仍记录目标版本 |
| `client-confirmed` | 已在网易目标客户端实际执行成功 | 可以用于正式方案，保留设备与版本 |
| `corpus-observed` | 只在你提供的网易地图、`.bdx`、`.mcworld` 或旧教程中出现 | 先改写为新语法，再通过 `/help` 或实机确认 |
| `international-cross-check` | 只在国际版文档中存在 | 默认不能当成网易可用能力 |
| `unverified` | 命令、参数或 ID 没有足够证据，或官方页面互相冲突 | 不能伪装成可直接交付，必须给替代方案 |

## 命令边界

网易官方命令列表明确包含 `clear`、`clearspawnpoint`、`clone`、`effect`、`enchant`、`event`、`execute`、`fill`、`function`、`gamemode`、`gamerule`、`give`、`kill`、`locate`、`mobevent`、`music`、`particle`、`playanimation`、`playsound`、`reload`、`replaceitem`、`ride`、`schedule`、`scoreboard`、`setblock`、`setworldspawn`、`spawnpoint`、`spreadplayers`、`stopsound`、`structure`、`summon`、`tag`、`tell`、`tellraw`、`testfor`、`testforblock`、`testforblocks`、`tickingarea`、`time`、`title`、`toggledownfall`、`tp`、`weather` 和 `xp`。

`damage` 在真实网易地图语料中出现过，但本页不把它当作官方列表的原生项；使用前运行 `/help damage`。`titleraw` 也属于网易地图常见但未在官方表中稳定列出的命令，必须用 `/help titleraw` 验证。

### 纯命令方块可用

以下命令适合做成纯命令方块系统：

- `execute`、`scoreboard`、`tag`、`testfor*`、`kill`、`tp`、`teleport`
- `setblock`、`fill`、`clone`、`structure`、`tickingarea`
- `give`、`clear`、`replaceitem`、`effect`、`enchant`
- `title`、`tellraw`、`titleraw`（先验证）、`playsound`、`particle`
- `camerashake`、`playanimation`、`event`、`mobevent`、`music`
- `damage`（语料观察，先验证）、`spreadplayers`、`ride`

命令方块版本的交付仍要遵守 `INPUT → VALIDATE → TRANSITION → OUTPUT → CLEANUP`，并逐个报告链头、类型、条件、红石和延迟。

### 不是纯命令方块默认能力

- `/function`：运行 Add-on 中的函数文件。网易命令表有它，但没有对应函数文件时不可用。
- `/schedule`：可以调度 Add-on 函数。它不能替代命令方块计时；纯方块方案使用延迟循环块、计分板倒计时或红石触发。
- `/reload`：重载函数、战利品表等内容，属于资源/行为包工作流，不是命令方块链的初始化手段。

因此，“网易命令表里有 `schedule`”和“纯命令方块版可以使用 `schedule`”是两个不同结论。默认交付选择后者。

## 未验证或未实装命令

网易官方命令列表和真实地图样本没有形成足够证据支持以下命令；默认从主方案中移除：

| 命令 | 默认处理 |
| --- | --- |
| `camera` | 未验证；用 `camerashake`、`tp ... facing`、`title`/`titleraw` 做镜头表现 |
| `inputpermission` | 未验证；用传送、效果、过场或明确的客户端能力代替 |
| `dialogue` | 未验证；网易 NPC 对话属于编辑器或专用组件，不要伪装成普通命令方块 |
| `loot` | 未验证；用 `give`、`clear`、`replaceitem` 或结构模板 |
| `place` | 未验证；用 `structure load` |
| `recipe` | 未验证；固定奖励用 `give`，复杂配方用明确的系统状态机 |
| `scriptevent` | 未验证；属于脚本/ModSDK 边界 |
| `hud` | 官方列表未列出；先 `/help hud`，并提供恢复原版 HUD 的路径 |
| `fog` | 官方页面存在“已列出”和“尚未实装”的冲突；默认不用，先 `/help fog` 和实测 |

不要用 Java 版命令补齐这些缺口。`data`、`item`、`attribute`、`bossbar`、`team`、`forceload`、`advancement`、`worldborder`、`spectate`、`datapack` 和 `fillbiome` 继续视为不可用或不属于目标范围。

## 新 execute 与选择器

网易 1.21.130 的真实地图语料中，新式 `execute` 占主导；旧式 `execute @a ~ ~ ~ ...` 仍有残留，但不能作为新图基线。

```text
execute as @a at @s run scoreboard players add @s coins 1
execute as @e[type=item,tag=!processed,c=1] at @s run kill @s
execute as @a[scores={menu=1..}] at @s run titleraw @s actionbar {"rawtext":[{"text":"菜单"}]}
```

注意：

- `as` 只换执行者，`at` 才换位置、旋转和维度。
- `if score` 的比较两侧都要解析为单一目标；`@a`、`@e` 不能直接放进比较。
- `hasitem` 的参数是 `quantity`，不是 Java 的 `count`；槽位要写 `slot.weapon.mainhand 0`、`slot.armor.head 0` 等形式。
- 选择器坐标、`dx/dy/dz`、`r/rm` 和命令方块所在位置要有明确的参照对象。远处机关和展示实体优先使用绝对体积或 `execute positioned`。

## 网易地图常见模式

### 计分板菜单与动作栏

菜单页面通常是一个整数分数；视角确认/取消由 `rx`/`rxm` 选择器触发，显示层用 `titleraw ... actionbar`。动作栏只有一个，多个菜单、HUD 和撤离提示必须仲裁优先级，不能各自每 tick 覆盖。

### 数据化 HUD

网易地图常用自建 `dummy` 分数显示生命、攻击、防御、经验、硬币和菜单状态。这是**模拟数据**：

- 装备和 Buff 层每 tick 先清零再重建，基础值保持持久。
- 最终属性只读，交易和伤害使用临时槽，结算后清理。
- `titleraw` 限频，只给有需求的玩家；大面板和高频刷新要单独做性能预算。
- 原版普通攻击不会自动同步真实生命和伤害。真实受击检测若使用网易语料中的耐久或实体探针技巧，必须标为 `corpus-observed` 并逐项实机确认。

### 结构、克隆与常加载

`structure save/load` 适合带方块实体的模板，`clone` 适合纯方块复制。远处循环方块和机关需要 `tickingarea`；结构加载后要重新检查实体、tag、效果和初始化状态。

### FMBE / MBE

FMBE 常用狐狸和 `playanimation` 伪装显示实体，MBE 常用盔甲架和物品模型。它们是**客户端视觉层**，不是真实方块、碰撞体或可被 `if block` 检测的空间。

- 一只实体通常只显示一个模型，先计算实体数量和刷新频率。
- 固定锚点、隐身、抗性、消音、区块加载和展示区绝对坐标都要写清。
- 多部件模型需要逐部件锚定；只靠一个大坐标偏移容易产生枢轴和前后分层错位。
- FMBE/MBE 的客户端效果需要截图校准，不能把静态命令检查写成“视觉已通过”。

## `/help` 实机门禁

首次使用任何不在 `official` 表中的网易命令时，先在目标客户端执行：

```text
/help <命令名>
```

再记录：

```text
渠道：网易中国版
客户端版本：3.10 / BE1.21.130
设备：Windows / 手机 / 租赁服
命令或 ID：
证据等级：
结果：补全可见 / 执行成功 / 报错 / 未测试
替代方案：
```

只有命令被补全并实际执行成功，才能把该条从 `unverified` 或 `corpus-observed` 升级。

## 来源

- [网易开发者：3.10 版本更新](https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/%E6%9B%B4%E6%96%B0%E4%BF%A1%E6%81%AF/3.10.html)，V3.10 BE1.21.130，稳定版与玩家包更新时间。
- [网易开发者：命令列表及概述](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/10-addon%E6%95%99%E7%A8%8B/%E7%AC%AC04%E7%AB%A0%EF%BC%9A%E6%8C%87%E4%BB%A4%E7%B3%BB%E7%BB%9F%EF%BC%8C%E4%BD%A0%E7%9A%84%E5%88%9B%E4%BD%9C%E7%AE%A1%E5%AE%B6/%E8%AF%BE%E7%A8%8B04.%E5%91%BD%E4%BB%A4%E5%88%97%E8%A1%A8%E5%8F%8A%E6%A6%82%E8%BF%B0.html)，官方命令表；`fog` 条目与其他官方页面的状态存在时间差。
- [网易开发者：常用命令及用法](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/15-%E7%8E%A9%E6%B3%95%E7%BB%84%E4%BB%B6%E6%95%99%E7%A8%8B/3-%E4%BA%86%E8%A7%A3%E6%88%91%E7%9A%84%E4%B8%96%E7%95%8C%E5%8E%9F%E7%89%88%E5%91%BD%E4%BB%A4/5-%E5%B8%B8%E7%94%A8%E5%91%BD%E4%BB%A4%E5%8F%8A%E7%94%A8%E6%B3%95.html)，基础命令语法。

最近核对日期：2026-11-16。
