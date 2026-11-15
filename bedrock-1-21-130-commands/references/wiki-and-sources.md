# Wiki 与资料来源

这些页面用于查证和扩展实现，不是纯命令方块方案的运行依赖。项目固定目标是国际版基岩 1.21.130；`stable` 页面会继续滚动到更新版本，因此“页面当前写着”不能单独证明某个语法或 ID 在 1.21.130 已经存在。

## 选择顺序

1. 目标 1.21.130 客户端的实测结果，注明平台、对象和完整方块上下文。
2. 官方版本更新日志、Microsoft Learn 命令参考、Mojira 或 Minecraft Feedback 的缺陷状态。
3. 维护中的 Bedrock Wiki 技术文章；与官方资料交叉核对后，再把命令重写成纯命令方块版本。
4. Minecraft Wiki 用于版本历史、时序和术语交叉核对。
5. 用户提供的教程、MC百科、旧 Fandom 页面和论坛回答只作为线索，不能直接成为正式语法。

有冲突时保留证据等级和目标版本，不要把社区文章、旧教程或搜索摘要升级成“官方已确认”。等级定义见 [channel-matrix.md](channel-matrix.md)。

## 主要来源

| 来源 | 等级 | 适合查什么 | 版本与许可提醒 |
| --- | --- | --- | --- |
| [Microsoft Learn：命令方块](https://learn.microsoft.com/en-us/minecraft/creator/documents/commandblocks?view=minecraft-bedrock-stable) | `official` | 类型、条件、红石、延迟和基础命令方块链 | Stable 会滚动更新；本文示例也可能混用旧命令，以目标版本和实测为准 |
| [Microsoft Learn：命令参考](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/commandsreference/examples/commandlist?view=minecraft-bedrock-stable) | `official` | 查命令是否出现在当前 Stable 文档 | 当前 Stable 可能晚于 1.21.130；新命令要另查首次版本 |
| [Microsoft Learn：更多资料来源](https://learn.microsoft.com/en-us/minecraft/creator/documents/moreinfosources?view=minecraft-bedrock-stable) | `official` | 官方给出的社区 Wiki、样例仓库和协议边界 | 列链接表示推荐入口，不表示社区内容自动正确或匹配 1.21.130 |
| [MicrosoftDocs/minecraft-creator](https://github.com/MicrosoftDocs/minecraft-creator) | `official-source` | 查看 Learn 页面源文件、提交历史和某个时间点的内容 | 文档为 CC BY 4.0，代码为 MIT；引用时仍需标出来源和修改 |
| [Minecraft 1.21.130 Changelog](https://www.minecraft.net/en-us/article/minecraft-1-21-130-bedrock-changelog) | `official` | 固定版本的更新、修复和新增 ID | 版本事实优先于之后更新的滚动文档 |
| [Mojira](https://bugs.mojang.com/) / [Minecraft Feedback](https://feedback.minecraft.net/) | `official` | 缺陷状态、`Works As Intended`、影响版本和修复版本 | 搜索问题 ID；先看状态和影响版本，不看标题猜测 |
| [Bedrock Wiki AI 索引](https://wiki.bedrock.dev/llms.txt) | `community-doc` | 按任务定位社区技术文章，避免整站抓取 | 正文和代码示例分别看页面与仓库声明；只链接并自行重写 |
| [Minecraft Wiki：Commands](https://minecraft.wiki/w/Commands) | `cross-check` | 命令解析、成功数、版本差异和旧行为对照 | 正文为 CC BY-NC-SA 3.0；只链接和核对事实，不把正文或表格搬进 Apache-2.0 仓库 |
| [中文 Minecraft Wiki：转载须知](https://zh.minecraft.wiki/w/Minecraft_Wiki:%E8%BD%AC%E8%BD%BD%E9%A1%BB%E7%9F%A5?variant=zh-cn) | `license` | 中文 Wiki 的复制和署名条件 | 与当前项目许可不兼容，默认只链接 |
| [Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples) | `official-sample` | `metadata/command_modules` 中的命令名和样例元数据 | `main` 是更新版本；必须查 Release、tag 或历史提交才能用于 1.21.130 |
| [MC百科《基岩版入门指令解析教程》](https://www.mcmod.cn/post/3872.html) | `corpus-observed` | 网易渠道和 1.21.120 入门语料 | 作者明确标注未经允许禁止转载；只用作用户语料线索，不复制、不当通用基线 |

## Bedrock Wiki 路由

先打开 `llms.txt`，再只读当前任务需要的一页；不要把命令目录、整个仓库或 Wiki 备份一次性塞进上下文。

| 需要处理 | 读取 |
| --- | --- |
| 命令方块 UI、类型、条件和基本摆放 | [Intro to Command Blocks](https://wiki.bedrock.dev/commands/intro-to-command-blocks) |
| 选择器、计数、距离、分数和类型过滤 | [Understanding Selectors](https://wiki.bedrock.dev/commands/selectors) |
| 新 `execute` 的执行上下文和子命令 | [Execute](https://wiki.bedrock.dev/commands/new-execute) |
| 相对坐标、局部坐标和旋转 | [Coordinate System](https://wiki.bedrock.dev/commands/relative-coordinates) |
| 方块状态与数据值迁移 | [Block States](https://wiki.bedrock.dev/commands/block-states) |
| 记分板运算、计时、最高/最低分 | [Scoreboard Operations](https://wiki.bedrock.dev/commands/scoreboard-operations)、[Scoreboard Timers](https://wiki.bedrock.dev/commands/scoreboard-timers)、[Comparing Scores](https://wiki.bedrock.dev/commands/comparing-scores) |
| 给目标分配稳定编号 | [Assign Unique Scores](https://wiki.bedrock.dev/commands/assign-unique-score) |
| 少搭方块但保留条件语义 | [Execute Logic Gates](https://wiki.bedrock.dev/commands/logic-gates) |
| 计算来源数乘目标数的执行成本 | [Execution Forking](https://wiki.bedrock.dev/commands/execution-forking) |
| 每名玩家每次进服 | [On Player Join](https://wiki.bedrock.dev/commands/on-player-join) |
| 在线人数净变化 | [On Player Leave](https://wiki.bedrock.dev/commands/on-player-leave)、[Entity Counter](https://wiki.bedrock.dev/commands/entity-counter) |
| 移动、朝向、丢物品和天气触发 | [Movement Detections](https://wiki.bedrock.dev/commands/detect-movements)、[Look Detection](https://wiki.bedrock.dev/commands/detect-looking)、[Item Drop Detection](https://wiki.bedrock.dev/commands/detect-item-drop)、[Rain Detection](https://wiki.bedrock.dev/commands/detect-rain) |

页面出现 `.mcfunction`、`tick.json`、行为包或脚本时，只提取机制；在纯命令方块交付中逐条展开、重新计数并补上清理路径。高级显示实体、摄像机、二进制存储和大型生成器只在用户明确需要时读取，不能为了展示技巧默认加入。

## 版本门禁

使用社区 Wiki 或滚动官方页面前，依次确认：

1. 页面是否写明支持的基岩版本。
2. 若没有版本标记，搜索更新日志或源文件历史，确认功能在 1.21.130 已经出现。
3. 用官方 changelog、Mojira 或 Microsoft 文档交叉核对命令名和限制。
4. 将社区函数、行为包或脚本示例改写为命令方块链，报告新增 CB 和执行分叉。
5. 未在目标客户端执行时标为 `static-only`；不要用网页存在代替实机通过。

Microsoft Learn 的 `?view=minecraft-bedrock-stable` 是当前 Stable 视图。需要固定 1.21.130 时，可查看 `MicrosoftDocs/minecraft-creator` 在该版本发布日期附近的提交与文件历史，同时以 1.21.130 更新日志和客户端测试为准。

## 检索与复制规则

- Bedrock Wiki 的 `llms.txt` 提供网页到原始 Markdown 的转换方法；按单页读取，原始文件只用于定位与核验。
- Minecraft Wiki 适合在线核对事实。它的英文约 1.8 GiB、中文约 1.1 GiB 离线 ZIM 不应随 skill 发布。
- Fandom 旧站、过时的 `wiki.mcbe-dev.net`、百度百科和只给命令截图的转帖不作为最终依据。
- `minecraft.net`、`bugs.mojang.com`、`feedback.minecraft.net` 的链接和片段属于来源材料；发布包只保留必要链接和原创改写。
- 记录“来源 URL、核实日期、目标版本、证据等级、改写内容”。不要只留下一个无日期、无版本的复制命令。

最近核对日期：2026-11-15。
