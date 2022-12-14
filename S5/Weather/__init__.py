"""
Scripts and functions to are used to generate weather files.
TODO: reorganise this subpackage
TODO: code to convert Australia Bureau of Meteorology 1 min solar data to weather file
"""
import pandas as pd
import numpy as np


def convert_wind(input_wind_vel: pd.Series, wind_level=10):
    """
    convert 10m wind velocity to solar car level (1m) assuming open terrain with surface roughness of z0 = 0.01
    Args:
        input_wind_vel: A pa.Series of wind velocity at wind level.
        wind_level: level of the the wind velocity in meters
    Returns:
        A pa.Series of wind converted to 1m.

    Examples:
        >>> df.loc[:,'WindVel (m/s)'] = convert_wind(df.loc[:,'10m WindVel (m/s)'])

    """
    zcar = 1
    z0 = 0.01
    zh = 0
    one_meter_wind = input_wind_vel * np.log((zcar - zh) / z0) / np.log((wind_level - zh) / z0)
    return one_meter_wind
