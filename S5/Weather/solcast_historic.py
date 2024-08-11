"""Script to compile Weather Files from Solcast.

Requires the CSVs from SolCast and a "road file" with columns ['Distance (km)', 'Latitude', 'Longitude'] to maps
the CSVs to distances along the route. The Road file can have extra points but each CSV file have to have a point
specified in the Road file or else a warning will be raised and the row that does not have data in the road file
will be omitted.

The Solcast historic CSVs should be named in the format of {lat}_{lon}_Solcast_{sample_mode}.csv


Examples:
    >>> ROAD_FILE = r'Road-SolCast-10km.dat'
    >>> CSV_LOC = '.'
    >>> tz = pytz.timezone('Australia/Darwin')
    >>> START_DATE = datetime.datetime(2019, 10, 13, 0, 0)
    >>> END_DATE = datetime.datetime(2019, 10, 20, 23, 0)
    >>> START_DATE = tz.localize(START_DATE)
    >>> END_DATE = tz.localize(END_DATE)
    >>> main(START_DATE, END_DATE, ROAD_FILE, CSV_LOC)
"""
import datetime
import os
import re
import warnings
from os import PathLike
from typing import Union, Set, Iterable

import numpy as np
import pandas as pd
import pytz.tzinfo
from tqdm import trange

import S5.Tecplot as TP
from S5.Weather import convert_wind


def main(start_date: datetime.datetime, end_date: datetime.datetime, RoadFile: Union[str, os.PathLike],
         csv_location: [str, os.PathLike], output_file: [str, os.PathLike] = 'Weather-SolCast-temp.dat') -> None:
    r"""Creates a SolarSim weather file from solcast historic CSVs.

    Requires the CSVs from SolCast and a "road file" with columns ['Distance (km)', 'Latitude', 'Longitude'] to maps
    the CSVs to distances along the route. The Road file can have extra points but each CSV file have to have a point
    specified in the Road file or else a warning will be raised and the row that does not have data in the road file
    will be omitted.

    The Solcast historic CSVs should be named in the format of {lat}_{lon}_Solcast_{sample_mode}.csv

    Args:
        start_date: The start date and time for the output file with timezone info.
        end_date: The end date and time for the output file with timezone info.
        RoadFile: Path the the road file used to map the CSVs to distance along the route. Must have the following
            columns: ['Distance (km)', 'Latitude', 'Longitude']
        csv_location: Path to the parent folder that contains all the CSVs, the CSVs can be stored in subfolders in
            this location.
        output_file: Path and name to write the output weather file. Example: 'output\Weather-Solcast-20221217.dat'

    Returns:
        Creates the weather file at the location specified by output_file.
    """

    # Get the list of SolCast CSVs that are available.
    files = get_file_list(csv_location)

    # Use the lat lon to map the CSVs file to distance along the route.
    infile = map_files(RoadFile, files)

    # Initialise output weather Tecplot object.
    WeatherTP = TP.SSWeather()
    WeatherTP.zone = TP.TPHeaderZone()

    # Read the solcast csv for each spot along the route and add it to the output weather file.
    for i in trange(0, infile.shape[0]):
        csvname = infile.loc[i, 'File Name']
        distance = infile.loc[i, 'Distance (km)']
        df = read_solcast_csv(csvname, distance, start_date, end_date)
        if i == 0:
            WeatherTP.data = df
        else:
            WeatherTP.data = pd.concat([WeatherTP.data, df])

    WeatherTP.data.sort_values(by=['Distance (km)', 'DateTime'], inplace=True)
    if start_date.tzinfo != end_date.tzinfo:
        warnings.warn(
            'Starting and ending time zone mismatch, using starting timezone as output timezone.')
    output_timezone = start_date.tzinfo
    WeatherTP.data = WeatherTP.data.tz_convert(output_timezone)
    WeatherTP.add_day_time_cols()

    # TODO: The next line is a temporary solution to make sure the weather file is a fully rectangular grid in space
    #  and time. Measurements are taken at slightly different time at each station.
    #  For example: 3 minute past the hour at Darwin but 6 minute past the hour at Coober Pedy.
    #  !!!This will NOT work if the measurements are not at 10 min intervals.!!!
    WeatherTP.data.loc[:, 'Time (HHMM)'] = WeatherTP.data.loc[:, 'Time (HHMM)'].astype(str).str[:-1] + str(
        int(np.mean(WeatherTP.data.loc[:, 'Time (HHMM)'].astype(str).str[-1].astype(int))))

    WeatherTP.data.reset_index(inplace=True)
    WeatherTP.data.drop(columns='DateTime', inplace=True)
    WeatherTP.zone.nj = WeatherTP.data.loc[:, 'Distance (km)'].nunique()
    WeatherTP.zone.ni = WeatherTP.data.iloc[:, 0].count() / WeatherTP.zone.nj

    WeatherTP.data = WeatherTP.data[
        ['Day', 'Time (HHMM)', 'Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
         'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)', 'WindDir (deg)']]

    WeatherTP.check_rectangular()
    WeatherTP.write_tecplot(output_file)


def map_files(RoadFile: Union[str, os.PathLike], files: Iterable[Union[str, os.PathLike]]) -> pd.DataFrame:
    """ Maps CSVs to distance along the route.

    Using the road file provided, maps the list of CSVs to distance along the route. The Road file can have extra points
    but each CSV file have to have a point specified in the Road file or else a warning will be raised and the row that
    does not have data in the road file will be omitted.

    Args:
        RoadFile: Path the the road file.
        files: List of path to the CSVs.

    Returns:
        A pandas Dataframe with columns ['File Name', 'Latitude', 'Longitude', 'Distance (km)'] with each row
        corresponding to a CSV.

    """
    # Read the Road file and check if it got the right columns.
    RoadTP = TP.TecplotData(RoadFile)
    for col_name in ['Distance (km)', 'Latitude', 'Longitude']:
        if col_name not in RoadTP.data.columns:
            raise IndexError(f'{col_name} is missing from Road file {RoadFile}')

    # create a dataframe from the filenames and infer the latitude and longitude from it.
    filenames = pd.DataFrame(files)
    filenames.columns = ['File Name']
    filenames.loc[:, ['Latitude', 'Longitude']] = filenames['File Name'].apply(os.path.basename).str. \
        extract(r'(.*)_(.*)_Solcast.*').astype('float64').to_numpy()

    # merge the road dataframe and the file dataframe to create the mapping.
    mapped_df = filenames.merge(RoadTP.data[['Distance (km)', 'Latitude', 'Longitude']],
                                left_on=['Latitude', 'Longitude'],
                                right_on=['Latitude', 'Longitude'], validate="1:1", how='left')
    if mapped_df['Distance (km)'].isna().sum() != 0:
        # the dataframe total of isna is not 0 means that there are lines that are not mapped.
        missing_points = mapped_df[mapped_df['Distance (km)'].isna()]
        warnings.warn(
            f"There are {mapped_df['Distance (km)'].isna().sum()} point(s) omitted in the output as they are missing in"
            f" the road file.\nThe file with missing point(s) are {missing_points['File Name'].to_list()}"
        )
        mapped_df.dropna(axis=0, inplace=True)

    return mapped_df


def get_file_list(csv_location: Union[str, os.PathLike]) -> Set[Union[str, os.PathLike]]:
    """Get the list of Solcast historic CSVs in the folder.

    The Solcast historic CSVs should be named in the format of {lat}_{lon}_Solcast_{sample_mode}.csv

    Args:
        csv_location: The location to search for the CSVs recursively

    Returns:
        A set of filepath to the solcast historic CSVs
    """

    # set up the regex filter and initialize the output file list
    f = re.compile('.*Solcast.*.csv')
    file_list = set()

    # perform a walk into all the subdirectories and get all the CSVs that matches the filter name
    for dirpath, dirs, files in os.walk(csv_location):
        for file in files:
            if f.match(os.path.join(dirpath, file)) is not None:
                file_list.add(os.path.join(dirpath, file))
    return file_list


def read_solcast_csv(filename: Union[str, PathLike], distance: float, start_date: datetime.datetime,
                     end_date: datetime.datetime) -> pd.DataFrame:
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
    # read the csv and set it to the distance along the route
    df = pd.read_csv(filename)
    df.loc[:, 'Distance (km)'] = distance

    # convert the data type of the datetime columns. Decoded not to rename the PeriodStart column to leave flexibility
    # in the future if we want to say the samples corresponds to the middle of the period
    df.loc[:, ['PeriodEnd']] = pd.to_datetime(df['PeriodEnd'])
    df.loc[:, ['PeriodStart']] = pd.to_datetime(df['PeriodStart'])
    df.loc[:, 'DateTime'] = df['PeriodStart']
    df.drop(columns=['PeriodEnd', 'PeriodStart'], inplace=True)

    # rename the columns
    df.rename(columns={'Dni': 'DirectSun (W/m2)', 'Dhi': 'DiffuseSun (W/m2)', 'AirTemp': 'AirTemp (degC)',
                       'SurfacePressure': 'AirPress (hPa)', 'WindSpeed10m': '10m WindVel (m/s)',
                       'WindDirection10m': 'WindDir (deg)',
                       'Azimuth': 'SunAzimuth (deg)'}, inplace=True)
    # convert values into those used by SolarSim
    df.loc[:, 'WindVel (m/s)'] = convert_wind(df.loc[:, '10m WindVel (m/s)'])
    df.loc[:, 'SunElevation (deg)'] = 90 - df['Zenith']
    df.loc[:, 'SunAzimuth (deg)'] = df.loc[:, 'SunAzimuth (deg)'] * -1
    df.loc[:, 'AirPress (Pa)'] = df.loc[:, 'AirPress (hPa)'] * 100

    # as the csv are in UTC, localize timezone before slicing the portion of data that we want.
    df.set_index('DateTime', inplace=True)
    df = df.loc[start_date:end_date, :].copy()

    # return only the columns that we are interested in.
    df = df[['Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
             'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)',
             'WindDir (deg)']].copy()
    return df


if __name__ == '__main__':  # pragma: no cover
    ROAD_FILE = r'Road-SolCast-10km.dat'
    CSV_LOC = '.'
    tz = pytz.timezone('Australia/Darwin')
    START_DATE = datetime.datetime(2019, 10, 13, 0, 0)
    END_DATE = datetime.datetime(2019, 10, 20, 23, 0)
    START_DATE = tz.localize(START_DATE)
    END_DATE = tz.localize(END_DATE)

    main(START_DATE, END_DATE, ROAD_FILE, CSV_LOC)

    if __debug__:  # pragma: no cover
        def test_dev_compare_outfile() -> None:
            """quick test to make sure noting have bwoken yet..."""
            f1_path = r'E:\solar_car_race_strategy\SolCastHistoric\Weather-SolCast-temp.dat'
            f2_path = r'E:\solar_car_race_strategy\SolCastHistoric\Weather-SolCast-N200-20220530.dat'
            with open(f1_path) as f1:
                with open(f2_path) as f2:
                    f1lines = f1.readlines()
                    f2lines = f2.readlines()
            assert f1lines == f2lines


        test_dev_compare_outfile()
