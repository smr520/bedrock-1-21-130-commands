# Validation

验证日期：2026-11-19。

## 环境

| 项目 | 结果 |
| --- | --- |
| Node.js | 24.19.0，校验脚本仅使用标准库 |
| Python | 3.12；扫描器仅使用标准库和可选解析器，`quick_validate.py` 使用 PyYAML 6.0.3 |
| Minecraft 客户端 | 当前环境未安装 |
| 默认目标 | 网易中国版 V3.10 / BE1.21.130，纯命令方块 |
| 兼容目标 | 国际版 Minecraft Bedrock 1.21.130 |
| 网易来源核对 | 2026-11-16 在线核对网易 3.10 更新页、官方命令列表和常用命令页 |
| Wiki 来源核对 | 2026-11-19 核对 Microsoft Learn 原始文本 JSON、官方来源页、Bedrock Wiki、Minecraft Wiki、Mojira、MC百科和外部仓库提交 `9184e4d36c4df62a8fc4e2be951bd9163dd8196a` 的用途及许可边界 |

## 自动检查

| 检查 | 结果 |
| --- | --- |
| skill-creator `quick_validate.py` | 通过；frontmatter、名称和未完成脚手架检查 |
| `node scripts/validate-skill.mjs` | 通过；22 份运行时文档、26 份 Markdown 内部链接、入口路由、网易与 Wiki 关键来源、命令语法、rawtext 参数槽、链结构、JSON schema、链 spec、配方注册表和 CB 声明一致 |
| `node scripts/selftest.mjs` | 通过；校验器正向、负向、严格模式、动作型与纯条件型 `execute`、网易未验证警告、rawtext 参数槽、链 spec、单目标分数比较、传送目的地和配方复用 |
| `node scripts/validate-chain-spec.mjs` | 通过；同分互传 spec 无错误，可生成 Markdown 构建表 |
| `validate-commands.mjs --channel netease` | 通过；未验证命令给警告，纯命令方块中的函数/调度依赖仍被拦截 |
| `python -B -X utf8 scripts/scan-corpora.py --self-test` | 通过；去重、嵌套 ZIP、DOCX、7z 降级和不可解析文件盘点 |
| Node.js `--check` | 6 个 `.mjs` 脚本全部通过语法检查 |
| JSON / YAML 解析 | skill 内全部 JSON、发布仓库内 5 个 GitHub YAML 全部通过解析 |
| UTF-8 完整性 | 所有发布文本不含 `U+FFFD`；校验器新增负向回归用例 |
| 敏感信息扫描 | 未发现密钥、令牌、邮箱、手机号、个人绝对路径或口令 |
| 二进制文件检查 | skill 目录 39 个文件全部为 UTF-8 文本，不包含二进制资产或 NUL 字节 |
| 安装目录哈希比对 | 通过；源目录、发布目录和已安装 skill 的 39 个文件逐文件 SHA-256 一致 |
| ZIP 完整性 | 通过；`v2.1.0` ZIP 共 39 个文件、138,572 bytes，逐文件 SHA-256 与发布目录一致，没有越界路径 |

ZIP SHA-256：

```text
135cca7345ee271c2b1387c79fe90732e9642b1ebc4a4defcc487c43d7aaef75
```

GitHub Actions 在每次推送到 `main` 和每个拉取请求中执行脚本语法检查、整包校验、回归测试、语料扫描器自测和配方规划。

## 预算检查

选择 `server-starter-core`、`player-hud` 和 `hud-arbiter`：

```text
名义方块总数: 17
复用后总数: 16
复用减少: 1
共享模块: display-bus
风险: 多个动作栏输出需要仲裁
```

选择 `hud-arbiter` 时，应删除被它接管的独立动作栏输出；仲裁格和原显示格不能机械相加。

同分双人互传：

```text
A 与 B 在线且同分: 1 个实例，传送到另一名玩家
一方离线或未设置分数: 0 个实例
目标标签只有 A、B: 排除来源后，每次触发只剩 1 个目标实例
```

方案使用 `as @a[...,c=1] at @s at @a[...]` 保存来源与目标上下文。`c=1`、专用标签和 `rm=0.1` 同时限制目标数量与自比较。

运行中重进欢迎：

```text
进服事件: 4 个方块
5 秒公告: 1 个方块
示例总计: 5 个方块
```

事件链先给尚无分数的在线玩家补 0，对 0 分玩家执行一次动作，再对独立 `join_epoch` 目标执行 `reset *`，最后只把当前在线玩家设为 1。该顺序没有改套到金币、等级、冷却或长期档案。

## 尚需实机验收

以下项目必须在目标 1.21.130 客户端完成，当前发布版不声称通过：

- 网易中国版 3.10 / BE1.21.130 的 `/help` 补全：`titleraw`、`damage`、`hud`、`fog` 和其他未验证命令。
- 双人同时使用同一按钮、菜单落点和撤离区。
- 同分双人互传中的双方挤近、单方离线、不同分数、死亡/旁观和跨维度行为。
- 世界保持运行时，每名玩家断开再进只欢迎一次、两人同 tick 进入，以及大量离线分数记录下的 `reset *` 开销。
- 完整退出世界再打开时，首个玩家是否进入 0 分事件、是否需要世界载入初始化，必须单独实测。
- 一人离开时人数差能发现净减少；同一 tick 一人进入、一人离开时应明确记录净差为 0 的漏报边界。
- 空背包、满背包、重复按键和交易中途失败。
- 方块链所在区块卸载、常加载区设置和世界重进。
- 网易 `titleraw actionbar` 多字段显示、缺失分数行为和动作栏仲裁视觉效果。
- 键盘鼠标、手柄和触屏的抬头、低头及菜单操作。
- FMBE/MBE 实体数量、动画变量、客户端视觉、碰撞遮挡和 1 Hz 刷新。
- 数据化 RPG 的真实受击探针、中文 objective、`haspermission`、`has_property`、`@n` 和网易专用 ID。
- 两个不同网易客户端设备上的同 tick、帧率和动作栏刷新差异。
- 大量玩家、实体或每刻选择器下的性能。

验收项目见 `bedrock-1-21-130-commands/references/test-matrix.md`。
