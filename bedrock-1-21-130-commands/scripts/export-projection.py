#!/usr/bin/env python3
"""Export a chain spec as an importable Bedrock world and BDS world folder.

The LevelDB and low-level NBT approach is adapted from
yixin-amore/MinecraftBE-Command-Building-Skill's MIT-licensed
build_cbworld.py, then reduced to this project's pure command-block scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_VALIDATOR = ROOT / "scripts" / "validate-chain-spec.mjs"
DEFAULT_TEMPLATE = ROOT / "assets" / "world-template.level.dat"
PROJECTION_NAME_PREFIX = "指令区"

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

BLOCK_VERSION = 0x01150100
COMMAND_BLOCK_VERSION = 39
BLOCK_TARGET = {b"\x2c": b"\x28", b"\x36": struct.pack("<i", 2)}

FACING_NUMBER = {
    "down": 0,
    "up": 1,
    "north": 2,
    "south": 3,
    "west": 4,
    "east": 5,
}
FACING_DELTA = {
    "down": (0, -1, 0),
    "up": (0, 1, 0),
    "north": (0, 0, -1),
    "south": (0, 0, 1),
    "west": (-1, 0, 0),
    "east": (1, 0, 0),
}


class ExportError(RuntimeError):
    pass


def skill_version() -> str:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else "unknown"


def encode_string(value: str) -> bytes:
    data = value.encode("utf-8")
    if len(data) > 0xFFFF:
        raise ExportError("NBT string exceeds 65535 bytes")
    return struct.pack("<H", len(data)) + data


def encode_payload(tag: int, value) -> bytes:
    if tag == TAG_BYTE:
        return struct.pack("<b", int(value))
    if tag == TAG_SHORT:
        return struct.pack("<h", int(value))
    if tag == TAG_INT:
        return struct.pack("<i", int(value))
    if tag == TAG_LONG:
        return struct.pack("<q", int(value))
    if tag == TAG_FLOAT:
        return struct.pack("<f", float(value))
    if tag == TAG_DOUBLE:
        return struct.pack("<d", float(value))
    if tag == TAG_BYTE_ARRAY:
        data = bytes(value)
        return struct.pack("<i", len(data)) + data
    if tag == TAG_STRING:
        return encode_string(str(value))
    if tag == TAG_INT_ARRAY:
        items = [int(item) for item in value]
        return struct.pack("<i", len(items)) + b"".join(struct.pack("<i", item) for item in items)
    if tag == TAG_LIST:
        element_tag, items = value
        return (
            struct.pack("<bi", int(element_tag), len(items))
            + b"".join(encode_payload(element_tag, item) for item in items)
        )
    if tag == TAG_COMPOUND:
        return encode_compound(value)
    raise ExportError(f"unsupported NBT tag: {tag}")


def encode_compound(values: dict) -> bytes:
    body = bytearray()
    for name, (tag, value) in values.items():
        body.extend(struct.pack("<b", tag))
        body.extend(encode_string(name))
        body.extend(encode_payload(tag, value))
    body.append(0)
    return bytes(body)


def encode_root_compound(value: dict) -> bytes:
    return bytes([TAG_COMPOUND]) + encode_string("") + encode_compound(value)


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
    raise ExportError(f"unsupported NBT tag: {tag}")


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


def decode_level_dat(raw: bytes) -> tuple[int, dict]:
    if raw[:2] == bytes((0x1F, 0x8B)):
        import gzip
        raw = gzip.decompress(raw)
        version = 10
        body = raw
    else:
        version, declared = struct.unpack("<II", raw[:8])
        body = raw[8:8 + declared]
        if len(body) != declared:
            raise ExportError("level.dat length header does not match file size")
    if len(body) < 3 or body[0] != TAG_COMPOUND:
        raise ExportError("level.dat root must be a compound tag")
    tag, _, root, end = decode_named_tag(body, 0)
    if tag != TAG_COMPOUND:
        raise ExportError("level.dat root must be a compound tag")
    if end != len(body):
        raise ExportError("level.dat contains trailing bytes")
    return version, root


def load_template(path: Path) -> tuple[int, dict, str]:
    raw = path.read_bytes()
    if path.suffix.lower() == ".mcworld" or raw[:2] == b"PK":
        with zipfile.ZipFile(path) as archive:
            raw = archive.read("level.dat")
    version, root = decode_level_dat(raw)
    return version, root, hashlib.sha256(raw).hexdigest()


def build_level_dat(template_path: Path, world_name: str, spawn: tuple[int, int, int]) -> tuple[bytes, str]:
    version, root, template_hash = load_template(template_path)
    root["LevelName"] = (TAG_STRING, world_name)
    root["SpawnX"] = (TAG_INT, spawn[0])
    root["SpawnY"] = (TAG_INT, spawn[1])
    root["SpawnZ"] = (TAG_INT, spawn[2])
    root["GameType"] = (TAG_INT, 1)
    root["commandsEnabled"] = (TAG_BYTE, 1)
    root["cheatsEnabled"] = (TAG_BYTE, 1)
    root["commandblocksenabled"] = (TAG_BYTE, 1)
    root["commandblockoutput"] = (TAG_BYTE, 1)
    root["sendcommandfeedback"] = (TAG_BYTE, 1)
    root["showcoordinates"] = (TAG_BYTE, 1)
    root["RandomSeed"] = (TAG_INT, 0)
    root["FlatWorldLayers"] = (TAG_STRING, "")
    body = encode_root_compound(root)
    return struct.pack("<II", version, len(body)) + body, template_hash


def crc32c(data: bytes) -> int:
    polynomial = 0x82F63B78
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ polynomial if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def mask_crc(crc: int) -> int:
    return (((crc >> 15) | (crc << 17)) + 0xA282EAD8) & 0xFFFFFFFF


def encode_varint(value: int) -> bytes:
    output = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        output.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(output)


def decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ExportError("truncated varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7


def encode_log(pairs: list[tuple[int, bytes, bytes]], block_size: int = 32768) -> bytes:
    output = bytearray()

    def emit(body: bytes) -> None:
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
            if last:
                break

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


def decode_log(data: bytes, block_size: int = 32768) -> list[tuple[bytes, bytes]]:
    payloads = []
    fragment = None
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
                raise ExportError("LevelDB log CRC mismatch")
            if record_type == 1:
                payloads.append(chunk)
            elif record_type == 2:
                fragment = chunk
            elif record_type == 3:
                fragment = (fragment or b"") + chunk
            elif record_type == 4:
                payloads.append((fragment or b"") + chunk)
                fragment = None
            else:
                raise ExportError(f"invalid LevelDB record type: {record_type}")
            offset += 7 + length
    if fragment is not None:
        raise ExportError("unfinished LevelDB fragmented record")

    records = []
    for payload in payloads:
        if len(payload) < 12:
            raise ExportError("truncated LevelDB write batch")
        _, count = struct.unpack("<QI", payload[:12])
        offset = 12
        for _ in range(count):
            if offset >= len(payload):
                raise ExportError("truncated LevelDB write batch entry")
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
            records.append((key, value))
        if offset != len(payload):
            raise ExportError("LevelDB write batch contains trailing bytes")
    return records


def encode_manifest(last_sequence: int = 0) -> bytes:
    def record(fields: list[tuple[int, int | None]]) -> bytes:
        payload = bytearray()
        for field, value in fields:
            if field == 1:
                comparator = b"leveldb.BytewiseComparator"
                payload.extend(bytes([field]))
                payload.extend(encode_varint(len(comparator)))
                payload.extend(comparator)
            else:
                payload.extend(bytes([field]))
                payload.extend(encode_varint(int(value)))
        checksum = mask_crc(crc32c(bytes([1]) + bytes(payload)))
        return struct.pack("<IHB", checksum, len(payload), 1) + bytes(payload)

    return (
        record([(1, None), (2, 0), (3, 1), (4, 0)])
        + record([(2, 1), (3, 2), (4, last_sequence)])
    )


def command_block_descriptor(block: dict) -> tuple[tuple, dict]:
    name = {
        "impulse": "minecraft:command_block",
        "repeat": "minecraft:repeating_command_block",
        "chain": "minecraft:chain_command_block",
    }[block["type"]]
    states = (
        ("conditional_bit", (TAG_BYTE, int(block["conditional"]))),
        ("facing_direction", (TAG_INT, FACING_NUMBER[block["facing"]])),
    )
    return (name, states), {"name": name, "states": dict(states)}


def button_descriptor() -> tuple[tuple, dict]:
    states = (
        ("button_pressed_bit", (TAG_BYTE, 0)),
        ("facing_direction", (TAG_INT, 1)),
    )
    return ("minecraft:stone_button", states), {"name": "minecraft:stone_button", "states": dict(states)}


def encode_block_entry(descriptor: dict) -> bytes:
    values = {
        "name": (TAG_STRING, descriptor["name"]),
        "states": (TAG_COMPOUND, descriptor["states"]),
        "version": (TAG_INT, BLOCK_VERSION),
    }
    return encode_root_compound(values)


def encode_subchunk(subchunk_y: int, blocks: dict[tuple[int, int, int], tuple], descriptors: dict) -> bytes:
    air_key = ("minecraft:air", ())
    used = [air_key] + sorted((key for key in set(blocks.values()) if key != air_key), key=repr)
    palette_index = {key: index for index, key in enumerate(used)}
    bits = max(1, math.ceil(math.log2(max(2, len(used)))))
    blocks_per_word = 32 // bits
    words = [0] * math.ceil(4096 / blocks_per_word)
    for (x, y, z), key in blocks.items():
        slot = (x << 8) | (z << 4) | y
        words[slot // blocks_per_word] |= palette_index[key] << ((slot % blocks_per_word) * bits)

    output = bytearray([9, 2, subchunk_y & 0xFF, (bits << 1) | 0])
    output.extend(struct.pack("<" + "I" * len(words), *words))
    output.extend(struct.pack("<I", len(used)))
    for key in used:
        output.extend(encode_block_entry(descriptors.get(key, {"name": key[0], "states": dict(key[1])})))
    output.extend(bytes([0]))
    output.extend(encode_block_entry({"name": "minecraft:air", "states": {}}))
    return bytes(output)


def command_block_entity(block: dict) -> bytes:
    x, y, z = block["pos"]
    values = {
        "id": (TAG_STRING, "CommandBlock"),
        "x": (TAG_INT, x),
        "y": (TAG_INT, y),
        "z": (TAG_INT, z),
        "Command": (TAG_STRING, block["command"]),
        "auto": (TAG_BYTE, int(block["redstone"] == "always_active")),
        "conditionalMode": (TAG_BYTE, int(block["conditional"])),
        "conditionMet": (TAG_BYTE, 1),
        "ExecuteOnFirstTick": (TAG_BYTE, int(block["executeFirstTick"])),
        "powered": (TAG_BYTE, 0),
        "TickDelay": (TAG_INT, block["delay"]),
        "TrackOutput": (TAG_BYTE, 1),
        "LastOutput": (TAG_STRING, ""),
        "LastOutputParams": (TAG_LIST, (TAG_STRING, [])),
        "LastExecution": (TAG_LONG, 0),
        "SuccessCount": (TAG_INT, 0),
        "CustomName": (TAG_STRING, block["id"]),
        "LPCommandMode": (TAG_BYTE, 0),
        "LPCondionalMode": (TAG_BYTE, 0),
        "LPRedstoneMode": (TAG_BYTE, 0),
        "Version": (TAG_INT, COMMAND_BLOCK_VERSION),
        "isMovable": (TAG_BYTE, 1),
    }
    return encode_root_compound(values)


def decode_subchunk_blocks(key: bytes, value: bytes) -> dict[tuple[int, int, int], tuple]:
    if len(value) < 4 or value[0] != 9 or value[1] < 1:
        raise ExportError("unsupported subchunk encoding")
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
            raise ExportError("subchunk palette entry is not a compound")
        palette.append(descriptor)
    chunk_x, chunk_z = struct.unpack("<ii", key[:8])
    blocks = {}
    for x in range(16):
        for z in range(16):
            for y in range(16):
                slot = (x << 8) | (z << 4) | y
                index = (words[slot // blocks_per_word] >> ((slot % blocks_per_word) * bits)) & ((1 << bits) - 1)
                if index >= len(palette):
                    raise ExportError("subchunk palette index out of range")
                world = (chunk_x * 16 + x, subchunk_y * 16 + y, chunk_z * 16 + z)
                blocks[world] = palette[index]
    return blocks


def verify_world_files(files: dict[str, bytes], blocks: list[dict], buttons: list[tuple[int, int, int]]) -> None:
    _, level = decode_level_dat(files["level.dat"])
    if level.get("commandsEnabled", (0, 0))[1] != 1:
        raise ExportError("generated level.dat does not enable commands")
    if level.get("cheatsEnabled", (0, 0))[1] != 1:
        raise ExportError("generated level.dat does not enable cheats")

    block_grid = {}
    entities = {}
    for key, value in decode_log(files["db/000001.log"]):
        if len(key) < 9:
            continue
        key_tag = key[8]
        if key_tag == 0x2F:
            block_grid.update(decode_subchunk_blocks(key, value))
        elif key_tag == 0x31:
            offset = 0
            while offset < len(value):
                tag, _, entity, offset = decode_named_tag(value, offset)
                if tag != TAG_COMPOUND:
                    raise ExportError("block entity record is not a compound")
                if entity.get("id", (0, ""))[1] == "CommandBlock":
                    position = tuple(entity[axis][1] for axis in ("x", "y", "z"))
                    if position in entities:
                        raise ExportError(f"duplicate command block entity at {position}")
                    entities[position] = entity

    if len(entities) != len(blocks):
        raise ExportError(f"command block entity count mismatch: {len(entities)} != {len(blocks)}")
    for block in blocks:
        position = block["pos"]
        descriptor = block_grid.get(position)
        if not descriptor:
            raise ExportError(f"missing command block at {position}")
        expected_name = command_block_descriptor(block)[1]["name"]
        if descriptor.get("name", (0, ""))[1] != expected_name:
            raise ExportError(f"wrong block type at {position}")
        states = descriptor.get("states", (0, {}))[1]
        if states.get("facing_direction", (0, -1))[1] != FACING_NUMBER[block["facing"]]:
            raise ExportError(f"wrong facing at {position}")
        if states.get("conditional_bit", (0, -1))[1] != int(block["conditional"]):
            raise ExportError(f"wrong conditional state at {position}")
        entity = entities[position]
        checks = {
            "Command": block["command"],
            "auto": int(block["redstone"] == "always_active"),
            "conditionalMode": int(block["conditional"]),
            "ExecuteOnFirstTick": int(block["executeFirstTick"]),
            "TickDelay": block["delay"],
        }
        for field, expected in checks.items():
            actual = entity.get(field, (0, None))[1]
            if actual != expected:
                raise ExportError(f"{block['id']} has wrong {field}: {actual!r} != {expected!r}")

    for position in buttons:
        descriptor = block_grid.get(position)
        if not descriptor or descriptor.get("name", (0, ""))[1] != "minecraft:stone_button":
            raise ExportError(f"missing button at {position}")


def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as failure:
        raise ExportError(f"cannot parse spec JSON: {failure}") from failure
    if not isinstance(spec, dict) or not isinstance(spec.get("blocks"), list):
        raise ExportError("spec must contain a blocks array")
    return spec


def validate_spec(spec_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        raise ExportError("Node.js is required for chain-spec validation")
    if not SPEC_VALIDATOR.exists():
        raise ExportError(f"missing validator: {SPEC_VALIDATOR}")
    result = subprocess.run(
        [node, str(SPEC_VALIDATOR), str(spec_path), "--quiet"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        details = (result.stdout + result.stderr).strip()
        raise ExportError(f"chain spec validation failed\n{details}")


def normalized_blocks(spec: dict) -> list[dict]:
    blocks = []
    for item in spec["blocks"]:
        block = dict(item)
        block["id"] = str(block["id"])
        block["type"] = str(block["type"])
        block["command"] = str(block["command"]).strip().lstrip("/")
        block["conditional"] = block.get("condition", "unconditional") == "conditional"
        block["redstone"] = block.get("redstone") or (
            "always_active" if block["type"] == "chain" else "needs_redstone"
        )
        block["delay"] = int(block.get("delay", 0))
        block["executeFirstTick"] = bool(block.get("executeFirstTick", False))
        block["pos"] = list(block["pos"]) if block.get("pos") is not None else None
        block["facing"] = block.get("facing")
        block["note"] = str(block.get("note", ""))
        blocks.append(block)
    return blocks


def ordered_blocks(blocks: list[dict]) -> list[dict]:
    by_id = {block["id"]: block for block in blocks}
    incoming = {block["id"]: 0 for block in blocks}
    for block in blocks:
        next_id = block.get("next")
        if next_id in by_id:
            incoming[next_id] += 1
    roots = [block for block in blocks if incoming[block["id"]] == 0]
    result = []
    seen = set()
    for root in roots + blocks:
        current = root
        while current and current["id"] not in seen:
            seen.add(current["id"])
            result.append(current)
            next_id = current.get("next")
            current = by_id.get(next_id)
    return result


def apply_automatic_layout(blocks: list[dict], origin: tuple[int, int, int], axis: str, layout: str, width: int) -> None:
    ordered = ordered_blocks(blocks)
    for index, block in enumerate(ordered):
        if layout == "line":
            x = origin[0] + (index if axis == "x" else 0)
            z = origin[2] + (index if axis == "z" else 0)
            y = origin[1]
        else:
            row = index // width
            column = index % width
            forward = row % 2 == 0
            travel = column if forward else width - 1 - column
            x = origin[0] + (travel if axis == "x" else row)
            z = origin[2] + (travel if axis == "z" else row)
            y = origin[1]
        block["pos"] = [x, y, z]
    for block in blocks:
        next_block = next((candidate for candidate in blocks if candidate["id"] == block.get("next")), None)
        block["facing"] = block.get("facing") or (
            delta_to_facing(tuple(next_block["pos"][i] - block["pos"][i] for i in range(3)))
            if next_block else "up"
        )


def delta_to_facing(delta: tuple[int, int, int]) -> str:
    for facing, expected in FACING_DELTA.items():
        if delta == expected:
            return facing
    raise ExportError(f"next command block is not adjacent: delta={delta}")


def prepare_positions(blocks: list[dict], projection: dict, args) -> None:
    explicit = [block["pos"] is not None for block in blocks]
    if any(explicit) and not all(explicit):
        raise ExportError("all blocks must have pos when any block uses explicit coordinates")
    if not any(explicit):
        origin = tuple(args.origin or projection.get("origin", [0, 4, 0]))
        axis = args.axis or projection.get("axis", "x")
        layout = args.layout or projection.get("layout", "serpentine")
        width = int(args.width or projection.get("width", 64))
        if axis not in ("x", "z") or layout not in ("line", "serpentine"):
            raise ExportError("projection axis/layout is invalid")
        if width < 1 or width > 512:
            raise ExportError("projection width must be 1..512")
        apply_automatic_layout(blocks, origin, axis, layout, width)

    by_id = {block["id"]: block for block in blocks}
    for block in blocks:
        if not isinstance(block["pos"], list) or len(block["pos"]) != 3:
            raise ExportError(f"{block['id']}: pos must be three integers")
        block["pos"] = tuple(int(value) for value in block["pos"])
        next_block = by_id.get(block.get("next"))
        if next_block:
            expected = delta_to_facing(tuple(next_block["pos"][i] - block["pos"][i] for i in range(3)))
            block["facing"] = block.get("facing") or expected
            if block["facing"] != expected:
                raise ExportError(
                    f"{block['id']}: facing={block['facing']} but next block is toward {expected}"
                )
        else:
            block["facing"] = block.get("facing") or "up"
        if block["facing"] not in FACING_NUMBER:
            raise ExportError(f"{block['id']}: unsupported facing {block['facing']}")


def bounds(points: list[tuple[int, int, int]]) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    if not points:
        raise ExportError("projection contains no command blocks")
    start = tuple(min(point[index] for point in points) for index in range(3))
    end = tuple(max(point[index] for point in points) for index in range(3))
    size = tuple(end[index] - start[index] + 1 for index in range(3))
    return start, end, size


def projection_archive_name(
    start: tuple[int, int, int], end: tuple[int, int, int]
) -> str:
    return (
        f"{PROJECTION_NAME_PREFIX}@[{','.join(map(str, start))}]"
        f"~[{','.join(map(str, end))}]"
    )


def build_world_files(
    spec: dict,
    blocks: list[dict],
    buttons: list[tuple[int, int, int]],
    template_path: Path,
    world_name: str,
    spawn: tuple[int, int, int],
    projection: dict,
) -> tuple[dict[str, bytes], dict]:
    command_start, command_end, command_size = bounds([block["pos"] for block in blocks])
    visual_points = [block["pos"] for block in blocks] + buttons
    visual_start, visual_end, visual_size = bounds(visual_points)
    archive_name = projection_archive_name(command_start, command_end)
    level_name = (
        f"{world_name} | start {command_start[0]} {command_start[1]} {command_start[2]} "
        f"| end {command_end[0]} {command_end[1]} {command_end[2]}"
    )
    level_dat, template_hash = build_level_dat(template_path, level_name, spawn)

    descriptors = {}
    block_keys = {}
    for block in blocks:
        key, descriptor = command_block_descriptor(block)
        descriptors[key] = descriptor
        block_keys[block["pos"]] = key
    for position in buttons:
        key, descriptor = button_descriptor()
        descriptors[key] = descriptor
        block_keys[position] = key

    commands_by_position = {block["pos"]: block for block in blocks}
    chunks: dict[tuple[int, int], dict] = {}
    for (x, y, z), key in block_keys.items():
        chunk = chunks.setdefault((x // 16, z // 16), {"blocks": {}, "entities": []})
        subchunk = chunk["blocks"].setdefault(y // 16, {})
        subchunk[(x % 16, y % 16, z % 16)] = key
        if (x, y, z) in commands_by_position:
            chunk["entities"].append(command_block_entity(commands_by_position[(x, y, z)]))

    pairs = []
    sequence = 0
    for (chunk_x, chunk_z) in sorted(chunks):
        chunk = chunks[(chunk_x, chunk_z)]
        chunk_key = struct.pack("<ii", chunk_x, chunk_z)
        for tag, value in BLOCK_TARGET.items():
            sequence += 1
            pairs.append((sequence, chunk_key + tag, value))
        pairs.append((sequence + 1, chunk_key + b"\x2b", b"\x00" * 632))
        sequence += 1
        for subchunk_y, subchunk in sorted(chunk["blocks"].items()):
            sequence += 1
            pairs.append(
                (sequence, chunk_key + b"\x2f" + struct.pack("<b", subchunk_y),
                 encode_subchunk(subchunk_y, subchunk, descriptors))
            )
        if chunk["entities"]:
            sequence += 1
            pairs.append((sequence, chunk_key + b"\x31", b"".join(chunk["entities"])))

    manifest = {
        "schemaVersion": 1,
        "format": "bedrock-command-projection",
        "name": spec["name"],
        "description": spec.get("description", ""),
        "skillVersion": skill_version(),
        "target": {
            "channel": spec.get("channel", "netease-china"),
            "edition": "bedrock",
            "version": spec.get("targetVersion", "1.21.130"),
            "dimension": "overworld",
        },
        "coordinateSystem": {
            "units": "blocks",
            "axes": {"x": "east", "y": "up", "z": "south"},
        },
        "bounds": {
            "start": list(command_start),
            "end": list(command_end),
            "size": list(command_size),
            "visualStart": list(visual_start),
            "visualEnd": list(visual_end),
            "visualSize": list(visual_size),
        },
        "spawn": list(spawn),
        "archiveName": archive_name,
        "chainRoots": [block["id"] for block in blocks if block["type"] in ("impulse", "repeat")],
        "blocks": [
            {
                "id": block["id"],
                "type": block["type"],
                "pos": list(block["pos"]),
                "facing": block["facing"],
                "condition": "conditional" if block["conditional"] else "unconditional",
                "redstone": block["redstone"],
                "delay": block["delay"],
                "executeFirstTick": block["executeFirstTick"],
                "command": block["command"],
                "next": block.get("next"),
                "note": block["note"],
            }
            for block in blocks
        ],
        "buttons": [list(position) for position in buttons],
        "setup": spec.get("setup", []),
        "tests": spec.get("tests", []),
        "notes": spec.get("notes", []),
        "template": {
            "sha256": template_hash,
            "note": "Sanitized NetEase-compatible level.dat template; world chunks and command blocks are generated.",
        },
        "import": {
            "mcworld": "Open/import the .mcworld archive in Minecraft Bedrock.",
            "bds": "Copy the matching BDS folder into worlds/<server-world-name>/.",
        },
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    commands_text = "\n".join(
        [f"# setup: /{command.lstrip('/')}" for command in spec.get("setup", [])]
        + [
            f"# {block['id']} [{block['type']} {block['pos']} {block['facing']}] /{block['command']}"
            for block in blocks
        ]
    ) + "\n"
    placement = (
        f"Command projection: {spec['name']}\n"
        f"Start: {command_start[0]} {command_start[1]} {command_start[2]}\n"
        f"End: {command_end[0]} {command_end[1]} {command_end[2]}\n"
        f"Size: {command_size[0]} x {command_size[1]} x {command_size[2]}\n"
        f"Spawn: {spawn[0]} {spawn[1]} {spawn[2]}\n\n"
        "MCWorld: import the matching .mcworld archive.\n"
        "BDS: copy the matching BDS folder into worlds/<world-name>/.\n"
    ).encode("utf-8")

    files = {
        "level.dat": level_dat,
        "levelname.txt": level_name.encode("utf-8"),
        "world_behavior_packs.json": b"[]\n",
        "world_resource_packs.json": b"[]\n",
        "db/CURRENT": b"MANIFEST-000000\n",
        "db/LOCK": b"",
        "db/LOG": b"",
        "db/MANIFEST-000000": encode_manifest(sequence),
        "db/000001.log": encode_log(pairs),
        "projection.json": manifest_bytes,
        "PROJECTION.txt": placement,
        "commands.txt": commands_text.encode("utf-8"),
    }
    verify_world_files(files, blocks, buttons)
    return files, manifest


def write_archive(path: Path, files: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            archive.writestr(name, files[name])


def write_directory(path: Path, files: dict[str, bytes], force: bool) -> None:
    path = path.resolve()
    if path.exists():
        if not force:
            raise ExportError(f"output directory already exists: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True)
    for name, data in files.items():
        target = (path / name).resolve()
        if path not in target.parents and target != path:
            raise ExportError(f"unsafe archive path: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def write_sidecars(outdir: Path, block_manifest: dict, world_files: dict[str, bytes], force: bool) -> dict[str, str]:
    archive_name = block_manifest["archiveName"]
    sidecars = {
        "manifest": outdir / f"{archive_name}.projection.json",
        "commands": outdir / f"{archive_name}.commands.txt",
        "placement": outdir / f"{archive_name}.placement.txt",
    }
    for kind, path in sidecars.items():
        if path.exists() and not force:
            raise ExportError(f"output file already exists: {path}")
        if kind == "manifest":
            path.write_text(json.dumps(block_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            path.write_bytes(world_files["commands.txt" if kind == "commands" else "PROJECTION.txt"])
    return {kind: str(path) for kind, path in sidecars.items()}


def export_projection(spec_path: Path, outdir: Path, args) -> dict:
    if not args.no_validate:
        validate_spec(spec_path)
    spec = load_spec(spec_path)
    projection = spec.get("projection") or {}
    blocks = normalized_blocks(spec)
    prepare_positions(blocks, projection, args)
    command_positions = {block["pos"] for block in blocks}
    by_id = {block["id"]: block for block in blocks}
    incoming = {block["id"]: 0 for block in blocks}
    for block in blocks:
        if block.get("next") in by_id:
            incoming[block["next"]] += 1
    roots = [block for block in blocks if incoming[block["id"]] == 0]

    include_buttons = not args.no_buttons and bool(projection.get("buttons", True))
    buttons = []
    if include_buttons:
        for root in roots:
            if root["redstone"] == "needs_redstone":
                candidate = (root["pos"][0], root["pos"][1] + 1, root["pos"][2])
                if candidate not in command_positions and candidate not in buttons:
                    buttons.append(candidate)

    command_start, _, _ = bounds([block["pos"] for block in blocks])
    default_spawn = (command_start[0] + 2, command_start[1] + 2, command_start[2])
    spawn = tuple(args.spawn or projection.get("spawn", default_spawn))
    world_name = args.world_name or projection.get("worldName") or spec["name"]
    world_clean = re.sub(r"[\r\n\x00-\x1f]", " ", str(world_name)).strip() or spec["name"]

    template_path = Path(args.template).resolve() if args.template else DEFAULT_TEMPLATE
    if not template_path.exists():
        raise ExportError(f"world template does not exist: {template_path}")

    world_files, manifest = build_world_files(
        spec, blocks, buttons, template_path, world_clean, spawn, projection
    )
    outdir.mkdir(parents=True, exist_ok=True)
    formats = [item.strip() for item in args.formats.split(",") if item.strip()]
    if "all" in formats:
        formats = ["mcworld", "bds"]
    invalid = sorted(set(formats) - {"mcworld", "bds"})
    if invalid:
        raise ExportError(f"unsupported formats: {', '.join(invalid)}")

    stem = manifest["archiveName"]
    archive_path = outdir / f"{stem}.mcworld"
    bds_path = outdir / "bds" / stem
    sidecar_paths = [
        outdir / f"{stem}.projection.json",
        outdir / f"{stem}.commands.txt",
        outdir / f"{stem}.placement.txt",
        outdir / f"{stem}.SHA256SUMS.txt",
    ]
    conflicts = [path for path in sidecar_paths if path.exists()]
    if "mcworld" in formats and archive_path.exists():
        conflicts.append(archive_path)
    if "bds" in formats and bds_path.exists():
        conflicts.append(bds_path)
    if conflicts and not args.force:
        raise ExportError(f"output already exists: {conflicts[0]}")

    outputs = {}
    if "mcworld" in formats:
        write_archive(archive_path, world_files)
        outputs["mcworld"] = str(archive_path)
    if "bds" in formats:
        write_directory(bds_path, world_files, args.force)
        outputs["bds"] = str(bds_path)

    outputs.update(write_sidecars(outdir, manifest, world_files, args.force))
    checksum_lines = []
    for kind, path_text in outputs.items():
        path = Path(path_text)
        if kind in ("manifest", "commands", "placement") or path.is_file():
            checksum_lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    checksum_path = outdir / f"{stem}.SHA256SUMS.txt"
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    outputs["checksums"] = str(checksum_path)
    return {
        "name": spec["name"],
        "start": manifest["bounds"]["start"],
        "end": manifest["bounds"]["end"],
        "size": manifest["bounds"]["size"],
        "blocks": len(blocks),
        "buttons": len(buttons),
        "formats": formats,
        "outputs": outputs,
    }


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="bedrock-export-") as temporary:
        sample_name = projection_archive_name(
            (1000000, -61, 1000000), (1000063, -50, 1000063)
        )
        if sample_name != "指令区@[1000000,-61,1000000]~[1000063,-50,1000063]":
            raise ExportError("self-test projection name does not match the required example")
        root = Path(temporary)
        spec_path = root / "spec.json"
        spec = {
            "name": "export-self-test",
            "channel": "netease-china",
            "targetVersion": "1.21.130",
            "commandsOnly": True,
            "projection": {"origin": [0, 4, 0], "layout": "serpentine", "axis": "x", "width": 2},
            "blocks": [
                {
                    "id": "B1",
                    "type": "impulse",
                    "condition": "unconditional",
                    "redstone": "needs_redstone",
                    "command": "say first",
                    "next": "B2",
                },
                {
                    "id": "B2",
                    "type": "chain",
                    "condition": "unconditional",
                    "redstone": "always_active",
                    "command": "say second",
                    "next": "B3",
                },
                {
                    "id": "B3",
                    "type": "chain",
                    "condition": "unconditional",
                    "redstone": "always_active",
                    "command": "say third",
                    "next": None,
                },
            ],
            "setup": [],
            "tests": ["run both commands"],
            "notes": [],
        }
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        args = argparse.Namespace(
            no_validate=False,
            origin=None,
            axis=None,
            layout=None,
            width=None,
            no_buttons=False,
            spawn=None,
            world_name=None,
            template=None,
            formats="mcworld,bds",
            force=False,
        )
        result = export_projection(spec_path, root / "out", args)
        archive_path = Path(result["outputs"]["mcworld"])
        bds_path = Path(result["outputs"]["bds"])
        expected_stem = "指令区@[0,4,0]~[1,4,1]"
        if archive_path.name != f"{expected_stem}.mcworld":
            raise ExportError("self-test archive filename does not match the required coordinate format")
        if bds_path.name != expected_stem:
            raise ExportError("self-test BDS folder name does not match the archive stem")
        sidecar_names = {
            Path(result["outputs"]["manifest"]).name,
            Path(result["outputs"]["commands"]).name,
            Path(result["outputs"]["placement"]).name,
            Path(result["outputs"]["checksums"]).name,
        }
        if sidecar_names != {
            f"{expected_stem}.projection.json",
            f"{expected_stem}.commands.txt",
            f"{expected_stem}.placement.txt",
            f"{expected_stem}.SHA256SUMS.txt",
        }:
            raise ExportError("self-test sidecar names do not share the required archive stem")
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            required = {
                "level.dat",
                "levelname.txt",
                "db/CURRENT",
                "db/MANIFEST-000000",
                "db/000001.log",
                "projection.json",
            }
            if not required.issubset(names):
                raise ExportError("self-test archive is missing required files")
            manifest = json.loads(archive.read("projection.json"))
            if manifest["archiveName"] != expected_stem:
                raise ExportError("self-test manifest archiveName does not match the required stem")
            level_name = archive.read("levelname.txt").decode("utf-8")
            if "start 0 4 0" not in level_name or "end 1 4 1" not in level_name:
                raise ExportError("self-test level name is missing bounds")
            if archive.read("db/000001.log").count(b"CommandBlock") != 3:
                raise ExportError("self-test command-block NBT count mismatch")
            if manifest["bounds"]["start"] != [0, 4, 0] or manifest["bounds"]["end"] != [1, 4, 1]:
                raise ExportError("self-test bounds mismatch")
            for name in archive.namelist():
                bds_file = bds_path / name
                if not bds_file.is_file() or bds_file.read_bytes() != archive.read(name):
                    raise ExportError(f"self-test BDS/archive mismatch: {name}")
        if not (bds_path / "level.dat").exists() or not (bds_path / "db" / "000001.log").exists():
            raise ExportError("self-test BDS folder is incomplete")
    print("self-test passed: chain spec -> MCWorld + BDS folder + coordinate manifest")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a pure command-block chain spec as .mcworld and/or a BDS world folder."
    )
    parser.add_argument("spec", nargs="?", help="chain-spec JSON")
    parser.add_argument("--outdir", help="output directory")
    parser.add_argument("--formats", default="mcworld,bds", help="mcworld,bds,all")
    parser.add_argument("--origin", nargs=3, type=int, help="first command-block X Y Z")
    parser.add_argument("--axis", choices=("x", "z"))
    parser.add_argument("--layout", choices=("line", "serpentine"))
    parser.add_argument("--width", type=int, help="serpentine row width")
    parser.add_argument("--world-name")
    parser.add_argument("--spawn", nargs=3, type=int)
    parser.add_argument("--template", help="sanitized level.dat or .mcworld template")
    parser.add_argument("--no-buttons", action="store_true", help="do not add activator buttons")
    parser.add_argument("--no-validate", action="store_true", help="skip chain-spec validation")
    parser.add_argument("--force", action="store_true", help="overwrite generated outputs")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.self_test:
        return self_test()
    if not args.spec or not args.outdir:
        raise ExportError("spec and --outdir are required unless --self-test is used")
    result = export_projection(Path(args.spec).resolve(), Path(args.outdir).resolve(), args)
    if not args.quiet:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExportError as failure:
        print(f"error: {failure}", file=sys.stderr)
        raise SystemExit(1)
