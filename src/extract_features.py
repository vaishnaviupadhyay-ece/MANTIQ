
import pandas as pd
import numpy as np
from scipy.stats import kurtosis
from pathlib import Path

# Dataset folder
data_folder = Path("data/raw/IMS/IMS/1st_test")

records = []

# Get measurement files in chronological order
files = sorted(
    [f for f in data_folder.iterdir()
     if f.is_file() and not f.name.startswith("._")],
    key=lambda f: f.name
)

for file in files:
    # Read vibration measurements
    data = pd.read_csv(file, sep=r"\s+", header=None)

    row = {"timestamp": file.name}

    # Extract features from all 8 channels
    for channel in range(8):
        signal = data[channel].to_numpy()

        rms = np.sqrt(np.mean(signal ** 2))
        std = np.std(signal)
        peak = np.max(np.abs(signal))
        kurt = kurtosis(signal)
        crest = peak / rms if rms != 0 else 0

        row[f"ch{channel+1}_rms"] = rms
        row[f"ch{channel+1}_std"] = std
        row[f"ch{channel+1}_peak"] = peak
        row[f"ch{channel+1}_kurtosis"] = kurt
        row[f"ch{channel+1}_crest"] = crest

    records.append(row)

# Save extracted features
features = pd.DataFrame(records)

output_folder = Path("data/processed")
output_folder.mkdir(parents=True, exist_ok=True)

features.to_csv(output_folder / "ims_features.csv", index=False)

print("Feature extraction complete!")
print("Total recordings:", len(features))
print("Feature table shape:", features.shape)
print(features.head())
