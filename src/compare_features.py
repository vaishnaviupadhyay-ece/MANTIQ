import pandas as pd

data = pd.read_csv("data/processed/ims_features.csv")

split = int(len(data) * 0.60)

print("\nTRAINING VS TESTING FEATURE COMPARISON")

for bearing in range(1, 5):

    ch1 = bearing * 2 - 1
    ch2 = bearing * 2

    print(f"\nBEARING {bearing}")

    for feature in ["rms", "kurtosis"]:

        columns = [
            f"ch{ch1}_{feature}",
            f"ch{ch2}_{feature}"
        ]

        train_avg = data.iloc[:split][columns].mean().mean()
        test_avg = data.iloc[split:][columns].mean().mean()

        change = ((test_avg - train_avg) / abs(train_avg)) * 100

        print(f"{feature.upper()}:")
        print(f"Training average: {train_avg:.5f}")
        print(f"Testing average:  {test_avg:.5f}")
        print(f"Change: {change:+.2f}%")