"""
Script to compile Weather Files from Solcast.
Requires the CSVs from SolCast and a "road file" to give the
corresponding race distance. Run the script in the same folder as all the CSVs or change the variable csv_location
"""
import tqdm
if __name__ == '__main__':
    import sys
    sys.path.append('E:/solar_car_race_strategy/S5')
import os
import re
import datetime
import pandas as pd
import numpy as np
from pvlib import solarposition
import pytz.tzinfo
from tqdm import trange
import S5.Tecplot as TP
from S5.Weather.Atm import convert_wind
from tqdm import trange

csv_location = '.'
tz = pytz.timezone('Australia/Darwin')
start_date = datetime.datetime(2019, 10, 13, 0, 0, tzinfo=tz)
end_date = datetime.datetime(2019, 10, 20, 23, 0, tzinfo=tz)

RoadTP = TP.TecplotData('E:\solar_car_race_strategy\SolCastHistoric\Road-SolCast-10km.dat')


def _makedatetimecol(df):
    df.loc[:, 'Day'] = df.index.day - df.index.day[0] + 1  # convert to day of race, 1 indexed
    df.loc[:, 'Time (HHMM)'] = df.index.strftime("%H%M")
    return df

f = re.compile('.*Solcast.*.csv')
file = filter(f.match, os.listdir(csv_location))
infile = pd.DataFrame(list(file))
infile.columns = ['File']
infile.loc[:, ['Latitude', 'Longitude']] = infile['File'].str.extract('(.*)_(.*)_Solcast.*').astype(
    'float64').to_numpy()
infile = infile.merge(RoadTP.data[['Distance (km)', 'Latitude', 'Longitude']], left_on=['Latitude', 'Longitude'],
             right_on=['Latitude', 'Longitude'])


i = 0
df = pd.read_csv(infile.loc[i, 'File'])
df.loc[:, ['PeriodEnd', 'PeriodStart']] = df.loc[:, ['PeriodEnd', 'PeriodStart']].astype(np.datetime64)
# take the centre of the measurement period as the data record time.
# df.loc[:, 'DateTime'] = df['PeriodStart'] + (df['PeriodEnd'].to_numpy() - df['PeriodStart'].to_numpy())/2
df.loc[:,'DateTime'] = df['PeriodStart']

df.drop(columns = ['PeriodEnd', 'PeriodStart'],inplace=True)
df.rename(columns={'Dni': 'DirectSun (W/m2)', 'Dhi': 'DiffuseSun (W/m2)', 'AirTemp': 'AirTemp (degC)',
                    'SurfacePressure': 'AirPress (hPa)', 'WindSpeed10m': '10m WindVel (m/s)',
                   'WindDirection10m': 'WindDir (deg)',
                   'Azimuth': 'SunAzimuth (deg)'}, inplace=True)
df = convert_wind(df)
df.loc[:, 'SunElevation (deg)'] = 90 - df['Zenith']
df.loc[:,'SunAzimuth (deg)'] = df.loc[:,'SunAzimuth (deg)']*-1
df.loc[:,'Distance (km)'] = infile.loc[i, 'Distance (km)']
df.loc[:,'AirPress (Pa)'] = df.loc[:,'AirPress (hPa)']*100
df.set_index('DateTime',inplace=True)
df = df.tz_localize('UTC').loc[start_date:end_date,:]

WeatherTP = TP.TecplotData()
WeatherTP.zone = TP.TPHeaderZone()
WeatherTP.data = df[['Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
 'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)', 'WindDir (deg)']].copy()



for i in trange(1,infile.shape[0]):
    df = pd.read_csv(infile.loc[i, 'File'])
    df.loc[:, ['PeriodEnd', 'PeriodStart']] = df.loc[:, ['PeriodEnd', 'PeriodStart']].astype(np.datetime64)
    # take the centre of the measurement period as the data record time.
    # df.loc[:, 'DateTime'] = df['PeriodStart'] + (df['PeriodEnd'].to_numpy() - df['PeriodStart'].to_numpy())/2
    df.loc[:, 'DateTime'] = df['PeriodStart']
    df.drop(columns=['PeriodEnd', 'PeriodStart'], inplace=True)
    df.rename(columns={'Dni': 'DirectSun (W/m2)', 'Dhi': 'DiffuseSun (W/m2)', 'AirTemp': 'AirTemp (degC)',
                       'SurfacePressure': 'AirPress (hPa)', 'WindSpeed10m': '10m WindVel (m/s)',
                       'WindDirection10m': 'WindDir (deg)',
                       'Azimuth': 'SunAzimuth (deg)'}, inplace=True)
    df = convert_wind(df)
    df.loc[:, 'SunElevation (deg)'] = 90 - df['Zenith']
    df.loc[:, 'SunAzimuth (deg)'] = df.loc[:, 'SunAzimuth (deg)'] * -1
    df.loc[:, 'Distance (km)'] = infile.loc[i, 'Distance (km)']
    df.loc[:, 'AirPress (Pa)'] = df.loc[:, 'AirPress (hPa)'] * 100
    df.set_index('DateTime', inplace=True)
    df = df.tz_localize('UTC').loc[start_date:end_date, :].copy()

    df=df[['Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
                         'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)',
                         'WindDir (deg)']].copy()

    # WeatherTP.data = pd.DataFrame.append(WeatherTP.data, df) # depreciated
    WeatherTP.data = pd.concat([WeatherTP.data, df])



WeatherTP.data.sort_values(by=['Distance (km)', 'DateTime'], inplace=True)
WeatherTP.data = WeatherTP.data.tz_convert(tz)
WeatherTP.data = _makedatetimecol(WeatherTP.data)
WeatherTP.data.loc[:,'Time (HHMM)'] = WeatherTP.data.loc[:,'Time (HHMM)'].astype(str).str[:-1]+str(int(np.mean(WeatherTP.data.loc[:,'Time (HHMM)'].astype(str).str[-1].astype(int))))
WeatherTP.data.reset_index(inplace=True)
WeatherTP.data.drop(columns = 'DateTime',inplace=True)
WeatherTP.zone.nj = WeatherTP.data.loc[:, 'Distance (km)'].nunique()
WeatherTP.zone.ni = WeatherTP.data.iloc[:, 0].count() / WeatherTP.zone.nj


WeatherTP.data = WeatherTP.data[['Day', 'Time (HHMM)', 'Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
 'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)', 'WindDir (deg)']]
WeatherTP.write_tecplot('Weather-SolCast-temp.dat')

