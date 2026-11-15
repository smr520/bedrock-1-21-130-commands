# 撤离点（5 格精简版）

玩家在绿色地毯上连续等待约 5 秒后撤离；离开地毯会归零。命令方块总数：5 个，准备命令放在聊天栏执行。

## 准备：聊天栏执行一次

```text
/scoreboard objectives add extract dummy "撤离进度"
/fill 0 64 0 2 64 2 lime_carpet
```

把地毯范围保留在地图中，把 `0 64 0` 和 `2 64 2` 改成实际撤离区；地毯必须位于玩家脚下所在的方块位置。

## A：撤离链

```text
A1【循环｜无条件｜保持开启｜延迟10】
/execute as @a at @s if block ~ ~ ~ lime_carpet run scoreboard players add @s extract 1

A2【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={extract=1..9}] at @s unless block ~ ~ ~ lime_carpet run scoreboard players set @s extract 0

A3【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={extract=1..9}] run titleraw @s actionbar {"rawtext":[{"text":"§a撤离中 "},{"score":{"name":"@s","objective":"extract"}},{"text":" / 10"}]}

A4【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={extract=10..}] at @s run tp @s 4 64 0 facing 4 64 10

A5【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a[scores={extract=10..}] extract 0
```

## 摆放

A1 是循环方块，设为“无条件｜保持开启｜延迟10”；A2–A5 接常开无条件连锁，箭头依次指向下一格。A1 所在区块必须加载。

## 行为和取舍

- 延迟 10 表示每半秒加 1；达到 10 时约 5 秒。想改成 10 秒，把 A1 延迟改为 20，或把 A2/A3 的上限和 A4 阈值统一改成 20。
- 离开检查每半秒做一次，玩家离开后最多半秒归零；若必须立即归零，要另加延迟 0 的检测根。
- 进度保存在玩家分数中；离开地毯、执行撤离后都会归零。
- 音效、粒子、复杂进度条和多人撤离奖励已省略。多人同时待在地毯上会各自累计。
- A4 的 `4 64 0` 是撤离目标，`4 64 10` 是朝向点。目标必须位于撤离地毯之外且能够安全站立；示例中的 `x=4` 已在 `0..2` 地毯范围之外，但仍要换成地图中的实际坐标。

## 检查

1. 玩家站上绿色地毯，动作栏显示 1–9 的进度。
2. 中途离开，`extract` 应回到 0。
3. 连续站满 10 次检测后被传送到目标点，分数再次归零。
4. 用 `/scoreboard players list @s` 查看 `extract`。
