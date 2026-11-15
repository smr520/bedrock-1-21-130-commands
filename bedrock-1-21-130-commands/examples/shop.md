# 金币商店 / 回收（精简版）

命令方块总数：6 个。100 金币 + 1 钻石换 1 苹果；1 钻石换 50 金币；另有 1 格查询余额。

## 准备：聊天栏执行一次

```text
/scoreboard objectives add coins dummy "金币"
```

第一次通过商店指令增加金币时会自动建立玩家分数。若要求所有在线玩家在赚到第一枚金币前也固定显示 0，可额外增加一格循环：`scoreboard players add @a coins 0`。

## C：购买链，3 个方块

```text
C1【脉冲｜无条件｜需要红石｜延迟0】
/execute as @p[r=3,scores={coins=100..},hasitem={item=diamond,quantity=1..}] run scoreboard players remove @s coins 100

C2【连锁｜有条件｜保持开启｜延迟0】
/execute as @p[r=3,hasitem={item=diamond,quantity=1..}] run clear @s diamond 0 1

C3【连锁｜有条件｜保持开启｜延迟0】
/execute as @p[r=3] run give @s apple 1
```

## D：回收链，2 个方块

```text
D1【脉冲｜无条件｜需要红石｜延迟0】
/execute as @p[r=3,hasitem={item=diamond,quantity=1..}] run clear @s diamond 0 1

D2【连锁｜有条件｜保持开启｜延迟0】
/execute as @p[r=3] run scoreboard players add @s coins 50
```

## E：查余额链，1 个方块

```text
E1【脉冲｜无条件｜需要红石｜延迟0】
/execute as @p[r=3] run tellraw @s {"rawtext":[{"text":"§e金币："},{"score":{"name":"@s","objective":"coins"}}]}
```

## 摆放

1. C1、D1、E1 都是脉冲方块，设为“无条件｜需要红石”，分别放按钮。
2. C2、C3、D2 是连锁方块，设为“有条件｜保持开启｜延迟0”，箭头依次指向同一链的下一格。
3. 三条链旁边都留单人操作区。`@p[r=3]` 选择附近最近的玩家；这套最少方块方案依赖单人操作，避免前后格选到不同的人。

## 为什么能少格

- 分数和钻石检测直接写进选择器，不再各用一格 `execute if`。
- 用“有条件连锁”在扣分成功后继续清钻石、发苹果；前一步失败就停止整条交易。
- 音效、成功提示和临时标签被省略。用标签固定买家会增加打标签和清标签两步，适合多人共用按钮的版本。
- 两个移动操作仍在同一个游戏刻按顺序执行，操作区应阻止玩家在链运行途中换人。

## 检查

1. `/scoreboard players set @s coins 100`，背包放 1 个钻石，按购买按钮。
2. 金币减 100、钻石减 1、苹果加 1。
3. 再按购买但没有钻石，金币、钻石和苹果都不应变化。
4. 按回收按钮，钻石减 1、金币加 50。
5. 按查询按钮，显示当前金币。
