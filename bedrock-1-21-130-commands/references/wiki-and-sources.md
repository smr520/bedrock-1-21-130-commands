# Wiki 与资料来源

这些页面用于查证和扩展实现，不是纯命令方块方案的运行依赖。项目默认目标是网易中国版 3.10 / BE1.21.130，国际版 1.21.130 是兼容核对层。官方页面、客户端 `/help` 和用户实机记录分别代表不同证据，滚动文档里“当前写着”不能单独证明某条命令在某个固定客户端已经存在。

## 选择顺序

1. 网易 3.10 / BE1.21.130 目标客户端的 `/help` 和执行结果，注明设备、环境和完整方块上下文。
2. 网易开发者官网的 3.10 版本说明、命令列表和常用命令页面。
3. 国际版固定版本更新日志、Microsoft Learn、Mojira 或 Minecraft Feedback，用于兼容核对和状态确认。
4. 维护中的 Bedrock Wiki 技术文章；与官方资料交叉核对后，再把机制重写成网易纯命令方块版本。
5. Minecraft Wiki 用于版本历史、时序和术语交叉核对。
6. 用户提供的网易地图、指令合集、MC百科、旧 Fandom 页面和论坛回答只作为线索，不能直接成为正式语法。

有冲突时保留证据等级和目标版本，不要把社区文章、旧教程或搜索摘要升级成“官方已确认”。等级定义见 [channel-matrix.md](channel-matrix.md)。

## 主要来源

| 来源 | 等级 | 适合查什么 | 版本与许可提醒 |
| --- | --- | --- | --- |
| [网易开发者：3.10 版本更新](https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/%E6%9B%B4%E6%96%B0%E4%BF%A1%E6%81%AF/3.10.html) | `official` | 网易版本线与 BE1.21.130 映射、稳定版和玩家包时间 | 版本说明不列全部命令；命令仍查独立命令页 |
| [网易开发者：命令列表及概述](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/10-addon%E6%95%99%E7%A8%8B/%E7%AC%AC04%E7%AB%A0%EF%BC%9A%E6%8C%87%E4%BB%A4%E7%B3%BB%E7%BB%9F%EF%BC%8C%E4%BD%A0%E7%9A%84%E5%88%9B%E4%BD%9C%E7%AE%A1%E5%AE%B6/%E8%AF%BE%E7%A8%8B04.%E5%91%BD%E4%BB%A4%E5%88%97%E8%A1%A8%E5%8F%8A%E6%A6%82%E8%BF%B0.html) | `official` | 网易可用命令基线；`fog` 状态需要和其他官方页面交叉核对 | 页面未必覆盖新命令和参数；参数以 `/help` 补全为准 |
| [网易开发者：常用命令及用法](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/15-%E7%8E%A9%E6%B3%95%E7%BB%84%E4%BB%B6%E6%95%99%E7%A8%8B/3-%E4%BA%86%E8%A7%A3%E6%88%91%E7%9A%84%E4%B8%96%E7%95%8C%E5%8E%9F%E7%89%88%E5%91%BD%E4%BB%A4/5-%E5%B8%B8%E7%94%A8%E5%91%BD%E4%BB%A4%E5%8F%8A%E7%94%A8%E6%B3%95.html) | `official` | 网易基岩常用命令的基础签名 | 教程可能同时给出旧数据值和新方块状态重载 |
| [Microsoft Learn：命令方块](https://learn.microsoft.com/en-us/minecraft/creator/documents/commandblocks?view=minecraft-bedrock-stable) | `official` | 类型、条件、红石、延迟和基础命令方块链 | Stable 会滚动更新；本文示例也可能混用旧命令，以目标版本和实测为准 |
| [Microsoft Learn：世界模板打包](https://learn.microsoft.com/en-us/minecraft/creator/documents/packagingaworldtemplate) | `official` | 世界目录包含 `db/`、`level.dat` 和世界包清单 | 页面描述 `.mctemplate` 打包；`.mcworld` 与 BDS 目录复用同一世界文件布局 |
| [Microsoft Learn：Bedrock 与 Java 差异](https://learn.microsoft.com/en-us/minecraft/creator/documents/differencesbetweenbedrockandjava?view=minecraft-bedrock-experimental) | `official-cross-check` | Bedrock 世界采用 LevelDB，而不是 Java Anvil | Experimental 视图会滚动；只用于格式交叉核对 |
| [Microsoft Learn：命令参考](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/commandsreference/examples/commandlist?view=minecraft-bedrock-stable) | `official` | 查命令是否出现在当前 Stable 文档 | 当前 Stable 可能晚于 1.21.130；新命令要另查首次版本 |
| [Microsoft Learn：Raw Message JSON](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/rawmessagejson?view=minecraft-bedrock-stable) | `official` | `text`、`translate`、`with`、`selector`、`score` 和 `%%n` 参数槽的原始文本语义 | Stable 会滚动更新；用 `%%2` 做条件显示仍要在网易目标客户端验证 |
| [Microsoft Learn：更多资料来源](https://learn.microsoft.com/en-us/minecraft/creator/documents/moreinfosources?view=minecraft-bedrock-stable) | `official` | 官方给出的社区 Wiki、样例仓库和协议边界 | 列链接表示推荐入口，不表示社区内容自动正确或匹配 1.21.130 |
| [MicrosoftDocs/minecraft-creator](https://github.com/MicrosoftDocs/minecraft-creator) | `official-source` | 查看 Learn 页面源文件、提交历史和某个时间点的内容 | 文档为 CC BY 4.0，代码为 MIT；引用时仍需标出来源和修改 |
| [Minecraft 1.21.130 Changelog](https://www.minecraft.net/en-us/article/minecraft-1-21-130-bedrock-changelog) | `official` | 固定版本的更新、修复和新增 ID | 版本事实优先于之后更新的滚动文档 |
| [Mojira](https://bugs.mojang.com/) / [Minecraft Feedback](https://feedback.minecraft.net/) | `official` | 缺陷状态、`Works As Intended`、影响版本和修复版本 | 搜索问题 ID；先看状态和影响版本，不看标题猜测 |
| [Bedrock Wiki AI 索引](https://wiki.bedrock.dev/llms.txt) | `community-doc` | 按任务定位社区技术文章，避免整站抓取 | 正文和代码示例分别看页面与仓库声明；只链接并自行重写 |
| [Minecraft Wiki：Commands](https://minecraft.wiki/w/Commands) | `cross-check` | 命令解析、成功数、版本差异和旧行为对照 | 正文为 CC BY-NC-SA 3.0；只链接和核对事实，不把正文或表格搬进 Apache-2.0 仓库 |
| [中文 Minecraft Wiki：转载须知](https://zh.minecraft.wiki/w/Minecraft_Wiki:%E8%BD%AC%E8%BD%BD%E9%A1%BB%E7%9F%A5?variant=zh-cn) | `license` | 中文 Wiki 的复制和署名条件 | 与当前项目许可不兼容，默认只链接 |
| [Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples) | `official-sample` | `metadata/command_modules` 中的命令名和样例元数据 | `main` 是更新版本；必须查 Release、tag 或历史提交才能用于 1.21.130 |
| [MC百科《基岩版入门指令解析教程》](https://www.mcmod.cn/post/3872.html) | `corpus-observed` | 网易渠道和 1.21.120 入门语料 | 作者明确标注未经允许禁止转载；只用作用户语料线索，不复制、不当通用基线 |
| [yixin-amore/MinecraftBE-Command-Building-Skill](https://github.com/yixin-amore/MinecraftBE-Command-Building-Skill) | `community-skill` | 网易命令边界、命令建模、spec/linter、FMBE/MBE、数据化 RPG 和原始文本 UI 的设计线索 | MIT；只吸收经本项目重写和校验的方法。审计提交 `9184e4d36c4df62a8fc4e2be951bd9163dd8196a`；该次建筑栈不并入纯命令方块默认流程 |
| [xiaobo121388/mc-bedrock-commands-skill](https://github.com/xiaobo121388/mc-bedrock-commands-skill) | `community-reference` | 命令别名、权限、加入版本和 BDS/Education/Editor/ModAPI 范围对照的字段设计 | MIT；目标资料停在 1.21.120，97 份 reference 无逐条来源 URL，且存在命令矛盾；审计提交 `6836bfe7ae0fd34b2eb02bd210b201294f614e57`，不复制其命令百科 |
| [xiaobo121388/netease_mc-ui-skill](https://github.com/xiaobo121388/netease_mc-ui-skill) | `community-ui-reference` | 控件状态、菜单生命周期、取消路径、设备可达性和文字可读性原则 | 根声明 MIT，但 54 个以上模板带 Mojang/Microsoft 保留权利声明；审计提交 `5238ee29460792c55db73aaeba3a6a02f1869ba7`，不导入任何模板、图片或 Python API |

该仓库 2026-11-18 的更新还加入了建筑编译器和一份 `command-syntax.json`。建筑编译器不进入本项目默认流程；命令表缺少可直接追溯的目标客户端证据，且该仓库自身仍把 `fog` 标为未实装，因此不能覆盖本项目的网易官方证据矩阵。

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

1. 页面是否写明支持的网易版本或基岩底层版本。
2. 若没有版本标记，搜索更新日志或源文件历史，确认功能在 1.21.130 已经出现。
3. 用官方 changelog、Mojira 或 Microsoft 文档交叉核对命令名和限制。
4. 将社区函数、行为包或脚本示例改写为网易命令方块链，报告新增 CB、执行分叉和 `/help` 门禁。
5. 未在目标客户端执行时标为 `static-only`；不要用网页存在代替实机通过。

Microsoft Learn 的 `?view=minecraft-bedrock-stable` 是当前 Stable 视图。需要固定 1.21.130 时，可查看 `MicrosoftDocs/minecraft-creator` 在该版本发布日期附近的提交与文件历史，同时以 1.21.130 更新日志和客户端测试为准。

## 检索与复制规则

- Bedrock Wiki 的 `llms.txt` 提供网页到原始 Markdown 的转换方法；按单页读取，原始文件只用于定位与核验。
- Minecraft Wiki 适合在线核对事实。它的英文约 1.8 GiB、中文约 1.1 GiB 离线 ZIM 不应随 skill 发布。
- Fandom 旧站、过时的 `wiki.mcbe-dev.net`、百度百科和只给命令截图的转帖不作为最终依据。
- `minecraft.net`、`bugs.mojang.com`、`feedback.minecraft.net` 的链接和片段属于来源材料；发布包只保留必要链接和原创改写。
- 记录“来源 URL、核实日期、目标版本、证据等级、改写内容”。不要只留下一个无日期、无版本的复制命令。

最近核对日期：2026-11-19。
