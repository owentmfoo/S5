import os.path

import pytest
from S5.Weather.solcast_forecast import send_request, to_csv, to_s3
from unittest.mock import MagicMock


# @pytest.mark.parametrize(
#     "latitude, longitude, api_key, expected_status_code",
#     [
#         (51.178882, -1.826215, "<your-api-key>", 200),
#         (41.89021, 12.492231, "<your-api-key>", 200),
#         (27.175145, 78.042142, "<your-api-key>", 200),
#     ],
# )
# def test_send_request(latitude, longitude, api_key, expected_status_code):
#     response = send_request(latitude, longitude, api_key)
#     assert response is not None
#     assert response != b""
#     assert response.startswith(b"Period End Time")
#     assert response.count(b"\n") >= 170  # The response should have at least 170 lines
#     assert response.count(b",") >= 1000  # The response should have at least 1000 commas
#     assert response.count(b"\r") == 0  # The response should not have any \r characters
#     assert response.count(b"\n") == response.count(b"\r\n")  # The response should only have \n characters


@pytest.mark.parametrize(
    "latitude, longitude, api_key, expected_status_code",
    [
        (51.178882, -1.826215, "<your-api-key>", 200),
        (41.89021, 12.492231, "<your-api-key>", 200),
        (27.175145, 45.042142, "<your-api-key>", 429),
    ],
)
def test_send_request(monkeypatch, latitude, longitude, api_key, expected_status_code):
    def mock_requests_get(url, params):
        mock_response = MagicMock()
        mock_response.status_code = expected_status_code
        mock_response.content = b""
        return mock_response

    monkeypatch.setattr("requests.get", mock_requests_get)

    # Test that send_request returns bytes when the API call is successful.
    assert isinstance(send_request(latitude, longitude, api_key), bytes)


def test_to_csv(tmpdir):
    content = b"Period End Time,Period,Period Start Time,Radiation,ghi\n2023-05-08T23:00:00.000Z,1,2023-05-08T22:30:00.000Z,0,0\n2023-05-08T23:30:00.000Z,2,2023-05-08T23:00:00.000Z,0,0\n"
    name = "test_location"
    to_csv(name, content, str(tmpdir))
    file_path = tmpdir.join(os.listdir(tmpdir)[0])
    # assert file_path.check() is True
    with open(file_path, "rb") as f:
        file_content = f.read()
        assert file_content == content


@pytest.mark.skip(reason="requires S3 credentials and bucket access")
def test_to_s3():
    content = b"Period End Time,Period,Period Start Time,Radiation,ghi\n2023-05-08T23:00:00.000Z,1,2023-05-08T22:30:00.000Z,0,0\n2023-05-08T23:30:00.000Z,2,2023-05-08T23:00:00.000Z,0,0\n"
    to_s3("test_location", content, "my-bucket-name")
    # TODO: Check that the file was successfully uploaded to S3
