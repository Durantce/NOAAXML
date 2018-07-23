import pandas as pd
import datetime
from xml.dom.minidom import parse
from urllib.request import urlopen
import numpy as np
import openpyxl

class NOAAXML(object):
    
    def __init__(self, excel_file_name, stations_frame, population_dataframe):
        
        self.excel_file_name = excel_file_name
        self.stations_frame = stations_frame
        self.population_dataframe = population_dataframe
        
    def ReformatFrames(self):
        
        self.stations_frame.index = self.stations_frame['Station ID']
        self.stations_frame.drop('Station ID', axis=1, inplace=True)
        
        self.population_dataframe.index = [str(fips_code).zfill(5) for fips_code in self.population_dataframe['Fips']]
        
    def GetTemperatures(self):
        
        now = datetime.datetime.now()
        
        for inum, row in enumerate(self.stations_frame.iterrows()):

            try:

                url1 = row[1]['xml url']

                value = float(parse(urlopen(url1)).getElementsByTagName('current_observation')[0].getElementsByTagName('temp_f')[0].childNodes[0].data)

                self.stations_frame.loc[inum:inum+1, 'Temperature'] = value

            except:

                self.stations_frame.drop(row[0], inplace=True,axis=0)

        self.stations_frame.dropna(axis=0, inplace=True)
        
        self.non_weighted_national_average = np.average([temp for temp in self.stations_frame['Temperature']])

        self.county_averages = {fips:np.average([temp for temp in fips_frame['Temperature']]) for fips, fips_frame in self.stations_frame.groupby('FIPS')}

        total_population = 0
        keys_to_pop = []

        for key, value in self.county_averages.items():

            if key in self.population_dataframe.index:

                total_population += self.population_dataframe.loc[key]['Population']

            else:

                keys_to_pop.append(key)

        for key in keys_to_pop:

            self.county_averages.pop(key)

        self.weighted_national_average = 0

        for key, value in self.county_averages.items():

            county_weight = self.population_dataframe.loc[key]['Population']/total_population

            weighted_temp = value*county_weight

            self.weighted_national_average += weighted_temp

        self.difference = self.weighted_national_average - self.non_weighted_national_average
        
        return [now, self.difference]
    
if __name__ == '__main__':
    
    excel_file_name = 'NOAAFeed.xlsx'
    stations_frame = pd.read_excel('XMLPerStation.xlsx')
    population_dataframe = pd.read_excel('PopulationByFIPS.xlsx')
        
    data = NOAAXML(excel_file_name, stations_frame, population_dataframe)

    data.ReformatFrames()

    diff = data.GetTemperatures()

    workbook = openpyxl.load_workbook(excel_file_name)
    data_sheet = workbook['Data']

    data_sheet.append([now, difference])

    workbook.save(excel_file_name)
