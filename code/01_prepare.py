"""Step 1. Prepare: country grid from Natural Earth, and GeoNames cities matched to their WorldClim grid cell.

Writes work/countries.npz (country index for every 10' cell, plus the country table) and data/cities.csv (every
GeoNames city over 15,000 people with the 12 monthly mean daily maxima for 1970 to 2000 and for 2041 to 2060,
the mean of three CMIP6 models, SSP2-4.5, in tenths of a degree rounded to 0.1 C).
Run: python3 code/01_prepare.py
"""
import json, os
import numpy as np, pandas as pd
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
import grid as G

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)

# ---- countries: rasterise Natural Earth 1:50m admin 0 onto the 10' grid (cell centres) ----
ne = json.load(open(os.path.join(G.NE, "ne_50m_admin_0_countries.geojson"), encoding="utf-8"))
SC = 4  # draw at 4x and take the centre sample of each cell
img = Image.new("I", (G.NC * SC, G.NR * SC), 0); dr = ImageDraw.Draw(img)
ctab = []
for i, f in enumerate(ne["features"], start=1):
    p = f["properties"]
    iso = p.get("ISO_A2_EH") if p.get("ISO_A2") in (None, "-99") else p["ISO_A2"]
    ctab.append(dict(k=i, iso=iso if iso and iso != "-99" else "", name=p["NAME"], admin=p["ADMIN"], continent=p["CONTINENT"]))
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        for j, ring in enumerate(poly):
            xy = [((x + 180) / G.RES * SC, (90 - y) / G.RES * SC) for x, y in ring]
            if len(xy) > 2: dr.polygon(xy, fill=i if j == 0 else 0)
a = np.array(img, dtype=np.int32)[SC // 2::SC, SC // 2::SC]
assert a.shape == (G.NR, G.NC)
np.savez_compressed(os.path.join(ROOT, "work", "countries.npz"), grid=a.astype(np.uint16))
pd.DataFrame(ctab).to_csv(os.path.join(ROOT, "work", "country_table.csv"), index=False)
print("country grid: cells with a country", int((a > 0).sum()))

# ---- climate grids ----
B, F, valid, filled, fill_km = G.load_all()
Fm = np.round(F.mean(axis=0), 1)
na = G.LAT > -60
print("baseline land cells", int(valid.sum()), "outside Antarctica", int(valid[na].sum()),
      "future change borrowed from a neighbour", int(filled[na].sum()), "median km", float(np.median(fill_km[filled & na[:, None]])))

# ---- cities: nearest land cell on the sphere ----
C = pd.DataFrame(G.cities())
rr, cc = np.nonzero(valid)
tree = cKDTree(G.xyz(G.LAT[rr], G.LON[cc]))
d, k = tree.query(G.xyz(C.lat.values, C.lon.values))
C["cell_row"], C["cell_col"] = rr[k], cc[k]
C["cell_lat"], C["cell_lon"] = np.round(G.LAT[rr[k]], 4), np.round(G.LON[cc[k]], 4)
C["cell_km"] = np.round(G.chord_km(d), 1)
C["future_borrowed"] = filled[C.cell_row, C.cell_col].astype(int)
# country name from Natural Earth by ISO code (GeoNames codes); fall back to the code
names = {}
for r in ctab:
    if r["iso"] and r["iso"] not in names: names[r["iso"]] = r["name"]
names.update({"XK": "Kosovo", "GB": "United Kingdom", "US": "United States", "CN": "China", "RU": "Russia", "BQ": "Caribbean Netherlands",
              "CC": "Cocos (Keeling) Islands", "CX": "Christmas Island", "GF": "French Guiana", "GI": "Gibraltar", "GP": "Guadeloupe",
              "MQ": "Martinique", "RE": "Réunion", "SJ": "Svalbard and Jan Mayen", "TW": "Taiwan", "YT": "Mayotte"})
C["country"] = C.cc.map(lambda c: names.get(c, c))
for m in range(12):
    C[f"now_{m + 1:02d}"] = B[m, C.cell_row, C.cell_col]
    C[f"fut_{m + 1:02d}"] = Fm[m, C.cell_row, C.cell_col]
for j, mod in enumerate(G.MODELS):
    for m in range(12):
        C[f"{mod}_{m + 1:02d}"] = F[j, m, C.cell_row, C.cell_col]
C = C.sort_values("pop", ascending=False).reset_index(drop=True)
keep = ["id", "name", "ascii", "cc", "country", "admin1", "fcode", "lat", "lon", "pop", "cell_lat", "cell_lon", "cell_km", "future_borrowed"]
C[keep + [f"now_{m:02d}" for m in range(1, 13)] + [f"fut_{m:02d}" for m in range(1, 13)]].rename(
    columns={"id": "geonameid", "pop": "population"}).to_csv(os.path.join(ROOT, "data", "cities.csv"), index=False, float_format="%.1f")
C.to_pickle(os.path.join(ROOT, "work", "cities_full.pkl"))
print("cities", len(C), "population", int(C["pop"].sum()), "max distance to a land cell km", C.cell_km.max(),
      "over 20 km", int((C.cell_km > 20).sum()))
print("unnamed countries", sorted(set(c for c in C.cc if c not in names)))
