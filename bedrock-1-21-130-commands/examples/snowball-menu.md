# 雪球菜单（精简版）

命令方块总数：11 个。菜单用一格统一显示全部选项和当前编号，抬头确认、低头关闭；不再为每个选项各放一格显示。

菜单生命周期、取消路径和多设备验收见 [command-ui-playbook.md](../references/command-ui-playbook.md)。

## 准备：聊天栏执行一次

```text
/scoreboard objectives add menu dummy "雪球菜单"
/gamerule commandblockoutput false
```

第二条关闭命令方块输出提示，可按需保留。

## B：运行链

```text
B1【循环｜无条件｜保持开启｜延迟0】
/replaceitem entity @a slot.hotbar 8 destroy snowball 16 0 {"minecraft:item_lock":{"mode":"lock_in_slot"}}

B2【连锁｜无条件｜保持开启｜延迟0】
/execute as @e[type=snowball] at @s run scoreboard players add @p[r=2] menu 1

B3【连锁｜无条件｜保持开启｜延迟0】
/execute as @e[type=snowball] at @s run kill @s

B4【连锁｜无条件｜保持开启｜延迟0】
/scoreboard players set @a[scores={menu=7..}] menu 1

B5【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=1..6}] at @s run titleraw @s actionbar {"rawtext":[{"text":"§l§b雪球菜单  当前："},{"score":{"name":"@s","objective":"menu"}},{"text":" / 6\n§e1. 传送主城  2. 原地去世  3. 生存模式\n§e4. 设置重生点  5. 领取苹果  6. 关闭\n§a抬头确定  §c低头关闭"}]}

B6【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=1},rx=-88] at @s run tp @s 0 64 0 facing 0 64 10

B7【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=2},rx=-88] run kill @s

B8【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=3},rx=-88] run gamemode survival @s

B9【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=4},rx=-88] at @s run spawnpoint @s

B10【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=5},rx=-88] run give @s apple 1

B11【连锁｜无条件｜保持开启｜延迟0】
/execute as @a[scores={menu=1..6}] unless entity @s[rxm=-87,rx=87] run scoreboard players set @s menu 0
```

## 摆放

1. 在聊天栏执行准备命令。
2. B1 是循环方块，设为“无条件｜保持开启｜延迟0”，并开启“执行第一个刻”；B2–B11 接常开连锁，箭头依次指向下一格。
3. `slot.hotbar 8` 是快捷栏第 9 格。该格原有物品会被替换；正式地图建议留空。
4. 命令方块所在区块必须加载，否则菜单物品刷新、雪球检测和抬头执行都会停止。

## 压缩内容与取舍

- 原来每个选项一格高亮显示，现改为统一菜单加“当前编号”，显示部分从 6 格减为 1 格。
- 音效和关闭后额外提示已省略。
- 第 6 项在抬头时直接走到 B11 归零，不单独占用动作方块。
- B11 用 `unless entity @s[rxm=-87,rx=87]` 同时识别近似抬头和低头，把原来两格归零合并为一格。
- 默认把雪球附近最近的玩家当作使用者；多人挤在落点附近可能误选，适合单人菜单区。
- 动作仍然必须一格一条：传送、击杀、切模式、设置重生点和给物品无法塞进显示格。

## 改法与检查

1. 把 B6 的 `0 64 0` 和 `0 64 10` 改成主城坐标与朝向点。
2. 丢出雪球后，动作栏显示菜单和当前编号；继续丢会循环 1–6。
3. 抬头执行当前项，低头直接把菜单清零；执行后 `menu` 也会归零。
4. 用 `/scoreboard players list @s` 查看 `menu` 是否在 0–6。
5. 增加选项时，新增一个动作块，并同时修改 B4 的回绕值、B5 的显示文本及 B11 的关闭范围。
