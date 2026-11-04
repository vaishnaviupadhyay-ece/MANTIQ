"""
MANTIQ data service.

"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.config import (
    BEARINGS,
    FEATURES_CSV,
    TIMELINE_CSV,
    TIMESTAMP_FORMAT,
    TRAIN_FRACTION,
    bearing_channels,
)

# Same order as src/bearing_analysis.py
FEATURE_NAMES = ("rms", "std", "peak", "kurtosis", "crest")


class DataError(Exception):
    """A data or model file is missing or invalid. The message is safe to show on screen."""


def feature_columns(bearing: int) -> list:
    """The 10 feature columns of one bearing (two channels x five features)."""
    columns = []
    for channel in bearing_channels(bearing):
        columns.extend(f"ch{channel}_{name}" for name in FEATURE_NAMES)
    return columns


def _read_csv(path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise DataError(
            f"{label} was not found at {path}. "
            "Check that the file exists and has not been moved or renamed."
        )
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DataError(f"{label} could not be read ({exc}). The file may be corrupted.") from exc
    if df.empty:
        raise DataError(f"{label} is empty.")
    return df


def _add_time(df: pd.DataFrame, label: str, number_recordings: bool) -> pd.DataFrame:
    """Add a real datetime column 'time' (original dataset time, not today's date).
    The text 'timestamp' column is kept unchanged because it is the join key."""
    if "timestamp" not in df.columns:
        raise DataError(f"{label} has no 'timestamp' column.")
    parsed = pd.to_datetime(df["timestamp"].astype(str), format=TIMESTAMP_FORMAT, errors="coerce")
    bad = int(parsed.isna().sum())
    if bad:
        raise DataError(
            f"{label}: {bad} timestamp(s) do not match the expected format YYYY.MM.DD.HH.MM.SS."
        )
    df = df.copy()
    df["time"] = parsed
    if number_recordings:
        df["recording"] = np.arange(1, len(df) + 1)  # 1-based recording number
    return df


def load_features() -> pd.DataFrame:
    """All recordings from ims_features.csv, plus 'time' and 'recording' columns."""
    label = "The feature file (ims_features.csv)"
    df = _add_time(_read_csv(FEATURES_CSV, label), "ims_features.csv", number_recordings=True)

    needed = [c for b in BEARINGS for c in feature_columns(b)]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        shown = ", ".join(missing[:6]) + (" ..." if len(missing) > 6 else "")
        raise DataError(f"ims_features.csv is missing {len(missing)} expected column(s): {shown}")

    non_numeric = [c for c in needed if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        shown = ", ".join(non_numeric[:6])
        raise DataError(f"ims_features.csv has non-numeric values in: {shown}")
    return df


def load_timeline() -> pd.DataFrame:
    """The saved anomaly timeline (test period only), plus a 'time' column."""
    label = "The anomaly timeline (bearing_timeline.csv)"
    df = _add_time(_read_csv(TIMELINE_CSV, label), "bearing_timeline.csv", number_recordings=False)

    needed = [f"bearing_{b}_{kind}" for b in BEARINGS for kind in ("score", "anomaly")]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise DataError(f"bearing_timeline.csv is missing expected column(s): {', '.join(missing)}")
    return df


@dataclass(frozen=True)
class SplitInfo:
    """Where the training period ends and the unseen test period begins."""

    n_total: int                 # recordings in ims_features.csv
    n_train: int                 # recordings before the first unseen one
    n_test: int                  # rows in bearing_timeline.csv
    first_test_index: int        # 0-based position of the first unseen recording
    first_test_recording: int    # the same, as a 1-based recording number
    expected_train_count: int    # int(n_total * 0.60), what bearing_analysis.py uses
    aligned: bool                # timeline rows are exactly the last rows of the features file

    @property
    def matches_training_script(self) -> bool:
        return self.first_test_index == self.expected_train_count


def locate_split(features: pd.DataFrame, timeline: pd.DataFrame) -> SplitInfo:
    """Find the first test recording by matching the timeline's first timestamp."""
    first_stamp = timeline["timestamp"].iloc[0]
    hits = np.flatnonzero((features["timestamp"] == first_stamp).to_numpy())
    if len(hits) == 0:
        raise DataError(
            f"The first timestamp of bearing_timeline.csv ({first_stamp}) does not appear in "
            "ims_features.csv, so the two files cannot be lined up."
        )
    first = int(hits[0])
    tail = features["timestamp"].iloc[first:first + len(timeline)].tolist()
    aligned = tail == timeline["timestamp"].tolist()
    return SplitInfo(
        n_total=len(features),
        n_train=first,
        n_test=len(timeline),
        first_test_index=first,
        first_test_recording=first + 1,
        expected_train_count=int(len(features) * TRAIN_FRACTION),
        aligned=aligned,
    )


def data_quality_notes(features: pd.DataFrame) -> list:
    """Plain-language notes about anything unusual in the feature file."""
    notes = []
    if not features["time"].is_monotonic_increasing:
        notes.append("Feature timestamps are not in chronological order.")
    duplicates = int(features["timestamp"].duplicated().sum())
    if duplicates:
        notes.append(f"{duplicates} duplicate timestamp(s) found in ims_features.csv.")
    numeric = features[[c for c in features.columns if c.startswith("ch")]]
    n_inf = int(np.isinf(numeric.to_numpy(dtype=float)).sum())
    n_nan = int(numeric.isna().sum().sum())
    if n_inf or n_nan:
        notes.append(
            f"ims_features.csv contains {n_nan} missing and {n_inf} infinite feature value(s). "
            "They are filled with each model's saved training medians, exactly as in training."
        )
    return notes