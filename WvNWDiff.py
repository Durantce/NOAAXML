import pandas as pd
import datetime
from xml.dom.minidom import parse
from urllib.request import urlopen

stations_frame = pd.read_excel('XMLPerStation.xlsx')
stations_frame.index = stations_frame['Station ID']
stations_frame.drop('Station ID', axis=1, inplace=True)

population_dataframe = pd.read_excel('PopulationByFIPS.xlsx')
population_dataframe.index = [str(fips_code).zfill(5) for fips_code in population_dataframe['Fips']]

now = datetime.datetime.now()
runtime = now.strftime('%m-%d-%y @ {}:{}'.format(now.hour, now.minute))

for inum, row in enumerate(stations_frame.iterrows()):
    
    try:
        
        
        url1 = row[1]['xml url']

        value = float(minidom.parse(urlopen(url1)).getElementsByTagName('current_observation')[0].getElementsByTagName('temp_f')[0].childNodes[0].data)

        stations_frame.loc[inum:inum+1, 'Temperature'] = value
        
    except IndexError:
        
        print('INDEX ERROR: Dropping ', row[0])
        stations_frame.drop(row[0], inplace=True,axis=0)
    
stations_frame.dropna(axis=0, inplace=True)

non_weighted_national_average = np.average([temp for temp in stations_frame['Temperature']])

county_averages = {fips:np.average([temp for temp in fips_frame['Temperature']]) for fips, fips_frame in stations_frame.groupby('FIPS')}

total_population = 0
keys_to_pop = []

for key, value in county_averages.items():
    
    if key in population_dataframe.index:
        
        total_population += population_dataframe.loc[key]['Population']
        
    else:
        
        keys_to_pop.append(key)
    
for key in keys_to_pop:
    
    county_averages.pop(key)
    
weighted_national_average = 0

for key, value in county_averages.items():
    
    county_weight = population_dataframe.loc[key]['Population']/total_population
    
    weighted_temp = value*county_weight
    
    weighted_national_average += weighted_temp
    
difference = weighted_national_average - non_weighted_national_average

print('{}: {}'.format(runtime, difference))
