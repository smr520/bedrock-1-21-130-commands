# Validation

验证日期：2026-11-15。

## 环境

| 项目 | 结果 |
| --- | --- |
| Node.js | 24.19.0，脚本仅使用标准库 |
| Python | 3.12，扫描器仅使用标准库和可选解析器 |
| Minecraft 客户端 | 当前环境未安装 |
| 目标 | Minecraft Bedrock 1.21.130 |

## 自动检查

| 检查 | 结果 |
| --- | --- |
| skill-creator `quick_validate.py` | 通过；frontmatter、名称和未完成脚手架检查 |
| `node scripts/validate-skill.mjs` | 通过；18 份运行时文档、命令语法、链结构、链接、配方注册表和 CB 声明一致 |
| `node scripts/selftest.mjs` | 通过；校验器正向、负向、严格模式、命令语法和配方复用 |
| `python -B -X utf8 scripts/scan-corpora.py --self-test` | 通过；去重、嵌套 ZIP、DOCX、7z 降级和不可解析文件盘点 |
| Node.js `--check` | 所有 `.mjs` 脚本通过语法检查 |
| 敏感信息扫描 | 未发现密钥、令牌、邮箱、手机号、个人绝对路径或口令 |
| 二进制文件检查 | skill 目录全部为 UTF-8 文本，不包含二进制资产 |
| 安装目录哈希比对 | 通过；源目录、发布目录和已安装 skill 的 29 个文件逐文件 SHA-256 一致 |
| ZIP 完整性 | 通过；36 个文件与发布目录逐文件 SHA-256 一致，没有越界路径 |

## 预算检查

选择 `server-starter-core` 和 `player-hud`：

```text
名义方块总数: 14
复用后总数: 13
复用减少: 1
共享模块: display-bus
```

选择 `hud-arbiter` 时，应删除被它接管的独立动作栏输出；仲裁格和原显示格不能机械相加。

## 尚需实机验收

以下项目必须在目标 1.21.130 客户端完成，当前发布版不声称通过：

- 双人同时使用同一按钮、菜单落点和撤离区。
- 空背包、满背包、重复按键和交易中途失败。
- 方块链所在区块卸载、常加载区设置和世界重进。
- `titleraw actionbar` 多字段显示、缺失分数行为和动作栏仲裁视觉效果。
- 键盘鼠标、手柄和触屏的抬头、低头及菜单操作。
- 大量玩家、实体或每刻选择器下的性能。

验收项目见 `bedrock-1-21-130-commands/references/test-matrix.md`。
