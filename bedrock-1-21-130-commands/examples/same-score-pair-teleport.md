# 同分双人互传

同一按钮、同一积分目标：A 和 B 都在线且分数相同时，谁走近按钮触发，谁就传送到另一名同分玩家。核心为 1 个脉冲命令方块。

`if score` 的两边都必须解析成单一目标。这里按执行分叉方式安排上下文：`as` 固定触发方，第一次 `at @s` 固定触发方位置，第二次 `at` 遍历另一名已登记玩家。最终 `@s` 是触发方，`@p` 是当前比较目标。

## 准备：聊天栏执行，0 格

把 `A`、`B` 换成实际玩家名。若已有积分目标，把 `pair_score` 换成现有内部名。

```text
/scoreboard objectives add pair_score dummy "同分"
/scoreboard players set A pair_score 1
/scoreboard players set B pair_score 1
/tag A add teleport_eligible
/tag B add teleport_eligible
```

两条 `set` 只用于测试。全图只能让 A、B 拥有 `teleport_eligible`，否则第三人可能被当成触发方或传送目标。

## 按钮链

```text
C1【脉冲｜无条件｜需要红石｜延迟0】
/execute as @a[tag=teleport_eligible,r=3,c=1] at @s at @a[tag=teleport_eligible,rm=0.1] if score @s pair_score = @p pair_score run tp @s @p
```

命令方块总数：1 个

- `as @a[tag=teleport_eligible,r=3,c=1]`：从按钮附近最多选一名最近的已登记玩家，作为触发方。
- `at @s`：把执行位置固定到触发方位置；`@s` 之后保持为触发方。
- `at @a[tag=teleport_eligible,rm=0.1]`：遍历另一名在线已登记玩家，并把位置切到该玩家。
- `if score @s ... = @p ...`：`@s` 是触发方，`@p` 是当前目标位置上的玩家；两边都是单目标，分数相等才继续。
- `tp @s @p`：把触发方传送到当前同分目标。

## 必须保留的多人限制

- 纯命令方块不能精确读取按钮按压者；`@p` 是位置近似。
- 按钮附近同时只能有一名已登记玩家。
- 只登记 A、B 两名玩家，并且两人不要完全重叠站位。
- 两人需要在线并处于可正常选择、传送的同一维度。
- 第三人替 A 按按钮而 A 正好在附近时，系统仍可能把 A 当成触发方。

## 测试

| 路径 | 预期 |
| --- | --- |
| A、B 在线，分数都是 1，A 触发 | A 传送到 B |
| A、B 在线，分数都是 1，B 触发 | B 传送到 A |
| A、B 在线，分数分别为 1 和 2 | 不传送 |
| B 离线，A 触发 | 不传送 |
| A 在按钮附近，B 距离较远 | 传送到 B 位置 |
| A、B 同时挤在按钮旁 | `@p` 可能选错触发方，不保证方向 |
