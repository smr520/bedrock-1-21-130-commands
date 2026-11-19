# 1 格条件 T 显

用 `translate:"%%2"` 和原始文本参数槽，在一个命令方块里按玩家分数选择要显示的文字。它只压缩显示分叉，不替代传送、交易或状态写入。

命令方块总数：1 个。

## 准备命令（0 个命令方块）

在聊天栏执行：

```text
/scoreboard objectives add quest dummy
/scoreboard players set @a quest 0
```

测试时分别把一名玩家的 `quest` 设为 `1`、`2`、`3` 或 `0`：

```text
/scoreboard players set 玩家名 quest 1
/scoreboard players set 玩家名 quest 2
/scoreboard players set 玩家名 quest 3
/scoreboard players set 玩家名 quest 0
```

## 命令方块

```text
C1【循环｜无条件｜保持开启｜延迟10】
/execute as @a run titleraw @s actionbar {"rawtext":[{"text":"§6任务："},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={quest=1}]"},{"text":"§a已领取"}]}},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={quest=2}]"},{"text":"§e进行中"}]}},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={quest=3}]"},{"text":"§b可领取"}]}}]}
```

这条命令每秒刷新两次。`quest=1` 时只出现“已领取”，`quest=2` 时只出现“进行中”，`quest=3` 时只出现“可领取”，`quest=0` 时三个条件都不命中，只显示“任务：”。分数区间必须互斥；例如也用 `1..3`，就会同时显示多段文字。

动态菜单可在状态变化时用脉冲块刷新一次；常驻动作栏更适合 10–20 tick 的低频循环，不建议每 tick 重发不变的大文本。

## 网易验证

1. 先执行 `/help tellraw` 和 `/help titleraw`。
2. 把 C1 临时改为脉冲块，用一条 `tellraw` 版本确认 `%%2` 的命中、未命中和参数跳过行为。
3. 确认 `titleraw ... actionbar` 在目标网易客户端可用后，再恢复上面的循环块。
4. 用两名玩家同时测试，确认 `@s` 各自读取自己的 `quest`，没有串号或覆盖。
5. 未完成以上步骤时只写 `static-only`，不要声称网易实机已经通过。

## 多档提示的边界

社区资料还给出 `%%9` 的 8 档累进写法，用无命中选择器被跳过后让候选文字前移。它能进一步缩短 JSON，但上限、重叠选择器和不同客户端补位顺序都更脆弱。只有目标客户端逐档测试后才使用，默认采用上面的互斥 `%%2` 模板。
