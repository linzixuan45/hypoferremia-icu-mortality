#!/usr/bin/env python3
"""Write or verify the data-free local R3 candidate SHA-256 manifest."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SOURCE_SHA256_MANIFEST.tsv"
IGNORED_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv", "result"}


def current_entries() -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ROOT.rglob("*"))
        if path.is_file() and path != MANIFEST
        and not any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate candidate checksum manifest")
    args = parser.parse_args()
    observed = current_entries()
    if args.write:
        MANIFEST.write_text(
            "path\tsha256\n" + "".join(f"{path}\t{digest}\n" for path, digest in observed.items()),
            encoding="utf-8",
        )
        print(f"Wrote {len(observed)} candidate SHA-256 entries")
        return 0
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "path\tsha256":
        raise ValueError("Unexpected checksum manifest header")
    expected = dict(line.split("\t", 1) for line in lines[1:])
    if expected != observed:
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        changed = sorted(path for path in expected.keys() & observed.keys() if expected[path] != observed[path])
        print({"missing": missing, "extra": extra, "changed": changed})
        return 1
    print(f"PASS: {len(observed)} candidate SHA-256 entries match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
