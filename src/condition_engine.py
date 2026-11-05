import pandas as pd


def max_anomaly_streak(values):
    """Return the longest consecutive anomaly run in a sequence."""
    longest = 0
    current = 0

    for value in values:
        if value == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def current_anomaly_streak(values):
    """Count consecutive anomalies ending at the latest recording."""
    streak = 0

    for value in reversed(values):
        if value == 1:
            streak += 1
        else:
            break

    return streak


def assess_condition(anomaly_rate, avg_score, streak):
    """
    Assess condition using recent anomaly frequency, score severity
    and the current consecutive anomaly streak.

    These are experimental prototype thresholds, not validated
    industrial failure thresholds.
    """

    # Sustained and substantial deviation
    if (
        anomaly_rate >= 0.70
        and avg_score <= -0.08
        and streak >= 10
    ) or (
        anomaly_rate >= 0.85
        and avg_score <= -0.05
        and streak >= 15
    ):
        return "CRITICAL"

    # Repeated anomalies with a meaningfully negative average score
    elif (
        anomaly_rate >= 0.40
        and avg_score <= -0.03
        and streak >= 5
    ):
        return "WARNING"

    return "NORMAL"


def recommend_action(condition):

    if condition == "CRITICAL":
        return (
            "Prioritise maintenance inspection. "
            "Review recent vibration trends before deciding on operation."
        )

    elif condition == "WARNING":
        return (
            "Schedule a bearing inspection and continue closer monitoring."
        )

    return "Continue routine monitoring."


def main():
    data = pd.read_csv("results/bearing_timeline.csv")

    recent = data.tail(50)

    print("\n========== MANTIQ CONDITION REPORT ==========\n")

    for bearing in range(1, 5):

        anomaly_column = f"bearing_{bearing}_anomaly"
        score_column = f"bearing_{bearing}_score"

        anomaly_rate = recent[anomaly_column].mean()
        avg_score = recent[score_column].mean()

        streak = current_anomaly_streak(
            recent[anomaly_column].tolist()
        )

        condition = assess_condition(
            anomaly_rate,
            avg_score,
            streak
        )

        action = recommend_action(condition)

        print(f"BEARING {bearing}")
        print(f"Recent anomaly rate: {anomaly_rate * 100:.2f}%")
        print(f"Average anomaly score: {avg_score:.4f}")
        print(f"Current anomaly streak: {streak} recordings")
        print(f"Machine condition: {condition}")
        print(f"Recommended action: {action}")
        print("--------------------------------------------")


if __name__ == "__main__":
    main()
