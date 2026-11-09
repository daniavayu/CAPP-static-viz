# FCV classification by country and year

Source: World Bank GPID `class` repository, file `OutputData/CLASS.dta`
https://github.com/GPID-WB/class (shared by Daniel; downloaded 2026-11-09).
Converted from Stata to CSV with no changes to the values.

## Files
- `fcv_by_country_year.csv`: one row per country and year (1998-2025).
  - `year`: the data year the classification is applied to (`year_data` in the original).
  - `wb_fiscal_year_list`: the World Bank fiscal-year list it comes from. In this file, data year N uses the fiscal-year N+2 list (e.g. 2005 -> FY2007, 2025 -> FY2027).
  - `is_fcv`: 1 = fragile/conflict-affected, 0 = not.
- `fcv_list_2005.csv`: only the countries flagged FCV in 2005.

Years before 1998 are blank in the original file and are not included.
