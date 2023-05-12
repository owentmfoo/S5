import json

import pandas as pd
import requests
from requests import RequestException

from S5.Weather.solcast_forecast import send_request

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
    mock_response = MockResponse(status_code=200, text=json.dumps(response_text))

    # Mock the requests.get method
    def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)

    # Call the send_request function
    result = send_request(latitude, longitude, api_key, name)

    # Check the result is a pandas DataFrame
    assert isinstance(result, pd.DataFrame)

    # Check the DataFrame contains the expected columns
    expected_columns = ["period", "ghi", "dni", "dhi"]
    assert set(result.columns) == set(expected_columns)

    # Check the DataFrame contains the expected number of rows
    assert len(result) == len(response_text["forecasts"])

    # Check the DataFrame index is a pandas DatetimeIndex
    assert isinstance(result.index, pd.DatetimeIndex)

    # Check the DataFrame index is set to the 'period_end' column
    assert result.index.name == "period_end"

    # Check the DataFrame values match the expected response
    for i, (index, row) in enumerate(result.iterrows()):
        expected_row = response_text["forecasts"][i]
        assert row["period"] == expected_row["period"]
        assert row["ghi"] == expected_row["ghi"]
        assert row["dni"] == expected_row["dni"]
        assert row["dhi"] == expected_row["dhi"]

    # test the response of a rate limit
    mock_response = MockResponse(status_code=429, text=b'')

    # Mock the requests.get method
    def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)

    # Call the send_request function
    result = send_request(latitude, longitude, api_key, name)

    # Check that the DataFrame is empty
    assert result.empty

    # Check that the warning is logged
    assert "Bad response from Solacast API for forecast data." in caplog.text
    assert "429" in caplog.text


def test_send_request_failure(monkeypatch, caplog):
    # set up mock response with error
    def mock_get(url, *args, **kwargs):
        raise RequestException("Network error")

    monkeypatch.setattr("requests.get", mock_get)

    # call the function
    latitude, longitude, api_key, name = (
        37.7749,
        -122.4194,
        "your_api_key",
        "San Francisco",
    )
    result = send_request(latitude, longitude, api_key, name)

    # check that the function returns an empty DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty

    # check that an error was captured in the log
    assert "ERROR" in caplog.text
    assert "Network error" in caplog.text
