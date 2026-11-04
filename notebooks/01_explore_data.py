import pandas as pd
import matplotlib.pyplot as plt

# Load one vibration measurement file
file_path = r"data/raw/IMS/IMS/1st_test/2003.10.22.12.06.24"

data = pd.read_csv(file_path, sep=r"\s+", header=None)

# Plot the first accelerometer channel
plt.figure(figsize=(12, 4))
plt.plot(data[0])

plt.title("Bearing Vibration Signal - Channel 1")
plt.xlabel("Sample Number")
plt.ylabel("Vibration Amplitude")
plt.grid(True)

plt.tight_layout()
plt.show()