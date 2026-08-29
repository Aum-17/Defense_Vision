import { useRef, useState, useCallback, useEffect } from "react";
import type { Detection } from "../types";

export type ViewerMode = "side" | "slider" | "overlay" | "bbox";

interface BBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

function parseBBox(d: Detection): BBox | null {
  if (!d.bbox_json) return null;
  try {
    const [x, y, w, h] = JSON.parse(d.bbox_json);
    return { x, y, w, h };
  } catch {
    return null;
  }
}

export function ImageViewer({
  beforeUrl,
  afterUrl,
  maskUrl,
  detections,
  imageWidth,
  imageHeight,
}: {
  beforeUrl: string;
  afterUrl: string;
  maskUrl: string | null;
  detections: Detection[];
  imageWidth: number | null;
  imageHeight: number | null;
}) {
  const [mode, setMode] = useState<ViewerMode>("slider");
  const [slider, setSlider] = useState(50);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);

  const imgW = imageWidth || 800;
  const imgH = imageHeight || 600;

  const onWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.15 : 0.87;
      setZoom((z) => Math.min(6, Math.max(1, z * factor)));
    },
    []
  );

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y };
  }, [pan]);

  useEffect(() => {
    const move = (e: MouseEvent) => {
      if (!drag.current) return;
      const dx = e.clientX - drag.current.x;
      const dy = e.clientY - drag.current.y;
      setPan({ x: drag.current.px + dx, y: drag.current.py + dy });
    };
    const up = () => (drag.current = null);
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    return () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
    };
  }, []);

  const boxes = detections
    .map((d) => ({ det: d, box: parseBBox(d) }))
    .filter((b): b is { det: Detection; box: BBox } => b.box !== null);

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {(
          [
            ["side", "Side-by-side"],
            ["slider", "Slider"],
            ["overlay", "Overlay Mask"],
            ["bbox", "Detections"],
          ] as [ViewerMode, string][]
        ).map(([m, label]) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              mode === m ? "bg-accent text-white" : "bg-base-800 text-slate-300 hover:bg-base-700"
            }`}
          >
            {label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-1 text-xs text-slate-400">
          <button className="btn-ghost !px-2 !py-1" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>
            Reset
          </button>
          <span>{Math.round(zoom * 100)}%</span>
        </div>
      </div>

      <div
        className="relative h-[480px] cursor-grab touch-none select-none overflow-hidden rounded-lg border border-base-800 bg-base-950 active:cursor-grabbing"
        onWheel={onWheel}
        onMouseDown={onMouseDown}
      >
        <div
          className="absolute inset-0"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "center center",
          }}
        >
          <div className="relative flex h-full w-full items-center justify-center">
            <div
              className="relative"
              style={{ width: imgW, height: imgH }}
            >
              {/* Side-by-side: before left, after right */}
              {mode === "side" && (
                <>
                  <img
                    src={beforeUrl}
                    className="absolute left-0 top-0"
                    style={{ width: "50%", height: "100%" }}
                    draggable={false}
                    alt="before"
                  />
                  <div className="absolute inset-y-0 left-1/2 z-10 w-px bg-slate-700" />
                  <img
                    src={afterUrl}
                    className="absolute top-0"
                    style={{ left: "50%", width: "50%", height: "100%" }}
                    draggable={false}
                    alt="after"
                  />
                </>
              )}

              {/* Slider comparison */}
              {mode === "slider" && (
                <>
                  <img src={beforeUrl} className="absolute inset-0 h-full w-full object-fill" draggable={false} alt="before" />
                  <img
                    src={afterUrl}
                    className="absolute inset-0 h-full w-full object-fill"
                    draggable={false}
                    alt="after"
                    style={{ clipPath: `inset(0 ${100 - slider}% 0 0)` }}
                  />
                  <div
                    className="absolute inset-y-0 z-10 w-0.5 bg-accent"
                    style={{ left: `${slider}%` }}
                  />
                </>
              )}

              {/* Overlay mask */}
              {mode === "overlay" && (
                <>
                  <img src={beforeUrl} className="absolute inset-0 h-full w-full object-fill" draggable={false} alt="before" />
                  {maskUrl && (
                    <img
                      src={maskUrl}
                      className="absolute inset-0 h-full w-full object-fill opacity-70 mix-blend-screen"
                      draggable={false}
                      alt="change mask"
                      style={{ filter: "invert(1) brightness(0.85) saturate(2)" }}
                    />
                  )}
                </>
              )}

              {/* Detection bounding boxes */}
              {mode === "bbox" && (
                <>
                  <img src={afterUrl} className="absolute inset-0 h-full w-full object-fill" draggable={false} alt="after" />
                  {boxes.map(({ det, box }) => (
                    <div
                      key={det.id}
                      className="absolute border-2 border-accent"
                      style={{
                        left: `${(box.x / imgW) * 100}%`,
                        top: `${(box.y / imgH) * 100}%`,
                        width: `${(box.w / imgW) * 100}%`,
                        height: `${(box.h / imgH) * 100}%`,
                      }}
                      title={`${det.change_id} — ${det.category}`}
                    >
                      <span className="absolute -top-5 left-0 whitespace-nowrap rounded bg-accent px-1.5 py-0.5 text-[10px] font-semibold text-white">
                        {det.change_id}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {mode === "slider" && (
        <input
          type="range"
          min={0}
          max={100}
          value={slider}
          onChange={(e) => setSlider(parseInt(e.target.value, 10))}
          className="mt-3 w-full accent-accent"
        />
      )}

      {(mode === "side" || mode === "slider" || mode === "overlay" || mode === "bbox") && (
        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
          <span>Scroll to zoom</span>
          <span>·</span>
          <span>Drag to pan</span>
          <span>·</span>
          <span>
            {mode === "bbox"
              ? `${boxes.length} detection${boxes.length === 1 ? "" : "s"} boxed`
              : mode === "overlay"
              ? "Red overlay = change mask"
              : "Before vs After"}
          </span>
        </div>
      )}
    </div>
  );
}
