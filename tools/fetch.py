#!/usr/bin/env python3
"""Fetch the gold-master boards listed in boards.toml at their pinned commits; verify sha256.
Stdlib only. Usage: python3 tools/fetch.py [board-id ...]   -> boards/<id>/{pcb,pro,dru}"""
import hashlib, pathlib, sys, tomllib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = tomllib.loads((ROOT / "boards.toml").read_text())


def fetch(bid: str) -> None:
    b = MANIFEST[bid]
    out = ROOT / "boards" / bid
    out.mkdir(parents=True, exist_ok=True)
    for kind, f in b["files"].items():
        dst = out / f"board.kicad_{kind}"
        if dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest() == f["sha256"]:
            continue
        url = f"https://raw.githubusercontent.com/{b['repo']}/{b['commit']}/{f['path']}"
        data = urllib.request.urlopen(url, timeout=120).read()
        got = hashlib.sha256(data).hexdigest()
        if got != f["sha256"]:
            sys.exit(f"{bid}/{f['path']}: sha256 {got} != pinned {f['sha256']}")
        dst.write_bytes(data)
    print(f"{bid}: ok ({b['tier']}, {b['repo']}@{b['commit'][:7]})")


if __name__ == "__main__":
    for bid in sys.argv[1:] or MANIFEST:
        fetch(bid)
