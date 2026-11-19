#!/usr/bin/env python3
"""Read-only audit for NetEase .building zlib JSON structures."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import tempfile
import urllib.parse
import zlib
from pathlib import Path


MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_JSON_BYTES = 1024 * 1024 * 1024
STRING_FIELD = r'"((?:\\.|[^"])*)"'
COMMAND_BLOCK_RE = re.compile(
    r'name\s*:\s*"(minecraft:(?:chain|repeating|command)_command_block)"',
    re.IGNORECASE,
)


def decompress_limited(raw: bytes):
    decompressor = zlib.decompressobj()
    output = decompressor.decompress(raw, MAX_JSON_BYTES + 1)
    if len(output) > MAX_JSON_BYTES or decompressor.unconsumed_tail:
        raise ValueError("building JSON exceeds decompression safety limit")
    remaining = MAX_JSON_BYTES + 1 - len(output)
    output += decompressor.flush(remaining)
    if len(output) > MAX_JSON_BYTES:
        raise ValueError("building JSON exceeds decompression safety limit")
    return output


def string_field(text: str, name: str, default=""):
    match = re.search(
        rf"(?:^|[,{{])\s*{re.escape(name)}\s*:\s*{STRING_FIELD}",
        text,
    )
    if not match:
        return default
    try:
        return json.loads('"' + match.group(1) + '"')
    except json.JSONDecodeError:
        return match.group(1)


def int_field(text: str, name: str, default=0):
    match = re.search(
        rf"(?:^|[,{{])\s*{re.escape(name)}\s*:\s*(-?\d+)",
        text,
    )
    return int(match.group(1)) if match else default


def bool_field(text: str, name: str):
    match = re.search(
        rf"(?:^|[,{{])\s*{re.escape(name)}\s*:\s*([01])(?:b)?",
        text,
        re.IGNORECASE,
    )
    return bool(int(match.group(1))) if match else False


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)


def decode_wrapper(value: str):
    decoded = urllib.parse.unquote(value.strip())
    try:
        parsed = json.loads(decoded)
        if isinstance(parsed, dict):
            return parsed, decoded
    except json.JSONDecodeError:
        pass
    return {}, decoded


def parse_command_blocks(payload):
    command_blocks = []
    seen = set()
    for value in iter_strings(payload):
        wrapper, decoded = decode_wrapper(value)
        complete_nbt = str(wrapper.get("blockCompleteNBT", ""))
        block_nbt = str(wrapper.get("blockNBT", ""))
        if not complete_nbt and "Command:" in decoded and "id:" in decoded:
            complete_nbt = decoded
            block_nbt = decoded
        if "Command:" not in complete_nbt:
            continue
        if 'id:"CommandBlock"' not in complete_nbt:
            continue

        command = string_field(complete_nbt, "Command")
        x = int_field(complete_nbt, "x")
        y = int_field(complete_nbt, "y")
        z = int_field(complete_nbt, "z")
        key = (x, y, z, command)
        if key in seen:
            continue
        seen.add(key)

        mode_match = COMMAND_BLOCK_RE.search(block_nbt or decoded)
        command_blocks.append(
            {
                "id": "CommandBlock",
                "position": [x, y, z],
                "command": command,
                "customName": string_field(complete_nbt, "CustomName"),
                "blockType": (
                    mode_match.group(1)
                    if mode_match
                    else "minecraft:command_block"
                ),
                "auto": bool_field(complete_nbt, "auto"),
                "conditional": bool_field(complete_nbt, "LPCondionalMode"),
                "delay": int_field(complete_nbt, "TickDelay"),
                "executeOnFirstTick": bool_field(
                    complete_nbt, "ExecuteOnFirstTick"
                ),
                "trackOutput": bool_field(complete_nbt, "TrackOutput"),
                "version": int_field(complete_nbt, "Version"),
            }
        )
    command_blocks.sort(key=lambda item: (*item["position"], item["command"]))
    return command_blocks


def find_privacy_signals(commands):
    signals = collections.Counter()
    patterns = {
        "absolute-coordinate": re.compile(
            r"\b(?:tp|teleport|setblock|fill|clone|structure)\b"
            r"[\s\S]{0,120}?(?<![~^])-?\d{4,}\s+-?\d+\s+-?\d{4,}"
        ),
        "netease-prefixed-id": re.compile(r"\bnetease:[A-Za-z0-9_.:-]+"),
        "quoted-selector-name": re.compile(
            r'\b(?:as|name=)\s*"([^"\r\n]{1,64})"'
        ),
    }
    for command in commands:
        for kind, pattern in patterns.items():
            signals[kind] += sum(1 for _ in pattern.finditer(command))
    return dict(signals)


def inspect_file(path: Path):
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("building file exceeds input safety limit")
    raw = path.read_bytes()
    decoded = decompress_limited(raw)
    payload = json.loads(decoded)
    command_blocks = parse_command_blocks(payload)
    commands = [item["command"] for item in command_blocks]
    nonempty = [command for command in commands if command.strip()]
    normalized = collections.Counter(
        command.strip().lstrip("/") for command in nonempty
    )
    return {
        "file": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "fileSize": len(raw),
        "jsonBytes": len(decoded),
        "commands": {
            "count": len(command_blocks),
            "nonEmpty": len(nonempty),
            "empty": len(command_blocks) - len(nonempty),
            "unique": len(set(commands)),
            "uniqueNonEmpty": len(set(nonempty)),
            "duplicateSlots": len(nonempty) - len(set(nonempty)),
            "delayed": sum(item["delay"] > 0 for item in command_blocks),
            "conditional": sum(item["conditional"] for item in command_blocks),
            "auto": sum(item["auto"] for item in command_blocks),
            "blockTypes": dict(
                collections.Counter(
                    item["blockType"] for item in command_blocks
                )
            ),
            "prefixes": dict(
                collections.Counter(
                    (
                        command.strip().lstrip("/").split(maxsplit=1)[0]
                        if command.strip()
                        else "<empty>"
                    )
                    for command in commands
                )
            ),
            "topDuplicateCommands": [
                {"command": command, "count": count}
                for command, count in normalized.most_common(20)
                if count > 1
            ],
            "commandBlocks": command_blocks,
        },
        "privacySignals": find_privacy_signals(commands),
    }


def markdown_report(result, output: Path):
    commands = result["commands"]
    lines = [
        "# `.building` 语料审计",
        "",
        f"- SHA-256：`{result['sha256']}`",
        f"- 文件大小：{result['fileSize']} bytes",
        f"- 解压 JSON：{result['jsonBytes']} bytes",
        f"- 命令方块：{commands['count']}",
        f"- 非空 / 空：{commands['nonEmpty']} / {commands['empty']}",
        f"- 唯一非空：{commands['uniqueNonEmpty']}",
        f"- 重复槽位：{commands['duplicateSlots']}",
        f"- 延迟 / 条件 / 保持开启：{commands['delayed']} / "
        f"{commands['conditional']} / {commands['auto']}",
        "",
        "## 命令首词",
        "",
        "| 命令 | 数量 |",
        "| --- | ---: |",
    ]
    for prefix, count in sorted(
        commands["prefixes"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"| `{prefix}` | {count} |")
    lines.extend(["", "## 命令清单", "", "```text"])
    for block in commands["commandBlocks"]:
        x, y, z = block["position"]
        lines.append(
            f"[{x} {y} {z}] "
            f"block={block['blockType']} "
            f"auto={int(block['auto'])} "
            f"conditional={int(block['conditional'])} "
            f"delay={block['delay']}"
        )
        lines.append(
            block["command"].replace("\r", "\\r").replace("\n", "\\n")
        )
    lines.extend(["```", ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def write_commands(results, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, result in enumerate(results, start=1):
        path = output_dir / f"building-{index}.commands.txt"
        path.write_text(
            "\n".join(
                item["command"].replace("\r", "\\r").replace("\n", "\\n")
                for item in result["commands"]["commandBlocks"]
                if item["command"].strip()
            )
            + "\n",
            encoding="utf-8",
        )


def self_test():
    with tempfile.TemporaryDirectory(prefix="building-audit-") as temporary:
        path = Path(temporary) / "sample.building"
        block_nbt = (
            '{name:"minecraft:repeating_command_block",'
            "states:{conditional_bit:0b,facing_direction:0},"
            "version:18100737}"
        )
        complete_nbt = (
            '{Command:"/say hello",CustomName:"",'
            "ExecuteOnFirstTick:1b,LPCommandMode:0,LPCondionalMode:0b,"
            "TickDelay:20,TrackOutput:0b,Version:36,auto:1b,"
            'id:"CommandBlock",powered:0b,x:1,y:2,z:3}'
        )
        wrapper = json.dumps(
            {
                "blockNBT": block_nbt,
                "blockCompleteNBT": complete_nbt,
            },
            ensure_ascii=False,
        )
        payload = {"chunkedBlocks": [{"blocks": [[1, 2, 3, 0, 0, wrapper]]}]}
        path.write_bytes(zlib.compress(json.dumps(payload).encode("utf-8")))
        result = inspect_file(path)
        assert result["commands"]["count"] == 1
        assert result["commands"]["nonEmpty"] == 1
        assert result["commands"]["delayed"] == 1
        assert result["commands"]["auto"] == 1
        assert result["commands"]["commandBlocks"][0]["command"] == "/say hello"
    print("self-test passed: .building zlib JSON and command SNBT decoding")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--commands-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return
    if not args.files:
        parser.error("at least one .building file is required")

    results = [inspect_file(path.resolve()) for path in args.files]
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(results, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown:
        if len(results) != 1:
            raise SystemExit("--markdown accepts exactly one input file")
        markdown_report(results[0], args.markdown.resolve())
    if args.commands_dir:
        write_commands(results, args.commands_dir.resolve())
    print(json.dumps(
        [
            {
                "file": Path(result["file"]).name,
                "commandBlocks": result["commands"]["count"],
                "nonEmpty": result["commands"]["nonEmpty"],
                "empty": result["commands"]["empty"],
                "unique": result["commands"]["uniqueNonEmpty"],
            }
            for result in results
        ],
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError, zlib.error) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
