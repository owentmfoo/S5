import pandas as pd
import pytest
import numpy as np
from S5.Weather import readgrib
from io import StringIO
from unittest.mock import MagicMock
import datetime
import pytz
import xarray

"""
Test Strategy.
Single end to end test, compare with previous output
Minimal testing on xarray and reading of grib file as they were tested externally.
TODO: Test for ssr_to_direct_and_diffuse to be added when function is finalised.  
"""


def test_cumulative_ssr_to_hourly_one_day():
    x = np.random.random(15)
    cum = np.cumsum(x)
    hourly = readgrib.cumulative_ssr_to_hourly(cum)
    np.testing.assert_allclose(x, hourly)


def test_cumulative_ssr_to_hourly_complex():
    x = np.random.random(15)
    y = np.zeros(20)
    z = np.random.random(1)
    cum = np.concatenate((np.cumsum(x), np.cumsum(y), np.cumsum(z)))
    hourly = readgrib.cumulative_ssr_to_hourly(cum)
    np.testing.assert_allclose(np.concatenate((x, y, z)), hourly)


@pytest.fixture()
def grib_df():
    csv = StringIO("""time,step,u10,v10,t2m,ssr,sp,ssrd,number,surface,latitude,longitude,valid_time
2020-09-13,0 days 01:00:00,-2.3109846,0.2997589,303.2915,2184136.5,101293.94,2531763.5,0,0.0,-12.51,130.98,2020-09-13 01:00:00
2020-09-13,0 days 02:00:00,-2.7291832,0.19225502,305.33398,4871910.0,101218.56,5647287.5,0,0.0,-12.51,130.98,2020-09-13 02:00:00
2020-09-13,0 days 03:00:00,-2.9107647,0.07004833,306.8567,7870393.5,101086.5,9122994.0,0,0.0,-12.51,130.98,2020-09-13 03:00:00
2020-09-13,0 days 04:00:00,-2.752367,0.124402046,307.89478,10928230.0,100937.75,12667493.0,0,0.0,-12.51,130.98,2020-09-13 04:00:00
2020-09-13,0 days 05:00:00,-2.8820362,0.44239426,308.75513,13794126.0,100825.25,15989492.0,0,0.0,-12.51,130.98,2020-09-13 05:00:00
2020-09-13,0 days 06:00:00,-2.7047367,0.20237732,309.0066,16251759.0,100733.375,18838232.0,0,0.0,-12.51,130.98,2020-09-13 06:00:00
2020-09-13,0 days 07:00:00,-2.6927958,-0.20650005,308.85547,17963876.0,100683.31,20822908.0,0,0.0,-12.51,130.98,2020-09-13 07:00:00
2020-09-13,0 days 08:00:00,-2.1996584,-0.65552807,307.90234,18982948.0,100700.125,22004208.0,0,0.0,-12.51,130.98,2020-09-13 08:00:00
2020-09-13,0 days 09:00:00,-1.4100647,-1.8915176,305.6172,19288974.0,100789.56,22358994.0,0,0.0,-12.51,130.98,2020-09-13 09:00:00
2020-09-13,0 days 10:00:00,-0.3195696,-2.5932646,303.08423,19292198.0,100876.81,22362728.0,0,0.0,-12.51,130.98,2020-09-13 10:00:00
""")
    df = pd.read_csv(filepath_or_buffer=csv)
    df['time'] = df['time'].astype('datetime64')
    df['valid_time'] = df['valid_time'].astype('datetime64')
    df.set_index('time')
    return df.copy()


@pytest.fixture(scope='function')
def mock_extract_df(grib_df, monkeypatch):
    monkeypatch.setattr(readgrib, "extract_df", MagicMock(return_value=grib_df))


def test_era5_spot(mock_extract_df, tmp_path, grib_df):
    TZ = pytz.timezone('UTC')
    START_DATE = datetime.datetime(2020, 9, 13, 2, 0, tzinfo=TZ)
    END_DATE = datetime.datetime(2020, 9, 13, 9, 0, tzinfo=TZ)
    output_df = readgrib.era5_spot(xarray.Dataset.from_dataframe(grib_df), START_DATE, END_DATE)
    assert output_df.shape[0] == 8


def test_from_era5(mock_extract_df, tmp_path, grib_df, road_file, monkeypatch):
    STATION_FILE = road_file
    GRIB_FILE = 'mock'
    monkeypatch.setattr(xarray, 'open_dataset', MagicMock(return_value=xarray.Dataset.from_dataframe(grib_df)))
    TZ = pytz.timezone('UTC')
    START_DATE = datetime.datetime(2020, 9, 13, 2, 0, tzinfo=TZ)
    END_DATE = datetime.datetime(2020, 9, 13, 9, 0, tzinfo=TZ)
    readgrib.from_era5(STATION_FILE, GRIB_FILE, START_DATE, END_DATE, outfile=tmp_path / r'Weather-era5byS5-tmp.dat',
                       Solar=True)
