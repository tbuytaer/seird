import csv
import os
import matplotlib.pyplot as plt
import time
import multiprocessing as mp

from sirfunctions import SIR
from sirfunctions import country_SIR
from dataloader import load_data


# Clear the terminal
os.system('clear')

# Get the data from Johns Hopkins
JH_data = load_data()
countries_data = JH_data['countries_data']
countries = JH_data['countries']

number_of_days = len(countries_data[1]['confirmed'])


start = time.time()
print(f"\nStart: {time.asctime(time.localtime(start))}")

today = len(countries_data[1]['confirmed'])

# Calculate SIR for all countries and output progress to terminal
print("\nLast calculated Re per country:")

def parallel_sir(country_id):
    some_country = country_SIR(countries, countries_data, country_id)
    print(f"\t{countries_data[country_id]['name']} -> {some_country['r0'][-1]}")

# Count the processors for parallel processing
pool = mp.Pool(mp.cpu_count())
pool.map(parallel_sir, [country_id for country_id in range(len(countries)) ] )

pool.close()


end = time.time()
duration = end - start
print(f"\nStart: {time.asctime(time.localtime(start))}")
print(f"End: {time.asctime(time.localtime(end))}")
print(f"Duration: {duration:.1f} seconds")



# Plot a graph
fig, ax = plt.subplots(figsize=(15,10))
plt.style.use('seaborn')
chosen_country = 16
some_country = country_SIR(countries, countries_data, chosen_country)

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