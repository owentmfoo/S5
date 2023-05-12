import json
import logging
import os

import numpy as np
import pandas as pd
import requests


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
    url = f"https://api.tomorrow.io/v4/weather/forecast?location={latitude},{longitude}&apikey={api_key}"

    # Send the API request
    logging.debug(f"Sending request to tomorrow.io for lat:{latitude} lon:{longitude}")
    try:
        response = requests.get(url)
    except requests.RequestException as e:
        logging.error(e)
        return pd.DataFrame()
    logging.debug(f"tomorrow.io response for {name}: {response.status_code}")

    # Parse the response JSON
    if response.status_code != 200:
        logging.error(
            f"Bad response from tomorrow.io API for forecast data.\n"
            f"\tError {response.status_code}: {response.text}"
        )
        return pd.DataFrame()

    data = json.loads(response.text)

    timescale = "minutely"
    minutely = pd.DataFrame(
        [i["values"].values() for i in data["timelines"][timescale]],
        columns=data["timelines"][timescale][0]["values"].keys(),
        index=[i["time"] for i in data["timelines"][timescale]],
    )
    timescale = "hourly"
    hourly = pd.DataFrame(
        [i["values"].values() for i in data["timelines"][timescale]],
        columns=data["timelines"][timescale][0]["values"].keys(),
        index=[i["time"] for i in data["timelines"][timescale]],
    )
    timescale = "daily"
    daily = pd.DataFrame(
        [i["values"].values() for i in data["timelines"][timescale]],
        columns=data["timelines"][timescale][0]["values"].keys(),
        index=[i["time"] for i in data["timelines"][timescale]],
    )

    df = pd.concat([minutely, hourly, daily])

    for time_variable in ["moonriseTime", "moonsetTime", "sunriseTime", "sunsetTime"]:
        if time_variable in df.columns:
            df.loc[:, time_variable] = df.loc[:, time_variable].astype(np.datetime64)
    df.index = pd.DatetimeIndex(df.index)
    return df


if __name__ == "__main__":  # pragma: no cover
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("lambda function started")
    from S5.Weather import to_parquet, upload_file
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

    os.mkdir("/tmp/Forecasts")
    for location in locations:
        df = send_request(location[0], location[1], API_KEY, location[2])
        to_parquet(location[2], df, r"/tmp/Forecasts")

    forecasts = os.listdir("/tmp/Forecasts")
    for forecast in forecasts:
        upload_file(
            os.path.join("/tmp/Forecasts", forecast),
            "solcastresults",
            f"tomorrow/{forecast}",
        )
