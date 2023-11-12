import json
import random
import time
from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests
from requests import RequestException
from solcast.api import Response

from S5.Weather.solcast_forecast import (
    send_request_old,
    send_live_request,
    send_forecast_request,
)

# Define mock input parameters
latitude = 37.7749
longitude = -122.4194
api_key = "fake_api_key"
name = "San Francisco"

# Define mock response JSON
response_text = {
    "forecasts": [
        {
            "period_end": "2023-05-15T23:00:00.000Z",
            "period": "PT30M",
            "ghi": 800,
            "dni": 700,
            "dhi": 100,
        },
        {
            "period_end": "2023-05-16T00:00:00.000Z",
            "period": "PT30M",
            "ghi": 750,
            "dni": 650,
            "dhi": 100,
        },
    ]
}


# Define mock response object
class MockResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text)


# Define test function
def test_send_request(monkeypatch, caplog):
    # Define mock response
    mock_response = MockResponse(
        status_code=200,
        text=json.dumps(response_text)
    )

    # Mock the requests.get method
    def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)

    # Call the send_request function
    result = send_request_old(latitude, longitude, api_key, name)

    # Check the result is a pandas DataFrame
    assert isinstance(result, pd.DataFrame)

    # Check the DataFrame contains the expected columns
    expected_columns = [
        "period",
        "ghi",
        "dni",
        "dhi",
        "period_end",
        "latitude",
        "longitude",
        "location_name",
        "prediction_date",
    ]
    assert set(result.columns) == set(expected_columns)

    # Check the DataFrame contains the expected number of rows
    assert len(result) == len(response_text["forecasts"])

    # Check the DataFrame values match the expected response
    for i, (index, row) in enumerate(result.iterrows()):
        expected_row = response_text["forecasts"][i]
        assert row["period"] == expected_row["period"]
        assert row["ghi"] == expected_row["ghi"]
        assert row["dni"] == expected_row["dni"]
        assert row["dhi"] == expected_row["dhi"]
    assert (result.latitude == latitude).min()
    assert (result.longitude == longitude).min()
    assert (result.location_name == name).min()

    # test the response of a rate limit
    mock_response = MockResponse(status_code=429, text=b"")

    # Mock the requests.get method
    def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)

    # Call the send_request function
    result = send_request_old(latitude, longitude, api_key, name)

    # Check that the DataFrame is empty
    assert result.empty

    # Check that the warning is logged
    assert "Bad response from Solacast API for forecast data at" in caplog.text
    assert api_key in caplog.text
    assert str(latitude) in caplog.text
    assert str(longitude) in caplog.text
    assert "429" in caplog.text


def test_send_request_failure(monkeypatch, caplog):
    # set up mock response with error
    def mock_get(url, *args, **kwargs):
        raise RequestException("Network error")

    monkeypatch.setattr("requests.get", mock_get)

    result = send_request_old(latitude, longitude, api_key, name)

    # check that the function returns an empty DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty

    # check that an error was captured in the log
    assert "ERROR" in caplog.text
    assert "Network error" in caplog.text


@pytest.fixture()
def mock_solcast_response():
    mock_response = MagicMock(spec=Response)
    mock_response.code = 200
    mock_response.url = "https://example.com"
    mock_response.data = b'{"example": "data"}'
    mock_response.success = True
    mock_response.exception = None
    return mock_response


def test_send_live_requests(monkeypatch, mock_solcast_response):
    # arrange
    def mock_solcast_call(*args, **kwargs):
        return mock_solcast_response

    monkeypatch.setattr("solcast.live.radiation_and_weather", mock_solcast_call)

    # act
    response = send_live_request(latitude, longitude, api_key, name)

    # assert
    mock_solcast_response.to_pandas.assert_called()


def test_send_live_requests_timeout(monkeypatch, mock_solcast_response):
    # arrange
    mock_solcast_response.code = 429
    timout = random.randrange(1, 60)
    mock_solcast_response.exception = f"Rate limited ... {timout} second."

    def mock_solcast_call(*args, **kwargs):
        return mock_solcast_response

    monkeypatch.setattr("solcast.live.radiation_and_weather", mock_solcast_call)
    mock_sleep = MagicMock(spec_set=time.sleep)
    monkeypatch.setattr("time.sleep", mock_sleep)

    # act
    response = send_live_request(latitude, longitude, api_key, name)

    # assert
    assert response is None
    mock_sleep.assert_called_with(timout + 1)
    assert mock_sleep.call_count == 3


def test_send_forecast_requests(monkeypatch, mock_solcast_response):
    # arrange
    def mock_solcast_call(*args, **kwargs):
        return mock_solcast_response

    monkeypatch.setattr(
        "solcast.forecast.radiation_and_weather",
        mock_solcast_call
    )

    # act
    response = send_forecast_request(latitude, longitude, api_key, name)

    # assert
    mock_solcast_response.to_pandas.assert_called()


def test_send_forecast_requests_timeout(monkeypatch, mock_solcast_response):
    # arrange
    mock_solcast_response.code = 429
    timout = random.randrange(1, 60)
    mock_solcast_response.exception = f"Rate limited ... {timout} second."

    def mock_solcast_call(*args, **kwargs):
        return mock_solcast_response

    monkeypatch.setattr(
        "solcast.forecast.radiation_and_weather",
        mock_solcast_call
    )
    mock_sleep = MagicMock(spec_set=time.sleep)
    monkeypatch.setattr("time.sleep", mock_sleep)

    # act
    response = send_forecast_request(latitude, longitude, api_key, name)

    # assert
    assert response is None
    mock_sleep.assert_called_with(timout + 1)
    assert mock_sleep.call_count == 3
