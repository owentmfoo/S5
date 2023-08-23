"""
Scripts and functions to are used to generate weather files.
TODO: reorganise this subpackage
TODO: code to convert Australia Bureau of Meteorology 1 min solar data to weather file
"""
import datetime
import logging
import os
from typing import Union

import boto3
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError


def convert_wind(input_wind_vel: pd.Series, wind_level=10) -> pd.Series:
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
    one_meter_wind = (
            input_wind_vel * np.log((zcar - zh) / z0) / np.log((wind_level - zh) / z0)
    )
    return one_meter_wind


def upload_file(
        file_name, bucket_name: str = "duscweather", object_name=None
) -> bool:  # pragma: no cover - code lifted directly from the s3 examples
    """Upload a file to an S3 bucket

    Args:
        file_name: File to upload
        bucket: Bucket to upload to
        object_name: S3 object name. If not specified then file_name is used
    Returns:
        True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        logging.debug(f'uploading {file_name} to S3 bucket: {bucket_name}.')
        response = s3_client.upload_file(file_name, bucket_name, object_name)
        logging.info(f'{file_name} uploaded to S3 bucket: {bucket_name}.')
    except ClientError as e:
        logging.error(e)
        return False
    return True


def to_csv(name: str, df: pd.DataFrame, dest_dir: Union[os.PathLike, str] = "") -> None:
    """Save the forecast to a csv.

    Args:
        name: Name of the location for the forecast.
        df: Forecast returned as a DataFrame.
        dest_dir: Destination directory either an absolute path or
        relative to the current working directory.
        Leave blank to save to current working directory.
    Returns:
        Saves the dataframe to the csv file.
    """
    if df.empty:
        logging.warning("Dataframe is empty, skip exporting to csv.")
        return None
    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime("%Y%m%d%H%M")
    file_name = f"Forecast{timestamp}{name}.csv"
    full_path = os.path.join(dest_dir, file_name)
    df.to_csv(full_path)
    return None


def to_parquet(name: str, df: pd.DataFrame, dest_dir: Union[os.PathLike, str] = "") -> None:
    """Save the forecast to a parquet file.

    Args:
        name: Name of the location for the forecast.
        df: Forecast returned as a DataFrame.
        dest_dir: Destination directory either an absolute path or
        relative to the current working directory.
        Leave blank to save to current working directory.
    Returns:
        Saves the dataframe to the parquuet file.
    """
    if df.empty:
        logging.warning("Dataframe is empty, skip exporting to parquet.")
        return None
    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime("%Y%m%d%H%M")
    file_name = f"Forecast{timestamp}{name}.parquet"
    full_path = os.path.join(dest_dir, file_name)
    df.to_parquet(full_path)
    return None
