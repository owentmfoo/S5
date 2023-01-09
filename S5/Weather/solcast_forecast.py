import requests
import datetime


def send_request(latitude=-1.873331, longitude=55.025538, name='unknown'):
    parameters = {
        'api_key': 'XXX',
        'latitude': latitude,
        'longitude': longitude,
        'hours': 168,
        'format': 'csv'
    }
    if name == 'unknown':
        name = f'lat{latitude}lon{longitude}'

    response = requests.get("https://api.solcast.com.au/world_radiation/forecasts", params=parameters)
    print(name, response.status_code)
    if response.status_code == 200:
        timestamp = datetime.datetime.now()
        timestamp = timestamp.strftime("%Y%m%d%H%M")
        FileName = f"Forecast{timestamp}{name}"
        with open(f'{FileName}.csv', 'wb') as f:
            f.write(response.content)


if __name__ == '__main__':
    send_request(-12.4239, 130.8925, "Darwin_Airport")
    send_request(-19.64, 134.18, "Tennant_Creek_Airport")
    send_request(-23.7951, 133.8890, "Alice_Springs_Airport")
    send_request(-29.03, 134.72, "Coober_Pedy_Airport")
    send_request(-34.9524, 138.5196, "Adelaide_Airport")
    send_request(-31.1558, 136.8054, "Woomera")
    send_request(-16.262330910217, 133.37694753742824, "Daly_Waters")
