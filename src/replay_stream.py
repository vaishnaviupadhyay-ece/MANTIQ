import pandas as pd
import numpy as np
import joblib
import time
import os

# Replay settings
REPLAY_DELAY = 0.5  # Seconds between recordings
MAX_RECORDINGS = 100  # Start with 100 for testing

# Load NASA feature data
data = pd.read_csv("data/processed/ims_features.csv")

# Load the four trained bearing models
models = {}

for bearing in range(1, 5):
    models[bearing] = joblib.load(
        f"models/bearing_{bearing}.joblib"
    )

# Store processed recordings
stream_results = []

print("\n===================================")
print("       MANTIQ DATA REPLAY")
print("===================================")
print("Source: NASA IMS Bearing Dataset")
print("Mode: Historical data replay simulation")
print("Starting stream...\n")

# Feed recordings one at a time
for index, row in data.iterrows():

    result = {
        "timestamp": row["timestamp"]
    }

    for bearing in range(1, 5):

        artifact = models[bearing]

        columns = artifact["feature_columns"]

        # Extract features for this bearing
        features = row[columns].to_frame().T

        features = features.replace(
            [np.inf, -np.inf], np.nan
        )

        features = features.fillna(
            artifact["medians"]
        )

        # Apply saved scaler
        scaled = artifact["scaler"].transform(features)

        # Run anomaly detection
        score = artifact["model"].decision_function(scaled)[0]

        prediction = artifact["model"].predict(scaled)[0]

        result[f"bearing_{bearing}_score"] = score

        result[f"bearing_{bearing}_anomaly"] = (
            1 if prediction == -1 else 0
        )

    stream_results.append(result)

    # Display current recording
    print(f"Recording {index + 1}/{len(data)}")
    print(f"Timestamp: {row['timestamp']}")

    for bearing in range(1, 5):
        status = (
            "ANOMALY"
            if result[f"bearing_{bearing}_anomaly"] == 1
            else "NORMAL"
        )

        print(f"  Bearing {bearing}: {status}")

    print("-----------------------------------")

    # Save progress periodically
    if (index + 1) % 10 == 0:
        pd.DataFrame(stream_results).to_csv(
            "results/live_stream.csv",
            index=False
        )

    # Stop after the testing limit
    if index + 1 >= MAX_RECORDINGS:
        break

    time.sleep(REPLAY_DELAY)

# Save final output
pd.DataFrame(stream_results).to_csv(
    "results/live_stream.csv",
    index=False
)

print("\nReplay completed!")
print("Results saved to results/live_stream.csv")
