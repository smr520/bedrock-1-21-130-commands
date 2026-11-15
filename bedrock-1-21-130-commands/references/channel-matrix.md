# 国际版与网易渠道矩阵

同一句语法在多个渠道可用，不代表实体 ID、粒子 ID、NPC 能力或版本修复完全一致。生成方案时先记录目标渠道，再决定哪些 ID 可以直接使用。

## 证据等级

| 等级 | 含义 | 能否直接交付 |
| --- | --- | --- |
| `official` | 官方文档明确写出，且版本匹配 | 可以，仍应记录目标版本 |
| `client-confirmed` | 已在目标客户端实际执行成功 | 可以 |
| `community-doc` | 维护中的社区技术文档明确写出，但未在目标客户端确认 | 只能作为实现线索；与官方资料交叉核对后再交付 |
| `corpus-observed` | 只在用户提供的旧教程或语料中出现 | 只能作为线索，交付前验证 |
| `unverified` | 名称、命名空间或参数无法确认 | 不能当作可用命令 |

## 能力矩阵

| 能力 | 国际版基岩 1.21.130 | 网易渠道 | 处理规则 |
| --- | --- | --- | --- |
| 新式 `execute`（动作型 `run`／纯条件型） | 基线语法；动作可接 `run`，条件命令可直接以 `if/unless` 结尾 | 是否完全同步取决于客户端版本 | 先做通用模板，再用目标客户端补全验证 |
| `scoreboard`、`tag`、`titleraw`、`replaceitem` | 通用基岩语法 | 通常存在，但界面与补全可能有差异 | 不依赖专用命名空间，保留实机测试项 |
| `hasitem` 选择器 | 基线语法 | 版本相关 | 在目标客户端用实际物品测试 |
| 1.21.130 新实体、物品、效果 | 按版本文档使用 | 不能直接假设存在 | 网易版单独建立 ID 清单 |
| `netease:pet`、`netease:tutorial_particle` | 不属于通用国际版 ID | 语料中大量出现 | 只在确认后的网易方案中使用 |
| NPC 对话、伙伴、会员动画 | NPC 对话是国际版原版能力，但 `@initiator` 只在对话中有效，不属于普通命令方块上下文；伙伴和会员动画另有渠道差异 | 可能来自网易编辑工具或专用组件 | 不能把 `@initiator` 当作按钮按压者，也不能伪装成纯命令方块 |
| 自定义物品 NBT/任意组件读写 | 纯指令不提供 | 差异大且不可通用 | 统一使用记分板、`hasitem`、`replaceitem` 或结构方案 |
| 真实血量、受击事件、每玩家进入事件 | 纯指令无可靠通用读取 | 不能假设存在等价命令 | 说明为模拟状态或需额外运行环境 |

## 国际版规则

- 项目版本基线是国际版基岩 1.21.130。新 ID 以 [version-1.21.130.md](version-1.21.130.md) 为准。
- 新 ID 在旧版本会报未知实体、物品或效果，交付时写最低版本。
- 原版命令方块、资源和世界可以正常使用；不生成行为包或资源包。
- 若方案只使用通用语法，可以标记为“国际版静态通过”，但仍不代表目标设备实机通过。

## 网易渠道规则

- “网易版”“中国版”“互通版”不是同一个无限定版本。必须先确认实际客户端版本。
- 语料出现 `netease:` 命名空间时，标记为 `corpus-observed`，不要自动改成 `minecraft:`。
- NPC、伙伴、会员动画、专用粒子和编辑器组件与普通命令方块不是同一层能力，不能直接写进纯指令交付。
- 网易作者的延迟实测、补全顺序和界面槽位只能作为线索；最终以目标客户端为准。
- 如果通用原版方案能完成核心玩法，先交付通用版，再列出待替换的渠道专用 ID。

## 待验证记录格式

```text
渠道：
客户端版本：
设备：
命令或 ID：
证据等级：
测试结果：
替代方案：
```

## 交付写法

可以写：

```text
本方案使用国际版 1.21.130 的木质长矛 ID；目标为网易旧客户端时，需在客户端 Tab 补全后替换。
```

不要写：

```text
网易版肯定能用这个 ID。
```

无法确认时，保留通用原版机制并把专用 ID 放入待验证表。不要用猜测的命名空间让命令看起来完整。

## 官方参考

- [Minecraft 1.21.130 Bedrock Changelog](https://www.minecraft.net/en-us/article/minecraft-1-21-130-bedrock-changelog)
- [More Sources of Information about Minecraft: Bedrock Edition](https://learn.microsoft.com/en-us/minecraft/creator/documents/moreinfosources?view=minecraft-bedrock-stable)
- [Getting Started with Command Blocks](https://learn.microsoft.com/en-us/minecraft/creator/documents/commandblocks?view=minecraft-bedrock-stable)
- [Target Selectors](https://learn.microsoft.com/en-us/minecraft/creator/documents/targetselectors?view=minecraft-bedrock-stable)
- [execute Command](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/commandsreference/examples/commands/execute?view=minecraft-bedrock-stable)

来源分类、社区 Wiki 路由、许可和版本核对流程见 [wiki-and-sources.md](wiki-and-sources.md)。
