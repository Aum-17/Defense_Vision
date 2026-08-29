"""Import already-staged xBD pairs from data/imports/<name>/{pre,post,gt}.png into DefenceVision.

Each pair becomes an analysis: create -> upload before/after -> process -> wait.
Run inside the backend container (needs httpx and the API on localhost:8000).

    docker compose exec backend python scripts/import_staged.py [<name> ...]

With no names, all staged pairs under data/imports are imported.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import httpx

BASE = "http://localhost:8000"
IMPORTS = Path("data/imports")


def find_pairs(root: Path) -> list[Path]:
    subs = [d for d in root.iterdir() if d.is_dir()]
    pairs = []
    for d in sorted(subs):
        pre, post = d / "pre.png", d / "post.png"
        if pre.exists() and post.exists():
            pairs.append(d)
    return pairs


def run_pipeline(client: httpx.Client, label: str, sub: Path) -> int:
    r = client.post(
        "/api/analyses",
        json={
            "name": label,
            "description": "Imported real xBD (xView2) pre/post disaster imagery pair",
        },
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
    for _ in range(300):  # 1024x1024 xBD tiles can be slow
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
    parser.add_argument("names", nargs="*", help="Subset of staged pair names to import")
    args = parser.parse_args()

    pairs = find_pairs(IMPORTS)
    if args.names:
        wanted = {Path(n) for n in args.names}
        pairs = [p for p in pairs if p.name in wanted]
    if not pairs:
        print(f"No staged pairs found under {IMPORTS}")
        return 2

    failures = 0
    with httpx.Client(base_url=BASE, timeout=600) as client:
        for i, sub in enumerate(pairs, 1):
            print(f"[import] [{i}/{len(pairs)}] pair {sub}")
            if run_pipeline(client, sub.name, sub) != 0:
                failures += 1

    print(f"\n[import] done: imported {len(pairs)} pair(s), {failures} failed.")
    print("         view the analyses at http://localhost:3000/analyses")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
