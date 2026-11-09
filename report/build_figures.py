"""Build the figures and key numbers used in left_behind.qmd.

Run from anywhere:  .venv/bin/python report/build_figures.py
"""

import json
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import requests

REPORT_DIR = Path(__file__).resolve().parent
ROOT = REPORT_DIR.parent
FIGURES = REPORT_DIR / 'figures'
FIGURES.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'dev_indicators'))
from indicator_analysis_helpers import fetch_indicator  # noqa: E402

DISTRIBUTION = ROOT / 'GlobalDist1000bins_1990_2026_20260922_2021_01_02_PROD.csv'
# FCV status by country and World Bank fiscal-year list (GPID-WB/class, CLASS.dta).
FCV_FILE = ROOT / 'data' / 'FCV_daniel' / 'fcv_by_country_year.csv'
THRESHOLD = 50
# 2026 in the PIP release is a forecast; stop at 2025.
LAST_YEAR = 2025
# World Bank data-viz palette: blue for the poorest tenth, gold for reference marks, greys for everyone else.
BLUE, GOLD, DARK, LIGHT = '#34A7F2', '#F3B712', '#5F5F5F', '#D9D9D9'
OTHER = '#9E9E9E'  # every decile other than D1
FONT = 'Helvetica'

distribution = pd.read_csv(DISTRIBUTION, usecols=['year', 'code', 'region_name', 'welf', 'pop'])


def global_deciles(year):
    bins = distribution[distribution['year'].eq(year)].sort_values('welf', kind='stable').copy()
    bins['decile'] = np.minimum(np.ceil(bins['pop'].cumsum() / (bins['pop'].sum() / 10)), 10).astype(int)
    return bins


def group_share(bins, flagged, deciles):
    observed = bins[bins['decile'].isin(deciles)].assign(flag=lambda df: df['code'].map(flagged)).dropna(subset=['flag'])
    return 100 * observed.loc[observed['flag'].eq(1), 'pop'].sum() / observed['pop'].sum()


def styled(chart):
    return (
        chart.configure(font=FONT)
        .configure_view(stroke=None)
        .configure_axis(grid=False, labelFontSize=11, titleFontSize=11, titleColor='#444444')
        .configure_title(anchor='start', fontSize=15, subtitleFontSize=11, subtitleColor='#555555')
    )


def save(chart, name):
    styled(chart).save(str(FIGURES / name), scale_factor=3)


numbers = {}
DECILES = {year: global_deciles(year) for year in range(1990, LAST_YEAR + 1)}

# --- Income summaries: derive every distribution figure from the same PIP release --------
deciles_year = pd.concat(
    [
        bins.assign(welf_pop=bins['welf'] * bins['pop'])
        .groupby('decile', as_index=False)
        .agg(pop=('pop', 'sum'), welf_pop=('welf_pop', 'sum'))
        .assign(year=year)
        for year, bins in DECILES.items()
    ],
    ignore_index=True,
)
deciles_year['mean_welf'] = deciles_year['welf_pop'] / deciles_year['pop']
deciles_year['share'] = 100 * deciles_year['mean_welf'] / deciles_year.groupby('year')['mean_welf'].transform('sum')
deciles_year['panel'] = 'Decile ' + deciles_year['decile'].astype(str)
deciles_year['is_d1'] = deciles_year['decile'].eq(1)
shares_wide = deciles_year.pivot(index='year', columns='decile', values='share')
d1_peak_year = int(shares_wide[1].idxmax())  # year the poorest tenth's share peaked (2014)
numbers['income_share'] = {
    str(year): shares_wide.loc[year].round(2).to_dict() for year in (1990, 2000, 2015, 2019, LAST_YEAR)
}

fig1 = (
    alt.Chart(deciles_year)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X('year:Q', title=None, scale=alt.Scale(domain=[1990, LAST_YEAR], nice=False),
                axis=alt.Axis(format='d', values=[1990, 2000, 2010, 2020], labelFontSize=9)),
        y=alt.Y('share:Q', title=None, scale=alt.Scale(zero=False),
                axis=alt.Axis(tickCount=4, format='.2~f', labelFontSize=9)),
        color=alt.condition(alt.datum.is_d1, alt.value(BLUE), alt.value(OTHER)),
    )
    .properties(width=105, height=80)
    .facet(
        facet=alt.Facet('panel:N', sort=[f'Decile {i}' for i in range(1, 11)], title=None,
                        header=alt.Header(labelFontSize=11, labelFontWeight='bold')),
        columns=5,
    )
    .resolve_scale(y='independent')
    .properties(title=alt.TitleParams(
        f"Since {d1_peak_year}, the poorest tenth's share of global income has been shrinking",
        subtitle=[f'Share of global income held by each global income decile, 1990-{LAST_YEAR} (%).',
                  'Each panel has its own vertical scale: compare shapes, not heights.'],
    ))
)
save(fig1, 'fig1_income_share_by_decile.png')

# --- Figure 1b: income share changes by decile -----------------------------------------
index_df = deciles_year.copy()
index_df['index'] = 100 * (index_df['share'] / index_df['decile'].map(shares_wide.loc[1990]) - 1)
numbers['share_index'] = {
    str(year): index_df[index_df['year'].eq(year)].set_index('decile')['index'].round(1).to_dict()
    for year in (2015, 2019, LAST_YEAR)
}
last_index = index_df[index_df['year'].eq(LAST_YEAR)]
individual_labels = last_index[last_index['decile'].isin([1, 7, 8, 9, 10])][['decile', 'index']].copy()
individual_labels['label'] = 'D' + individual_labels['decile'].astype(str)
individual_labels['color'] = np.where(individual_labels['decile'].eq(1), BLUE, OTHER)
cluster = last_index[last_index['decile'].between(2, 6)]
cluster_label = pd.DataFrame({
    'index': [cluster['index'].mean()],
    'label': ['D2-D6'],
    'color': [OTHER],
})
index_labels = pd.concat([individual_labels[['index', 'label', 'color']], cluster_label], ignore_index=True)
index_labels = index_labels.sort_values('index').reset_index(drop=True)
label_y = index_labels['index'].to_numpy().copy()
for i in range(1, len(label_y)):
    label_y[i] = max(label_y[i], label_y[i - 1] + 7)
if label_y[-1] > 65:
    label_y -= label_y[-1] - 65
index_labels['label_index'] = label_y
index_labels['label_year'] = LAST_YEAR + 2
index_x = alt.X('year:Q', title=None, scale=alt.Scale(domain=[1990, LAST_YEAR + 10], nice=False),
                axis=alt.Axis(format='d', values=list(range(1990, LAST_YEAR + 1, 10))))
index_x_cross = alt.X(
    'year:Q', title=None, scale=alt.Scale(domain=[1990, LAST_YEAR + 10], nice=False),
    axis=alt.Axis(labels=False, ticks=False, domain=False),
)
index_y = alt.Y(
    'index:Q', title='Change since 1990 (%)', scale=alt.Scale(domain=[-20, 70]),
    axis=alt.Axis(values=[-20, 0, 20, 40, 60]),
)
year_axis = pd.DataFrame({'year': [1990, 2000, 2010, 2020], 'index': 0, 'tick_end': -2})
zero_line = pd.DataFrame({'year': [1990], 'year_end': [LAST_YEAR + 10], 'index': [0]})
means = deciles_year.pivot(index='year', columns='decile', values='mean_welf')
ratio = (means[10] / means[1]).rename('ratio').reset_index()
turning_year = int(ratio.loc[ratio['ratio'].idxmin(), 'year'])
numbers['d10_d1_ratio'] = {str(year): round(ratio.set_index('year').loc[year, 'ratio'], 1) for year in (1990, turning_year, 2019, LAST_YEAR)}
numbers['turning_year'] = turning_year


def turning_rule(x_axis=index_x):
    return alt.Chart(pd.DataFrame({'year': [turning_year]})).mark_rule(color=GOLD, strokeWidth=2).encode(x=x_axis)


def turning_label(y, x_axis=index_x):
    return alt.Chart(pd.DataFrame({'year': [turning_year], 'index': [y], 'text': [f'Turning point ({turning_year})']})).mark_text(
        align='right', dx=-4, fontSize=10, fontWeight='bold', color='#B08600',
    ).encode(x=x_axis, y=index_y, text='text:N')


index_panel = alt.layer(
    turning_rule(index_x_cross),
    alt.Chart(zero_line).mark_rule(color='#777777', strokeWidth=0.8).encode(
        x=index_x_cross, x2='year_end:Q',
        y=index_y,
    ),
    alt.Chart(year_axis).mark_rule(color='#555555', strokeWidth=0.8).encode(
        x=index_x_cross, y=index_y, y2='tick_end:Q',
    ),
    alt.Chart(year_axis).mark_text(align='center', dy=9, fontSize=9, color='#444444').encode(
        x=index_x_cross, y=index_y, text=alt.Text('year:Q', format='d'),
    ),
    alt.Chart(index_df[index_df['decile'].ne(1)]).mark_line(strokeWidth=1.5, color=OTHER).encode(
        x=index_x_cross,
        y=index_y,
        detail='decile:N',
    ),
    alt.Chart(index_df[index_df['decile'].eq(1)]).mark_line(strokeWidth=3.5, color=BLUE).encode(
        x=index_x_cross, y=index_y,
    ),
    alt.Chart(index_labels).mark_rule(strokeWidth=0.8, opacity=0.8).encode(
        x=index_x_cross,
        x2='label_year:Q', y=index_y, y2='label_index:Q', color=alt.Color('color:N', scale=None),
    ),
    alt.Chart(index_labels).mark_text(align='left', dx=3, fontSize=9, fontWeight='bold').encode(
        x=alt.X(
            'label_year:Q', scale=alt.Scale(domain=[1990, LAST_YEAR + 10], nice=False),
            axis=alt.Axis(labels=False, ticks=False, domain=False),
        ),
        y='label_index:Q', text='label:N', color=alt.Color('color:N', scale=None),
    ),
    turning_label(65, index_x_cross),
).properties(
    width=310, height=220,
    title=alt.TitleParams("D1 and the other global deciles", subtitle=["Percent change in each decile's income share since 1990"], fontSize=12),
)

ratio_points = ratio[ratio['year'].isin([1990, turning_year, LAST_YEAR])].assign(
    label=lambda df: df['ratio'].round().astype(int).astype(str) + 'x'
)
ratio_panel = alt.layer(
    turning_rule(),
    alt.Chart(ratio).mark_line(strokeWidth=3.5, color=BLUE).encode(
        x=index_x, y=alt.Y('ratio:Q', title='Richest 10% / poorest 10% (mean income)', scale=alt.Scale(domain=[40, 85])),
    ),
    alt.Chart(ratio_points).mark_point(filled=True, size=50, color=BLUE, opacity=1).encode(x=index_x, y='ratio:Q'),
    alt.Chart(ratio_points).mark_text(dy=-12, fontSize=11, fontWeight='bold', color=BLUE).encode(x=index_x, y='ratio:Q', text='label:N'),
).properties(
    width=230, height=220,
    title=alt.TitleParams('The gap with the richest tenth is widening again', subtitle=['Times the poorest 10% mean income'], fontSize=12),
)

fig1b = alt.hconcat(index_panel, ratio_panel, spacing=40).properties(
    title=alt.TitleParams(
        f'Around {turning_year}, the poorest tenth stopped catching up',
        subtitle=[f'Global income deciles, 1990-{LAST_YEAR}'],
    ),
).resolve_axis(x='independent')
save(fig1b, 'fig1b_share_index.png')

# --- Figure 2: income growth over the past decade, by decile ---------------------------
growth = (100 * (means.loc[2025] / means.loc[2015] - 1)).rename('growth').reset_index()
growth['label'] = 'D' + growth['decile'].astype(str)
growth['highlight'] = growth['decile'].eq(1)
numbers['growth_2015_2025'] = growth.set_index('label')['growth'].round(1).to_dict()
numbers['mean_welfare'] = {str(year): means.loc[year].round(2).to_dict() for year in (1990, 2000, 2015, 2025)}

growth_base = alt.Chart(growth).encode(
    x=alt.X('label:N', sort=[f'D{i}' for i in range(1, 11)], title='Global income decile (D1 = poorest)', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('growth:Q', title='Income growth, 2015-2025 (%)', scale=alt.Scale(domain=[0, round(growth['growth'].max() * 1.2)])),
)
fig2 = alt.layer(
    growth_base.mark_bar(size=34).encode(
        color=alt.condition(alt.datum.highlight, alt.value(BLUE), alt.value(OTHER)),
    ),
    growth_base.mark_text(dy=-8, fontSize=12, fontWeight='bold').encode(
        text=alt.Text('growth:Q', format='.0f'),
        color=alt.condition(alt.datum.highlight, alt.value(BLUE), alt.value(OTHER)),
    ),
).properties(
    width=520, height=230,
    title=alt.TitleParams(
        "Over the past decade, the poorest tenth's income barely grew",
        subtitle=['Growth in mean daily income of each global income decile between 2015 and 2025 (%)'],
    ),
)
save(fig2, 'fig2_growth_by_decile.png')

# --- Figure 2b: where the poorest tenth lives, by region over time ---------------------
REGION_GROUPS = {
    'Sub-Saharan Africa': 'Sub-Saharan Africa',
    'Middle East, North Africa, Afghanistan & Pakistan': 'Middle East, N. Africa, Afghanistan & Pakistan',
    'South Asia': 'South Asia',
    'East Asia & Pacific': 'East Asia & Pacific',
}
REGION_COLORS = {
    'Sub-Saharan Africa': BLUE,
    'Middle East, N. Africa, Afghanistan & Pakistan': GOLD,
    'South Asia': '#7F7F7F',
    'East Asia & Pacific': '#B3B3B3',
    'Rest of the world': '#E0E0E0',
}
d1_regions = pd.concat([
    bins[bins['decile'].eq(1)]
    .assign(region=lambda df: df['region_name'].map(REGION_GROUPS).fillna('Rest of the world'))
    .groupby('region')['pop'].sum()
    .pipe(lambda s: 100 * s / s.sum())
    .rename('share').reset_index().assign(year=year)
    for year, bins in DECILES.items()
])
d1_regions['order'] = d1_regions['region'].map({name: i for i, name in enumerate(REGION_COLORS)})
numbers['d1_by_region'] = {
    str(year): d1_regions[d1_regions['year'].eq(year)].set_index('region')['share'].round(1).to_dict()
    for year in (1990, 2000, 2014, 2015, 2025)
}
numbers['d1_country_share'] = {
    str(year): {
        code: round(100 * DECILES[year].query('decile == 1 and code == @code')['pop'].sum()
                    / DECILES[year].query('decile == 1')['pop'].sum(), 1)
        for code in ('CHN', 'IND', 'NGA', 'COD')
    }
    for year in (1990, 2014, 2025)
}

fig2b = alt.Chart(d1_regions).mark_area().encode(
    x=alt.X('year:Q', title=None, scale=alt.Scale(domain=[1990, LAST_YEAR], nice=False),
            axis=alt.Axis(format='d', values=list(range(1990, LAST_YEAR + 1, 5)))),
    y=alt.Y('share:Q', stack='normalize', title='Share of the poorest 10%', axis=alt.Axis(format='%')),
    color=alt.Color('region:N', sort=list(REGION_COLORS),
                    scale=alt.Scale(domain=list(REGION_COLORS), range=list(REGION_COLORS.values())),
                    legend=alt.Legend(title=None, orient='right', labelLimit=260)),
    order=alt.Order('order:Q', sort='ascending'),
).properties(
    width=380, height=240,
    title=alt.TitleParams(
        'The poorest tenth used to be mostly in Asia; today it is mostly in Africa',
        subtitle=[f'Regional composition of the global poorest 10%, 1990-{LAST_YEAR}'],
    ),
)
save(fig2b, 'fig2b_d1_regions.png')

# --- Figure 3: where the poorest tenth lives -------------------------------------------
bins_2025 = DECILES[2025]
country_d1 = (
    bins_2025.assign(in_d1=bins_2025['decile'].eq(1) * bins_2025['pop'])
    .groupby('code')[['in_d1', 'pop']].sum()
    .assign(share=lambda df: 100 * df['in_d1'] / df['pop'])
)
names = requests.get(
    'https://api.worldbank.org/v2/country', params={'format': 'json', 'per_page': 400}, timeout=60,
).json()[1]
country_d1['name'] = pd.Series({r['id']: r['name'] for r in names})
country_d1['name'] = country_d1['name'].replace({
    'Congo, Dem. Rep.': 'DR Congo', 'Congo, Rep.': 'Republic of Congo', 'Yemen, Rep.': 'Yemen',
    'Central African Republic': 'Central African Rep.', 'Somalia, Fed. Rep.': 'Somalia',
})
top = country_d1.sort_values('share', ascending=False).head(15).reset_index()
top['majority'] = top['share'].gt(50)
majority = country_d1[country_d1['share'].gt(50)].sort_values('share', ascending=False)
numbers['countries_majority_d1'] = majority['name'].tolist()
numbers['d1_people_in_majority_countries_m'] = round(majority['in_d1'].sum(), 1)
numbers['d1_total_m'] = round(bins_2025.loc[bins_2025['decile'].eq(1), 'pop'].sum(), 1)

top_base = alt.Chart(top).encode(
    y=alt.Y('name:N', sort='-x', title=None),
    x=alt.X('share:Q', title='Share of population in the global poorest 10% (%)', scale=alt.Scale(domain=[0, 100])),
)
fig3 = alt.layer(
    alt.Chart(pd.DataFrame({'x': [50]})).mark_rule(strokeDash=[3, 3], color=GOLD, strokeWidth=2).encode(x='x:Q'),
    top_base.mark_bar(height=14).encode(color=alt.condition(alt.datum.majority, alt.value(BLUE), alt.value(LIGHT))),
    top_base.mark_text(align='left', dx=4, fontSize=11).encode(
        text=alt.Text('share:Q', format='.0f'),
        color=alt.condition(alt.datum.majority, alt.value(BLUE), alt.value(DARK)),
    ),
).properties(
    width=440, height=alt.Step(18),
    title=alt.TitleParams(
        f'In {len(majority)} countries, most people belong to the world\'s poorest tenth',
        subtitle=['Share of each country\'s population in the global poorest 10%, 2025. Top 15 countries.'],
    ),
)
save(fig3, 'fig3_d1_countries.png')

# --- Figure 4: services and fragility, before vs. today --------------------------------
COMPARISONS = [
    ('Internet', 'Most people are offline', 'ITU_DH', 'IT_NET_USER', 2000, 2024),
    ('Electricity', 'Most people lack electricity', 'WB_WDI', 'WB_WDI_EG_ELC_ACCS_ZS', 2000, 2023),
    ('Sanitation', 'Most people lack basic sanitation', 'WB_WDI', 'WB_WDI_SH_STA_BASS_ZS', 2000, 2024),
]
GROUPS = {'Poorest 10%': [1], 'Second-poorest 10%': [2], 'Other 80%': range(3, 11)}


def flags_for(values, year):
    return values[values['year'].eq(year)].set_index('code')['indicator_value'].lt(THRESHOLD).astype(float)


panels = []
for name, title, dataset, indicator_id, start, end in COMPARISONS:
    values = fetch_indicator(dataset, indicator_id).drop_duplicates(['code', 'year'])
    panels.append((name, title, start, end, flags_for(values, start), flags_for(values, end)))

fcv = pd.read_csv(FCV_FILE)


def fcv_flags(year):
    # The fiscal-year N+1 list is matched to the year-N income distribution.
    listed = set(fcv.loc[fcv['wb_fiscal_year_list'].eq(year + 1) & fcv['is_fcv'].eq(1), 'country_code'])
    codes = DECILES[year]['code'].unique()
    return pd.Series([float(code in listed) for code in codes], index=codes)


panels.append(('Fragility', 'Fragile or conflict-affected state', 2000, 2025, fcv_flags(2000), fcv_flags(2025)))

rows = []
for name, title, start, end, f0, f1 in panels:
    for group, deciles in GROUPS.items():
        for period, year, flags in (('Before', start, f0), ('Today', end, f1)):
            rows.append({
                'indicator': name, 'panel': f'{title} ({start} → {end})', 'group': group,
                'period': period, 'share': group_share(DECILES[year], flags, deciles),
            })
services = pd.DataFrame(rows)
services['tone'] = services['period']
services['label_color'] = services['tone'].map({'Before': '#8C8C8C', 'Today': BLUE})
numbers['services'] = {
    name: group.pivot(index='group', columns='period', values='share').round(1).to_dict(orient='index')
    for name, group in services.groupby('indicator')
}

TONES = {'Before': LIGHT, 'Today': BLUE}
services_base = alt.Chart().encode(
    y=alt.Y('group:N', sort=list(GROUPS), title=None, axis=alt.Axis(labelFontSize=11, ticks=False, domain=False)),
    yOffset=alt.YOffset('period:N', sort=['Before', 'Today']),
    x=alt.X('share:Q', scale=alt.Scale(domain=[0, 100]), title='Share of group (%)'),
)
services_layer = alt.layer(
    services_base.mark_bar().encode(
        color=alt.Color('tone:N', sort=list(TONES), scale=alt.Scale(domain=list(TONES), range=list(TONES.values())),
                        legend=alt.Legend(title=None, orient='top')),
    ),
    services_base.transform_calculate(label="format(datum.share, '.0f') + '%'").mark_text(align='left', dx=3, fontSize=10).encode(
        text='label:N',
        color=alt.Color('label_color:N', scale=None),
    ),
    data=services,
)
fig4 = (
    services_layer
    # A step height gives each Before/Today bar its own band; a fixed height collapses them into lines.
    .properties(width=200, height=alt.Step(13))
    .facet(
        facet=alt.Facet('panel:N', sort=services['panel'].unique().tolist(), title=None,
                        header=alt.Header(labelFontSize=12, labelFontWeight='bold', labelAnchor='start')),
        columns=2,
    )
    .properties(title=alt.TitleParams(
        "Progress has largely bypassed the world's poorest tenth",
        subtitle=['Share of each group living in a country where most people lack each service, or in a fragile or conflict-affected state'],
    ))
)
save(fig4, 'fig4_services_before_today.png')

(FIGURES / 'numbers.json').write_text(json.dumps(numbers, indent=2, default=float))
print(json.dumps(numbers, indent=2, default=float))
