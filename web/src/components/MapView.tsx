import * as maplibregl from "maplibre-gl";
import type { GeoJSONSource, LngLatBoundsLike } from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import { useEffect, useRef } from "react";
import type { BBox, Region } from "../api";
import { normalizeBBox } from "../format";

// maplibre-gl 6 ships its worker as a separate ES module; let Vite bundle it.
maplibregl.setWorkerUrl(workerUrl);

const STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
// Map paint cannot read CSS variables; these mirror DESIGN.md (primary, faint).
const PRIMARY = "#c2410c";
const FAINT = "#6b6c66";

function polygon(b: BBox): GeoJSON.Feature<GeoJSON.Polygon> {
  const [x0, y0, x1, y1] = b;
  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [x0, y0],
          [x1, y0],
          [x1, y1],
          [x0, y1],
          [x0, y0],
        ],
      ],
    },
  };
}

const collection = (features: GeoJSON.Feature[]): GeoJSON.FeatureCollection => ({
  type: "FeatureCollection",
  features,
});

interface Props {
  bbox: BBox;
  regions: Region[];
  drawing: boolean;
  /** Text pinned to the selected rectangle's top-left corner, e.g. "6.45 M people in 2020". */
  callout: string | null;
  onDraw: (bbox: BBox) => void;
  onSelectRegion: (key: string) => void;
}

export default function MapView({ bbox, regions, drawing, callout, onDraw, onSelectRegion }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onLoad = useRef<(() => void) | null>(null);
  const loaded = useRef(false);
  // Latest callbacks, so map listeners registered once never go stale.
  const handlers = useRef({ onDraw, onSelectRegion, drawing });
  handlers.current = { onDraw, onSelectRegion, drawing };
  const bboxRef = useRef(bbox);
  bboxRef.current = bbox;

  useEffect(() => {
    const map = new maplibregl.Map({
      container: container.current!,
      style: STYLE,
      bounds: bbox as LngLatBoundsLike,
      fitBoundsOptions: { padding: 64 },
      attributionControl: { compact: true },
      dragRotate: false,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    const el = document.createElement("div");
    el.className =
      "pointer-events-none rounded-chip bg-ink px-2 py-1 type-label text-surface shadow-float num whitespace-nowrap";
    markerRef.current = new maplibregl.Marker({ element: el, anchor: "bottom-left", offset: [-1, -6] });

    map.on("load", () => {
      map.addSource("regions", { type: "geojson", data: collection([]) });
      map.addSource("selection", { type: "geojson", data: collection([]) });
      map.addSource("draft", { type: "geojson", data: collection([]) });
      map.addLayer({
        id: "regions-fill",
        type: "fill",
        source: "regions",
        paint: { "fill-color": FAINT, "fill-opacity": 0 },
      });
      map.addLayer({
        id: "regions-line",
        type: "line",
        source: "regions",
        paint: { "line-color": FAINT, "line-opacity": 0.45, "line-width": 1 },
      });
      map.addLayer({
        id: "selection-fill",
        type: "fill",
        source: "selection",
        paint: { "fill-color": PRIMARY, "fill-opacity": 0.1 },
      });
      map.addLayer({
        id: "selection-line",
        type: "line",
        source: "selection",
        paint: { "line-color": PRIMARY, "line-width": 2 },
      });
      map.addLayer({
        id: "draft-line",
        type: "line",
        source: "draft",
        paint: { "line-color": PRIMARY, "line-width": 2, "line-opacity": 0.7 },
      });
      loaded.current = true;
      onLoad.current?.();
    });

    // The click that ends a drawn rectangle must not select the preset region under it.
    let justDrew = false;
    map.on("click", "regions-fill", (e) => {
      if (justDrew) {
        justDrew = false;
        return;
      }
      if (handlers.current.drawing) return;
      const key = e.features?.[0]?.properties?.key;
      if (key) handlers.current.onSelectRegion(String(key));
    });
    map.on("mouseenter", "regions-fill", () => {
      if (!handlers.current.drawing) map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "regions-fill", () => {
      if (!handlers.current.drawing) map.getCanvas().style.cursor = "";
    });

    // Rectangle drawing: press, drag, release.
    let start: [number, number] | null = null;
    const draft = () => map.getSource<GeoJSONSource>("draft");
    let last: [number, number] | null = null;
    const begin = (e: maplibregl.MapMouseEvent | maplibregl.MapTouchEvent) => {
      if (!handlers.current.drawing) return;
      e.preventDefault();
      start = last = [e.lngLat.lng, e.lngLat.lat];
    };
    const move = (e: maplibregl.MapMouseEvent | maplibregl.MapTouchEvent) => {
      if (!start) return;
      last = [e.lngLat.lng, e.lngLat.lat];
      draft()?.setData(collection([polygon(normalizeBBox(start, last))]));
    };
    const end = () => {
      if (!start || !last) return;
      const b = normalizeBBox(start, last);
      start = last = null;
      justDrew = true;
      setTimeout(() => (justDrew = false), 0);
      draft()?.setData(collection([]));
      if (b[2] - b[0] > 0.01 && b[3] - b[1] > 0.01) handlers.current.onDraw(b);
    };
    map.on("mousedown", begin);
    map.on("touchstart", begin);
    map.on("mousemove", move);
    map.on("touchmove", move);
    map.on("mouseup", end);
    map.on("touchend", end);

    // Keep the selection framed when the layout changes width (sidebar fold, rotation).
    const resize = new ResizeObserver(() => {
      map.resize();
      if (loaded.current) map.fitBounds(bboxRef.current as LngLatBoundsLike, { padding: 64, duration: 0 });
    });
    resize.observe(container.current!);

    return () => {
      resize.disconnect();
      loaded.current = false;
      markerRef.current?.remove();
      map.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- the map is created once
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.getCanvas().style.cursor = drawing ? "crosshair" : "";
    if (drawing) map.dragPan.disable();
    else map.dragPan.enable();
  }, [drawing]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      map.getSource<GeoJSONSource>("regions")?.setData(
        collection(regions.map((r) => ({ ...polygon(r.bbox), properties: { key: r.key } }))),
      );
      map.getSource<GeoJSONSource>("selection")?.setData(collection([polygon(bbox)]));
      map.fitBounds(bbox as LngLatBoundsLike, { padding: 64, duration: 900 });
    };
    if (loaded.current) apply();
    else onLoad.current = apply;
  }, [bbox, regions]);

  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    if (!map || !marker) return;
    if (callout) {
      marker.getElement().textContent = callout;
      marker.setLngLat([bbox[0], bbox[3]]).addTo(map);
    } else {
      marker.remove();
    }
  }, [bbox, callout]);

  // maplibre's own (unlayered) CSS sets the container to position: relative, so the
  // positioning lives on a wrapper that Tailwind utilities can still control.
  return (
    <div className="absolute inset-0">
      <div ref={container} className="h-full w-full" />
    </div>
  );
}
