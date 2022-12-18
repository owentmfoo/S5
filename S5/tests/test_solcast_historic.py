import datetime
import os
from typing import Union

import mock
import numpy as np
import pandas as pd
import pytest
import pytz

import S5.Tecplot as TP
from S5.Weather import solcast_historic


@pytest.fixture(scope="session")
def solcast_hist_csv(tmp_path_factory):
    """Returns a typical solcast historic csv."""
    filepath = tmp_path_factory.mktemp("data") / "-22.35721_133.38904_Solcast_native.csv"
    with open(filepath, 'w') as file:
        file.write(
            # pylint: disable=invalid-name
            """PeriodEnd,PeriodStart,Period,AirTemp,Azimuth,CloudOpacity,DewpointTemp,Dhi,Dni,Ebh,Ghi,GtiFixedTilt,GtiTracking,PrecipitableWater,RelativeHumidity,SurfacePressure,WindDirection10m,WindSpeed10m,Zenith,AlbedoDaily
2018-12-31T00:10:00Z,2018-12-31T00:04:00Z,PT6M,36.7,-100,0.0,14.3,95,922,688,783,783,1031,35.9,26.3,936.6,358,3.9,42,0.15
2018-12-31T00:20:00Z,2018-12-31T00:14:00Z,PT6M,36.8,-100,0.0,14.3,98,928,717,814,814,1039,35.9,26.2,936.5,359,3.7,39,0.15
2018-12-31T00:30:00Z,2018-12-31T00:24:00Z,PT6M,36.9,-99,0.0,14.3,100,935,745,844,844,1046,35.9,26.1,936.4,0,3.6,37,0.15
2018-12-31T00:40:00Z,2018-12-31T00:34:00Z,PT6M,37.0,-99,0.0,14.4,101,941,772,873,873,1053,35.9,26.0,936.3,2,3.4,35,0.15
2018-12-31T00:50:00Z,2018-12-31T00:44:00Z,PT6M,37.1,-98,0.0,14.4,102,947,798,900,900,1059,35.9,25.9,936.2,3,3.2,33,0.15""")
    return filepath


@pytest.fixture(scope="session")
def road_file(tmp_path_factory):
    """Returns a typical solcast historic csv."""
    filepath = tmp_path_factory.mktemp("data") / "Road_test.dat"
    with open(filepath, 'w') as file:
        file.write(
            """Title = "Stuart Highway - Altitudes, Headings, Latitude, and Longitude from Google Maps, Speed Limits from WSC2017 Route Notes"
Variables = "Distance (km)", "Altitude (m)", "Heading (deg)", "SpeedLimit (km/h)", "Latitude", "Longitude"
Zone T = "Stuart Highway", I=5, J=1, K=1, F=POINT
       0.000         24.7        318.7         50.0        -12.46597        130.84273
       30.25         25.0         17.3         50.0        -16.46571        131.54249
       70.16         24.8         61.4         50.0        -18.46555        128.08255
       100.53        24.8         43.3         50.0        -25.46545        122.45274
       250.6         25.0         44.3         50.0        -53.46534        127.84284""")
    return filepath


def test_read_solcast_csv(solcast_hist_csv):
    distance = 6969
    tz = pytz.timezone('UTC')
    start_date = datetime.datetime(2018, 12, 31, 0, 10, tzinfo=tz)
    end_date = datetime.datetime(2018, 12, 31, 0, 40, tzinfo=tz)
    df = solcast_historic.read_solcast_csv(solcast_hist_csv, distance, start_date, end_date)
    assert df.shape[0] == 3
    assert df['Distance (km)'][0] == distance
    correct_col_list = ['Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
                        'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)',
                        'WindDir (deg)']
    for col_name in correct_col_list:
        assert col_name in df.columns


def test_get_file_list(tmpdir):
    def _make_solcast_csv(path):
        """Private function to make an empty placeholder files at the path given and return the path with the file."""
        lat = np.random.randint(90)
        lon = np.random.randint(90)

        filename = f'{lat}_{lon}_Solcast_native.csv'
        with open(path / filename, 'x'):
            pass
        return str(path / filename)

    # set up the file tree to be searched
    correct_result = set()

    filepath = tmpdir / "folder1"
    os.mkdir(filepath)
    correct_result.add(_make_solcast_csv(filepath))
    correct_result.add(_make_solcast_csv(filepath))

    filepath = tmpdir / "folder2"
    os.mkdir(filepath)
    correct_result.add(_make_solcast_csv(filepath))
    correct_result.add(_make_solcast_csv(filepath))

    filepath = tmpdir / "folder1" / "folder3"
    os.mkdir(filepath)
    correct_result.add(_make_solcast_csv(filepath))
    correct_result.add(_make_solcast_csv(filepath))
    correct_result.add(_make_solcast_csv(filepath))

    test_result = solcast_historic.get_file_list(tmpdir)

    assert len(test_result) == len(correct_result)
    assert test_result == correct_result


@pytest.fixture(scope="session")
def mock_read_solcast_csv():
    """return a mock function that can be used to replace read_solcast_csv"""

    def mock_read_solcast_csv(filename: Union[str, os.PathLike], distance: float, start_date: datetime.datetime,
                              end_date: datetime.datetime):
        end_date = end_date.astimezone(start_date.tzinfo)
        patch_spot_df = pd.DataFrame(
            columns=['Distance (km)', 'DirectSun (W/m2)', 'DiffuseSun (W/m2)', 'SunAzimuth (deg)',
                     'SunElevation (deg)', 'AirTemp (degC)', 'AirPress (Pa)', 'WindVel (m/s)',
                     'WindDir (deg)'],
            index=pd.date_range(start_date, end_date, periods=6),
        )
        patch_spot_df.fillna(0, inplace=True)
        patch_spot_df.loc[:, 'Distance (km)'] = distance
        patch_spot_df.loc[:, 'DateTime'] = patch_spot_df.index
        return patch_spot_df

    return mock_read_solcast_csv


def test_main(road_file, monkeypatch, tmpdir, mock_read_solcast_csv):
    """Tests the main function of solcast_historic.
    The individual functions should be tested sperately and this test should only focus on tests how it pulls it all
    together."""
    RoadTP = TP.TecplotData(road_file)
    RoadTP.data.loc[:, 'infile'] = RoadTP.data['Latitude'].astype(str) + '_' + RoadTP.data['Longitude'].astype(
        str) + '_Solcast_native.csv'

    # patch get_file_list
    monkeypatch.setattr(solcast_historic, 'get_file_list', mock.MagicMock(return_value=RoadTP.data['infile'].to_list()))

    # patch read_solcast_csv
    monkeypatch.setattr(solcast_historic, 'read_solcast_csv', mock_read_solcast_csv)

    tz = pytz.timezone('UTC')
    start_date = datetime.datetime(2019, 10, 13, 6, 00, tzinfo=tz)
    end_date = datetime.datetime(2019, 10, 18, 6, 00, tzinfo=tz)
    csv_location = tmpdir

    solcast_historic.main(start_date, end_date, road_file, csv_location,
                          output_file=tmpdir / 'Weather-SolCast-temp.dat')

    WeatherTP = TP.SSWeather(tmpdir / 'Weather-SolCast-temp.dat')
    assert WeatherTP.data['Distance (km)'].nunique() == 5
    WeatherTP.add_timestamp(startday='20191013')
    assert WeatherTP.data['DateTime'].nunique() == 6


def test_main_mismatch_timezone(road_file, monkeypatch, tmpdir, mock_read_solcast_csv):
    RoadTP = TP.TecplotData(road_file)
    RoadTP.data.loc[:, 'File Name'] = RoadTP.data['Latitude'].astype(str) + '_' + RoadTP.data['Longitude'].astype(
        str) + '_Solcast_native.csv'

    # patch get_file_list
    monkeypatch.setattr(solcast_historic, 'get_file_list',
                        mock.MagicMock(return_value=RoadTP.data['File Name'].to_list()))

    # patch read_solcast_csv
    monkeypatch.setattr(solcast_historic, 'read_solcast_csv', mock_read_solcast_csv)

    tz = pytz.timezone('UTC')
    start_date = datetime.datetime(2019, 10, 13, 6, 00, tzinfo=tz)
    end_date = datetime.datetime(2019, 10, 18, 6, 00, tzinfo=tz)
    end_date = end_date.astimezone(pytz.timezone('Australia/Darwin'))
    csv_location = tmpdir

    with pytest.warns(UserWarning) as warn:
        solcast_historic.main(start_date, end_date, road_file, csv_location,
                              output_file=tmpdir / 'Weather-SolCast-temp.dat')

    assert len(warn) == 1
    assert warn[0].message.args[
               0] == 'Starting and ending time zone mismatch, using starting timezone as output timezone.'

    WeatherTP = TP.SSWeather(tmpdir / 'Weather-SolCast-temp.dat')
    assert WeatherTP.data.loc[0, 'Time (HHMM)'] == 600


@pytest.mark.parametrize('col', ['Distance (km)', 'Latitude', 'Longitude'])
def test_map_files_missing_col(road_file, col, tmpdir):
    RoadTP = TP.TecplotData(road_file)
    RoadTP.data.loc[:, 'File Name'] = RoadTP.data['Latitude'].astype(str) + '_' + RoadTP.data['Longitude'].astype(
        str) + '_Solcast_native.csv'
    file_names = RoadTP.data['File Name'].to_list()
    RoadTP.data.drop(columns=col, inplace=True)
    mock_road_path = tmpdir / 'mockRoad.dat'
    RoadTP.write_tecplot(mock_road_path)

    with pytest.raises(IndexError, match=rf' is missing from Road file'):
        output_df = solcast_historic.map_files(mock_road_path, file_names)


def test_map_files(road_file):
    RoadTP = TP.TecplotData(road_file)
    RoadTP.data.loc[:, 'File Name'] = RoadTP.data['Latitude'].astype(str) + '_' + RoadTP.data['Longitude'].astype(
        str) + '_Solcast_native.csv'
    file_names = RoadTP.data['File Name'].to_list()

    # check if the mapping worked
    output_df = solcast_historic.map_files(road_file, file_names)
    pd.testing.assert_frame_equal(RoadTP.data[['File Name', 'Latitude', 'Longitude', 'Distance (km)']], output_df)
    # check if having extra rows in the road file is fine
    solcast_historic.map_files(road_file, file_names[:-1])


def test_map_files_missing_point_in_road(road_file, tmpdir):
    RoadTP = TP.TecplotData(road_file)
    RoadTP.data.loc[:, 'File Name'] = RoadTP.data['Latitude'].astype(str) + '_' + RoadTP.data['Longitude'].astype(
        str) + '_Solcast_native.csv'
    file_names = RoadTP.data['File Name'].to_list()
    RoadTP.data.drop(index=[1, 3], inplace=True)
    RoadTP.update_zone_1d()
    RoadTP.write_tecplot(tmpdir / 'tmpRoad.dat')

    with pytest.warns(UserWarning, match=r'There are \d point\(s\) omitted in the output as they are missing in the '
                                         r'road file.\nThe file with missing point\(s\) are'):
        output_df = solcast_historic.map_files(tmpdir / 'tmpRoad.dat', file_names)
    assert output_df.isna().sum().sum() == 0
    assert output_df.shape[0] == 3
