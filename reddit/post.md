## Title

[OC] How many months a year are pleasantly warm (average daily high 18 to 27 °C)? For people in the world's cities it is 3.6 months in the 1970 to 2000 climate and 2.9 by 2041 to 2060; 14 cities of a million or more had all twelve, 5 will

## Body (optional)

I counted the months whose average afternoon high falls between 18 and 27 °C, on WorldClim's 10 arc-minute climate grid, for 1970 to 2000 and for 2041 to 2060 (mean of three climate models, SSP2-4.5). A third of land outside Antarctica never gets a month in the band. The average person in a city of 15,000 or more gets 3.6 pleasant months now and 2.9 by mid-century: 46% of them lose at least one month, 14% gain one. Year-round "spring" cities (São Paulo, Lima, Kigali) mostly lose it; in 38 big cities, including Paris and Berlin, the pleasant season splits in two around a summer that gets too hot.

Caveat: highs only. Humidity, rain and nights are ignored, and it is three models and one scenario.

Pick your own band on the interactive map: https://tristan-hotham.github.io/pleasant-months/

## Source comment

Source: WorldClim 2.1 monthly average daily maximum temperature, 1970 to 2000, 10 arc-minutes (Fick, S.E. and Hijmans, R.J. 2017, International Journal of Climatology 37(12): 4302 to 4315; CC BY 4.0); WorldClim downscaled CMIP6 projections for 2041 to 2060 under SSP2-4.5 from MPI-ESM1-2-HR, UKESM1-0-LL and IPSL-CM6A-LR (CC BY 4.0); cities from GeoNames cities15000 (CC BY 4.0), population-weighted with city districts removed so nobody is counted twice (31,778 cities, 3.9 billion people).

Tools: Python (NumPy, pandas, SciPy for nearest-cell matching, tifffile, matplotlib; Equal Earth projection computed directly).

Interactive: https://tristan-hotham.github.io/pleasant-months/
Blog post: https://blog.tristanhotham.com/2026/10/28/pleasant-months/
Paper: https://doi.org/10.5281/zenodo.23732576
