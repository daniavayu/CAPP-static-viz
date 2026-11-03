"""Parse the World Bank FCS/LICUS PDF (FY06-FY26) into a tidy country-year table."""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pdfplumber
import requests

PDF_PATH = Path("data/C2-FCSList-FY06toFY26.pdf")

# PDF spellings that differ from the World Bank country list.
ALIASES = {
    "congo democratic republic of": "COD",
    "democratic republic of congo": "COD",
    "congo dem rep": "COD",
    "congo dr": "COD",
    "dem rep of congo": "COD",
    "congo republic of": "COG",
    "congo rep": "COG",
    "republic of congo": "COG",
    "yemen republic of": "YEM",
    "yemen rep": "YEM",
    "republic of yemen": "YEM",
    "micronesia federated states of": "FSM",
    "micronesia fed sts": "FSM",
    "sao tome and principe": "STP",
    "venezuela rb": "VEN",
    "venezuela republica bolivariana de": "VEN",
    "west bank and gaza territory": "PSE",
    "west bank and gaza": "PSE",
    "syrian arab republic": "SYR",
    "syria": "SYR",
    "egypt arab rep": "EGY",
    "gambia the": "GMB",
    "the gambia": "GMB",
    "lao pdr": "LAO",
    "lao people s democratic republic": "LAO",
    "kyrgyz republic": "KGZ",
    "cote d ivoire": "CIV",
    "ivory coast": "CIV",
    "timor leste": "TLS",
    "east timor": "TLS",
    "myanmar": "MMR",
    "burma": "MMR",
    "korea dem people s rep": "PRK",
    "korea dem rep": "PRK",
    "north korea": "PRK",
    "kosovo": "XKX",
    "sudan": "SDN",
    "south sudan": "SSD",
    "guinea bissau": "GNB",
    "central african republic": "CAF",
    "solomon islands": "SLB",
    "marshall islands": "MHL",
    "papua new guinea": "PNG",
    "sierra leone": "SLE",
    "burkina faso": "BFA",
    "cape verde": "CPV",
    "cabo verde": "CPV",
    "tonga": "TON",
    "zimbabwe": "ZWE",
    "eritrea": "ERI",
    "djibouti": "DJI",
    "comoros": "COM",
    "angola": "AGO",
    "nigeria": "NGA",
    "niger": "NER",
    # pdfplumber drops some spaces and truncates some cells.
    "solomonislands": "SLB",
    "timorleste": "TLS",
    "sao tome and pr": "STP",
    "sao tome and principe": "STP",
    "central afr rep": "CAF",
    "central african rep": "CAF",
    # Abbreviations used as row labels in the FY10-FY14 tables.
    "drc": "COD",
    "car": "CAF",
    "cote divoire": "CIV",
    "western sahara": "ESH",
}

# Lines at or after these markers are explanatory notes, which name non-listed countries.
FOOTNOTE = re.compile(r"^\s*(\*|a/|b/|c/|d/|notes?\s*:|memo)", re.IGNORECASE)


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=1)
def _country_patterns() -> list[tuple[str, str]]:
    """(normalised name, iso3) pairs, longest first so 'South Sudan' beats 'Sudan'."""
    response = requests.get(
        "https://api.worldbank.org/v2/country",
        params={"format": "json", "per_page": 400},
        headers={"Accept": "application/json", "User-Agent": "fcs-parser/1.0"},
        timeout=60,
    )
    response.raise_for_status()
    lookup: dict[str, str] = {}
    bases: dict[str, set[str]] = {}
    for record in response.json()[1]:
        region = (record.get("region") or {}).get("value")
        if not record.get("id") or not region or region == "Aggregates":
            continue
        name = record["name"]
        lookup[_norm(name)] = record["id"]
        bases.setdefault(_norm(name.split(",")[0]), set()).add(record["id"])
    # "Somalia, Fed. Rep." should also match a bare "Somalia", but "Congo" is ambiguous.
    for base, codes in bases.items():
        if len(codes) == 1 and base not in lookup:
            lookup[base] = next(iter(codes))
    lookup.update(ALIASES)
    return sorted(lookup.items(), key=lambda kv: -len(kv[0]))


def _codes_in(text: str) -> set[str]:
    """Find country codes mentioned in a page, masking matches so names cannot overlap."""
    haystack = f" {_norm(text)} "
    found = set()
    for name, code in _country_patterns():
        pattern = re.compile(rf"(?<![a-z]){re.escape(name)}(?![a-z])")
        if pattern.search(haystack):
            found.add(code)
            haystack = pattern.sub(lambda m: " " * len(m.group()), haystack)
    return found


def _list_body(text: str) -> str:
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if FOOTNOTE.match(line):
            return "\n".join(lines[:index])
    return text


def _methodology(header: str) -> str:
    upper = header.upper()
    if "LICUS" in upper:
        return "LICUS"
    if "HARMONIZED" in upper:
        return "Harmonized fragile situations"
    if "FRAGILE STATES" in upper:
        return "Fragile states"
    return "FCS"


def parse_fcs(pdf_path: Path = PDF_PATH) -> pd.DataFrame:
    """Return one row per (fiscal_year, code) on the FCS/LICUS list."""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            header = text.split("\n")[0] if text else ""
            match = re.search(r"FY\s?(\d{2})", header)
            if not match:
                continue
            fiscal_year = 2000 + int(match.group(1))
            methodology = _methodology(header)
            for code in _codes_in(_list_body(text)):
                rows.append(
                    {"fiscal_year": fiscal_year, "code": code, "methodology": methodology}
                )
    frame = pd.DataFrame(rows).drop_duplicates()
    # A fiscal year is published mid-prior calendar year, so FY26 covers calendar 2025.
    frame["year"] = frame["fiscal_year"] - 1
    return frame.sort_values(["fiscal_year", "code"]).reset_index(drop=True)


if __name__ == "__main__":
    fcs = parse_fcs()
    summary = fcs.groupby(["fiscal_year", "methodology"])["code"].nunique()
    print(summary.to_string())
    print("\ntotal rows:", len(fcs))
