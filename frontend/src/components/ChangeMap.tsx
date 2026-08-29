import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Detection } from "../types";

function parseCentroid(d: Detection): [number, number] | null {
  if (!d.centroid_json) return null;
  try {
    const [x, y] = JSON.parse(d.centroid_json);
    return [x, y];
  } catch {
    return null;
  }
}

export function ChangeMap({
  detections,
  latitude,
  longitude,
  imageWidth,
  imageHeight,
}: {
  detections: Detection[];
  latitude: number | null;
  longitude: number | null;
  imageWidth: number | null;
  imageHeight: number | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  const hasGeo = latitude !== null && longitude !== null;

  useEffect(() => {
    if (!containerRef.current) return;
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    const w = imageWidth || 800;
    const h = imageHeight || 600;

    let map: L.Map;
    if (hasGeo) {
      map = L.map(containerRef.current).setView([latitude as number, longitude as number], 16);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
      }).addTo(map);
    } else {
      // Image-relative coordinate grid (clearly labelled).
      map = L.map(containerRef.current, { crs: L.CRS.Simple });
      const bounds: L.LatLngBoundsExpression = [[0, 0], [h, w]];
      L.rectangle(bounds, { color: "#475569", weight: 1, fillColor: "#1e293b", fillOpacity: 0.4 }).addTo(map);
      map.fitBounds(bounds);
    }

    detections.forEach((d) => {
      const c = parseCentroid(d);
      if (!c) return;
      const sev = (d.severity || "LOW").toLowerCase();
      const color = sev === "high" ? "#ef4444" : sev === "medium" ? "#f59e0b" : "#22c55e";
      const icon = L.divIcon({
        className: "",
        html: `<div style="width:13px;height:13px;border-radius:50%;background:${color};border:2px solid #0f172a;"></div>`,
        iconSize: [13, 13],
        iconAnchor: [7, 7],
      });

      let latlng: L.LatLngExpression;
      if (hasGeo) {
        // Spread image-relative positions by an arbitrary small geo offset around centre.
        const fx = w > 0 ? (c[0] / w - 0.5) * 0.004 : 0;
        const fy = h > 0 ? (0.5 - c[1] / h) * 0.004 : 0;
        latlng = [(latitude as number) + fy, (longitude as number) + fx];
      } else {
        latlng = [c[1], c[0]];
      }

      const marker = L.marker(latlng, { icon });
      marker.bindPopup(
        `<strong>${d.change_id}</strong><br/>${d.category || "Change"}<br/>` +
          `Confidence: ${(d.confidence * 100).toFixed(0)}%<br/>Severity: ${d.severity}<br/>` +
          `Status: ${d.status.replace("_", " ")}`
      );
      marker.addTo(map);
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [detections, latitude, longitude, imageWidth, imageHeight, hasGeo]);

  return (
    <div>
      <div ref={containerRef} className="h-[380px] w-full rounded-lg border border-base-800" />
      <p className="mt-2 text-[11px] text-slate-500">
        {hasGeo
          ? "Markers placed approximately around the supplied geographic reference."
          : "No geographic coordinates provided — markers shown in image-relative coordinates only. Geographic coordinates are not fabricated."}
      </p>
    </div>
  );
}
