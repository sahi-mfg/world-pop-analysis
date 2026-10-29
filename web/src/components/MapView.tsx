import * as maplibregl from "maplibre-gl";
import type { GeoJSONSource, LngLatBoundsLike } from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import { useEffect, useRef } from "react";
import type { BBox, Region } from "../api";
import { normalizeBBox } from "../format";

// maplibre-gl 6 ships its worker as a separate ES module; let Vite bundle it.
maplibregl.setWorkerUrl(workerUrl);

const STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

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
  onDraw: (bbox: BBox) => void;
  onSelectRegion: (key: string) => void;
}

export default function MapView({ bbox, regions, drawing, onDraw, onSelectRegion }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const onLoad = useRef<(() => void) | null>(null);
  const loaded = useRef(false);
  // Latest callbacks, so map listeners registered once never go stale.
  const handlers = useRef({ onDraw, onSelectRegion, drawing });
  handlers.current = { onDraw, onSelectRegion, drawing };

  useEffect(() => {
    const map = new maplibregl.Map({
      container: container.current!,
      style: STYLE,
      bounds: bbox as LngLatBoundsLike,
      fitBoundsOptions: { padding: 80 },
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      map.addSource("regions", { type: "geojson", data: collection([]) });
      map.addSource("selection", { type: "geojson", data: collection([]) });
      map.addSource("draft", { type: "geojson", data: collection([]) });
      map.addLayer({
        id: "regions-fill",
        type: "fill",
        source: "regions",
        paint: { "fill-color": "#a3abb7", "fill-opacity": 0.04 },
      });
      map.addLayer({
        id: "regions-line",
        type: "line",
        source: "regions",
        paint: { "line-color": "#a3abb7", "line-opacity": 0.35, "line-dasharray": [2, 2] },
      });
      map.addLayer({
        id: "selection-fill",
        type: "fill",
        source: "selection",
        paint: { "fill-color": "#f5a524", "fill-opacity": 0.14 },
      });
      map.addLayer({
        id: "selection-line",
        type: "line",
        source: "selection",
        paint: { "line-color": "#f5a524", "line-width": 2 },
      });
      map.addLayer({
        id: "draft-line",
        type: "line",
        source: "draft",
        paint: { "line-color": "#2dd4bf", "line-width": 2, "line-dasharray": [1.5, 1] },
      });
      loaded.current = true;
      onLoad.current?.();
    });

    map.on("click", "regions-fill", (e) => {
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
    map.on("mousedown", (e) => {
      if (!handlers.current.drawing) return;
      e.preventDefault();
      start = [e.lngLat.lng, e.lngLat.lat];
    });
    map.on("mousemove", (e) => {
      if (!start) return;
      draft()?.setData(collection([polygon(normalizeBBox(start, [e.lngLat.lng, e.lngLat.lat]))]));
    });
    map.on("mouseup", (e) => {
      if (!start) return;
      const b = normalizeBBox(start, [e.lngLat.lng, e.lngLat.lat]);
      start = null;
      draft()?.setData(collection([]));
      if (b[2] - b[0] > 0.01 && b[3] - b[1] > 0.01) handlers.current.onDraw(b);
    });

    return () => {
      loaded.current = false;
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
      map.fitBounds(bbox as LngLatBoundsLike, { padding: 80, duration: 1200 });
    };
    if (loaded.current) apply();
    else onLoad.current = apply;
  }, [bbox, regions]);

  return <div ref={container} className="absolute inset-0" />;
}
