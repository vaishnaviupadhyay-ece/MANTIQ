import pandas as pd

data = pd.read_csv("data/processed/ims_features.csv")

split = int(len(data) * 0.60)
test = data.iloc[split:].copy()

test["period"] = pd.qcut(
    range(len(test)),
    5,
    labels=["Period 1", "Period 2", "Period 3", "Period 4", "Period 5"]
)

for bearing in range(1, 5):

    ch1 = bearing * 2 - 1
    ch2 = bearing * 2

    print(f"\nBEARING {bearing}")

    for feature in ["rms", "kurtosis"]:

        columns = [
            f"ch{ch1}_{feature}",
            f"ch{ch2}_{feature}"
        ]

        print(f"\n{feature.upper()}")

        print(
            test.groupby("period", observed=True)[columns]
            .mean()
            .mean(axis=1)
            .round(4)
        )