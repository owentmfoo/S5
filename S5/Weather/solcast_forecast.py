import datetime
import json
import logging

import awswrangler as wr
import numpy as np
import pandas as pd
import requests


def send_request(
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
    logging.debug(f"Sending request to solcast for lat:{latitude} lon:{longitude}")
    try:
        response = requests.get(
            "https://api.solcast.com.au/world_radiation/forecasts", params=parameters
        )
    except requests.RequestException as e:
        logging.error(e)
        return pd.DataFrame()
    logging.debug(f"Solcast response for {name}: {response.status_code}")

    if response.status_code == 200:
        data = json.loads(response.text)
        df = pd.DataFrame(data["forecasts"])
        df.loc[:, "period_end"] = df.loc[:, "period_end"].astype(np.datetime64)
        df.loc[:, "period"] = df.loc[:, "period"].astype(pd.CategoricalDtype())
        df["latitude"] = latitude
        df["longitude"] = longitude
        df["location_name"] = name
        df["prediction_date"] = np.datetime64(pd.Timestamp(timestamp))
        return df
    logging.error(
        f"Bad response from Solacast API for forecast data at {latitude}, "
        f"{longitude} with key= {api_key}.\n"
        f"\tError {response.status_code}: {response.text}"
    )
    return pd.DataFrame()


if __name__ == "__main__":  # pragma: no cover
    logging.getLogger().setLevel(logging.INFO)
    logging.info("lambda function started")
    from config import solcast_api_key

    API_KEY = solcast_api_key

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

    wr.s3.to_parquet(
        df=df,
        path=f"s3://duscweather/solcast/",
        dataset=True,
        mode="append",
        filename_prefix="solcast_",
    )
