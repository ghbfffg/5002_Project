"""Rebuild April 2013 tables. Set TAXI_DATA and TAXI_WORK to override local paths."""

import os
from collections import Counter
from pathlib import Path

import geopandas as gp
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as ac
import pyarrow.parquet as pq

R = Path(os.environ.get("TAXI_DATA", Path(__file__).resolve().parents[1] / "data"))
W = Path(os.environ.get("TAXI_WORK", "work/rerun"))
W.mkdir(parents=True, exist_ok=True)
O = Path(__file__).resolve().parents[1] / "tables"
keys = ["hack_license", "medallion", "vendor_id", "pickup_datetime"]
cols = {
    "data": keys
    + [
        "dropoff_datetime",
        "trip_distance",
        "pickup_longitude",
        "pickup_latitude",
        "dropoff_longitude",
        "dropoff_latitude",
        "passenger_count",
    ],
    "fare": keys + ["payment_type", "fare_amount"],
}
from pyarrow import compute as pc

audit = Counter()
for kind, fields in cols.items():
    file = R / "trip_data" / f"trip_{kind}_4.csv"
    names = [s.strip() for s in file.open().readline().split(",")]
    stream = ac.open_csv(
        file,
        read_options=ac.ReadOptions(
            column_names=names, skip_rows=1, block_size=16 << 20
        ),
        convert_options=ac.ConvertOptions(include_columns=fields),
    )
    writers = {}
    for batch in stream:
        table = pa.Table.from_batches([batch])
        audit[kind + " raw"] += len(table)
        prefixes = pc.utf8_upper(pc.utf8_slice_codeunits(table["hack_license"], 0, 1))
        for i, k in enumerate("0123456789ABCDEF"):
            sub = table.filter(pc.equal(prefixes, k))
            if k not in writers:
                writers[k] = pq.ParquetWriter(W / f"{kind}{k}.parquet", sub.schema)
            writers[k].write_table(sub)
            audit[kind + " valid prefix"] += len(sub)
    for writer in writers.values():
        writer.close()
    print("partitioned", kind, flush=True)
z = gp.read_file(R / "taxi_zones/taxi_zones.shp").to_crs(4326).dissolve(by="LocationID")


def locate(t, side):
    pts = gp.GeoDataFrame(
        geometry=gp.points_from_xy(t[side + "_longitude"], t[side + "_latitude"]),
        index=t.index,
        crs=4326,
    )
    j = gp.sjoin(pts, z[["geometry"]], how="left", predicate="within")
    return j[~j.index.duplicated()].iloc[:, -1]


hours = []
hotspots = []
routes = []
active = []
landings = []
for k in "0123456789ABCDEF":
    t = pd.read_parquet(W / f"data{k}.parquet")
    f = pd.read_parquet(W / f"fare{k}.parquet")
    for frame, name in [(t, "data"), (f, "fare")]:
        frame.dropna(subset=keys, inplace=True)
        frame.drop_duplicates(keys, keep=False, inplace=True)
        audit[name + " unique complete keys"] += len(frame)
    # Shift before fare matching and trip eligibility to preserve observed ordering.
    t = t.sort_values(["hack_license", "pickup_datetime", "medallion"])
    g = t.groupby("hack_license")
    nx = g.pickup_datetime.shift(-1)
    t["gap"] = (nx - t.dropoff_datetime).dt.total_seconds() / 60
    t.loc[g.medallion.shift(-1).ne(t.medallion), "gap"] = np.nan
    t = t.merge(f, on=keys, validate="1:1")
    audit["matched"] += len(t)
    t["mins"] = (t.dropoff_datetime - t.pickup_datetime).dt.total_seconds() / 60
    for name, mask in [
        ("April", t.pickup_datetime.dt.to_period("M").eq("2013-04")),
        ("payment", t.payment_type.isin(["CRD", "CSH"])),
        ("fare", t.fare_amount.between(2.5, 300)),
        ("duration", t.mins.between(1, 180)),
        ("distance", t.trip_distance.between(0.1, 100)),
    ]:
        t = t.loc[mask.reindex(t.index)]
        audit[name] += len(t)
    audit["drivers"] += t.hack_license.nunique()
    t["date"] = t.pickup_datetime.dt.normalize()
    t["hour"] = t.pickup_datetime.dt.hour
    t["weekday"] = t.pickup_datetime.dt.dayofweek
    hours.append(t.groupby(["date", "hour"]).size())
    active.append(
        t.groupby("date").agg(
            active=("hack_license", "nunique"),
            fare=("fare_amount", "sum"),
            mins=("mins", "sum"),
        )
    )
    t["zone"] = locate(t, "pickup")
    audit["pickup mapped"] += t.zone.notna().sum()
    for label, mask in [
        ("Weekday AM", (t.weekday < 5) & t.hour.between(7, 9)),
        ("Weekend night", (t.weekday >= 5) & t.hour.between(0, 2)),
    ]:
        h = t.loc[mask].groupby("zone").size().rename("n").reset_index()
        h["window"] = label
        hotspots.append(h)
    # Count observed new fares anywhere after a drop-off; include non-links in denominator.
    drop = t.dropoff_datetime
    for label, mask in [
        ("Weekday AM", (drop.dt.dayofweek < 5) & drop.dt.hour.between(7, 9)),
        ("Weekend night", (drop.dt.dayofweek >= 5) & drop.dt.hour.between(0, 2)),
    ]:
        v = t.loc[mask & drop.dt.month.eq(4)].copy()
        v["zone"] = locate(v, "dropoff")
        v["within5"] = v.gap.between(0, 5)
        v["within10"] = v.gap.between(0, 10)
        byzone = (
            v.groupby("zone")
            .agg(
                drops=("mins", "size"),
                next5=("within5", "sum"),
                next10=("within10", "sum"),
            )
            .reset_index()
        )
        byzone["window"] = label
        landings.append(byzone)
    m = t[t.zone.eq(161)].copy()
    audit["midtown"] += len(m)
    m["dest"] = locate(m, "dropoff")
    m["route"] = np.select(
        [
            m.dest.eq(132),
            m.dest.eq(138),
            m.dest.isin(z[z.borough.eq("Manhattan")].index) & m.trip_distance.le(2),
            m.dest.isin(z[z.borough.eq("Manhattan")].index) & m.trip_distance.gt(2),
        ],
        ["JFK", "LGA", "Local short", "Local long"],
        default="Other",
    )
    m["peak"] = np.where(
        (m.weekday < 5) & m.hour.between(16, 19), "PM peak", "Other hours"
    )
    routes.append(
        m.loc[
            m.route.ne("Other"),
            [
                "date",
                "hour",
                "route",
                "peak",
                "mins",
                "fare_amount",
                "gap",
                "passenger_count",
                "trip_distance",
            ],
        ]
    )
    print("analyzed", k, flush=True)
audit = pd.Series(audit, name="n")
audit.to_csv(O / "driver_flow.csv", index_label="step")
m = pd.concat(routes, ignore_index=True)
m.to_parquet(W / "routes.parquet")


def metrics(g):
    d = dict(
        n=len(g),
        mean_fare=g.fare_amount.mean(),
        mean_min=g.mins.mean(),
        mean_miles=g.trip_distance.mean(),
        occ_rate=60 * g.fare_amount.sum() / g.mins.sum(),
    )
    for limit in [30, 60, 90]:
        v = g[g.gap.between(0, limit)]
        d.update(
            {
                f"n{limit}": len(v),
                f"occ{limit}": 60 * v.fare_amount.sum() / v.mins.sum(),
                f"cycle{limit}": 60 * v.fare_amount.sum() / (v.mins + v.gap).sum(),
            }
        )
    return pd.Series(d)


for name, groups in [("route", ["route"]), ("route_peak", ["route", "peak"])]:
    m.groupby(groups).apply(metrics, include_groups=False).to_csv(O / f"{name}.csv")
passengers = m[m.passenger_count.between(1, 6)].copy()
passengers["party"] = np.where(passengers.passenger_count.eq(1), "solo", "2-6")
passengers.groupby(["route", "party"]).apply(metrics, include_groups=False).to_csv(
    O / "route_party.csv"
)
hours = pd.concat(hours, axis=1).fillna(0).sum(axis=1).rename("trips").reset_index()
hours["weekday"] = hours.date.dt.dayofweek
hours.groupby(["weekday", "hour"]).trips.mean().unstack().to_csv(O / "heat.csv")
assert len(hours) == 720 and int(hours.trips.sum()) == audit["distance"]
hot = (
    pd.concat(hotspots)
    .groupby(["window", "zone"])
    .n.sum()
    .reset_index()
    .join(z.zone.rename("name"), on="zone")
)
hot["hourly"] = hot.n / np.where(hot.window.eq("Weekday AM"), 22 * 3, 8 * 3)
hot.to_csv(O / "zones.csv", index=False)
daily = (
    hours.groupby("date")
    .trips.sum()
    .to_frame()
    .join(pd.concat(active).groupby(level=0).sum())
    .join(
        pd.read_csv(R / "cache/weather_2013.csv", parse_dates=["date"]).set_index(
            "date"
        )[["rain_mm"]]
    )
)
assert daily.rain_mm.notna().all()
daily["weekday"] = daily.index.dayofweek
daily["wet"] = daily.rain_mm.gt(1)
daily["occupied_rate"] = 60 * daily.fare / daily.mins
daily.to_csv(O / "days.csv")
print(audit)

land = (
    pd.concat(landings)
    .groupby(["window", "zone"])[["drops", "next5", "next10"]]
    .sum()
    .reset_index()
)
land = land.merge(hot, on=["window", "zone"], how="left")
land["share5"] = 100 * land.next5 / land.drops
land["share10"] = 100 * land.next10 / land.drops
land.to_csv(O / "dropoffs.csv", index=False)
