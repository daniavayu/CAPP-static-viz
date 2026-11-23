# Methodology note: "The poorest 10% of the world have made little progress in a decade"

**Source.** All income figures come from the World Bank's Poverty and Inequality Platform (PIP) 1,000-bin global distribution (2026 release, vintage 20260922), in 2021 PPP dollars per person per day. Each country-year is described by 1,000 bins. Each bin represents one-thousandth of the country's population and records the average daily income (or consumption) of that slice. The analysis covers 1990-2025. The 2026 forecast in the release is excluded. For years after a country's latest household survey, PIP extrapolates the distribution using national accounts growth, so the most recent years are estimates, not direct observations. The reversal in the bottom 10%'s share is already visible in 2019 (share of 0.99%, down from 1.04% at the peak), before the pandemic and in years with broader survey coverage.

**Building global deciles.** For each year separately:

1. All bins from all countries are pooled and sorted from lowest to highest daily income.
2. Each bin is weighted by the population it represents.
3. Population is accumulated along the sorted list. The first 10% of world population is decile 1 (D1, the "bottom 10%"), the next 10% is decile 2, and so on up to decile 10.
4. A decile's mean income is the population-weighted average across its bins. Its income share is its mean income divided by the sum of the ten decile means. Because each decile holds about 10% of the population, this equals its share of global income. Growth rates compare decile means across years.

**Implications.**

- Deciles are global: a person in Burundi and a person in India are ranked against each other, not within their own countries.
- Deciles are recalculated every year. The "bottom 10%" is a position in the distribution, not a fixed group of people. Growth figures describe how that position's average income changed, not the trajectory of the same individuals.
- Each bin is assigned whole to one decile, so each decile holds between 9.98% and 10.02% of world population. The difference is negligible.

**Figures and headline numbers.**

- *Income share and growth (Figures 1-2):* shares in 1990, 2014 and 2025 and growth between 2015 and 2025 are computed from decile mean incomes as above. D1 mean income rose from $1.88 to $1.96 a day (+4.1%). The middle deciles rose about 25%, and D2 rose 21.1%.
- *Regions and countries (Figures 2b-3):* each bin carries a country code and a PIP region. The regional composition of D1 is the share of D1 population by region. Country concentration is the share of each country's 2025 population that falls in D1. "Most of the population" means more than 50%, which holds for 13 countries.
- *Services (Figure 4):* a country is classified as low access if fewer than half of its population has the service. The indicators are access to electricity (World Bank WDI), individuals using the internet (ITU) and at least basic sanitation services (WHO/UNICEF JMP via WDI). Each bar shows the share of a group's population that lives in a low-access country, where the groups are D1, D2 and deciles 3-10. This describes where people live, not whether each individual has the service. Countries without data for an indicator and year are excluded from that calculation.
- *Fragility:* World Bank lists of fragile and conflict-affected situations (FCV), from the GPID-WB/class repository (https://github.com/GPID-WB/class). The fiscal-year 2001 list is matched to the 2000 distribution and the fiscal-year 2026 list to the 2025 distribution.
- *Reference years:* "before" is 2000 for services and fragility. "Today" is 2023 for electricity, 2024 for internet and sanitation, and 2025 for fragility.

**Reproducibility.** `report/build_figures.py` generates every figure and `report/figures/numbers.json`, which contains each number quoted in the text. It needs the PIP CSV, which isn't committed because of its size (772 MB), and it fetches the service indicators from the Data360/World Bank APIs.

