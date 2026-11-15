# 运行中重进欢迎 + 5 秒公告（精简版）

命令方块总数：5 个。建记分板目标放在聊天栏执行，不占用方块。

本例识别“世界保持运行，玩家断开后再进入”。玩家完全退出世界再打开时没有独立的世界载入信号，首个玩家的触发行为必须单独实机验证。

## 准备：聊天栏执行一次

```text
/scoreboard objectives add join_epoch dummy "进服事件"
/gamerule commandblockoutput false
```

第二条关闭命令方块输出提示，可按需保留。它们不是命令方块。

## B：运行中重进欢迎，持续运行

```text
B1【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a join_epoch 0

B2【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={join_epoch=0}] run tellraw @s {"rawtext":[{"text":"§a欢迎回来！"}]}

B3【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players reset * join_epoch

B4【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a join_epoch 1
```

## C：5 秒公告

```text
C1【循环｜无条件｜保持开启｜延迟100】
/title @a actionbar §a5 秒到了
```

## 摆放

1. 在聊天栏执行准备命令。
2. B1 放循环方块，设为“无条件｜保持开启｜延迟0”；B2、B3、B4 接常开连锁，箭头依次指向下一格。
3. C1 单独放一个循环方块，设为“无条件｜保持开启｜延迟100”。它每 100 游戏刻执行一次，不需要再搭计时、判断和归零链。
4. 两条链所在区块必须加载；远处系统要放入常加载区域。

## 压缩内容与取舍

- 原来的全局时钟链改为循环方块自身延迟，少 4 个方块。
- 欢迎音效、动作栏成功提示等装饰已省略。
- B 链在世界持续运行时，对每名玩家的断开再进欢迎一次。B3 清掉所有历史事件记录，B4 只把当前在线玩家标成 1；下一 tick 不会重复欢迎。
- `reset *` 只用于独立的 `join_epoch` 事件目标。不要把它改为金币、等级、冷却或玩家档案目标。
- 要改公告频率，直接改 C1 的延迟：`20` 是 1 秒，`200` 是 10 秒。

## 检查

1. `/scoreboard objectives list` 能看到 `join_epoch`。
2. 新玩家进入后聊天栏出现一次欢迎，在线玩家的 `join_epoch` 为 1。
3. 退出后重进会再次欢迎一次，不会每 tick 刷屏。
4. 两名玩家同 tick 进入时各收到一次欢迎；完整退出世界再打开时，首个玩家可能不会触发，必须实机确认并记录结果。
5. C1 的动作栏提示每 5 秒出现一次。

如果只需要“当前世界首次进入欢迎”，改用 `../references/shared-core.md` 的 3 格持久分数版本，不要使用本示例的 `reset *` 链。

事件顺序参考 Bedrock Wiki 的 [On Player Join](https://wiki.bedrock.dev/commands/on-player-join)；命令已改写为命令方块链，仍需目标客户端测试。来源等级见 `../references/wiki-and-sources.md`。
