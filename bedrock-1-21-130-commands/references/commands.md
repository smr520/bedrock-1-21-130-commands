# 1.21.130 纯指令速查

面向命令方块。命令方块里 `/` 可写可不写；聊天栏必须写。下面统一带 `/`，粘贴到两边都能用。

## 通用语法

- 坐标：绝对 `100 64 -20`；相对 `~ ~1 ~`；局部 `^ ^ ^3`。
- 选择器：`@a`、`@p`、`@r`、`@e`、`@n`、`@s`、`@initiator`。
- 范围：`1..5`、`..5`、`1..`。
- 字符串含空格时加双引号：`name="Steve"`。
- 方块状态：`["state"=value]`，例如 `["color"="red"]`。
- 文本 JSON：基岩版用 `{"rawtext":[{"text":"..."}]}`。
- 数字、引号、逗号、冒号全部用半角。

## 玩家与实体

| 用途 | 语法 | 备注 |
| --- | --- | --- |
| 切换模式 | `/gamemode <survival\|creative\|adventure\|spectator\|default> [player]` | 也接受 `s/c/a/d`；目标写在模式后面 |
| 传送 | `/tp <target> <x y z> [yRot xRot]` | `/teleport` 同义 |
| 传送并朝向 | `/tp <target> <x y z> facing <x y z>` | 也可 `facing entity <target> eyes\|feet` |
| 给物品 | `/give <player> <item> [amount] [data] [components]` | 无 NBT |
| 清物品 | `/clear <player> [item] [data] [maxCount]` | 不写 item 清空背包 |
| 替换槽位 | `/replaceitem entity <target> <slot> <slotId> <destroy\|keep> <item> [amount] [data] [components]` | 1.21.130 推荐显式写出旧物品处理方式；基岩版没有 `/item replace` |
| 效果 | `/effect <player> <effect> [seconds] [amplifier] [hideParticles]` | amplifier 从 0 开始 |
| 附魔 | `/enchant <player> <enchantment> [level]` | 作用于手持物品；等级从 1 开始 |
| 经验 | `/xp <amount> [player]` 或 `/xp <amount>L [player]` | `L` 是等级 |
| 杀死 | `/kill <target>` | |
| 标签 | `/tag <target> <add\|remove\|list> [name]` | 用标签分组，替代队伍 |
| 伤害 | `/damage <target> <amount> [cause] [entity]` | 1.19.80+ |
| 召唤 | `/summon <entity> [x y z] [spawnEvent] [nameTag]` | **不能带 NBT** |
| 重生点 | `/spawnpoint <player> [pos]` | |
| 世界出生点 | `/setworldspawn [pos]` | |
| 骑乘 | `/ride <riders> <ride>` | 让实体骑上去 |
| 摄像机 | `/camera <player> <set\|clear\|fade\|...>` | 基岩专属 |
| 输入限制 | `/inputpermission set <player> <camera\|movement> <enabled\|disabled>` | 基岩专属 |

`give`/`replaceitem` 的组件只支持四种：

```text
minecraft:can_place_on
minecraft:can_destroy
minecraft:item_lock
minecraft:keep_on_death
```

示例：

```text
/give @s diamond_pickaxe 1 0 {"minecraft:can_destroy":{"blocks":["stone"]}}
/give @s diamond_sword 1 0 {"minecraft:can_place_on":{"blocks":["grass_block"]}}
/replaceitem entity @a slot.hotbar 8 destroy snowball 16 0 {"minecraft:item_lock":{"mode":"lock_in_slot"}}
```

不要写 Java 的 `{Enchantments:[...]}`、`{display:{Name:...}}`。

## 方块与区域

| 用途 | 语法 | 备注 |
| --- | --- | --- |
| 放方块 | `/setblock <pos> <block> [states] [replace\|keep\|destroy]` | |
| 填充 | `/fill <from> <to> <block> [states] [destroy\|hollow\|keep\|outline\|replace]` | 单次最多 32,768 格 |
| 条件替换 | `/fill <from> <to> <block> [states] replace [replaceBlock] [replaceStates]` | 只替换指定方块 |
| 复制 | `/clone <begin> <end> <destination> [replace\|masked] [normal\|force\|move]` | 单次上限比 fill 大，仍不要拉太远 |
| 过滤复制 | `/clone <begin> <end> <destination> filtered <normal\|force\|move> <block> [states]` | 1.21.130 修复了 filtered |
| 保存结构 | `/structure save <name> <from> <to> [includeEntities] [disk\|memory] [includeBlocks]` | |
| 加载结构 | `/structure load <name> <to> [rotation] [mirror] [includeEntities] [includeBlocks] [waterlogged] [integrity] [seed]` | 旋转写 `90_degrees` |
| 删除结构 | `/structure delete <name>` | |
| 放置结构 | `/place structure <name> [pos]` | |
| 放置地物 | `/place feature <feature> [pos]` | 需要对应地物 ID |

方块状态示例：

```text
/setblock ~ ~1 ~ command_block ["facing_direction"=1]
/setblock ~ ~2 ~ wool ["color"="red"]
/fill ~ ~ ~ ~10 ~ ~ stone ["stone_type"="granite"]
```

填充模式：

- `replace`：全部替换，不掉落。
- `keep`：只替换空气。
- `hollow`：填外壳，内部清空为空气。
- `outline`：填外壳，内部方块保持原样。
- `destroy`：替换并掉落原方块。

任一维度小于 3 时，`hollow`/`outline` 都接近 `replace`。

判断方块：

```text
/execute if block ~ ~-1 ~ stone run say 脚下是石头
/execute unless block ~ ~-1 ~ air run say 脚下不是空气
```

`testforblock`、`testforblocks` 仍可用，但新代码建议用 `execute if`。

## execute（1.19.50+ 新语法）

```text
/execute <子命令链> run <命令>
```

| 子命令 | 作用 |
| --- | --- |
| `as <target>` | 改变执行者，`@s` 随之改变 |
| `at <target>` | 改变位置、旋转、维度 |
| `positioned <x y z>` | 只改位置 |
| `positioned as <target>` | 用目标位置 |
| `align <x\|y\|z\|xy\|xz\|yz\|xyz>` | 位置向下取整 |
| `anchored <eyes\|feet>` | 改变局部坐标锚点 |
| `rotated <yaw> <pitch>` | 改旋转 |
| `rotated as <target>` | 用目标旋转 |
| `facing <x y z>` | 朝向坐标 |
| `facing entity <target> <eyes\|feet>` | 朝向实体 |
| `in <overworld\|nether\|the_end>` | 改维度 |
| `if/unless block <pos> <block> [states]` | 判断方块 |
| `if/unless blocks <begin> <end> <dest> <all\|masked>` | 判断区域 |
| `if/unless entity <target>` | 判断实体存在 |
| `if/unless score <target> <obj> matches <range>` | 判断分数范围 |
| `if/unless score <target> <obj> <op> <target> <obj>` | 比较两个分数；`<op>` 为 `=` `<` `<=` `>` `>=` |
| `run <command>` | 执行命令，放最后 |

示例：

```text
/execute as @a at @s run playsound random.levelup @s ~ ~ ~ 1 1
/execute as @a at @s if block ~ ~-1 ~ grass_block run effect @s regeneration 5 0 true
/execute as @e[type=zombie,c=5] at @s run particle minecraft:large_explosion ~ ~1 ~
/execute if score .clock timer matches 100.. run say 5 秒到了
```

旧语法 `execute @a ~ ~ ~ say hi` 在 1.21.130 会直接报错。

## 记分板

```text
/scoreboard objectives add <name> dummy [displayName]
/scoreboard objectives remove <name>
/scoreboard objectives list
/scoreboard objectives setdisplay sidebar <name> [ascending|descending]
/scoreboard objectives setdisplay list <name>
/scoreboard objectives setdisplay belowname <name>

/scoreboard players set <target> <obj> <value>
/scoreboard players add <target> <obj> <value>
/scoreboard players remove <target> <obj> <value>
/scoreboard players reset <target> [obj]
/scoreboard players test <target> <obj> <min> [max]
/scoreboard players random <target> <obj> <min> <max>
/scoreboard players operation <target> <obj> <op> <source> <obj>
```

- 基岩版目标**只有 `dummy`**；没有 `deathCount`、`health`、`xp`、`food` 等自动目标。
- 没有 `/team`；用 `tag` 分组。
- 显示槽只有 `sidebar`、`list`、`belowname`。
- `operation` 运算符：`=`、`+=`、`-=`、`*=`、`/=`、`%=`、`<`、`>`、`><`。
- 假玩家用 `.` 开头，例如 `.clock`、`.total`；不要和真实玩家重名。
- `reset` 是删除分数，不是设成 0。

## 文本、声音、粒子

```text
/tellraw @a {"rawtext":[{"text":"§aHello"}]}
/titleraw @a title {"rawtext":[{"text":"§6标题"}]}
/titleraw @a subtitle {"rawtext":[{"text":"§7副标题"}]}
/titleraw @a actionbar {"rawtext":[{"text":"§b动作栏"}]}

/title @a title 纯文本标题
/title @a actionbar §a纯文本动作栏
```

`tellraw`/`titleraw` 的 JSON 写法：

```text
/tellraw @a {"rawtext":[{"text":"金币："},{"score":{"name":"@s","objective":"coins"}}]}
/tellraw @a {"rawtext":[{"selector":"@s"},{"text":" 加入了服务器"}]}
/titleraw @a actionbar {"rawtext":[{"text":"§e生命 "},{"score":{"name":"@s","objective":"hp"}},{"text":"/100"}]}
```

- `\n` 可换行：`{"rawtext":[{"text":"第一行\n第二行"}]}`。
- 颜色用 `§`，例如 `§a`、`§c`、`§l`。
- 基岩版 `particle` 没有 Java 的 `count dx dy dz speed` 参数。
- 粒子 ID 用游戏内补全确认；常用 `minecraft:basic_flame_particle`、`minecraft:large_explosion`。

```text
/playsound random.levelup @a ~ ~ ~ 1 1
/stopsound @a random.levelup
/particle minecraft:basic_flame_particle ~ ~1 ~
```

## 世界、时间与规则

```text
/time set day
/time add 1000
/time query daytime
/weather clear
/weather rain 600
/difficulty normal
/gamerule sendcommandfeedback false
/gamerule showcoordinates true
```

常用基岩版 gamerule（全小写）：

`commandblocksenabled`、`commandblockoutput`、`sendcommandfeedback`、`showcoordinates`、`showtags`、`showdeathmessages`、`keepinventory`、`mobgriefing`、`naturalregeneration`、`tntexplodes`、`dodaylightcycle`、`doweathercycle`、`randomtickspeed`、`spawnradius`、`falldamage`、`firedamage`、`drowningdamage`、`freezedamage`、`pvp`、`doentitydrops`、`domobspawning`、`domobloot`、`dofiretick`、`playerssleepingpercentage`、`respawnblocksexplode`、`maxcommandchainlength`。

不确定时输入 `/gamerule ` 看补全，不要照抄 Java 的驼峰写法。

## 常加载区

```text
/tickingarea add <from> <to> [name] [preload]
/tickingarea add circle <center> <radius> [name] [preload]
/tickingarea remove <name|pos>
/tickingarea list [all-dimensions]
```

- 命令方块所在区块必须加载。
- 玩家走远后系统停了，先查 `tickingarea list`。
- 圆形常加载区半径 0–4 区块。

## 其他有用命令

```text
/loot give @s loot <loot_table>
/ride @s <entity>
/inputpermission set @s movement disabled
```

`/loot` 的桌子名用游戏内补全；自定义战利品表需要行为包，纯指令只用原版表。

## Java → 基岩版差异

| Java | 基岩版 |
| --- | --- |
| `data get/merge/modify` | 不支持；用记分板/结构替代 |
| `execute store` | 不支持；用 `scoreboard players operation` |
| `execute if data` | 不支持 |
| `execute if items` | 不支持；用 `hasitem` 选择器 |
| `execute if biome` | 不支持 |
| `predicate` | 不支持 |
| `summon <entity> ~ ~ ~ {NBT}` | `summon <entity> ~ ~ ~`，无 NBT |
| `give ... {Enchantments:[...]}` | 不支持；用 `/enchant` 或四种组件 |
| `tellraw @a {"text":"hi"}` | `tellraw @a {"rawtext":[{"text":"hi"}]}` |
| `team` / `team=` | 不支持；用 `tag` |
| `bossbar` | 不支持；用 `title`/`titleraw`/侧边栏 |
| `attribute` | 不支持 |
| `advancement` | 不支持 |
| `recipe` | 不支持 |
| `forceload` | 用 `tickingarea` |
| `datapack` | 用行为包；纯指令不需要 |
| `function ns:path` | 展开函数里的逐条命令，依次填进命令方块；递归与定时改用分数/标签状态机 |
| `@e[limit=5,sort=nearest,distance=..10]` | `@e[c=5,r=10]` |
| `@e[nbt={...}]` | 不支持 |
| `item replace` | `replaceitem` |
| `fillbiome` | 不支持 |
| `place template` | `structure load` 或 `place structure` |

## 容易踩的坑

1. 用了旧 `execute @e ~~~`。
2. 选择器写了 `limit`、`sort`、`distance`、`nbt`、`team`。
3. `tellraw` 用了 Java 顶层文本组件，没有 `rawtext`。
4. 记分板目标写了 `deathCount`、`health`：基岩版只支持 `dummy`。
5. 方块状态用了 Java 的 `[facing=north]`，或还在用数据值 `wool 14`。
6. `summon`、`give` 后面带 NBT。
7. 用了 `/item replace`，基岩版是 `/replaceitem`。
8. 命令方块链方向反了、有条件卡住、循环根设成“需要红石”。
9. 命令方块所在区块没加载。
10. 先改分数再判断，导致后面的命令选择器不匹配；用临时 `tag` 锁定。
11. `@e` 包括玩家；只选实体要加 `type=!player`。
12. 全角 `～`、`，`、`：`、`｜` 粘进命令里。
