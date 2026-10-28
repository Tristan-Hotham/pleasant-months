"""Step 7. Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader (numbers inside them are filled).
Run: python3 code/07_release.py
"""
import importlib.util, json, os, re, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "03_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--"): assert bad not in vis, bad
open(os.path.join(ROOT, "release", "blog", "post.html"), "w", encoding="utf-8").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
C = R["cities"]
meta = dict(
    title="How many months a year are pleasantly warm?",
    slug="pleasant-months",
    excerpt=(f"Count the months whose average afternoon high is 18 to 27 °C and the average city dweller gets {C['now']['mean']:.1f} a year. "
             f"By 2041 to 2060 it is {C['fut']['mean']:.1f}: months are lost at the hot end, gained at the cool end, and you can pick your own band."),
    seo_description=f"A world map of pleasant months a year, now and in 2041 to 2060: {C['now']['mean']:.1f} falling to {C['fut']['mean']:.1f} for city dwellers. Set your own band.",
    tags=["climate", "weather", "climate change", "maps", "cities", "WorldClim", "data"],
    header_alt=(f"Title card reading 'How many months a year are pleasantly warm?' in dark ink and terracotta on warm sand, beside a world map shaded from pale apricot "
                f"(one pleasant month) to deep terracotta (twelve), with the tropics in pale mauve (too hot all year) and the far north in pale blue (too cool). "
                f"Text: months with an average high of 18 to 27 °C, {C['now']['mean']:.1f} a year for the average city dweller in 1970 to 2000, {C['fut']['mean']:.1f} by 2041 to 2060."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in ("—", "–", "--"): assert bad not in str(v)
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

NAME = "Hotham_Pleasant_Months"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex"), encoding="utf-8").read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~\\textdegree C", " °C").replace("\\textdegree", "°")
assert "\\" not in ab and "$" not in ab, ab
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="How Many Months a Year Are Pleasantly Warm? Pleasant Months in the Climate of 1970 to 2000 and 2041 to 2060 from WorldClim",
    description_html=(f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/pleasant-months/. Data and code: https://github.com/Tristan-Hotham/pleasant-months. "
                      "Blog post: to follow.</p><p>Derived from WorldClim 2.1 and WorldClim downscaled CMIP6 data (Fick and Hijmans 2017; CC BY 4.0) and GeoNames (CC BY 4.0). "
                      "The paper, data and figures are released under CC BY 4.0; the code under the MIT licence.</p>"),
    keywords=["climate", "pleasant weather", "temperature", "thermal comfort", "WorldClim", "CMIP6", "SSP2-4.5", "cities", "climate change", "interactive map"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/pleasant-months", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/pleasant-months/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://www.worldclim.org/data/worldclim21.html", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.worldclim.org/data/cmip6/cmip6climate.html", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://doi.org/10.1002/joc.5086", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://download.geonames.org/export/dump/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["city_pleasant_months_18_27C.csv", "cities.csv", "countries.csv", "results.json",
          "pleasant_months_18_27C_1970_2000.asc.gz", "pleasant_months_18_27C_2041_2060.asc.gz"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "pleasant-months_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data", "data/page"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"pleasant-months/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"pleasant-months/{f}")
words = len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split())
print("release files written; post words:", words, "abstract words:", len(ab.split()))
