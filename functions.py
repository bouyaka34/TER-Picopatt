from pathlib import Path
import re, unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from zoneinfo import ZoneInfo  

# CODE
def create_folder(path):
    """Crée le dossier si nécessaire avant d'enregistrer un fichier."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

# NETTOYAGE et LECTURE des données
def strip_accents(s):
    """Supprime les accents d'une chaîne."""
    if pd.isna(s):
        return s
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s)) if not unicodedata.combining(c))


def normalize_track(x):
    """Nettoie et unifie les noms de parcours."""
    if pd.isna(x):
        return np.nan
    x = strip_accents(str(x)).lower().strip()
    x = x.replace("boulevard", "boulevards")
    if "antigone" in x:
        return "antigone"
    if "boulevards" in x:
        return "boulevards"
    if "ecusson" in x:
        return "ecusson"
    return np.nan


def infer_track_from_filename(name: str):
    """Déduit le parcours à partir du nom du fichier."""
    n = strip_accents(name.lower())
    if "antigone" in n:
        return "antigone"
    if "boulevard" in n:
        return "boulevards"
    if "ecusson" in n:
        return "ecusson"
    return np.nan


def parse_fr_ts(s):
    """Convertit les dates au format français en datetime."""
    return pd.to_datetime(s, errors="coerce", dayfirst=True)


def assign_mslot_from_filename_winter(file_name: str) -> str:
    """
    Détermine le M_slot (M1..M4) à partir du nom du fichier (hiver uniquement).
    Format : picopatt_montpellier_<parcours>_YYYYMMDD_HHMM.csv
    """
    # Extraire la date et l'heure
    m = re.search(r"(\d{8})_(\d{4})", file_name)
    if not m:
        return "UNK"

    date_part, time_part = m.groups()
    dt_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:]}:00"
    dt = pd.Timestamp(dt_str).tz_localize(ZoneInfo("Europe/Paris"))

    hour = dt.hour

    # Attribution M1–M4 
    if 8 <= hour < 11:
        return "M1"
    elif 11 <= hour < 14:
        return "M2"
    elif 14 <= hour < 17:
        return "M3"
    elif 17 <= hour < 20:
        return "M4"
    else:
        return "UNK"
    

def read_any(p: Path) -> pd.DataFrame:
    """Lit un fichier CSV ou Excel avec tentative sur plusieurs séparateurs."""
    if p.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(p)
    else:
        df = None
        for sep in [",", ";", "\t"]:
            try:
                temp = pd.read_csv(p, sep=sep)
                if temp.shape[1] >= 5:
                    df = temp
                    break
            except Exception:
                continue
        if df is None:
            raise ValueError(f"Impossible de lire le fichier : {p}")
    df["__source_file"] = p.name
    return df


def extract_info_from_filename(name: str):
    """
    Extrait la date (YYYY-MM-DD) et le M_slot à partir du nom de fichier.
    Exemple : 20241107_1122 -> 2024-11-07 et M2 (car 11h22 ≈ M2 en hiver)
    """
    m = re.search(r"(\d{8})_(\d{4})", name)
    if not m:
        return None, None

    date_part, time_part = m.groups()
    date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
    hh = int(time_part[:2])

    # Attribution M_slot (hiver)
    if 8 <= hh < 11:
        mslot = "M1"
    elif 11 <= hh < 14:
        mslot = "M2"
    elif 14 <= hh < 17:
        mslot = "M3"
    elif 17 <= hh < 20:
        mslot = "M4"
    else:
        mslot = "UNK"

    return date_str, mslot


def load_all(data_dir: Path) -> pd.DataFrame:
    """Charge les fichiers et attribue la date et le M_slot selon le nom du fichier."""
    paths = sorted([p for p in data_dir.rglob("*") if p.suffix.lower() in (".csv", ".xlsx", ".xls")])
    assert paths, f"Aucun fichier trouvé dans {data_dir.resolve()}"

    frames = []
    for p in paths:
        df = read_any(p)

        #  Extrait infos depuis le nom du fichier
        date_str, mslot = extract_info_from_filename(p.name)
        df["date"] = pd.to_datetime(date_str).date() if date_str else np.nan
        df["M_slot"] = mslot

        # Déduit le parcours
        trk_file = infer_track_from_filename(p.name)
        df["track_id"] = trk_file

        frames.append(df)

        print(f"{p.name:<50} ->  {date_str}  {mslot}")

    return pd.concat(frames, ignore_index=True, sort=False) 


# STATS
def summary_stats(df, cols):
    # Calcule les statistiques descriptives principales
    q = df[cols].quantile([.10, .25, .50, .75, .90], numeric_only=True).T
    return pd.DataFrame({
        "mean": df[cols].mean(numeric_only=True),
        "std": df[cols].std(numeric_only=True),
        "min": df[cols].min(numeric_only=True),
        "p10": q[.10], "p25": q[.25], "median": q[.50],
        "p75": q[.75], "p90": q[.90],
        "max": df[cols].max(numeric_only=True),
    })

def circular_mean_deg(s):
    # Moyenne circulaire pour les angles (direction du vent)
    r = np.deg2rad(s.dropna().astype(float) % 360.0)
    if r.size == 0: return np.nan
    ang = np.arctan2(np.sin(r).mean(), np.cos(r).mean())
    return np.rad2deg(ang) % 360.0