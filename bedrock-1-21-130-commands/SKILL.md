---
name: bedrock-1-21-130-commands
description: 编写、现代化、排错和审计 Minecraft 网易中国版 3.10 / BE 1.21.130 的纯指令命令方块系统，并可导出带起止坐标的 .mcworld 或 BDS 世界目录；覆盖菜单、奖励、计时、多人配对、数据化 HUD、FMBE/MBE、状态机、旧语法转换、执行分叉预算和减少命令方块。
metadata:
  version: "3.3.0"
  author: "一个高质量的神秘人"
  github: "smr520"
  qq_group: "1031096520"
---

# 网易 1.21.130 纯指令命令方块

交付目标是让用户能把每条命令复制到网易中国版 1.21.130 的原版命令方块并按顺序搭好。国际版只在用户明确要求或需要交叉核对时作为第二目标。系统应优先减少命令方块数量，同时保留多人选择、交易原子性、状态清理和可测试性。

## 固定边界

- 默认渠道是网易中国版 3.10 / BE 1.21.130；先查网易官方命令列表和目标客户端 `/help`，不要因为国际版页面存在就直接认定网易可用。
- 运行环境只使用原版命令、命令方块、红石及原版实体和方块。
- 默认不生成或依赖行为包、资源包、插件、脚本、`.mcfunction`、`manifest.json`、`tick.json` 或 `.mcpack`。
- 用户需要投影时，可把已验证的纯命令方块 spec 导出为 `.mcworld` 或 BDS 世界目录；导出文件仍只包含世界元数据、LevelDB、命令方块、按钮和坐标清单，不加入行为包或函数。
- 网易命令表里存在 `/function`、`/schedule` 和 `/reload`，但它们依赖 Add-on 函数。当前纯命令方块边界内不使用它们代替方块链；只有用户明确改变范围时才切换交付类型。
- 默认允许一次性准备命令在聊天栏执行并记为 **0 个命令方块**。用户说“全部用方块”“只用方块初始化”时，再增加脉冲根和按钮并把它们计入总数。
- 用户要求、已在网易目标客户端确认的事实和已测原版语法优先于旧教程和外部合集。合集只用于发现模式，不是可直接执行的指令。
- `tellraw`/`titleraw` 的 `%%n` 参数槽可以做单格条件文本：无目标时省略选择器参数，再用后续文本补位。该技巧走原版 rawtext，不需要资源包；网易 `titleraw` 仍须先 `/help titleraw`，目标客户端未测时标为 `static-only`。
- `camera`、`inputpermission`、`dialogue`、`loot`、`place`、`recipe`、`scriptevent`、`hud` 和 `fog` 在网易 1.21.130 的官方证据不足或互相冲突。默认给替代方案；只有 `/help` 或目标客户端实测确认后才能使用。
- FMBE/MBE、数据化 RPG、大型 HUD 和命令计算机属于高级纯指令能力。用户明确需要时才启用，并同时报告实体数、刷新频率、区块加载和客户端视觉验证边界。

## 先确定实现条件

内部能推断的不要反复追问；只确认会改变方块链的未知项：

1. 目标渠道与版本：网易 3.10 / BE1.21.130、其他网易客户端或国际版 1.21.130。
2. 触发方式：循环根、按钮、拉杆、压力板、玩家丢物品、实体检测或菜单状态。
3. 状态载体：记分板目标、假玩家、玩家分数、`tag`、结构或临时标签。
4. 玩家数量：单人操作区、多人共用按钮，还是任意位置自动触发。
5. 加载条件：命令方块所在区块是否会加载，远处系统是否需要 `/tickingarea`。
6. 持久性与失败规则：重进、区块卸载、离线、满背包、重复点击、并发交易时应该怎样处理。

## 任务深度路由

- 用户只问一条语法、报错或单方块命令时，直接给修复、原因和最小验证；不要为了“完整”强行输出状态表或 JSON spec。
- 多条链、持久状态、多人事务、重进、队列、数据化系统或减少大量方块时，先选计算模型并写状态表，再排命令。
- 复杂方案可用 [chain-spec.schema.json](assets/chain-spec.schema.json) 描述链，再运行 `scripts/validate-chain-spec.mjs`。spec 是内部和发布用构建表，不是 `mcfunction`，最终交付仍是命令方块。

## 命令方块硬约束

| 项目 | 必须遵守 |
| --- | --- |
| 一格一命令 | 不能凭换行、分号或多个 `run` 把多条动作塞进一个方块 |
| 循环 | 保持开启时按方块延迟重复执行；固定间隔优先用延迟循环块 |
| 脉冲 | 每次红石信号执行一次；不要用不稳定的一次性红石源做正式触发器 |
| 连锁 | 箭头必须指下一格，同一 tick 内按链顺序执行 |
| 有条件 | 只检查紧邻上游的成功次数；失败仍把触发传给下一格，不能截断后续无条件块 |
| 延迟 | 单位是游戏刻，20 刻约为 1 秒；连锁默认写 0 |
| 区块 | 命令方块所在区块必须加载，远处系统用 `/tickingarea` 或明确要求玩家靠近 |
| 长度 | 单格文本上限约 32,500 字符；少格超长 `execute` 需同时报告性能和维护风险 |

## 减少命令方块

按以下顺序压缩，直到再删就会改变核心玩法：

1. 把分数、物品、距离、朝向、类型等条件直接放进选择器，例如 `scores`、`hasitem`、`r`、`rx`、`type`。
2. 固定间隔动作直接使用延迟循环块，不搭“每刻加时钟、判断、归零”的长链。
3. 菜单默认用一格总菜单加当前编号；需要逐项高亮时再增加显示块。
4. 只控制显示文字时，可用 `%%n` 参数槽根据选择器是否命中选择或省略文本，把多个条件提示收进一格；不要用它替代需要持久状态或实际动作的分支。
5. 音效、成功提示、粒子、过场标题和测试按钮默认省略，用户确认玩法后再加回。
6. 单人操作区可用连续 `@p[r=3]` 和有条件连锁；多人共用一个按钮、交易跨多步或对象可能改变时，用临时 `tag` 锁定并在所有结束路径清理。
7. 初始化只做一次。聊天栏可执行时记 0 格；不能在循环链重复 `objectives add`、`gamerule`、`tickingarea add` 或大范围 `fill/clone`。
8. 多个技能同时安装时，先检查能否共享显示、循环根、初始化或交易锁；独立状态仍使用独立目标，不能为了少格混用。

低方块数不等于低开销。`as`、`at` 的目标选择器会让后续命令按目标数量分叉；多个多目标子命令连用时，实例数按乘法增长。不要把几十个 `positioned`、巨量 `translate` 和超长选择器塞进一格来换取更小总数。压缩后必须检查命令长度、每刻扫描范围、选择器分叉数、箭头连接和失败路径。

## 工作流

1. **定模型**：判断这是状态机、数据流事务、队列、图、调度器还是空间采样；写清触发、初态、终态、失败、重置和离线行为。
2. **列状态**：每项状态写载体、归属、范围、初值、写入者和读取者。全局假玩家、每玩家分数、标签、菜单编号、锁和临时实体分开。
3. **分链**：按 `INPUT → VALIDATE → TRANSITION → OUTPUT → CLEANUP` 分阶段，把一次性初始化、持续循环、按钮触发、分支和清理拆开。
4. **写命令**：动作型命令使用 1.19.50+ 的 `execute ... run`；只检测条件时允许以完整 `if/unless` 结尾。先改状态会破坏后续选择器时，先用 `tag` 固定对象。
5. **核对预算**：统计每个命令方块和每次触发的执行分叉，不计聊天栏准备命令；说明删掉的装饰和保留的保护格。
6. **静态检查**：运行命令、链级、NetEase 可用性、spec 和整包校验，修掉旧语法、Java 参数、坏 JSON、全角符号、`if score` 多目标比较和传送多目标目的地。
7. **导出投影**：用户需要 `.mcworld`、BDS 或精确命令区坐标时，读取 [projection-export.md](references/projection-export.md)，从同一份 spec 生成世界文件；文件名和 `projection.json` 必须同时记录起止坐标。
8. **列实机测试**：覆盖成功、失败、边界、重复触发、多人、离开加载区、重进和清理路径。静态通过后仍标为 `static-only`。

用户提供已有 `.mcworld` 作为训练语料或要求审计已有地图时，先用
`python -B -X utf8 scripts/audit-mcworld.py <世界.mcworld> --json <审计.json> --markdown <审计.md> --commands-dir <临时目录>`
只读提取世界元数据、命令方块类型、命令、坐标、空命令、重复槽位和匿名化信号，并把 `CommandBlock` 实体数、已知物理方块数、空气坐标孤儿实体数和类型未知数分开报告。再对导出的命令文本运行 `validate-commands.mjs --channel netease`。地图中存在某条命令只算 `corpus-observed`，不等于该命令已在目标客户端成功执行。原始世界、完整命令、玩家名、地图坐标和内部价格不得进入 Apache-2.0 发布包；只有获得明确再分发许可后才能附带原始资产。

## 完整交付格式

回答用户时，先给能落地的内容，再解释原理。至少包含：

1. 目标版本、目标渠道和仍待替换的地图坐标或 ID。
2. 所有聊天栏准备命令；注明它们不占命令方块。
3. 按链分组的完整命令方块序列，每格都带四项设置。
4. 每条链的方块数、总方块数、按钮位置和箭头连接方式。
5. 正常路径、失败路径、多人路径和加载/重进测试。
6. 执行分叉预算：来源数、目标数、触发频率和最大实例数。
7. 纯指令做不到的状态，或为了减少方块而接受的可见差异。
8. 投影交付时给出 `.mcworld`、BDS 目录、起点、终点、尺寸、世界名和导入路径。

方块标注统一使用：

```text
B1【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a online 0

B2【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={online=0}] run tellraw @s {"rawtext":[{"text":"§a欢迎"}]}
```

- 类型只能是 `循环`、`连锁`、`脉冲`。
- 条件只能是 `无条件`、`有条件`。
- 红石状态写 `保持开启` 或 `需要红石`。
- 延迟写 `延迟0`、`延迟20` 这类明确游戏刻数。
- 命令放在标注下一行，一格只放一条；未闭合的坐标不能宣称为可直接运行。

按用户当前问题只实现需要的系统。用户问“还能做什么”时，从 [system-ideas.md](references/system-ideas.md) 选择 5–8 项，写清方块预算、限制和依赖，不要一次倾倒全部待办。

## 外部资料与旧教程

- 用户提供教程合集时，先按目录、扩展名、编码和内容哈希盘点，再抽样读取相关文件，不整批加载。
- 批量复核可运行 `python scripts/scan-corpora.py <合集根目录> --summary-only`；脚本自测用 `--self-test`。
- 从外部资料提取触发方式、状态字段、判定顺序和用户体验；命令本身按目标版本重写。
- 查 Wiki、社区教程、版本差异或许可规则时，先读 [wiki-and-sources.md](references/wiki-and-sources.md)。官方 Stable 页面会滚动更新，不能拿页面当前内容直接证明 1.21.130 行为。
- 文件名中的 `1CB`、`5CB` 通常只表示核心部分，不能当作初始化、收尾和测试后的总预算。
- 旧命令按 [legacy-to-modern.md](references/legacy-to-modern.md) 做语义转换，不能只做字符串替换。
- `.docx`、`.pdf` 中的截图可能包含文字提取不到的方块设置；`.bdx`、`.mcworld`、`.mcaddon` 不是纯指令文本；`.exe`、未知脚本和导入工具不运行。
- 网易专用内容与国际版普通 ID 分开记录。无法验证的 ID 留在“待实机确认”，不要用猜测补齐。

## 静态校验

以下 PowerShell 命令共用 `$skillRoot`。先在文件资源管理器中进入本 skill 根目录，再执行第一行；不要把个人电脑的绝对路径写进交付文档。

对整理后的单个命令文本：

```powershell
$skillRoot = (Get-Location).Path
node (Join-Path $skillRoot "scripts\validate-commands.mjs") <文件.txt|文件.md>
```

对整个 skill 的入口、运行时可执行文档、示例语法和声明方块数：

```powershell
node (Join-Path $skillRoot "scripts\validate-skill.mjs")
```

对某一套命令方块方案检查链起止、多人 `@p`、临时标签和动作栏冲突：

```powershell
node (Join-Path $skillRoot "scripts\validate-chains.mjs") <文件.md> --strict
```

对已有 `.mcworld` 做只读语料审计，并验证审计器自身：

```powershell
python -B -X utf8 (Join-Path $skillRoot "scripts\audit-mcworld.py") <世界.mcworld> --json <审计.json> --markdown <审计.md> --commands-dir <临时目录>
python -B -X utf8 (Join-Path $skillRoot "scripts\audit-mcworld.py") --self-test
```

对结构化命令链 spec 检查 ID、链头、拓扑、条件、延迟、方块朝向和纯命令边界：

```powershell
node (Join-Path $skillRoot "scripts\validate-chain-spec.mjs") <文件.json> --write <构建表.md>
```

对网易渠道的未验证、证据冲突和附加包依赖命令做专项扫描：

```powershell
node (Join-Path $skillRoot "scripts\validate-commands.mjs") <文件.txt|文件.md> --channel netease
```

从 chain spec 生成 `.mcworld` 与 BDS 世界目录：

```powershell
python -B -X utf8 (Join-Path $skillRoot "scripts\export-projection.py") <spec.json> --outdir <输出目录>
```

验证投影导出器的正向、世界容器和 BDS 目录一致性：

```powershell
python -B -X utf8 (Join-Path $skillRoot "scripts\export-projection.py") --self-test
```

验证脚本自身的正向、负向和严格模式行为：

```powershell
node (Join-Path $skillRoot "scripts\selftest.mjs")
```

组合多个已登记玩法前，先计算总预算、共享目标和显示冲突：

```powershell
node (Join-Path $skillRoot "scripts\plan-recipes.mjs") player-hud shop-single-operator
```

`legacy-to-modern.md` 故意包含错误旧语法，不按可直接运行文件整体校验；应校验转换后的输出。静态检查通过只代表没有发现明显文本问题，不能代替目标客户端的实机测试。

按 [test-matrix.md](references/test-matrix.md) 选择相关测试。没有实机结果时明确写“仅静态检查”，不要声称已经通过。

## 能力边界

- 基岩版记分板目标使用 `dummy`；不能直接读取玩家真实生命、饥饿或经验等级作为自动目标。
- 纯指令不能可靠读取任意实体真实生命值；BOSS 血条和自定义生命通常是模拟分数，普通攻击不会自动同步。
- `scoreboard` 冷却表示在线且链运行时的累计刻数，不是现实自然日。
- `@a` 只选择在线玩家。专用记分项配合 `add @a ... 0`、`reset *` 和 `set @a ... 1` 可在 4 格识别命令链持续运行期间的断开再进；完整退出世界再打开没有独立的世界载入信号，必须单列实机测试。玩家真正离开后，不能再对那名离线玩家本人执行命令。
- 前后在线人数差可以检测“这一游戏刻玩家总数净减少”，但不能指出具体是谁离开；同一游戏刻有人进入又有人离开时，净差可能为 0 而漏报。
- 雪球落点、`@p` 和最近实体只能做近似归属；多人挤近时必须说明误选可能。
- 纯原版可以显示标题、动作栏、聊天文本和侧边栏；复杂交互界面需要资源包，不能伪装成纯指令方案。
- 网易命令表存在 `/schedule` 不代表纯命令方块可以独立调度；没有 Add-on 函数文件时不能依赖它。同理，`/function` 和 `/reload` 不进入默认交付。
- FMBE/MBE 是实体加客户端动画的显示层，不是方块实体或真实碰撞体。必须报告实体数量、固定位置、刷新频率和截图校准需求。
- 数据化 RPG 的生命、攻击、防御等数值仍是自建 `dummy` 状态。普通原版攻击不会自动把真实伤害写入分数；“真实受击”技巧属于网易渠道观察项，必须在目标客户端逐项实测。
- `.mcworld` 是可直接导入的 ZIP 世界容器；BDS 使用解压后的同一套 `level.dat + db/ + levelname.txt` 目录。静态回读通过不等于目标网易客户端或 BDS 已成功加载。

## 参考资料路由

| 需要处理 | 读取 |
| --- | --- |
| 命令方块类型、延迟、条件、排错 | [command-blocks.md](references/command-blocks.md) |
| 复杂系统的行为契约、状态表、计算模型和不变量 | [command-model.md](references/command-model.md) |
| `.mcworld`、BDS、起止坐标、自动布局和投影导入 | [projection-export.md](references/projection-export.md) |
| 网易 1.21.130 命令边界、证据等级和高级纯指令能力 | [netease-1.21.130.md](references/netease-1.21.130.md) |
| FMBE/MBE、数据化 RPG、武器触发、UID 和大型网易地图 | [netease-advanced.md](references/netease-advanced.md) |
| 用户网易语料的匿名模式、旧图迁移和反模式 | [netease-corpus-patterns.md](references/netease-corpus-patterns.md) |
| 减少方块、初始化、交易和显示压缩 | [block-budget.md](references/block-budget.md) |
| 组合多个系统、共享显示、冷却和交易锁 | [shared-core.md](references/shared-core.md) |
| 常用命令、Java 差异、文本与方块语法 | [commands.md](references/commands.md) |
| 纯命令菜单、HUD、状态反馈、取消路径和多设备可读性 | [command-ui-playbook.md](references/command-ui-playbook.md) |
| 选择器、记分板、冷却和状态机 | [selectors-and-scoreboard.md](references/selectors-and-scoreboard.md) |
| 现有完整系统模板 | [systems.md](references/systems.md) |
| 配方依赖、方块预算和多人能力登记 | [recipe-registry.json](references/recipe-registry.json) |
| 验收与实机测试 | [test-matrix.md](references/test-matrix.md) |
| 旧语法和旧教程转换 | [legacy-to-modern.md](references/legacy-to-modern.md) |
| Wiki 选择、来源等级、许可、版本核对和按需抓取 | [wiki-and-sources.md](references/wiki-and-sources.md) |
| 网易映射、国际版 1.21.130 新 ID 和版本差异 | [version-1.21.130.md](references/version-1.21.130.md) |
| 国际版与网易 ID、能力边界 | [channel-matrix.md](references/channel-matrix.md) |
| 可继续实现的系统和建议预算 | [system-ideas.md](references/system-ideas.md) |

完整可复制示例在 [examples/README.md](examples/README.md)，包括雪球菜单、商店、撤离、玩家 HUD、条件 T 显、世界投影和欢迎公告。优先读取与当前需求最接近的单个示例，不要一次加载全部资料。
