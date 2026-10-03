# Daniela Avayu

## Description

During my last weeks working on my internship at the DECDA division at the World Bank, I worked on a research project about the development of the poorest decile worldwide over the last 100 years.

For this project, I want to build a deep description of the poorest people in the world, those who have been left behind by the waves of poverty reduction: where they live, what they have, what they lack, and what characterizes them. The goal is to eventually understand why a portion of the world has not improved over the years while the rest of the world has.

## Data Sources

1. World Bank Poverty and Inequality Platform
2. World Bank Global Monitoring Database (GMD)
3. Data 360: 

### Data Source 1: Poverty and Inequality Platform 

URL: https://pip.worldbank.org/

Size: 2,588 rows and 44 columns as downloaded from the API (12 columns kept in my working table)

This dataset contains country-level poverty estimates from the World Bank's Poverty and Inequality Platform, downloaded through its API for all countries. It covers 172 countries and reporting years 1963 to 2025. The API returned a single poverty line (3.00 per day), so each row is a survey-based observation for a country, year, welfare type (consumption or income), reporting level (national, urban or rural), and survey coverage. So far I have only downloaded the data and built a working table with 12 columns: I converted the headcount ratio into a percentage and estimated the number of people below the poverty line using the reported population. I have not yet compared countries or years. A key limitation is that observations are not necessarily directly comparable across countries or years when the underlying surveys, welfare concepts, or coverage differ.

### Data Source 2: Global Monitoring Database

URL: Local

Size: 63,965,193 rows and 16 columns

This dataset contains harmonized household-level observations from the World Bank's Global Monitoring Database, using 2017 purchasing power parity (PPP). The variables include welfare values, survey weights, country and survey identifiers, survey years, welfare concepts, data types, coverage indicators, and comparability information. The data is stored locally as `GMD_all_2017.dta` and is processed in chunks because the file is approximately 3.5 GB. I will probably use the data for some countries, but my idea is to model some behaviors of the poorest countries. 

### Data Source 3: Data 360

URL: https://data360.worldbank.org/en/api?indicatorid=FAO_AS_4114&datasetid=FAO_AS

This is one example: total population with access to safe drinking-water. It comes from FAO, but this platform has many others, and they all have APIs to connect to the data. 

Size: 6,179 rows, 24 columns

My idea here is to choose some development indicators (access to electricity, access to internet, clean water usage, among others) that have similar behavior to the poorest decile because I have the hypothesis that these indicators can show what I am trying to prove: a tenth of the population is being left behind in every aspect, and even though we can't really know if it is the same people, about a billion people either way are being left behind.

## Questions

{Numbered list of questions for course staff, if any.}

1.
2.
3.