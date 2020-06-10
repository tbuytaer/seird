import csv
import os

# Read data from Johns Hopkins
file_jh_confirmed = './johns-hopkins-data/time_series_covid19_confirmed_global.csv'
with open(file_jh_confirmed) as f:
    reader = csv.reader(f)
    header_row = next(reader)
    hopkins_confirmed = []
    for row in reader:
        hopkins_confirmed.append(row)

file_jh_deaths = './johns-hopkins-data/time_series_covid19_deaths_global.csv'
with open(file_jh_deaths) as f:
    reader = csv.reader(f)
    header_row = next(reader)
    hopkins_deaths = []
    for row in reader:
        hopkins_deaths.append(row)

# List of ISO codes for countries
file_countries = './ISO-countries.csv'
with open(file_countries) as f:
    reader = csv.reader(f)
    header_row = next(reader)
    countries_ISO = []
    for row in reader:
        countries_ISO.append(row)

# List of countries in Johns Hopkins files
countries_ori = []
for row in hopkins_confirmed:
    countries_ori.append(row[1])
countries_ori = sorted(set(countries_ori))

# List of ISO countries that can be found in Johns Hopkins files. This is the one we will be using.
countries = []
for country_ori in countries_ori:
    notfound = True
    for country_ISO in countries_ISO:
        if country_ori == country_ISO[1]:
            notfound = False
            countries.append(country_ISO)
    




# Clear the terminal
os.system('clear')
print(f"JH Confirmed: {len(hopkins_confirmed)} rows")
print(f"JH Deaths: {len(hopkins_deaths)} rows")
print(f"{len(countries_ori)} countries ORI")
print(f"{len(countries_ISO)} countries ISO")
print(f"{len(countries)} countries NOW")
#print(countries_ori)
#print(countries_ISO)
#print(countries)