"""Script to compile Weather Files from Solcast.
TODO: actually write this.
Requires the CSVs from SolCast and a "road file" to give the
corresponding race distance. Run the script in the same folder as all the CSVs or change the variable csv_location

The CSVs from SolCast
"""
import os
import re
import datetime
from typing import Union
from os import PathLike
import pandas as pd
import numpy as np
from pvlib import solarposition
import pytz.tzinfo
import S5.Tecplot as TP
from S5.Weather import convert_wind
from tqdm import trange


def main(start_date, end_date, RoadFile, csv_location):
    RoadTP = TP.TecplotData(RoadFile)
    # TODO: check if it got the right columns in the file? i.e. contains distance, lat, lon

    # def add_day_time_cols(df):  # refactored as a method of Tecplot.SSWeather
    #     df.loc[:, 'Day'] = df.index.day - df.index.day[0] + 1  # convert to day of race, 1 indexed
    #     df.loc[:, 'Time (HHMM)'] = df.index.strftime("%H%M")
    #     return df

    # get the list of SolCast csv that are available.
    f = re.compile('.*Solcast.*.csv')
    file = filter(f.match, os.listdir(csv_location))

    # use the lat lon, map the csv file to distance along the route.
    infile = pd.DataFrame(list(file))
    infile.columns = ['File']
    infile.loc[:, ['Latitude', 'Longitude']] = infile['File'].str.extract('(.*)_(.*)_Solcast.*').astype(
        'float64').to_numpy()
    infile = infile.merge(RoadTP.data[['Distance (km)', 'Latitude', 'Longitude']], left_on=['Latitude', 'Longitude'],
                          right_on=['Latitude', 'Longitude'])

    WeatherTP = TP.SSWeather()
    WeatherTP.zone = TP.TPHeaderZone()

    # Read the solcast csv for each spot along the route and add it to the output weather file.
    for i in trange(0, infile.shape[0]):
        csvname = infile.loc[i, 'File']
        distance = infile.loc[i, 'Distance (km)']
        df = read_solcast_csv(csvname, distance, start_date, end_date)
        if i == 0:
            WeatherTP.data = df
        else:
            WeatherTP.data = pd.concat([WeatherTP.data, df])

    WeatherTP.data.sort_values(by=['Distance (km)', 'DateTime'], inplace=True)
    WeatherTP.data = WeatherTP.data.tz_convert(tz)
    WeatherTP.add_day_time_cols()
    WeatherTP.data.loc[:, 'Time (HHMM)'] = WeatherTP.data.loc[:, 'Time (HHMM)'].astype(str).str[:-1] + str(
        int(np.mean(WeatherTP.data.loc[:, 'Time (HHMM)'].astype(str).str[-1].astype(int))))
    WeatherTP.data.reset_index(inplace=True)
    WeatherTP.data.drop(columns='DateTime', inplace=True)
    WeatherTP.zone.nj = WeatherTP.data.loc[:, 'Distance (km)'].nunique()
    WeatherTP.zone.ni = WeatherTP.data.iloc[:, 0].count() / WeatherTP.zone.nj

    WeatherTP.data = WeatherTP.data[
        ['Day', 'Time (HHMM)', 'Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
         'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)', 'WindDir (deg)']]
    WeatherTP.write_tecplot('Weather-SolCast-temp.dat')


def read_solcast_csv(filename: Union[str, PathLike], distance: float, start_date: datetime.datetime,
                     end_date: datetime.datetime):
    """Reads the solcast csv for a single spot.

     Reads the solcast csv that corresponds to a single point along the route, format it a chunk of the weather file
     and return it as a dataframe.

    Args:
        filename: Path to the solcast csv corresponding to this spot.
        distance: Mapped distance along the route.
        start_date: start time in local time with timezone
        end_date: end time in local time with timezone

    Returns: A formatted pandas dataframe with columns ['Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)',
    'SunAzimuth (deg)', 'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)', 'WindDir (deg)']
    """
    df = pd.read_csv(filename)
    df.loc[:, 'Distance (km)'] = distance

    df.loc[:, ['PeriodEnd', 'PeriodStart']] = df.loc[:, ['PeriodEnd', 'PeriodStart']].astype(np.datetime64)
    df.loc[:, 'DateTime'] = df['PeriodStart']
    df.drop(columns=['PeriodEnd', 'PeriodStart'], inplace=True)
    df.rename(columns={'Dni': 'DirectSun (W/m2)', 'Dhi': 'DiffuseSun (W/m2)', 'AirTemp': 'AirTemp (degC)',
                       'SurfacePressure': 'AirPress (hPa)', 'WindSpeed10m': '10m WindVel (m/s)',
                       'WindDirection10m': 'WindDir (deg)',
                       'Azimuth': 'SunAzimuth (deg)'}, inplace=True)
    df.loc[:, 'WindVel (m/s)'] = convert_wind(df.loc[:, '10m WindVel (m/s)'])
    df.loc[:, 'SunElevation (deg)'] = 90 - df['Zenith']
    df.loc[:, 'SunAzimuth (deg)'] = df.loc[:, 'SunAzimuth (deg)'] * -1
    df.loc[:, 'AirPress (Pa)'] = df.loc[:, 'AirPress (hPa)'] * 100
    df.set_index('DateTime', inplace=True)

    # as the csv are in UTC, localize timezone before slicing the portion of data that we want.
    df = df.tz_localize('UTC').loc[start_date:end_date, :].copy()
    df = df[['Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
             'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)',
             'WindDir (deg)']].copy()
    return df


if __name__ == '__main__':  # pragma: no cover
    ROAD_FILE = r'E:\solar_car_race_strategy\SolCastHistoric\Road-SolCast-10km.dat'
    CSV_LOC = '.'
    tz = pytz.timezone('Australia/Darwin')
    START_DATE = datetime.datetime(2019, 10, 13, 0, 0, tzinfo=tz)
    END_DATE = datetime.datetime(2019, 10, 20, 23, 0, tzinfo=tz)
    main(START_DATE, END_DATE, ROAD_FILE, CSV_LOC)
