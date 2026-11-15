# 选择器与记分板

## 选择器变量

| 变量 | 选中谁 |
| --- | --- |
| `@a` | 所有玩家 |
| `@p` | 最近的玩家 |
| `@r` | 随机一名玩家 |
| `@e` | 所有实体（**包括玩家**） |
| `@n` | 最近的实体（基岩版专属） |
| `@s` | 当前执行者 |
| `@initiator` | 与 NPC 交互的玩家；只在 NPC 对话命令中有效 |

只选实体：`@e[type=!player]`。

## 参数

### 类型与数量

```text
@e[type=zombie]
@e[type=!zombie]
@e[type=zombie,c=5]
@e[type=zombie,c=-5]
@r[type=pig]
```

- `type`：实体 ID；原版通常不带命名空间。
- `c`：数量。`@a`、`@p`、`@e` 按距离排序；`c=-5` 取最远的 5 个；`@r` 随机。
- 没有 `limit`、`sort`。

### 位置与距离

```text
@a[x=100,y=64,z=-20,r=10]
@e[type=zombie,rm=5,r=20]
@e[dx=10,dy=5,dz=10]
```

- `x/y/z`：选择器搜索原点。
- `r` / `rm`：球形距离，最大/最小，按脚部位置算。
- `dx/dy/dz`：长方体体积，按碰撞箱判断。
- 没有 `distance`。

### 名称、标签、族

```text
@e[type=zombie,name="Bob"]
@e[name=!"Bob"]
@a[tag=menu:ready]
@a[tag=menu:ready,tag=!menu:banned]
@e[family=monster]
@e[family=!undead]
```

- `name` 可加引号；`!` 取反。
- `tag` 可重复，多个标签是“且”关系。
- 基岩版没有队伍，`tag` 是最常用的分组方式。
- `family` 来自实体行为文件的族，常见 `monster`、`undead`、`arthropod`。

### 分数

```text
@a[scores={coins=100..}]
@a[scores={coins=10..50,deaths=0}]
@a[scores={coins=!0}]
```

- 范围：`N..`、`..N`、`N..M`。
- 可写多个目标，全部满足才选中。
- 非玩家实体也能有分数；实体死亡时分数会被删除。

### 旋转、等级、模式

```text
@a[rxm=-90,rx=-45]      # 仰视：-90 到 -45
@a[rym=-45,ry=45]       # 水平朝向范围
@a[l=10]                # 等级 <= 10
@a[lm=10,l=20]          # 等级 10..20
@a[m=creative]
@a[m=!survival]
```

- `rx`/`rxm`：俯仰角，-90 到 90；-90 是正上方，90 是正下方。
- `ry`/`rym`：水平旋转，-180 到 180。
- `l`/`lm`：经验等级，只对玩家有效。
- `m` 可用 `0/s/survival`、`1/c/creative`、`2/a/adventure`、`spectator`、`d/default`。

抬头/低头检测：

```text
@a[rx=-88]       # 抬头
@a[rxm=88]       # 低头
```

### 物品与权限

```text
@a[hasitem={item=diamond,quantity=4..}]
@a[hasitem={item=netherite_sword,location=slot.weapon.mainhand}]
@a[hasitem=[{item=diamond,quantity=2},{item=stick,quantity=2}]]
@a[haspermission={camera=enabled}]
@a[haspermission={movement=disabled}]
```

- `hasitem` 参数：`item`（必填）、`quantity`（支持范围）、`data`、`location`、`slot`。
- `hasitem` 可传数组，表示同时拥有多组物品。
- 槽位名：`slot.weapon.mainhand`、`slot.weapon.offhand`、`slot.armor.head`、`slot.container.0`、`slot.hotbar.0`。
- `haspermission` 用 `camera`/`movement` 加 `enabled`/`disabled`。

### 属性

```text
@e[has_property={minecraft:is_baby=true}]
```

属性名来自实体行为文件；不确定时不要用，写错会让整个选择器失效。

### 不可用参数

| 不可用 | 替代 |
| --- | --- |
| `limit` / `sort` | `c` |
| `distance` | `r` / `rm` |
| `nbt` | 不支持；用 tag/分数 |
| `team` | `tag` |
| `predicate` | 不支持 |
| `advancements` | 不支持 |
| `type=#tag` | 不支持 |

## 记分板

### 目标

```text
/scoreboard objectives add menu dummy "雪球菜单"
/scoreboard objectives add coins dummy "金币"
/scoreboard objectives add clock dummy "全局时钟"
/scoreboard objectives list
/scoreboard objectives remove coins
/scoreboard objectives setdisplay sidebar coins descending
```

基岩版**只有 `dummy`**。没有 `deathCount`、`playerKillCount`、`health`、`food`、`air`、`trigger` 等条件类型。

显示槽：

- `sidebar`
- `list`
- `belowname`

没有 Java 的 `below_name`、`tab`。

### 分数操作

```text
/scoreboard players set Steve coins 100
/scoreboard players add Steve coins 10
/scoreboard players remove Steve coins 5
/scoreboard players reset Steve coins
/scoreboard players random @a coins 1 6
/scoreboard players test Steve coins 10 20
/scoreboard players list Steve
```

- `random` 的范围包含最小值和最大值。
- `test` 成功时返回成功数，适合接有条件连锁。
- `reset` 删除分数，不是设 0。
- `list <player>` 可查该玩家所有目标，调试很有用。

### `execute if score` 的单目标限制

`execute ... if score` 进行比较时，运算符左右都必须解析成**一个**目标。`@a`、`@e` 即使加了 `tag=` 或 `scores=`，也可能同时匹配多人；直接放进分数比较会失败。这个限制从基岩版 1.19.60 起明确生效，[官方 MCPE-156279 修复说明](https://feedback.minecraft.net/hc/en-us/articles/11995250732557-Minecraft-Beta-Preview-1-19-60-25)写明 `if|unless score` 不再接受可能返回多个实体的 `@a`、`@e` 选择器；1.21.120 与 1.21.130 没有恢复旧行为。

错误写法：`execute if score @a[tag=turn] coins = @s coins run say 同分`。这里的 `@a` 没有 `c=1`，可能匹配多人。

需要在“两个玩家集合”之间逐对比较时，用执行分叉：`as` 保存被检查方，第一次 `at @s` 固定它的位置，第二次 `at` 遍历对比方。进入第二次 `at` 后，`@s` 仍指向被检查方，`@p` 指向当前对比位置的最近玩家；因此 `if score @s ... = @p ...` 两边都是单目标。这个结构也与 [Bedrock Wiki 的匹配分数写法](https://wiki.bedrock.dev/commands/comparing-scores)一致。

```text
/execute as @a[tag=trigger,r=3,c=1] at @s at @a[tag=eligible,rm=0.1] if score @s score = @p score run tp @s @p
```

这条示例从按钮附近最多选择一名 `trigger`，再遍历 `eligible` 中的其他玩家，把触发方传送到当前同分目标。`c=1`、`r=3` 和标签限制既保证单目标，也限制执行分叉数量。`@p` 仍是位置近似；同一时间只应有一名操作者靠近按钮。

### 运算

```text
/scoreboard players operation .total coins += Steve coins
/scoreboard players operation .total coins -= Steve coins
/scoreboard players operation .total coins *= Steve coins
/scoreboard players operation .total coins /= Steve coins
/scoreboard players operation .total coins %= Steve coins
/scoreboard players operation .a coins = .b coins
/scoreboard players operation .a coins < .b coins
/scoreboard players operation .a coins > .b coins
/scoreboard players operation .a coins >< .b coins
```

| 运算符 | 结果 |
| --- | --- |
| `=` | 赋值 |
| `+=` `-=` `*=` `/=` `%=` | 算术，除法向下取整 |
| `<` | 取较小值 |
| `>` | 取较大值 |
| `><` | 交换两个分数 |

### 假玩家

以 `.` 开头是常用的“全局变量”约定：

```text
/scoreboard players set .config coins 0
/scoreboard players add .clock timer 1
```

假玩家不是实体，不能被选择器选中，只存在于记分板。不要用玩家可能取的名字。

### 初始化要幂等

```text
/scoreboard objectives add clock dummy "全局时钟"
/scoreboard players add .clock clock 0
```

- `objectives add` 重复执行会失败，但不会中断无条件链。
- `players add ... 0` 在分数不存在时创建为 0，已存在时不变。

## 常用状态机

### 全局时钟

```text
【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add .clock timer 1

【连锁｜无条件｜保持开启｜延迟0】
/execute if score .clock timer matches 100.. run scoreboard players set .clock timer 0

【连锁｜无条件｜保持开启｜延迟0】
/execute if score .clock timer matches 0 run say 5 秒到了
```

### 每玩家冷却

```text
【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a cooldown 1

【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={cooldown=200..}] run scoreboard players set @s cooldown 200
```

使用技能时：

```text
/execute as @a[scores={cooldown=200}] run tag @s add skill_ready
/execute as @a[tag=skill_ready] run scoreboard players set @s cooldown 0
/execute as @a[tag=skill_ready] run say 技能释放
/tag @a[tag=skill_ready] remove skill_ready
```

`cooldown=200` 表示冷却已满；`0` 表示刚用过。200 tick = 10 秒。

### 玩家首次进入

```text
【循环｜无条件｜保持开启｜延迟0】
/scoreboard players add @a online 0

【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={online=0}] run tellraw @s {"rawtext":[{"text":"§a欢迎！"}]}

【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a[scores={online=0}] online 1
```

- 分数会存档，所以同一名玩家只记录第一次进入。
- 要识别世界运行期间每名玩家的断开再进，使用专用目标并追加 `scoreboard players reset * online` 与 `scoreboard players set @a online 1` 两个连锁块；不要对金币、冷却或长期档案使用 `reset *`。完整退出世界再打开的行为必须实机验证。完整示例见 [welcome-clock.md](../examples/welcome-clock.md)。
- 玩家真正离开后，选择器无法再选中他本人。比较前后在线人数可以检测总人数净减少，但不能指出具体离线者；同一刻有人进入又有人离开时可能互相抵消。

### 菜单状态机

```text
menu = 0  关闭
menu = 1  第 1 项
menu = 2  第 2 项
...
```

- 丢雪球/按按钮 → `menu` +1。
- 抬头 → 执行当前项 → `menu` 设 0。
- 低头 → 关闭 → `menu` 设 0。
- 超过最大项 → 回到 1。
- 每次显示用 `execute as @a[scores={menu=N}] run titleraw ...`。

### 随机分支

```text
/scoreboard players random @a[tag=crate] crate 1 100

/execute as @a[tag=crate,scores={crate=1..50}] run give @s apple 1
/execute as @a[tag=crate,scores={crate=51..80}] run give @s golden_apple 1
/execute as @a[tag=crate,scores={crate=81..100}] run give @s diamond 1
```

先把参与者打上 `crate` 标签，抽完再删标签。

### 先锁定再修改

```text
/execute as @a[scores={coins=100..},hasitem={item=diamond,quantity=1..}] run tag @s buying
/execute as @a[tag=buying] run scoreboard players remove @s coins 100
/execute as @a[tag=buying] run clear @s diamond 0 1
/execute as @a[tag=buying] run give @s apple 1
/tag @a[tag=buying] remove buying
```

如果先扣分，后面的 `scores={coins=100..}` 就不匹配了。

## 纯指令做不到的事

| 需求 | 限制 |
| --- | --- |
| 读取原版血量 | 基岩版没有 `health` 目标；只能显示自定义分数 |
| 自动统计死亡 | 没有 `deathCount`；只能用自己控制的 `kill`/`damage` 记分 |
| 识别具体离线者 | 选择器只能选在线玩家；离线后不能对该玩家本人执行命令。人数差只能检测总人数净减少 |
| 读取命令返回值 | 没有 `execute store`；只能用 `execute if` 做条件 |
| 读取 NBT | 没有 `data get`；用 `hasitem`/`tag`/分数 |
| 队伍 | 没有 `/team`；用 `tag` |
| 自定义 UI | 纯指令只能 `title`/`titleraw`/侧边栏；复杂 UI 要资源包 |

## 常见错误

1. 目标写成 `deathCount`/`health`：基岩版不支持。
2. 用 `@e[scores={...}]` 选已死亡实体：实体死亡后分数被删除。
3. 忘记建目标，整段记分板命令静默失败。
4. 每刻给所有玩家 `tellraw`：刷屏且卡顿。
5. 用 `team=` 或 `/team`：基岩版没有。
6. 用 `limit`、`sort`、`distance`、`nbt`：选择器直接失效。
7. 假玩家和真实玩家重名：分数混在一起。
8. 认为 `@e` 不含玩家：需要时加 `type=!player`。
9. 先改分数再判断：后面的选择器匹配不到；用临时 `tag`。
10. 抬头/低头写反：`rx=-88` 是抬头，`rxm=88` 是低头。
