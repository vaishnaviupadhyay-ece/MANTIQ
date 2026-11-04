
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Load extracted features
data = pd.read_csv("data/processed/ims_features.csv")

# Select all 40 vibration features
feature_columns = [
    col for col in data.columns
    if col != "timestamp"
]

X = data[feature_columns].replace(
    [np.inf, -np.inf], np.nan
)

# Handle missing values
X = X.fillna(X.median())

# Split chronologically: first 60% for training
split = int(len(X) * 0.60)

X_train = X.iloc[:split]
X_test = X.iloc[split:]

# Scale features using training data only
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train anomaly detection model
model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)

model.fit(X_train_scaled)

# Predict anomalies
train_predictions = model.predict(X_train_scaled)
test_predictions = model.predict(X_test_scaled)

# Calculate anomaly scores
train_scores = model.decision_function(X_train_scaled)
test_scores = model.decision_function(X_test_scaled)

# Combine results
data["anomaly_score"] = np.concatenate(
    [train_scores, test_scores]
)

data["prediction"] = np.concatenate(
    [train_predictions, test_predictions]
)

data["status"] = data["prediction"].map({
    1: "Normal",
    -1: "Anomaly"
})

# Save results
data.to_csv(
    "results/anomaly_predictions.csv",
    index=False
)

print("\nMANTIQ - ANOMALY DETECTION RESULTS")
print("=" * 45)
print("Training recordings:", len(X_train))
print("Testing recordings:", len(X_test))
print("\nPredictions:")
print(data["status"].value_counts())
print("\nModel training complete!")
print("Saved: results/anomaly_predictions.csv")