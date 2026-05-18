from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"
METADATA = DATA_PROCESSED / "prediction" / "heatmap_tmrt_montpellier_10m_filters" / "tmrt_montpellier_10m_filtres_metadata.json"
MAIN_METADATA = DATA_PROCESSED / "prediction" / "heatmap_tmrt_montpellier_10m" / "tmrt_montpellier_10m_metadata_catboost.json"
MAIN_PREDICTIONS = DATA_PROCESSED / "prediction" / "heatmap_tmrt_montpellier_10m" / "tmrt_montpellier_10m_predictions_catboost.csv"
ROUTE_PREDICTIONS = DATA_PROCESSED / "prediction" / "tmrt_predictions_grid_or_points.csv"
CLEAN_NOZEROS = DATA_PROCESSED / "picopatt" / "clean_nozeros"
HEATMAP_TILE_SOURCE = ROOT / "prediction" / "figures" / "heatmap_tmrt_montpellier_10m" / "tmrt_montpellier_10m_overlay_catboost_smooth2x.png"
HEATMAP_EXPORT = ROOT / "prediction" / "figures" / "heatmap_tmrt_montpellier_10m" / "tmrt_montpellier_10m_overlay_catboost_smooth2x.webp"
APP_DIR = ROOT / "app" / "webapp_tmrt_montpellier"
DATA_JS = APP_DIR / "scenario-data.js"
TILE_DIR = APP_DIR / "heatmap_tiles"
TILE_MANIFEST = TILE_DIR / "manifest.json"
VALUE_TILE_DIR = APP_DIR / "heatmap_value_tiles"
VALUE_TILE_MANIFEST = VALUE_TILE_DIR / "manifest.json"

BOUNDS = [[43.5587043762207, 3.7986068725585938], [43.66122817993164, 3.961625576019287]]
MONTH_ORDER = ["10", "11", "12", "01"]
SLOT_ORDER = ["M1", "M2", "M3", "M4"]
MONTH_LABEL_FIXES = {
    "Decembre": "Decembre",
}
TRACKS = [
    {"id": "antigone", "order": 1, "name": "Antigone", "color": "#007a5a"},
    {"id": "boulevards", "order": 2, "name": "Boulevards", "color": "#b23a1b"},
    {"id": "ecusson", "order": 3, "name": "Ecusson", "color": "#1f2937"},
]
MAX_POINTS_PER_TRACK = 1000
TILE_SIZE = 256
TILE_MIN_ZOOM = 12
TILE_MAX_ZOOM = 17
VALUE_RASTER_SCALE = 2


def _as_clean_float(value: float, digits: int) -> float:
    return round(float(value), digits)


def _world_xy(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    sin_lat = math.sin(lat * math.pi / 180)
    size = TILE_SIZE * 2**zoom
    x = ((lon + 180) / 360) * size
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * size
    return x, y


def ensure_heatmap_tiles() -> dict:
    source_stat = HEATMAP_TILE_SOURCE.stat()
    manifest = {
        "version": 2,
        "source": str(HEATMAP_TILE_SOURCE.relative_to(ROOT)),
        "source_mtime_ns": source_stat.st_mtime_ns,
        "source_size": source_stat.st_size,
        "bounds": BOUNDS,
        "tile_size": TILE_SIZE,
        "min_zoom": TILE_MIN_ZOOM,
        "max_zoom": TILE_MAX_ZOOM,
        "url_template": "./heatmap_tiles/{z}/{x}/{y}.webp",
    }
    if TILE_MANIFEST.exists():
        try:
            existing = json.loads(TILE_MANIFEST.read_text(encoding="utf-8"))
            if existing == manifest:
                return manifest
        except json.JSONDecodeError:
            pass

    if TILE_DIR.exists():
        shutil.rmtree(TILE_DIR)
    TILE_DIR.mkdir(parents=True, exist_ok=True)

    src = Image.open(HEATMAP_TILE_SOURCE).convert("RGBA")
    src_w, src_h = src.size
    (south, west), (north, east) = BOUNDS

    for zoom in range(TILE_MIN_ZOOM, TILE_MAX_ZOOM + 1):
        nw_x, nw_y = _world_xy(north, west, zoom)
        se_x, se_y = _world_xy(south, east, zoom)
        x_start = math.floor(nw_x / TILE_SIZE)
        x_end = math.floor(se_x / TILE_SIZE)
        y_start = math.floor(nw_y / TILE_SIZE)
        y_end = math.floor(se_y / TILE_SIZE)

        for x in range(x_start, x_end + 1):
            x0 = x * TILE_SIZE
            x1 = (x + 1) * TILE_SIZE
            ix0 = max(x0, nw_x)
            ix1 = min(x1, se_x)
            if ix1 <= ix0:
                continue

            zoom_dir = TILE_DIR / str(zoom) / str(x)
            zoom_dir.mkdir(parents=True, exist_ok=True)

            for y in range(y_start, y_end + 1):
                y0 = y * TILE_SIZE
                y1 = (y + 1) * TILE_SIZE
                iy0 = max(y0, nw_y)
                iy1 = min(y1, se_y)
                if iy1 <= iy0:
                    continue

                sx0 = (ix0 - nw_x) / (se_x - nw_x) * src_w
                sx1 = (ix1 - nw_x) / (se_x - nw_x) * src_w
                sy0 = (iy0 - nw_y) / (se_y - nw_y) * src_h
                sy1 = (iy1 - nw_y) / (se_y - nw_y) * src_h

                crop = src.crop((sx0, sy0, sx1, sy1))
                dw = max(1, round(ix1 - ix0))
                dh = max(1, round(iy1 - iy0))
                crop = crop.resize((dw, dh), Image.Resampling.LANCZOS)

                tile = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
                tile.alpha_composite(crop, (round(ix0 - x0), round(iy0 - y0)))
                tile.save(zoom_dir / f"{y}.webp", format="WEBP", quality=88, method=4)

    TILE_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def ensure_value_tiles(main_metadata: dict) -> dict:
    source_stat = MAIN_PREDICTIONS.stat()
    vmin = float(main_metadata["tmrt_pred_min"])
    vmax = float(main_metadata["tmrt_pred_max"])
    manifest = {
        "version": 1,
        "source": str(MAIN_PREDICTIONS.relative_to(ROOT)),
        "source_mtime_ns": source_stat.st_mtime_ns,
        "source_size": source_stat.st_size,
        "bounds": BOUNDS,
        "tile_size": TILE_SIZE,
        "min_zoom": TILE_MIN_ZOOM,
        "max_zoom": TILE_MAX_ZOOM,
        "value_min": vmin,
        "value_max": vmax,
        "raster_scale": VALUE_RASTER_SCALE,
        "url_template": "./heatmap_value_tiles/{z}/{x}/{y}.png",
    }
    if VALUE_TILE_MANIFEST.exists():
        try:
            existing = json.loads(VALUE_TILE_MANIFEST.read_text(encoding="utf-8"))
            if existing == manifest:
                return manifest
        except json.JSONDecodeError:
            pass

    if VALUE_TILE_DIR.exists():
        shutil.rmtree(VALUE_TILE_DIR)
    VALUE_TILE_DIR.mkdir(parents=True, exist_ok=True)

    (south, west), (north, east) = BOUNDS
    nx = int(main_metadata["raster_bins_x"])
    ny = int(main_metadata["raster_bins_y"])

    pred = pd.read_csv(MAIN_PREDICTIONS, usecols=["longitude", "latitude", "tmrt_pred"])
    lon = pd.to_numeric(pred["longitude"], errors="coerce").to_numpy(dtype=float)
    lat = pd.to_numeric(pred["latitude"], errors="coerce").to_numpy(dtype=float)
    val = pd.to_numeric(pred["tmrt_pred"], errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(lon) & np.isfinite(lat) & np.isfinite(val)
    lon, lat, val = lon[mask], lat[mask], val[mask]

    sums, _, _ = np.histogram2d(
        lat,
        lon,
        bins=[ny, nx],
        range=[[south, north], [west, east]],
        weights=val,
    )
    counts, _, _ = np.histogram2d(lat, lon, bins=[ny, nx], range=[[south, north], [west, east]])
    raster = np.divide(sums, counts, out=np.full_like(sums, np.nan), where=counts > 0)
    finite = np.isfinite(raster)
    normalized = np.clip((raster - vmin) / max(vmax - vmin, 1e-9), 0.0, 1.0)
    gray = np.where(finite, np.rint(normalized * 255), 0).astype(np.uint8)
    alpha = np.where(finite, 255, 0).astype(np.uint8)
    value_rgba = np.dstack([np.flipud(gray), np.flipud(gray), np.flipud(gray), np.flipud(alpha)])
    value_img = Image.fromarray(value_rgba, mode="RGBA")
    if VALUE_RASTER_SCALE > 1:
        value_img = value_img.resize(
            (value_img.width * VALUE_RASTER_SCALE, value_img.height * VALUE_RASTER_SCALE),
            Image.Resampling.BILINEAR,
        )

    src_w, src_h = value_img.size
    for zoom in range(TILE_MIN_ZOOM, TILE_MAX_ZOOM + 1):
        nw_x, nw_y = _world_xy(north, west, zoom)
        se_x, se_y = _world_xy(south, east, zoom)
        x_start = math.floor(nw_x / TILE_SIZE)
        x_end = math.floor(se_x / TILE_SIZE)
        y_start = math.floor(nw_y / TILE_SIZE)
        y_end = math.floor(se_y / TILE_SIZE)

        for x in range(x_start, x_end + 1):
            x0 = x * TILE_SIZE
            x1 = (x + 1) * TILE_SIZE
            ix0 = max(x0, nw_x)
            ix1 = min(x1, se_x)
            if ix1 <= ix0:
                continue

            zoom_dir = VALUE_TILE_DIR / str(zoom) / str(x)
            zoom_dir.mkdir(parents=True, exist_ok=True)

            for y in range(y_start, y_end + 1):
                y0 = y * TILE_SIZE
                y1 = (y + 1) * TILE_SIZE
                iy0 = max(y0, nw_y)
                iy1 = min(y1, se_y)
                if iy1 <= iy0:
                    continue

                sx0 = (ix0 - nw_x) / (se_x - nw_x) * src_w
                sx1 = (ix1 - nw_x) / (se_x - nw_x) * src_w
                sy0 = (iy0 - nw_y) / (se_y - nw_y) * src_h
                sy1 = (iy1 - nw_y) / (se_y - nw_y) * src_h

                crop = value_img.crop((sx0, sy0, sx1, sy1))
                dw = max(1, round(ix1 - ix0))
                dh = max(1, round(iy1 - iy0))
                crop = crop.resize((dw, dh), Image.Resampling.BILINEAR)

                tile = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
                tile.alpha_composite(crop, (round(ix0 - x0), round(iy0 - y0)))
                tile.save(zoom_dir / f"{y}.png", format="PNG", optimize=True)

    VALUE_TILE_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def build_tracks() -> dict:
    if not ROUTE_PREDICTIONS.exists() or not CLEAN_NOZEROS.exists():
        return {
            "source": str(CLEAN_NOZEROS.relative_to(ROOT)),
            "items": [],
            "scale": {"vmin": None, "vmax": None},
        }

    track_ids = {track["id"] for track in TRACKS}
    geom_frames = []
    geom_cols = ["track_id", "section_id", "point_id", "lon_ontrack", "lat_ontrack", "tmrt"]
    for path in sorted(CLEAN_NOZEROS.glob("*.csv")):
        geom_frames.append(pd.read_csv(path, usecols=geom_cols))
    if not geom_frames:
        return {
            "source": str(CLEAN_NOZEROS.relative_to(ROOT)),
            "items": [],
            "scale": {"vmin": None, "vmax": None},
        }

    geometry = pd.concat(geom_frames, ignore_index=True)
    geometry["track_id"] = geometry["track_id"].astype(str).str.lower()
    geometry = geometry[geometry["track_id"].isin(track_ids)]
    geometry["tmrt"] = pd.to_numeric(geometry["tmrt"], errors="coerce")
    geometry = geometry.dropna(subset=["lon_ontrack", "lat_ontrack", "section_id", "point_id", "tmrt"])
    geometry["section_id"] = pd.to_numeric(geometry["section_id"], errors="coerce")
    geometry["point_id"] = pd.to_numeric(geometry["point_id"], errors="coerce")
    geometry["lon_ontrack"] = pd.to_numeric(geometry["lon_ontrack"], errors="coerce")
    geometry["lat_ontrack"] = pd.to_numeric(geometry["lat_ontrack"], errors="coerce")
    geometry = geometry.dropna(subset=["lon_ontrack", "lat_ontrack", "section_id", "point_id"])

    geom_points = (
        geometry.groupby(["track_id", "section_id", "point_id"], as_index=False)
        .agg(
            lon=("lon_ontrack", "median"),
            lat=("lat_ontrack", "median"),
            tmrt_observed=("tmrt", "median"),
        )
    )

    pred_cols = ["track_id", "section_id", "point_id", "tmrt_pred"]
    predictions = pd.read_csv(ROUTE_PREDICTIONS, usecols=pred_cols)
    predictions["track_id"] = predictions["track_id"].astype(str).str.lower()
    predictions = predictions[predictions["track_id"].isin(track_ids)]
    predictions["section_id"] = pd.to_numeric(predictions["section_id"], errors="coerce")
    predictions["point_id"] = pd.to_numeric(predictions["point_id"], errors="coerce")
    predictions["tmrt_pred"] = pd.to_numeric(predictions["tmrt_pred"], errors="coerce")
    predictions = predictions.dropna(subset=["section_id", "point_id", "tmrt_pred"])
    pred_points = (
        predictions.groupby(["track_id", "section_id", "point_id"], as_index=False)
        .agg(
            tmrt_pred=("tmrt_pred", "median"),
        )
    )

    points = geom_points.merge(pred_points, on=["track_id", "section_id", "point_id"], how="inner")
    points["tmrt_error"] = points["tmrt_pred"] - points["tmrt_observed"]
    points = points.sort_values(["track_id", "section_id", "point_id"])
    if points.empty:
        return {
            "source": str(CLEAN_NOZEROS.relative_to(ROOT)),
            "items": [],
            "scale": {"vmin": None, "vmax": None},
        }

    scale = {
        "pred": {
            "vmin": _as_clean_float(points["tmrt_pred"].quantile(0.05), 2),
            "vmax": _as_clean_float(points["tmrt_pred"].quantile(0.95), 2),
        },
        "observed": {
            "vmin": _as_clean_float(points["tmrt_observed"].quantile(0.05), 2),
            "vmax": _as_clean_float(points["tmrt_observed"].quantile(0.95), 2),
        },
        "error": {
            "vmin": _as_clean_float(points["tmrt_error"].quantile(0.05), 2),
            "vmax": _as_clean_float(points["tmrt_error"].quantile(0.95), 2),
        },
    }

    tracks = []
    for track in TRACKS:
        track_points = points[points["track_id"] == track["id"]]
        if track_points.empty:
            continue

        step = max(1, math.ceil(len(track_points) / MAX_POINTS_PER_TRACK))
        sections = []
        for section_id, section in track_points.groupby("section_id", sort=True):
            sampled = section.iloc[::step]
            if not sampled.empty and sampled.index[-1] != section.index[-1]:
                sampled = pd.concat([sampled, section.tail(1)])
            sampled = sampled.drop_duplicates(subset=["lon", "lat"], keep="first")
            if len(sampled) < 2:
                continue

            route_points = [
                [
                    _as_clean_float(row.lon, 6),
                    _as_clean_float(row.lat, 6),
                    _as_clean_float(row.tmrt_pred, 2),
                    _as_clean_float(row.tmrt_observed, 2),
                    _as_clean_float(row.tmrt_error, 2),
                ]
                for row in sampled.itertuples(index=False)
            ]
            sections.append({"id": str(section_id), "points": route_points})

        tracks.append(
            {
                **track,
                "label": f"Parcours {track['order']}",
                "n_points_full": int(len(track_points)),
                "n_points_drawn": int(sum(len(section["points"]) for section in sections)),
                "tmrt_min": _as_clean_float(track_points["tmrt_pred"].min(), 2),
                "tmrt_median": _as_clean_float(track_points["tmrt_pred"].median(), 2),
                "tmrt_max": _as_clean_float(track_points["tmrt_pred"].max(), 2),
                "tmrt_observed_median": _as_clean_float(track_points["tmrt_observed"].median(), 2),
                "tmrt_error_median": _as_clean_float(track_points["tmrt_error"].median(), 2),
                "sections": sections,
            }
        )

    return {
        "source": f"{CLEAN_NOZEROS.relative_to(ROOT)} + {ROUTE_PREDICTIONS.relative_to(ROOT)}",
        "value_label": "Tmrt predite sur coordonnees GPS ontrack",
        "scale": scale,
        "items": tracks,
    }


def build_payload() -> dict:
    metadata = json.loads(METADATA.read_text(encoding="utf-8")) if METADATA.exists() else {}
    main_metadata = json.loads(MAIN_METADATA.read_text(encoding="utf-8"))
    tile_manifest = ensure_heatmap_tiles()
    value_tile_manifest = ensure_value_tiles(main_metadata)

    return {
        "title": "PICOPATT - carte Tmrt",
        "model": main_metadata["model"],
        "bounds": BOUNDS,
        "meters_per_pixel": metadata.get("meters_per_pixel", 10.0),
        "n_grid_points": int(main_metadata["n_predicted_points"]),
        "n_train_rows": main_metadata.get("n_train_rows") or metadata.get("n_train_rows"),
        "vmin": float(main_metadata["tmrt_pred_min"]),
        "vmax": float(main_metadata["tmrt_pred_max"]),
        "color_vmin": float(main_metadata["tmrt_pred_p05"]),
        "color_vmax": float(main_metadata["tmrt_pred_p95"]),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "main_heatmap": {
            "title": "Carte de la Tmrt prédite via embedding AlphaEarth (10 m)",
            "image_url": "../../prediction/figures/heatmap_tmrt_montpellier_10m/tmrt_montpellier_10m_overlay_catboost_smooth2x.webp",
            "export_url": "../../prediction/figures/heatmap_tmrt_montpellier_10m/tmrt_montpellier_10m_overlay_catboost_smooth2x.webp",
            "tile_url_template": tile_manifest["url_template"],
            "value_tile_url_template": value_tile_manifest["url_template"],
            "tile_min_zoom": tile_manifest["min_zoom"],
            "tile_max_zoom": tile_manifest["max_zoom"],
            "n_predicted_points": int(main_metadata["n_predicted_points"]),
            "tmrt_min": float(main_metadata["tmrt_pred_min"]),
            "tmrt_median": float(main_metadata["tmrt_pred_median"]),
            "tmrt_max": float(main_metadata["tmrt_pred_max"]),
            "tmrt_p05": float(main_metadata["tmrt_pred_p05"]),
            "tmrt_p95": float(main_metadata["tmrt_pred_p95"]),
            "model": main_metadata["model"],
            "raster_bins_x": int(main_metadata["raster_bins_x"]),
            "raster_bins_y": int(main_metadata["raster_bins_y"]),
        },
        "routes": build_tracks(),
    }


def main() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    text = "window.PICOPATT_DATA = "
    text += json.dumps(payload, ensure_ascii=False, indent=2)
    text += ";\n"
    DATA_JS.write_text(text, encoding="utf-8")
    print(DATA_JS)


if __name__ == "__main__":
    main()
