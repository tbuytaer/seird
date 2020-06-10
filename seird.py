import csv
import os

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

countrylist_ori = []
for row in hopkins_confirmed:
    countrylist_ori.append(row[1])
countrylist_ori = sorted(set(countrylist_ori))


# Clear the terminal
os.system('clear')
print(f"JH Confirmed: {len(hopkins_confirmed)} rows")
print(f"JH Deaths: {len(hopkins_deaths)} rows")
print(f"{len(countrylist_ori)} countries")
print(countrylist_ori)