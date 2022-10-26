import pandas as pd
import warnings
import datetime
from S5 import Tecplot
from S5.config import data_source
import requests

# todo: take in buffers instead of file path

def get_data(sourcefile, source='AUSBoM',start_date=None, end_date=None, tz=None, **kwargs) -> pd.DataFrame:
    """get solar data from different sources
    'AUSBoM': from 1 min irridance data recorded by the Australia Bureau of Meteorology csv.
    'off': disable solar output (all zeros)
    'csv': from csv with header ['Day', 'Time (HHMM)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)']
    """
    if source == 'AUSBoM':
        return AUSBoMSolar(sourcefile, tz=tz, start_date=start_date, end_date=end_date)
    if source == 'off':
        return zeros(tz=tz, start_date=start_date,end_date=end_date)
    if source == "solcast":
        return get_from_solcast(**kwargs)
    if source == "csv":
        return from_csv(sourcefile, tz=None, start_date=start_date)


def zeros(start_date=None, end_date=None, tz=None) -> pd.DataFrame:
    '''
    Create solar data with zero irridance (ignore solar) with 1 min frequency.
    :param start_date: start date
    :param end_date: end date
    :param tz: default Darwin
    :return: pandas dataframe
    '''
    if tz is None:
        warnings.warn("TimeZone in Solar.zeros not specified. Using UTC as import timezone.")
        tz = 'UTC'
    Solar = pd.DataFrame(index=pd.date_range(start=start_date, end=end_date, freq='1min', tz=tz))
    Solar.loc[:, 'Direct'] = 0
    Solar.loc[:, 'Diffuse'] = 0
    return Solar


def AUSBoMSolar(file, start_date=None, end_date=None, tz=None) -> pd.DataFrame:
    """
    Obtain solar data from 1 min irridance data recorded by the Australia Bureau of Meteorology
    :param file: filepath to datafile
    :param start_date:
    :param end_date:
    :return:
    """

    Solar = pd.read_csv(file, skiprows=0, parse_dates=[[2, 3, 4, 5, 6]])
    Solar = Solar.iloc[:, [0, 8, 13]]  # only retain date, direct and diffuse
    Solar.columns = ['DateTime', "DirectSun (W/m2)", "DiffuseSun (W/m2)"]
    # there may be missing data in 'Direct'
    Solar.loc[:, "DirectSun (W/m2)"] = pd.to_numeric(Solar.loc[:, "DirectSun (W/m2)"], errors='coerce')
    Solar.loc[:, "DiffuseSun (W/m2)"] = pd.to_numeric(Solar.loc[:, "DiffuseSun (W/m2)"], errors='coerce')
    Solar.loc[:, 'DateTime'] = pd.to_datetime(Solar.loc[:, 'DateTime'], format='%Y %m %d %H %M')
    if (Solar.isna().sum().sum() != 0):
        warnings.warn(f"Missing Values in {file}, forward filling missing values.")
        Solar.fillna(method='ffill', inplace=True)
    Solar.set_index(['DateTime'], inplace=True)

    # tz should be in local standard time
    if tz is None:
        warnings.warn("TimeZone in Solar.AUSBoMSolar not specified. Using Darwin as import timezone.")
        tz = 'Australia/Darwin'
    Solar = Solar.tz_localize(tz)
    Solar = Solar.loc[start_date:end_date]
    return Solar


def from_csv(sourcefile, day='Day', time='Time (HHMM)', start_date='19990716', tz=None) -> pd.DataFrame:
    """
    Get irradiance data from a csv with header ['Day', 'Time (HHMM)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)'],
    additional columns permitted but will not be used.
    :param sourcefile: file path to csv
    :param day: Column header for day column (default 'Day')
    :param time: Column header for time column (default 'Time (HHMM)')
    :param start_day: day of day one of the race
    :return: pandas dataframe
    """
    SolarTP = Tecplot.TecplotData()
    SolarTP.data = pd.read_csv(sourcefile)
    SolarTP.data = SolarTP.data.loc[:, ['Day', 'Time (HHMM)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)']]
    SolarTP.addtimestamp(day=day, time=time, startday=start_date)
    SolarTP.data.set_index('DateTime', inplace=True)
    if tz is None:
        warnings.warn("TimeZone in Solar.from_csv not specified. Using UTC as import timezone.")
        tz = 'UTC'
    SolarTP.data = SolarTP.data.tz_localize(tz=tz)
    return SolarTP.data


def get_from_solcast(startDate, endDate, latitude=-1.873331, longitude=55.025538):
    # check if there is a quite updated file
    # data retention policy?
    # emulator function?

    return pd.DataFrame()



if __name__ == "__main__":
    solarfile = data_source+"\sl_014015_2019_10.txt"
    solstartDate = "13Oct2019"
    solendDate = "22Oct2019"
    out = AUSBoMSolar(data_source+"\sl_014015_2019_10.txt", start_date="13Oct2019", end_date="22Oct2019")
    out2 = from_csv(data_source+'\SolarExample.csv')

