"""Reconstruct the tip cohorts directly from both monthly TLC Parquet files."""

import os
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(os.environ.get("TAXI_DATA", Path(__file__).resolve().parents[1] / "data"))
O = Path(__file__).resolve().parents[1] / "tables"
order = ["Fast", "Typical", "Slower", "Much slower", "Extreme"]
cols = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "trip_distance",
    "payment_type",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "passenger_count",
]
flows = []
frames = []
for month in ["2024-12", "2025-01"]:
    d = pd.read_parquet(R / f"yellow_tripdata_{month}.parquet", columns=cols)

    def audit(step):
        flows.append((month, step, len(d)))

    audit("raw")
    d = d[d.tpep_pickup_datetime.dt.to_period("M").eq(month)].copy()
    audit("pickup month")
    d = d[d.payment_type.eq(1)].copy()
    audit("card")
    d["mins"] = (
        d.tpep_dropoff_datetime - d.tpep_pickup_datetime
    ).dt.total_seconds() / 60
    d["bill"] = d.total_amount - d.tip_amount
    d["pct"] = 100 * d.tip_amount / d.bill
    for col, mask in [
        ("fare", d.fare_amount.gt(2.5)),
        ("duration", d.mins.between(1, 180, inclusive="neither")),
        ("distance", (d.trip_distance.gt(0.5) & d.trip_distance.le(100))),
        ("bill", d.bill.gt(0)),
        ("tip rate", d.pct.between(0, 200, inclusive="left")),
    ]:
        d = d.loc[mask.reindex(d.index)]
        audit(col)
    d["month"] = month
    frames.append(d)
d = pd.concat(frames, ignore_index=True)
del frames
d["hour"] = d.tpep_pickup_datetime.dt.floor("h")
d["day"] = d.hour.dt.normalize()
d["distance_bin"], edges = pd.qcut(
    d.trip_distance, 10, labels=False, retbins=True, duplicates="drop"
)
pd.Series(edges, name="distance_miles").to_csv(O / "distance_edges.csv", index=False)
g = d.groupby(["hour", "distance_bin"])
keep = g.mins.transform("size").ge(30)
d["ratio"] = d.mins / g.mins.transform("median")
d = d[keep].copy()
for mon, n in d.month.value_counts().items():
    flows.append((mon, "eligible cell", n))
# Open upper tail includes every valid record.
d["speed"] = pd.cut(d.ratio, [0, 0.85, 1, 1.2, 1.6, np.inf], labels=order)
rates = [0.15, 0.20, 0.25]
error = np.min([np.abs(d.tip_amount - d.bill * r) for r in rates], axis=0)
d["matched"] = error <= 0.030000001
d["zero"] = d.tip_amount.eq(0)
d["band"] = pd.cut(d.bill, [0, 12, 16, 25, 35, 40, 50, 80, 120, np.inf], right=False)


def summarize(frame, keys):
    return (
        frame.groupby(keys, observed=True)
        .agg(
            n=("bill", "size"),
            bill=("bill", "mean"),
            dollars=("tip_amount", "mean"),
            rate=("pct", "mean"),
            zero_pct=("zero", "mean"),
            match_pct=("matched", "mean"),
        )
        .assign(
            zero_pct=lambda x: x.zero_pct * 100, match_pct=lambda x: x.match_pct * 100
        )
    )


for name, frame, keys in [
    ("tips", d, ["speed", "matched"]),
    ("tips_month", d, ["month", "speed", "matched"]),
    ("bills", d, ["band"]),
    ("fixed_bill", d[d.bill.between(18, 20, inclusive="left")], ["speed", "matched"]),
    ("tips_all", d, ["speed"]),
    ("tips_vendor", d, ["VendorID", "speed", "matched"]),
]:
    summarize(frame, keys).to_csv(O / f"{name}.csv")
tols = []
for tol in [0.01, 0.03, 0.05]:
    d["flag"] = error <= tol + 1e-9
    v = (
        d.groupby(["speed", "flag"], observed=True)
        .pct.agg(["size", "mean"])
        .reset_index()
    )
    v["tolerance"] = tol
    tols.append(v)
pd.concat(tols).to_csv(O / "tolerance.csv", index=False)
wx = pd.read_csv(R / "cache/weather_202412_202501.csv", parse_dates=["time"]).set_index(
    "time"
)
pu = d.hour
do = d.tpep_dropoff_datetime.dt.floor("h")
precip = (pu.map(wx.precipitation) + do.map(wx.precipitation)) / 2
snow = (pu.map(wx.snowfall) + do.map(wx.snowfall)) / 2
d["weather"] = np.where(precip.ge(1) | snow.ge(0.5), "heavy", "other")
d["party"] = np.where(d.passenger_count.eq(1), "solo", "2-6")
v = d[~d.matched & d.passenger_count.between(1, 6) & precip.notna() & snow.notna()]
summarize(v, ["weather", "party", "speed"]).to_csv(O / "tip_context.csv")
# Paired calendar-day cluster bootstrap with shared resampled days for both groups.
rng = np.random.default_rng(20261119)
boot = []
for month, sub in [("pooled", d), *d.groupby("month")]:
    day = sub.groupby(["day", "matched", "speed"], observed=True).pct.agg(
        ["sum", "size"]
    )
    days = sub.day.nunique()
    weights = rng.multinomial(days, np.ones(days) / days, size=3000)
    deltas = []
    for b in [False, True]:
        estimates = []
        for speed in ["Fast", "Extreme"]:
            cell = day.xs((b, speed), level=("matched", "speed")).reindex(
                sorted(sub.day.unique()), fill_value=0
            )
            estimates.append((weights @ cell["sum"]) / (weights @ cell["size"]))
        delta = estimates[1] - estimates[0]
        deltas.append(delta)
        boot.append([month, str(b), *np.percentile(delta, [2.5, 97.5])])
    boot.append(
        [
            month,
            "other minus matched",
            *np.percentile(deltas[0] - deltas[1], [2.5, 97.5]),
        ]
    )
pd.DataFrame(boot, columns=["month", "group", "lo_pp", "hi_pp"]).to_csv(
    O / "tip_intervals.csv", index=False
)
pd.DataFrame(flows, columns=["month", "step", "n"]).to_csv(
    O / "tip_flow.csv", index=False
)
print(summarize(d, ["speed", "matched"]))

# Pickup-hour conditions are defined before the ride; mixed snow/rain goes to snow.
wx_good = wx.dropna(subset=["precipitation", "snowfall"])
wx_good["condition"] = np.select(
    [wx_good.snowfall.gt(0), wx_good.precipitation.gt(0)],
    ["Snow", "Rain"],
    default="Dry",
)
d["condition"] = d.hour.map(wx_good.condition)
wx_good.groupby("condition").apply(
    lambda v: pd.Series({"hours": len(v), "days": v.index.normalize().nunique()}),
    include_groups=False,
).to_csv(O / "weather_hours.csv")
summarize(d, ["condition", "matched", "speed"]).to_csv(O / "weather_speed.csv")
summarize(d, ["condition", "matched"]).to_csv(O / "weather_level.csv")
summarize(
    d[d.bill.between(18, 20, inclusive="left")], ["condition", "matched", "speed"]
).to_csv(O / "weather_fixed.csv")
