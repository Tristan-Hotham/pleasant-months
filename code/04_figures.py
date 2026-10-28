"""Step 4. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png).
Maps are drawn from the 10' grid in the Equal Earth projection (no web tiles). Every number comes from the grids,
data/results.json or data/cities.csv. Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono); falls back to defaults.
Also writes work/header_map.png for the social card (step 5).
Run: FONT_DIR=/path/to/fonts python3 code/04_figures.py
"""
import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib import font_manager as fm
from matplotlib.colors import to_rgb
import grid as G

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
FD = os.environ.get("FONT_DIR", "")
SER, MONO = "DejaVu Serif", "DejaVu Sans Mono"
DISP = None
if FD and os.path.exists(os.path.join(FD, "FrauncesVar.ttf")):
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
        fm.fontManager.addfont(os.path.join(FD, f))
    SER, MONO = "Source Serif 4", "IBM Plex Mono"
    DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=800)
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#6E6153", "axes.labelcolor": "#231C16",
                     "xtick.color": "#6E6153", "ytick.color": "#6E6153", "axes.spines.top": False, "axes.spines.right": False})
BG, FG, MUT, RULE, OCEAN = "#F7F0E3", "#231C16", "#6E6153", "#E0D4BE", "#E3DACA"
NOW, FUT = "#231C16", "#C2562E"
MCOL = ["#F7E6BE", "#F3D6A0", "#EFC585", "#EAB16C", "#E49D57", "#DC8746", "#D0723A", "#C05E32", "#AC4C2D", "#953E2A", "#7C3227", "#612622"]
ZCOLD, ZHOT = "#C7D5E2", "#D9C3D3"
CHG = {-6: "#5E1F3D", -5: "#6E2747", -4: "#7F3152", -3: "#985072", -2: "#B67C97", -1: "#D7B2C2", 0: "#E6E1D8", 1: "#B3D6D3", 2: "#82BDB9",
       3: "#57A19E", 4: "#348583", 5: "#216C6B", 6: "#155756"}
LO, HI = 18.0, 27.0
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
MON = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
MON3 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---- grids ----
B, F, valid, filled, fill_km = G.load_all()
Fm = np.round(F.mean(axis=0), 1)
land = valid & (G.LAT > -60)[:, None]
nb, nf = G.count_months(B, LO, HI), G.count_months(Fm, LO, HI)
def zero_class(t, n):
    z = np.zeros(n.shape, np.int8)
    z[(n == 0) & (np.nanmax(t, axis=0) < LO)] = 1
    z[(n == 0) & (np.nanmin(t, axis=0) > HI)] = 2
    return z
zb, zf = zero_class(B, nb), zero_class(Fm, nf)

# ---- Equal Earth ----
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = np.sqrt(3) / 2
def ee(lon, lat):
    th = np.arcsin(M * np.sin(np.radians(lat))); l = np.radians(lon)
    x = 2 * np.sqrt(3) * l * np.cos(th) / (3 * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1))
    y = A4 * th ** 9 + A3 * th ** 7 + A2 * th ** 3 + A1 * th
    return x, y
def ee_inv(x, y):
    th = y.copy()
    for _ in range(12):
        f = A4 * th ** 9 + A3 * th ** 7 + A2 * th ** 3 + A1 * th - y
        d = 9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1
        th = th - f / d
    lat = np.degrees(np.arcsin(np.clip(2 * np.sin(th) / np.sqrt(3), -1, 1)))
    lon = np.degrees(3 * x * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1) / (2 * np.sqrt(3) * np.cos(th)))
    return lon, lat
XMAX = ee(180, 0)[0]; YTOP = ee(0, 84)[1]; YBOT = ee(0, -57)[1]


def ee_rgba(colour_of, width, lat_min=-57, lat_max=84, lon_min=-180, lon_max=180):
    """colour_of: 1080 x 2160 x 4 float RGBA grid. Returns an image in Equal Earth for the given window."""
    x0, x1 = ee(lon_min, 0)[0], ee(lon_max, 0)[0]
    y0, y1 = ee(0, lat_min)[1], ee(0, lat_max)[1]
    if lon_min > -180:  # regional: use the widest extent at the mid latitude
        mid = (lat_min + lat_max) / 2
        x0, x1 = ee(lon_min, mid)[0], ee(lon_max, mid)[0]
    h = int(width * (y1 - y0) / (x1 - x0))
    X, Y = np.meshgrid(np.linspace(x0, x1, width), np.linspace(y1, y0, h))
    lon, lat = ee_inv(X, Y)
    out = np.zeros((h, width, 4))
    ok = (np.abs(lon) <= 180) & (lat >= lat_min) & (lat <= lat_max)
    r = np.clip(((90 - lat) * 6).astype(int), 0, G.NR - 1); c = np.clip(((lon + 180) * 6).astype(int), 0, G.NC - 1)
    out[ok] = colour_of[r[ok], c[ok]]
    # graticule-free outline of the globe for the world map
    return out, (x0, x1, y0, y1)


def months_rgba(n, z):
    out = np.zeros(n.shape + (4,))
    for k in range(1, 13): out[land & (n == k)] = (*to_rgb(MCOL[k - 1]), 1)
    out[land & (n == 0) & (z == 1)] = (*to_rgb(ZCOLD), 1)
    out[land & (n == 0) & (z == 2)] = (*to_rgb(ZHOT), 1)
    out[land & (n == 0) & (z == 0)] = (*to_rgb("#E2DCD2"), 1)
    return out


def change_rgba(a, b):
    out = np.zeros(a.shape + (4,))
    d = np.clip(b.astype(int) - a.astype(int), -6, 6)
    for k in range(-6, 7): out[land & (d == k)] = (*to_rgb(CHG[k]), 1)
    out[land & (a == 0) & (b == 0)] = (*to_rgb("#FBF8F2"), 1)
    return out


def globe_outline(ax):
    lat = np.linspace(-57, 84, 200)
    xl, yl = ee(np.full_like(lat, -180), lat); xr, yr = ee(np.full_like(lat, 180), lat)
    xs = np.r_[xl, xr[::-1], xl[0]]; ys = np.r_[yl, yr[::-1], yl[0]]
    ax.fill(xs, ys, color=OCEAN, zorder=0, lw=0)


def world_map(path, rgba, legend, w_in=15.2, dpi=100, title=None):
    img, (x0, x1, y0, y1) = ee_rgba(rgba, int(w_in * dpi * 1.4))
    fig = plt.figure(figsize=(w_in, w_in * (y1 - y0) / (x1 - x0) + 1.3), dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0.01, 0.13, 0.98, 0.86]); ax.set_facecolor(BG)
    globe_outline(ax)
    ax.imshow(img, extent=(x0, x1, y0, y1), interpolation="nearest", zorder=1)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
    legend(fig)
    fig.savefig(path, dpi=dpi, facecolor=BG); plt.close(fig)


def legend_months(fig, y=0.06):
    lx = fig.add_axes([0.06, y, 0.5, 0.035]); lx.axis("off"); lx.set_xlim(0, 13); lx.set_ylim(0, 1)
    for k in range(12): lx.add_patch(plt.Rectangle((k, 0), 1, 1, color=MCOL[k]))
    lx.text(0.5, -0.45, "1", ha="center", va="top", fontsize=12, color=FG); lx.text(11.5, -0.45, "12", ha="center", va="top", fontsize=12, color=FG)
    lx.text(6, 1.25, "pleasant months a year (average daily high 18 to 27 °C)", ha="center", va="bottom", fontsize=12, color=FG)
    lx2 = fig.add_axes([0.6, y, 0.38, 0.035]); lx2.axis("off"); lx2.set_xlim(0, 10); lx2.set_ylim(0, 1)
    lx2.add_patch(plt.Rectangle((0, 0), 0.55, 1, color=ZCOLD)); lx2.text(0.8, 0.5, "none: too cool all year", va="center", fontsize=12, color=FG)
    lx2.add_patch(plt.Rectangle((5.3, 0), 0.55, 1, color=ZHOT)); lx2.text(6.1, 0.5, "none: too hot all year", va="center", fontsize=12, color=FG)


def legend_change(fig, y=0.06):
    lx = fig.add_axes([0.2, y, 0.6, 0.035]); lx.axis("off"); lx.set_xlim(-6.5, 6.5); lx.set_ylim(0, 1)
    for k in range(-6, 7): lx.add_patch(plt.Rectangle((k - .5, 0), 1, 1, color=CHG[k]))
    for k in (-6, -3, 0, 3, 6): lx.text(k, -0.45, f"{k:+d}" if k else "0", ha="center", va="top", fontsize=12, color=FG)
    lx.text(0, 1.25, "change in pleasant months, 1970 to 2000 to 2041 to 2060 (three-model mean, SSP2-4.5)", ha="center", va="bottom", fontsize=12, color=FG)
    lx.add_patch(plt.Rectangle((7.2, 0), 0.5, 1, color="#FBF8F2", ec=RULE, clip_on=False)); lx.text(7.9, 0.5, "none in\neither period", va="center", fontsize=11, color=FG, clip_on=False)


for d, dpi in ((PAP, 120), (BLOG, 100)):
    pre = "f_" if d == PAP else "b_"
    world_map(os.path.join(d, pre + "map_now.png"), months_rgba(nb, zb), legend_months, dpi=dpi)
    world_map(os.path.join(d, pre + "map_change.png"), change_rgba(nb, nf), legend_change, dpi=dpi)
print("maps done")

# ---- Europe and the Mediterranean, now and mid-century (blog and paper) ----
def region_pair(path, dpi):
    fig = plt.figure(figsize=(15.2, 7.4), dpi=dpi, facecolor=BG)
    for j, (n, z, lab) in enumerate(((nb, zb, "1970 to 2000"), (nf, zf, "2041 to 2060"))):
        img, (x0, x1, y0, y1) = ee_rgba(months_rgba(n, z), 900, lat_min=27, lat_max=71, lon_min=-25, lon_max=50)
        ax = fig.add_axes([0.01 + j * 0.5, 0.14, 0.48, 0.8]); ax.set_facecolor(OCEAN)
        ax.imshow(img, extent=(x0, x1, y0, y1), interpolation="nearest"); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.axis("off")
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=RULE, lw=1))
        ax.text(x0 + (x1 - x0) * 0.02, y1 - (y1 - y0) * 0.04, lab, fontsize=15, color=FG, va="top", fontweight="bold",
                bbox=dict(fc=BG, ec="none", pad=4))
    legend_months(fig, y=0.045)
    fig.savefig(path, dpi=dpi, facecolor=BG); plt.close(fig)
region_pair(os.path.join(BLOG, "b_europe.png"), 100); region_pair(os.path.join(PAP, "f_europe.png"), 120)

# ---- distribution: land and people ----
def dist_fig(path, dpi):
    fig, axs = plt.subplots(1, 2, figsize=(15.2, 5.6), dpi=dpi, facecolor=BG, sharey=True)
    for ax, grp, lab in ((axs[0], "land", "Share of land outside Antarctica"), (axs[1], "cities", "Share of people in cities of 15,000 or more")):
        ax.set_facecolor(BG); a, b = np.array(R[grp]["now"]["dist"]), np.array(R[grp]["fut"]["dist"])
        x = np.arange(13)
        ax.bar(x - 0.2, a * 100, 0.38, color=NOW, label="1970 to 2000"); ax.bar(x + 0.2, b * 100, 0.38, color=FUT, label="2041 to 2060")
        ax.set_xticks(x); ax.set_xlabel("pleasant months a year", fontsize=12); ax.set_title(lab, fontsize=13, color=FG, loc="left")
        ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
        ax.tick_params(labelsize=11)
    axs[0].legend(frameon=False, fontsize=12)
    fig.tight_layout(); fig.savefig(path, dpi=dpi, facecolor=BG); plt.close(fig)
dist_fig(os.path.join(PAP, "f_dist.png"), 120)

# ---- latitude profile and months ----
def lat_month_fig(path, dpi):
    fig, axs = plt.subplots(1, 2, figsize=(15.2, 6.2), dpi=dpi, facecolor=BG, gridspec_kw=dict(width_ratios=[1, 1.35]))
    ax = axs[0]; ax.set_facecolor(BG)
    P = R["land"]["lat_profile"]; y = [p["lat0"] + 2.5 for p in P]
    ax.plot([p["now"] for p in P], y, color=NOW, lw=2.2, label="1970 to 2000"); ax.plot([p["fut"] for p in P], y, color=FUT, lw=2.2, ls="--", label="2041 to 2060")
    ax.set_yticks([-60, -30, 0, 30, 60, 85]); ax.set_yticklabels(["60°S", "30°S", "0°", "30°N", "60°N", ""]); ax.axhline(0, color=MUT, lw=.8)
    ax.set_xlabel("mean pleasant months a year (land, by area)", fontsize=12); ax.grid(color=RULE); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=11, loc="upper right")
    ax.set_title("By latitude, 5 degree bands", fontsize=13, loc="left", color=FG)
    ax = axs[1]; ax.set_facecolor(BG)
    a, b = np.array(R["cities"]["now"]["by_month"]), np.array(R["cities"]["fut"]["by_month"]); x = np.arange(12)
    ax.bar(x - .2, a * 100, .38, color=NOW, label="1970 to 2000"); ax.bar(x + .2, b * 100, .38, color=FUT, label="2041 to 2060")
    ax.set_xticks(x); ax.set_xticklabels(MON3); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
    ax.set_title("Share of people in cities for whom each month is pleasant", fontsize=13, loc="left", color=FG)
    fig.tight_layout(); fig.savefig(path, dpi=dpi, facecolor=BG); plt.close(fig)
lat_month_fig(os.path.join(PAP, "f_lat_months.png"), 120); lat_month_fig(os.path.join(BLOG, "b_lat_months.png"), 100)

# ---- dumbbell: big and familiar cities ----
NAMES = ["Addis Ababa", "Medellín", "Cape Town", "Bogotá", "São Paulo", "Lima", "Nairobi", "Mexico City", "Sydney", "Johannesburg", "Kunming",
         "Los Angeles", "San Francisco", "Lisbon", "Paris", "Berlin", "London", "Moscow", "New York City", "Tokyo", "Rome", "Madrid", "Cairo", "Delhi",
         "Dubai", "Brasília", "Rio de Janeiro", "Lagos", "Singapore"]
def dumbbell(path, dpi):
    rows = [R["named"][n] for n in NAMES]
    fig = plt.figure(figsize=(15.2, 11.5), dpi=dpi, facecolor=BG); ax = fig.add_axes([0.2, 0.09, 0.56, 0.88]); ax.set_facecolor(BG)
    for i, c in enumerate(rows):
        y = len(rows) - 1 - i
        col = "#2C7A7B" if c["fut"] > c["now"] else ("#8E3B5F" if c["fut"] < c["now"] else MUT)
        ax.plot([c["now"], c["fut"]], [y, y], color=col, lw=2.5, zorder=1)
        ax.scatter([c["now"]], [y], s=80, color=NOW, zorder=2); ax.scatter([c["fut"]], [y], s=80, color=FUT, zorder=3, edgecolor=BG, lw=1)
        ax.text(-0.5, y, f"{c['name']}", ha="right", va="center", fontsize=12.5, color=FG, family=SER)
        # month strips on the right
        for m in range(12):
            for k, (mask, t) in enumerate(((c["pn"], c["tn"]), (c["pf"], c["tf"]))):
                colr = "#E39A3B" if mask[m] == "1" else ("#D7735B" if t[m] > HI else "#B9CCDD")
                fig.patches.append(plt.Rectangle((0.785 + m * 0.0155, 0.09 + (y + .7) / (len(rows) + .4) * 0.88 + 0.0005 - k * 0.0105), 0.0135, 0.0095,
                                                 transform=fig.transFigure, color=colr, figure=fig))
    ax.set_xlim(-0.3, 12.3); ax.set_ylim(-0.7, len(rows) - 0.3); ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xticks(range(0, 13, 2)); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
    ax.set_xlabel("pleasant months a year: black 1970 to 2000, orange 2041 to 2060", fontsize=12, labelpad=6)
    for m in range(12): fig.text(0.785 + m * 0.0155 + 0.0067, 0.975, MON[m], ha="center", fontsize=10, color=MUT)
    fig.text(0.2, 0.012, "Right: each month, 1970 to 2000 (upper half) and 2041 to 2060 (lower half); orange pleasant, red too hot, blue too cool.", fontsize=11, color=MUT)
    fig.savefig(path, dpi=dpi, facecolor=BG); plt.close(fig)
dumbbell(os.path.join(PAP, "f_cities.png"), 120); dumbbell(os.path.join(BLOG, "b_cities.png"), 100)

# ---- city profiles, small multiples (blog) ----
PROF = ["London", "Paris", "São Paulo", "Bogotá", "Cape Town", "Delhi"]
def profiles(path, dpi):
    fig, axs = plt.subplots(2, 3, figsize=(15.2, 8.4), dpi=dpi, facecolor=BG, sharex=True)
    for ax, nm in zip(axs.ravel(), PROF):
        c = R["named"][nm]; ax.set_facecolor(BG); x = np.arange(12)
        ax.axhspan(LO, HI, color="#E9A85A", alpha=.25, lw=0)
        ax.plot(x, c["tn"], color=NOW, lw=2); ax.plot(x, c["tf"], color=FUT, lw=2, ls="--")
        for t, col in ((c["tn"], NOW), (c["tf"], FUT)):
            t = np.array(t); ins = (t >= LO) & (t <= HI)
            ax.scatter(x[ins], t[ins], color=col, s=34, zorder=3); ax.scatter(x[~ins], t[~ins], facecolor=BG, edgecolor=col, s=34, zorder=3)
        ax.set_title(f"{nm}: {c['now']} → {c['fut']} months", fontsize=13.5, loc="left", color=FG, family=SER)
        ax.set_xticks(x); ax.set_xticklabels(MON); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5 if max(c["tf"]) - min(c["tn"]) > 12 else 2))
        ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}°")
    fig.text(0.01, 0.005, "Average daily high by month, °C. Black: 1970 to 2000. Orange dashed: 2041 to 2060 (three-model mean). Band: 18 to 27 °C; filled dots are pleasant months.",
             fontsize=11, color=MUT)
    fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(path, dpi=dpi, facecolor=BG); plt.close(fig)
profiles(os.path.join(BLOG, "b_profiles.png"), 100)
print("figures written")

# ---- transparent world map for the social card and the collage ----
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
img, ext = ee_rgba(months_rgba(nb, zb), 1400)
plt.imsave(os.path.join(ROOT, "work", "header_map.png"), img)
img, ext = ee_rgba(months_rgba(nf, zf), 1400)
plt.imsave(os.path.join(ROOT, "work", "map_fut.png"), img)
img, ext = ee_rgba(change_rgba(nb, nf), 1400)
plt.imsave(os.path.join(ROOT, "work", "map_change.png"), img)
json.dump(dict(extent=ext), open(os.path.join(ROOT, "work", "map_extent.json"), "w"))
print("work maps written")
