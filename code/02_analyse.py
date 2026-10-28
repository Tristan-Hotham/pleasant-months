"""Step 2. Analyse: every number for the page, paper, blog and collage goes into data/results.json.
Also writes the data tables (data/*.csv, data/*.asc.gz) and the compact page data (data/page/).

A "pleasant month" is a calendar month whose mean daily maximum temperature (WorldClim, 10' grid) lies within the
band, inclusive. Default band 18 to 27 C. "Now" is the 1970 to 2000 normal; "mid-century" is 2041 to 2060 under
SSP2-4.5, the mean of three CMIP6 models (MPI-ESM1-2-HR, UKESM1-0-LL, IPSL-CM6A-LR) as downscaled by WorldClim.
Land statistics: all land cells north of 60 S (Antarctica left out), weighted by true cell area.
City statistics: GeoNames cities over 15,000 people, weighted by their GeoNames population, leaving out
sections of cities (PPLX) and historical, abandoned or destroyed places so people are not counted twice.
Run: python3 code/02_analyse.py
"""
import gzip, json, os
import numpy as np, pandas as pd
import grid as G

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data"); PAGE = os.path.join(DATA, "page"); os.makedirs(PAGE, exist_ok=True)
LO, HI = 18.0, 27.0
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
R = {}

B, F, valid, filled, fill_km = G.load_all()
Fm = np.round(F.mean(axis=0), 1)
land = valid & (G.LAT > -60)[:, None]
W = np.broadcast_to(G.ROW_AREA[:, None], valid.shape)
w = W[land]; wsum = w.sum()
b, fm = B[:, land], Fm[:, land]
fmod = F[:, :, land]
nb, nf = G.count_months(b, LO, HI), G.count_months(fm, LO, HI)
nmod = [G.count_months(fmod[j], LO, HI) for j in range(3)]
ws = lambda mask: float(w[mask].sum() / wsum)


def why_zero(t, n, lo, hi):
    """0 = has pleasant months, 1 = too cold all year, 2 = too hot all year, 3 = jumps over the band."""
    out = np.zeros(n.shape, np.int8)
    z = n == 0
    out[z & (t.max(axis=0) < lo)] = 1
    out[z & (t.min(axis=0) > hi)] = 2
    out[z & (out == 0)] = 3
    return out


zb, zf = why_zero(b, nb, LO, HI), why_zero(fm, nf, LO, HI)
R["meta"] = dict(lo=LO, hi=HI, lo_f=LO * 9 / 5 + 32, hi_f=HI * 9 / 5 + 32, models=G.MODELS, scenario="SSP2-4.5",
                 cells=int(land.sum()), cells_all=int(valid.sum()), land_km2=float(wsum),
                 filled_cells=int(filled[land].sum()), filled_share=float(W[land & filled].sum() / wsum),
                 filled_median_km=float(np.median(fill_km[land & filled])), retrieved_text="28 October 2026")
L = {}
for tag, n, z, t in (("now", nb, zb, b), ("fut", nf, zf, fm)):
    L[tag] = dict(dist=[ws(n == k) for k in range(13)], mean=float((n * w).sum() / wsum),
                  ge6=ws(n >= 6), all12=ws(n == 12), zero=ws(n == 0), km2_12=float(w[n == 12].sum()),
                  zero_cold=ws(z == 1), zero_hot=ws(z == 2), zero_jump=ws(z == 3),
                  by_month=[ws((t[m] >= LO) & (t[m] <= HI)) for m in range(12)])
d = nf - nb
L["change"] = dict(gain=ws(d > 0), loss=ws(d < 0), same=ws(d == 0), mean=float((d * w).sum() / wsum),
                   gain2=ws(d >= 2), loss2=ws(d <= -2),
                   models=[dict(model=G.MODELS[j], mean_now=L["now"]["mean"], mean_fut=float((nmod[j] * w).sum() / wsum),
                                gain=ws(nmod[j] > nb), loss=ws(nmod[j] < nb),
                                warming=float(((fmod[j] - b).mean(axis=0) * w).sum() / wsum)) for j in range(3)],
                   warming=float(((fm - b).mean(axis=0) * w).sum() / wsum))
# latitude profile, 5 degree bands
lat_c = np.broadcast_to(G.LAT[:, None], valid.shape)[land]
prof = []
for a in range(-60, 90, 5):
    m = (lat_c >= a) & (lat_c < a + 5)
    if w[m].sum() == 0: continue
    prof.append(dict(lat0=a, lat1=a + 5, now=float((nb[m] * w[m]).sum() / w[m].sum()), fut=float((nf[m] * w[m]).sum() / w[m].sum()),
                     km2=float(w[m].sum())))
L["lat_profile"] = prof
peak = max(prof, key=lambda p: p["now"])
L["lat_peak"] = peak
R["land"] = L

# ---- 10' grids for reuse (ESRI ASCII grid, gzipped): pleasant months now and mid-century, default band ----
def write_asc(path, arr):
    hdr = f"ncols {G.NC}\nnrows {G.NR}\nxllcorner -180\nyllcorner -90\ncellsize {G.RES:.12f}\nNODATA_value -1\n"
    with gzip.open(path, "wt") as fh:
        fh.write(hdr)
        for row in arr: fh.write(" ".join(map(str, row)) + "\n")
for tag, n in (("1970_2000", nb), ("2041_2060", nf)):
    full = np.full(valid.shape, -1, np.int16); full[land] = n
    write_asc(os.path.join(DATA, f"pleasant_months_18_27C_{tag}.asc.gz"), full)

# ---- countries, area weighted ----
cg = np.load(os.path.join(ROOT, "work", "countries.npz"))["grid"]
ct = pd.read_csv(os.path.join(ROOT, "work", "country_table.csv"), keep_default_na=False)
ck = cg[land]
rows = []
for r in ct.itertuples():
    m = ck == r.k
    if not m.any(): continue
    ww = w[m]
    rows.append(dict(k=r.k, iso=r.iso, name=r.name, continent=r.continent, cells=int(m.sum()), km2=float(ww.sum()),
                     months_now=float((nb[m] * ww).sum() / ww.sum()), months_fut=float((nf[m] * ww).sum() / ww.sum())))
CA = pd.DataFrame(rows)
# merge split features that share an ISO code (rare)
CA = CA.sort_values("km2", ascending=False)
CA["change"] = CA.months_fut - CA.months_now

# ---- cities ----
C = pd.read_pickle(os.path.join(ROOT, "work", "cities_full.pkl"))
now = C[[f"now_{m:02d}" for m in range(1, 13)]].to_numpy().T
fut = C[[f"fut_{m:02d}" for m in range(1, 13)]].to_numpy().T
mods = [C[[f"{mod}_{m:02d}" for m in range(1, 13)]].to_numpy().T for mod in G.MODELS]
C["n_now"], C["n_fut"] = G.count_months(now, LO, HI), G.count_months(fut, LO, HI)
for j, mod in enumerate(G.MODELS): C[f"n_{mod}"] = G.count_months(mods[j], LO, HI)
C["why_now"], C["why_fut"] = why_zero(now, C.n_now.values, LO, HI), why_zero(fut, C.n_fut.values, LO, HI)
C["change"] = C.n_fut - C.n_now
C["pleasant_now"] = ["".join("1" if LO <= t <= HI else "0" for t in col) for col in now.T]
C["pleasant_fut"] = ["".join("1" if LO <= t <= HI else "0" for t in col) for col in fut.T]
DROP = {"PPLX", "PPLH", "PPLQ", "PPLW"}
C["counted"] = (~C.fcode.isin(DROP) & (C.cell_km <= 25)).astype(int)
K = C[C.counted == 1]
P = K["pop"].to_numpy(float); Ps = P.sum()
ps = lambda mask: float(P[np.asarray(mask)].sum() / Ps)
Cs = {}
for tag in ("now", "fut"):
    n = K[f"n_{tag}"].to_numpy(); z = K[f"why_{tag}"].to_numpy(); t = now[:, K.index] if tag == "now" else fut[:, K.index]
    Cs[tag] = dict(dist=[ps(n == k) for k in range(13)], mean=float((n * P).sum() / Ps), ge6=ps(n >= 6), all12=ps(n == 12),
                   zero=ps(n == 0), zero_cold=ps(z == 1), zero_hot=ps(z == 2), zero_jump=ps(z == 3),
                   by_month=[ps((t[m] >= LO) & (t[m] <= HI)) for m in range(12)],
                   median=float(np.interp(0.5, np.cumsum(np.bincount(n, weights=P, minlength=13)) / Ps, np.arange(13))))
dch = K.change.to_numpy()
Cs["change"] = dict(gain=ps(dch > 0), loss=ps(dch < 0), same=ps(dch == 0), mean=float((dch * P).sum() / Ps),
                    models=[dict(model=mod, mean_fut=float((K[f"n_{mod}"] * P).sum() / Ps), loss=ps(K[f"n_{mod}"] < K.n_now),
                                 gain=ps(K[f"n_{mod}"] > K.n_now)) for mod in G.MODELS])
Cs.update(n=int(len(K)), n_all=int(len(C)), pop=float(Ps), dropped_sections=int(C.fcode.isin(DROP).sum()),
          dropped_far=int((C.cell_km > 25).sum()), median_km=float(K.cell_km.median()))
Kn, Kf = now[:, K.index], fut[:, K.index]
lost_heat = ((Kn >= LO) & (Kn <= HI) & (Kf > HI)).any(axis=0)
gain_cold = ((Kn < LO) & (Kf >= LO) & (Kf <= HI)).any(axis=0)
Cs["shift"] = dict(lost_heat=ps(lost_heat), gain_cold=ps(gain_cold), both=ps(lost_heat & gain_cold),
                   months_lost_heat=float((((Kn >= LO) & (Kn <= HI) & (Kf > HI)).sum(axis=0) * P).sum() / Ps),
                   months_gain_cold=float((((Kn < LO) & (Kf >= LO) & (Kf <= HI)).sum(axis=0) * P).sum() / Ps))
def runs(mask):
    """number of separate runs of pleasant months, treating the year as a circle"""
    m = [c == "1" for c in mask]
    if all(m): return 1
    return sum(1 for i in range(12) if m[i] and not m[i - 1])
R["cities"] = Cs


def months_text(mask):
    """'May to September', 'April and May, and September to November', 'all year', 'none'"""
    m = [c == "1" for c in mask]
    if all(m): return "all year"
    if not any(m): return "none"
    start = next(i for i in range(12) if not m[i])  # begin after a gap so runs do not wrap
    parts, i = [], 0
    while i < 12:
        j = (start + i) % 12
        if m[j]:
            k = i
            while k + 1 < 12 and m[(start + k + 1) % 12]: k += 1
            a, b = MONTHS[j], MONTHS[(start + k) % 12]
            parts.append(a if k == i else (f"{a} and {b}" if k == i + 1 else f"{a} to {b}"))
            i = k + 1
        else:
            i += 1
    return ", then ".join(parts)


def crow(r):
    return dict(name=r.name, country=r.country, cc=r.cc, pop=int(r.pop), lat=round(r.lat, 3), lon=round(r.lon, 3),
                now=int(r.n_now), fut=int(r.n_fut), change=int(r.change), pn=r.pleasant_now, pf=r.pleasant_fut,
                pn_txt=months_text(r.pleasant_now), pf_txt=months_text(r.pleasant_fut),
                tn=[round(float(x), 1) for x in now[:, r.Index]], tf=[round(float(x), 1) for x in fut[:, r.Index]],
                models=[int(getattr(r, f"n_{m}".replace("-", "_"), 0)) for m in G.MODELS])


C2 = C.rename(columns={f"n_{m}": f"n_{m}".replace("-", "_") for m in G.MODELS})
K2 = C2[C2.counted == 1]
BIG = K2[K2["pop"] >= 1_000_000]
R["big"] = dict(n=int(len(BIG)), gain=int((BIG.change > 0).sum()), loss=int((BIG.change < 0).sum()), same=int((BIG.change == 0).sum()),
                all12_now=int((BIG.n_now == 12).sum()), all12_fut=int((BIG.n_fut == 12).sum()),
                zero_now=int((BIG.n_now == 0).sum()), zero_fut=int((BIG.n_fut == 0).sum()),
                mean_now=float(BIG.n_now.mean()), mean_fut=float(BIG.n_fut.mean()),
                top_now=[crow(r) for r in BIG.sort_values(["n_now", "pop"], ascending=[False, False]).head(20).itertuples()],
                gains=[crow(r) for r in BIG.sort_values(["change", "pop"], ascending=[False, False]).head(15).itertuples()],
                losses=[crow(r) for r in BIG.sort_values(["change", "pop"], ascending=[True, False]).head(15).itertuples()],
                largest=[crow(r) for r in BIG.sort_values("pop", ascending=False).head(30).itertuples()])
R["big"]["models_loss"] = [int((BIG[f"n_{m}".replace("-", "_")] < BIG.n_now).sum()) for m in G.MODELS]
R["big"]["models_gain"] = [int((BIG[f"n_{m}".replace("-", "_")] > BIG.n_now).sum()) for m in G.MODELS]
R["big"]["split"] = [crow(r) for r in BIG[(BIG.pleasant_now.map(runs) == 1) & (BIG.pleasant_fut.map(runs) >= 2)].sort_values("pop", ascending=False).itertuples()]
R["big"]["split_n"] = len(R["big"]["split"])
R["big"]["year_round_now"] = [crow(r) for r in BIG[BIG.n_now == 12].sort_values("pop", ascending=False).itertuples()]
R["big"]["year_round_fut"] = [crow(r) for r in BIG[BIG.n_fut == 12].sort_values("pop", ascending=False).itertuples()]
R["big"]["year_round_lost"] = [crow(r) for r in BIG[(BIG.n_now == 12) & (BIG.n_fut < 12)].sort_values("pop", ascending=False).itertuples()]

# named cities used in the text
NAMED = {}
for nm, cc in [("London", "GB"), ("Birmingham", "GB"), ("Manchester", "GB"), ("Glasgow", "GB"), ("Edinburgh", "GB"), ("Cardiff", "GB"),
               ("Belfast", "GB"), ("Leeds", "GB"), ("Bristol", "GB"), ("Newcastle upon Tyne", "GB"), ("Plymouth", "GB"), ("Aberdeen", "GB"),
               ("Dublin", "IE"), ("Paris", "FR"), ("Madrid", "ES"), ("Rome", "IT"), ("Athens", "GR"), ("Lisbon", "PT"), ("Berlin", "DE"),
               ("New York City", "US"), ("Los Angeles", "US"), ("San Francisco", "US"), ("Phoenix", "US"), ("Miami", "US"),
               ("Mexico City", "MX"), ("Bogotá", "CO"), ("Quito", "EC"), ("Nairobi", "KE"), ("Addis Ababa", "ET"), ("Kunming", "CN"),
               ("Bengaluru", "IN"), ("Delhi", "IN"), ("Dubai", "AE"), ("Riyadh", "SA"), ("Cairo", "EG"), ("Lagos", "NG"), ("Kinshasa", "CD"),
               ("Singapore", "SG"), ("Jakarta", "ID"), ("Bangkok", "TH"), ("Tokyo", "JP"), ("Shanghai", "CN"), ("Sydney", "AU"),
               ("Cape Town", "ZA"), ("Johannesburg", "ZA"), ("São Paulo", "BR"), ("Rio de Janeiro", "BR"), ("Lima", "PE"), ("Moscow", "RU"),
               ("Reykjavík", "IS"), ("Brasília", "BR"), ("Kigali", "RW"), ("Bandung", "ID"), ("Kampala", "UG"), ("Medellín", "CO"),
               ("Arequipa", "PE"), ("La Paz", "BO"), ("Toronto", "CA"), ("Vienna", "AT"), ("Warsaw", "PL"), ("Mumbai", "IN"), ("Oslo", "NO"), ("Karachi", "PK"), ("Dhaka", "BD"), ("Manila", "PH"), ("Ho Chi Minh City", "VN")]:
    m = C2[(C2.name == nm) & (C2.cc == cc)].sort_values("pop", ascending=False)
    if len(m): NAMED[nm] = crow(next(m.itertuples()))
    else: print("not found", nm)
R["named"] = NAMED
UKc = K2[K2.cc == "GB"]
PUK = UKc["pop"].to_numpy(float)
R["uk"] = dict(n=int(len(UKc)), pop=float(PUK.sum()), mean_now=float((UKc.n_now * PUK).sum() / PUK.sum()), mean_fut=float((UKc.n_fut * PUK).sum() / PUK.sum()),
               zero_now=float(PUK[UKc.n_now.to_numpy() == 0].sum() / PUK.sum()), zero_fut=float(PUK[UKc.n_fut.to_numpy() == 0].sum() / PUK.sum()),
               cities=[crow(r) for r in UKc.sort_values("pop", ascending=False).head(12).itertuples()],
               most_now=[crow(r) for r in UKc.sort_values(["n_now", "pop"], ascending=[False, False]).head(5).itertuples()],
               dist_now=[int((UKc.n_now == k).sum()) for k in range(13)], dist_fut=[int((UKc.n_fut == k).sum()) for k in range(13)])

# ---- countries, population weighted (cities) ----
g = K2.assign(pn=K2.n_now * K2["pop"], pf=K2.n_fut * K2["pop"]).groupby(["cc", "country"]).agg(
    cities=("name", "size"), pop=("pop", "sum"), pn=("pn", "sum"), pf=("pf", "sum")).reset_index()
g["months_now"], g["months_fut"] = g.pn / g["pop"], g.pf / g["pop"]
g["change"] = g.months_fut - g.months_now
CA2 = CA.merge(g[["cc", "cities", "pop", "months_now", "months_fut", "change"]].rename(columns={"cc": "iso", "months_now": "pop_months_now",
                                                                                              "months_fut": "pop_months_fut", "change": "pop_change"}), on="iso", how="outer")
CA2["name"] = CA2.name.fillna(CA2.iso.map(dict(zip(g.cc, g.country))))
CA2 = CA2.sort_values("pop", ascending=False)
CA2.to_csv(os.path.join(DATA, "countries.csv"), index=False, float_format="%.3f",
           columns=["iso", "name", "continent", "cells", "km2", "months_now", "months_fut", "change", "cities", "pop", "pop_months_now", "pop_months_fut", "pop_change"])
QC = CA2[(CA2["pop"] >= 5_000_000) & (CA2.cities >= 5)]
cr = lambda r: dict(iso=r.iso, name=r.name, pop=int(r.pop), cities=int(r.cities), now=float(r.pop_months_now), fut=float(r.pop_months_fut),
                    change=float(r.pop_change), area_now=None if pd.isna(r.months_now) else float(r.months_now),
                    area_fut=None if pd.isna(r.months_fut) else float(r.months_fut))
R["countries"] = dict(min_pop=5_000_000, min_cities=5, n=int(len(QC)),
                      top=[cr(r) for r in QC.sort_values("pop_months_now", ascending=False).head(15).itertuples()],
                      bottom=[cr(r) for r in QC.sort_values("pop_months_now").head(10).itertuples()],
                      losers=[cr(r) for r in QC.sort_values("pop_change").head(10).itertuples()],
                      gainers=[cr(r) for r in QC.sort_values("pop_change", ascending=False).head(10).itertuples()],
                      uk=cr(next(CA2[CA2.iso == "GB"].itertuples())))
AQ = CA2[CA2.km2 >= 100_000].dropna(subset=["months_now"])
R["countries"]["area_top"] = [dict(name=r.name, iso=r.iso, km2=float(r.km2), now=float(r.months_now), fut=float(r.months_fut)) for r in AQ.sort_values("months_now", ascending=False).head(10).itertuples()]

# ---- sensitivity to the band ----
SENS = []
for lo, hi in [(15, 25), (16, 24), (18, 27), (20, 30), (21, 29), (18, 24), (22, 32)]:
    a, c = G.count_months(b, lo, hi), G.count_months(fm, lo, hi)
    pn, pf = G.count_months(now[:, K.index], lo, hi), G.count_months(fut[:, K.index], lo, hi)
    bn, bf = G.count_months(now[:, BIG.index], lo, hi), G.count_months(fut[:, BIG.index], lo, hi)
    SENS.append(dict(lo=lo, hi=hi, land_now=float((a * w).sum() / wsum), land_fut=float((c * w).sum() / wsum),
                     pop_now=float((pn * P).sum() / Ps), pop_fut=float((pf * P).sum() / Ps),
                     pop_loss=ps(pf < pn), pop_gain=ps(pf > pn), big_loss=int((bf < bn).sum()), big_gain=int((bf > bn).sum())))
R["sensitivity"] = SENS

# ---- cities table for reuse ----
out = C2[["id", "name", "country", "cc", "lat", "lon", "pop", "fcode", "cell_km", "counted", "n_now", "n_fut", "change",
          "n_MPI_ESM1_2_HR", "n_UKESM1_0_LL", "n_IPSL_CM6A_LR", "pleasant_now", "pleasant_fut"]]
out.rename(columns={"id": "geonameid", "pop": "population", "n_now": "pleasant_months_1970_2000", "n_fut": "pleasant_months_2041_2060",
                    "change": "change", "pleasant_now": "months_mask_1970_2000", "pleasant_fut": "months_mask_2041_2060"}).to_csv(
    os.path.join(DATA, "city_pleasant_months_18_27C.csv"), index=False)

# ---- page data ----
# grid: 20 arc-minute cells north of 60 S (mean of the 10' land cells in each 2 x 2 block, rounded to 0.1 C).
# Each value is stored as a one-byte code that answers "is t >= L?" and "is t <= H?" exactly for whole-degree L and H:
# code 2n means t is exactly n C, code 2n - 1 means n - 1 < t < n. So t >= L iff code >= 2L, and t <= H iff code <= 2H.
v = land[:900]
vs = v.reshape(450, 2, G.NC // 2, 2); nsub = vs.sum(axis=(1, 3)); pv = nsub > 0
def agg(a):
    s = np.where(v, a, 0).reshape(12, 450, 2, G.NC // 2, 2).sum(axis=(2, 4))
    return s / np.maximum(nsub, 1)
pb, pf_ = agg(np.nan_to_num(B[:, :900])), agg(np.nan_to_num(Fm[:, :900]))
def q(a):
    t = np.round(a[:, pv], 1)
    whole = np.abs(t - np.round(t)) < 1e-6
    return np.clip(np.where(whole, 2 * np.round(t), 2 * np.ceil(t) - 1), -127, 127).astype(np.int8)
qb, qf = q(pb), q(pf_)
# country of each page cell: the most common country among its 10' cells (0 = none)
cg9 = cg[:900].astype(np.int32) * v
blk = cg9.reshape(450, 2, G.NC // 2, 2).transpose(0, 2, 1, 3).reshape(450, G.NC // 2, 4)[pv]
pc = np.array([np.bincount(r[r > 0]).argmax() if (r > 0).any() else 0 for r in blk])
# page country list: Natural Earth features that occur, mapped to ISO and name
keys = sorted(set(pc) - {0})
kmap = {k: i + 1 for i, k in enumerate(keys)}
ctl = ct.set_index("k")
pcountry = np.array([kmap.get(k, 0) for k in pc], np.uint8)
assert len(keys) < 255
mask_bits = np.packbits(pv.ravel())
delta = lambda a: np.diff(a.astype(np.int16), axis=1, prepend=0).astype(np.int8)  # wraps; client undoes with int8 arithmetic
blob = mask_bits.tobytes() + nsub[pv].astype(np.uint8).tobytes() + pcountry.tobytes() + delta(qb).tobytes() + delta(qf).tobytes()
open(os.path.join(PAGE, "grid20.bin.gz"), "wb").write(gzip.compress(blob, 9))
# cities: names and positions in JSON, temperatures in a binary file (tenths of a degree)
cc_list = sorted(set(C2.cc))
ccname = dict(zip(C2.cc, C2.country))
page_c = dict(cc=cc_list, country=[ccname[c] for c in cc_list],
              rows=[[r.name, cc_list.index(r.cc), round(r.lat, 2), round(r.lon, 2), int(r.pop), int(r.counted)] for r in C2.itertuples()])
json.dump(page_c, open(os.path.join(PAGE, "cities.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
tn = np.round(now.T * 10).astype("<i2"); tf = np.round(fut.T * 10).astype("<i2")
md = np.stack([np.clip(np.round((mods[j].T - fut.T) * 10), -127, 127).astype(np.int8) for j in range(3)], axis=1)  # model minus mean
cblob = tn.tobytes() + tf.tobytes() + md.tobytes()
open(os.path.join(PAGE, "cities_t.bin.gz"), "wb").write(gzip.compress(cblob, 9))
R["page"] = dict(ncol=G.NC // 2, nrow=450, res=1 / 3, cells=int(pv.sum()), ncity=int(len(C2)),
                 countries=[dict(iso=ctl.loc[k, "iso"], name=ctl.loc[k, "name"]) for k in keys])
# check: what the page's coarser grid gives at the default band (land share stats)
pw = np.broadcast_to((np.cos(np.radians(90 - (np.arange(450) + .5) / 3)))[:, None], pv.shape)[pv] * nsub[pv]
qn, qfu = G.count_months(qb.astype(int), 2 * LO, 2 * HI), G.count_months(qf.astype(int), 2 * LO, 2 * HI)
R["page"]["check"] = dict(mean_now=float((qn * pw).sum() / pw.sum()), mean_fut=float((qfu * pw).sum() / pw.sum()),
                          ge6_now=float(pw[qn >= 6].sum() / pw.sum()), zero_now=float(pw[qn == 0].sum() / pw.sum()))

# words for the text: the most widely pleasant month
for grp in ("land", "cities"):
    for tag in ("now", "fut"):
        bm = R[grp][tag]["by_month"]; i = int(np.argmax(bm))
        R[grp][tag]["best_month"] = MONTHS[i]; R[grp][tag]["best_share"] = bm[i]
        R[grp][tag]["jul_aug"] = (bm[6] + bm[7]) / 2
R["derived"] = dict(lat_peak_s0=-L["lat_peak"]["lat1"], lat_peak_s1=-L["lat_peak"]["lat0"],city_pop_bn=R["cities"]["pop"] / 1e9, land_km2_12_now_m=L["now"]["km2_12"] / 1e6, land_km2_12_fut_m=L["fut"]["km2_12"] / 1e6,
                    city_mean_drop=R["cities"]["now"]["mean"] - R["cities"]["fut"]["mean"],
                    models_city_loss_min=min(m["loss"] for m in R["cities"]["change"]["models"]),
                    models_city_loss_max=max(m["loss"] for m in R["cities"]["change"]["models"]),
                    models_big_loss_min=min(R["big"]["models_loss"]), models_big_loss_max=max(R["big"]["models_loss"]),
                    warm_min=min(m["warming"] for m in L["change"]["models"]), warm_max=max(m["warming"] for m in L["change"]["models"]))
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps({k: R["land"][k] for k in ("now", "fut")}, default=float)[:1500])
print("change", R["land"]["change"])
print("cities", {k: v for k, v in R["cities"].items() if k not in ("now", "fut")})
print("cities now", R["cities"]["now"]); print("cities fut", R["cities"]["fut"])
print("big", {k: v for k, v in R["big"].items() if not isinstance(v, list)}, R["big"]["models_loss"], R["big"]["models_gain"])
print("page", R["page"]["check"])
for f in sorted(os.listdir(PAGE)): print(f, os.path.getsize(os.path.join(PAGE, f)))
