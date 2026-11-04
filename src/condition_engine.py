import pandas as pd


def max_anomaly_streak(values):
    longest = 0
    current = 0

    for value in values:
        if value == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def assess_condition(anomaly_rate, avg_score, streak):

    if anomaly_rate >= 0.75 or (avg_score < -0.10 and streak >= 5):
        return "CRITICAL"

    elif anomaly_rate >= 0.20 or (avg_score < 0.05 and streak >= 3):
        return "WARNING"

    else:
        return "NORMAL"


def recommend_action(condition):

    if condition == "CRITICAL":
        return "Escalate to maintenance head. Inspect bearing before continued operation."

    elif condition == "WARNING":
        return "Schedule bearing inspection. Monitor vibration closely."

    else:
        return "Continue normal operation and routine monitoring."


def main():
    # Load bearing anomaly predictions
    data = pd.read_csv("results/bearing_timeline.csv")

    # Use the latest 50 recordings
    recent = data.tail(50)

    print("\n========== MANTIQ CONDITION REPORT ==========\n")

    for bearing in range(1, 5):

        anomaly_column = f"bearing_{bearing}_anomaly"
        score_column = f"bearing_{bearing}_score"

        anomaly_rate = recent[anomaly_column].mean()
        avg_score = recent[score_column].mean()
        streak = max_anomaly_streak(recent[anomaly_column].tolist())

        condition = assess_condition(anomaly_rate, avg_score, streak)
        action = recommend_action(condition)

        print(f"BEARING {bearing}")
        print(f"Recent anomaly rate: {anomaly_rate * 100:.2f}%")
        print(f"Average anomaly score: {avg_score:.4f}")
        print(f"Longest anomaly streak: {streak} recordings")
        print(f"Machine condition: {condition}")
        print(f"Recommended action: {action}")
        print("--------------------------------------------")


if __name__ == "__main__":
    main()