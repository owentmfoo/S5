import logging
from typing import Union
import os
import sys
import datetime
import requests
import boto3


def send_request(
        latitude: float, longitude: float, api_key: str, name: str = "unknown"
) -> bytes:
    """Obtain the forecast from Solcast

    Args:
        latitude: latitude of the spot to get the forecast.
        longitude: longitude  of the spot to get the forecast.
        api_key: Solcast api key
        name: Name of the location for the forecast.

    Returns:
        Forecast in bytes as a csv.
    """
    parameters = {
        "api_key": api_key,
        "latitude": latitude,
        "longitude": longitude,
        "hours": 168,
        "format": "csv",
    }
    logging.debug(f"Sending request for lat-{latitude} lon-{longitude}")
    response = requests.get(
        "https://api.solcast.com.au/world_radiation/forecasts", params=parameters
    )
    logging.debug(f"{name} {response.status_code}")
    if response.status_code == 200:
        return response.content
    logging.error(
        f"Bad response from Solacast API for forecast data.\n"
        f"\tError {response.status_code}: {response.content.decode('utf8')}"
    )
    return b""


def to_csv(name: str, content: bytes, dest_dir: Union[os.PathLike, str] = ""):
    """Save the forecast to a csv.

    Args:
        name: Name of the location for the forecast.
        content: Forecast returned.
        dest_dir: Destination directory either an absolute path or
        relative to the current working directory.
        Leave blank to save to current working directory.
    Returns:
        Saves the bytes to the csv file.
    """
    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime("%Y%m%d%H%M")
    file_name = f"Forecast{timestamp}{name}.csv"
    full_path = os.path.join(dest_dir, file_name)
    with open(f"{full_path}", "wb") as f:
        f.write(content)


def to_s3(name: str, content: bytes, bucket_name: str = "solcastresults") -> None:
    """Save the forecast to AWS S3. To be used on AWS Lambda.

    Args:
        name: Name of the location for the forecast.
        content: Forecast returned.
        bucket_name: Name of the S3 bucket.

    Returns:
        Saves the forecast to S3.
    """
    s3 = boto3.resource("s3")
    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime("%Y%m%d%H%M")
    FileName = f"Forecast{timestamp}{name}"
    s3.Bucket(bucket_name).put_object(Key=FileName, Body=content)


def forecast_to_csv(
        latitude: float,
        longitude: float,
        api_key: str,
        name: str = None,
        dest_dir: str = "",
) -> None:
    """Obtains a forecast from solcast and save to csv.

    Args:
        latitude: latitude of the spot to get the forecast.
        longitude: longitude  of the spot to get the forecast.
        api_key: Solcast api key
        name: Name of the location for the forecast.
        dest_dir: Destination directory either an absolute path
        or relative to the current working directory.
        Leave blank to save to current working directory.

    Returns:
        Forecast will be save to csv.
    """
    if name is None:
        name = f"lat{latitude}lon{longitude}"
    response = send_request(latitude, longitude, api_key, name)
    to_csv(name, response, dest_dir)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG", stream=sys.stdout)
    logging.info("test")
    from config import solcast_api_key

    # solcast_api_key = ''
    send_request(51.178882, -1.826215, solcast_api_key, "Stonehenge.csv")
    # send_request(-12.4239, 130.8925, solcast_api_key, "Darwin_Airport.csv")
    # send_request(-19.64, 134.18, solcast_api_key, "Tennant_Creek_Airport.csv")
    # send_request(-23.7951, 133.8890, solcast_api_key, "Alice_Springs_Airport.csv")
    # send_request(-29.03, 134.72, solcast_api_key, "Coober_Pedy_Airport.csv")
    # send_request(-34.9524, 138.5196, solcast_api_key, "Adelaide_Airport.csv")
    # send_request(-31.1558, 136.8054, solcast_api_key, "Woomera.csv")
    # send_request(-16.262330910217, 133.37694753742824, solcast_api_key, "Daly_Waters.csv")
