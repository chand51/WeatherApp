import os
from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"


def fetch_weather(city: str):
    if not WEATHER_API_KEY:
        return None, "Missing WEATHER_API_KEY environment variable."

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            return None, f"City '{city}' was not found."

        try:
            payload = response.json()
            message = payload.get("message")
        except ValueError:
            message = response.text.strip()

        if response.status_code == 401:
            return None, "Invalid API key. Please check WEATHER_API_KEY."
        if message:
            return None, f"Weather service returned an error ({response.status_code}): {message}"
        return None, "Weather service returned an error."
    except requests.exceptions.RequestException:
        return None, "Unable to reach the weather service. Please try again later."

    payload = response.json()
    weather = payload.get("weather", [{}])[0]
    main = payload.get("main", {})
    wind = payload.get("wind", {})

    result = {
        "city": payload.get("name", city),
        "country": payload.get("sys", {}).get("country", ""),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "wind_speed": wind.get("speed"),
        "description": weather.get("description", "").title(),
        "icon_url": f"https://openweathermap.org/img/wn/{weather.get('icon')}@2x.png",
    }

    return result, None


@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    error = None
    city = ""

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            error = "Please enter a city name."
        else:
            weather, error = fetch_weather(city)

    return render_template("index.html", weather=weather, error=error, city=city)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
