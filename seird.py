import csv
import os
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import json
import numpy
from datetime import date
from datetime import timedelta
import sys

from sirfunctions import SIR
from sirfunctions import country_SIR
from dataloader import download_data
from dataloader import load_data



def parallel_sir(country_id):
    some_country = country_SIR(countries, countries_data, country_id, average = average, future = future)
    print(f"\t{countries_data[country_id]['name']} -> {some_country['r0'][-1]}")
    country_sir = {
        'country_id': country_id,
        'name': countries_data[country_id]['name'],
        'iso': countries[country_id][0],
        'sir': some_country,
    }
    return country_sir 


def generate_jsons():
    number_of_days = len(countries_data[1]['confirmed'])
    today = len(countries_data[1]['confirmed'])

    # Calculate SIR for all countries and output progress to terminal
    start = time.time()
    print(f"\nStart: {time.asctime(time.localtime(start))}")
    print("\nLast calculated Re per country:")

    # Count the processors for parallel processing
    pool = mp.Pool(mp.cpu_count())
    countrysirs = pool.map(parallel_sir, [country_id for country_id in range(len(countries)) ] )
    pool.close()
    end = time.time()
    duration = end - start
    print(f"\nStart: {time.asctime(time.localtime(start))}")
    print(f"End: {time.asctime(time.localtime(end))}")
    print(f"Duration: {str(timedelta(seconds=duration))}")

    # output JSON files
    # Cumulative cases
    # I want to output as float with 2 decimals, so f"{something:.2f}" to print it with 2 decimal places, and then convert back to a float
    jason = [{'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': float(f"{countrysirs[country]['sir']['cumulative'][-(future + 1)] * 100_000 / int(countries[country][2]):.2f}")} for country in range(len(countrysirs))]
    #jason_file = 'export/world-cumulative.json'
    jason_file = f"export/{region}-cumulative.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Active cases
    jason = [{'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': float(f"{countrysirs[country]['sir']['infected'][-(future + 1)] * 100_000 / int(countries[country][2]):.2f}")} for country in range(len(countrysirs))]
    #jason_file = 'export/world-active.json'
    jason_file = f"export/{region}-active.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Deaths
    jason = [{'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': float(f"{countrysirs[country]['sir']['deaths'][-(future + 1)] * 100_000 / int(countries[country][2]):.1f}")} for country in range(len(countrysirs))]
    #jason_file = 'export/world-deaths.json'
    jason_file = f"export/{region}-deaths.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Calculated Re
    jason = [{ 'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': countrysirs[country]['sir']['r0'][-(future + 1)] } for country in range(len(countrysirs))]
    #jason_file = 'export/world-R0.json'
    jason_file = f"export/{region}-R0.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Calculated CFR, only if Standard Deviation less than 1% and non-zero
    country_cfrs = []
    for country in range(len(countrysirs)):
        if countrysirs[country]['sir']['CFR_std'] <= 0.01 and countrysirs[country]['sir']['CFR_std'] > 0.0:
            country_cfrs.append(countrysirs[country])
    jason = [{ 'id': country_cfrs[country]['iso'], 'nr': country_cfrs[country]['country_id'], 'value': float(f"{100 * country_cfrs[country]['sir']['CFR']:.1f}"), 'std': float(f"{100 * country_cfrs[country]['sir']['CFR_std']:.1f}") } for country in range(len(country_cfrs))]
    #jason_file = 'export/world-CFR.json'
    jason_file = f"export/{region}-CFR.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # This is a calculated risk
    jason = [{ 'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': countrysirs[country]['sir']['risk'][-(future + 1)] } for country in range(len(countrysirs))]
    #jason_file = 'export/world-risk.json'
    jason_file = f"export/{region}-risk.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Country files: date as x-value
    for country in range(len(countrysirs)):
        # JH files: confirmed
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countries_data[country]['confirmed'][day] } for day in range(len(countries_data[country]['confirmed']))]
        #jason_file = f"export/country-{country}-jh-confirmed.json"
        jason_file = f"export/{region}-{country}-jh-confirmed.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)
        # JH files: deaths
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countries_data[country]['deaths'][day] } for day in range(len(countries_data[country]['deaths']))]
        #jason_file = f"export/country-{country}-jh-deaths.json"
        jason_file = f"export/{region}-{country}-jh-deaths.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: confirmed
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countrysirs[country]['sir']['cumulative'][day] } for day in range(len(countrysirs[country]['sir']['cumulative']))]
        #jason_file = f"export/country-{country}-c.json"
        jason_file = f"export/{region}-{country}-c.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: deaths
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countrysirs[country]['sir']['deaths'][day] } for day in range(len(countrysirs[country]['sir']['deaths']))]
        #jason_file = f"export/country-{country}-m.json"
        jason_file = f"export/{region}-{country}-m.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: active
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': float(f"{countrysirs[country]['sir']['infected'][day]:.0f}") } for day in range(len(countrysirs[country]['sir']['infected']))]
        #jason_file = f"export/country-{country}-i.json"
        jason_file = f"export/{region}-{country}-i.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: Re
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countrysirs[country]['sir']['r0'][day] } for day in range(len(countrysirs[country]['sir']['r0']))]
        #jason_file = f"export/country-{country}-r0.json"
        jason_file = f"export/{region}-{country}-r0.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

    # TODO: Recovered world map?
    # TODO: Diff infections to plot per country? (JH & calculated)
    # TODO: Diff deaths to plot per country? (JH & calculated)
    # TODO: Recovered to plot per country? (JH & calculated)
    # TODO: Risk to plot per country?

    # Plot a graph
    fig, axs = plt.subplots(2, figsize=(15,10))
    plt.style.use('seaborn')
    chosen_country = 16
    some_country = country_SIR(countries, countries_data, chosen_country, average = average, future = future)

    x_values = list(range(number_of_days))
    axs[0].scatter(x_values, countries_data[chosen_country]['confirmed'],s=4)
    axs[0].scatter(x_values, countries_data[chosen_country]['deaths'],s=4)
    axs[0].scatter(x_values, countries_data[chosen_country]['d_confirmed'],s=4)
    axs[0].scatter(x_values, countries_data[chosen_country]['d_deaths'],s=4)
    axs[0].set_title(countries[chosen_country][1])

    x_values2 = list(range(number_of_days + future))
    axs[0].plot(x_values2, some_country['cumulative'], linewidth=1)
    axs[0].plot(x_values2, some_country['deaths'], linewidth=1)
    axs[0].plot(x_values2, some_country['infected'], linewidth=1)

    axs[1].plot(x_values2, some_country['r0'], linewidth=1)
    axs[1].set_ylim([0,5])

    plt.savefig('some-country.png', bbox_inches='tight')



# Clear the terminal
os.system('clear')

# Fit the model to data that has been averaged out over this amount of days before and after each date
average = 3
# Calculate this number of days ahead if current Re stays the same
future = 30

# Download most recent data files from Jons Hopkins
download_data()

# Choose which region to calculate
# python3.7 <region>
# Valid choices: world, USA

if len(sys.argv) == 1:
    print(f"No region option given. Generating data for all of them.")
    region = "USA"
    JH_data = load_data(region=region)
    countries_data = JH_data['countries_data']
    countries = JH_data['countries']
    generate_jsons()
    region = "world"
    # Load the data from Johns Hopkins
    JH_data = load_data(region=region)
    countries_data = JH_data['countries_data']
    countries = JH_data['countries']
    generate_jsons()

elif len(sys.argv) == 2:
    if sys.argv[1] == "USA":
        region = "USA"
        # Load the data from Johns Hopkins
        JH_data = load_data(region=region)
        countries_data = JH_data['countries_data']
        countries = JH_data['countries']
        generate_jsons()
    elif sys.argv[1] == "world":
        region = "world"
        # Load the data from Johns Hopkins
        JH_data = load_data(region=region)
        countries_data = JH_data['countries_data']
        countries = JH_data['countries']
        generate_jsons()
    else:
        sys.exit(f"Invalid option {sys.argv[1]}. Exiting.")
else:
    sys.exit(f"Too many options. Exiting.")
