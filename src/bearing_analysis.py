import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Load extracted NASA features
data = pd.read_csv("data/processed/ims_features.csv")

# Use the first 60% for training
split = int(len(data) * 0.60)

# Store test predictions
results = pd.DataFrame({
    "timestamp": data["timestamp"].iloc[split:].values
})

for bearing in range(1, 5):

    print(f"\nTraining Bearing {bearing}...")

    ch1 = bearing * 2 - 1
    ch2 = bearing * 2

    columns = []

    for ch in [ch1, ch2]:
        columns.extend([
            f"ch{ch}_rms",
            f"ch{ch}_std",
            f"ch{ch}_peak",
            f"ch{ch}_kurtosis",
            f"ch{ch}_crest"
        ])

    X = data[columns].replace(
        [np.inf, -np.inf], np.nan
    )

    # Calculate missing-value replacements from training data only
    medians = X.iloc[:split].median()
    X = X.fillna(medians)

    train = X.iloc[:split]
    test = X.iloc[split:]

    # Scale features
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train)
    test_scaled = scaler.transform(test)

    # Train anomaly detection model
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42
    )

    model.fit(train_scaled)

    # Save model and its preprocessing information
    artifact = {
        "model": model,
        "scaler": scaler,
        "medians": medians,
        "feature_columns": columns
    }

    joblib.dump(
        artifact,
        f"models/bearing_{bearing}.joblib"
    )

    # Generate test predictions
    results[f"bearing_{bearing}_score"] = (
        model.decision_function(test_scaled)
    )

    results[f"bearing_{bearing}_anomaly"] = (
        model.predict(test_scaled) == -1
    ).astype(int)

    print(f"Saved models/bearing_{bearing}.joblib")

# Save anomaly timeline
results.to_csv(
    "results/bearing_timeline.csv",
    index=False
)

print("\nBearing timeline saved!")

print("\nAnomaly percentage by bearing:")

for bearing in range(1, 5):
    column = f"bearing_{bearing}_anomaly"

    print(
        f"Bearing {bearing}: "
        f"{results[column].mean() * 100:.2f}%"
    )

print("\nAll four bearing models saved successfully!")