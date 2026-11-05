
"""
MANTIQ condition service.
"""

import sys

import numpy as np
import pandas as pd

from app.config import BEARINGS, CONDITION_WINDOW, SRC_DIR

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

try:
    import condition_engine as engine
except Exception as exc:
    raise ImportError(
        f"Could not import src/condition_engine.py: {exc}"
    ) from exc

if not hasattr(engine, "assess_condition"):
    raise ImportError(
        "The condition engine does not contain assess_condition()."
    )

SEVERITY_RANK = {
    "NORMAL": 0,
    "WARNING": 1,
    "CRITICAL": 2,
}

CONDITION_LABELS = {
    "NORMAL": "Normal",
    "WARNING": "Warning",
    "CRITICAL": "Critical",
}


def overall_condition(conditions) -> str:
    """Return the most severe condition among the bearings."""
    return max(
        conditions,
        key=lambda condition: SEVERITY_RANK.get(condition, 0)
    )


def compute_conditions(
    scored: pd.DataFrame,
    window: int = CONDITION_WINDOW
) -> pd.DataFrame:
    """
    Calculate rolling condition assessments for every bearing.

    The anomaly streak represents consecutive anomalies ending
    at the current recording, not the longest streak in the window.
    """

    n = len(scored)

    data = {
        "recording": scored["recording"].to_numpy(),
        "timestamp": scored["timestamp"].to_numpy(),
        "time": scored["time"].to_numpy(),
        "window_size": np.minimum(
            np.arange(1, n + 1),
            window
        ),
    }

    for bearing in BEARINGS:

        flags = scored[
            f"bearing_{bearing}_anomaly"
        ].to_numpy(dtype=int)

        scores = scored[
            f"bearing_{bearing}_score"
        ].to_numpy(dtype=float)

        rates = np.empty(n)
        averages = np.empty(n)
        streaks = np.empty(n, dtype=int)
        conditions = []

        for i in range(n):

            start = max(0, i - window + 1)

            window_flags = flags[start:i + 1]
            window_scores = scores[start:i + 1]

            rate = float(window_flags.mean())
            average = float(window_scores.mean())

            streak = engine.current_anomaly_streak(
                window_flags.tolist()
            )

            condition = engine.assess_condition(
                rate,
                average,
                streak
            )

            rates[i] = rate
            averages[i] = average
            streaks[i] = streak

            conditions.append(condition)

        data[f"bearing_{bearing}_condition"] = conditions
        data[f"bearing_{bearing}_rate"] = rates
        data[f"bearing_{bearing}_avg_score"] = averages
        data[f"bearing_{bearing}_streak"] = streaks

    return pd.DataFrame(data)


def recommended_action(condition: str) -> str:
    return engine.recommend_action(condition)


def transitions_between(
    conditions: pd.DataFrame,
    from_index: int,
    to_index: int
) -> pd.DataFrame:
    """
    Find condition changes after from_index through to_index.

    A worsening transition to WARNING or CRITICAL is relevant
    for maintenance alert creation.
    """

    from_index = max(int(from_index), 0)
    to_index = min(int(to_index), len(conditions) - 1)

    rows = []

    for bearing in BEARINGS:

        column = conditions[
            f"bearing_{bearing}_condition"
        ].to_numpy()

        for i in range(from_index + 1, to_index + 1):

            before = column[i - 1]
            after = column[i]

            if before == after:
                continue

            worsened = (
                SEVERITY_RANK[after] >
                SEVERITY_RANK[before]
            )

            rows.append({
                "index": i,
                "recording": int(
                    conditions["recording"].iloc[i]
                ),
                "timestamp": conditions["timestamp"].iloc[i],
                "bearing": bearing,
                "from_condition": before,
                "to_condition": after,
                "change": (
                    "WORSENED" if worsened else "IMPROVED"
                ),
                "alert_relevant": bool(
                    worsened and after in ("WARNING", "CRITICAL")
                ),
            })

    columns = [
        "index",
        "recording",
        "timestamp",
        "bearing",
        "from_condition",
        "to_condition",
        "change",
        "alert_relevant",
    ]

    result = pd.DataFrame(rows, columns=columns)

    return result.sort_values(
        ["index", "bearing"]
    ).reset_index(drop=True)


def snapshot(
    conditions: pd.DataFrame,
    scored: pd.DataFrame,
    index: int
) -> dict:
    """Return the condition snapshot used by the dashboards."""

    row = conditions.iloc[index]

    bearings = {}

    for bearing in BEARINGS:

        condition = row[
            f"bearing_{bearing}_condition"
        ]

        bearings[bearing] = {
            "condition": condition,
            "anomaly_rate": float(
                row[f"bearing_{bearing}_rate"]
            ),
            "avg_score": float(
                row[f"bearing_{bearing}_avg_score"]
            ),
            "streak": int(
                row[f"bearing_{bearing}_streak"]
            ),
            "latest_score": float(
                scored[f"bearing_{bearing}_score"].iloc[index]
            ),
            "latest_flag": int(
                scored[f"bearing_{bearing}_anomaly"].iloc[index]
            ),
            "action": engine.recommend_action(condition),
        }

    return {
        "recording": int(row["recording"]),
        "timestamp": row["timestamp"],
        "time": row["time"],
        "window_size": int(row["window_size"]),
        "overall": overall_condition([
            item["condition"]
            for item in bearings.values()
        ]),
        "bearings": bearings,
    }