"""
TODO: doctrings
TODO: type hints
TODO: tests
"""
import warnings
import datetime
import xarray as xr

# TODO: move to S5.__init__ ? it is supressde everytime S5 is imported?
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import numpy as np
from pvlib import solarposition
import pytz.tzinfo
from tqdm import trange
import S5.Tecplot as TP
from S5.Weather import convert_wind


def era5_spot(dataset, start_date=None, end_date=None, tz=None, latitude=54.766776, longitude=358.430261,
              elevation=0, distance=0):
    # specific to era5 data.
    # start and end date are datetime objs
    # assume grib file downloaded somewhere
    ds = dataset
    forecast_time = ds.time.data
    # TODO: need hour and round off to nearest hour.

    # check requested time period is valid
    if np.datetime64(start_date.strftime("%Y-%m-%dT%H:00")) not in ds.valid_time.data:
        raise IndexError("start date out of range of grib file")
    if np.datetime64(end_date.strftime("%Y-%m-%dT%H:00")) not in ds.valid_time.data:
        raise IndexError("end date out of range of grib file")

    if start_date.tzinfo is None or end_date.tzinfo is None:
        print('TimeZone info not specified, using "Australia/Darwin"')
        tz = pytz.timezone('Australia/Darwin')
        start_date.replace(tzinfo=tz)
        end_date.replace(tzinfo=tz)
    else:
        tz = start_date.tzinfo

    # convert timezone to UTC (era5 default)
    start_date = start_date.astimezone(pytz.timezone('UTC'))
    end_date = end_date.astimezone(pytz.timezone('UTC'))
    step = np.datetime64(start_date.strftime("%Y%m%d%H%M")) - forecast_time

    # need to do sel twice because slice does not like method
    df = ds.sel(latitude=latitude, longitude=longitude, method='nearest').sel(
        time=slice(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))).get(ds.keys()).to_dataframe()

    # reshape the dataframe now...
    df.reset_index(inplace=True)
    df.set_index('valid_time', inplace=True)  # TODO: timezone??
    df.drop(['time', 'step'], axis=1, inplace=True)
    df.index.name = 'DateTime'

    # u10 and v10 are already in ms-1
    # u10 is eastward +ve, v10 is northward +ve
    # sp in Pa
    # t2m in K
    # ssr: Surface net solar radiation (J/m2), 'surface_net_downward_shortwave_flux'
    # This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a horizontal
    # plane at the surface of the Earth (both direct and diffuse) minus the amount reflected by the Earth's surface
    # (which is governed by the albedo).

    # ssrd: Surface solar radiation downwards (J/m2), 'surface_downwelling_shortwave_flux_in_air'
    # ssr but does not minus the amount reflected by the Earth's surface.

    # TODO: replace this with one that checks all data are not available.
    # TODO: if solar is False then it is fine to not have SSR at all.
    # if one of the variable have no data at all then return None
    if df.isna().sum().max() == df.shape[0]:
        return None

    weather = df[[]].copy()
    # weather = pd.DataFrame(index = df.index)
    weather.loc[:, "10m WindVel (m/s)"] = (df['u10'] ** 2 + df['v10'] ** 2) ** 0.5
    weather.loc[:, "WindDir (deg)"] = np.mod(np.rad2deg(-np.arctan2(df['v10'], -df['u10'])) + 90, 360)
    # todo: check if wind dir is correct,"WindDir (deg)" is direction it's coming from?
    weather.loc[:, "AirPress (Pa)"] = df['sp']
    weather.loc[:, "AirTemp (degC)"] = df['t2m'] - 273.15  # convert from k to degC

    solpos = solarposition.get_solarposition(weather.index, latitude, longitude, elevation)
    solpos.loc[:, 'azimuth'] = solpos['azimuth'].apply(lambda x: x if x < 180 else x - 360)
    weather.loc[:, "SunAzimuth (deg)"] = solpos['azimuth']
    weather.loc[:, "SunElevation (deg)"] = solpos['apparent_elevation']

    # convert cumulative sum to hourly total
    ssrnp = df['ssr'].to_numpy()
    SSR = cumulative_SSR_to_hourly(start_date, end_date, ssrnp)

    ssr_to_direct_and_diffuse(SSR, weather)

    weather["Distance (km)"] = distance
    # TODO: do we want this? need to make sure to grid is fully rectangular. Should interpolate instaed?
    weather.dropna(inplace=True)
    weather = weather.tz_localize('UTC')
    weather = weather.tz_convert(tz)
    weather = weather[start_date:end_date]

    # put it in a SSWeather object to generate the day and time columns.
    WeatherTP = TP.SSWeather()
    WeatherTP.data = weather
    WeatherTP.add_day_time_cols()
    weather = WeatherTP.data

    weather.loc[:, 'WindVel (m/s)'] = convert_wind(weather.loc[:, '10m WindVel (m/s)'])

    return weather


def ssr_to_direct_and_diffuse(SSR, weather):
    # TODO: Refactor to work on np array
    weather.loc[:, "DirectSun_uncorrected (W/m2)"] = SSR / 3600
    weather.loc[:, "correction"] = abs(np.sin(np.deg2rad(weather.loc[:, "SunElevation (deg)"])))
    weather.loc[:, "DirectSun_corrected (W/m2)"] = weather.loc[:, "DirectSun_uncorrected (W/m2)"] / \
                                                   weather.loc[:, "correction"]
    # todo: need to convert to surface normal to sun.
    weather.loc[:, "DiffuseSun (W/m2)"] = 0


def cumulative_SSR_to_hourly(start_date, end_date, cumulative_ssr):
    # TODO: decide function name

    # TODO: what if the number of points per day are different?
    daily = np.split(cumulative_ssr, (end_date.date() - start_date.date()).days + 1)
    hourly_ssr = np.array([])
    for day in daily:
        converted_day = (day - np.insert(day, 0, 0)[:-1])
        hourly_ssr = np.concatenate([hourly_ssr, converted_day])
    return hourly_ssr


def from_era5(stationfile, gribfile, start_date, end_date, outfile="Weather-era5byS5.dat", Solar=True):
    """
    create solarsim weather file from era5 grib files
    :param stationfile: file path to .dat file with station details.0
    :param gribfile: file path to grib file to be used
    :param start_date: datetime object
    :param end_date: datetime object
    :param outfile: file path and name to create output file
    :param Solar: bool, False to disable irradiance output (all 0)
    :return: None, weather file will be created and stored at location specified by outfile

    >>> from_era5('Weather/Station.dat', 'ExampleDataSource/ERA5-Land-test.grib', datetime.datetime(2020, 9, 14, 0, 0), datetime.datetime(2020, 9, 14, 0, 0))
    """
    debug = False
    WeatherTP = TP.SSWeather()

    station = TP.TecplotData()
    station.readfile(stationfile)
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
            WeatherTP.data = pd.DataFrame.append(WeatherTP.data, weather)
    ds.close()

    if not Solar:
        print('disabeling solar output')
        WeatherTP.data.loc[:, ["DirectSun (W/m2)", "DiffuseSun (W/m2)"]] = 0

    if WeatherTP.data['Distance (km)'].min() != 0:
        print('Data missing for starting point, backfilling from first point in space.')
        Start = WeatherTP.data[WeatherTP.data['Distance (km)'] == WeatherTP.data['Distance (km)'].min()]
        Start.loc[:, 'Distance (km)'] = 0
        WeatherTP.data = pd.DataFrame.append(Start, WeatherTP.data)

    WeatherTP.data.sort_values(by=['Distance (km)', 'DateTime'], inplace=True)
    # WeatherTP.data.drop(columns='DateTime', inplace=True)
    WeatherTP.data.loc[:, 'Time (HHMM)'] = WeatherTP.data.loc[:, 'Time (HHMM)'].astype('str').str.pad(width=4,
                                                                                                      side='left',
                                                                                                      fillchar='0')
    WeatherTP.zone = TP.TPHeaderZone()
    WeatherTP.zone.nj = WeatherTP.data.loc[:, 'Distance (km)'].nunique()
    WeatherTP.zone.ni = WeatherTP.data.iloc[:, 0].count() / WeatherTP.zone.nj
    WeatherTP.zone.zonetitle = "S5Weather"
    WeatherTP.title = "Weather file generated by S5.from_era5"

    if not debug:
        WeatherTP.data.rename(columns={"DirectSun_uncorrected (W/m2)": "DirectSun (W/m2)"}, inplace=True)
        WeatherTP.data = WeatherTP.data.loc[:,
                         ["Day", "Time (HHMM)", "Distance (km)", "DirectSun (W/m2)", "DiffuseSun (W/m2)",
                          "SunAzimuth (deg)",
                          "SunElevation (deg)", "AirTemp (degC)", "AirPress (Pa)", "WindVel (m/s)", "WindDir (deg)"]]
    WeatherTP.check_rectangular()
    WeatherTP.write_tecplot(outfile)
    print(f'Weather file {outfile} created.')


if __name__ == '__main__':
    # stationfile = 'E:\solar_car_race_strategy\S5\S5\Weather\Station.dat'
    STATION_FILE = r'E:\solar_car_race_strategy\SolCastHistoric\Road-SolCast-10km.dat'
    GRIB_FILE = 'E:\solar_car_race_strategy\S5\ExampleDataSource\ERA5-Land-test.grib'
    TZ = pytz.timezone('Australia/Darwin')
    START_DATE = datetime.datetime(2020, 9, 14, 0, 0, tzinfo=TZ)
    END_DATE = datetime.datetime(2020, 9, 15, 23, 0, tzinfo=TZ)
    import datetime

    start = datetime.datetime.now()
    from_era5(STATION_FILE, GRIB_FILE, START_DATE, END_DATE, outfile='E:\Weather-era5byS5-tmp.dat',
              Solar=True)
    duration = datetime.datetime.now() - start
    print(f'Time taken: {duration}')
