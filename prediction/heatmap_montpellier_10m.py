from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from picopatt.io import create_folder, load_all  # noqa: E402


TARGET = "tmrt"
BANDS = [f"A{i:02d}" for i in range(64)]
MF_BASE_CANDIDATES = [
    "T",
    "U",
    "PSTAT",
    "FF",
    "DD",
    "FXI",
    "RR1",
    "N",
    "INS",
    "GLO",
    "DIR",
    "DIF",
    "WW",
    "VV",
]
HGBR_TUNED = {
    "max_iter": 500,
    "learning_rate": 0.05,
    "max_depth": 8,
    "min_samples_leaf": 30,
    "l2_regularization": 0.1,
}


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_picopatt_with_alphaearth(root: Path) -> pd.DataFrame:
    data_dir = root / "data" / "processed" / "picopatt" / "clean_nozeros"
    ae_dir = root / "data" / "processed" / "alphaearth" / "alphaearth_data"
    raw_path = ae_dir / "alphaearth_A00_A63_points.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Fichier AlphaEarth PICOPATT manquant: {raw_path}")

    bd = load_all(data_dir, False).copy()
    bd["lon_std"] = safe_numeric(bd["lon_ontrack"])
    bd["lat_std"] = safe_numeric(bd["lat_ontrack"])
    bd = bd.dropna(subset=["lon_std", "lat_std"])
    bd = bd[(bd["lon_std"].between(-180, 180)) & (bd["lat_std"].between(-90, 90))]
    bd = bd.reset_index(drop=True)
    bd["uid"] = bd.index.astype(int)

    aef_raw = pd.read_csv(raw_path, usecols=["uid"] + BANDS)
    if len(aef_raw) != len(bd):
        raise ValueError(
            "Alignement uid douteux: "
            f"{len(bd):,} lignes PICOPATT contre {len(aef_raw):,} lignes AlphaEarth."
        )
    return bd.merge(aef_raw, on="uid", how="left", validate="one_to_one")


def load_meteofrance(root: Path) -> pd.DataFrame:
    mf_dir = root / "data" / "processed" / "meteofrance"
    candidates = sorted(mf_dir.glob("mf_montpellier_*.csv"))
    if not candidates:
        raise FileNotFoundError(f"Aucun fichier MeteoFrance trouve dans {mf_dir}")
    wx = pd.read_csv(candidates[-1], sep=";", dtype=str)
    wx["DATE"] = pd.to_datetime(wx["DATE"], format="%Y%m%d%H", utc=True)
    for col in [c for c in wx.columns if c not in ["POSTE", "DATE"]]:
        wx[col] = wx[col].str.replace(",", ".", regex=False).replace({"": None})
        wx[col] = pd.to_numeric(wx[col], errors="coerce")
    return wx.sort_values("DATE").reset_index(drop=True)


def merge_nearest_weather(df: pd.DataFrame, wx: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp", TARGET])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("Europe/Paris")
    df["timestamp_utc"] = df["timestamp"].dt.tz_convert("UTC")

    return pd.merge_asof(
        df.sort_values("timestamp_utc"),
        wx.sort_values("DATE"),
        left_on="timestamp_utc",
        right_on="DATE",
        direction="nearest",
        tolerance=pd.Timedelta("30min"),
    )


def build_mf_features(train: pd.DataFrame) -> list[str]:
    mf_base = [c for c in MF_BASE_CANDIDATES if c in train.columns]
    mf_q = [f"Q{c}" for c in mf_base if f"Q{c}" in train.columns]
    missing_flags: list[str] = []
    for col in mf_base:
        flag = f"{col}_missing"
        train[flag] = train[col].isna().astype(int)
        missing_flags.append(flag)
    features = mf_base + mf_q + missing_flags
    return [c for c in features if train[c].notna().any()]


def add_time_and_extra_features(df: pd.DataFrame, include_coordinates: bool) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    ts = df["timestamp_utc"]
    df["hour_sin"] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df["doy_sin"] = np.sin(2 * np.pi * ts.dt.dayofyear / 365)
    df["doy_cos"] = np.cos(2 * np.pi * ts.dt.dayofyear / 365)

    # Meme fallback que le notebook quand pvlib n'est pas disponible.
    df["solar_hour_angle"] = (ts.dt.hour + ts.dt.minute / 60 - 12) * 15
    df["is_daytime"] = (df["solar_hour_angle"].abs() < 90).astype(int)
    df["solar_elev_sq"] = np.maximum(0, 90 - np.abs(df["solar_hour_angle"])) ** 2
    df["min_sin"] = np.sin(2 * np.pi * ts.dt.minute / 60)
    df["min_cos"] = np.cos(2 * np.pi * ts.dt.minute / 60)

    extra = [
        "hour_sin",
        "hour_cos",
        "doy_sin",
        "doy_cos",
        "solar_hour_angle",
        "is_daytime",
        "solar_elev_sq",
        "min_sin",
        "min_cos",
    ]

    if include_coordinates:
        df["lat_feat"] = safe_numeric(df["lat_std"])
        df["lon_feat"] = safe_numeric(df["lon_std"])
        extra.extend(["lat_feat", "lon_feat"])

    if {"T", "U"}.issubset(df.columns):
        t = safe_numeric(df["T"]).fillna(safe_numeric(df["T"]).median())
        u = safe_numeric(df["U"]).fillna(safe_numeric(df["U"]).median())
        df["apparent_T"] = t - 0.4 * (t - 10) * (1 - u / 100)
        extra.append("apparent_T")
    if "T" in df.columns:
        df["T_x_elev"] = safe_numeric(df["T"]).fillna(0) * np.maximum(0, 90 - np.abs(df["solar_hour_angle"]))
        extra.append("T_x_elev")
    if {"FF", "GLO"}.issubset(df.columns):
        df["FF_x_GLO"] = safe_numeric(df["FF"]).fillna(0) * safe_numeric(df["GLO"]).fillna(0)
        extra.append("FF_x_GLO")
    if "N" in df.columns:
        df["N_x_elev"] = safe_numeric(df["N"]).fillna(0) * np.maximum(0, 90 - np.abs(df["solar_hour_angle"]))
        extra.append("N_x_elev")
    if "GLO" in df.columns:
        df["GLO_x_elev"] = safe_numeric(df["GLO"]).fillna(0) * np.maximum(0, 90 - np.abs(df["solar_hour_angle"]))
        extra.append("GLO_x_elev")
    if {"N", "GLO"}.issubset(df.columns):
        df["N_x_GLO"] = safe_numeric(df["N"]).fillna(0) * safe_numeric(df["GLO"]).fillna(0)
        extra.append("N_x_GLO")
    if {"T", "GLO"}.issubset(df.columns):
        df["T_x_GLO"] = safe_numeric(df["T"]).fillna(0) * safe_numeric(df["GLO"]).fillna(0)
        extra.append("T_x_GLO")

    return df, extra


def train_model(
    root: Path,
    include_coordinates: bool,
    model_type: str,
) -> tuple[Any, list[str], dict[str, float], dict[str, Any]]:
    base = load_picopatt_with_alphaearth(root)
    wx = load_meteofrance(root)
    dfm = merge_nearest_weather(base, wx)
    train = dfm.dropna(subset=[TARGET, "DATE"]).copy()
    train["day_utc"] = train["timestamp_utc"].dt.floor("D")

    mf_features = build_mf_features(train)
    train, extra_features = add_time_and_extra_features(train, include_coordinates=include_coordinates)

    raw_features = [c for c in BANDS if c in train.columns and train[c].notna().any()]
    feature_cols = mf_features + raw_features + extra_features
    feature_cols = [c for c in feature_cols if c in train.columns and train[c].notna().any()]

    X = train[feature_cols].apply(safe_numeric).replace([np.inf, -np.inf], np.nan)
    y = safe_numeric(train[TARGET]).astype(float)
    if model_type == "catboost":
        from catboost import CatBoostRegressor

        model = CatBoostRegressor(
            loss_function="RMSE",
            eval_metric="RMSE",
            iterations=541,
            depth=6,
            learning_rate=0.05,
            l2_leaf_reg=8,
            random_seed=42,
            allow_writing_files=False,
            verbose=False,
        )
        model.fit(X, y)
        model_label = "CatBoostRegressor from Prediction.ipynb best config, retrained on all PICOPATT"
    else:
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("reg", HistGradientBoostingRegressor(random_state=42, **HGBR_TUNED.copy())),
            ]
        )
        model.fit(X, y)
        model_label = "HistGradientBoostingRegressor tuned from Prediction.ipynb, retrained on all PICOPATT"

    scenario = {
        col: float(safe_numeric(train[col]).median())
        for col in feature_cols
        if col not in raw_features and safe_numeric(train[col]).notna().any()
    }
    meta = {
        "model": model_label,
        "n_train_rows": int(len(train)),
        "n_features": int(len(feature_cols)),
        "n_mf_features": int(len(mf_features)),
        "n_alphaearth_raw_features": int(len(raw_features)),
        "n_extra_features": int(len(extra_features)),
        "include_coordinates": bool(include_coordinates),
        "feature_columns": feature_cols,
    }
    return model, feature_cols, scenario, meta

def add_scenario_columns(chunk: pd.DataFrame, feature_cols: list[str], scenario: dict[str, float], include_coordinates: bool) -> pd.DataFrame:
    out = chunk.copy()
    if include_coordinates:
        out["lon_feat"] = safe_numeric(out["longitude"])
        out["lat_feat"] = safe_numeric(out["latitude"])
    for col in feature_cols:
        if col not in out.columns:
            out[col] = scenario.get(col, np.nan)
    return out


def predict_grid(
    root: Path,
    model: Any,
    feature_cols: list[str],
    scenario: dict[str, float],
    include_coordinates: bool,
    model_type: str,
    chunksize: int,
) -> pd.DataFrame:
    grid_path = root / "data" / "processed" / "alphaearth" / "alphaearth_data" / "mtp_points.csv"
    if not grid_path.exists():
        raise FileNotFoundError(f"Grille AlphaEarth Montpellier manquante: {grid_path}")

    out_dir = root / "data" / "processed" / "prediction" / "heatmap_tmrt_montpellier_10m"
    create_folder(out_dir)
    pred_csv = out_dir / f"tmrt_montpellier_10m_predictions_{model_type}.csv"

    usecols = ["uid", "longitude", "latitude"] + BANDS
    header = True
    frames: list[pd.DataFrame] = []
    total = 0

    for chunk in pd.read_csv(grid_path, usecols=usecols, chunksize=chunksize):
        pred_input = add_scenario_columns(chunk, feature_cols, scenario, include_coordinates=include_coordinates)
        X_grid = pred_input[feature_cols].apply(safe_numeric).replace([np.inf, -np.inf], np.nan)
        pred = model.predict(X_grid)
        out = chunk[["uid", "longitude", "latitude"]].copy()
        out["tmrt_pred"] = pred
        out.to_csv(pred_csv, index=False, mode="w" if header else "a", header=header)
        header = False
        frames.append(out)
        total += len(out)
        print(f"Predictions grille: {total:,} points", flush=True)

    return pd.concat(frames, ignore_index=True)


def plot_heatmap(pred_df: pd.DataFrame, root: Path, meta: dict[str, Any]) -> tuple[Path, Path]:
    out_dir = root / "data" / "processed" / "prediction" / "heatmap_tmrt_montpellier_10m"
    fig_dir = root / "prediction" / "figures" / "heatmap_tmrt_montpellier_10m"
    create_folder(out_dir)
    create_folder(fig_dir)

    lon = safe_numeric(pred_df["longitude"]).to_numpy(dtype=float)
    lat = safe_numeric(pred_df["latitude"]).to_numpy(dtype=float)
    val = safe_numeric(pred_df["tmrt_pred"]).to_numpy(dtype=float)
    mask = np.isfinite(lon) & np.isfinite(lat) & np.isfinite(val)
    lon, lat, val = lon[mask], lat[mask], val[mask]

    mean_lat = float(np.nanmean(lat))
    width_m = (float(np.nanmax(lon)) - float(np.nanmin(lon))) * 111_320.0 * math.cos(math.radians(mean_lat))
    height_m = (float(np.nanmax(lat)) - float(np.nanmin(lat))) * 110_540.0
    nx = max(200, int(round(width_m / 10.0)))
    ny = max(200, int(round(height_m / 10.0)))

    sums, y_edges, x_edges = np.histogram2d(lat, lon, bins=[ny, nx], weights=val)
    counts, _, _ = np.histogram2d(lat, lon, bins=[ny, nx])
    raster = np.divide(sums, counts, out=np.full_like(sums, np.nan), where=counts > 0)

    suffix = "catboost" if "CatBoost" in meta["model"] else "histgbr"
    png = fig_dir / f"tmrt_montpellier_10m_heatmap_{suffix}.png"
    plt.figure(figsize=(12, 9))
    im = plt.imshow(
        raster,
        origin="lower",
        extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]],
        cmap="inferno",
        aspect="auto",
    )
    plt.colorbar(im, label="TMRT predite")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    coord_note = "avec lon/lat" if meta["include_coordinates"] else "sans lon/lat directes"
    plt.title(f"TMRT predite sur Montpellier - grille AlphaEarth 10 m ({coord_note})")
    plt.tight_layout()
    plt.savefig(png, dpi=300)
    plt.close()

    overlay_png = fig_dir / f"tmrt_montpellier_10m_overlay_{suffix}.png"
    html = fig_dir / f"tmrt_montpellier_10m_interactive_{suffix}.html"
    save_interactive_map(raster, x_edges, y_edges, overlay_png, html)

    meta_path = out_dir / f"tmrt_montpellier_10m_metadata_{suffix}.json"
    meta = {
        **meta,
        "n_predicted_points": int(len(pred_df)),
        "lon_min": float(np.nanmin(lon)),
        "lon_max": float(np.nanmax(lon)),
        "lat_min": float(np.nanmin(lat)),
        "lat_max": float(np.nanmax(lat)),
        "raster_bins_x": int(nx),
        "raster_bins_y": int(ny),
        "tmrt_pred_min": float(np.nanmin(val)),
        "tmrt_pred_p05": float(np.nanpercentile(val, 5)),
        "tmrt_pred_median": float(np.nanmedian(val)),
        "tmrt_pred_p95": float(np.nanpercentile(val, 95)),
        "tmrt_pred_max": float(np.nanmax(val)),
        "figure": str(png),
        "interactive_map": str(html),
        "transparent_overlay": str(overlay_png),
        "predictions_csv": str(out_dir / f"tmrt_montpellier_10m_predictions_{suffix}.csv"),
        "scenario": meta.get("scenario", {}),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return png, meta_path


def save_interactive_map(
    raster: np.ndarray,
    x_edges: np.ndarray,
    y_edges: np.ndarray,
    overlay_png: Path,
    html: Path,
) -> None:
    import folium
    from branca.colormap import LinearColormap

    vmin = float(np.nanpercentile(raster, 2))
    vmax = float(np.nanpercentile(raster, 98))
    clipped = np.clip(raster, vmin, vmax)
    norm = (clipped - vmin) / max(vmax - vmin, 1e-9)

    cmap = plt.get_cmap("inferno")
    rgba = cmap(norm)
    rgba[..., 3] = np.where(np.isfinite(raster), 0.68, 0.0)
    rgba_u8 = (rgba * 255).astype(np.uint8)
    Image.fromarray(np.flipud(rgba_u8), mode="RGBA").save(overlay_png)

    south = float(y_edges[0])
    north = float(y_edges[-1])
    west = float(x_edges[0])
    east = float(x_edges[-1])
    center = [(south + north) / 2, (west + east) / 2]

    m = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap", control_scale=True)
    folium.raster_layers.ImageOverlay(
        image=str(overlay_png.resolve()),
        bounds=[[south, west], [north, east]],
        opacity=0.72,
        name="TMRT predite 10 m",
        interactive=True,
        cross_origin=False,
    ).add_to(m)
    colormap = LinearColormap(
        colors=["#000004", "#2c115f", "#721f81", "#b73779", "#f1605d", "#feb078", "#fcffa4"],
        vmin=vmin,
        vmax=vmax,
    )
    colormap.caption = "TMRT predite"
    colormap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[south, west], [north, east]])
    m.save(str(html))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Predire TMRT sur la grille AlphaEarth Montpellier 10 m.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--chunksize", type=int, default=50_000)
    parser.add_argument("--model", choices=["histgbr", "catboost"], default="catboost")
    parser.add_argument(
        "--plot-existing",
        type=Path,
        default=None,
        help="CSV predictions deja calcule avec uid, longitude, latitude, tmrt_pred; reconstruit seulement les cartes.",
    )
    parser.add_argument(
        "--include-coordinates",
        action="store_true",
        help="Reproduit plus fidelement le notebook ameliore, mais la carte devient moins purement generalisable.",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if args.plot_existing is not None:
        pred_df = pd.read_csv(args.plot_existing)
        meta = {
            "model": "CatBoostRegressor from Prediction.ipynb best config, retrained on all PICOPATT"
            if args.model == "catboost"
            else "HistGradientBoostingRegressor tuned from Prediction.ipynb, retrained on all PICOPATT",
            "n_train_rows": None,
            "n_features": None,
            "n_mf_features": None,
            "n_alphaearth_raw_features": None,
            "n_extra_features": None,
            "include_coordinates": bool(args.include_coordinates),
            "feature_columns": [],
            "scenario": {},
        }
    else:
        model, feature_cols, scenario, meta = train_model(
            root,
            include_coordinates=args.include_coordinates,
            model_type=args.model,
        )
        meta["scenario"] = scenario
        pred_df = predict_grid(
            root,
            model,
            feature_cols,
            scenario,
            include_coordinates=args.include_coordinates,
            model_type=args.model,
            chunksize=args.chunksize,
        )
    png, meta_path = plot_heatmap(pred_df, root, meta)
    print("Heatmap terminee.")
    print(f"Figure: {png}")
    print(f"Metadonnees: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
