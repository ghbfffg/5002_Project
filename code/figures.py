"""Draw the eight standalone charts in the analysis report."""

import os
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import geopandas as gp
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle

O = Path(__file__).resolve().parents[1]
F = O / "figures"
T = O / "tables"
R = Path(os.environ.get("TAXI_DATA", Path(__file__).resolve().parents[1] / "data"))


def read(name):
    return pd.read_csv(T / (name + ".csv"))


route = (
    read("route").set_index("route").loc[["JFK", "LGA", "Local short", "Local long"]]
)
heat = read("heat").set_index("weekday")
tips = read("tips")
fixed = read("fixed_bill")
zones = (
    gp.read_file(R / "taxi_zones/taxi_zones.shp").to_crs(4326).dissolve(by="LocationID")
)
hot = read("zones")
navy = "#16394a"
teal = "#007c83"
rust = "#ad5023"
gold = "#ffbd40"
gray = "#526771"
cmap = LinearSegmentedColormap.from_list(
    "pickup", ["#f0f4f0", "#cae1d7", "#76b4ad", "#33828a", "#185168", "#132f43"]
)
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#aebfc0",
        "axes.labelcolor": navy,
        "text.color": navy,
        "xtick.color": gray,
        "ytick.color": gray,
        "text.parse_math": False,
        "pdf.fonttype": 42,
        "axes.axisbelow": True,
    }
)


def fares(ax):
    bars = ax.barh(
        ["JFK", "LaGuardia", "Local ≤2 mi", "Local >2 mi"],
        route.occ_rate,
        color=[teal, teal, "#7695a0", "#7695a0"],
        height=0.56,
    )
    ax.invert_yaxis()
    ax.bar_label(bars, fmt="%.2f", padding=4)
    ax.set_xlim(0, 89)
    ax.set_xlabel("Base fare per occupied hour ($)")
    ax.grid(axis="x", alpha=0.16)


def gap(ax):
    for name, col in [("JFK", teal), ("Local short", rust)]:
        vals = [route.loc[name, f"cycle{i}"] for i in [30, 60, 90]]
        ax.plot(
            [30, 60, 90],
            vals,
            "o-",
            color=col,
            lw=2.3,
            label=name if name == "JFK" else "Local ≤2 mi",
        )
    ax.set(
        xlim=(25, 95),
        ylim=(0, 55),
        xticks=[30, 60, 90],
        xlabel="Largest included gap (min)",
        ylabel="Fare / cycle hour ($)",
    )
    ax.legend(frameon=False, ncol=2, loc="lower center")
    ax.grid(axis="y", alpha=0.16)


def timeplot(ax):
    im = ax.imshow(heat.values / 1000, cmap=cmap, aspect="auto", vmin=0, vmax=36)
    ax.set(
        yticks=range(7),
        yticklabels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        xticks=[0, 4, 8, 12, 16, 19, 23],
        xlabel="Local pickup hour",
    )
    ax.add_patch(Rectangle((18.5, 3.5), 1, 1, fc="none", ec=gold, lw=2.5))
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.045, pad=0.025)
    cb.set_label("Thousands / hour")


def maps(axs):
    for ax, win, title in zip(
        axs, ["Weekday AM", "Weekend night"], ["Weekday 07–10", "Weekend 00–03"]
    ):
        zm = zones.copy()
        d = hot[hot.window.eq(win)].set_index("zone")
        zm["v"] = d.hourly.reindex(zm.index).fillna(0)
        zm.geometry = zm.geometry.simplify(0.00012)
        zm.plot(
            ax=ax,
            column="v",
            cmap=cmap,
            vmin=0,
            vmax=2200,
            edgecolor="#a6bab9",
            linewidth=0.23,
        )
        pt = zm.loc[d.hourly.idxmax()].geometry.representative_point()
        ax.scatter(pt.x, pt.y, c=gold, s=45, edgecolors=navy, linewidths=1, zorder=3)
        ax.set(xlim=(-74.028, -73.935), ylim=(40.701, 40.795))
        ax.set_aspect(1.32)
        ax.axis("off")
        ax.set_title(title, fontsize=plt.rcParams["font.size"])


def trend(ax, df, col, label):
    for b, color, name in [(True, teal, "Preset match"), (False, rust, "Other amount")]:
        d = df[df.matched.eq(b)]
        ax.plot(range(5), d[col], marker="o", color=color, label=name, lw=2.4)
    ax.set(
        xticks=range(5),
        xticklabels=["≤0.85", "≤1.0", "≤1.2", "≤1.6", ">1.6"],
        xlabel="Relative duration band (upper edge)",
        ylabel=label,
        ylim=(0, 24 if col == "rate" else max(5, df[col].max() * 1.15)),
    )
    ax.legend(
        frameon=False,
        ncol=2,
        loc="lower left",
        fontsize=plt.rcParams["font.size"] * 0.85,
    )
    ax.grid(axis="y", alpha=0.16)


def billplot(ax):
    b = read("bills")
    ax.plot(range(len(b)), b.match_pct, "o-", color=teal)
    ax.set(
        xticks=range(len(b)),
        xticklabels=["<12", "12", "16", "25", "35", "40", "50", "80", "120+"],
        xlabel="Bill band, lower edge ($)",
        ylabel="Preset match (%)",
        ylim=(0, 80),
    )
    ax.grid(axis="y", alpha=0.18)


for nm, draw in [
    ("fares", fares),
    ("cycles", gap),
    ("heat", timeplot),
    ("tip_rates", lambda ax: trend(ax, tips, "rate", "Average tip (%)")),
    ("tip_dollars", lambda ax: trend(ax, tips, "dollars", "Average tip ($)")),
    ("fixed_bill", lambda ax: trend(ax, fixed, "dollars", "Average tip ($)")),
    ("bills", billplot),
]:
    f, ax = plt.subplots(figsize=(7.2, 3.4), layout="constrained")
    draw(ax)
    f.savefig(F / (nm + ".png"), dpi=165)
    plt.close(f)
f, axs = plt.subplots(1, 2, figsize=(6.6, 4.6), layout="constrained")
maps(axs)
f.colorbar(
    plt.cm.ScalarMappable(norm=Normalize(0, 2200), cmap=cmap),
    ax=axs,
    shrink=0.76,
    label="Pickups per hour",
)
f.savefig(F / "maps.png", dpi=165)
plt.close(f)
