import json

import pandas as pd
import pytest
from requests import RequestException

from S5.Weather.tomorrow_forecast import send_request


@pytest.fixture(scope="session")
def mock_tomorrow_response():
    # set up mock response
    mock_response = {
        "timelines": {
            "minutely": [{
                "time": "2023-05-13T23:05:00Z",
                "values": {"temperature": 20, "humidity": 60},
            }],
            "hourly": [{
                "time": "2023-05-13T23:00:00Z",
                "values": {"temperature": 19, "humidity": 65},
            }],
            "daily": [{
                "time": "2023-05-13T00:00:00Z",
                "values": {"temperatureMax": 25, "temperatureMin": 16},
            }],
        }
    }
    return mock_response


def test_send_request_success(monkeypatch, mock_tomorrow_response, caplog):
    def mock_get(url):
        class MockResponse:

            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = json.dumps(mock_tomorrow_response)

            def json(self):
                return self.json_data

        if "location=37.7749,-122.4194" in url:
            return MockResponse(mock_tomorrow_response, 200)
        else:
            return MockResponse(None, 404)

    monkeypatch.setattr("requests.get", mock_get)

    # call the function
    latitude, longitude, api_key, name = (
        37.7749,
        -122.4194,
        "your_api_key",
        "San Francisco",
    )
    result = send_request(latitude, longitude, api_key, name)

    # check that the function returns a non-empty DataFrame
    assert isinstance(result, pd.DataFrame)
    assert not result.empty

    # check that the returned DataFrame has the expected columns and index
    expected_columns = ["temperature", "humidity", "temperatureMax", "temperatureMin"]
    expected_index = pd.DatetimeIndex(
        ["2023-05-13T23:05:00Z", "2023-05-13T23:00:00Z", "2023-05-13T00:00:00Z"]
    )
    assert result.columns.tolist() == expected_columns
    assert result.index.tolist() == expected_index.tolist()


def test_send_request_failure(monkeypatch, caplog):
    # set up mock response with error
    def mock_get(url):
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
