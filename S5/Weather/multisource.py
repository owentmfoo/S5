
import pandas as pd
from pvlib import solarposition
from S5.Weather import Solar
from S5.Weather import Atm
from S5.config import data_source
from S5 import Tecplot

def _makedatetimecol(df):
    df.loc[:, 'Day'] = df.index.day - df.index.day[0] + 1  # convert to day of race, 1 indexed
    df.loc[:, 'Time (HHMM)'] = df.index.strftime("%H%M")
    return df


def compilesiteweather(solar_sourceFile=data_source + '\\sl_014015_2019_10.txt', solar_source="AUSBoM",
                       weather_sourceFile=data_source + '\\Darwin Airport.csv', weather_source='WOW',
                       dist=0, elevation=0, sol_startDate="13Oct2019", sol_endDate="22Oct2019",
                       weather_startDate="13Oct2019", weather_endDate="22Oct2019", sol_tz=None, weather_tz=None,
                       latitude=0, longitude=0):
    """
    Create weather dataframe for a single spot
    :param solar_sourceFile: file path to input file
    :param solar_source: type if input
    :param weather_sourceFile:
    :param weather_source:
    :param sol_startDate: either string in format '13Oct2019' or '093022Sep2021', or datetime object
    :param sol_endDate:
    :param weather_startDate:
    :param weather_endDate:
    :param sol_tz:
    :param weather_tz:
    :param dist:
    :param elevation:
    :param latitude:
    :param longitude:
    :return:
    """
    # don't need to include elevation as it make parctically no difference (on the magnitude of 1e-3 for apparent zenith,
    # 1e-9 for apparent elevation)
    if ((pd.to_datetime(sol_endDate) - pd.to_datetime(sol_startDate)) != (
            pd.to_datetime(weather_endDate) - pd.to_datetime(weather_startDate))):
        raise Exception('Input error, solar and weather duration mismatch!')

    # TODO: need to remove start from 0500 for EV ranging?
    def parse_date(date):
        """
        private function to parse input date string
        """
        if isinstance(date, str):
            try:
                date = datetime.datetime.strptime(date, "%d%b%Y")
            except ValueError:
                pass
            try:
                date = datetime.datetime.strptime(date, "%m%H%d%b%Y")
            except ValueError:
                print(
                    "incorrect date format.\nFormat should be `ddmmmyyyy`.\nFor example '13Oct2019' or '093022Sep2021'")
        else:
            pass
        return date

    sol_startDate = "05:00 " + sol_startDate
    weather_startDate = "05:00 " + weather_startDate
    sol_endDate = "05:00 " + sol_endDate
    wowendtDate = "05:00 " + weather_endDate

    solar_df = Solar.get_data(solar_sourceFile, source=solar_source, start_date=sol_startDate,
                             end_date=sol_endDate, tz=sol_tz).loc[:, ['DirectSun (W/m2)', 'DiffuseSun (W/m2)']]
    assert solar_df.index.tz is not None, "Solar timezone missing from import method"
    atm_df = Atm.get_data(weather_sourceFile, source=weather_source, start_date=weather_startDate,
                          end_date=wowendtDate, tz=weather_tz)
    assert atm_df.index.tz is not None, "Sun timezone missing from import method"
    # solpos require timezone localized index
    solpos = solarposition.get_solarposition(solar_df.index, latitude, longitude, elevation)
    # convert to SS convention for Azimuth (-180 to180)
    solpos['azimuth'] = solpos['azimuth'].apply(lambda x: x if x < 180 else x - 360)

    # merge the different data

    # TODO: deal with adding data from different time. (but also keep default some period)

    solar_df = _makedatetimecol(solar_df.join(solpos[['azimuth', 'apparent_elevation']]))
    atm_df = _makedatetimecol(
        atm_df.loc[:, ["AirTemp (degC)", "AirPress (Pa)", "WindVel (m/s)", "WindDir (deg)"]])
    weather = solar_df.merge(atm_df, left_on=['Day', 'Time (HHMM)'], right_on=['Day', 'Time (HHMM)'])

    weather.columns = ["DirectSun (W/m2)", "DiffuseSun (W/m2)", "SunAzimuth (deg)",
                       "SunElevation (deg)", 'Day', 'Time (HHMM)', "AirTemp (degC)", "AirPress (Pa)", "WindVel (m/s)",
                       "WindDir (deg)"]

    # weather.fillna(value=0, inplace=True)  # only NaN should be WOW data before and after 0050 and 2350

    weather['Distance (km)'] = dist
    # reorder the columns
    weather = weather.loc[:,
              ["Day", "Time (HHMM)", "Distance (km)", "DirectSun (W/m2)", "DiffuseSun (W/m2)", "SunAzimuth (deg)",
               "SunElevation (deg)", "AirTemp (degC)", "AirPress (Pa)", "WindVel (m/s)", "WindDir (deg)"]]
    ''' 
    output format in SS:
    "Day", "Time (HHMM)", "Distance (km)", "DirectSun (W/m2)", "DiffuseSun (W/m2)", "SunAzimuth (deg)", 
    "SunElevation (deg)", "AirTemp (degC)", "AirPress (Pa)", "WindVel (m/s)", "WindDir (deg)"
    '''

    return weather


def comb_existing(input_dict):
    """INCOMPLETE. combine columns from differnt existing weather file, assuming same frequency and time period."""
    # TODO: check freq and interpolate if needed
    # TODO: check how bad is interpolating sun pos
    #input_dict: dict of input file and column to take
    # {'Weather_1.dat':["DirectSun (W/m2)", "DiffuseSun (W/m2)"],'Weather_2.dat':["WindVel (m/s)", "WindDir (deg)"]}
    #initialise output tecplot data
    output_tp = Tecplot.TecplotData()
    for key,val in input_dict.items():
        input_i = Tecplot.TecplotData()
        input_i.readfile(key)
        input_i.addtimestamp()
        output_tp.data.loc[:,val] = input_i.data.loc[:,val]
    output_tp.data.loc[:,["Day","Time (HHMM)"]] = input_i.data.loc[:,["Day","Time (HHMM)"]]

    return output_tp.data




if __name__ == "__main__":
    # Darwin = compilesiteweather(dist=0, solar_sourceFile=data_source+'\sl_014015_2019_10.txt',
    #                              weather_sourceFile=data_source+'\Darwin Airport.csv')
    # Darwin2 = compilesiteweather(solar_sourceFile=data_source + '\\SolarExample.csv', solar_source='csv',
    #                              sol_tz='Australia/Darwin',
    #                              weather_sourceFile=data_source + '\\WindExample.csv', weather_source='csv',
    #                              weather_tz='Australia/Darwin',
    #                              dist=0)

    test = comb_existing({'Weather-era5byS5.dat':["DirectSun (W/m2)", "DiffuseSun (W/m2)"],'Weather-test.dat':["WindVel (m/s)", "WindDir (deg)"]})
# .dat file for multilocation input.
