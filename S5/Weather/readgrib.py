"""
Create SolarSim weather file from era5-land grib files.

The core functionality of reading era5 grib files are here, but do note that this is not tested extensively.
Solar irradiance were not in direct and diffuse radiation, so until there is a good way to convert them to direct and
diffuse irradiance it might only be useful for generating EV weather files where solar irradiance data is not needed.

See Also:
    S5.Weather.solcast_historic for historic data with direct and diffuse irradiation.
"""
import os
import warnings
import datetime
from typing import Union
import xarray as xr
import pandas as pd
import numpy as np
from pvlib import solarposition
import pytz.tzinfo
from tqdm import trange
import S5.Tecplot as TP
from S5.Weather import convert_wind


def era5_spot(dataset: xr.Dataset, start_date: datetime.datetime = None, end_date: datetime.datetime = None,
              latitude: float = 54.766776, longitude: float = 358.430261,
              elevation: float = 0, distance: float = 0):
    """Extract data from era5 grib file for a single spot in space.

    Wind direction, wind velocity, temperature, and pressure are extracted from the grib file.
    The azimuth and elevation are calculated using pvlib.solarposition.

    Args:
        dataset: xarray dataset with the grib file opened.
        start_date: Start date and time with timezone.
        end_date: End date and time with timezone.
        latitude: Latitude of the location in decimal degrees.
        longitude: Longitude of the location in decimal degrees
        elevation: Elevation of the spot in meters
        distance: Distance along the route.

    Returns:
        A pandas dataframe with the weather data.

    Raises:
        IndexError: When the start or end date are outside of the available data in the grib file
    """
    if start_date.tzinfo is None:
        print('TimeZone info not specified, using "Australia/Darwin"')
        tz = pytz.timezone('Australia/Darwin')
        start_date.replace(tzinfo=tz)
        end_date.replace(tzinfo=tz)
    elif start_date.tzinfo != end_date.tzinfo:
        warnings.warn('Starting and ending time zone mismatch, using starting timezone as output timezone.')
    tz = start_date.tzinfo

    # convert timezone to UTC (era5 default)
    start_date = start_date.astimezone(pytz.timezone('UTC'))
    end_date = end_date.astimezone(pytz.timezone('UTC'))

    # check requested time period is valid
    if np.datetime64(start_date.strftime("%Y-%m-%dT%H:00")) not in dataset.valid_time.data:
        raise IndexError("start date out of range of grib file")
    if np.datetime64(end_date.strftime("%Y-%m-%dT%H:00")) not in dataset.valid_time.data:
        raise IndexError("end date out of range of grib file")

    df = extract_df(dataset, latitude, longitude, start_date, end_date)

    # reshape the dataframe now...
    df.reset_index(inplace=True)
    df.set_index('valid_time', inplace=True)
    df = df.tz_localize('UTC')
    df.drop(['time', 'step'], axis=1, inplace=True)
    df.index.name = 'DateTime'

    """
    Extract from era5 documentation:
    https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation#heading-Table2streamopermnthmodalevtypesfcsurfaceparametersinstantaneous
        u10 and v10 are in m/s
        u10 is towards the east, v10 is towards the north
        sp in Pa
        t2m in K
        ssr: Surface net solar radiation (J/m2), 'surface_net_downward_shortwave_flux'
        This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a horizontal
        plane at the surface of the Earth (both direct and diffuse) minus the amount reflected by the Earth's surface
        (which is governed by the albedo).
        ssrd: Surface solar radiation downwards (J/m2), 'surface_downwelling_shortwave_flux_in_air'
        ssr but does not minus the amount reflected by the Earth's surface.
    """

    # TODO: replace this with one that checks all data are not available.
    # TODO: if solar is False then it is fine to not have SSR at all.
    # if one of the variable have no data at all then return None
    if df.isna().sum().max() == df.shape[0]:
        return None

    weather = pd.DataFrame(index=df.index)
    weather["Distance (km)"] = distance

    df = _calculate_wind(df)
    weather[["10m WindVel (m/s)", "WindVel (m/s)", "WindDir (deg)"]] = df[
        ["10m WindVel (m/s)", "WindVel (m/s)", "WindDir (deg)"]]
    weather.loc[:, "AirPress (Pa)"] = df['sp']
    weather.loc[:, "AirTemp (degC)"] = df['t2m'] - 273.15  # convert from k to degC

    solpos = solarposition.get_solarposition(weather.index, latitude, longitude, elevation)
    solpos.loc[:, 'azimuth'] = solpos['azimuth'].apply(lambda x: x if x < 180 else x - 360)
    weather.loc[:, "SunAzimuth (deg)"] = solpos['azimuth']
    weather.loc[:, "SunElevation (deg)"] = solpos['apparent_elevation']

    # convert cumulative sum to hourly total
    cum_ssr = df['ssr'].to_numpy()
    SSR = cumulative_ssr_to_hourly(cum_ssr)
    weather['ssr'] = SSR

    ssr_to_direct_and_diffuse(weather)

    # TODO: This is to make sure the grid is fully rectangular, potential improvements can be done in the future by
    #  interpolate missing points instead of dropping them so we don't lose too many points.
    weather.dropna(inplace=True)

    weather = weather.tz_convert(tz)
    weather = weather[start_date:end_date]

    return weather


def _calculate_wind(df: pd.DataFrame) -> pd.DataFrame:
    """ Private function to convert the 10m u v component of wind to direction and velocity

    According to era5 documentation, u10 is towards the east, v10 is towards the north, both in m/s at 10m.
    WindDir is the direction the wind is coming from.

    Args:
        df: Pandas Dataframe with the columns 'v10' and 'u10'.

    Returns:
        Pandas Dataframe with columns "10m WindVel (m/s)", "WindVel (m/s)", "WindDir (deg)".
    """
    df.loc[:, "10m WindVel (m/s)"] = (df['u10'] ** 2 + df['v10'] ** 2) ** 0.5
    df.loc[:, "WindDir (deg)"] = np.mod(np.rad2deg(-np.arctan2(df['v10'], -df['u10'])) + 90, 360)
    df.loc[:, "WindVel (m/s)"] = convert_wind(df.loc[:, '10m WindVel (m/s)'])
    return df


def extract_df(ds: xr.Dataset, latitude: float, longitude: float, start_date: datetime.datetime,
               end_date: datetime.datetime) -> pd.DataFrame:  # pragma: no cover
    """ Extract subset of data from grib file through xarray as a pandas dataframe.

    Args:
        ds: xarray dataset of the grib file.
        latitude: Latitude.
        longitude: Longitude.
        start_date: Start date of the period to be extracted in UTC.
        end_date: End date of the period to be extracted in UTC.

    Returns:
        pandas dataframe that contains the raw extracted data.
    """
    # extracted this as a method to help with mocking, excluded from test coverage as this uses exclusively xarray APIs.
    # need to do ds.sel twice because time slicing does not work with method.
    df = ds.sel(latitude=latitude, longitude=longitude, method='nearest').sel(
        time=slice(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))).get(ds.keys()).to_dataframe()
    return df


def ssr_to_direct_and_diffuse(weather: pd.DataFrame) -> pd.DataFrame:
    """Temporary implementation to convert surface net solar radiation (ssr) to direct and diffuse.

    The fact is it is just not the same thing, this may give you some somewhat realistic data to play with but you
    should really use a different datasource.

    Args:
        weather: dataframe with columns "ssr", and "SunElevation(deg)"

    Returns:
        This function modifies the original dataframe but also returns a copy of the modified dataframe.
    """
    weather.loc[:, "DirectSun_uncorrected (W/m2)"] = weather["ssr"] / 3600
    # weather.loc[:, "correction"] = abs(np.sin(np.deg2rad(weather.loc[:, "SunElevation (deg)"])))
    # weather.loc[:, "DirectSun_corrected (W/m2)"] = weather.loc[:, "DirectSun_uncorrected (W/m2)"] / \
    #                                      weather.loc[:, "correction"]
    weather.loc[:, "DirectSun (W/m2)"] = weather.loc[:, "DirectSun_uncorrected (W/m2)"]
    weather.loc[:, "DiffuseSun (W/m2)"] = 0
    return weather.copy()


def cumulative_ssr_to_hourly(cumulative_ssr: np.ndarray) -> np.ndarray:
    """Converts the cumulative surface net solar radiation (ssr) to the hourly ssr.

    Args:
        cumulative_ssr: Array of cumulative ssr.

    Returns:
        Numpy array of hourly ssr.
    """
    # identify the point to split by the fact that the last sample point should only be larger than the next one when it
    #  is a new day it was reset to 0.
    is_new_day = cumulative_ssr[:-1] > cumulative_ssr[1:]
    daily = np.split(cumulative_ssr, np.argwhere(is_new_day).flatten() + 1)
    hourly_ssr = np.array([])
    for day in daily:
        converted_day = day - np.insert(day, 0, 0)[:-1]
        hourly_ssr = np.concatenate([hourly_ssr, converted_day])
    return hourly_ssr


def from_era5(stationfile: Union[str, os.PathLike], gribfile: Union[str, os.PathLike], start_date: datetime.datetime,
              end_date: datetime.datetime, outfile: Union[str, os.PathLike] = "Weather-era5byS5.dat",
              Solar: bool = True) -> None:
    """Create solarsim weather file from era5 grib files.

    Args:
        stationfile: File path to .dat file with station details.
        gribfile: File path to grib file to be used downloaded from era5
        start_date: Start date and time including timezone.
        end_date: End date and time including timezone.
        outfile: Name of the output file.
        Solar: False to disable irradiance output (all 0).

    Returns:
        None, SolarSim weather file created at outfile.

    Examples:
        >>> from_era5('Station.dat', 'ERA5-Land.grib', datetime.datetime(2020, 9, 14, 0, 0), datetime.datetime(2020, 9, 15, 0, 0))
    """
    debug = False  # TODO: better way to do this <--
    WeatherTP = TP.SSWeather()

    station = TP.TecplotData(stationfile)
    for col_name in ['Distance (km)', 'Latitude', 'Longitude', 'Altitude (m)']:
        if col_name not in station.data.columns:
            raise IndexError(f'{col_name} is missing from Road file {station}')
    # assert dtype

    ds = xr.open_dataset(gribfile, engine='cfgrib')
    for i in trange(station.zone.ni):
        latitude = station.data.loc[i, 'Latitude']
        longitude = station.data.loc[i, 'Longitude']
        elevation = station.data.loc[i, 'Altitude (m)']
        distance = station.data.loc[i, 'Distance (km)']
        weather = era5_spot(ds, start_date=start_date, end_date=end_date, latitude=latitude, longitude=longitude,
                            elevation=elevation, distance=distance)
        if weather is None:
            warnings.warn(f"Spot weather at row {i}, location {latitude},{longitude} received NaN from Grib file.")
        else:
            WeatherTP.data = pd.concat([WeatherTP.data, weather], axis='index')
    ds.close()

    if not Solar:
        print('Disabling solar output.')
        WeatherTP.data.loc[:, ["DirectSun (W/m2)", "DiffuseSun (W/m2)"]] = 0

    if WeatherTP.data['Distance (km)'].min() != 0:
        print('Data missing for starting point, backfilling from first point in space.')
        Start = WeatherTP.data[WeatherTP.data['Distance (km)'] == WeatherTP.data['Distance (km)'].min()]
        Start.loc[:, 'Distance (km)'] = 0
        WeatherTP.data = pd.concat([Start, WeatherTP.data], axis='index')

    WeatherTP.data.sort_values(by=['Distance (km)', 'DateTime'], inplace=True)
    WeatherTP.add_day_time_cols()
    WeatherTP.zone = TP.TPHeaderZone()
    WeatherTP.zone.nj = WeatherTP.data.loc[:, 'Distance (km)'].nunique()
    WeatherTP.zone.ni = WeatherTP.data.iloc[:, 0].count() / WeatherTP.zone.nj
    WeatherTP.zone.zonetitle = "S5Weather"
    WeatherTP.title = "Weather file generated by S5.from_era5"

    # TODO: use __debug__ instad?
    if not debug:
        WeatherTP.data = WeatherTP.data.loc[:,
                         ["Day", "Time (HHMM)", "Distance (km)", "DirectSun (W/m2)", "DiffuseSun (W/m2)",
                          "SunAzimuth (deg)",
                          "SunElevation (deg)", "AirTemp (degC)", "AirPress (Pa)", "WindVel (m/s)", "WindDir (deg)"]]

    WeatherTP.check_rectangular()
    WeatherTP.write_tecplot(outfile)
    print(f'Weather file {outfile} created.')


if __name__ == '__main__':  # pragma: no cover
    # stationfile = 'E:\solar_car_race_strategy\S5\S5\Weather\Station.dat'
    STATION_FILE = r'E:\solar_car_race_strategy\SolCastHistoric\Road-SolCast-10km.dat'
    GRIB_FILE = r'E:\solar_car_race_strategy\S5\ExampleDataSource\ERA5-Land-test.grib'
    TZ = pytz.timezone('Australia/Darwin')
    START_DATE = datetime.datetime(2020, 9, 14, 0, 0, tzinfo=TZ)
    END_DATE = datetime.datetime(2020, 9, 15, 23, 0, tzinfo=TZ)
    start = datetime.datetime.now()
    from_era5(STATION_FILE, GRIB_FILE, START_DATE, END_DATE, outfile=r'E:\Weather-era5byS5-tmp.dat',
              Solar=True)
    duration = datetime.datetime.now() - start
    print(f'Time taken: {duration}')
