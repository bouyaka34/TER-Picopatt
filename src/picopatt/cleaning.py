from __future__ import annotations

import re
import unicodedata
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


def strip_accents(value):
    """Remove accents from a string-like value."""
    if pd.isna(value):
        return value
    return "".join(
        char for char in unicodedata.normalize("NFKD", str(value)) if not unicodedata.combining(char)
    )


def normalize_track(value):
    """Normalize route names to the three Montpellier track ids."""
    if pd.isna(value):
        return np.nan
    text = strip_accents(str(value)).lower().strip()
    text = text.replace("boulevard", "boulevards")
    if "antigone" in text:
        return "antigone"
    if "boulevards" in text:
        return "boulevards"
    if "ecusson" in text:
        return "ecusson"
    return np.nan


def infer_track_from_filename(name: str):
    """Infer the Montpellier track id from a file name."""
    normalized = strip_accents(name.lower())
    if "antigone" in normalized:
        return "antigone"
    if "boulevard" in normalized:
        return "boulevards"
    if "ecusson" in normalized:
        return "ecusson"
    return np.nan


def parse_fr_ts(values):
    """Parse French day-first timestamps."""
    return pd.to_datetime(values, errors="coerce", dayfirst=True)


def assign_mslot_from_filename_winter(file_name: str) -> str:
    """Determine the winter M_slot (M1..M4) from a PICOPATT file name."""
    match = re.search(r"(\d{8})_(\d{4})", file_name)
    if not match:
        return "UNK"

    date_part, time_part = match.groups()
    dt_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:]}:00"
    dt = pd.Timestamp(dt_str).tz_localize(ZoneInfo("Europe/Paris"))
    hour = dt.hour

    if 8 <= hour < 11:
        return "M1"
    if 11 <= hour < 14:
        return "M2"
    if 14 <= hour < 17:
        return "M3"
    if 17 <= hour < 20:
        return "M4"
    return "UNK"


def extract_info_from_filename(name: str):
    """Extract date (YYYY-MM-DD) and winter M_slot from a file name."""
    match = re.search(r"(\d{8})_(\d{4})", name)
    if not match:
        return None, None

    date_part, time_part = match.groups()
    date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
    hour = int(time_part[:2])

    if 8 <= hour < 11:
        mslot = "M1"
    elif 11 <= hour < 14:
        mslot = "M2"
    elif 14 <= hour < 17:
        mslot = "M3"
    elif 17 <= hour < 20:
        mslot = "M4"
    else:
        mslot = "UNK"

    return date_str, mslot
