# How many months a year are pleasantly warm?

A world map of the number of months whose average daily high falls inside a band you choose (default 18 to 27 °C), for the climate of 1970 to 2000 and for 2041 to 2060. The interactive page lets you drag the band, switch between Celsius and Fahrenheit, compare now with mid-century or map the change, look at one month at a time, search any city of 15,000 people or more and rank countries and big cities. Every number on the page is recalculated in the browser as you move the band.

**Interactive version:** https://tristan-hotham.github.io/pleasant-months/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23732576

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results (band 18 to 27 °C)

- Land outside Antarctica has 2.5 pleasant months a year on average in 1970 to 2000. 34% has none: 11.7% too cool all year, 22.3% too hot all year. 1.4% (about 2.0 million km²) has all twelve.
- The average person in the 31,778 GeoNames cities of 15,000 or more (3.9 billion people) has 3.6 pleasant months; 20.5% live where no month is in the band, almost all because it is too hot (Lagos, Kinshasa, Mumbai, Bangkok, Jakarta, Singapore).
- In 2041 to 2060 (mean of MPI-ESM1-2-HR, UKESM1-0-LL and IPSL-CM6A-LR under SSP2-4.5), the city average falls to 2.9 months. 46% of city dwellers lose at least one month and 14% gain one; 26.2% have none.
- Of 560 cities of a million or more, 14 had twelve pleasant months (São Paulo, Lima, Addis Ababa, Caracas, Cali, Medellín and others); by mid-century 5 do (Addis Ababa, Medellín, Arequipa, plus Cape Town and La Paz). 264 big cities lose at least one month, 71 gain.
- In 38 big cities, mostly in the northern mid-latitudes, one pleasant season splits into a spring and an autumn either side of a summer that is too hot: Paris goes from May to September to May and June, then September and October.
- Biggest losers include Brasília (9 to 0 months), Bandung (8 to 0) and Kampala (9 to 1); biggest gainers Bogotá (3 to 11) and Quito (0 to 4). People in UK cities go from 3.2 to 4.3; London from June to September to May to September.
- The direction holds for all seven bands tested (15 to 25 °C up to 22 to 32 °C) and for each model separately: the share of city dwellers losing a month is 38% with MPI-ESM1-2-HR and 50% with UKESM1-0-LL.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page. Results are embedded; the climate grid and city list are loaded from `data/page/`. |
| `header.png` | Social card (1200 by 630). |
| `data/cities.csv` | Every GeoNames city of 15,000 or more (34,191): id, name, country, coordinates, population, the 10' cell used and its distance, whether the future change was borrowed from a neighbouring cell, and the 12 monthly mean daily maxima (°C) for 1970 to 2000 (`now_01` to `now_12`) and 2041 to 2060, three-model mean (`fut_01` to `fut_12`). |
| `data/city_pleasant_months_18_27C.csv` | Pleasant months per city at the default band, now, later and for each model, with month masks (January first) and a flag for cities counted in population totals. |
| `data/countries.csv` | Pleasant months by country, by land area (Natural Earth outlines) and by city population. |
| `data/pleasant_months_18_27C_1970_2000.asc.gz`, `..._2041_2060.asc.gz` | Pleasant months on the 10' grid (ESRI ASCII grid, -1 = no data or Antarctica). |
| `data/page/grid20.bin.gz` | The page grid: 20' cells north of 60° S, one byte per cell and month (see `code/02_analyse.py` for the coding). |
| `data/page/cities.json`, `data/page/cities_t.bin.gz` | City names, positions and populations, and their monthly highs in tenths of a degree (now, mean later, each model's difference from the mean). |
| `data/results.json` | Every number used anywhere. |
| `code/grid.py` | Readers for WorldClim and GeoNames, and the gap filling for the future grids. |
| `code/01_prepare.py` | Rasterises country outlines and matches cities to grid cells. |
| `code/02_analyse.py` | All statistics; writes the data tables, `results.json` and the page data. |
| `code/03_build_site.py` | Fills `code/page_template.html` to make `index.html` and checks facts stated in words. |
| `code/04_figures.py` | Static figures for the paper and blog (Equal Earth maps drawn from the grid). |
| `code/05_header.py` | Renders `header.png` with Playwright. |
| `code/06_paper.py` | Builds the paper PDF from `code/paper_template.tex` with xelatex. |
| `code/07_release.py` | Blog post, blog and Zenodo metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Pleasant month.** A month whose mean daily maximum temperature T satisfies L ≤ T ≤ H; default L = 18 °C, H = 27 °C. Values rounded to 0.1 °C.
- **Now.** WorldClim 2.1 monthly maximum temperature, 1970 to 2000, 10 arc-minutes. Land statistics cover land north of 60° S, weighted by true cell area.
- **Mid-century.** WorldClim downscaled CMIP6, 2041 to 2060, SSP2-4.5, mean of three models' monthly highs. 6.3% of the land area has no value in the downscaled grids (coasts, small islands, lake shores); there the nearest covered cell's change (median 19 km away) is added to the baseline.
- **Cities.** GeoNames cities15000, nearest land cell (median 6.7 km). Population totals leave out city sections (PPLX) and historical, abandoned or destroyed places so people are not counted twice. Big cities: population of a million or more.
- **Page.** The grid is averaged to 20' and each value stored as a one-byte code: 2n if T is exactly n °C, 2n − 1 if n − 1 < T < n, so comparisons with whole-degree band limits are exact. At the default band the page grid gives a land mean of 2.51 months against 2.51 on the full grid.

## Known limits

- Afternoon highs only: humidity, wind, rain, sunshine and nights are ignored; "pleasant" is a band, not a comfort index.
- The 10' grid smooths mountains and coasts; each city takes one cell. The baseline is 1970 to 2000 and the climate has warmed since.
- Three models and one scenario; UKESM1-0-LL is a hot model. Each model is reported separately.
- GeoNames populations mix city proper and municipality definitions and cover only listed cities (about half of all people).

## How to rerun

Inputs are read in place from the paths at the top of `code/grid.py` (WorldClim zips and GeoTIFFs, GeoNames `cities15000.zip`, Natural Earth 1:50m countries).

```
pip install imagecodecs   # tifffile needs it for the LZW-compressed WorldClim files
python3 code/01_prepare.py
python3 code/02_analyse.py
python3 code/03_build_site.py
FONT_DIR=path/to/fonts python3 code/04_figures.py
FONT_DIR=path/to/fonts python3 code/05_header.py
python3 code/06_paper.py
python3 code/07_release.py
```

Needs Python 3 with numpy, pandas, scipy, pillow, tifffile with imagecodecs, matplotlib and playwright, and xelatex with TeX Gyre Pagella and Inter for the paper.

## Sources and licences

- Climate 1970 to 2000: WorldClim 2.1. Fick, S.E. and Hijmans, R.J. (2017) WorldClim 2: new 1-km spatial resolution climate surfaces for global land areas. International Journal of Climatology 37(12): 4302 to 4315. https://www.worldclim.org (CC BY 4.0).
- Climate 2041 to 2060: WorldClim downscaled CMIP6 data, SSP2-4.5: MPI-ESM1-2-HR (Max Planck Institute for Meteorology), UKESM1-0-LL (Met Office Hadley Centre and UK partners), IPSL-CM6A-LR (Institut Pierre-Simon Laplace); CMIP6, World Climate Research Programme. https://www.worldclim.org/data/cmip6/cmip6climate.html (CC BY 4.0).
- Cities: GeoNames cities15000, https://www.geonames.org (CC BY 4.0).
- Country outlines: Natural Earth 1:50m admin 0 (public domain).
- Base map tiles on the page © Esri. Map library: Leaflet.

The derived data files are released under CC BY 4.0 with credit to WorldClim and GeoNames. Text and figures: CC BY 4.0. Code: MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) How Many Months a Year Are Pleasantly Warm? Pleasant Months in the Climate of 1970 to 2000 and 2041 to 2060 from WorldClim. Zenodo. https://doi.org/10.5281/zenodo.23732576

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
