# Provides shared functions to fetch and clean World Bank indicators, 
# combine them with PIP global-decile data, and generate summaries and 
# visualizations for the analysis notebooks and report.

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import requests

API_ROOT = "https://data360api.worldbank.org"
DATA_URL = f"{API_ROOT}/data360/data"
METADATA_URL = f"{API_ROOT}/data360/metadata"
D1_FILE = Path("GlobalDist1000bins_1990_2026_20260922_2021_01_02_PROD.csv")
HEADERS = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Data360-dev-indicators/1.0"}
PAGE_SIZE = 1000
TIMEOUT = 60
REGION_COLORS = {
    "East Asia & Pacific": "#0072B2",
    "Europe & Central Asia": "#009E73",
    "Latin America & Caribbean": "#D55E00",
    "Middle East, North Africa, Afghanistan & Pakistan": "#CC79A7",
    "North America": "#56B4E9",
    "South Asia": "#E69F00",
    "Sub-Saharan Africa": "#F0E442",
}


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("value", "data", "observations", "results", "records", "items"):
        if key in payload:
            found = _records(payload[key])
            if found:
                return found
    if payload and all(not isinstance(value, (dict, list)) for value in payload.values()):
        return [payload]
    for value in payload.values():
        found = _records(value)
        if found:
            return found
    return []


def fetch_metadata(dataset_id: str, indicator_id: str) -> dict[str, Any]:
    response = requests.post(
        METADATA_URL,
        json={"query": f"&$filter=series_description/idno eq '{indicator_id}'"},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    records = response.json().get("value", [])
    for record in records:
        series = record.get("series_description", {})
        if series.get("idno") == indicator_id:
            return series
    return {"idno": indicator_id, "database_id": dataset_id}


@lru_cache(maxsize=1)
def fetch_country_regions() -> pd.DataFrame:
    response = requests.get(
        "https://api.worldbank.org/v2/country",
        params={"format": "json", "per_page": 400},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    records = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    regions = pd.DataFrame(
        [
            {
                "code": record.get("id"),
                "region": (record.get("region") or {}).get("value"),
            }
            for record in records
            if isinstance(record, dict) and record.get("id")
        ]
    )
    regions["region"] = regions["region"].str.strip()
    return regions


def fetch_indicator(dataset_id: str, indicator_id: str, breakdown: str | None = None) -> pd.DataFrame:
    params = {"DATABASE_ID": dataset_id, "INDICATOR": indicator_id, "skip": 0}
    first = requests.get(DATA_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
    first.raise_for_status()
    payload = first.json()
    rows = _records(payload)
    expected = int(payload.get("count", payload.get("@odata.count", len(rows)))) if isinstance(payload, dict) else len(rows)
    while len(rows) < expected:
        params["skip"] = len(rows)
        response = requests.get(DATA_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        page = _records(response.json())
        if not page:
            break
        rows.extend(page)
    data = pd.json_normalize(rows)
    if data.empty:
        raise ValueError(f"No observations returned for {indicator_id}.")
    rename = {"REF_AREA": "code", "TIME_PERIOD": "year", "OBS_VALUE": "indicator_value"}
    data = data.rename(columns=rename)
    required = {"code", "year", "indicator_value"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing expected columns {sorted(missing)}. Columns returned: {data.columns.tolist()}")
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data["indicator_value"] = pd.to_numeric(data["indicator_value"], errors="coerce")
    for dimension in ("SEX", "AGE", "URBANISATION"):
        if dimension in data.columns and (data[dimension] == "_T").any():
            data = data[data[dimension] == "_T"]
    for dimension in ("COMP_BREAKDOWN_1", "COMP_BREAKDOWN_2", "COMP_BREAKDOWN_3"):
        if dimension not in data.columns:
            continue
        values = set(data[dimension].dropna().unique())
        if breakdown is not None and breakdown in values:
            data = data[data[dimension] == breakdown]
            continue
        if "_Z" in values:
            data = data[data[dimension] == "_Z"]
            continue
        # Some sources split a series into value/score/rank rows; keep only the value.
        value_codes = {v for v in values if str(v).upper().endswith("_VAL")}
        if value_codes and len(values) > 1:
            data = data[data[dimension].isin(value_codes)]
        elif len(values) > 1:
            raise ValueError(
                f"{dimension} has multiple breakdowns {sorted(values)} and no total; "
                "pass breakdown=... to pick one."
            )
    data = data[["code", "year", "indicator_value"]].dropna().drop_duplicates()
    return data.merge(fetch_country_regions(), on="code", how="left")


def load_d1_shares(path: Path = D1_FILE) -> pd.DataFrame:
    if not path.exists():
        path = Path("../") / path
    d1 = pd.read_csv(path)
    d1["year"] = pd.to_numeric(d1["year"], errors="coerce")
    d1["welf"] = pd.to_numeric(d1["welf"], errors="coerce")
    d1["pop"] = pd.to_numeric(d1["pop"], errors="coerce")
    d1 = d1.dropna(subset=["year", "welf", "pop"]).sort_values(
        ["year", "welf"], kind="stable"
    )
    d1["cum_pop"] = d1.groupby("year")["pop"].cumsum()
    d1["total_pop"] = d1.groupby("year")["pop"].transform("sum")
    d1["decile"] = np.minimum(
        np.ceil(d1["cum_pop"] / (d1["total_pop"] / 10)), 10
    ).astype(int)
    country_population = (
        d1.groupby(["year", "code"], as_index=False)
        .agg(country_population=("pop", "sum"))
    )
    global_d1 = (
        d1[d1["decile"] == 1]
        .groupby(["year", "code"], as_index=False)
        .agg(d1_pop_people=("pop", "sum"))
    )
    total_d1 = (
        d1[d1["decile"] == 1]
        .groupby("year", as_index=False)["pop"]
        .sum()
        .rename(columns={"pop": "global_d1_population"})
    )
    result = (
        country_population
        .merge(global_d1, on=["year", "code"], how="left")
        .merge(total_d1, on="year", how="left")
        .fillna({"d1_pop_people": 0})
    )
    result["d1_country_population_pct"] = (
        100 * result["d1_pop_people"] / result["country_population"]
    )
    result["d1_population_share"] = (
        result["d1_pop_people"] / result["global_d1_population"]
    )
    return result


def _correlations(joined: pd.DataFrame, value_column: str) -> pd.DataFrame:
    rows = []
    for year, group in joined.groupby("year"):
        group = group.dropna(subset=["d1_country_population_pct", value_column])
        rows.append({
            "year": year,
            "pearson_r": group["d1_country_population_pct"].corr(group[value_column], method="pearson"),
            "spearman_r": group["d1_country_population_pct"].rank().corr(group[value_column].rank(), method="pearson"),
            "observations": len(group),
        })
    return pd.DataFrame(rows).sort_values("year")


def low_coverage_concentration(joined: pd.DataFrame, threshold: float = 50.0, min_countries: int = 100) -> pd.DataFrame:
    """Share of the global D1 versus share of world population living in countries below a coverage threshold.

    Counts where people live, so it carries no assumption about access within a country.
    """
    rows = []
    for year, group in joined.groupby("year"):
        group = group.dropna(subset=["indicator_value"])
        if group["code"].nunique() < min_countries:
            continue
        below = group["indicator_value"] < threshold
        d1_share = 100 * group.loc[below, "d1_population_share"].sum() / group["d1_population_share"].sum()
        world_share = 100 * group.loc[below, "country_population"].sum() / group["country_population"].sum()
        rows.append({
            "year": int(year),
            "d1_share_below": d1_share,
            "world_share_below": world_share,
            "gap_ratio": d1_share / world_share if world_share > 0 else np.nan,
            "countries_below": int(group.loc[below, "code"].nunique()),
            "countries_with_data": group["code"].nunique(),
        })
    columns = [
        "year",
        "d1_share_below",
        "world_share_below",
        "gap_ratio",
        "countries_below",
        "countries_with_data",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values("year").reset_index(drop=True)


def low_coverage_chart(concentration: pd.DataFrame, indicator_label: str, threshold: float = 50.0) -> alt.Chart:
    long = concentration.melt(
        id_vars=["year"],
        value_vars=["d1_share_below", "world_share_below"],
        var_name="group",
        value_name="share",
    ).replace({"d1_share_below": "Poorest global decile", "world_share_below": "World population"})
    return (
        alt.Chart(long)
        .mark_line(strokeWidth=3, point=False)
        .encode(
            x=alt.X("year:Q", title="Year", axis=alt.Axis(format="d")),
            y=alt.Y("share:Q", title=f"Living in countries below {threshold:.0f}% coverage (%)"),
            color=alt.Color(
                "group:N",
                title=None,
                scale=alt.Scale(
                    domain=["Poorest global decile", "World population"],
                    range=["#D55E00", "#0072B2"],
                ),
            ),
            tooltip=[
                alt.Tooltip("year:O", title="Year"),
                alt.Tooltip("group:N", title="Group"),
                alt.Tooltip("share:Q", title="Share (%)", format=".1f"),
            ],
        )
        .properties(width=760, height=380, title=f"{indicator_label}: where the poorest decile lives")
    )


def run_indicator_analysis(
    dataset_id: str,
    indicator_id: str,
    deprivation_mode: str,
    breakdown: str | None = None,
    low_coverage_min_countries: int = 100,
) -> dict[str, Any]:
    metadata = fetch_metadata(dataset_id, indicator_id)
    indicator = fetch_indicator(dataset_id, indicator_id, breakdown=breakdown)
    d1 = load_d1_shares()
    joined = indicator.merge(d1, on=["code", "year"], how="inner")
    if joined.empty:
        raise ValueError("The indicator and D1 data have no common country-year observations.")
    if deprivation_mode == "coverage_pct":
        joined["deprivation_proxy"] = 100 - joined["indicator_value"]
        deprivation_label = "Estimated population without access (%) = 100 - coverage"
    elif deprivation_mode == "bad_pct":
        joined["deprivation_proxy"] = joined["indicator_value"]
        deprivation_label = "Indicator value interpreted as population exposed/deprived (%)"
    else:
        joined["deprivation_proxy"] = np.nan
        deprivation_label = "Not calculated: indicator is a count or not a direct access measure"
    first_year = int(joined["year"].min())
    last_year = int(joined["year"].max())
    endpoint = joined[joined["year"].isin([first_year, last_year])].copy()
    correlations = _correlations(joined, "deprivation_proxy")
    access_correlations = _correlations(joined, "indicator_value")
    summary_rows = []
    for year, group in endpoint.groupby("year"):
        row = {
            "year": year,
            "countries": group["code"].nunique(),
            "mean_indicator": group["indicator_value"].mean(),
            "mean_deprivation_proxy": group["deprivation_proxy"].mean(),
            "median_deprivation_proxy": group["deprivation_proxy"].median(),
            "observed_population": group["country_population"].sum(),
            "population_weighted_indicator": np.average(
                group["indicator_value"], weights=group["country_population"]
            ),
            "population_weighted_deprivation_proxy": np.average(
                group["deprivation_proxy"], weights=group["country_population"]
            ) if group["deprivation_proxy"].notna().any() else np.nan,
        }
        summary_rows.append(row)
    endpoint_summary = pd.DataFrame(summary_rows).sort_values("year")
    chart = (
        alt.Chart(endpoint)
        .mark_circle(size=55, opacity=0.7)
        .encode(
            x=alt.X("d1_country_population_pct:Q", title="Country population in global D1 (%)"),
            y=alt.Y("indicator_value:Q", title=metadata.get("name", indicator_id)),
            color=alt.Color("year:N", title="Year"),
            tooltip=["code:N", "year:Q", "indicator_value:Q", "d1_population_share:Q", "deprivation_proxy:Q"],
        )
        .properties(width=650, height=400, title=f"{indicator_id}: D1 country share vs indicator")
    )
    return {
        "metadata": metadata,
        "joined": joined,
        "correlations": correlations,
        "access_correlations": access_correlations,
        "endpoint": endpoint,
        "endpoint_summary": endpoint_summary,
        "low_coverage": low_coverage_concentration(
            joined, min_countries=low_coverage_min_countries
        ),
        "first_year": first_year,
        "last_year": last_year,
        "deprivation_label": deprivation_label,
        "chart": chart,
    }
