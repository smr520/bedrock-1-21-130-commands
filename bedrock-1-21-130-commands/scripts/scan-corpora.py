#!/usr/bin/env python3
"""Inventory Minecraft command corpora without extracting archives in place."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TEXT_SUFFIXES = {".txt", ".mcfunction", ".md"}
ZIP_CONTAINER_SUFFIXES = {".zip", ".docx", ".mcworld", ".mcaddon"}
ARCHIVE_SUFFIXES = ZIP_CONTAINER_SUFFIXES | {".7z"}
OPAQUE_SUFFIXES = {".pdf", ".bdx", ".doc", ".exe", ".sh"}
SKIP_DIRS = {".git", ".opencode", "node_modules"}

SYNTAX_PATTERNS = {
    "modern_execute": re.compile(
        r"(?im)^\s*/?execute\s+(?:align|anchored|as|at|facing|if|in|on|positioned|rotated|run|unless)\b"
    ),
    "legacy_execute": re.compile(r"(?im)^\s*/?execute\s+@"),
    "execute_store": re.compile(r"(?im)\bexecute\s+store\b"),
    "java_selector": re.compile(
        r"(?im)\b(?:limit|sort|distance|nbt|team|predicate|advancement)\s*="
    ),
    "data_command": re.compile(r"(?im)^\s*/?data\s+"),
    "item_replace": re.compile(r"(?im)^\s*/?item\s+replace\b"),
    "forceload": re.compile(r"(?im)^\s*/?forceload\b"),
    "function_command": re.compile(r"(?im)^\s*/?function\b"),
    "schedule_command": re.compile(r"(?im)^\s*/?schedule\b"),
    "scoreboard": re.compile(r"(?im)^\s*/?scoreboard\b"),
    "title": re.compile(r"(?im)^\s*/?title(?:raw)?\b"),
    "tellraw": re.compile(r"(?im)^\s*/?tellraw\b"),
    "replaceitem": re.compile(r"(?im)^\s*/?replaceitem\b"),
    "summon_nbt": re.compile(r"(?im)^\s*/?summon\b[^\n]*\{"),
    "hasitem": re.compile(r"(?im)\bhasitem\s*="),
    "tickingarea": re.compile(r"(?im)^\s*/?tickingarea\b"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_text(data: bytes) -> tuple[str, str]:
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8-sig"
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le"), "utf-16-le"
    if data.startswith(b"\xfe\xff"):
        return data[2:].decode("utf-16-be"), "utf-16-be"
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    if data.count(b"\x00") > max(8, len(data) // 10):
        try:
            return data.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            pass

    try:
        return data.decode("gb18030"), "gb18030"
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace"), "utf-8-replace"


def count_lines(text: str) -> int:
    return text.count("\n") + (1 if text else 0)


def count_syntax(text: str, counts: Counter[str]) -> None:
    for name, pattern in SYNTAX_PATTERNS.items():
        counts[name] += sum(1 for _ in pattern.finditer(text))


def iter_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
    ]


def scan_extracted(root: Path) -> dict:
    all_files = iter_files(root)
    files_by_suffix: Counter[str] = Counter()
    text_records: dict[str, dict[str, Any]] = {}
    text_files = 0
    text_bytes = 0
    lines = 0
    encodings_all: Counter[str] = Counter()
    mislabeled_archives: list[str] = []
    top_text_files: list[dict[str, Any]] = []

    for path in all_files:
        suffix = path.suffix.lower() or "<none>"
        files_by_suffix[suffix] += 1
        if suffix not in TEXT_SUFFIXES:
            continue

        data = path.read_bytes()
        text, encoding = decode_text(data)
        text_files += 1
        text_bytes += len(data)
        lines += count_lines(text)
        encodings_all[encoding] += 1
        top_text_files.append({"path": str(path), "bytes": len(data), "lines": count_lines(text)})

        digest = sha256_bytes(data)
        if digest not in text_records:
            text_records[digest] = {
                "path": str(path),
                "bytes": len(data),
                "lines": count_lines(text),
                "encoding": encoding,
                "text": text,
                "count": 1,
            }
        else:
            text_records[digest]["count"] += 1

        if data.startswith(b"PK\x03\x04"):
            mislabeled_archives.append(str(path))

    encodings_unique: Counter[str] = Counter()
    syntax_unique: Counter[str] = Counter()
    syntax_all: Counter[str] = Counter()
    unique_lines = 0
    unique_bytes = 0
    for record in text_records.values():
        encodings_unique[record["encoding"]] += 1
        unique_lines += record["lines"]
        unique_bytes += record["bytes"]
        record_syntax: Counter[str] = Counter()
        count_syntax(record["text"], record_syntax)
        syntax_unique.update(record_syntax)
        for name, count in record_syntax.items():
            syntax_all[name] += count * record["count"]

    top_text_files.sort(key=lambda item: (item["bytes"], item["lines"]), reverse=True)
    duplicate_text_files = text_files - len(text_records)
    return {
        "all_files": len(all_files),
        "files_by_suffix": dict(files_by_suffix.most_common()),
        "text_files": text_files,
        "unique_text_files": len(text_records),
        "duplicate_text_files": duplicate_text_files,
        "text_bytes": text_bytes,
        "unique_text_bytes": unique_bytes,
        "lines": lines,
        "unique_lines": unique_lines,
        "encodings": dict(encodings_all.most_common()),
        "unique_encodings": dict(encodings_unique.most_common()),
        "syntax_hits": dict(syntax_all.most_common()),
        "unique_syntax_hits": dict(syntax_unique.most_common()),
        "mislabeled_archives": mislabeled_archives,
        "top_text_files": top_text_files[:15],
    }


def new_zip_metrics() -> dict[str, Any]:
    return {
        "entries": 0,
        "nested_archives": 0,
        "encrypted_entries": 0,
        "unreadable_entries": 0,
        "suffixes": Counter(),
        "text_files": 0,
        "text_bytes": 0,
        "lines": 0,
        "encodings_all": Counter(),
        "text_digests": {},
        "errors": [],
    }


def ingest_text(
    metrics: dict[str, Any],
    data: bytes,
    text: str,
    encoding: str,
) -> None:
    metrics["text_files"] += 1
    metrics["text_bytes"] += len(data)
    metrics["lines"] += count_lines(text)
    metrics["encodings_all"][encoding] += 1
    digest = sha256_bytes(data)
    if digest not in metrics["text_digests"]:
        metrics["text_digests"][digest] = {
            "bytes": len(data),
            "lines": count_lines(text),
            "encoding": encoding,
            "text": text,
            "count": 1,
        }
    else:
        metrics["text_digests"][digest]["count"] += 1


def extract_docx_text(data: bytes) -> str:
    root = ET.fromstring(data)
    paragraphs: list[str] = []
    for paragraph in root.iter():
        if paragraph.tag.endswith("}p"):
            texts = [node.text or "" for node in paragraph.iter() if node.tag.endswith("}t")]
            if texts:
                paragraphs.append("".join(texts))
    return "\n".join(paragraphs)


def scan_zip_bytes(
    data: bytes,
    name: str,
    max_depth: int,
    depth: int = 0,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if metrics is None:
        metrics = new_zip_metrics()
    if depth > max_depth:
        metrics["errors"].append(f"nested depth exceeded: {name}")
        return metrics

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if Path(name).suffix.lower() == ".docx":
                try:
                    xml_data = archive.read("word/document.xml")
                    text = extract_docx_text(xml_data)
                    ingest_text(metrics, xml_data, text, "docx-xml-utf-8")
                except (KeyError, ET.ParseError, OSError) as exc:
                    metrics["errors"].append(f"docx text unavailable in {name}: {exc}")

            for info in archive.infolist():
                if info.is_dir():
                    continue
                metrics["entries"] += 1
                suffix = Path(info.filename).suffix.lower() or "<none>"
                metrics["suffixes"][suffix] += 1
                if info.flag_bits & 0x1:
                    metrics["encrypted_entries"] += 1
                    continue
                try:
                    entry_data = archive.read(info)
                except (OSError, RuntimeError, NotImplementedError) as exc:
                    metrics["unreadable_entries"] += 1
                    metrics["errors"].append(f"unreadable {info.filename}: {exc}")
                    continue

                if suffix in TEXT_SUFFIXES:
                    text, encoding = decode_text(entry_data)
                    ingest_text(metrics, entry_data, text, encoding)
                    if entry_data.startswith(b"PK\x03\x04"):
                        nested_name = f"{info.filename}.zip"
                        metrics["nested_archives"] += 1
                        scan_zip_bytes(
                            entry_data,
                            nested_name,
                            max_depth,
                            depth + 1,
                            metrics,
                        )
                    continue

                if suffix in ZIP_CONTAINER_SUFFIXES:
                    metrics["nested_archives"] += 1
                    scan_zip_bytes(
                        entry_data,
                        info.filename,
                        max_depth,
                        depth + 1,
                        metrics,
                    )
    except (OSError, zipfile.BadZipFile) as exc:
        metrics["errors"].append(f"zip unavailable: {exc}")

    return metrics


def finalize_zip_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    encodings_unique: Counter[str] = Counter()
    syntax_unique: Counter[str] = Counter()
    syntax_all: Counter[str] = Counter()
    unique_text_bytes = 0
    unique_lines = 0
    for record in metrics["text_digests"].values():
        encodings_unique[record["encoding"]] += 1
        unique_text_bytes += record["bytes"]
        unique_lines += record["lines"]
        record_syntax: Counter[str] = Counter()
        count_syntax(record["text"], record_syntax)
        syntax_unique.update(record_syntax)
        for name, count in record_syntax.items():
            syntax_all[name] += count * record["count"]
    return {
        "entries": metrics["entries"],
        "nested_archives": metrics["nested_archives"],
        "encrypted_entries": metrics["encrypted_entries"],
        "unreadable_entries": metrics["unreadable_entries"],
        "suffixes": dict(metrics["suffixes"].most_common()),
        "text_files": metrics["text_files"],
        "unique_text_files": len(metrics["text_digests"]),
        "duplicate_text_files": metrics["text_files"] - len(metrics["text_digests"]),
        "text_bytes": metrics["text_bytes"],
        "unique_text_bytes": unique_text_bytes,
        "lines": metrics["lines"],
        "unique_lines": unique_lines,
        "encodings": dict(metrics["encodings_all"].most_common()),
        "unique_encodings": dict(encodings_unique.most_common()),
        "syntax_hits": dict(syntax_all.most_common()),
        "unique_syntax_hits": dict(syntax_unique.most_common()),
        "errors": metrics["errors"][:50],
    }


def scan_archives(root: Path, max_depth: int) -> list[dict]:
    archives = [path for path in iter_files(root) if path.suffix.lower() in ARCHIVE_SUFFIXES]
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for path in archives:
        by_hash[sha256_file(path)].append(path)

    results: list[dict] = []
    for digest, copies in sorted(
        by_hash.items(),
        key=lambda item: max(path.stat().st_size for path in item[1]),
        reverse=True,
    ):
        representative = sorted(copies, key=lambda p: ("(1)" in p.name, len(p.name), str(p)))[0]
        suffix = representative.suffix.lower()
        archive_bytes = representative.stat().st_size
        total_bytes = sum(path.stat().st_size for path in copies)
        result: dict[str, Any] = {
            "name": representative.name,
            "path": str(representative),
            "kind": suffix.lstrip("."),
            "sha256": digest,
            "copies": len(copies),
            "archive_bytes": archive_bytes,
            "total_bytes": total_bytes,
            "entries": 0,
            "text_files": 0,
            "text_bytes": 0,
            "lines": 0,
            "encrypted_entries": 0,
            "unreadable_entries": 0,
            "parser": "unavailable",
            "error": None,
        }

        if suffix in ZIP_CONTAINER_SUFFIXES:
            data = representative.read_bytes()
            metrics = scan_zip_bytes(data, representative.name, max_depth)
            result.update(finalize_zip_metrics(metrics))
            result["parser"] = "stdlib-zip"
            if result.get("errors"):
                result["error"] = "; ".join(result["errors"][:3])
        elif suffix == ".7z":
            result["error"] = "7z parser unavailable; archive hash and size were inventoried"

        results.append(result)

    return results


def scan_opaque_files(root: Path) -> list[dict]:
    files = [path for path in iter_files(root) if path.suffix.lower() in OPAQUE_SUFFIXES]
    by_key: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for path in files:
        by_key[(sha256_file(path), path.suffix.lower())].append(path)

    results: list[dict] = []
    for (digest, suffix), copies in sorted(by_key.items()):
        representative = sorted(copies, key=lambda p: (len(p.name), str(p)))[0]
        result = {
            "name": representative.name,
            "path": str(representative),
            "kind": suffix.lstrip("."),
            "sha256": digest,
            "copies": len(copies),
            "bytes": representative.stat().st_size,
            "total_bytes": sum(path.stat().st_size for path in copies),
            "parsed": False,
            "note": "opaque or binary; inventoried without execution or text extraction",
        }
        if suffix == ".pdf":
            result["note"] = "PDF text parser unavailable; file inventoried without extraction"
        elif suffix == ".bdx":
            result["note"] = "BDump binary structure; use PhoenixBuilder or a dedicated parser"
        results.append(result)
    return results


def summarize(extracted: dict, archives: list[dict], opaque: list[dict]) -> dict:
    archive_copies = sum(item["copies"] for item in archives)
    unique_archive_bytes = sum(item["archive_bytes"] for item in archives)
    total_archive_bytes = sum(item["total_bytes"] for item in archives)
    return {
        "extracted_all_files": extracted["all_files"],
        "text_files": extracted["text_files"],
        "unique_text_files": extracted["unique_text_files"],
        "duplicate_text_files": extracted["duplicate_text_files"],
        "archive_files": archive_copies,
        "unique_archives": len(archives),
        "duplicate_archives": archive_copies - len(archives),
        "unique_archive_bytes": unique_archive_bytes,
        "total_archive_bytes": total_archive_bytes,
        "parsed_zip_archives": sum(1 for item in archives if item["parser"] == "stdlib-zip"),
        "opaque_unique_files": len(opaque),
        "opaque_files": sum(item["copies"] for item in opaque),
    }


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="scan-corpora-") as temp:
        root = Path(temp)
        text = "/execute as @a run say hi\n/execute @a ~ ~ ~ say old\n"
        (root / "a.txt").write_text(text, encoding="utf-8")
        (root / "a-copy.txt").write_text(text, encoding="utf-8")
        (root / "z.bin").write_bytes(b"\x00\x01")

        with zipfile.ZipFile(root / "bundle.zip", "w") as archive:
            archive.writestr("inside.txt", "/scoreboard players add @a coins 0\n")
            nested = io.BytesIO()
            with zipfile.ZipFile(nested, "w") as inner:
                inner.writestr("nested.txt", "/give @s apple 1\n")
            archive.writestr("nested.zip", nested.getvalue())

        with zipfile.ZipFile(root / "note.docx", "w") as document:
            document.writestr(
                "word/document.xml",
                "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
                "<w:body><w:p><w:r><w:t>/tag @s add test_tag</w:t></w:r></w:p></w:body></w:document>",
            )

        (root / "fake.7z").write_bytes(b"7z\xbc\xaf\x27\x1c")
        (root / "manual.pdf").write_bytes(b"%PDF-1.7\n")

        extracted = scan_extracted(root)
        archives = scan_archives(root, max_depth=3)
        opaque = scan_opaque_files(root)
        summary = summarize(extracted, archives, opaque)

        assert extracted["text_files"] == 2, extracted
        assert extracted["unique_text_files"] == 1, extracted
        assert extracted["syntax_hits"]["legacy_execute"] == 2, extracted
        assert extracted["unique_syntax_hits"]["legacy_execute"] == 1, extracted
        assert summary["unique_archives"] == 3, summary
        assert summary["opaque_unique_files"] == 1, summary
        docx = next(item for item in archives if item["kind"] == "docx")
        assert docx["text_files"] == 1, docx
        assert docx["syntax_hits"]["title"] == 0, docx
        seven = next(item for item in archives if item["kind"] == "7z")
        assert "parser unavailable" in seven["error"], seven

    print("self-test passed: extracted dedupe, nested zip, docx text, 7z fallback and opaque inventory")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-nested-depth", type=int, default=3)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.root is None:
        parser.error("root is required unless --self-test is used")
    if args.max_nested_depth < 0:
        parser.error("--max-nested-depth must be >= 0")

    root = args.root.resolve()
    extracted = scan_extracted(root)
    archives = scan_archives(root, args.max_nested_depth)
    opaque = scan_opaque_files(root)
    report = {
        "root": str(root),
        "summary": summarize(extracted, archives, opaque),
        "extracted": extracted,
        "archives": archives,
        "opaque_files": opaque,
    }
    if args.summary_only:
        report.pop("archives")
        report.pop("opaque_files")
        report["extracted"].pop("top_text_files", None)

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
