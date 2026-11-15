# 欢迎 + 5 秒公告（精简版）

命令方块总数：4 个。建记分板目标放在聊天栏执行，不占用方块。

## 准备：聊天栏执行一次

```text
/scoreboard objectives add welcome dummy "首次欢迎"
/gamerule commandblockoutput false
```

第二条关闭命令方块输出提示，可按需保留。它们不是命令方块。

## B：首次欢迎，持续运行

```text
B1【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a welcome 0

B2【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={welcome=0}] run tellraw @s {"rawtext":[{"text":"§a欢迎来到服务器！"}]}

B3【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a[scores={welcome=0}] welcome 1
```

## C：5 秒公告

```text
C1【循环｜无条件｜保持开启｜延迟100】
/title @a actionbar §a5 秒到了
```

## 摆放

1. 在聊天栏执行准备命令。
2. B1 放循环方块，设为“无条件｜保持开启｜延迟0”；B2、B3 接常开连锁，箭头依次指向下一格。
3. C1 单独放一个循环方块，设为“无条件｜保持开启｜延迟100”。它每 100 游戏刻执行一次，不需要再搭计时、判断和归零链。
4. 两条链所在区块必须加载；远处系统要放入常加载区域。

## 压缩内容与取舍

- 原来的全局时钟链改为循环方块自身延迟，少 4 个方块。
- 欢迎音效、动作栏成功提示等装饰已省略。
- B 链在每名玩家第一次获得 `welcome` 分数时欢迎一次，不会在每次重新登录时重复欢迎。
- 要改公告频率，直接改 C1 的延迟：`20` 是 1 秒，`200` 是 10 秒。

## 检查

1. `/scoreboard objectives list` 能看到 `welcome`。
2. 新玩家进入后聊天栏出现一次欢迎，`welcome` 变成 1。
3. 退出重进不会再次欢迎；这是当前纯指令方案的限制。
4. C1 的动作栏提示每 5 秒出现一次。
