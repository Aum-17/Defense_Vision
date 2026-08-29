"""Headless demo: run the full pipeline through the API (requires stack up)."""
from __future__ import annotations

import sys
import time

import httpx

BASE = "http://localhost:8000"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=120) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        print(f"[health] {health.json()}")

        r = client.post("/api/demo/load")
        r.raise_for_status()
        analysis = r.json()
        aid = analysis["id"]
        print(f"[demo] loaded analysis #{aid} -> {analysis['name']}")

        # Trigger processing (demo/load already started it in background).
        for _ in range(60):
            s = client.get(f"/api/analyses/{aid}/statistics").json()
            if s["status"] in ("COMPLETED", "FAILED"):
                break
            time.sleep(0.5)
        print(f"[status] {s['status']}")
        if s["status"] != "COMPLETED":
            print("[error] processing failed")
            return 1

        stats = s["detection_statistics"]
        print(f"[changes] total={stats['total']} high={stats['high']} "
              f"med={stats['medium']} low={stats['low']} avg_conf={stats['avg_confidence']}")

        dets = client.get(f"/api/analyses/{aid}/detections").json()
        for d in dets:
            print(f"  {d['change_id']} {d['category']} severity={d['severity']} "
                  f"conf={d['confidence']:.2f} area={d['area_pixels']}")

        rr = client.post(f"/api/analyses/{aid}/report")
        rr.raise_for_status()
        print(f"[report] {rr.json()['filename']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
