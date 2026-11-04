
import pandas as pd
import matplotlib.pyplot as plt

# Load extracted features
data = pd.read_csv("data/processed/ims_features.csv")

# Convert timestamps into datetime
data["timestamp"] = pd.to_datetime(
    data["timestamp"],
    format="%Y.%m.%d.%H.%M.%S"
)

# Average RMS of the two channels for each bearing
for bearing in range(1, 5):
    ch1 = bearing * 2 - 1
    ch2 = bearing * 2

    data[f"bearing_{bearing}_rms"] = (
        data[f"ch{ch1}_rms"] + data[f"ch{ch2}_rms"]
    ) / 2

# Plot all four bearings
plt.figure(figsize=(13, 6))

for bearing in range(1, 5):
    plt.plot(
        data["timestamp"],
        data[f"bearing_{bearing}_rms"],
        label=f"Bearing {bearing}"
    )

plt.title("Bearing Vibration Trends Over Time")
plt.xlabel("Date")
plt.ylabel("Average RMS Vibration")
plt.legend()
plt.grid(True)
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()
