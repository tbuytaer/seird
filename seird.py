import csv
import os
import matplotlib.pyplot as plt

from dataloader import load_data

# Clear the terminal
os.system('clear')

# Get the data from Johns Hopkins
JH_data = load_data()
countries_data = JH_data['countries_data']
countries = JH_data['countries']

number_of_days = len(countries_data[1]['confirmed'])


def SIR(country, dday, population0, incubation0, infected0, epsilon, gamma, delta, listr0):
    """ calculate SIR model for a country, up till a certain day, with a set of initial parameters """
    population = population0
    incubation = incubation0
    infected = infected0
    recovered = 0
    deaths = 0
    cumulative = infected + recovered + deaths
    susceptible = population - incubation - infected -recovered - deaths
    cost = 0
    for sirday in range(0, dday + 1):
        lamb = (gamma + delta) * listr0[sirday]
        d_susceptible = - lamb * infected * (susceptible / population)
        d_incubation = lamb * infected * (susceptible / population) - epsilon * incubation
        infected_new = lamb * infected * (susceptible / population)
        d_infected = epsilon * incubation - gamma * infected - delta * infected
        d_recovered = gamma * infected
        d_deaths = delta * infected
        d_cumulative = d_infected + d_recovered + d_deaths
        susceptible += d_susceptible
        incubation += d_incubation
        infected += d_infected
        recovered += d_recovered
        deaths += d_deaths
        cumulative += d_cumulative
        population = susceptible + incubation + infected + recovered
        risk = infected * listr0[sirday]
        if sirday < len(countries_data[country]['confirmed']):
            cost += (cumulative - countries_data[country]['confirmed'][sirday]) ** 2
    sir = {
        'susceptible': susceptible,
        'infected': infected,
        'recovered': recovered,
        'deaths': deaths,
        'cumulative': cumulative,
        'cost': cost,
        'd_infected': d_infected,
        'd_deaths': d_deaths,
        'infected_new': infected_new,
        'risk': risk,
    }
    return sir


def country_SIR(country, window = 4, future = 30):
    """ calculate SIR model for a country, with a certain window size, and a number of days ahead """
    CFR = countries_data[country]['deaths'][-1] / countries_data[country]['confirmed'][-1]

    population0 = int(countries[country][2])
    incubation0 = 5
    infected0 = 1
    epsilon = 1/2
    gamma = (1 - CFR) / 12.4
    delta = CFR / 10.4
    listr0 = []

    # create a list of default R0 values. They will be replaced with better values later.
    for day in range(0, len(countries_data[country]['confirmed']) + future):
        listr0.append(4.3)

    # fit model to the data
    for day in range(0, len(countries_data[country]['confirmed']) - window):
        bestr0 = listr0[day]
        sir = SIR(country, day + window, population0, incubation0, infected0, epsilon, gamma, delta, listr0)
        bestcost = sir['cost']
        # range uses int, so we will need to divide this r0 by 100 later: 5 should become 0.05. 
        for r0 in range(10, 2000, 5):
            # set this selected r0 for all following days
            for futureday in range(0, len(listr0) - day):
                # r0 is still an integer. Divide it by 100
                listr0[day + futureday] = r0 / 100
            sir_temp = SIR(country, day + window, population0, incubation0, infected0, epsilon, gamma, delta, listr0)
            if sir_temp['cost'] < bestcost:
                bestcost = sir_temp['cost']
                # r0 is still an integer. Divide it by 100
                bestr0 = r0 / 100

        # We found a good r0 for this day, set it for all the following days
        for futureday in range(0, len(listr0) - day):
            listr0[day + futureday] = bestr0

    # Generate lists of data for the plots and exports
    list_susceptible = []
    list_infected = []
    list_recovered = []
    list_deaths = []
    list_cumulative = []
    list_d_infected = []
    list_d_deaths = []
    list_infected_new = []
    list_risk = []
    # Append the daily values to the lists
    for day in range(0,len(countries_data[country]['confirmed']) + future):
        temp_sir = SIR(country, day, population0, incubation0, infected0, epsilon, gamma, delta, listr0)
        list_susceptible.append(temp_sir['susceptible'])
        list_infected.append(temp_sir['infected'])
        list_recovered.append(temp_sir['recovered'])
        list_deaths.append(temp_sir['deaths'])
        list_cumulative.append(temp_sir['cumulative'])
        list_d_infected.append(temp_sir['d_infected'])
        list_d_deaths.append(temp_sir['d_deaths'])
        list_infected_new.append(temp_sir['infected_new'])
        list_risk.append(temp_sir['risk'])
    # Return the lists
    country_sir = {
        'susceptible': list_susceptible,
        'infected': list_infected,
        'recovered': list_recovered,
        'deaths': list_deaths,
        'cumulative': list_cumulative,
        'd_infected': list_d_infected,
        'd_deaths': list_d_deaths,
        'infected_new': list_infected_new,
        'risk': list_risk,
        'r0': listr0,
        'CFR': CFR,
    }
    return country_sir


chosen_country = 16
some_country = country_SIR(chosen_country)
today = len(countries_data[1]['confirmed'])

# Output some of the data to terminal
print(countries_data[chosen_country]['name'])
print(countries_data[chosen_country]['confirmed'])
print(some_country['r0'])

# Plot a graph
fig, ax = plt.subplots(figsize=(15,10))
plt.style.use('seaborn')

x_values = list(range(number_of_days))
ax.scatter(x_values, countries_data[chosen_country]['confirmed'],s=4)
ax.scatter(x_values, countries_data[chosen_country]['deaths'],s=4)
ax.scatter(x_values, countries_data[chosen_country]['d_confirmed'],s=4)
ax.scatter(x_values, countries_data[chosen_country]['d_deaths'],s=4)

x_values2 = list(range(number_of_days + 30))
ax.plot(x_values2, some_country['cumulative'], linewidth=1)
ax.plot(x_values2, some_country['deaths'], linewidth=1)
ax.plot(x_values2, some_country['infected'], linewidth=1)

plt.savefig('some-country.png', bbox_inches='tight')