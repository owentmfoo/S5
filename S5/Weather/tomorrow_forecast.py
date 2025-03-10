import datetime
import json
import logging

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)
null_handler = logging.NullHandler()
logger.addHandler(null_handler)


def send_request(
        latitude: float, longitude: float, api_key: str, name: str = "unknown"
) -> pd.DataFrame:
    """Obtain the forecast from tomorrow.io

    Args:
        latitude: latitude of the spot to get the forecast.
        longitude: longitude  of the spot to get the forecast.
        api_key: Solcast api key
        name: Name of the location for the forecast.

    Returns:
        Forecast as a dataframe.

    """
    # Build the API request URL
    url = f"https://api.tomorrow.io/v4/weather/forecast?location={latitude},{longitude}&apikey={api_key}"  # url so pylint: disable=line-too-long
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")

    # Send the API request
    logger.debug(
        "Sending request to tomorrow.io for lat: %f lon: %f with key: %s",
        latitude,
        longitude,
        api_key,
    )
    try:
        response = requests.get(url)
    except requests.RequestException as e:
        logging.error(e)
        return pd.DataFrame()
    logging.debug(
        "tomorrow.io response for %s: %d", name, response.status_code
    )

    # Parse the response JSON
    if response.status_code != 200:
        logging.error(
            "Bad response from tomorrow.io API for forecast data at %f, "
            "%f with key= %s.\n"
            "\tError %s: %s",
            latitude,
            longitude,
            api_key,
            response.status_code,
            response.text,
        )
        return pd.DataFrame()

    data = json.loads(response.text)

    timescale = "minutely"
    minutely2 = pd.DataFrame(
        [
            pd.Series(i["values"], name=i["time"])
            for i in data["timelines"][timescale]
        ]
    )

    timescale = "hourly"
    hourly2 = pd.DataFrame(
        [
            pd.Series(i["values"], name=i["time"])
            for i in data["timelines"][timescale]
        ]
    )

    timescale = "daily"
    daily2 = pd.DataFrame(
        [
            pd.Series(i["values"], name=i["time"])
            for i in data["timelines"][timescale]
        ]
    )

    df = pd.concat([minutely2, hourly2, daily2])

    for time_variable in [
        "moonriseTime",
        "moonsetTime",
        "sunriseTime",
        "sunsetTime",
    ]:
        if time_variable in df.columns:
            df.loc[:, time_variable] = df.loc[:, time_variable].astype(
                np.datetime64
            )
    df["latitude"] = latitude
    df["longitude"] = longitude
    df["location_name"] = name
    df["prediction_date"] = np.datetime64(pd.Timestamp(timestamp))
    df.index = pd.DatetimeIndex(df.index)
    df = df.reset_index(names="period_end")
    return df


if __name__ == "__main__":  # pragma: no cover
    logging.getLogger().setLevel(logging.INFO)
    logging.info("lambda function started")
    from config import tomorrow_api_key

    API_KEY = tomorrow_api_key

    locations = [
        [51.178882, -1.826215, "Stonehenge"],
        [41.89021, 12.492231, "The Colosseum"],
        [-12.4239, 130.8925, "Darwin_Airport"],
        [-19.64, 134.18, "Tennant_Creek_Airport"],
        [-23.7951, 133.8890, "Alice_Springs_Airport"],
        [-29.03, 134.72, "Coober_Pedy_Airport"],
        [-34.9524, 138.5196, "Adelaide_Airport"],
        [-31.1558, 136.8054, "Woomera"],
        [-16.262330910217, 133.37694753742824, "Daly_Waters"],
    ]

    for location in locations:
        loc_df = send_request(location[0], location[1], API_KEY, location[2])
        try:
            df = pd.concat([df, loc_df], axis=0)
        except NameError:
            df = loc_df
