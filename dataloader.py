import csv

def load_data():
    # Read data from Johns Hopkins
    file_jh_confirmed = './johns-hopkins-data/time_series_covid19_confirmed_global.csv'
    with open(file_jh_confirmed) as f:
        reader = csv.reader(f)
        next(reader)
        hopkins_confirmed = []
        for row in reader:
            hopkins_confirmed.append(row)

    file_jh_deaths = './johns-hopkins-data/time_series_covid19_deaths_global.csv'
    with open(file_jh_deaths) as f:
        reader = csv.reader(f)
        next(reader)
        hopkins_deaths = []
        for row in reader:
            hopkins_deaths.append(row)

    # List of ISO codes for countries
    file_countries = './ISO-countries.csv'
    with open(file_countries) as f:
        reader = csv.reader(f)
        next(reader)
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
        if notfound:
            print(f"Not found: {country_ori}")

    # Number of days for which we have dat in the file
    countries_data = []
    number_of_days = len(hopkins_confirmed[1]) - 4
    print(f"{number_of_days} days in data set")
    for country in countries:
        temp_confirmed = [0 for i in range(number_of_days)]
        temp_deaths = [0 for i in range(number_of_days)]

        # combine rows that belong to the same country
        for row in hopkins_confirmed:
            if country[1] == row[1]:
                #temp_confirmed = temp_confirmed + row[4:]
                temp_confirmed = [int(temp_confirmed[i]) + int(row[4:][i]) for i in range(number_of_days)]
        for row in hopkins_deaths:
            if country[1] == row[1]:
                temp_deaths = [int(temp_deaths[i]) + int(row[4:][i]) for i in range(number_of_days)]

        # Create lists of differences
        temp_confirmed_prev = temp_confirmed[:-1]
        temp_confirmed_prev.insert(0,0)
        temp_confirmed_delta = [int(temp_confirmed[i]) - int(temp_confirmed_prev[i]) for i in range(len(temp_confirmed))]
        temp_deaths_prev = temp_deaths[:-1]
        temp_deaths_prev.insert(0,0)
        temp_deaths_delta = [int(temp_deaths[i]) - int(temp_deaths_prev[i]) for i in range(len(temp_deaths))]
        
        country_data = {
            'name': country[1],
            'confirmed': temp_confirmed,
            'deaths': temp_deaths,
            'confirmed_delta': temp_confirmed_delta,
            'deaths_delta': temp_deaths_delta
        }
        countries_data.append(country_data)
    return countries_data