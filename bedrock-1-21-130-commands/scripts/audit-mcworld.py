#!/usr/bin/env python3
"""Read-only audit of Bedrock .mcworld archives for command-corpus suitability."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
import struct
import sys
import tempfile
import zipfile
from pathlib import Path


TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
MAX_ENTRY_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024


class AuditError(RuntimeError):
    pass


def encode_string(value: str):
    data = value.encode("utf-8")
    return struct.pack("<H", len(data)) + data


def encode_payload(tag: int, value):
    if tag == TAG_BYTE:
        return struct.pack("<b", int(value))
    if tag == TAG_INT:
        return struct.pack("<i", int(value))
    if tag == TAG_STRING:
        return encode_string(str(value))
    if tag == TAG_COMPOUND:
        return encode_compound(value)
    raise AuditError(f"unsupported encoder tag {tag}")


def encode_compound(values: dict):
    output = bytearray()
    for name, (tag, value) in values.items():
        output.extend(bytes([tag]))
        output.extend(encode_string(name))
        output.extend(encode_payload(tag, value))
    output.append(0)
    return bytes(output)


def encode_root_compound(values: dict):
    return bytes([TAG_COMPOUND]) + encode_string("") + encode_compound(values)


def encode_varint(value: int):
    output = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        output.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(output)


def encode_log(pairs, block_size: int = 32768):
    output = bytearray()

    def emit(body: bytes):
        position = 0
        first = True
        while position < len(body) or (first and not body):
            available = block_size - (len(output) % block_size)
            if available < 7:
                output.extend(b"\x00" * available)
                available = block_size
            take = min(len(body) - position, available - 7)
            last = position + take == len(body)
            record_type = 1 if first and last else 2 if first else 4 if last else 3
            chunk = body[position:position + take]
            checksum = mask_crc(crc32c(bytes([record_type]) + chunk))
            output.extend(struct.pack("<IHB", checksum, take, record_type))
            output.extend(chunk)
            position += take
            first = False

    for sequence, key, value in pairs:
        body = (
            struct.pack("<QI", sequence, 1)
            + bytes([1])
            + encode_varint(len(key))
            + key
            + encode_varint(len(value))
            + value
        )
        emit(body)
    return bytes(output)


def decode_payload(data: bytes, offset: int, tag: int):
    if tag == TAG_BYTE:
        return struct.unpack("<b", data[offset:offset + 1])[0], offset + 1
    if tag == TAG_SHORT:
        return struct.unpack("<h", data[offset:offset + 2])[0], offset + 2
    if tag == TAG_INT:
        return struct.unpack("<i", data[offset:offset + 4])[0], offset + 4
    if tag == TAG_LONG:
        return struct.unpack("<q", data[offset:offset + 8])[0], offset + 8
    if tag == TAG_FLOAT:
        return struct.unpack("<f", data[offset:offset + 4])[0], offset + 4
    if tag == TAG_DOUBLE:
        return struct.unpack("<d", data[offset:offset + 8])[0], offset + 8
    if tag == TAG_BYTE_ARRAY:
        length = struct.unpack("<i", data[offset:offset + 4])[0]
        return list(data[offset + 4:offset + 4 + length]), offset + 4 + length
    if tag == TAG_STRING:
        length = struct.unpack("<H", data[offset:offset + 2])[0]
        start = offset + 2
        return data[start:start + length].decode("utf-8", "replace"), start + length
    if tag == TAG_LIST:
        element_tag = data[offset]
        length = struct.unpack("<i", data[offset + 1:offset + 5])[0]
        offset += 5
        items = []
        for _ in range(length):
            item, offset = decode_payload(data, offset, element_tag)
            items.append(item)
        return (element_tag, items), offset
    if tag == TAG_COMPOUND:
        values = {}
        while True:
            item_tag = data[offset]
            offset += 1
            if item_tag == 0:
                return values, offset
            name_length = struct.unpack("<H", data[offset:offset + 2])[0]
            offset += 2
            name = data[offset:offset + name_length].decode("utf-8", "replace")
            offset += name_length
            item, offset = decode_payload(data, offset, item_tag)
            values[name] = (item_tag, item)
    if tag == TAG_INT_ARRAY:
        length = struct.unpack("<i", data[offset:offset + 4])[0]
        start = offset + 4
        items = list(struct.unpack("<" + "i" * length, data[start:start + length * 4]))
        return items, start + length * 4
    raise AuditError(f"unsupported NBT tag {tag} at offset {offset}")


def decode_named_tag(data: bytes, offset: int = 0):
    tag = data[offset]
    offset += 1
    if tag == 0:
        return tag, "", None, offset
    name_length = struct.unpack("<H", data[offset:offset + 2])[0]
    offset += 2
    name = data[offset:offset + name_length].decode("utf-8", "replace")
    offset += name_length
    value, offset = decode_payload(data, offset, tag)
    return tag, name, value, offset


def decode_level_dat(raw: bytes):
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
        storage_version = 10
        body = raw
    else:
        storage_version, declared = struct.unpack("<II", raw[:8])
        body = raw[8:8 + declared]
        if len(body) != declared:
            raise AuditError("level.dat length header mismatch")
    tag, _, root, end = decode_named_tag(body, 0)
    if tag != TAG_COMPOUND or end != len(body):
        raise AuditError("invalid level.dat root")
    return storage_version, root


def decode_varint(data: bytes, offset: int):
    value = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise AuditError("truncated varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7


def crc32c(data: bytes):
    polynomial = 0x82F63B78
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ polynomial if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def mask_crc(crc: int):
    return (((crc >> 15) | (crc << 17)) + 0xA282EAD8) & 0xFFFFFFFF


def decode_log(data: bytes, block_size: int = 32768):
    payloads = []
    fragment = None
    bad_records = 0
    for block_start in range(0, len(data), block_size):
        block_end = min(block_start + block_size, len(data))
        offset = block_start
        while offset + 7 <= block_end:
            checksum, length, record_type = struct.unpack("<IHB", data[offset:offset + 7])
            if record_type == 0 or offset + 7 + length > block_end:
                break
            chunk = data[offset + 7:offset + 7 + length]
            actual = mask_crc(crc32c(bytes([record_type]) + chunk))
            if actual != checksum:
                bad_records += 1
            if record_type == 1:
                payloads.append(chunk)
            elif record_type == 2:
                fragment = chunk
            elif record_type == 3:
                fragment = (fragment or b"") + chunk
            elif record_type == 4:
                payloads.append((fragment or b"") + chunk)
                fragment = None
            offset += 7 + length
    if fragment is not None:
        raise AuditError("unfinished fragmented LevelDB record")

    records = []
    for payload in payloads:
        if len(payload) < 12:
            raise AuditError("truncated LevelDB write batch")
        sequence, count = struct.unpack("<QI", payload[:12])
        offset = 12
        for _ in range(count):
            value_type = payload[offset]
            offset += 1
            key_length, offset = decode_varint(payload, offset)
            key = payload[offset:offset + key_length]
            offset += key_length
            if value_type == 0:
                continue
            value_length, offset = decode_varint(payload, offset)
            value = payload[offset:offset + value_length]
            offset += value_length
            records.append((sequence, key, value))
    return records, bad_records


def unpack_nbt_value(value, default=None):
    return value[1] if isinstance(value, tuple) and len(value) == 2 else default


def entity_records(records):
    entities = []
    parse_errors = []
    block_entity_values = 0
    for sequence, key, value in records:
        if len(key) < 9 or key[8] != 0x31:
            continue
        block_entity_values += 1
        offset = 0
        while offset < len(value):
            try:
                tag, _, entity, next_offset = decode_named_tag(value, offset)
            except Exception as error:
                parse_errors.append(f"sequence {sequence}: {error}")
                break
            if tag != TAG_COMPOUND:
                parse_errors.append(f"sequence {sequence}: non-compound block entity")
                break
            entity["__sequence"] = (TAG_LONG, sequence)
            entities.append(entity)
            if next_offset <= offset:
                parse_errors.append(f"sequence {sequence}: parser made no progress")
                break
            offset = next_offset
    return entities, block_entity_values, parse_errors


def collect_strings(value, limit=200):
    strings = []

    def visit(item):
        if len(strings) >= limit:
            return
        if isinstance(item, str):
            if item:
                strings.append(item)
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                visit(key)
                visit(unpack_nbt_value(child))
            return
        if isinstance(item, tuple):
            for child in item:
                visit(unpack_nbt_value(child) if isinstance(child, tuple) else child)

    visit(value)
    return strings


def parse_command_blocks(entities):
    command_blocks = []
    other_entity_types = collections.Counter()
    for entity in entities:
        entity_id = str(unpack_nbt_value(entity.get("id"), ""))
        other_entity_types[entity_id or "<missing>"] += 1
        if entity_id not in {"CommandBlock", "MinecartCommandBlock"}:
            continue
        command = str(unpack_nbt_value(entity.get("Command"), ""))
        position = tuple(
            int(unpack_nbt_value(entity.get(axis), 0))
            for axis in ("x", "y", "z")
        )
        command_blocks.append(
            {
                "sequence": int(unpack_nbt_value(entity.get("__sequence"), -1)),
                "id": entity_id,
                "position": position,
                "command": command,
                "customName": str(unpack_nbt_value(entity.get("CustomName"), "")),
                "auto": bool(unpack_nbt_value(entity.get("auto"), 0)),
                "conditional": bool(unpack_nbt_value(entity.get("conditionalMode"), 0)),
                "delay": int(unpack_nbt_value(entity.get("TickDelay"), 0)),
                "powered": bool(unpack_nbt_value(entity.get("powered"), 0)),
                "lastOutput": str(unpack_nbt_value(entity.get("LastOutput"), "")),
                "version": int(unpack_nbt_value(entity.get("Version"), 0)),
            }
        )
    return command_blocks, other_entity_types


def decode_subchunk_blocks(key: bytes, value: bytes):
    if len(value) < 4 or value[0] != 9:
        raise AuditError(f"unsupported subchunk version {value[0] if value else 'empty'}")
    subchunk_y = struct.unpack("<b", key[9:10])[0]
    bits = value[3] >> 1
    if bits == 0:
        return {}
    blocks_per_word = 32 // bits
    word_count = math.ceil(4096 / blocks_per_word)
    words = struct.unpack("<" + "I" * word_count, value[4:4 + word_count * 4])
    offset = 4 + word_count * 4
    palette_count = struct.unpack("<I", value[offset:offset + 4])[0]
    offset += 4
    palette = []
    for _ in range(palette_count):
        tag, _, descriptor, offset = decode_named_tag(value, offset)
        if tag != TAG_COMPOUND:
            raise AuditError("subchunk palette entry is not a compound")
        palette.append(descriptor)
    chunk_x, chunk_z = struct.unpack("<ii", key[:8])
    blocks = {}
    for x in range(16):
        for z in range(16):
            for y in range(16):
                slot = (x << 8) | (z << 4) | y
                index = (
                    words[slot // blocks_per_word]
                    >> ((slot % blocks_per_word) * bits)
                ) & ((1 << bits) - 1)
                if index >= len(palette):
                    raise AuditError("subchunk palette index out of range")
                world = (chunk_x * 16 + x, subchunk_y * 16 + y, chunk_z * 16 + z)
                blocks[world] = palette[index]
    return blocks


def safe_zip_entries(archive: zipfile.ZipFile):
    result = []
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        pure = Path(name)
        unsafe = pure.is_absolute() or ".." in pure.parts
        result.append(
            {
                "name": name,
                "size": info.file_size,
                "compressed": info.compress_size,
                "unsafe": unsafe,
            }
        )
    return result


def enforce_archive_limits(entries):
    total = sum(entry["size"] for entry in entries)
    oversized = [
        entry["name"] for entry in entries if entry["size"] > MAX_ENTRY_BYTES
    ]
    if oversized:
        raise AuditError(
            "archive contains oversized uncompressed entries: " + ", ".join(oversized)
        )
    if total > MAX_ARCHIVE_BYTES:
        raise AuditError(
            f"archive expands to {total} bytes, above limit {MAX_ARCHIVE_BYTES}"
        )


def find_privacy_signals(commands):
    signals = collections.Counter()
    examples = []
    patterns = {
        "quoted-selector-name": re.compile(r'\b(?:as|name=)\s*"([^"\r\n]{1,64})"'),
        "netease-prefixed-id": re.compile(r"\bnetease:[A-Za-z0-9_.:-]+"),
        "absolute-world-coordinate": re.compile(
            r"\b(?:tp|teleport|setblock|fill|clone|structure)\b[\s\S]{0,120}?"
            r"(?<![~^])-?\d{4,}\s+-?\d+\s+-?\d{4,}"
        ),
    }
    for command in commands:
        for kind, pattern in patterns.items():
            for match in pattern.finditer(command):
                signals[kind] += 1
                if len(examples) < 20:
                    examples.append(
                        {
                            "kind": kind,
                            "match": match.group(0)[:160],
                        }
                    )
    return {"counts": dict(signals), "examples": examples}


def inspect_world(path: Path):
    with zipfile.ZipFile(path) as archive:
        entries = safe_zip_entries(archive)
        enforce_archive_limits(entries)
        names = {entry["name"] for entry in entries}
        if "level.dat" not in names:
            raise AuditError("level.dat is missing")
        level_raw = archive.read("level.dat")
        level_storage, level = decode_level_dat(level_raw)
        levelname = archive.read("levelname.txt").decode("utf-8", "replace") if "levelname.txt" in names else ""
        logs = [name for name in sorted(names) if name.startswith("db/") and name.endswith(".log")]
        table_files = [
            name for name in sorted(names) if name.startswith("db/") and name.endswith(".ldb")
        ]
        all_records = []
        bad_records = 0
        for name in logs:
            records, bad = decode_log(archive.read(name))
            all_records.extend(records)
            bad_records += bad

    if not logs and table_files:
        raise AuditError(
            "the world uses LevelDB .ldb tables but no write-ahead .log; "
            "command-block extraction from table files is unsupported"
        )

    entities, block_entity_values, parse_errors = entity_records(all_records)
    command_blocks, entity_types = parse_command_blocks(entities)
    block_grid = {}
    subchunk_errors = []
    subchunks = 0
    for sequence, key, value in all_records:
        if len(key) < 10 or key[8] != 0x2F:
            continue
        subchunks += 1
        try:
            block_grid.update(decode_subchunk_blocks(key, value))
        except Exception as error:
            subchunk_errors.append(f"sequence {sequence}: {error}")
    for block in command_blocks:
        descriptor = block_grid.get(block["position"], {})
        block["blockType"] = str(unpack_nbt_value(descriptor.get("name"), ""))
    block_type_counts = collections.Counter(
        block["blockType"] or "<unknown>" for block in command_blocks
    )
    key_tags = collections.Counter(key[8] for _, key, _ in all_records if len(key) >= 9)
    commands = [block["command"] for block in command_blocks]
    nonempty_commands = [command for command in commands if command.strip()]
    duplicate_positions = [
        position
        for position, count in collections.Counter(
            block["position"] for block in command_blocks
        ).items()
        if count > 1
    ]
    duplicate_commands = [
        (command, count)
        for command, count in collections.Counter(commands).items()
        if count > 1
    ]
    prefixes = collections.Counter()
    prefix_by_block_type = collections.defaultdict(collections.Counter)
    for block in command_blocks:
        command = block["command"].strip().lstrip("/")
        prefix = command.split(maxsplit=1)[0] if command else "<empty>"
        prefix_by_block_type[block.get("blockType") or "<unknown>"][prefix] += 1
    for command in commands:
        cleaned = command.strip().lstrip("/")
        prefixes[cleaned.split(maxsplit=1)[0] if cleaned else "<empty>"] += 1

    level_fields = {}
    for field in (
        "LevelName",
        "StorageVersion",
        "LastPlayed",
        "SpawnX",
        "SpawnY",
        "SpawnZ",
        "GameType",
        "Generator",
        "commandsEnabled",
        "cheatsEnabled",
        "commandblocksenabled",
        "commandblockoutput",
        "sendcommandfeedback",
        "experiments",
        "educationFeaturesEnabled",
    ):
        if field in level:
            level_fields[field] = unpack_nbt_value(level[field])

    string_candidates = []
    for entity in entities:
        for text in collect_strings(entity):
            if (
                text.startswith("/")
                or " execute " in text
                or text.startswith("execute ")
                or text.startswith("scoreboard ")
                or text.startswith("tellraw ")
                or text.startswith("titleraw ")
            ):
                string_candidates.append(text)

    result = {
        "file": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "fileSize": path.stat().st_size,
        "archive": {
            "entries": entries,
            "unsafePaths": [item["name"] for item in entries if item["unsafe"]],
            "totalUncompressed": sum(item["size"] for item in entries),
        },
        "level": {
            "storageVersion": level_storage,
            "levelname": levelname,
            "fields": level_fields,
            "topLevelKeys": sorted(level.keys()),
        },
        "database": {
            "logFiles": logs,
            "tableFiles": table_files,
            "records": len(all_records),
            "badCrcRecords": bad_records,
            "keyTags": {f"0x{tag:02X}": count for tag, count in sorted(key_tags.items())},
            "blockEntityValues": block_entity_values,
            "subchunks": subchunks,
            "subchunkErrors": subchunk_errors,
            "entitiesParsed": len(entities),
            "entityTypes": dict(entity_types.most_common()),
            "parseErrors": parse_errors,
        },
        "commands": {
            "count": len(commands),
            "nonEmpty": len(nonempty_commands),
            "unique": len(set(commands)),
            "empty": sum(1 for command in commands if not command.strip()),
            "auto": sum(1 for block in command_blocks if block["auto"]),
            "conditional": sum(1 for block in command_blocks if block["conditional"]),
            "delayed": sum(1 for block in command_blocks if block["delay"] > 0),
            "maxDelay": max((block["delay"] for block in command_blocks), default=0),
            "newlineCommands": sum(
                1 for command in commands if "\r" in command or "\n" in command
            ),
            "missingRunSpace": sum(1 for command in commands if "run/" in command),
            "maxLength": max((len(command) for command in commands), default=0),
            "averageLength": (
                round(sum(len(command) for command in commands) / len(commands), 1)
                if commands
                else 0
            ),
            "blockTypes": dict(block_type_counts.most_common()),
            "prefixByBlockType": {
                block_type: dict(counter.most_common())
                for block_type, counter in sorted(prefix_by_block_type.items())
            },
            "duplicatePositions": [list(position) for position in duplicate_positions],
            "duplicateCommands": [
                {"command": command, "count": count}
                for command, count in duplicate_commands
            ],
            "prefixes": dict(prefixes.most_common()),
            "commandBlocks": sorted(
                command_blocks,
                key=lambda block: (
                    block["position"][1],
                    block["position"][0],
                    block["position"][2],
                    block["sequence"],
                ),
            ),
        },
        "otherCommandLikeStrings": list(dict.fromkeys(string_candidates)),
        "privacySignals": find_privacy_signals(commands),
    }
    return result


def markdown_report(results, output: Path):
    lines = [
        "# MCWorld 训练适用性审计",
        "",
        "本报告由只读解包与 NBT/LevelDB 解析生成；未在任何存档中执行命令。",
        "",
    ]
    for result in results:
        level = result["level"]
        command_data = result["commands"]
        database = result["database"]
        lines.extend(
            [
                f"## {Path(result['file']).name}",
                "",
                f"- SHA-256：`{result['sha256']}`",
                f"- 文件大小：{result['fileSize']} bytes",
                f"- 世界名：`{level['levelname']}`",
                f"- LevelDB 日志记录：{database['records']}",
                f"- 方块实体：{database['entitiesParsed']}",
                f"- 命令方块：{command_data['count']}",
                f"- 唯一命令：{command_data['unique']}",
                f"- 空命令：{command_data['empty']}",
                f"- 保持开启（auto）：{command_data['auto']}",
                f"- 有条件：{command_data['conditional']}",
                f"- 延迟大于 0：{command_data['delayed']}",
                f"- `run/` 粘连：{command_data['missingRunSpace']}",
                f"- 最长命令：{command_data['maxLength']} 字符",
                f"- 子区块：{database['subchunks']}",
                f"- 子区块解析异常：{len(database['subchunkErrors'])}",
                f"- 隐私/本地化信号：{len(result['privacySignals']['counts'])} 类",
                f"- 重复坐标：{len(command_data['duplicatePositions'])}",
                f"- 解包越界路径：{len(result['archive']['unsafePaths'])}",
                "",
                "### 关键世界字段",
                "",
                "```json",
                json.dumps(level["fields"], ensure_ascii=False, indent=2, default=str),
                "```",
                "",
                "### 命令首词分布",
                "",
                "| 命令 | 数量 |",
                "| --- | ---: |",
            ]
        )
        for prefix, count in sorted(command_data["prefixes"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| `{prefix}` | {count} |")
        lines.extend(["", "### 方块实体类型", "", "```json"])
        lines.append(json.dumps(database["entityTypes"], ensure_ascii=False, indent=2))
        lines.extend(["```", "", "### 命令方块类型", "", "```json"])
        lines.append(json.dumps(command_data["blockTypes"], ensure_ascii=False, indent=2))
        lines.extend(["```", "", "### 方块类型 × 命令首词", "", "```json"])
        lines.append(
            json.dumps(
                command_data["prefixByBlockType"],
                ensure_ascii=False,
                indent=2,
            )
        )
        lines.extend(["```", "", "### 命令清单", "", "```text"])
        for block in command_data["commandBlocks"]:
            x, y, z = block["position"]
            flags = [
                f"block={block.get('blockType', '')}",
                f"auto={int(block['auto'])}",
                f"conditional={int(block['conditional'])}",
                f"delay={block['delay']}",
                f"version={block['version']}",
            ]
            lines.append(f"[{x} {y} {z}] {block['id']} {' '.join(flags)}")
            lines.append(block["command"].replace("\r", "\\r").replace("\n", "\\n"))
        lines.extend(["```", ""])
        if command_data["duplicateCommands"]:
            lines.extend(["### 重复命令", "", "```json"])
            lines.append(json.dumps(command_data["duplicateCommands"], ensure_ascii=False, indent=2))
            lines.extend(["```", ""])
        if database["parseErrors"]:
            lines.extend(["### 解析异常", "", "```text"])
            lines.extend(database["parseErrors"])
            lines.extend(["```", ""])
        if result["otherCommandLikeStrings"]:
            lines.extend(["### 其他实体中的命令样字符串", "", "```text"])
            lines.extend(result["otherCommandLikeStrings"])
            lines.extend(["```", ""])
        if result["privacySignals"]["counts"]:
            lines.extend(["### 发布前匿名化信号", "", "```json"])
            lines.append(
                json.dumps(
                    result["privacySignals"],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            lines.extend(["```", ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def write_command_corpus(results, directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, result in enumerate(results, start=1):
        stem = f"world-{index}"
        command_path = directory / f"{stem}.commands.txt"
        detail_path = directory / f"{stem}.command-blocks.json"
        blocks = result["commands"]["commandBlocks"]
        command_path.write_text(
            "\n".join(
                block["command"].replace("\r", "\\r").replace("\n", "\\n")
                for block in blocks
                if block["command"].strip()
            ) + "\n",
            encoding="utf-8",
        )
        detail_path.write_text(
            json.dumps(blocks, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest.append(
            {
                "source": Path(result["file"]).name,
                "sha256": result["sha256"],
                "commandFile": command_path.name,
                "detailFile": detail_path.name,
                "commandBlocks": len(blocks),
                "nonEmptyCommands": sum(1 for block in blocks if block["command"].strip()),
            }
        )
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def self_test():
    with tempfile.TemporaryDirectory(prefix="mcworld-audit-") as temporary:
        root = Path(temporary)
        level = {
            "LevelName": (TAG_STRING, "audit-self-test"),
            "StorageVersion": (TAG_INT, 9),
            "commandsEnabled": (TAG_BYTE, 1),
            "cheatsEnabled": (TAG_BYTE, 0),
            "commandblocksenabled": (TAG_BYTE, 1),
        }
        level_body = encode_root_compound(level)
        level_dat = struct.pack("<II", 9, len(level_body)) + level_body

        def command_block(x, command):
            return encode_root_compound(
                {
                    "id": (TAG_STRING, "CommandBlock"),
                    "x": (TAG_INT, x),
                    "y": (TAG_INT, 4),
                    "z": (TAG_INT, 0),
                    "Command": (TAG_STRING, command),
                    "auto": (TAG_BYTE, 1),
                    "conditionalMode": (TAG_BYTE, 0),
                    "TickDelay": (TAG_INT, 0),
                    "Version": (TAG_INT, 39),
                }
            )

        key = struct.pack("<ii", 0, 0) + b"\x31"
        value = command_block(0, "/say self-test") + command_block(
            1, "/execute as @a at @s run tag @s add audit"
        )
        log = encode_log([(1, key, value)])
        archive_path = root / "self-test.mcworld"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("level.dat", level_dat)
            archive.writestr("levelname.txt", "audit-self-test")
            archive.writestr("db/CURRENT", "MANIFEST-000000\n")
            archive.writestr("db/000001.log", log)

        result = inspect_world(archive_path)
        assert result["level"]["levelname"] == "audit-self-test"
        assert result["commands"]["count"] == 2
        assert result["commands"]["nonEmpty"] == 2
        assert result["commands"]["missingRunSpace"] == 0
        assert result["database"]["parseErrors"] == []
        assert result["archive"]["unsafePaths"] == []
    print("self-test passed: .mcworld metadata and command-block decoding")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("worlds", nargs="*", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--commands-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return
    if not args.worlds:
        parser.error("at least one .mcworld is required unless --self-test is used")
    results = [inspect_world(path.resolve()) for path in args.worlds]
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
    if args.markdown:
        markdown_report(results, args.markdown.resolve())
    if args.commands_dir:
        write_command_corpus(results, args.commands_dir.resolve())
    summary = [
        {
            "file": Path(result["file"]).name,
            "levelname": result["level"]["levelname"],
            "entities": result["database"]["entitiesParsed"],
            "commandBlocks": result["commands"]["count"],
            "uniqueCommands": result["commands"]["unique"],
            "duplicates": len(result["commands"]["duplicateCommands"]),
            "prefixes": result["commands"]["prefixes"],
            "parseErrors": len(result["database"]["parseErrors"]),
        }
        for result in results
    ]
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (AuditError, OSError, zipfile.BadZipFile, struct.error) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
