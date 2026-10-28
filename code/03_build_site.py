"""Step 3. Build index.html from code/page_template.html.

Every number in the text is a {{path|format}} token filled from data/results.json, so the page cannot drift from the
analysis. Facts the template states in words are checked against the data below. The results are embedded; the page
loads its climate grid and city list from data/page/.
Run: python3 code/03_build_site.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


# ---- facts stated in words (page, paper and blog) ----
N = R["named"]; B = R["big"]; L = R["land"]; C = R["cities"]
assert R["meta"]["lo"] == 18 and R["meta"]["hi"] == 27
assert 0.3 < L["now"]["zero"] < 0.37  # "a third"
assert 0.18 < C["now"]["zero"] < 0.22  # "a fifth"
assert C["now"]["zero_hot"] > 0.95 * C["now"]["zero"]  # "almost all because it is too hot"
for nm in ["Lagos", "Kinshasa", "Mumbai", "Bangkok", "Jakarta", "Ho Chi Minh City", "Singapore"]:
    assert N[nm]["now"] == 0, nm
assert L["lat_peak"]["lat0"] == -35 and L["lat_peak"]["now"] == max(p["now"] for p in L["lat_profile"])
north = max(p["now"] for p in L["lat_profile"] if p["lat0"] >= 0); assert L["lat_peak"]["now"] > north
yr = [c["name"] for c in B["year_round_now"]]
assert yr[:8] == ["São Paulo", "Lima", "Addis Ababa", "Caracas", "Cali", "Medellín", "Curitiba", "Ecatepec de Morelos"], yr
assert {c["country"] for c in B["year_round_now"][7:]} == {"Mexico", "Madagascar", "Brazil", "Peru", "Rwanda", "South Africa"}
assert [c["name"] for c in B["year_round_fut"]] == ["Cape Town", "Addis Ababa", "La Paz", "Medellín", "Arequipa"]
assert N["Cape Town"]["now"] < 12 and N["La Paz"]["now"] < 12
assert min(N["Brasília"]["now"], N["Bandung"]["now"], N["Kampala"]["now"]) >= 8
assert [c["name"] for c in B["losses"][:3]] == ["Brasília", "Bandung", "Kampala"]
assert [c["name"] for c in B["gains"][:2]] == ["Bogotá", "Quito"]
assert max(N["Bogotá"]["tn"]) < 18.5  # "a little too cool"
assert R["uk"]["mean_fut"] > R["uk"]["mean_now"]
assert [c["name"] for c in R["countries"]["gainers"][:2]] == ["Sweden", "United Kingdom"]
split = [c["name"] for c in B["split"]]
for nm in ["Paris", "Berlin", "Toronto", "Vienna", "Warsaw", "Moscow"]: assert nm in split, nm
assert C["now"]["best_month"] == "May" and C["fut"]["best_month"] == "April"
assert 0.22 < C["now"]["jul_aug"] < 0.27  # "about a quarter"
for s in R["sensitivity"]:
    assert s["pop_fut"] < s["pop_now"] and s["pop_loss"] > s["pop_gain"], s
assert len(R["sensitivity"]) == 7
mods = L["change"]["models"]
assert min(mods, key=lambda m: m["warming"])["model"] == "MPI-ESM1-2-HR" and max(mods, key=lambda m: m["warming"])["model"] == "UKESM1-0-LL"
cm = C["change"]["models"]
assert min(cm, key=lambda m: m["loss"])["model"] == "MPI-ESM1-2-HR" and max(cm, key=lambda m: m["loss"])["model"] == "UKESM1-0-LL"
assert [c["name"] for c in R["countries"]["top"][:5]] == ["South Africa", "Peru", "Guatemala", "Ethiopia", "Kenya"]
assert [c["name"] for c in R["countries"]["losers"][:2]] == ["Uganda", "Zambia"]

if __name__ == "__main__":
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    slim = {k: v for k, v in R.items() if k in ("meta", "page", "sensitivity", "big")}
    slim["big"] = {k: v for k, v in R["big"].items() if k in ("year_round_now",)}
    html = html.replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in html
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    for bad in ("—", "–"):
        assert bad not in html, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
