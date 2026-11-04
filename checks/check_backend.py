"""
Developer check for the MANTIQ backend (not part of the app).
Prints real numbers computed from your files. Run from the project root:
    python checks\\check_backend.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import BEARINGS, CONDITION_WINDOW  # noqa: E402
from app.services import pipeline  # noqa: E402
from app.services.data_service import DataError  # noqa: E402


def main():
    start = time.time()
    try:
        p = pipeline.build_pipeline()
    except (DataError, ImportError) as exc:
        print("ERROR:", exc)
        sys.exit(1)
    from app.services import condition_service as cs

    s = p.split
    print("\n=== DATA ===")
    print(f"Recordings in ims_features.csv : {s.n_total}")
    print(f"Training period                : first {s.n_train} recordings")
    print(f"Unseen test period             : {s.n_test} recordings (rows in bearing_timeline.csv)")
    print(f"First unseen recording         : number {s.first_test_recording}, "
          f"timestamp {p.features['timestamp'].iloc[s.first_test_index]}")
    print(f"Timeline lines up with features: {s.aligned}")
    print(f"Matches int(len*0.60) split    : {s.matches_training_script} "
          f"(training script would use {s.expected_train_count})")
    print(f"Last recording                 : {p.features['timestamp'].iloc[-1]}")
    print("Notes:", p.notes if p.notes else "none")

    print("\n=== MODEL INTEGRITY (recomputed vs results/bearing_timeline.csv) ===")
    print(p.integrity.message)
    for b in BEARINGS:
        print(f"  Bearing {b}: largest score difference "
              f"{p.integrity.max_score_diff.get(b, float('nan')):.2e}, "
              f"flag mismatches {p.integrity.flag_mismatches.get(b, '-')}")

    first = s.first_test_index
    print("\n=== TEST PERIOD: anomaly flags and conditions ===")
    for b in BEARINGS:
        flags = p.scored[f"bearing_{b}_anomaly"].iloc[first:]
        counts = p.conditions[f"bearing_{b}_condition"].iloc[first:].value_counts().to_dict()
        print(f"Bearing {b}: {flags.mean() * 100:.2f}% of recordings flagged | conditions {counts}")

    print(f"\n=== CONDITION AT REPLAY START (recording {s.first_test_recording}) ===")
    snap = cs.snapshot(p.conditions, p.scored, first)
    print(f"Window size {snap['window_size']} (should be {CONDITION_WINDOW}), overall {snap['overall']}")
    for b in BEARINGS:
        x = snap["bearings"][b]
        print(f"  Bearing {b}: {x['condition']:8s} rate {x['anomaly_rate'] * 100:5.1f}% "
              f"avg score {x['avg_score']:+.4f} streak {x['streak']}")

    print("\n=== CONDITION CHANGES during the test period ===")
    trans = cs.transitions_between(p.conditions, first, s.n_total - 1)
    print(f"{len(trans)} condition changes, {int(trans['alert_relevant'].sum())} of them alert-relevant")
    for b in BEARINGS:
        sub = trans[trans["bearing"] == b]
        print(f"  Bearing {b}: {len(sub)} changes "
              f"({int((sub['change'] == 'WORSENED').sum())} worsened, "
              f"{int((sub['change'] == 'IMPROVED').sum())} improved)")
    if len(trans):
        print("First changes:")
        print(trans[["recording", "timestamp", "bearing", "from_condition", "to_condition"]]
              .head(8).to_string(index=False))

    print("\n=== FINAL CONDITION vs src/condition_engine.py REPORT LOGIC ===")
    recent = p.timeline.tail(50)
    last = cs.snapshot(p.conditions, p.scored, s.n_total - 1)
    all_match = True
    for b in BEARINGS:
        col = f"bearing_{b}_anomaly"
        rate = recent[col].mean()
        avg = recent[f"bearing_{b}_score"].mean()
        streak = cs.engine.max_anomaly_streak(recent[col].tolist())
        expected = cs.engine.assess_condition(rate, avg, streak)
        ours = last["bearings"][b]["condition"]
        match = expected == ours
        all_match = all_match and match
        print(f"  Bearing {b}: engine says {expected:8s} | service says {ours:8s} | "
              f"{'MATCH' if match else 'DIFFERENT'}")
    print("Overall:", "all four match" if all_match else "MISMATCH - tell me")

    print(f"\nDone in {time.time() - start:.1f} seconds.")


if __name__ == "__main__":
    main()