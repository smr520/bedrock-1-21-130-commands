# 网易主档与渠道矩阵

默认目标是网易中国版 3.10 / BE 1.21.130。国际版 1.21.130 是兼容层和交叉核对来源。同一句语法在多个渠道可用，不代表实体 ID、粒子 ID、NPC 能力或版本修复完全一致。生成方案时先记录目标渠道，再决定哪些命令和 ID 可以直接使用。

## 证据等级

| 等级 | 含义 | 能否直接交付 |
| --- | --- | --- |
| `official` | 官方文档明确写出，且版本匹配 | 可以，仍应记录目标版本 |
| `client-confirmed` | 已在目标客户端实际执行成功 | 可以 |
| `community-doc` | 维护中的社区技术文档明确写出，但未在目标客户端确认 | 只能作为实现线索；与官方资料交叉核对后再交付 |
| `corpus-observed` | 只在用户提供的旧教程或语料中出现 | 只能作为线索，交付前验证 |
| `unverified` | 名称、命名空间或参数无法确认 | 不能当作可用命令 |

## 能力矩阵

| 能力 | 网易中国版 3.10 / BE 1.21.130 | 国际版兼容核对 | 处理规则 |
| --- | --- | --- | --- |
| 新式 `execute`（动作型 `run`／纯条件型） | 官方命令表有；真实地图样本以新语法为主 | 基线语法 | 新图一律用 `as/at/if/unless ... run`，旧图逐条迁移 |
| `scoreboard`、`tag`、`replaceitem` | 官方命令表有 | 通用基岩语法 | 可作为纯命令方块核心状态层 |
| `titleraw`、`damage` | 官方表未稳定列出，但语料中频繁出现 | 通常可用 | 标为 `corpus-observed`，首次使用先 `/help` 并在目标客户端执行 |
| `playanimation`、`camerashake`、`event`、`spreadplayers` | 官方表或真实语料有证据 | 与国际版大体相通 | 只在事件触发时运行，不放入每刻重链 |
| `hasitem` 选择器 | 版本与客户端补全相关 | 基线语法 | 用实际物品和 `slot.*` 参数测试，不使用 Java `count=` |
| 1.21.130 新实体、物品、效果 | 不能直接从国际版更新日志推定全部同步 | 按版本文档使用 | 网易单独建立 ID 清单，以客户端补全和召唤成功为准 |
| `camera`、`inputpermission`、`dialogue`、`loot`、`place`、`recipe`、`scriptevent` | 无足够官方命令表证据 | 部分有官方文档 | 网易默认视为未验证；先给替代方案 |
| `fog` | 官方页面之间有“已列出”和“尚未实装”的冲突 | 有国际版文档 | 默认不交付，先 `/help fog` 和客户端实测 |
| `function`、`schedule`、`reload` | 官方命令表有，但依赖 Add-on 函数或资源重载 | 通常可用 | 纯命令方块边界内排除 |
| `netease:pet`、`netease:tutorial_particle` | 网易专用语料出现 | 不属于通用国际版 ID | 只在确认后的网易方案中使用 |
| NPC 对话、伙伴、会员动画 | 可能来自编辑器或专用组件 | 能力不同 | 不能把 `@initiator` 当作按钮按压者，也不能伪装成纯命令方块 |
| 自定义物品 NBT/任意组件读写 | 纯指令不提供 | 纯指令不提供 | 统一使用计分板、`hasitem`、`replaceitem` 或结构方案 |
| 真实血量、受击事件、每玩家进入事件 | 纯指令无可靠通用读取；局部技巧需实测 | 不能假设存在等价命令 | 说明为模拟状态或额外运行环境 |

## 网易主档规则

- 版本基线是网易中国版 3.10 / BE 1.21.130；官方页面和客户端 `/help` 优先。
- 官方命令表有 `schedule`、`function`、`reload`，但默认纯命令方块不用它们代替方块链。
- `fog` 和其他官方证据不足或冲突的命令默认不进入网易方案；先 `/help`，再记录客户端、设备和结果。
- 真实地图语料中的旧 `execute`、方块数据值、作者昵称和联系方式不进入交付。语料只提取结构。
- 网易专用实体、粒子、NPC 和组件 ID 必须单独记录，不自动改成 `minecraft:` 或国际版 ID。
- 如果只用双方都确认的通用命令，可写“国际版兼容静态通过”，但不能写“网易目标客户端已通过”。

详细矩阵见 [netease-1.21.130.md](netease-1.21.130.md)。

## 国际版兼容规则

- 用户明确切换国际版时，新 ID 以 [version-1.21.130.md](version-1.21.130.md) 为准。
- 新 ID 在旧版本会报未知实体、物品或效果，交付时写最低版本。
- 原版命令方块、资源和世界可以正常使用；不生成行为包或资源包。
- 国际版文档里的 `camera`、`inputpermission`、`loot`、`place`、`recipe`、`scriptevent`、`fog` 和 `hud` 不能自动迁回网易主档。
- 若方案只使用通用语法，可以标记为“国际版静态通过”，但仍不代表目标设备实机通过。

## 待验证记录格式

```text
渠道：
客户端版本：网易 3.10 / BE1.21.130（或明确其他版本）
设备：
命令或 ID：
证据等级：
测试结果：
替代方案：
```

## 交付写法

可以写：

```text
本方案先使用网易官方列表中的 `execute`、`scoreboard`、`title` 和 `tickingarea`；专用粒子 ID 待客户端补全确认。
```

不要写：

```text
网易版肯定能用这个 ID。
```

无法确认时，保留通用原版机制并把专用 ID 放入待验证表。不要用猜测的命名空间让命令看起来完整。

## 官方参考

- [网易开发者：3.10 版本更新](https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/%E6%9B%B4%E6%96%B0%E4%BF%A1%E6%81%AF/3.10.html)
- [网易开发者：命令列表及概述](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/10-addon%E6%95%99%E7%A8%8B/%E7%AC%AC04%E7%AB%A0%EF%BC%9A%E6%8C%87%E4%BB%A4%E7%B3%BB%E7%BB%9F%EF%BC%8C%E4%BD%A0%E7%9A%84%E5%88%9B%E4%BD%9C%E7%AE%A1%E5%AE%B6/%E8%AF%BE%E7%A8%8B04.%E5%91%BD%E4%BB%A4%E5%88%97%E8%A1%A8%E5%8F%8A%E6%A6%82%E8%BF%B0.html)
- [网易开发者：常用命令及用法](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/15-%E7%8E%A9%E6%B3%95%E7%BB%84%E4%BB%B6%E6%95%99%E7%A8%8B/3-%E4%BA%86%E8%A7%A3%E6%88%91%E7%9A%84%E4%B8%96%E7%95%8C%E5%8E%9F%E7%89%88%E5%91%BD%E4%BB%A4/5-%E5%B8%B8%E7%94%A8%E5%91%BD%E4%BB%A4%E5%8F%8A%E7%94%A8%E6%B3%95.html)
- [Minecraft 1.21.130 Bedrock Changelog](https://www.minecraft.net/en-us/article/minecraft-1-21-130-bedrock-changelog)
- [More Sources of Information about Minecraft: Bedrock Edition](https://learn.microsoft.com/en-us/minecraft/creator/documents/moreinfosources?view=minecraft-bedrock-stable)
- [Getting Started with Command Blocks](https://learn.microsoft.com/en-us/minecraft/creator/documents/commandblocks?view=minecraft-bedrock-stable)
- [Target Selectors](https://learn.microsoft.com/en-us/minecraft/creator/documents/targetselectors?view=minecraft-bedrock-stable)
- [execute Command](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/commandsreference/examples/commands/execute?view=minecraft-bedrock-stable)

来源分类、社区 Wiki 路由、许可和版本核对流程见 [wiki-and-sources.md](wiki-and-sources.md)。
