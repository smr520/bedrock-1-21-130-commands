# 网易 / 国际版旧图升级到 1.21.130

网易真实地图合集里旧写法不少，尤其是枪械/神器类文件。网易 3.10 / BE1.21.130 和国际版 1.21.130 新图都应使用 1.19.50 之后的现代 `execute`。旧地图中的命令方块会保存创建或编辑时的命令版本，不能只看方块里的文本猜测它一定按当前语法解析。

v3.5 扩展语料从世界、BDX 和 `.building` 中恢复出约 3,252 条旧 `execute @...`，是数量最多的静态问题。另有大量 `scoreboard players test`、旧方块数据值、`replaceitem` 组件和坏 rawtext JSON。因此旧图只能作为迁移来源；转换和静态校验后的最小片段才进入正向示例。

## 旧地图与命令版本

从一个旧世界直接升级时，先复制并备份世界，再逐条打开需要迁移的命令方块。修改并保存命令，让方块记录当前命令版本；完成后分别测试循环、脉冲和连锁箭头。不要依赖批量文本替换，也不要把新语法粘贴到仍携带旧版本值的方块后宣称已经迁移。

- 官方 1.19.50 更新说明要求使用新 `execute` 的命令方块进行更新。
- [MCPE-164725](https://bugs.mojang.com/browse/MCPE/issues/MCPE-164725) 记录了 1.19.50 前创建的方块携带旧版本值，导致新 `execute` 无法工作时，重新编辑并保存后恢复。该问题被标记为 `Works As Intended`。
- 编辑后再做实机复核；文本看起来正确不能替代旧地图迁移测试。

## 转换四步

旧语法：

```text
/execute <目标> <坐标> <命令>
```

新语法：

```text
/execute as <目标> at @s run <命令>
```

1. `as <目标>`：让目标成为执行者，命令里的 `@s` 指向它。
2. `at @s`：把位置/旋转改成目标的位置；命令里用 `~ ~ ~` 就必须加。
3. `detect` 改成 `if block`。
4. 命令前加 `run`，放最后。

## 语料清洗顺序

旧合集不能按“搜索替换”直接现代化。先判断语义，再改语法：

1. 按字节探测 UTF-8、GB18030、UTF-16；把扩展名伪装、乱码和文档说明排除。
2. 把一条文本里的说明、编号、注释与真正命令拆开；一条命令一行。
3. 以 `&&` 串起的多个动作先拆成多个动作，再按执行是否依赖前一步决定普通连锁或有条件连锁。
4. 分析旧 `execute` 中哪部分是执行者、哪部分是位置、哪部分是条件；不要机械只做 `execute @e ~~~` 字符串替换。
5. 把中文内部记分板/标签改成 ASCII，同步修改该文件内所有引用。
6. 先保留业务状态机，按 `references/block-budget.md` 合并检测、计时和显示。
7. 用 `scripts/validate-commands.mjs` 做静态检查，最后进游戏验证。

常见资料类型要分别处理：

| 资料表现 | 处理方式 |
| --- | --- |
| 已经是现代 `execute ... run` | 优先参考；仍检查依赖、坐标、中文内部名和版本 |
| 旧 `execute @目标 坐标 命令` | 按执行者、位置、条件重写，不能盲换 |
| 文件名写 `1CB`、`5CB` | 只把数字当局部预算，统计完整依赖后再报总数 |
| `.docx` / `.pdf` | 先提取文字，再检查截图里的方块设置是否缺失 |
| `.bdx` / `.mcstructure` | 结构导入资料；必须同时交付结构或坐标 |
| `.building` | zlib JSON 工程；命令通常在 `blockCompleteNBT` 的 URL 编码 SNBT 中，用 `audit-building.py` 提取 |
| `.mcworld` / `.mcaddon` | 世界或附加包，不是可直接粘贴的纯指令 |
| `.exe` / 未审查脚本 | 不运行，也不作为技能依赖 |

一段文本若用 `&&` 压缩了多个副作用，现代化后仍然要拆成多格。新 `execute` 的条件链负责判断，不能把多条动作秘密塞进同一格：

```text
旧资料（示意）：
scoreboard players add @s coins 1 && title @s actionbar +1

命令方块序列：
B1【脉冲｜无条件｜需要红石｜延迟0】
/scoreboard players add @s coins 1
B2【连锁｜无条件｜保持开启｜延迟0】
/title @s actionbar +1
```

需要“第一步成功后才执行第二步”时，把 B2 改成“有条件”；需要多人交易安全时，先用标签固定 B1 选中的玩家。

## 逐条对照

| 旧写法 | 新写法 |
| --- | --- |
| `execute @e[type=zombie] ~ ~ ~ say hi` | `execute as @e[type=zombie] at @s run say hi` |
| `execute @a ~ ~ ~ say hi` | `execute as @a at @s run say hi` |
| `execute @p ~ ~ ~ give @p apple` | `execute as @p at @s run give @s apple` |
| `execute @a ~ ~ ~ title @a actionbar hi` | `execute as @a at @s run title @s actionbar hi` |
| `execute @e[type=arrow] ~ ~ ~ particle ...` | `execute as @e[type=arrow] at @s run particle ...` |
| `execute @a ~ ~ ~ detect ~ ~-1 ~ stone 0 say hi` | `execute as @a at @s if block ~ ~-1 ~ stone run say hi` |
| `execute @e[type=zombie] ~ ~ ~ detect ~ ~ ~ air 0 kill @s` | `execute as @e[type=zombie] at @s if block ~ ~ ~ air run kill @s` |
| `execute @a ~ ~ ~ detect ~ ~1 ~ command_block -1 say hi` | `execute as @a at @s if block ~ ~1 ~ command_block run say hi` |
| `execute @e[type=item] ~ ~ ~ testfor @p[r=2]` | `execute as @e[type=item] at @s if entity @p[r=2] run say hi` |
| `testfor @a[scores={coins=1..}]` | `execute if entity @a[scores={coins=1..}]` |
| `testforblock ~ ~-1 ~ stone` | `execute if block ~ ~-1 ~ stone` |
| `testforblocks 0 0 0 10 10 10 20 0 0` | `execute if blocks 0 0 0 10 10 10 20 0 0 all` |
| `fill ~ ~ ~ ~10 ~10 ~10 stone 0 outline` | `fill ~ ~ ~ ~10 ~10 ~10 stone outline` |
| `setblock ~ ~ ~ wool 14` | `setblock ~ ~ ~ wool ["color"="red"]` |
| `summon zombie ~ ~ ~ {IsBaby:1b}` | `summon zombie ~ ~ ~`（不能带 NBT） |
| `give @s diamond_sword 1 0 {Enchantments:[{id:"sharpness",lvl:5}]}` | `give @s diamond_sword` 然后 `/enchant @s sharpness 5` |
| `tellraw @a {"text":"hi"}` | `tellraw @a {"rawtext":[{"text":"hi"}]}` |
| `@e[limit=5,sort=nearest,distance=..10]` | `@e[c=5,r=10]` |
| `@a[team=red]` | `@a[tag=red]` |
| `scoreboard objectives add deaths deathCount` | `scoreboard objectives add deaths dummy`，死亡检测另写 |
| `execute store result score @s coins run ...` | 没有等价物；用 `scoreboard players operation` |
| `data get entity @s SelectedItem` | 没有等价物；用 `hasitem` |
| `item replace entity @s weapon.mainhand with diamond_sword` | `replaceitem entity @s slot.weapon.mainhand 0 destroy diamond_sword` |
| `forceload add 0 0 10 10` | `tickingarea add 0 0 0 10 10 10 menu` |
| `function ns:path` | 读取函数内的命令，逐条展开到命令方块；递归、定时逻辑改用分数/标签状态机 |
| `execute always run ...` | 基岩版没有 `always`；用循环命令方块持续执行 |
| `execute if weather ...` | 基岩版不能直接查询天气；只能由改变天气的机关记录自定义状态 |
| `tellraw @a ["",{"text":"hi","color":"green"}]` | `tellraw @a {"rawtext":[{"text":"§ahi"}]}` |
| `scoreboard players test @a coins 1..` | 对每名玩家执行时用 `execute as @a if score @s coins matches 1.. run ...`；只判断“有人满足”时用 `execute if entity @a[scores={coins=1..}] run ...` |

## 常见旧写法拆解

### 1. 只改执行者

旧：

```text
/execute @a ~ ~ ~ scoreboard players add @a coins 1
```

问题：`@a` 会让每个执行者再给所有玩家加一次，重复 N 次。

新：

```text
/execute as @a at @s run scoreboard players add @s coins 1
```

### 2. detect 判断脚下

旧：

```text
/execute @a ~ ~ ~ detect ~ ~-1 ~ grass_block 0 effect @s regeneration 5 0 true
```

新：

```text
/execute as @a at @s if block ~ ~-1 ~ grass_block run effect @s regeneration 5 0 true
```

### 3. 箭/雪球/鱼钩附近检测

旧：

```text
/execute @e[type=arrow] ~ ~ ~ detect ~ ~-1 ~ air 0 say 命中
```

新：

```text
/execute as @e[type=arrow] at @s if block ~ ~-1 ~ air run say 命中
```

### 4. 旧 `-1` 数据值

旧教程里 `detect ~ ~ ~ command_block -1` 的 `-1` 表示“任意数据值”。新语法直接省略状态：

```text
/execute as @a at @s if block ~ ~ ~ command_block run say 是命令方块
```

### 5. 旧 `~~~`

旧文件常写 `~~~`。基岩版能解析，但建议统一写 `~ ~ ~`，方便阅读和排查。

### 6. 旧 `minecraft:` 前缀

旧文件常写 `type=minecraft:fishing_hook`。基岩版实体选择器通常直接写：

```text
@e[type=fishing_hook]
```

自定义实体才需要 `namespace:entity`。

### 7. 多个玩家不能直接放进 `if score`

自基岩版 1.19.60 起，`execute ... if|unless score` 的运算符两侧必须解析为单个目标。`@a`、`@e` 即使加了 `tag=`、`scores=` 或当前只命中一名玩家，也不应直接写进比较位置。

把旧的“测试所有玩家”拆成两种语义：

```text
# 每名满足条件的玩家各自执行一次
/execute as @a if score @s coins matches 1.. run say 我有正数金币

# 只判断全服是否存在满足条件的人
/execute if entity @a[scores={coins=1..}] run say 至少一名玩家有正数金币
```

不要写成：

```text
execute if score @a coins matches 1.. run say 至少一名玩家有正数金币
```

需要在两组玩家间逐对比较时，用 `as → at @s → at 对比集合` 保存两种上下文：

```text
/execute as @a[tag=source,c=1] at @s at @a[tag=target,rm=0.1] if score @s coins = @p coins run say 找到同分目标
```

进入第二次 `at` 后，`@s` 仍是来源，`@p` 是当前目标。多目标 `at` 会产生执行分叉，实例数按来源数与目标数相乘；大集合先用 `tag=`、`r=`、`c=` 限制。

## 方块数据值 → 方块状态

1.19.70 起，`setblock`/`fill`/`clone` 不再用 `tileData` 数字。常见替换：

| 旧写法 | 新写法 |
| --- | --- |
| `wool 14` | `wool ["color"="red"]` |
| `concrete 14` | `concrete ["color"="red"]` |
| `stained_glass 14` | `stained_glass ["color"="red"]` |
| `planks 0` | `planks ["wood_type"="oak"]` |
| `stone 1` | `stone ["stone_type"="granite"]` |
| `stone 3` | `stone ["stone_type"="diorite"]` |
| `stone 5` | `stone ["stone_type"="andesite"]` |
| `light_block 15` | `light_block ["block_light_level"=15]` |
| `command_block 0` | `command_block`（朝向用 `facing_direction`，建议手动摆） |

不确定状态名时，在游戏里输入：

```text
/setblock ~ ~ ~ wool 
```

按 Tab 看补全，或查 1.21.130 的方块状态表。

## Java 专属写法

这些在基岩版没有等价命令，别照抄：

| Java | 替代 |
| --- | --- |
| `data get/merge/modify` | 记分板、`hasitem`、结构 |
| `execute store` | `scoreboard players operation` + 条件链 |
| `execute if data` | 无 |
| `execute if items` | `hasitem` 选择器 |
| `execute if biome` | 无 |
| `predicate` | 无 |
| `team` / `team=` | `tag` |
| `bossbar` | `titleraw`/`title`/侧边栏 |
| `attribute` | 无 |
| `advancement` | 无 |
| `recipe` | 无 |
| `forceload` | `tickingarea` |
| `datapack` | 行为包；纯指令不需要 |
| `item replace` | `replaceitem` |
| `fillbiome` | 无 |
| `place template` | `structure load` / `place structure` |
| `summon ... {NBT}` | 无 NBT；用生成事件/行为包 |
| `give ... {Enchantments:[...]}` | `/enchant` 或四种组件 |

## 全角符号

从网页/文档复制命令时，先替换：

| 全角 | 半角 |
| --- | --- |
| `～` | `~` |
| `，` | `,` |
| `：` | `:` |
| `；` | `;` |
| `｜` | `|` |
| `（` `）` | `(` `)` |
| `“` `”` | `"` |
| `＠` | `@` |
| `＃` | `#` |
| `％` | `%` |
| `＆` | `&` |
| `＊` | `*` |
| `／` | `/` |
| `－` | `-` |
| `＋` | `+` |
| `＝` | `=` |

颜色符号 `§` 和中文文本里的全角标点没问题；**命令语法部分**必须是半角。

## 真实片段转换

旧（枪械模板）：

```text
execute @e[type=minecraft:fishing_hook] ~~~ tag @a[scores={弹夹=1..,射击a=0},r=2,hasitem={item=fishing_rod,location=slot.weapon.mainhand}] add 射击
```

新：

```text
execute as @e[type=fishing_hook] at @s run tag @a[scores={弹夹=1..,射击a=0},r=2,hasitem={item=fishing_rod,location=slot.weapon.mainhand}] add 射击
```

旧（雪球菜单）：

```text
execute @e[type=snowball] ~~~ scoreboard players add @p[r=2] 雪球菜单 1
```

新：

```text
execute as @e[type=snowball] at @s run scoreboard players add @p[r=2] menu 1
```

旧（检测方块）：

```text
execute @a ~~~ detect ~ ~-1 ~ grass_block 0 effect @s regeneration 5 0 true
```

新：

```text
execute as @a at @s if block ~ ~-1 ~ grass_block run effect @s regeneration 5 0 true
```

## 批量检查

用技能里的校验脚本扫整份文本：

```powershell
node scripts/validate-commands.mjs <文件.txt>
```

它会报旧 `execute @`、Java 选择器、`execute store`、`data get`、全角符号、坏 JSON 等。先修 error，再进游戏。

批量旧图先按当前状态提取命令，不要直接改存档压缩包。世界使用 `audit-mcworld.py`，BDX 使用外部只读解析器，`.building` 使用 `audit-building.py`；导出到私有临时文本后统一校验。静态通过后仍需在目标网易客户端重新编辑并保存旧方块。
