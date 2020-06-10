import csv
import os
import matplotlib.pyplot as plt

from dataloader import load_data

# Clear the terminal
os.system('clear')

# Get the data from Johns Hopkins
countries_data = load_data()

number_of_days = len(countries_data[1]['confirmed'])

print(countries_data[16]['name'])
print(countries_data[16]['confirmed'])

# Plot a graph
fig, ax = plt.subplots()
plt.style.use('seaborn')
x_values = list(range(number_of_days))
ax.scatter(x_values, countries_data[16]['confirmed'],s=4)
ax.scatter(x_values, countries_data[16]['deaths'],s=4)
ax.scatter(x_values, countries_data[16]['confirmed_delta'],s=4)
ax.scatter(x_values, countries_data[16]['deaths_delta'],s=4)
plt.savefig("test.png")

