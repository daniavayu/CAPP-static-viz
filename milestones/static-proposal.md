# Daniela Avayu

## Description

A tenth of the world's population, roughly one billion people, has been largely left behind by the waves of poverty reduction that have reshaped the global economy since 1990. While extreme poverty has fallen dramatically at the global level, the poorest decile has grown more slowly, gained less from globalization, and continues to lag across every measurable dimension of wellbeing.

This project builds a visual portrait of those left behind: where they live, what they lack, and how their situation compares to the rest of the world. Using the global income distribution alongside development indicators for electricity, clean water, internet access, education, and health, I want to show that the divergence of the poorest decile is not limited to income. It is systematic and multi-dimensional. Even though we cannot confirm it is always the exact same people, approximately one billion individuals appear stuck at the bottom across every indicator we can measure.

I have already done substantial exploratory analysis during my internship at the World Bank's DECDA division, including decile-level income growth comparisons and income density plots, which I will adapt and extend for this project.

## Data Sources

1. World Bank Poverty and Inequality Platform / 1000 Binned Global Distribution
2. World Bank Global Monitoring Database (GMD)
3. Data 360

### Data Source 1: Poverty and Inequality Platform 

URL: https://pip.worldbank.org/


URL: https://datacatalog.worldbank.org/search/dataset/0064304/1000-binned-global-distribution

Size: 8066000 rows and 8 columns 

This dataset contains the global distribution of welfare divided into 1,000 bins, created from the Poverty and Inequality Platform (PIP). It covers 218 World Bank economies and annual observations from 1990 to 2026. Each row is one bin for one economy and year, with the year, country code, region, bin number (quantile), a welfare value (welf), a population weight (pop), and the PIP vintage used. Because the bins are much finer than deciles, I can use them to look closely at the poorest decile (the first 100 bins) and to track how it changes over time compared with the rest of the distribution. The data is stored locally as a CSV file of about 770 MB and is processed in chunks, but there is also the possibility of using the available API. 


### Data Source 2: Global Monitoring Database

URL: Local

Size: 63,965,193 rows and 16 columns

This dataset contains harmonized household-level observations from the World Bank's Global Monitoring Database, using 2017 purchasing power parity (PPP). The variables include welfare values, survey weights, country and survey identifiers, survey years, welfare concepts, data types, coverage indicators, and comparability information. The data is stored locally as `GMD_all_2017.dta` and is processed in chunks because the file is approximately 3.5 GB. I will probably use the data for some countries, but my idea is to model some behaviors of the poorest countries. 

### Data Source 3: Data 360

URL: https://data360.worldbank.org/en/api?indicatorid=FAO_AS_4114&datasetid=FAO_AS

This is one example: total population with access to safe drinking-water. It comes from FAO, but this platform has many others, and they all have APIs to connect to the data. 

Size: 6,179 rows, 24 columns (depends on indicator and year selection, 5 to 6 columns per indicator - generally country code, country name, indicator code, year, value)

My idea here is to choose some development indicators (access to electricity, access to the internet, access to clean water, and educational indicators, among others) that have similar behavior to the poorest decile because I have the hypothesis that these indicators can show what I am trying to prove: a tenth of the population is being left behind in every aspect, and even though we can't really know if it is the same people, about a billion people are stuck in that situation either way.

