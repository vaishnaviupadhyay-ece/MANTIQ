import pandas as pd

data = pd.read_csv("results/bearing_timeline.csv")

print("\nFIRST AND LAST ANOMALY")

for bearing in range(1, 5):

    column = f"bearing_{bearing}_anomaly"

    anomalies = data[data[column] == True]

    print(f"\nBearing {bearing}")

    if len(anomalies) == 0:
        print("No anomalies found")
        continue

    print("First anomaly:", anomalies.iloc[0]["timestamp"])
    print("Last anomaly:", anomalies.iloc[-1]["timestamp"])
    print("Total anomalous recordings:", len(anomalies))