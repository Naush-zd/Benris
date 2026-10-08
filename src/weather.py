import requests


def get_weather(city: str) -> str:
    try:
        location_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        location_data = location_response.json()
        location = location_data.get("results", [None])[0]
        if not location:
            return "City not found."

        forecast_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,relative_humidity_2m,pressure_msl,weather_code",
                "timezone": "auto",
            },
            timeout=10,
        )
        data = forecast_response.json()
    except (requests.RequestException, ValueError):
        return "Unable to connect to the weather service right now."

    try:
        current = data["current"]
        temperature = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        pressure = current["pressure_msl"]
        description = weather_description(current["weather_code"])
    except (KeyError, IndexError, TypeError):
        return "The weather service returned an invalid response."

    return (
        f"The temperature in {location['name']} is {temperature} degrees Celsius with "
        f"{description}. The atmospheric pressure is {pressure} hPa and "
        f"the humidity is {humidity}%."
    )


def weather_description(code: int) -> str:
    descriptions = {
        0: "clear sky",
        1: "mainly clear conditions",
        2: "partly cloudy conditions",
        3: "overcast conditions",
        45: "foggy conditions",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        61: "light rain",
        63: "moderate rain",
        65: "heavy rain",
        71: "light snow",
        73: "moderate snow",
        75: "heavy snow",
        80: "light rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        95: "a thunderstorm",
        96: "a thunderstorm with light hail",
        99: "a thunderstorm with heavy hail",
    }
    return descriptions.get(code, "changing weather")