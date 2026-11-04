# Global Progress, Unequally Shared

This project examines how global income growth has been shared across the poorest 10% and other global income deciles from 1990 to 2025.
The idea is to publish this piece in the World Bank's Data webpage, as it represents a continuation of a program started over the summer. 

It looks at poverty from a different angle and tries to explain differences throughout population deciles over the past years and its relationship with poverty and inequality. 

**Final report:** [`report/left_behind.pdf`](report/left_behind.pdf)

## Contents

- `report/left_behind.qmd`: report narrative and methods.
- `report/build_figures.py`: builds the report figures and `report/figures/numbers.json`.
- `report/figures/`: figures used in the report.
- `report/left_behind.pdf`: rendered report.
- `report/typst-template.typ`: PDF template.
- `dev_indicators/indicator_analysis_helpers.py` and `dev_indicators/parse_fcs_list.py`: report build helpers.
- `data/C2-FCSList-FY06toFY26.pdf`: World Bank fragile and conflict-affected situations lists used by the report.

## Supplementary indicator analyses

`dev_indicators/` includes the analysis notebooks used to develop and contextualize the blog:

- `decile_bars_visualization.ipynb` and `summary_indicators.ipynb`: cross-indicator comparisons by global decile.
- `electricity_access.ipynb`, `internet_access.ipynb`, `water_access.ipynb`, and `literacy_analysis.ipynb`: indicator-specific analyses.
- `fragility_fcs.ipynb`: fragile and conflict-affected states analysis.
- `ai_preparedness_exploration.ipynb`: supplementary AI preparedness exploration; it is not a source for the report's main figures.

These notebooks are supporting analyses, not required to render the PDF. Notebooks that calculate global deciles require the PIP CSV described below; the large source file is not committed.

## Data

The report uses the World Bank PIP 1,000-bin global distribution (2026 release, vintage 20260922), in 2021 PPP dollars per person per day. The 2026 forecast is excluded; the report ends in 2025. The 772 MB CSV is not included in this repository. Download it from the [World Bank Data Catalog](https://datacatalog.worldbank.org/search/dataset/0064304/1000-binned-global-distribution) and place `GlobalDist1000bins_1990_2026_20260922_2021_01_02_PROD.csv` in the project root.

The report build also fetches electricity, internet, and sanitation indicators from Data360/World Bank APIs (https://data360.worldbank.org/en/api). The FCS list PDF is included because it is small and required to reproduce the fragility figure.

## Reproduce

Requires Python 3.13, [uv](https://docs.astral.sh/uv/), and [Quarto](https://quarto.org).

```bash
uv sync
.venv/bin/python report/build_figures.py
quarto render report/left_behind.qmd
```

The report defines global deciles separately for each year by pooling country bins, sorting by welfare, and weighting by represented population. Deciles describe positions in the global distribution, not a fixed panel of people. Service-access comparisons classify countries by whether fewer than half of their population has a given service.