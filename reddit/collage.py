"""r/dataisbeautiful collage: reddit/pleasant_months.png (2400 x 3000), light warm sand.
Maps are recomputed from the WorldClim grids (code/grid.py, which needs tifffile with imagecodecs); every number comes from
../data/results.json. Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono).
Run from this folder: FONT_DIR=/path/to/fonts python3 collage.py
"""
import json, os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import to_rgb
from matplotlib.patches import Wedge

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "code"))
import grid as G
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, OCEAN, HOT = "#F6EEDD", "#231C16", "#6E6153", "#E6DCC8", "#C2562E"
MCOL = ["#F7E6BE", "#F3D6A0", "#EFC585", "#EAB16C", "#E49D57", "#DC8746", "#D0723A", "#C05E32", "#AC4C2D", "#953E2A", "#7C3227", "#612622"]
ZCOLD, ZHOT = "#C7D5E2", "#D9C3D3"
CHG = {-6: "#5E1F3D", -5: "#6E2747", -4: "#7F3152", -3: "#985072", -2: "#B67C97", -1: "#D7B2C2", 0: "#E9E4DA", 1: "#B3D6D3", 2: "#82BDB9",
       3: "#57A19E", 4: "#348583", 5: "#216C6B", 6: "#155756"}
PLEAS, COOL, HOTM = "#E39A3B", "#AFC4D8", "#D7735B"
LO, HI = 18.0, 27.0
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
C, L, B = R["cities"], R["land"], R["big"]

# ---- grids ----
Bt, F, valid, _, _ = G.load_all()
Fm = np.round(F.mean(axis=0), 1)
land = valid & (G.LAT > -60)[:, None]
nb, nf = G.count_months(Bt, LO, HI), G.count_months(Fm, LO, HI)
rgba_now = np.zeros(nb.shape + (4,))
for k in range(1, 13): rgba_now[land & (nb == k)] = (*to_rgb(MCOL[k - 1]), 1)
rgba_now[land & (nb == 0) & (np.nanmax(Bt, axis=0) < LO)] = (*to_rgb(ZCOLD), 1)
rgba_now[land & (nb == 0) & (np.nanmin(Bt, axis=0) > HI)] = (*to_rgb(ZHOT), 1)
rgba_chg = np.zeros(nb.shape + (4,))
d = np.clip(nf.astype(int) - nb.astype(int), -6, 6)
for k in range(-6, 7): rgba_chg[land & (d == k)] = (*to_rgb(CHG[k]), 1)
rgba_chg[land & (nb == 0) & (nf == 0)] = (*to_rgb("#FBF8F2"), 1)

A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
def ee(lon, lat):
    th = np.arcsin(np.sqrt(3) / 2 * np.sin(np.radians(lat))); l = np.radians(lon)
    return (2 * np.sqrt(3) * l * np.cos(th) / (3 * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1)),
            A4 * th ** 9 + A3 * th ** 7 + A2 * th ** 3 + A1 * th)
def ee_img(rgba, width, lat_min=-57, lat_max=84):
    x0, x1 = ee(-180, 0)[0], ee(180, 0)[0]; y0, y1 = ee(0, lat_min)[1], ee(0, lat_max)[1]
    h = int(width * (y1 - y0) / (x1 - x0))
    X, Y = np.meshgrid(np.linspace(x0, x1, width), np.linspace(y1, y0, h))
    th = Y.copy()
    for _ in range(12):
        th -= (A4 * th ** 9 + A3 * th ** 7 + A2 * th ** 3 + A1 * th - Y) / (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1)
    lat = np.degrees(np.arcsin(np.clip(2 * np.sin(th) / np.sqrt(3), -1, 1)))
    lon = np.degrees(3 * X * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1) / (2 * np.sqrt(3) * np.cos(th)))
    out = np.zeros((h, width, 4)); ok = np.abs(lon) <= 180
    r = np.clip(((90 - lat) * 6).astype(int), 0, G.NR - 1); c = np.clip(((lon + 180) * 6).astype(int), 0, G.NC - 1)
    out[ok] = rgba[r[ok], c[ok]]
    return out, (x0, x1, y0, y1)
def globe(ax, ext):
    lat = np.linspace(-57, 84, 200); xl, yl = ee(np.full_like(lat, -180), lat); xr, yr = ee(np.full_like(lat, 180), lat)
    ax.fill(np.r_[xl, xr[::-1]], np.r_[yl, yr[::-1]], color=OCEAN, lw=0, zorder=0)

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.045, 0.975, "How many months a year", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(0.045, 0.932, "are pleasantly warm?", fontproperties=DISP, fontsize=46, color=HOT, va="top")
fig.text(0.045, 0.882, "Months whose average afternoon high is 18 to 27 °C (64 to 81 °F), everywhere on land, for the climate of\n"
         "1970 to 2000 and for 2041 to 2060 (three climate models, a middle emissions path).", family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.3)

# hero map
img, ext = ee_img(rgba_now, 2300)
ax = fig.add_axes([0.01, 0.53, 0.98, 0.30]); ax.set_facecolor(BG); globe(ax, ext)
ax.imshow(img, extent=ext, interpolation="nearest", zorder=1); ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
def lab(lon, lat, txt, dx, dy, ha="left"):
    x, y = ee(lon, lat); x2, y2 = ee(lon + dx, lat + dy)
    ax.annotate(txt, xy=(x, y), xytext=(x2, y2), family=MONO, fontsize=10.5, color=FG, ha=ha, va="center", zorder=5, bbox=dict(fc=BG, ec="none", alpha=.85, pad=2),
                arrowprops=dict(arrowstyle="-", color=FG, lw=.8, shrinkA=2, shrinkB=2))
na = R["named"]
lab(38.75, 9.0, f"Addis Ababa: {na['Addis Ababa']['now']} months,\nand still {na['Addis Ababa']['fut']} by 2041 to 2060", 36, -22)
lab(-46.6, -23.5, f"São Paulo: {na['São Paulo']['now']} months,\n{na['São Paulo']['fut']} by 2041 to 2060", -62, -12, ha="right")
lab(3.4, 6.5, "Lagos: 0, too hot\nin every month", -16, -26, ha="center")
lab(-0.13, 51.5, f"London: {na['London']['now']} → {na['London']['fut']}", -40, 9, ha="right")
# legend
lx = fig.add_axes([0.06, 0.508, 0.42, 0.016]); lx.axis("off"); lx.set_xlim(0, 12); lx.set_ylim(0, 1)
for k in range(12): lx.add_patch(plt.Rectangle((k, 0), 1, 1, color=MCOL[k]))
lx.text(-0.2, 0.5, "1", ha="right", va="center", family=MONO, fontsize=11, color=FG); lx.text(12.2, 0.5, "12 pleasant months", ha="left", va="center", family=MONO, fontsize=11, color=FG)
fig.patches.append(plt.Rectangle((0.66, 0.508), 0.018, 0.016, transform=fig.transFigure, color=ZCOLD, figure=fig))
fig.text(0.683, 0.516, "too cool all year", family=MONO, fontsize=11, color=FG, va="center")
fig.patches.append(plt.Rectangle((0.83, 0.508), 0.018, 0.016, transform=fig.transFigure, color=ZHOT, figure=fig))
fig.text(0.853, 0.516, "too hot all year", family=MONO, fontsize=11, color=FG, va="center")

# change map
fig.text(0.045, 0.478, "BY 2041 TO 2060: MONTHS LOST AND GAINED", family=MONO, fontsize=11.5, color=MUT)
img2, ext2 = ee_img(rgba_chg, 1300)
ax2 = fig.add_axes([0.02, 0.29, 0.56, 0.18]); ax2.set_facecolor(BG); globe(ax2, ext2)
ax2.imshow(img2, extent=ext2, interpolation="nearest", zorder=1); ax2.set_xlim(ext2[0], ext2[1]); ax2.set_ylim(ext2[2], ext2[3]); ax2.set_aspect("equal"); ax2.axis("off")
cx = fig.add_axes([0.08, 0.272, 0.44, 0.012]); cx.axis("off"); cx.set_xlim(-6.5, 6.5); cx.set_ylim(0, 1)
for k in range(-6, 7): cx.add_patch(plt.Rectangle((k - .5, 0), 1, 1, color=CHG[k]))
cx.text(-6.8, 0.5, "6 fewer", ha="right", va="center", family=MONO, fontsize=10.5, color=FG); cx.text(6.8, 0.5, "6 more", ha="left", va="center", family=MONO, fontsize=10.5, color=FG)

# big numbers
tx = fig.add_axes([0.61, 0.255, 0.37, 0.225]); tx.axis("off"); tx.set_xlim(0, 1); tx.set_ylim(0, 1)
items = [
    (f"{C['now']['mean']:.1f} → {C['fut']['mean']:.1f}", f"pleasant months a year for the average\nperson in a city of 15,000 or more"),
    (f"{C['change']['loss'] * 100:.0f}% / {C['change']['gain'] * 100:.0f}%", "of those city dwellers lose / gain\nat least one pleasant month"),
    (f"{B['all12_now']} → {B['all12_fut']}", f"of {B['n']} cities over a million with all\ntwelve months pleasant"),
    (f"{B['split_n']}", f"big cities where summer gets too hot and the\nseason splits in two, like Paris"),
]
for i, (big, small) in enumerate(items):
    y = 1.0 - i * 0.25
    parts = big.split(" → ")
    t0 = tx.text(0, y, parts[0], fontproperties=DISP, fontsize=26, color=HOT if i % 2 == 0 else FG, va="top")
    if len(parts) == 2:
        fig.canvas.draw(); bb = t0.get_window_extent().transformed(tx.transAxes.inverted())
        t1 = tx.text(bb.x1 + 0.02, y - 0.04, "→", family=MONO, fontsize=20, color=MUT, va="top")
        fig.canvas.draw(); bb = t1.get_window_extent().transformed(tx.transAxes.inverted())
        tx.text(bb.x1 + 0.02, y, parts[1], fontproperties=DISP, fontsize=26, color=HOT if i % 2 == 0 else FG, va="top")
    tx.text(0, y - 0.125, small, family=SER, fontsize=11.5, color=FG, va="top", linespacing=1.15)

# rings: six cities
fig.text(0.045, 0.238, "TWELVE MONTHS, INNER RING 1970 TO 2000, OUTER RING 2041 TO 2060", family=MONO, fontsize=11.5, color=MUT)
RING = ["London", "Paris", "São Paulo", "Bogotá", "Cape Town", "Delhi"]
for i, nm in enumerate(RING):
    c = na[nm]
    a = fig.add_axes([0.02 + i * 0.163, 0.094, 0.15, 0.135]); a.set_xlim(-1.25, 1.25); a.set_ylim(-1.25, 1.25); a.set_aspect("equal"); a.axis("off")
    col = lambda t: PLEAS if LO <= t <= HI else (COOL if t < LO else HOTM)
    for m in range(12):
        th1 = 90 - m * 30; th0 = th1 - 30
        a.add_patch(Wedge((0, 0), 0.68, th0 + 2, th1 - 2, width=0.3, color=col(c["tn"][m])))
        a.add_patch(Wedge((0, 0), 1.0, th0 + 2, th1 - 2, width=0.28, color=col(c["tf"][m])))
        ang = np.radians(th1 - 15); a.text(1.14 * np.cos(ang), 1.14 * np.sin(ang), "JFMAMJJASOND"[m], ha="center", va="center", family=MONO, fontsize=8.5, color=MUT)
    a.text(0, 0.02, f"{c['now']}→{c['fut']}", ha="center", va="center", family=MONO, fontsize=11, color=FG)
    fig.text(0.095 + i * 0.163, 0.080, nm, ha="center", family=SER, fontsize=13, color=FG, fontweight="semibold")
for j, (cc, t) in enumerate(((PLEAS, "pleasant"), (COOL, "too cool"), (HOTM, "too hot"))):
    fig.patches.append(plt.Rectangle((0.66 + j * 0.11, 0.236), 0.014, 0.011, transform=fig.transFigure, color=cc, figure=fig))
    fig.text(0.678 + j * 0.11, 0.2415, t, family=MONO, fontsize=10.5, color=FG, va="center")

fig.text(0.045, 0.062, "Data: WorldClim 2.1 monthly average daily maximum, 1970 to 2000, 10 arc-minutes, and WorldClim downscaled CMIP6, 2041 to 2060, SSP2-4.5,\n"
         "mean of MPI-ESM1-2-HR, UKESM1-0-LL and IPSL-CM6A-LR (Fick and Hijmans 2017, CC BY 4.0). Cities: GeoNames cities15000 (CC BY 4.0).\n"
         "Highs only: humidity, rain and nights are ignored. Equal Earth projection, Antarctica omitted.\nAnalysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9, color=MUT, va="top", linespacing=1.4)
fig.savefig(os.path.join(HERE, "pleasant_months.png"), dpi=200, facecolor=BG)
print("collage written")
