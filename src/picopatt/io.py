from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from picopatt.cleaning import extract_info_from_filename, infer_track_from_filename


def create_folder(path) -> None:
    """Create a folder and its parents when needed."""
    Path(path).mkdir(parents=True, exist_ok=True)


def read_any(path: Path) -> pd.DataFrame:
    """Read a CSV or Excel file with a few common separators."""
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = None
        for sep in [",", ";", "\t"]:
            try:
                candidate = pd.read_csv(path, sep=sep)
                if candidate.shape[1] >= 5:
                    df = candidate
                    break
            except Exception:
                continue
        if df is None:
            raise ValueError(f"Impossible de lire le fichier : {path}")
    df["fichier_originaire"] = path.name
    return df


def load_all(data_dir: Path, show_print: bool = True) -> pd.DataFrame:
    """Load all PICOPATT CSV/Excel files from a directory tree."""
    data_dir = Path(data_dir)
    paths = sorted(
        path for path in data_dir.rglob("*") if path.suffix.lower() in (".csv", ".xlsx", ".xls")
    )
    if not paths:
        raise FileNotFoundError(f"Aucun fichier trouve dans {data_dir.resolve()}")

    frames = []
    for path in paths:
        try:
            df = read_any(path)
        except Exception as exc:
            print(f"Erreur de lecture pour {path.name} : {exc}")
            continue

        df["fichier_originaire"] = path.name
        date_str, mslot = extract_info_from_filename(path.name)
        df["date"] = pd.to_datetime(date_str).date() if date_str else np.nan
        df["M_slot"] = mslot
        df["track_id"] = infer_track_from_filename(path.name)
        frames.append(df)

        if show_print:
            print(f"{path.name:<50} ->  {date_str}  {mslot}")

    if not frames:
        raise ValueError(f"Aucun fichier exploitable dans {data_dir.resolve()}")

    raw = pd.concat(frames, ignore_index=True, sort=False)
    raw["fichier_originaire"] = raw.get("fichier_originaire", "unknown").astype(str)
    return raw
