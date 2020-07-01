import numpy
import copy

def SIR(countries_data, country, dday, population, incubation, infected, CFR, epsilon_tau, gamma_tau, delta_tau, listr0, running_average_confirmed, running_average_deaths, average, susceptible, recovered, deaths, cumulative, startday, cost2):
    """ calculate SIR model for a country, up till a certain day, with a set of initial parameters """
    cost = 0
    #cost2 = 0
    epsilon = 1 / epsilon_tau
    gamma = (1 - CFR['CFR']) / gamma_tau
    delta = CFR['CFR'] / delta_tau

    # While fitting, dday will always be startday + window and we will already have the sir values until startday
    # After fitting we want to generate the values for every day, so we will start from zero again.
    for sirday in range(startday, dday + 1):
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
        risk = infected * listr0[sirday] * 100_000 / population
        if sirday < len(countries_data[country]['confirmed']) - average:
            #cost += (cumulative - countries_data[country]['confirmed'][sirday]) ** 2
            cost += (cumulative - running_average_confirmed[sirday]) ** 2
            cost2 += (deaths - running_average_deaths[sirday]) ** 2
        if sirday == startday:
            values_today = {
                'population': population,
                'susceptible': susceptible,
                'incubation': incubation,
                'infected': infected,
                'recovered': recovered,
                'deaths': deaths,
                'cumulative': cumulative,
                'risk': risk,
                'd_infected': d_infected,
                'd_deaths': d_deaths,
                'infected_new': infected_new,
                'cost': cost,
                'cost2': cost2,
            }
    sir = {
        'population': population,
        'susceptible': susceptible,
        'incubation': incubation,
        'infected': infected,
        'recovered': recovered,
        'deaths': deaths,
        'cumulative': cumulative,
        'risk': risk,
        'd_infected': d_infected,
        'd_deaths': d_deaths,
        'infected_new': infected_new,
        'cost': cost,
        'cost2': cost2,
        'values_today': values_today,
    }
    return sir


def country_SIR(countries, countries_data, country, CFR, initial_values, running_average_confirmed, running_average_deaths, window = 4, future = 30, average = 3, epsilon_tau = 2, gamma_tau = 12.4, delta_tau = 10.4):
    """ calculate SIR model for a country, with a certain window size, and a number of days ahead """
    # create a list of default R0 values. They will be replaced with better values later.
    listr0 = []
    bestcost = 0
    best_values = copy.deepcopy(initial_values)
    for day in range(0, len(countries_data[country]['confirmed']) + future):
        listr0.append(4.3)

    # fit model to the data
    for day in range(0, len(countries_data[country]['confirmed']) - window):
        bestr0 = listr0[day]
        bestcost = 1000_000_000_000
        previous_values = copy.deepcopy(best_values)
        # range uses int, so we will need to divide this r0 by 100 later: 5 should become 0.05. 
        for r0 in range(10, 2000, 5):
            # set this selected r0 for all following days
            for futureday in range(0, len(listr0) - day):
                # r0 is still an integer. Divide it by 100
                listr0[day + futureday] = r0 / 100
            sir_temp = SIR(countries_data, country, day + window, previous_values['population'], previous_values['incubation'], previous_values['infected'], CFR, epsilon_tau, gamma_tau, delta_tau, listr0, running_average_confirmed, running_average_deaths, average, previous_values['susceptible'], previous_values['recovered'], previous_values['deaths'], previous_values['cumulative'], day, previous_values['cost2'])
            if sir_temp['cost'] < bestcost:
                # save values of currently best fit to use as starting point for next day
                best_values = {
                    'day': day,
                    'population': sir_temp['values_today']['population'],
                    'susceptible': sir_temp['values_today']['susceptible'],
                    'incubation': sir_temp['values_today']['incubation'],
                    'infected': sir_temp['values_today']['infected'],
                    'recovered': sir_temp['values_today']['recovered'],
                    'deaths': sir_temp['values_today']['deaths'],
                    'cumulative': sir_temp['values_today']['cumulative'],
                    'cost': sir_temp['values_today']['cost'],
                    'cost2': sir_temp['values_today']['cost2'],
                }
                bestcost = sir_temp['cost']
                bestcost2 = sir_temp['cost2']
                # r0 is still an integer. Divide it by 100
                bestr0 = r0 / 100

        # We found a good r0 for this day, set it for all the following days
        for futureday in range(0, len(listr0) - day):
            listr0[day + futureday] = bestr0
    r0s_and_cost = {
        'r0': listr0,
        'cost': bestcost,
        'cost2': bestcost2,
    }
    return r0s_and_cost


def running_mean(x, N):
    """
    Take the running mean of list x, over N past and N future elements.
    Since the last element is copied N times, the last N means will give increasing weight to the last value in the array.
    """
    # Shift list N elements to the right.
    x = numpy.insert(x, 0, [x[0] for i in range(N)])
    # Take the cumulative sum.
    cumsum = numpy.cumsum(x)
    # cumsum[2*N:] is cumulative sum, shifted 2*N elements to the left. So each element is what total will be 2*N elements later.
    # But we already shifted N to the right.
    # So cumsum[2*N:] is total N elements in the future.
    # cumsum[:-2*N] is cumulative sum N elements ago because the array was shifted N elements to the right.
    # We drop the last 2*N elements to have the same length as the other list.
    # So cumsum[2*N:] - cumsum[:-2*N] gives total over N past and N future elements
    return (cumsum[2*N:] - cumsum[:-2*N]) / float(2*N)


def running_mean_past(x, N):
    """ Take the running mean of list x, over N past elements."""
    # Shift list N elements to the right and take the cumulative sum.
    cumsum = numpy.cumsum(numpy.insert(x, 0, [x[0] for i in range(N)]))
    # cumsum[N:] is cumulative sum, shifted N elements to the left. So each element is what total will be N elements later.
    # But we already shifted N to the right. So we actually end up with the cumulative sum of the original list.
    # cumsum[:-N] is cumulative sum N elements ago because the array was shifted N elements to the right.
    # We drop the last N elements to have the same length as the other list.
    # So cumsum[N:] - cumsum[:-N] gives total over past N elements
    return (cumsum[N:] - cumsum[:-N]) / float(N)


def country_CFR(countries_data, country):
    """ Calculate CFR with standard deviation """
    cfr_temp = []
    confirmeds = numpy.array(countries_data[country]['confirmed'], dtype='float')
    for delay in range (1, 20):
        # shift array with deaths to the left by 'delay' days, and divide by 'confirmed' array
        deaths_shifted = numpy.array(numpy.concatenate((countries_data[country]['deaths'][delay:], [0 for i in range(delay)])), dtype='float')
        # divide deaths / cases. If cases = 0, output 0 instead
        cfrs = numpy.divide(deaths_shifted, confirmeds, out=numpy.zeros_like(deaths_shifted), where=confirmeds!=0)
        # get index of last non-zero value
        last_cfr_index = numpy.nonzero(cfrs)
        # add the CFR for this delay to list cfr_temp
        try:
            cfr_temp.append(cfrs[last_cfr_index[0][-1]])
        except IndexError:
            # There were no non-zero elements, so set CFR to zero. Otherwise the Python gets angry.
            cfr_temp.append(0)
    CFR = {
        'CFR': numpy.mean(cfr_temp),
        'CFR_std': numpy.std(cfr_temp),
    }
    return CFR


def generate_lists(countries_data, country, CFR, initial_values, future, average, epsilon_tau, gamma_tau, delta_tau, listr0, running_average_confirmed, running_average_deaths):
    """ Generate lists of data for the plots and exports. """
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
        temp_sir = SIR(countries_data, country, day, initial_values['population'], initial_values['incubation'], initial_values['infected'], CFR, epsilon_tau, gamma_tau, delta_tau, listr0, running_average_confirmed, running_average_deaths, average, initial_values['susceptible'], initial_values['recovered'], initial_values['deaths'], initial_values['cumulative'], 0, 0)
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
        'CFR': CFR['CFR'],
        'CFR_std': CFR['CFR_std'],
    }
    return country_sir
