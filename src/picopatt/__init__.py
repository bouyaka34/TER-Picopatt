"""Utilities for the PICOPATT TER project."""

from picopatt.cleaning import (
    assign_mslot_from_filename_winter,
    extract_info_from_filename,
    infer_track_from_filename,
    normalize_track,
    parse_fr_ts,
    strip_accents,
)
from picopatt.features import circular_mean_deg, summary_stats
from picopatt.io import create_folder, load_all, read_any

__all__ = [
    "assign_mslot_from_filename_winter",
    "circular_mean_deg",
    "create_folder",
    "extract_info_from_filename",
    "infer_track_from_filename",
    "load_all",
    "normalize_track",
    "parse_fr_ts",
    "read_any",
    "strip_accents",
    "summary_stats",
]
