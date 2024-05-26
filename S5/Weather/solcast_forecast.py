import datetime
import json
import logging
import os
import time

import numpy as np
import pandas as pd
import requests
from solcast import live, forecast

logger = logging.getLogger(__name__)
null_handler = logging.NullHandler()
logger.addHandler(null_handler)


def send_request_old(
        latitude: float, longitude: float, api_key: str, name: str = "unknown"
) -> pd.DataFrame:
    """Obtain the forecast from Solcast

    Args:
        latitude: latitude of the spot to get the forecast.
        longitude: longitude  of the spot to get the forecast.
        api_key: Solcast api key
        name: Name of the location for the forecast.

    Returns:
        Forecast as a dataframe.
    """
    parameters = {
        "api_key": api_key,
        "latitude": latitude,
        "longitude": longitude,
        "hours": 168,
        "format": "json",
    }
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    logger.debug(
        "Sending request to solcast for lat: %f lon: %f with key: %s",
        latitude,
        longitude,
        api_key,
    )
    try:
        response = requests.get(
            "https://api.solcast.com.au/world_radiation/forecasts",
            params=parameters,
        )
    except requests.RequestException as e:
        logger.error(e)
        return pd.DataFrame()
    logger.debug("Solcast response for %s: %d", name, response.status_code)

    if response.status_code == 200:
        data = json.loads(response.text)
        df = pd.DataFrame(data["forecasts"])
        df.loc[:, "period_end"] = pd.to_datetime(df["period_end"])
        df.loc[:, "period"] = df.loc[:, "period"].astype(pd.CategoricalDtype())
        df["latitude"] = latitude
        df["longitude"] = longitude
        df["location_name"] = name
        df["prediction_date"] = np.datetime64(pd.Timestamp(timestamp))
        return df
    logger.error(
        "Bad response from Solacast API for forecast data at %f, "
        "%f with key= %s.\n"
        "\tError %d: %s",
        latitude,
        longitude,
        api_key,
        response.status_code,
        response.text,
    )
    return pd.DataFrame()


def send_live_request(
        latitude: float, longitude: float, api_key: str, name: str = "unknown"
) -> pd.DataFrame:
    """Obtain the historic data from Solcast using the Solcast SDK

    Args:
        latitude: latitude of the spot to get the forecast.
        longitude: longitude  of the spot to get the forecast.
        api_key: Solcast api key
        name: Name of the location for the forecast.

    Returns:
        Forecast as a dataframe.
    """
    os.environ["SOLCAST_API_KEY"] = api_key
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    period = "PT5M"
    retries = 3
    for i in range(retries):
        res = live.radiation_and_weather(
            latitude=latitude,
            longitude=longitude,
            output_parameters=[
                "dni",
                "dhi",
                "air_temp",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "azimuth",
                "zenith",
            ],
            period=period,
            hours=168,
        )
        if res.code == 200:
            logging.debug("successful request for %s", name)
            loc_df = res.to_pandas()
            loc_df = loc_df.rename(
                columns={
                    "surface_pressure": "pressureSurfaceLevel",
                    "wind_speed_10m": "windSpeed",
                    "wind_direction_10m": "windDirection",
                }
            )
            loc_df.reset_index(inplace=True)
            loc_df.loc[:, "period"] = period
            loc_df.loc[:, "period"] = loc_df.loc[:, "period"].astype(
                pd.CategoricalDtype()
            )
            loc_df["latitude"] = latitude
            loc_df["longitude"] = longitude
            loc_df["location_name"] = name
            loc_df["prediction_date"] = np.datetime64(pd.Timestamp(timestamp))
            return loc_df
        elif res.code == 429:
            logging.info(
                "rate limited for request %s, %d retry remaining, "
                "retrying in %d seconds",
                name,
                retries - i,
                int(res.exception[-10:-8]) + 1,
            )
            time.sleep(int(res.exception[-10:-8]) + 1)
    logging.error("Unable to get forecast for %s, error %s",
                  name,
                  res.exception)


def send_forecast_request(
        latitude: float, longitude: float, api_key: str, name: str = "unknown"
) -> pd.DataFrame:
    """Obtain the forecast from Solcast using the Solcast SDK

    Args:
        latitude: latitude of the spot to get the forecast.
        longitude: longitude  of the spot to get the forecast.
        api_key: Solcast api key
        name: Name of the location for the forecast.

    Returns:
        Forecast as a dataframe.
    """
    os.environ["SOLCAST_API_KEY"] = api_key
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    period = "PT5M"
    retries = 3
    for i in range(retries):
        res = forecast.radiation_and_weather(
            latitude=latitude,
            longitude=longitude,
            output_parameters=[
                "dni",
                "dni10",
                "dni90",
                "dhi",
                "dhi10",
                "dhi90",
                "air_temp",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "azimuth",
                "zenith",
            ],
            period=period,
            hours=336,
        )
        if res.code == 200:
            logging.debug("successful request for %s", name)
            loc_df = res.to_pandas()
            loc_df = loc_df.rename(
                columns={
                    "surface_pressure": "pressureSurfaceLevel",
                    "wind_speed_10m": "windSpeed",
                    "wind_direction_10m": "windDirection",
                }
            )
            loc_df.reset_index(inplace=True)
            loc_df.loc[:, "period"] = period
            loc_df.loc[:, "period"] = loc_df.loc[:, "period"].astype(
                pd.CategoricalDtype()
            )
            loc_df["latitude"] = latitude
            loc_df["longitude"] = longitude
            loc_df["location_name"] = name
            loc_df["prediction_date"] = np.datetime64(pd.Timestamp(timestamp))
            return loc_df
        elif res.code == 429:
            logging.info(
                "rate limited for request %s, %d retry remaining, "
                "retrying in %d seconds",
                name,
                retries - i,
                int(res.exception[-10:-8]) + 1,
            )
            time.sleep(int(res.exception[-10:-8]) + 1)
    logging.error("Unable to get forecast for %s, error %s", name,
                  res.exception)
