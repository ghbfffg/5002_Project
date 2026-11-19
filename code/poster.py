"""Build the A0 landscape PDF and PNG preview from published summary tables."""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

O = Path(__file__).resolve().parents[1]


def read(name):
    return pd.read_csv(O / "tables" / (name + ".csv"))


tips, fixed = read("tips"), read("fixed_bill")
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "text.parse_math": False,
        "pdf.fonttype": 42,
    }
)
# Landscape poster. Position elements in a common design coordinate system.
W, H = 1500, 1500 * 841 / 1189
scale = 1189 / 25.4 * 72 / W
Y = "#f2b705"
ink = "#191918"
muted = "#53534e"
rule = "#d7d6cb"
blue = "#2368b4"
orange = "#bc4d21"
cream = "#fff5d5"
white = "#ffffff"
plt.rcParams.update(
    {
        "font.size": 12 * scale,
        "axes.labelsize": 12 * scale,
        "text.color": ink,
        "axes.labelcolor": ink,
        "xtick.color": muted,
        "ytick.color": muted,
        "axes.edgecolor": rule,
        "axes.linewidth": 1.5,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "lines.linewidth": 4,
        "axes.facecolor": "white",
    }
)
f = plt.figure(figsize=(1189 / 25.4, 841 / 25.4), facecolor=white)


def block(x, y, w, h, color):
    f.add_artist(
        Rectangle(
            (x / W, 1 - (y + h) / H),
            w / W,
            h / H,
            transform=f.transFigure,
            facecolor=color,
            edgecolor="none",
            zorder=-1,
        )
    )


def put(x, y, msg, size=13, weight="normal", color=ink, align="left", spacing=1.26):
    f.text(
        x / W,
        1 - y / H,
        msg,
        ha=align,
        va="top",
        fontsize=size * scale,
        weight=weight,
        color=color,
        linespacing=spacing,
    )


def plotbox(x, y, w, h):
    return f.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def key(x, y, msg, color):
    block(x, y + 4, 13, 5, color)
    put(x + 19, y, msg, 12, color=muted)


def section(x, y, title):
    block(x, y, 4, 18, Y)
    put(x + 10, y - 1, title, 17, "bold")


def grid(ax):
    ax.grid(axis="y", color=rule, linewidth=1.2, alpha=0.85)


def mini_table(x, y, width, headers, rows, positions, rowheight=23):
    block(x, y, width, rowheight, "#eeeee7")
    for i, (header, pos) in enumerate(zip(headers, positions)):
        put(x + pos, y + 4, header, 11.3, "bold", align="left" if not i else "right")
    for r, row in enumerate(rows):
        yy = y + (r + 1) * rowheight
        block(x, yy + rowheight - 1, width, 0.7, rule)
        for i, (v, pos) in enumerate(zip(row, positions)):
            put(
                x + pos,
                yy + 4,
                str(v),
                12.6,
                "bold" if i == 0 else "normal",
                align="left" if i == 0 else "right",
            )


# Yellow masthead and a small checker detail from the city's cab livery.
block(0, 0, W, 137, Y)
for i in range(14):
    for j in range(2):
        if (i + j) % 2 == 0:
            block(W - (14 - i) * 10, j * 10, 10, 10, ink)
put(30, 37, "A New York City cab driver’s guide", 49, "bold")
put(
    32,
    102,
    "Does the airport fare cover the wait? Where does the next ride start sooner? What can a tip tell us?",
    20,
)
block(0, 137, W, 40, ink)
put(31, 148, "APRIL 2013", 14, "bold", Y)
put(139, 148, "14,891,164 trips  ·  33,001 driver IDs", 14, color=white)
put(637, 148, "DEC 2024 + JAN 2025", 14, "bold", Y)
put(848, 148, "4,843,624 credit-card trips", 14, color=white)
X = [30, 526, 1022]
cw = 448
for x in [502, 998]:
    block(x, 199, 1, 736, rule)
for x, k, title, scope in zip(
    X,
    ["TRIP ECONOMICS", "PICKUP PATTERNS", "PASSENGER BEHAVIOR"],
    ["Is JFK worth the wait?", "Where is the next fare?", "Do tips reflect delay?"],
    [
        "Midtown departures at the same date and hour",
        "Follow the cab for five minutes after drop-off",
        "Relative trip duration and preset-sized tips",
    ],
):
    put(x, 200, k, 13, "bold", muted)
    put(x, 224, title, 28, "bold")
    put(x, 263, scope, 15)
    block(x, 292, cw, 3, Y)
x = X[0]
section(x, 313, "Hourly fare after counting the gap")
cycles = read("matched_cycles").query("airport == 'JFK' and days == 'Weekdays'")
main = cycles[cycles.limit.eq(90)].sort_values("period")
key(x, 347, "JFK", ink)
key(x + 84, 347, "Manhattan destination", "#b17e00")
ax = plotbox(x + 40, 381, 395, 94)
for field, color in [("air_rate", ink), ("city_rate", "#b17e00")]:
    ax.plot(range(5), main[field], marker="o", color=color, ms=9)
ax.set(
    xticks=range(5),
    xticklabels=main.period,
    yticks=[20, 30, 40],
    yticklabels=["$20", "$30", "$40"],
    ylim=(18, 43),
)
grid(ax)
put(
    x, 505, "Weekday departure hour. Next ride observed within 90 min.", 12, color=muted
)
section(x, 545, "JFK leads at midday, the city at rush hour")
rows = []
for _, r in main.iterrows():
    rows.append(
        [
            r.period,
            f"{r.air_gap:.1f} / {r.city_gap:.1f}",
            f"${r.air_rate:.2f}",
            f"${r.city_rate:.2f}",
        ]
    )
mini_table(
    x,
    578,
    cw,
    ["Hour", "Gap min: JFK / city", "JFK / h", "City / h"],
    rows,
    [6, 250, 347, 440],
    22,
)
section(x, 738, "The PM break-even gap is 40 minutes")
pm = main.set_index("period").loc["16–20"]
cutoff = pm.break_even_min
observed = pm.air_gap
ax = plotbox(x + 12, 783, 419, 66)
ax.set_xlim(0, 60)
ax.set_ylim(0, 1)
ax.axis("off")
ax.hlines(0.32, 0, 60, color=rule, lw=6)
ax.hlines(0.32, cutoff, observed, color=Y, lw=12)
ax.vlines(cutoff, 0.17, 0.72, color=ink, lw=2, linestyle="--")
ax.plot(observed, 0.32, "o", ms=16, color=Y, markeredgecolor=ink)
ax.text(cutoff - 1, 0.79, f"Break-even  {cutoff:.1f}", ha="right", size=12 * scale)
ax.text(
    observed,
    0.79,
    f"Actual  {observed:.1f}",
    ha="center",
    size=12 * scale,
    weight="bold",
)
ax.text(0, 0.02, "0 min", size=10 * scale)
ax.text(60, 0.02, "60 min", ha="right", size=10 * scale)
put(
    x,
    858,
    f"The average gap exceeded break-even by {observed-cutoff:.1f} minutes.\nAt the 90-minute cutoff, {int(pm.n_air)} of {int(pm.airport_total)} JFK trips qualified.\nAt 30 minutes only 119 qualified, and JFK led by $5.49/h.",
    13.1,
)
x = X[1]
section(x, 313, "Busier zones tend to turn cabs around faster")
land = read("dropoffs")
eligible = land[(land.drops >= 500) & (land.n >= 500)]
key(x, 346, "Weekday 07–10", ink)
key(x + 190, 346, "Weekend 00–03", "#ba8200")
ax = plotbox(x + 51, 381, 376, 102)
for win, col in [("Weekday AM", ink), ("Weekend night", "#ba8200")]:
    zz = eligible[eligible.window.eq(win)]
    ax.scatter(zz.hourly, zz.share5, color=col, alpha=0.64, s=45)
ax.set(
    xscale="log",
    xticks=[10, 100, 1000],
    xticklabels=["10", "100", "1,000"],
    yticks=[0, 50, 100],
    yticklabels=["0%", "50%", "100%"],
    ylim=(-1, 101),
)
grid(ax)
put(
    x,
    511,
    "Pickups/hour (log scale) vs. share with next ride in 5 min",
    12,
    color=muted,
)
section(x, 546, "Two neighborhoods trade places across shifts")
zone_rates = land.set_index(["name", "window"]).share5
ax = plotbox(x + 7, 588, 431, 117)
ax.set(xlim=(-0.78, 1.80), ylim=(25, 96))
ax.axis("off")
for name, col, offset in [("Yorkville East", "#956100", 3), ("East Village", ink, -3)]:
    morning = zone_rates.loc[(name, "Weekday AM")]
    night = zone_rates.loc[(name, "Weekend night")]
    ax.plot([0, 1], [morning, night], "-o", color=col, ms=8)
    ax.text(
        -0.04,
        morning + offset,
        f"{name}  {morning:.1f}%",
        ha="right",
        va="center",
        fontsize=11.6 * scale,
        color=col,
    )
    ax.text(
        1.04,
        night,
        f"{night:.1f}%  {name}",
        va="center",
        fontsize=11.6 * scale,
        color=col,
    )
put(x + 140, 708, "Weekday morning", 12, align="center", color=muted)
put(x + 303, 708, "Weekend night", 12, align="center", color=muted)
section(x, 738, "A quieter zone can yield a quicker next fare")
put(
    x,
    774,
    "Upper East Side North averaged 1,318 pickups per hour.\nAfter a drop-off there, 73% of cabs picked up again within\nfive minutes. Yorkville East had 404 pickups/hour and 86%.",
    13.4,
)
put(
    x,
    854,
    "Morning = weekdays 07–10. Night = weekends 00–03.\nThe next ride can start in any zone. These rates describe\ndrivers already there when their previous ride ended.",
    13.4,
)
# Right column: a rate profile, an actual-dollar check, and month-specific estimates.
x = X[2]
section(x, 313, "Tip rates across comparable rides")
key(x, 347, "Preset match", blue)
key(x + 163, 347, "Other amount", orange)


def duration_chart(y, h, data, field, ticks, limits, units):
    ax = plotbox(x + 43, y, 351, h)
    for b, c in [(True, blue), (False, orange)]:
        series = data[data.matched.eq(b)][field].to_numpy()
        ax.plot(np.arange(5), series, "o-", color=c, ms=8.5)
        last = series[-1]
        ax.text(
            4.07,
            last,
            (f"{last:.1f}%" if units == "%" else f"${last:.2f}"),
            color=c,
            va="center",
            fontsize=11.8 * scale,
            clip_on=False,
            fontweight="bold",
        )
    ax.set(
        xlim=(-0.08, 4.12),
        xticks=range(5),
        xticklabels=["≤0.85", "≤1.0", "≤1.2", "≤1.6", ">1.6"],
        ylim=limits,
        yticks=ticks,
        yticklabels=[f"{i}%" if units == "%" else f"${i}" for i in ticks],
    )
    grid(ax)


duration_chart(382, 93, tips, "rate", [0, 10, 20], (0, 23), "%")
put(
    x,
    508,
    "Duration ÷ median for the same date, hour and distance band",
    12,
    color=muted,
)
section(x, 548, "What changes on an $18–20 bill?")
duration_chart(592, 76, fixed, "dollars", [0, 2, 4], (0, 4.5), "$")
put(
    x,
    698,
    "At similar bill sizes, other-amount tips fell from $2.51 to\n$2.07 as rides got slower. Preset matches stayed near $3.90.",
    13.6,
)
section(x, 758, "How much can a $3.80 tip tell the driver?")
put(x, 788, "Illustrative checkout  /  $19.00 pre-tip bill", 12.5, color=muted)
for i, rate in enumerate([0.15, 0.20, 0.25]):
    left = x + i * 151
    block(left, 815, 143, 61, Y if i == 1 else "#f1f1eb")
    put(left + 71.5, 821, f"{rate:.0%}", 20, "bold", align="center")
    put(left + 71.5, 849, f"${19*rate:.2f}", 13.5, align="center")
put(
    x,
    899,
    "A rider who enjoyed the trip and one who routinely tips 20%\ncould leave exactly the same amount.",
    13.1,
)
# Source and interpretation notes, aligned with their respective result columns.
block(0, 970, W, H - 970, "#242421")
for x, title, body in zip(
    X,
    ["FARE MEASURE", "PICKUP MEASURE", "TIP MEASURE"],
    [
        "Base fare excludes tips and costs. City trips are weighted to\nthe departure date and hour of included airport trips.",
        "NYC TLC records. Scatter includes zones with at least 500\npickups and drop-offs per window. Non-links count in totals.",
        "A match is within $0.03 of 15%, 20% or 25% of the pre-tip\nbill. Button clicks and rider satisfaction are unobserved.",
    ],
):
    put(x, 985, title, 12, "bold", Y)
    put(x, 1007, body, 12.6, color=white)
f.savefig(O / "Poster.pdf")
f.savefig(O / "Poster-preview.png", dpi=40)
plt.close(f)
