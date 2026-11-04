import pandas as pd

data = pd.read_csv("results/bearing_timeline.csv")

data["period"] = pd.qcut(
    range(len(data)),
    5,
    labels=["Period 1", "Period 2", "Period 3", "Period 4", "Period 5"]
)

print("\nAVERAGE ANOMALY SCORES BY PERIOD")
print("(Lower scores indicate more unusual behaviour)\n")

for bearing in range(1, 5):

    column = f"bearing_{bearing}_score"

    print(f"\nBearing {bearing}")

    print(
        data.groupby("period", observed=True)[column]
        .mean()
        .round(4)
    )