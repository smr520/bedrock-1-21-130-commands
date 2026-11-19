# `.mcworld` 与 BDS 投影导出

导出层把同一份 chain spec 变成可导入的世界，不改变命令语义。输出只包含世界元数据、LevelDB、命令方块实体、按钮和坐标清单，不加行为包、资源包、函数或 `tick.json`。

## 两种世界交付

| 产物 | 用途 | 结构 |
| --- | --- | --- |
| `.mcworld` | 客户端双击或导入 | ZIP 根目录含 `level.dat`、`levelname.txt`、`db/`、`world_*_packs.json` 和 `projection.json` |
| BDS 世界目录 | 放入 `worlds/<世界名>/` | 与 `.mcworld` 解压后相同的 `level.dat`、`db/` 和说明文件 |

BDS 指 Bedrock Dedicated Server 的世界目录，不是第三方编辑器常用的 `.bdx` 工程文件。两者不要混写；本导出器当前直接生成 BDS 与 `.mcworld`。

文件名使用：

```text
<spec-name>__start_<x>_<y>_<z>__end_<x>_<y>_<z>.mcworld
```

同名 BDS 目录位于 `bds/` 下。起止坐标指命令方块区域的最小角和最大角，轴约定为 X 向东、Y 向上、Z 向南。按钮会让 `visualStart`/`visualEnd` 比命令区多一格，两个范围都写入 `projection.json`。

## 基础命令

```powershell
python -B -X utf8 scripts\export-projection.py examples\same-score-pair-teleport.spec.json --outdir build\exports
```

默认生成：

```text
*.mcworld
bds/<coordinates>/
*.projection.json
*.commands.txt
*.placement.txt
*.SHA256SUMS.txt
```

覆盖输出使用 `--force`。世界元数据模板是 [world-template.level.dat](../assets/world-template.level.dat)，其来源和哈希见 [WORLD_TEMPLATE.md](../assets/WORLD_TEMPLATE.md)。

## 自动布局

spec 顶层可写：

```json
{
  "projection": {
    "origin": [0, 4, 0],
    "axis": "x",
    "layout": "serpentine",
    "width": 64,
    "worldName": "指令测试世界",
    "spawn": [2, 6, 0],
    "buttons": true
  }
}
```

- `origin` 是第一块命令方块的世界坐标。
- `layout:"line"` 单线排列；长链默认用 `serpentine`，按 `width` 折行，减少区块加载跨度。
- 链上每一格必须与 `next` 紧邻；导出器自动写入对应朝向。末端朝上，避免回指下一块。
- `impulse`/`repeat` 默认需要红石，导出器可在上方生成石按钮；`always_active` 不生成按钮。
- 显式坐标可写进每个 `block.pos`。一旦有任一 block 写 `pos`，全部 block 都必须写 `pos`，防止半自动布局造成断链。

CLI 的 `--origin`、`--axis`、`--layout`、`--width`、`--spawn`、`--world-name` 和 `--no-buttons` 可覆盖 spec 中的默认值。

## 坐标清单

`projection.json` 同时嵌入世界并作为外部 sidecar。核心字段：

```json
{
  "bounds": {
    "start": [0, 4, 0],
    "end": [0, 4, 0],
    "size": [1, 1, 1],
    "visualStart": [0, 4, 0],
    "visualEnd": [0, 5, 0],
    "visualSize": [1, 2, 1]
  },
  "spawn": [2, 6, 0],
  "blocks": []
}
```

清单还记录每个命令方块的类型、坐标、朝向、条件、红石模式、延迟、命令、`next` 和备注。`levelname.txt` 同样写入起止坐标，移动或重命名文件后仍可核对原始命令区。

## 导入

1. 客户端：导入同名 `.mcworld`。
2. BDS：停止服务器，把 `bds/<coordinates>/` 复制到 `worlds/<server-world-name>/`，再在服务器配置中引用该世界名并启动。
3. 核对 `projection.json` 的 `start`、`end`、`size`；不要用按钮或视觉边界的坐标代替命令区坐标。
4. 在目标网易客户端和实际 BDS 版本上测试命令方块加载、按钮、链条朝向和区块常加载。

## 验证边界

`export-projection.py --self-test` 会验证：

- chain spec 通过现有命令和链校验。
- `.mcworld` 是 ZIP 根世界容器。
- `level.dat`、`db/CURRENT`、`db/MANIFEST-000000` 和 LevelDB 日志存在。
- 命令方块 NBT 数量与 spec 一致。
- BDS 目录中的每个文件与 `.mcworld` 内文件逐字节一致。

这些检查证明容器和数据结构自洽。当前环境没有网易客户端或实际 BDS，因此仍须记录为 `runtime-unverified`，不能仅凭生成成功宣称实机可导入。

导出后建议再运行只读审计：

```powershell
python -B -X utf8 scripts\audit-mcworld.py <输出.mcworld> --json <回读.json> --markdown <回读.md>
```

回读器会合并 LevelDB 的 `.ldb` 与 `.log`，按 sequence 取当前状态，并使用世界名中的起止坐标裁剪实体。交付前核对：

- `projection.json` 的命令方块数与审计器当前状态数一致。
- `levelname.txt`、文件名与 `projection.json` 的 `bounds` 一致。
- 没有选区外命令实体混入统计。
- 空命令、未知方块类型和物理/NBT 不匹配均为 0，除非 spec 明确要求预留空方块。
- 回读通过仍只证明静态数据结构一致；按钮、箭头、区块加载和客户端导入继续标为运行时未验证。

格式交叉核对：

- [Microsoft Learn：Packaging a world template](https://learn.microsoft.com/en-us/minecraft/creator/documents/packagingaworldtemplate)
- [Microsoft Learn：Differences between Bedrock and Java](https://learn.microsoft.com/en-us/minecraft/creator/documents/differencesbetweenbedrockandjava?view=minecraft-bedrock-experimental)
