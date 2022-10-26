"""Atmopsheric related weather function.
WindVel, WindDir, AirPress, AirTemp
WIP 20220609
"""
import math
import numpy
import pandas as pd
import warnings
from S5.config import data_source


# import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def convert_wind(df):
    """
    convert wind velocity to solar car level
    take in dataframe with column '10m WindVel (m/s)'
    return dataframe with column 'WindVel (m/s)' converted to 1 m height assuming
    open terrain with surface roughness of z0 = 0.01
    """
    zcar = 1
    z0 = 0.01
    zh = 0
    df.loc[:,'WindVel (m/s)'] = df.loc[:,'10m WindVel (m/s)']* numpy.log((zcar-zh)/z0)/numpy.log((10-zh)/z0)
    return df

"""WIP from here on"""

def get_data(sourcefile, source='WOW', tz=None, **kwargs) -> pd.DataFrame:
    """get solar data from different sources
    'WOW': UK Met Office Weather Observation Website
    'csv': from csv
    'Datahub':
    """
    if source == 'WOW':
        return from_WOW(sourcefile, tz=tz, **kwargs)
    if source == 'csv':
        return from_csv(sourcefile)


def from_csv(sourcefile, day='Day', time='Time (HHMM)', start_day='19990716') -> pd.DataFrame:
    """
    Get wind, pressure and temperature  data from a csv with header ['Day', 'Time (HHMM)'...],
    additional columns permitted but will not be used.
    :param sourcefile: file path to csv
    :param day: Column header for day column (default 'Day')
    :param time: Column header for time column (default 'Time (HHMM)')
    :param start_day: day of day one of the race
    :param tz: timezone of start day
    :return: pandas dataframe
    """
    #TODO: assert timezone in start_day?

    atm_tp = Tecplot.TecplotData()
    atm_tp.data = pd.read_csv(sourcefile)
    atm_tp.data = atm_tp.data.loc[:, ['Day', 'Time (HHMM)', 'AirTemp (degC)', 'AirPress (Pa)',
                                      'WindVel (m/s)', 'WindDir (deg)']]
    atm_tp.addtimestamp(day=day, time=time, startday=start_day)
    atm_tp.data.set_index('DateTime', inplace=True)
    if tz is None:
        warnings.warn("TimeZone in Sun.from_csv not specified. Using UTC as import timezone.")
        tz = 'UTC'
    atm_tp.data = atm_tp.data.tz_localize(tz)
    return atm_tp.data


def from_WOW(sourcefile, start_date=None, end_date=None, tz=None) -> pd.DataFrame:
    """
    get weather data from met office WoW
    :param sourcefile:
    :param start_date:
    :param end_date:
    :param tz:
    :return:
    """
    atm = pd.read_csv(sourcefile, header=0, parse_dates=['Report Date / Time'],
                                infer_datetime_format=True)
    Dropcols = ['Id', 'Site Id', 'Longitude', 'Latitude',
                'Wet Bulb', 'Dew Point', 'Concrete Temp.',
                'Grass Temp.', 'Min. Temp. (last 24hr)', 'Max. Temp. (last 24hr)',
                'Soil Temp. (at 10cm)', 'Soil Temp. (at 30cm)', 'Soil Temp. (at 100cm)',
                'Pressure (At Station)', 'Relative Humidity',
                'Rainfall Rate', 'Rainfall Accumulation', 'Snow Depth',
                'Soil Moisture', 'Present Weather', 'Visibility', 'Total Cloud Cover',
                'Sunshine', 'Ground State', 'Day of Thunder', 'Day of Gales',
                'Day of Hail', 'Day of Snow', 'Weather Diary', 'Travel Disruption',
                'Hazards causing Travel Disruption',
                'Property or Infrastructure Damage',
                'Hazards causing Property or Infrastructure Damage',
                'Personal Health and Safety',
                'Hazards causing Personal Health and Safety', 'Utility Disruption',
                'Hazards causing Utility Disruption', 'Service or Business Disruption',
                'Hazards causing Service or Business Disruption',
                'Agriculture Habitat Damage',
                'Hazards causing Agriculture Habitat Damage',
                'Disruption to Camping Events Leisure Activities',
                'Hazards causing Disruption to Camping Events Leisure Activities',
                'v1_Coastal', 'v1_Flood', 'v1_Ice', 'v1_Landslide', 'v1_Lightning',
                'v1_PoorVisibility', 'v1_Snow', 'v1_Wildfire', 'v1_Wind', 'v1_Other']

    atm.drop(Dropcols, axis=1, inplace=True)  # drop columns that are not interested
    atm.columns = ['DateTime', 'AirTemp (degC)', 'AirPress (hPa)',
                             'Sun Speed(kn)', 'WindDir (deg)', 'Sun Gust',
                             'Sun Gust Direction']  # give them more meaningful labels
    atm.set_index('DateTime', inplace=True)
    atm.index = atm.index.tz_localize(tz)  # set the datetime index
    atm.loc[:, 'AirPress (Pa)'] = atm.loc[:, 'AirPress (hPa)'] * 100
    atm.loc[:, 'WindVel (m/s)'] = atm.loc[:, 'Sun Speed(kn)'] * 0.5144  # knots to m/s
    if atm.isna().sum().sum() != 0:
        warnings.warn(f"Missing Values in {sourcefile}, forward filling missing values.")
        print(atm.isna().sum().sum())
        atm.fillna(method='ffill', inplace=True)
    atm = atm.asfreq('min').interpolate(
        method='linear')  # linearly interpolate the points to fill in the gaps
    atm = atm[start_date:end_date]  # select the WSC days only
    # TODO: do something instead of linear interpolation?

    if tz is None:
        warnings.warn("TimeZone in Sun.from_WOW not specified. Using UTC as import timezone.")
        tz = 'UTC'
    elif tz != "UTC":
        warnings.warn("TimeZone in Sun.from_WOW should be in UTC (not BST), please check before proceeding.")
    atm = atm.tz_localize(tz=tz)

    return atm[["AirTemp (degC)", "AirPress (Pa)", "WindVel (m/s)", "WindDir (deg)"]]




# Index(['AirTemp (degC)', 'AirPress (hPa)', 'Sun Speed(kn)', 'Sun Direction',
#        'Sun Gust', 'Sun Gust Direction', 'AirPress (Pa)', 'WindVel (m/s)'],
#       dtype='object')
if __name__ == "__main__":
    # Darwin = compilesiteweather(dist=0, solar_sourceFile=data_source+'\sl_014015_2019_10.txt',
    #                             weather_sourceFile=data_source+'\Darwin Airport.csv')
    # wind = fromWOW(data_source+'\Darwin Airport.csv',startDate="13Oct2019", endDate="22Oct2019",tz='UTC')
    wind = from_csv(data_source + '\WindExample.csv')
