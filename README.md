# Global Progress, Unequally Shared

This project examines how global income growth has been shared across the poorest 10% and other global income deciles from 1990 to 2025.

**Final report:** [`report/left_behind.pdf`](report/left_behind.pdf)

## Contents

- `report/left_behind.qmd`: report narrative and methods.
- `report/build_figures.py`: builds the report figures and `report/figures/numbers.json`.
- `report/figures/`: figures used in the report.
- `report/left_behind.pdf`: rendered report.
- `report/typst-template.typ`: PDF template.
- `dev_indicators/indicator_analysis_helpers.py` and `dev_indicators/parse_fcs_list.py`: report build helpers.
- `data/C2-FCSList-FY06toFY26.pdf`: World Bank fragile and conflict-affected situations lists used by the report.

## Data

The report uses the World Bank PIP 1,000-bin global distribution (2026 release, vintage 20260922), in 2021 PPP dollars per person per day. The 2026 forecast is excluded; the report ends in 2025. The 772 MB CSV is not included in this repository. Download it from the [World Bank Data Catalog](https://datacatalog.worldbank.org/search/dataset/0064304/1000-binned-global-distribution) and place `GlobalDist1000bins_1990_2026_20260922_2021_01_02_PROD.csv` in the project root.

The report build also fetches electricity, internet, and sanitation indicators from Data360/World Bank APIs. The FCS list PDF is included because it is small and required to reproduce the fragility figure.

## Reproduce

Requires Python 3.13, [uv](https://docs.astral.sh/uv/), and [Quarto](https://quarto.org).

```bash
uv sync
.venv/bin/python report/build_figures.py
quarto render report/left_behind.qmd
```

The report defines global deciles separately for each year by pooling country bins, sorting by welfare, and weighting by represented population. Deciles describe positions in the global distribution, not a fixed panel of people. Service-access comparisons classify countries by whether fewer than half of their population has a given service.