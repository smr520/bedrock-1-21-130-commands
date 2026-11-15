# 玩家状态 HUD（1 格精简版）

用一格动作栏显示名字、等级、经验、金币和自定义生命分数。命令方块总数：1 个。

## 准备：聊天栏执行一次

```text
/scoreboard objectives add level dummy "等级"
/scoreboard objectives add exp dummy "经验"
/scoreboard objectives add coins dummy "金币"
/scoreboard objectives add hp dummy "生命"
/gamerule commandblockoutput false
```

## A：每秒刷新

```text
A1【循环｜无条件｜保持开启｜延迟20】
/execute as @a run titleraw @s actionbar {"rawtext":[{"text":"§l§b"},{"selector":"@s"},{"text":"\n§eLv. "},{"score":{"name":"@s","objective":"level"}},{"text":"  §aEXP "},{"score":{"name":"@s","objective":"exp"}},{"text":"  §6Coins "},{"score":{"name":"@s","objective":"coins"}},{"text":"  §cHP "},{"score":{"name":"@s","objective":"hp"}}]}
```

## 摆放

A1 放一个循环方块，设为“无条件｜保持开启｜延迟20”，并放在加载区块。每秒刷新一次，不需要时钟链。

## 取舍

- `hp` 是自定义分数，不是原版真实生命值；原版受到的普通伤害不会自动同步。
- `titleraw` 的 `score` 会读取分数。没有分数条目时通常显示 0；若自己的客户端表现不同，先用 `scoreboard players add @a <目标> 0` 建立条目。
- 动作栏会和雪球菜单、撤离进度等 HUD 互相覆盖。多个 HUD 共存时，应把它们合并到一格显示，或按状态只启用一个刷新链。
- 改名显示时只改显示名；内部目标保持 `level`、`exp`、`coins`、`hp`。

## 检查

```text
/scoreboard players set @s level 5
/scoreboard players set @s exp 80
/scoreboard players set @s coins 100
/scoreboard players set @s hp 75
```

一秒内动作栏应显示当前四项数值。
