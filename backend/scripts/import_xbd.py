"""Import real xBD (xView2) disaster pairs into DefenceVision through the API.

The xBD dataset is organised into pre/post disaster tiles. For each tile the
dataset provides:

    {disaster}_{tile}_pre_disaster.png     (before image)
    {disaster}_{tile}_post_disaster.png    (after image)
    {disaster}_{tile}_post_disaster_target.png   (ground-truth damage mask)

This script:
  1. Recursively finds every *_pre_disaster.png / *_post_disaster.png pair.
  2. Copies each selected pair (and optionally its ground-truth target mask)
     into  DATA_ROOT/imports/{disaster}_{tile}/  as pre.png / post.png / gt.png.
  3. Creates an analysis via the API, uploads before/after, and starts processing.

Usage (with the stack up):

    # Import written files into this directory: use the kagglehub path directly
    docker compose exec backend python scripts/import_xbd.py \
        /root/.cache/kagglehub/datasets/qianlanzz/xbd-dataset/versions/*/ \
        --limit 1

    # Pick a specific disaster only
    docker compose exec backend python scripts/import_xbd.py <xbd_root> \
        --filter hurricane --limit 1

    # Skip the pipeline, just stage pairs to ./data/imports/
    docker compose exec backend python scripts/import_xbd.py <xbd_root> \
        --stage-only

Responsible-use note: files are imported *as provided* by the public dataset
and kept under ./data/imports so it is obvious they are external real imagery,
not synthetic.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

import httpx

BASE = "http://localhost:8000"
PRE = "_pre_disaster.png"
POST = "_post_disaster.png"
TARGET = "_post_disaster_target.png"


def find_pairs(root: Path) -> list[tuple[Path, Path, Path | None]]:
    """Return (pre, post, target|None) tuples across the dataset tree."""
    pre_set: dict[str, Path] = {}
    targets: dict[str, Path] = {}
    for f in root.rglob("*.png"):
        name = f.name
        if name.endswith(TARGET):
            targets[name[: -len(TARGET)]] = f
        elif name.endswith(PRE):
            pre_set[name[: -len(PRE)]] = f
    pairs: list[tuple[Path, Path, Path | None]] = []
    for base_name, pre in sorted(pre_set.items()):
        post = root / f"{base_name}{POST}"
        if not post.exists():
            # post may live elsewhere in the tree; locate it.
            for f in root.rglob(f"{base_name}{POST}"):
                post = f
                break
        if not post.exists():
            continue
        pairs.append((pre, post, targets.get(base_name)))
    return pairs


def stage_pair(pair: tuple[Path, Path, Path | None], dest_root: Path) -> Path:
    pre, post, target = pair
    stem = pre.stem[: -len(PRE)] if pre.stem.endswith(PRE) else pre.stem
    sub = dest_root / stem
    sub.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pre, sub / "pre.png")
    shutil.copy2(post, sub / "post.png")
    if target:
        shutil.copy2(target, sub / "gt.png")
    return sub


def run_pipeline(client: httpx.Client, label: str, sub: Path) -> int:
    """Create an analysis, upload the staged pair, and kick off processing."""
    r = client.post(
        "/api/analyses",
        json={"name": label, "description": "Imported xBD (xView2) real imagery pair"},
    )
    r.raise_for_status()
    aid = r.json()["id"]
    print(f"[import] analysis #{aid} created: {label}")

    for img_type, fname in (("before", "pre.png"), ("after", "post.png")):
        with open(sub / fname, "rb") as fh:
            up = client.post(
                f"/api/analyses/{aid}/upload",
                params={"type": img_type},
                files={"file": (fname, fh, "image/png")},
            )
            up.raise_for_status()
    print(f"[import] uploaded before/after for #{aid}")

    pp = client.post(f"/api/analyses/{aid}/process")
    pp.raise_for_status()

    s = {}
    for _ in range(120):  # xBD tiles are 1024x1024 -> can be slow
        s = client.get(f"/api/analyses/{aid}/statistics").json()
        if s["status"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(1)
    print(f"[import] #{aid} status={s['status']}")
    if s["status"] != "COMPLETED":
        print(f"[import]   error: {s.get('error_message')}")
        return 1
    stats = s["detection_statistics"]
    print(f"[import]   changes total={stats['total']} "
          f"(high={stats['high']} med={stats['medium']} low={stats['low']})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xbd_root", help="Path to the downloaded xBD dataset root")
    parser.add_argument("--limit", type=int, default=1, help="Max pairs to import")
    parser.add_argument("--filter", default="", help="Only pairs whose stem contains this")
    parser.add_argument("--stage-only", action="store_true",
                        help="Copy pairs into ./data/imports but do not run the pipeline")
    args = parser.parse_args()

    root = Path(args.xbd_root).expanduser().resolve()
    if not root.exists():
        print(f"Dataset path not found: {root}")
        return 2

    pairs = find_pairs(root)
    if args.filter:
        pairs = [p for p in pairs if args.filter in p[0].name]
    if not pairs:
        print(f"No xBD pre/post pairs found under {root}")
        return 2
    if args.limit:
        pairs = pairs[: args.limit]

    # Stage under DATA_ROOT so files are persisted next to other project data.
    dest_root = Path("data/imports").resolve()

    failures = 0
    with httpx.Client(base_url=BASE, timeout=300) as client:
        for i, pair in enumerate(pairs, 1):
            pre, _post, target = pair
            label = pre.stem[: -len(PRE)] if pre.stem.endswith(PRE) else pre.stem
            sub = stage_pair(pair, dest_root)
            print(f"[import] [{i}/{len(pairs)}] staged {label} -> {sub}"
                  f"{' (has ground-truth)' if target else ''}")
            if args.stage_only:
                continue
            if run_pipeline(client, label, sub) != 0:
                failures += 1

    print(f"\n[import] done: staged {len(pairs)} pair(s), {failures} failed.")
    print(f"         staged under: {dest_root}")
    if not args.stage_only:
        print("         view the analyses in the UI at http://localhost:3000/analyses")
    return 1 if (failures and not args.stage_only) else 0


if __name__ == "__main__":
    sys.exit(main())
