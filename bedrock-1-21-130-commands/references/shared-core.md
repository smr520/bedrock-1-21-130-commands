# 共享命令方块内核

这份文件解决的是“多个系统同时安装时，怎样少放方块、少撞名称、少抢 HUD”。每个模块仍然是纯命令方块；模块之间只用记分板、标签和一次性准备命令交接。

共享内核不会把多条动作塞进一个方块。它通过共享循环根、统一显示入口和固定命名减少整套服务器的总方块数。

## 命名约定

- 记分板目标使用功能前缀：`core_seen`、`cd_attack`、`cd_buff`、`coins`、`hp`。
- 临时标签使用动作前缀：`tx_shop`、`tx_reward`、`select_target`、`menu_lock`。
- 独立冷却不能共用同一个对象，否则攻击冷却会重置技能冷却。
- 多个系统需要同一类状态时复用对象；含义不同的状态即使名字相似也要分开。

## 玩家首次进入标记

用途：给第一次被当前世界记录的玩家发欢迎、设初始值或分配一次编号。它检测的是“记分板第一次出现”，不能识别每次重新登录。

### 准备：聊天栏执行一次

```text
/scoreboard objectives add core_seen dummy "首次进入"
```

### 运行链：3 个方块

```text
S1【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a core_seen 0

S2【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={core_seen=0}] run tellraw @s {"rawtext":[{"text":"§a欢迎，玩家档案已建立"}]}

S3【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a[scores={core_seen=0}] core_seen 1
```

S1 给尚无分数的在线玩家补 0；S2 只欢迎 0 分玩家；S3 把 0 改成 1。分数会持久化，所以同一玩家不会重复触发。需要可靠识别每次重登时，应明确这超出纯命令方块能力。

## 单一玩家 HUD

用途：把金币、等级、经验和模拟生命放进同一个动作栏输出，避免多个系统每秒互相覆盖。

### 准备：聊天栏执行一次

```text
/scoreboard objectives add coins dummy "金币"
/scoreboard objectives add level dummy "等级"
/scoreboard objectives add exp dummy "经验"
/scoreboard objectives add hp dummy "模拟生命"
```

### 显示链：1 个方块

```text
H1【循环｜无条件｜保持开启｜延迟20】
/execute as @a run titleraw @s actionbar {"rawtext":[{"text":"§6Coins "},{"score":{"name":"@s","objective":"coins"}},{"text":"  §aLv "},{"score":{"name":"@s","objective":"level"}},{"text":"  §bEXP "},{"score":{"name":"@s","objective":"exp"}},{"text":"  §cHP "},{"score":{"name":"@s","objective":"hp"}}]}
```

一个 `titleraw` 能组合多个 `score` 对象，但每个记分板目标仍要单独准备。若目标客户端对缺失分数显示为空而不是 0，再为对应目标增加一格 `scoreboard players add @a <目标> 0`。

动作栏只能可靠显示一个主动输出。菜单打开时，应让统一 HUD 按状态暂停，或把菜单并入同一个显示总线；不要同时运行多条每秒 `titleraw actionbar` 链。

## 多系统动作栏仲裁

用途：让普通 HUD、撤离进度和菜单共用一个动作栏，并且每名玩家在同一轮只收到一条主动输出。优先级为“菜单 > 撤离 > 普通 HUD”。

完整、可直接搭链的三格模板见 [hud-arbiter.md](../examples/hud-arbiter.md)。核心做法是一个循环根依次执行三条输出：

1. 普通 HUD 用 `unless entity` 排除撤离和菜单状态。
2. 撤离进度排除菜单状态。
3. 菜单最后输出，因此优先级最高。

相比让每个系统各放一条循环动作栏，这个模板共用调度根并避免同刻互相覆盖。接入时删除原系统里的 `titleraw ... actionbar` 方块，只保留它们对 `extract`、`menu` 等状态的维护；动作方块仍然一格一条。模板自身是 3 格，完整服务器总数应按“原系统动作格 + 仲裁格 - 已删除的原显示格”计算，不能把 3 格直接当成整套菜单和撤离系统。

## 共享冷却根

用途：多个技能各有独立冷却，但共用同一条每刻循环链。`cd_attack` 和 `cd_buff` 不能合并成一个目标。

### 准备：聊天栏执行一次

```text
/scoreboard objectives add cd_attack dummy "攻击冷却"
/scoreboard objectives add cd_buff dummy "增益冷却"
```

### 运行链：2 个冷却共 4 个方块

```text
C1【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a cd_attack 0

C2【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players remove @a[scores={cd_attack=1..}] cd_attack 1

C3【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players add @a cd_buff 0

C4【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players remove @a[scores={cd_buff=1..}] cd_buff 1
```

每增加一个独立冷却，在后面追加两格：第一格补 0，第二格递减。共享循环根节省的是每个新系统的启动根，而不是把两个动作合并。

技能触发时，用 `scores={cd_attack=0}` 作为选择器条件；成功释放后再把该玩家设为所需冷却值。按钮入口、扣费和动画仍按实际动作增加命令方块。

## 多人交易锁

用途：按钮启动后固定同一名玩家，再完成扣费、清物品、发奖励和标签清理。这个模板允许前后命令选择同一个对象。

### 准备：聊天栏执行一次

```text
/scoreboard objectives add coins dummy "金币"
```

### 按钮链：5 个方块

```text
T1【脉冲｜无条件｜需要红石｜延迟0】
/execute as @p[r=3,scores={coins=100..},hasitem={item=diamond,quantity=1..}] run tag @s add tx_shop

T2【连锁｜有条件｜保持开启｜延迟0】
/scoreboard players remove @a[tag=tx_shop,scores={coins=100..}] coins 100

T3【连锁｜有条件｜保持开启｜延迟0】
/clear @a[tag=tx_shop,hasitem={item=diamond,quantity=1..}] diamond 0 1

T4【连锁｜有条件｜保持开启｜延迟0】
/give @a[tag=tx_shop] apple 1

T5【连锁｜无条件｜保持开启｜延迟0】
/tag @a[tag=tx_shop] remove tx_shop
```

T1 失败时不会留下标签；T2 到 T4 失败时，T5 仍会清理已有标签。不同按钮必须使用不同临时标签，例如 `tx_shop`、`tx_reward`、`tx_teleport`。

`clear` 和 `give` 的背包边缘行为仍要在目标客户端验证。满背包时是否掉落、拒绝或覆盖，取决于实际命令返回结果；不要只凭静态语法承诺“必定收到”。

## 推荐组合

| 组合 | 方块预算 | 说明 |
| --- | ---: | --- |
| 首次进入 + 统一 HUD | 4 | 首次进入 3 格，HUD 1 格 |
| 统一 HUD + 两个独立冷却 | 5 | HUD 1 格，共享冷却根 4 格 |
| 首次进入 + HUD + 两个冷却 + 多人交易 | 13 | 这些模块彼此独立，可删去不需要的部分 |
| 普通 HUD + 撤离 + 菜单仲裁层 | 3 | 只算仲裁格；还需接入各系统的状态和动作格，并删除原独立显示格 |
| 多个菜单 | 每个视图至少 1 个显示块 | 显示块共用调度，但每个状态仍需独立的 `titleraw` 命令 |

## 组合规则

1. 先在聊天栏统一创建目标，再启动任何运行链。
2. 只安装当前玩法需要的模块；共享内核不是强制前置。
3. 所有临时标签都要在成功和失败路径清理。
4. 独立冷却使用独立目标，多个系统共享递减根。
5. 多个系统同时使用动作栏时，改用 [hud-arbiter.md](../examples/hud-arbiter.md)，不要保留各自独立的循环输出。
6. 两个独立循环链存在先后依赖时，不要依赖摆放顺序；放进同一链或用标签交接。
7. 组装完成后运行 `validate-skill.mjs`，再按 [test-matrix.md](test-matrix.md) 做双人和持久化测试。
