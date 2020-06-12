import numpy

def SIR(countries_data, country, dday, population0, incubation0, infected0, epsilon, gamma, delta, listr0, running_average_confirmed):
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
            #cost += (cumulative - countries_data[country]['confirmed'][sirday]) ** 2
            cost += (cumulative - running_average_confirmed[sirday]) ** 2
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


def country_SIR(countries, countries_data, country, window = 4, future = 30, average = 3):
    """ calculate SIR model for a country, with a certain window size, and a number of days ahead """
    CFR = countries_data[country]['deaths'][-1] / countries_data[country]['confirmed'][-1]

    running_average_confirmed = running_mean(countries_data[country]['confirmed'], average)
    #print(f"Running average: {countries_data[country]['confirmed']}")
    #print(f"Running average: {running_average_confirmed}")


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
        sir = SIR(countries_data, country, day + window, population0, incubation0, infected0, epsilon, gamma, delta, listr0, running_average_confirmed)
        bestcost = sir['cost']
        # range uses int, so we will need to divide this r0 by 100 later: 5 should become 0.05. 
        for r0 in range(10, 2000, 5):
            # set this selected r0 for all following days
            for futureday in range(0, len(listr0) - day):
                # r0 is still an integer. Divide it by 100
                listr0[day + futureday] = r0 / 100
            sir_temp = SIR(countries_data, country, day + window, population0, incubation0, infected0, epsilon, gamma, delta, listr0, running_average_confirmed)
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
        temp_sir = SIR(countries_data, country, day, population0, incubation0, infected0, epsilon, gamma, delta, listr0, running_average_confirmed)
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


def running_mean(x, N):
    """ Take the running mean of list x, over N past and N future elements."""
    # Add the first number N times so we end up with the same number of elements at the end
    x = numpy.insert(x, 0, [x[0] for i in range(N)])
    x = numpy.insert(x, -1, [x[-1] for i in range(N)])
    cumsum = numpy.cumsum(x)
    # cumsum[N:] is cumulative sum, shifted N elements to the left. So each element is what total will be N elements later.
    # cumsum[:-N] is cumulative sum now
    # So cumsum[N:] - cumsum[:N] gives total over next N elements
    return (cumsum[2*N:] - cumsum[:-2*N]) / float(2*N)

def running_mean_past(x, N):
    """ Take the running mean of list x, over N elements."""
    # Add the first number N times so we end up with the same number of elements at the end
    cumsum = numpy.cumsum(numpy.insert(x, 0, [x[0] for i in range(N)]))
    # cumsum[N:] is cumulative sum, shifted N elements to the left. So each element is what total will be N elements later.
    # cumsum[:-N] is cumulative sum now
    # So cumsum[N:] - cumsum[:N] gives total over next N elements
    return (cumsum[N:] - cumsum[:-N]) / float(N)