
"""Generate tracked alerts from historical replay transitions."""

from app.database.alert_service import create_alert


def process_replay_transitions(transitions, scored):
    if transitions is None or transitions.empty:
        return []

    created = []

    for _, transition in transitions.iterrows():
        if not bool(transition.get("alert_relevant", False)):
            continue

        bearing = int(transition["bearing"])
        severity = str(transition["to_condition"]).upper()

        if severity not in {"WARNING", "CRITICAL"}:
            continue

        recording = int(transition["recording"])

        matching = scored[scored["recording"] == recording]

        if matching.empty:
            continue

        row = matching.iloc[0]
        score_column = f"bearing_{bearing}_score"

        if score_column not in scored.columns:
            continue

        alert_id = create_alert(
            bearing=bearing,
            severity=severity,
            recording_timestamp=row["timestamp"],
            anomaly_score=float(row[score_column]),
            condition_label=severity,
        )

        created.append(alert_id)

    return created