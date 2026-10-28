"""Step 6. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Pleasant_Months.tex and compile it with xelatex (figures from step 4).
Run: python3 code/06_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Pleasant_Months"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}".replace("-", "$-$")
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


yr = "".join(f"{tex(c['name'])} & {tex(c['country'])} & {c['pop'] / 1e6:.1f} & {c['now']} & {c['fut']} & {tex(c['pf_txt'])}\\\\\n" for c in R["big"]["year_round_now"])
TYR = ("\\begin{table}[tbp]\\centering\\small\\caption{Cities of a million people or more (GeoNames) with twelve pleasant months in 1970 to 2000, "
       "band 18 to 27~\\textdegree C. Later: 2041 to 2060, three-model mean, SSP2-4.5.}\\label{tab:yr}"
       "\\begin{tabular}{llrrrl}\\toprule City & Country & Population (m) & Now & Later & Pleasant months later\\\\\\midrule\n" + yr + "\\bottomrule\\end{tabular}\\end{table}")
cr = lambda c: f"{tex(c['name'])} & {c['pop'] / 1e6:.1f} & {c['cities']} & {c['now']:.2f} & {c['fut']:.2f} & {c['change']:+.2f}\\\\\n".replace("+", "$+$").replace("-", "$-$")
CC = R["countries"]
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Population-weighted pleasant months a year by country, band 18 to 27~\\textdegree C, for countries with at least "
      f"{CC['min_pop'] / 1e6:.0f} million people in GeoNames cities and at least {CC['min_cities']} such cities ({CC['n']} countries). Later: 2041 to 2060, three-model mean, SSP2-4.5."
      "}\\label{tab:ctry}\\begin{tabular}{lrrrrr}\\toprule Country & People in cities (m) & Cities & Now & Later & Change\\\\\\midrule\n"
      "\\multicolumn{6}{l}{\\emph{Most pleasant months now}}\\\\\n" + "".join(cr(c) for c in CC["top"][:10]) +
      "\\midrule\\multicolumn{6}{l}{\\emph{Largest losses}}\\\\\n" + "".join(cr(c) for c in CC["losers"][:6]) +
      "\\midrule\\multicolumn{6}{l}{\\emph{Largest gains}}\\\\\n" + "".join(cr(c) for c in CC["gainers"][:6]) + "\\bottomrule\\end{tabular}\\end{table}")
sr = "".join(f"{s['lo']} to {s['hi']} & {s['land_now']:.2f} & {s['land_fut']:.2f} & {s['pop_now']:.2f} & {s['pop_fut']:.2f} & {s['pop_loss'] * 100:.0f} & {s['pop_gain'] * 100:.0f} & {s['big_loss']} & {s['big_gain']}\\\\\n" for s in R["sensitivity"])
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sensitivity to the band. Mean pleasant months a year on land (area-weighted, outside Antarctica) and for people in GeoNames cities "
      "(population-weighted), 1970 to 2000 and 2041 to 2060 (three-model mean, SSP2-4.5); percentage of city dwellers whose count falls or rises; number of the "
      f"{R['big']['n']} big cities whose count falls or rises.}}\\label{{tab:sens}}"
      "\\begin{tabular}{lrrrrrrrr}\\toprule & \\multicolumn{2}{c}{Land} & \\multicolumn{2}{c}{Cities} & \\multicolumn{2}{c}{\\% of people} & \\multicolumn{2}{c}{Big cities}\\\\"
      "Band (\\textdegree C) & Now & Later & Now & Later & Lose & Gain & Lose & Gain\\\\\\midrule\n" + sr + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_YR}}", TYR).replace("{{TABLE_CTRY}}", TC).replace("{{TABLE_SENS}}", TS)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper written", r.returncode)
