
import pandas as pd
from scipy.stats import linregress

data = pd.read_csv("data/processed/ims_features.csv")

print("\nMANTIQ - BEARING VIBRATION ANALYSIS")
print("=" * 55)

for bearing in range(1, 5):
    ch1 = bearing * 2 - 1
    ch2 = bearing * 2

    # Average RMS across the two sensors
    rms = (data[f"ch{ch1}_rms"] + data[f"ch{ch2}_rms"]) / 2

    # Analyse change over time
    x = range(len(rms))
    trend = linregress(x, rms)

    first = rms.iloc[:100].mean()
    last = rms.iloc[-100:].mean()
    change = ((last - first) / first) * 100

    print(f"\nBEARING {bearing}")
    print(f"Initial average RMS: {first:.5f}")
    print(f"Final average RMS:   {last:.5f}")
    print(f"Minimum RMS:         {rms.min():.5f}")
    print(f"Maximum RMS:         {rms.max():.5f}")
    print(f"Change:              {change:+.2f}%")

    if trend.slope > 0:
        print("Overall trend: Increasing")
    else:
        print("Overall trend: Decreasing")

print("\n" + "=" * 55)
print("Analysis complete.")
