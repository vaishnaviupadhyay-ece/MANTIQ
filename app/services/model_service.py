"""
MANTIQ model service.

"""

import warnings
from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd

from app.config import BEARINGS, model_path
from app.services.data_service import DataError, SplitInfo

REQUIRED_KEYS = ("model", "scaler", "medians", "feature_columns")


def load_artifacts():
    """Return ({bearing: artifact dict}, [notes]). Raises DataError on any problem."""
    artifacts, notes = {}, []
    for bearing in BEARINGS:
        path = model_path(bearing)
        if not path.exists():
            raise DataError(f"Model file {path.name} was not found in the models folder.")
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                artifact = joblib.load(path)
        except Exception as exc:
            raise DataError(f"Model file {path.name} could not be loaded ({exc}).") from exc
        if not isinstance(artifact, dict) or any(k not in artifact for k in REQUIRED_KEYS):
            raise DataError(
                f"Model file {path.name} does not contain the expected items "
                f"({', '.join(REQUIRED_KEYS)})."
            )
        for item in caught:
            notes.append(f"{path.name}: {item.category.__name__}: {str(item.message)[:160]}")
        artifacts[bearing] = artifact
    return artifacts, notes


def score_recordings(features: pd.DataFrame, artifacts: dict) -> pd.DataFrame:
    """Score ALL recordings (training and test period) for all four bearings in one batch.

    Columns: recording, timestamp, time, then bearing_N_score and bearing_N_anomaly.
    """
    out = pd.DataFrame(
        {
            "recording": features["recording"].to_numpy(),
            "timestamp": features["timestamp"].to_numpy(),
            "time": features["time"].to_numpy(),
        }
    )
    for bearing, artifact in artifacts.items():
        columns = artifact["feature_columns"]
        missing = [c for c in columns if c not in features.columns]
        if missing:
            raise DataError(f"Bearing {bearing}'s model expects columns missing from the features: {missing[:4]}")
        X = features[columns].replace([np.inf, -np.inf], np.nan)
        X = X.fillna(artifact["medians"])
        scaled = artifact["scaler"].transform(X)
        out[f"bearing_{bearing}_score"] = artifact["model"].decision_function(scaled)
        out[f"bearing_{bearing}_anomaly"] = (artifact["model"].predict(scaled) == -1).astype(int)
    return out


@dataclass(frozen=True)
class IntegrityResult:
    ok: bool
    rows_compared: int
    max_score_diff: dict      # bearing -> largest absolute score difference
    flag_mismatches: dict     # bearing -> number of rows where the anomaly flag differs
    message: str


def compare_with_timeline(scored: pd.DataFrame, timeline: pd.DataFrame,
                          split: SplitInfo, tolerance: float = 1e-9) -> IntegrityResult:
    """Check that our recomputed test-period scores match results/bearing_timeline.csv."""
    if not split.aligned:
        return IntegrityResult(
            False, 0, {}, {},
            "bearing_timeline.csv does not line up with the last rows of ims_features.csv, "
            "so the recomputed scores could not be checked against it.",
        )

    first, count = split.first_test_index, split.n_test
    max_diff, flag_diff = {}, {}
    for bearing in BEARINGS:
        score_col = f"bearing_{bearing}_score"
        flag_col = f"bearing_{bearing}_anomaly"
        new_scores = scored[score_col].iloc[first:first + count].to_numpy(dtype=float)
        old_scores = timeline[score_col].to_numpy(dtype=float)
        max_diff[bearing] = float(np.max(np.abs(new_scores - old_scores)))
        new_flags = scored[flag_col].iloc[first:first + count].to_numpy(dtype=int)
        old_flags = timeline[flag_col].to_numpy(dtype=int)
        flag_diff[bearing] = int(np.sum(new_flags != old_flags))

    ok = all(d <= tolerance for d in max_diff.values()) and all(v == 0 for v in flag_diff.values())
    worst = max(max_diff.values())
    if ok:
        message = (f"Recomputed scores match results/bearing_timeline.csv for all {count} "
                   f"test-period recordings (largest score difference {worst:.2e}).")
    else:
        message = ("WARNING: recomputed scores differ from results/bearing_timeline.csv. "
                   "The models or the features file may have changed since the timeline was "
                   "created, or a different scikit-learn version is installed. The app uses "
                   "scores recomputed from the saved models.")
    return IntegrityResult(ok, count, max_diff, flag_diff, message)