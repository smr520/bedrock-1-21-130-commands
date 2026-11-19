# 生成 MCWorld 与 BDS 投影

用现有 [同分互传 spec](same-score-pair-teleport.spec.json)直接生成可导入世界：

```powershell
python -B -X utf8 scripts\export-projection.py examples\same-score-pair-teleport.spec.json --outdir build\exports
```

预期生成：

```text
same-score-pair-teleport__start_0_4_0__end_0_4_0.mcworld
bds/same-score-pair-teleport__start_0_4_0__end_0_4_0/
same-score-pair-teleport__start_0_4_0__end_0_4_0.projection.json
same-score-pair-teleport__start_0_4_0__end_0_4_0.commands.txt
same-score-pair-teleport__start_0_4_0__end_0_4_0.placement.txt
same-score-pair-teleport__start_0_4_0__end_0_4_0.SHA256SUMS.txt
```

命令方块位于 `0 4 0`，起止坐标都是 `0 4 0`；石按钮位于 `0 5 0`，因此视觉范围终点是 `0 5 0`。世界出生点由 spec 写为 `2 6 0`。

覆盖已有输出：

```powershell
python -B -X utf8 scripts\export-projection.py examples\same-score-pair-teleport.spec.json --outdir build\exports --force
```

客户端导入 `.mcworld`。BDS 停止后，把 `bds/<coordinates>/` 目录放到 `worlds/<世界名>/`，再用服务器配置引用该世界。完整字段和边界见 [projection-export.md](../references/projection-export.md)。
