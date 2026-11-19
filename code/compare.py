"""Compare cycles using local fares reweighted to the airport's exact pickup date and hour."""

import os
from pathlib import Path

import numpy as np
import pandas as pd

O = Path(__file__).resolve().parents[1] / "tables"
m = pd.read_parquet(Path(os.environ.get("TAXI_WORK", "work/rerun")) / "routes.parquet")
m["route"] = m.route.replace({"Local long": "City", "Local short": "City"})
m["period"] = pd.cut(
    m.hour, [-1, 6, 9, 15, 19, 23], labels=["00–07", "07–10", "10–16", "16–20", "20–24"]
).astype(str)
m["days"] = np.where(m.date.dt.dayofweek < 5, "Weekdays", "Weekends")
rows = []
for (day, period), p in m.groupby(["days", "period"]):
    for window in [30, 60, 90, 120]:
        q = (
            p[p.gap.between(0, window)]
            .groupby(["route", "date", "hour"])
            .agg(
                n=("mins", "size"),
                fare=("fare_amount", "mean"),
                ride=("mins", "mean"),
                gap=("gap", "mean"),
            )
        )
        city = q.loc["City"]
        for airport in ["JFK", "LGA"]:
            if airport not in q.index.levels[0]:
                continue
            a = q.loc[airport].join(city, how="inner", lsuffix="_a", rsuffix="_c")
            if a.empty:
                continue
            row = dict(
                days=day,
                period=period,
                limit=window,
                airport=airport,
                airport_total=int(p.route.eq(airport).sum()),
                n_air=int(a.n_a.sum()),
                n_city=int(a.n_c.sum()),
                city_total=int(p.route.eq("City").sum()),
            )
            for pref, tag in [("air", "a"), ("city", "c")]:
                for measure in ["ride", "gap", "fare"]:
                    row[pref + "_" + measure] = np.average(
                        a[measure + "_" + tag], weights=a.n_a
                    )
                row[pref + "_rate"] = (
                    60
                    * row[pref + "_fare"]
                    / (row[pref + "_ride"] + row[pref + "_gap"])
                )
            row["break_even_min"] = (
                60 * row["air_fare"] / row["city_rate"] - row["air_ride"]
            )
            row["premium"] = row["air_rate"] - row["city_rate"]
            rows.append(row)
pd.DataFrame(rows).to_csv(O / "matched_cycles.csv", index=False)
