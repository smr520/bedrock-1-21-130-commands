# 常用系统模板

本文件只使用聊天栏初始化和原生命令方块。每个代码块中的一行命令对应一格；方块按编号顺序摆放，前一格箭头指向后一格。不同的“初始化链”“循环链”“按钮链”分别搭建，不要把它们接成同一条。

- **初始化链**：脉冲根、需要红石，用按钮执行一次；先初始化，再启动循环链。重按创建已存在的目标会提示失败，不要因此删除已有目标或重置玩家数据。
- **循环链**：循环根、保持开启，后接无条件连锁；只有每刻都需要的逻辑放这里。
- **按钮链**：脉冲根、需要红石，后接无条件连锁；按一次处理一次事件。
- 以下均为延迟 0；循环根的“执行第一个选项”设为开启。循环持续运行还要求方块所在区块被加载。
- `@p[r=3]` 按命令方块位置选附近玩家，不能识别是谁按了按钮。多人环境应设置单人操作区；同一系统放多套时，要替换目标名和临时标签以免串线。
- 秒数按每秒 20 个游戏刻计算；卡顿或区块停止运行时，实际等待时间会变长。

## 雪球菜单

完整的逐格方案见 [雪球菜单](../examples/snowball-menu.md)，当前精简版为 11 个命令方块：聊天栏初始化、循环根、统一菜单显示、确认、关闭与摆放方式。这里不复制第二套，以免修改后不一致。

适合用雪球切换菜单、抬头确认、低头关闭。雪球归属如果使用附近玩家推测，应明确多人挤在一起时可能误选；不能声称这是精确的投掷者识别。菜单会占用动作栏，须与其他动作栏 HUD 协调。

## 金币商店 / 回收

完整的逐格方案见 [金币商店与回收](../examples/shop.md)，当前精简版为 6 个命令方块：聊天栏创建金币目标、3 格购买、2 格回收和 1 格查询。

适合固定地点、单人操作区的交易。通过临时标签固定本次交易对象，再扣分、清物品、发放奖励；不要在扣分后重新用原价格门槛选择玩家。

## 开箱 / 抽奖

消耗 1 个 `tripwire_hook`，随机 1–100：1–50 发苹果、51–80 发金苹果、81–100 发钻石。精简版共 8 个命令方块；冷却为玩家在线且循环链运行时累计的 200 游戏刻，约 10 秒。

### 准备：聊天栏执行一次

```text
/scoreboard objectives add crate dummy "抽奖"
/scoreboard objectives add cooldown dummy "冷却"
```

### 循环链：补分并递减冷却

```text
1【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a cooldown 0

2【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players remove @a[scores={cooldown=1..}] cooldown 1
```

### 开箱按钮链：6 个方块

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/execute as @p[r=3,scores={cooldown=0},hasitem={item=tripwire_hook,quantity=1..}] run clear @s tripwire_hook 0 1

2【连锁｜有条件｜保持开启｜延迟0】
/scoreboard players random @p[r=3,scores={cooldown=0}] crate 1 100

3【连锁｜有条件｜保持开启｜延迟0】
/scoreboard players set @p[r=3] cooldown 200

4【连锁｜无条件｜保持开启｜延迟0】
/execute as @p[r=3,scores={crate=1..50}] run give @s apple 1

5【连锁｜无条件｜保持开启｜延迟0】
/execute as @p[r=3,scores={crate=51..80}] run give @s golden_apple 1

6【连锁｜无条件｜保持开启｜延迟0】
/execute as @p[r=3,scores={crate=81..100}] run give @s diamond 1
```

`scoreboard players random` 包含两个端点，三个奖励区间互斥。按钮设在单人操作区；这几格在同一游戏刻连续运行并反复选择 3 格内最近的玩家。多人共用按钮时，应加回开始标签和结束清理标签来固定同一玩家。音效、粒子和成功提示已经省略。分数会保存，但离线期间不会递减。

## 签到：在线冷却版

这里实现的是在线累计等待 24000 游戏刻（约 20 分钟）领取一次；把奖励冷却改成 `1728000` 就是累计在线约 24 小时。它不读取现实日期，不能当成按现实自然日零点刷新的签到。精简版共 4 个命令方块。

### 准备：聊天栏执行一次

```text
/scoreboard objectives add checkin_cd dummy "签到冷却"
```

### 循环链：补分并递减冷却

```text
1【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a checkin_cd 0

2【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players remove @a[scores={checkin_cd=1..}] checkin_cd 1
```

### 签到按钮链：2 个方块

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/execute as @p[r=3,scores={checkin_cd=0}] run give @s diamond 1

2【连锁｜有条件｜保持开启｜延迟0】
/scoreboard players set @p[r=3] checkin_cd 24000
```

下线和停服不会清掉已有分数，但这段时间也不会计入等待；重新上线且循环链运行后继续递减。按钮设在单人操作区；多人共用时要用标签固定刚完成领取的玩家。成功提示和音效已省略。若改为统一游戏日刷新，需要另行设计游戏时钟并说明睡觉、改时间和停服时的规则，不能把它描述成现实日期签到。

## 传送 / 回城

地毯撤离点的完整精简链见 [5 格撤离示例](../examples/extraction.md)；使用延迟 10 的循环根，累计、离开归零、进度显示和传送共 5 格。

### 回城按钮链

先固定本次对象，再传送；后续提示不会重新选择传送点附近的其他玩家。

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/tag @p[r=3] add cb_return

2【连锁｜无条件｜保持开启｜延迟0】
/tp @a[tag=cb_return] 0 64 0 facing 0 64 10

3【连锁｜无条件｜保持开启｜延迟0】
/title @a[tag=cb_return] actionbar §a已回城

4【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[tag=cb_return] at @s run playsound random.levelup @s ~ ~ ~ 1 1

5【连锁｜无条件｜保持开启｜延迟0】
/tag @a[tag=cb_return] remove cb_return
```

把 `0 64 0` 换成安全主城坐标，`facing 0 64 10` 换成希望看向的位置。测试时检查目标地点可站立，并确保标签未被其他系统使用。

### 设置当前位置为重生点：按钮链

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/tag @p[r=3] add cb_spawn

2【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[tag=cb_spawn] at @s run spawnpoint @s

3【连锁｜无条件｜保持开启｜延迟0】
/title @a[tag=cb_spawn] actionbar §a重生点已设置

4【连锁｜无条件｜保持开启｜延迟0】
/tag @a[tag=cb_spawn] remove cb_spawn
```

### 多传送点

每个固定目的地复制一条回城按钮链，分别修改第 2 格坐标，并为各条链使用不同临时标签。菜单传送则接在菜单已固定对象的执行分支里，不要单独依靠未初始化的 `point` 分数。

## 自定义血条 HUD：分数模拟

这里的 `hp` 是自定义分数，不是读取原版生命值。下面只响应人为添加的 `damage_10`、`heal_10` 标签；原版摔落、近战等伤害不会自动换算进这套分数。不能把此模板描述成原版伤害同步血条。

### 初始化链：按钮执行一次

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/scoreboard objectives add hp dummy "生命"
```

### 循环链：初始化玩家、处理事件、归零、显示

按 1–11 格组成同一条链；不要把伤害、初始化和死亡判断拆成执行顺序不确定的独立循环根。

```text
1【循环｜无条件｜保持开启｜延迟0】
/execute as @a unless score @s hp matches -2147483648..2147483647 run scoreboard players set @s hp 100

2【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players remove @a[tag=damage_10] hp 10

3【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players add @a[tag=heal_10] hp 10

4【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a[scores={hp=101..}] hp 100

5【连锁｜无条件｜保持开启｜延迟0】
/tag @a[tag=damage_10] remove damage_10

6【连锁｜无条件｜保持开启｜延迟0】
/tag @a[tag=heal_10] remove heal_10

7【连锁｜无条件｜保持开启｜延迟0】
/tag @a[scores={hp=..0}] add hp_dead

8【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a[tag=hp_dead] hp 100

9【连锁｜无条件｜保持开启｜延迟0】
/kill @a[tag=hp_dead]

10【连锁｜无条件｜保持开启｜延迟0】
/tag @a[tag=hp_dead] remove hp_dead

11【连锁｜无条件｜保持开启｜延迟0】
/execute as @a run titleraw @s actionbar {"rawtext":[{"text":"§c模拟生命 "},{"score":{"name":"@s","objective":"hp"}},{"text":"/100"}]}
```

第 1 格只给尚无 `hp` 分数的玩家设为 100，不会把已有的 0 分玩家当作新人回血。先结算扣血与回血，再判断死亡；同一刻有两个标签时净变化为 0。这个“标签事件”一次只表示一次，不会累计同一刻发生的多次伤害。

### 测试扣血按钮：单独一格

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/tag @p[r=3] add damage_10
```

### 测试回血按钮：单独一格

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/tag @p[r=3] add heal_10
```

这两格与循环链分开，按钮只提交事件，循环负责消费标签。先用测试按钮验证后，再将标签提交接到你的纯指令技能或机关。动作栏会覆盖菜单及其他 HUD；共存时应合并显示或按状态选择一个 HUD。

## BOSS 血条：单只 BOSS 的分数模拟

这里的 `boss_hp` 是全服共享的模拟分数，不会读取僵尸的真实血量，也不会自动侦测普通攻击。扣模拟血使用下方测试按钮；如果要接技能，需要让技能显式提交扣分事件。

### 初始化链：按钮执行一次

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/scoreboard objectives add boss_hp dummy "BOSS 模拟血量"
```

### 召唤按钮链：每轮战斗执行一次

先确认示例的 `0 64 0` 是安全位置，且其一格范围内没有其他僵尸。此简化链按召唤点附近实体打标签，不宣称能精确识别同地点重叠的召唤对象；同一时间只运行一只 BOSS。再次按按钮会再召唤并重置共享分数，因此战斗中不要按。

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/summon zombie 0 64 0

2【连锁｜无条件｜保持开启｜延迟0】
/tag @e[type=zombie,x=0,y=64,z=0,r=1,c=1] add boss

3【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set boss boss_hp 1000
```

召唤和设满血只在这条按钮链里，不能接在循环链里。修改召唤坐标时，第 2 格的 `x/y/z` 同步修改。

### 扣模拟血按钮：单独一格

```text
1【脉冲｜无条件｜需要红石｜延迟0】
/execute if entity @e[tag=boss] run scoreboard players remove boss boss_hp 10
```

### 循环链：死亡判断与显示

```text
1【循环｜无条件｜保持开启｜延迟0】
/execute if score boss boss_hp matches ..0 run kill @e[type=zombie,tag=boss]

2【连锁｜无条件｜保持开启｜延迟0】
/execute if score boss boss_hp matches ..0 run scoreboard players set boss boss_hp 0

3【连锁｜无条件｜保持开启｜延迟0】
/execute if entity @e[type=zombie,tag=boss] run titleraw @a actionbar {"rawtext":[{"text":"§cBOSS 模拟生命 "},{"score":{"name":"boss","objective":"boss_hp"}},{"text":"/1000"}]}
```

普通僵尸仍会受到原版伤害，也可能在模拟分数归零前死亡。此模板用于演示分数血条与指令技能扣分，不是完整的原版受击检测 BOSS。多个 BOSS 需要分别管理实体标签、分数持有者、事件和显示，不能只复制目标名就宣称已支持。

## 区域限制：简易位置约束

```text
1【循环｜无条件｜保持开启｜延迟0】
/execute as @a[x=0,y=0,z=0,dx=20,dy=10,dz=20,m=!creative] run tp @s 0 65 0
```

本例把保护区内的非创造玩家传到 `0 65 0`；请把目标点改成保护区外的安全站立点。它只限制位置，不能当作通用的防作弊或方块保护系统。

## 测试与改装

1. 先按各系统初始化按钮，确认目标创建成功；再启用各自循环根。
2. 先用一名玩家测试成功、条件不足、重复按钮、冷却结束；再测试两人同时在操作区的选择行为。
3. 修改坐标、物品、价格时，同步改说明和提示文本。不要在循环里加入重置余额、生命或 BOSS 满血的命令。
4. 走远、重进、停服重开后测试加载与持久化；这些静态模板尚需在目标客户端进行实际验证。
5. 同时安装多个系统时协调目标名、临时标签、动作栏显示与常加载区域，不要共享含义不同的同名状态。
