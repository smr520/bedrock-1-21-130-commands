# 示例索引

这些示例都是**纯命令方块**，不依赖行为包、函数或 `tick.json`。

示例标题中的“格数”只统计带方块标注的命令方块；在聊天栏执行一次的准备命令记为 0 格。

| 示例 | 内容 |
| --- | --- |
| `snowball-menu.md` | 11 格雪球菜单：锁物品、6 选项、抬头确认、低头关闭 |
| `welcome-clock.md` | 4 格首次欢迎 + 延迟循环公告 |
| `shop.md` | 6 格金币商店/回收，条件写入选择器 |
| `extraction.md` | 5 格地毯撤离点：累计、离开归零、传送 |
| `player-hud.md` | 1 格玩家状态动作栏，直接读取多个分数 |
| `hud-arbiter.md` | 3 格 HUD 仲裁层：菜单优先于撤离，撤离优先于普通状态；不含被接入系统的状态与动作块 |
| `same-score-pair-teleport.md` | 1 格同分双人互传：双重遍历比较单个目标，同一按钮按触发者传送 |

更多模板在 `../references/systems.md`：

- 开箱/抽奖
- 签到（冷却版）
- 传送/回城
- 自定义血条 HUD
- BOSS 血条
- 简易区域限制

跨系统共享层在 `../references/shared-core.md`，完整示例组合为 13 个命令方块：

- 首次进入 3 格
- 统一 HUD 1 格
- 两个独立冷却共享循环根 4 格
- 多人交易锁 5 格

同时安装普通 HUD、撤离进度和菜单时，优先把三处动作栏替换为 `hud-arbiter.md`。多系统组合时先读 `../references/shared-core.md`，复用首次进入、HUD、冷却和交易锁；依赖与预算登记在 `../references/recipe-registry.json`。

在 skill 根目录运行 `node scripts/plan-recipes.mjs <配方ID...>` 可预检组合预算与冲突。

压缩方法和取舍见 `../references/block-budget.md`。

## 测试通用步骤

1. 世界设置打开“作弊”，确认命令方块可用：

```text
/gamerule commandblocksenabled true
/gamerule commandblockoutput true
```

2. 按示例摆好链，箭头从前一格指向后一格。
3. 站在循环方块旁，看“上一格输出”。
4. 用 `/scoreboard players list @s` 看分数。
5. 调通后关输出：

```text
/gamerule commandblockoutput false
/gamerule sendcommandfeedback false
```

6. 玩家走远测试：如果系统停了，加常加载区：

```text
/tickingarea add 0 0 0 10 10 10 menu
```

## 改造顺序

1. 换坐标：`0 64 0`、`100 64 100`。
2. 换物品：`apple`、`diamond`、`tripwire_hook`。
3. 换数值：价格、冷却、菜单项数。
4. 换显示文本：颜色 `§a`/`§c`/`§e`，文字自己写。
5. 内部名保持英文：`menu`、`coins`、`crate`；显示名再用中文。

## 调试口诀

- 不跑：看箭头、条件、红石、区块。
- 跑一次就停：看脉冲/循环、分数有没有重置、标签有没有删。
- 重复执行：看循环根是不是每刻都在触发、红石是不是一直供能。
- 命令失败：看“上一格输出”，先查目标有没有建、全角符号、选择器参数。
