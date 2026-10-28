"""Step 5. Render header.png (1200 x 630 social card) with Playwright Chromium, using work/header_map.png from step 4.
Fonts: FONT_DIR holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf.
Run: FONT_DIR=/path/to/fonts python3 code/05_header.py
"""
import base64, json, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
FD = os.environ.get("FONT_DIR", "")
img = base64.b64encode(open(os.path.join(ROOT, "work", "header_map.png"), "rb").read()).decode()
MCOL = ["#F7E6BE", "#F3D6A0", "#EFC585", "#EAB16C", "#E49D57", "#DC8746", "#D0723A", "#C05E32", "#AC4C2D", "#953E2A", "#7C3227", "#612622"]
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
C = R["cities"]
ramp = "".join(f'<i style="background:{c}"></i>' for c in MCOL)
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:#F7F0E3;color:#231C16;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.map{{position:absolute;right:-30px;top:150px;width:700px;opacity:1}}
.k{{position:absolute;left:64px;top:52px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#6E6153;display:flex;gap:12px;align-items:center}}
.k b{{background:#C2562E;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:58px;top:86px;margin:0;font:900 68px/.93 Fraunces,Georgia,serif;letter-spacing:-.02em;width:500px}}
h1 em{{font-style:normal;color:#C2562E}}
p{{position:absolute;left:64px;top:388px;width:440px;margin:0;font-size:22px;line-height:1.36}}
p b{{color:#C2562E}}
.f{{position:absolute;left:64px;bottom:36px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#6E6153}}
.lg{{position:absolute;right:56px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;color:#6E6153;display:flex;align-items:center;gap:8px}}
.lg span.r{{display:flex}} .lg i{{display:block;width:18px;height:12px}}
</style></head><body>
<img class="map" src="data:image/png;base64,{img}">
<div class="k"><b>Data study</b><span>Climate · 1970 to 2060</span></div>
<h1>How many months a year are <em>pleasantly warm?</em></h1>
<p>Months with an average high of 18 to 27 °C: <b>{C['now']['mean']:.1f}</b> a year for the average city dweller in 1970 to 2000, <b>{C['fut']['mean']:.1f}</b> by 2041 to 2060. Pick your own band.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<div class="lg">1 <span class="r">{ramp}</span> 12 months</div>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w", encoding="utf-8").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-proxy-server"]); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(800)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
