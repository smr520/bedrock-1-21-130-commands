# 多系统 HUD 仲裁（3 格）

同一名玩家每轮只显示一条动作栏。优先级从高到低为：雪球菜单、撤离进度、普通玩家状态。准备命令放在聊天栏执行，仲裁链本身是 3 个命令方块，不包含菜单、撤离和 HUD 的状态与动作方块。

## 准备：聊天栏按需执行

```text
/scoreboard objectives add menu dummy "雪球菜单"
/scoreboard objectives add extract dummy "撤离进度"
/scoreboard objectives add level dummy "等级"
/scoreboard objectives add exp dummy "经验"
/scoreboard objectives add coins dummy "金币"
/scoreboard objectives add hp dummy "生命"
```

只创建实际使用的目标。缺少分数条目时，选择器不会把它当成 0；普通 HUD 不依赖 `menu` 或 `extract` 的 0 分条目。

## A：统一动作栏

```text
A1【循环｜无条件｜保持开启｜延迟1】
/execute as @a unless entity @s[scores={extract=1..10}] unless entity @s[scores={menu=1..6}] run titleraw @s actionbar {"rawtext":[{"text":"§l§b"},{"selector":"@s"},{"text":"\n§eLv. "},{"score":{"name":"@s","objective":"level"}},{"text":"  §aEXP "},{"score":{"name":"@s","objective":"exp"}},{"text":"  §6Coins "},{"score":{"name":"@s","objective":"coins"}},{"text":"  §cHP "},{"score":{"name":"@s","objective":"hp"}}]}

A2【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={extract=1..10}] unless entity @s[scores={menu=1..6}] run titleraw @s actionbar {"rawtext":[{"text":"§a撤离中 "},{"score":{"name":"@s","objective":"extract"}},{"text":" / 10"}]}

A3【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=1..6}] run titleraw @s actionbar {"rawtext":[{"text":"§l§b雪球菜单  当前："},{"score":{"name":"@s","objective":"menu"}},{"text":" / 6\n§e1. 传送主城  2. 原地去世  3. 生存模式\n§e4. 设置重生点  5. 领取苹果  6. 关闭"}]}
```

## 接入方法

1. 删除原 HUD、撤离和雪球菜单里各自单独执行的 `titleraw ... actionbar`。它们的状态计算、菜单切换和动作方块保留。
2. 保留 A1–A3 这一条循环链，箭头依次连接，全部常开。
3. 菜单状态使用 `menu=1..6`，撤离状态使用 `extract=1..10`；改名时同时修改本模板和对应系统。
4. 需要第三种优先级时，在 A3 后追加一格，并用 `unless entity` 排除更高优先级的现有状态。

## 为什么不会互相覆盖

- 菜单打开时，A1 和 A2 都被 `unless entity @s[scores={menu=1..6}]` 排除，只有 A3 输出。
- 菜单关闭、正在撤离时，A1 被撤离分数排除，A2 输出。
- 两种状态都没有时，只有 A1 输出。

## 取舍与检查

- 延迟 1 表示每游戏刻刷新，状态变化响应快；玩家很多时可改为 5 或 10，减少选择器扫描次数。
- 这仍是单个动作栏，不能同时展示普通 HUD、撤离和完整菜单；仲裁负责选出一条。
- 仲裁解决覆盖冲突，不会凭空减少整套系统的 CB；接入后要删除原来的独立动作栏块，再重新统计总数。
- 若客户端不显示缺失分数，先在聊天栏为相关目标运行 `scoreboard players add @a <目标> 0`。
- 双人测试时让一名玩家打开菜单、另一名玩家站进撤离区，确认两人的动作栏互不影响。
- 组件接入后必须运行 `validate-chains.mjs --strict`；仅有静态检查时不得标记为实机通过。
