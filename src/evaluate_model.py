
import pandas as pd

data = pd.read_csv("results/anomaly_predictions.csv")

split = 1293

train = data.iloc[:split]
test = data.iloc[split:]

print("\nMANTIQ - MODEL EVALUATION")
print("=" * 45)

print("\nTRAINING DATA")
print(train["status"].value_counts())

print("\nTESTING DATA")
print(test["status"].value_counts())

print("\nANOMALY SCORE SUMMARY")
print(data["anomaly_score"].describe())

print("\nFIRST 10 ANOMALOUS RECORDINGS")
anomalies = data[data["status"] == "Anomaly"]

print(
    anomalies[["timestamp", "anomaly_score"]]
    .head(10)
    .to_string(index=False)
)

print("\nLAST 10 ANOMALOUS RECORDINGS")
print(
    anomalies[["timestamp", "anomaly_score"]]
    .tail(10)
    .to_string(index=False)
)
