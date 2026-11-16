# 网易 3.10 / BE1.21.130 与兼容要点

## 版本信息

| 项目 | 内容 |
| --- | --- |
| 默认渠道 | **网易中国版 3.10 / BE1.21.130** |
| 网易稳定版 | 2026-10-28 上线；2026-10-30 起玩家包体逐步更新 |
| 基岩底层版本 | **1.21.130** |
| 更新名 | Mounts of Mayhem |
| 发布日期 | 2025-12-09 |
| 对应 Java 版 | 1.21.11 |
| 命令语法 | 1.19.50+ 新 `execute`，1.21.130 没有改语法 |

说明：

- 国际版此后进入 26.x 版本线；国际版 1.21.130 是本技能的兼容基线。
- 网易中国版用 3.10.x 启动器和组件体系映射 BE1.21.130。命令大体相通，但命令表、新 ID、客户端补全和实机行为不一定与国际版完全同步。
- 本页的“新增实体/物品/效果”来自国际版 1.21.130 更新。网易首次使用任一 ID 前，仍要在 3.10 / BE1.21.130 客户端补全、召唤、给予或施加成功。

## 新增实体 ID

| ID | 说明 |
| --- | --- |
| `nautilus` | 鹦鹉螺，可驯服的水下坐骑 |
| `zombie_nautilus` | 僵尸鹦鹉螺，中立；自然生成时骑手为持三叉戟的溺尸，有敌对骑手时转为敌对；有珊瑚变种 |
| `camel_husk` | 骆驼尸壳，沙漠夜间生成；生成时骑手为持长矛的尸壳和干枯者 |
| `parched` | 干枯者，沙漠亡灵骷髅变种，射虚弱之箭 |

`zombie_horse` 是旧 ID，但 1.21.130 开始在平原和热带草原夜间自然生成，可能带有持铁长矛的僵尸骑手。

国际版 ID 测试；网易主档必须逐项确认：

```text
/summon nautilus ~ ~ ~
/summon zombie_nautilus ~ ~ ~
/summon camel_husk ~ ~ ~
/summon parched ~ ~ ~
/summon zombie_horse ~ ~ ~
```

`summon` 不能带 NBT。要改属性请用生成事件、行为包实体定义或脚本 API。

## 新增物品 ID

### 长矛

```text
wooden_spear
stone_spear
copper_spear
iron_spear
golden_spear
diamond_spear
netherite_spear
```

### 鹦鹉螺盔甲

```text
copper_nautilus_armor
iron_nautilus_armor
golden_nautilus_armor
diamond_nautilus_armor
netherite_nautilus_armor
```

### 其他

```text
netherite_horse_armor
```

国际版 ID 测试；网易主档必须逐项确认：

```text
/give @s wooden_spear
/give @s netherite_spear
/give @s copper_nautilus_armor
/give @s netherite_nautilus_armor
/give @s netherite_horse_armor
```

注意：

- 以上 ID 是国际版 1.21.130 的版本事实，不能仅凭本节证明网易 3.10 全部同步。
- `give` 不能带 Java NBT。需要附魔就先用 `/enchant`：

```text
/give @s netherite_spear
/enchant @s lunge 1
```

- `/enchant` 作用于当前手持物品，所以要先手持长矛。
- 长矛只能附特定附魔；给不支持的物品附魔会失败。
- 1.21.130 之前的版本没有这些 ID，命令会报“未知物品”。

## 新增效果与附魔

| 类型 | ID | 用法 |
| --- | --- | --- |
| 状态效果 | `breath_of_the_nautilus` | `/effect @s breath_of_the_nautilus 30 0 true` |
| 附魔 | `lunge` | `/enchant @s lunge 1` |

`lunge` 是长矛专用附魔；用 `/enchant` 时物品必须是长矛。网易客户端若不认识该附魔，改回通用附魔并记录渠道差异。

## 命令变化

1.21.130 是内容更新，**没有引入新的命令语法**。与命令相关的修复：

- `/clone` 的 `filtered` 模式修复：不再复制与过滤掉方块共享位置的额外方块（例如含水的方块），也不会再把目标区域变成含水状态。现在可以按方块类型过滤复制：

```text
/clone ~ ~ ~ ~10 ~10 ~10 ~20 ~ ~ filtered force stone
```

- `/clone`、`/structure`、`/place` 在覆盖自定义方块时会触发脚本 API 的 `onBreak` 事件（beta API）。纯命令方块不受影响；只有脚本包要注意副作用。
- 其余命令语法与 1.21.120 一致；`execute` 仍是 1.19.50 之后的新语法。
- 自 1.19.60 起，`execute if|unless score` 不再接受可能匹配多个实体的 `@a`、`@e` 选择器。1.21.120 和 1.21.130 都没有恢复旧行为。

## 对网易纯指令的影响

- 不需要 `manifest.json`、`tick.json`、`min_engine_version`；这些是行为包的东西。
- 国际版确认的新 ID 可在国际版命令里直接使用；网易仍以客户端补全和实际执行结果为准。
- 旧版本客户端不认识新 ID；给旧版本写系统时不要用这些。
- 用 `hasitem` 检测新物品：

```text
/execute as @a[hasitem={item=netherite_spear}] run say 持有下界合金长矛
/execute as @a[hasitem={item=netherite_nautilus_armor,location=slot.armor.chest}] run say 穿着下界合金鹦鹉螺盔甲
```

- 用 `type` 检测新实体：

```text
/execute as @e[type=nautilus] run say 找到鹦鹉螺
/execute as @e[type=camel_husk] run say 找到骆驼尸壳
```

- 如果以后要把这些命令放进行为包 `functions/`，才需要 `min_engine_version: [1, 21, 130]`；纯命令方块不需要。

## 参考

- [Minecraft 1.21.130 Bedrock Changelog](https://www.minecraft.net/en-us/article/minecraft-1-21-130-bedrock-changelog)，2025-12-09 发布。
- [More Sources of Information about Minecraft: Bedrock Edition](https://learn.microsoft.com/en-us/minecraft/creator/documents/moreinfosources?view=minecraft-bedrock-stable)，官方说明 Stable 与 Preview 的边界，并列出社区参考入口。
- [Getting Started with Command Blocks](https://learn.microsoft.com/en-us/minecraft/creator/documents/commandblocks?view=minecraft-bedrock-stable)。
- [execute Command](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/commandsreference/examples/commands/execute?view=minecraft-bedrock-stable)。
- [Minecraft Beta & Preview 1.19.60.25：MCPE-156279](https://feedback.minecraft.net/hc/en-us/articles/11995250732557-Minecraft-Beta-Preview-1-19-60-25)，`if|unless score` 单目标限制的官方说明。
- [Target Selectors](https://learn.microsoft.com/en-us/minecraft/creator/documents/targetselectors?view=minecraft-bedrock-stable)。
- [titleraw Command](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/commandsreference/examples/commands/titleraw?view=minecraft-bedrock-stable)。

链接核实日期：2026-11-16。官方文档会继续更新；如果文档页面与固定目标客户端表现冲突，以目标客户端测试结果为准，并记录客户端版本。

网易渠道的完整命令边界和 `/help` 门禁见 [netease-1.21.130.md](netease-1.21.130.md)。

Wiki、社区文档、官方问题跟踪器和用户语料的可信度与许可不同，选择顺序见 [wiki-and-sources.md](wiki-and-sources.md)。
