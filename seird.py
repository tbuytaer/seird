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
from sirfunctions import country_CFR
from sirfunctions import running_mean
from sirfunctions import generate_lists
from dataloader import download_data
from dataloader import load_data


def parallel_sir(country_id):
    """"Calculate different variations of SIR for a country."""
    CFR = country_CFR(countries_data, country_id)
    running_average_confirmed = running_mean(countries_data[country_id]['confirmed'], average)
    # Initial values for this country
    initial_values = {
        'day': 0,
        'population': int(countries[country_id][2]),
        'susceptible': int(countries[country_id][2]),
        'incubation': 1,
        'infected': 1,
        'recovered': 0,
        'deaths': 0,
        'cumulative': 0,
        'cost': 0,
    }
    variations = []
    # Vary epsilon_tau
    for epsilon_k in range(0,2):
        epsilon_tau = 1 + epsilon_k
        # Vary delta_tau
        for delta_k in range(0,3):
            delta_tau = 8.4 + delta_k
            # Vary gamma_tau
            for gamma_k in range(0,3):
                gamma_tau = 10.4 + gamma_k
                variation_sir = country_SIR(countries, countries_data, country_id, CFR, initial_values, running_average_confirmed, window = 4, future = future, average = average, epsilon_tau = epsilon_tau, gamma_tau = gamma_tau, delta_tau = delta_tau)
                variations.append({
                    'epsilon_tau': epsilon_tau,
                    'gamma_tau': gamma_tau,
                    'delta_tau': delta_tau,
                    'cost': variation_sir['cost'],
                    'r0': variation_sir['r0'],
                })
    # Get the variation with best fit
    variations_costs = []
    variations_r0 = []
    for variation in variations:
        variations_costs.append(variation['cost'])
        variations_r0.append(variation['r0'])
    best_fit_index = variations_costs.index(min(variations_costs))
    r0_average = numpy.average(variations_r0, axis=0)
    r0_std = numpy.std(variations_r0, axis=0)
    # Generate the data points to plot and output
    sir = generate_lists(countries_data, country_id, CFR, initial_values, future, average, variations[best_fit_index]['epsilon_tau'], variations[best_fit_index]['gamma_tau'], variations[best_fit_index]['delta_tau'], variations[best_fit_index]['r0'], running_average_confirmed)
    # Return best fit and variations
    country_sir = {
        'country_id': country_id,
        'name': countries_data[country_id]['name'],
        'iso': countries[country_id][0],
        'sir': sir,
        'variations': variations,
        'r0_average': r0_average,
        'r0_std': r0_std,
    }
    print(f"{country_id} | {country_sir['name']} -> {country_sir['sir']['r0'][-1]}")
    return country_sir 


def generate_jsons():
    number_of_days = len(countries_data[1]['confirmed'])
#    today = len(countries_data[1]['confirmed'])

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
    jason_file = f"export/{region}-cumulative.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Active cases
    jason = [{'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': float(f"{countrysirs[country]['sir']['infected'][-(future + 1)] * 100_000 / int(countries[country][2]):.2f}")} for country in range(len(countrysirs))]
    jason_file = f"export/{region}-active.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Deaths
    jason = [{'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': float(f"{countrysirs[country]['sir']['deaths'][-(future + 1)] * 100_000 / int(countries[country][2]):.1f}")} for country in range(len(countrysirs))]
    jason_file = f"export/{region}-deaths.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Calculated Re
    jason = [{ 'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': countrysirs[country]['sir']['r0'][-(future + 1)] } for country in range(len(countrysirs))]
    jason_file = f"export/{region}-R0.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Calculated CFR, only if Standard Deviation less than 1% and non-zero
    country_cfrs = []
    for country in range(len(countrysirs)):
        if countrysirs[country]['sir']['CFR_std'] <= 0.01 and countrysirs[country]['sir']['CFR_std'] > 0.0:
            country_cfrs.append(countrysirs[country])
    jason = [{ 'id': country_cfrs[country]['iso'], 'nr': country_cfrs[country]['country_id'], 'value': float(f"{100 * country_cfrs[country]['sir']['CFR']:.1f}"), 'std': float(f"{100 * country_cfrs[country]['sir']['CFR_std']:.1f}") } for country in range(len(country_cfrs))]
    jason_file = f"export/{region}-CFR.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # This is a calculated risk
    jason = [{ 'id': countrysirs[country]['iso'], 'nr': countrysirs[country]['country_id'], 'value': countrysirs[country]['sir']['risk'][-(future + 1)] } for country in range(len(countrysirs))]
    jason_file = f"export/{region}-risk.json"
    with open(jason_file, 'w') as f:
        json.dump(jason, f, indent=4)

    # Country files: date as x-value
    for country in range(len(countrysirs)):
        # JH files: confirmed
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countries_data[country]['confirmed'][day] } for day in range(len(countries_data[country]['confirmed']))]
        jason_file = f"export/{region}-{country}-jh-confirmed.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # JH files: deaths
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countries_data[country]['deaths'][day] } for day in range(len(countries_data[country]['deaths']))]
        jason_file = f"export/{region}-{country}-jh-deaths.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: confirmed
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countrysirs[country]['sir']['cumulative'][day] } for day in range(len(countrysirs[country]['sir']['cumulative']))]
        jason_file = f"export/{region}-{country}-c.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: deaths
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countrysirs[country]['sir']['deaths'][day] } for day in range(len(countrysirs[country]['sir']['deaths']))]
        jason_file = f"export/{region}-{country}-m.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: active
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': float(f"{countrysirs[country]['sir']['infected'][day]:.0f}") } for day in range(len(countrysirs[country]['sir']['infected']))]
        jason_file = f"export/{region}-{country}-i.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

        # Calculated files: Re
        jason = [{ 'date': (date(2020, 1, 22) + timedelta(days=day)).strftime("%Y-%m-%d"), 'value': countrysirs[country]['sir']['r0'][day] } for day in range(len(countrysirs[country]['sir']['r0']))]
        jason_file = f"export/{region}-{country}-r0.json"
        with open(jason_file, 'w') as f:
            json.dump(jason, f, indent=4)

    # TODO: Recovered world map?
    # TODO: Diff infections to plot per country? (JH & calculated)
    # TODO: Diff deaths to plot per country? (JH & calculated)
    # TODO: Recovered to plot per country? (JH & calculated)
    # TODO: Risk to plot per country?

    # Plot a graph
    plt.style.use('bmh')
    fig, axs = plt.subplots(4, figsize=(15,20), gridspec_kw={'height_ratios': [2,1,1,1]})
    chosen_country = 16
    some_country = countrysirs[chosen_country]['sir']

    x_values = list(range(number_of_days))
    x_values2 = list(range(number_of_days + future))
    # Scatter plots with values from JH
    axs[0].set_title(countries[chosen_country][1])
    axs[0].scatter(x_values, countries_data[chosen_country]['confirmed'], s=4, c='cadetblue')
    axs[0].scatter(x_values, countries_data[chosen_country]['deaths'], s=4, c='firebrick')
    # Line plots with calculcated values from model
    axs[0].plot(x_values2, some_country['cumulative'], linewidth=1, c='darkslateblue')
    axs[0].plot(x_values2, some_country['deaths'], linewidth=1, c='firebrick')
    axs[0].plot(x_values2, some_country['infected'], linewidth=1, c='cornflowerblue')
    axs[0].fill_between(x_values2, some_country['infected'], facecolor='lightsteelblue')

    # Line plot with calculated R-value from model
    axs[1].set_title(f"Last R: {some_country['r0'][-1]}", loc='right')
    axs[1].set_ylabel("R-value")
    axs[1].plot(x_values2, some_country['r0'], linewidth=1, c='steelblue')
    axs[1].fill_between(x_values2, some_country['r0'], facecolor='lightsteelblue')
    axs[1].set_ylim([0,5])

    # Scatter plots with values from JH
    axs[2].set_ylabel("New infected")
    axs[2].scatter(x_values, countries_data[chosen_country]['d_confirmed'], s=4, c='darkslateblue')
    axs[2].plot(x_values2, some_country['infected_new'], linewidth=1, c='royalblue')

    # Line plots with calculated values from model
    axs[3].set_ylabel("New deaths")
    axs[3].scatter(x_values, countries_data[chosen_country]['d_deaths'], s=4, c='firebrick')
    axs[3].plot(x_values2, some_country['d_deaths'], linewidth=1, c='firebrick')

    # Save plot with name of this state
    plt.savefig(f"./export/{countries[chosen_country][1]}.png", bbox_inches='tight')

# Clear the terminal
os.system('clear')

# Fit the model to data that has been averaged out over this amount of days before and after each date
average = 3

# Calculate this number of days ahead if current Re stays the same
future = 30

# Download most recent data files from Jons Hopkins
download_data()

# Choose which region to calculate
# python3.6 <region>
# Valid choices: all, world, USA

if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "all"):
    print(f"No region option given. Generating data for all of them.")
    # Load data from Johns Hopkins for region 'USA'
    region = "USA"
    JH_data = load_data(region=region)
    countries_data = JH_data['countries_data']
    countries = JH_data['countries']
    # Fit the model and generate JSON for region 'USA'
    generate_jsons()
    # Load data from Johns Hopkins for region 'world'
    region = "world"
    JH_data = load_data(region=region)
    countries_data = JH_data['countries_data']
    countries = JH_data['countries']
    # Fit the model and generate JSON for region 'world'
    generate_jsons()
elif len(sys.argv) == 2:
    if sys.argv[1] == "USA":
        # Load data from Johns Hopkins
        region = "USA"
        JH_data = load_data(region=region)
        countries_data = JH_data['countries_data']
        countries = JH_data['countries']
        # Fit the model and generate JSON
        generate_jsons()
    elif sys.argv[1] == "world":
        # Load data from Johns Hopkins
        region = "world"
        JH_data = load_data(region=region)
        countries_data = JH_data['countries_data']
        countries = JH_data['countries']
        # Fit the model and generate JSON
        generate_jsons()
    else:
        sys.exit(f"Invalid option {sys.argv[1]}. Exiting.")
else:
    sys.exit(f"Too many options. Exiting.")
