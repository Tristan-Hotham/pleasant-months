"""Shared readers for the WorldClim grids and GeoNames cities (read in place, nothing copied).

WorldClim 2.1 10 arc-minute GeoTIFFs: 2160 columns x 1080 rows, global extent -180..180, -90..90, row 0 at the north.
The files are LZW-compressed, so tifffile needs the imagecodecs package (pip install imagecodecs).
Edit DATA below if your copies live elsewhere.
"""
import io, os, warnings, zipfile
import numpy as np
import tifffile

DATA = os.environ.get("PM_DATA", "/home/claude/hist/_data13")
NE = os.environ.get("PM_NE", "/home/claude/hist/_data3/ne/geojson")
MODELS = ["MPI-ESM1-2-HR", "UKESM1-0-LL", "IPSL-CM6A-LR"]
NR, NC, RES = 1080, 2160, 1 / 6
LAT = 90 - (np.arange(NR) + 0.5) * RES          # cell-centre latitudes, north to south
LON = -180 + (np.arange(NC) + 0.5) * RES
R_EARTH = 6371.0088
# area of each cell in a row, km2 (exact for a sphere)
ROW_AREA = (R_EARTH ** 2 * np.radians(RES) *
            (np.sin(np.radians(LAT + RES / 2)) - np.sin(np.radians(LAT - RES / 2))))
warnings.filterwarnings("ignore")
import logging; logging.getLogger("tifffile").setLevel(logging.ERROR)


def _clean(a):
    a = a.astype(np.float32)
    a[a < -1e30] = np.nan
    return a


def baseline_tmax():
    """12 x 1080 x 2160 array of 1970 to 2000 mean daily maximum temperature (C), NaN off land."""
    z = zipfile.ZipFile(os.path.join(DATA, "wc2.1_10m_tmax.zip"))
    return np.stack([_clean(tifffile.imread(io.BytesIO(z.read(f"wc2.1_10m_tmax_{m:02d}.tif")))) for m in range(1, 13)])


def future_tmax(model):
    """12 x 1080 x 2160 array for 2041 to 2060, SSP2-4.5, one CMIP6 model (WorldClim downscaled)."""
    a = tifffile.imread(os.path.join(DATA, f"wc2.1_10m_tmax_{model}_ssp245_2041-2060.tif"))
    return _clean(np.moveaxis(a, -1, 0))


def load_all():
    """Baseline B (12 x grid) and the three model grids F (3 x 12 x grid), all rounded to 0.1 C.

    The downscaled CMIP6 grids leave out some land cells that the baseline has (coasts, small islands, lake shores).
    For those I add the nearest covered cell's change (future minus baseline, per model and month) to the baseline.
    Returns B, F, valid (baseline land), filled (cells where the change was borrowed), fill_km (distance borrowed from).
    """
    from scipy.spatial import cKDTree
    B = np.round(baseline_tmax(), 1)
    valid = np.isfinite(B).all(axis=0)
    F = np.stack([future_tmax(m) for m in MODELS])
    have = valid & np.isfinite(F).all(axis=(0, 1))
    filled = valid & ~have
    fill_km = np.zeros(valid.shape, np.float32)
    if filled.any():
        hr, hc = np.nonzero(have); fr, fc = np.nonzero(filled)
        tree = cKDTree(xyz(LAT[hr], LON[hc]))
        d, k = tree.query(xyz(LAT[fr], LON[fc]))
        for j in range(len(MODELS)):
            for m in range(12):
                delta = F[j, m, hr[k], hc[k]] - B[m, hr[k], hc[k]]
                F[j, m, fr, fc] = B[m, fr, fc] + delta
        fill_km[fr, fc] = chord_km(d)
    F[:, :, ~valid] = np.nan
    return B, np.round(F, 1), valid, filled, fill_km


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def chord_km(d):
    return 2 * np.arcsin(np.minimum(np.asarray(d) / 2, 1)) * R_EARTH


def cities():
    """GeoNames cities15000 as a list of dicts (population over 15,000 or capitals)."""
    import csv
    z = zipfile.ZipFile(os.path.join(DATA, "cities15000.zip"))
    rows = []
    txt = io.TextIOWrapper(z.open("cities15000.txt"), encoding="utf-8")
    for r in csv.reader(txt, delimiter="\t", quoting=csv.QUOTE_NONE):
        rows.append(dict(id=int(r[0]), name=r[1], ascii=r[2], lat=float(r[4]), lon=float(r[5]), fclass=r[6], fcode=r[7],
                         cc=r[8], admin1=r[10], pop=int(r[14] or 0)))
    return rows


def count_months(t, lo, hi):
    """Number of months (0 to 12) whose mean daily maximum is within [lo, hi]. t: 12 x ... array."""
    ok = (t >= lo) & (t <= hi)
    return ok.sum(axis=0)
