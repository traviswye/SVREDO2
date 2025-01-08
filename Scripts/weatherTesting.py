import requests
from datetime import datetime, timedelta

def fetch_weather_data(latitude, longitude, date, time):
    # Initial time print statement
    print(f"Original time: {time}")

    # Combine date and time and convert it into a datetime object
    try:
        datetime_str = f"{date} {time}"
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M%p")
        print(f"Parsed datetime: {datetime_obj}")
    except ValueError as e:
        print(f"Error parsing datetime: {e}")
        return None

    # Set start time to one hour before the game time
    start_time = datetime_obj - timedelta(hours=1)
    end_time = datetime_obj + timedelta(hours=3)

    start_minutely_15 = start_time.strftime("%Y-%m-%dT%H:%M")
    end_minutely_15 = end_time.strftime("%Y-%m-%dT%H:%M")

    print(f"Start time: {start_minutely_15}, End time: {end_minutely_15}")

    # Construct the API URL with the 15-minutely interval and time zone
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
        f"&minutely_15=temperature_2m,relative_humidity_2m,precipitation,precipitation_probability,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
        f"&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FNew_York"
        f"&start_minutely_15={start_minutely_15}&end_minutely_15={end_minutely_15}"
    )

    # Print the API URL for debugging
    print(f"API URL: {url}")

    # Make the API call, ignoring SSL verification for testing purposes
    response = requests.get(url, verify=False)

    # Print the full response for debugging purposes
    print("API Response:")
    data = response.json()
    print(data)

    if response.status_code == 200:
        if "minutely_15" in data and "time" in data["minutely_15"]:
            # Convert response times to datetime objects
            response_times = [datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in data["minutely_15"]["time"]]
            # Find the closest time in the response data
            closest_time = min(response_times, key=lambda t: abs(t - datetime_obj))
            closest_time_str = closest_time.strftime("%Y-%m-%dT%H:%M")

            print(f"Closest time in response: {closest_time_str}")

            idx = data["minutely_15"]["time"].index(closest_time_str)
            weather_data = {
                "Temperature": data["minutely_15"]["temperature_2m"][idx],
                "Humidity": data["minutely_15"]["relative_humidity_2m"][idx],
                "RainProbability": data["minutely_15"]["precipitation_probability"][idx],
                "Rain": data["minutely_15"]["precipitation"][idx],
                "WindSpeed": data["minutely_15"]["wind_speed_10m"][idx],
                "WindDirection": data["minutely_15"]["wind_direction_10m"][idx],
                "WindGusts": data["minutely_15"]["wind_gusts_10m"][idx],
            }

            # Calculate the highest precipitation probability within the first two hours
            two_hours_after_start = datetime_obj + timedelta(hours=2)
            two_hour_window_idxs = [
                i for i, t in enumerate(response_times) if closest_time <= t <= two_hours_after_start
            ]
            if two_hour_window_idxs:
                max_precip_prob = max(data["minutely_15"]["precipitation_probability"][i] for i in two_hour_window_idxs)
                total_rain = sum(data["minutely_15"]["precipitation"][i] for i in two_hour_window_idxs)
            else:
                max_precip_prob = None
                total_rain = None

            return weather_data, max_precip_prob, total_rain
        else:
            print("Minutely data not available for the specific time.")
            return None, None, None
    else:
        print(f"Failed to fetch weather data. Status code: {response.status_code}")
        return None, None, None

# Example usage
latitude = 39.0973  # Latitude for Great American Ball Park
longitude = -84.5085  # Longitude for Great American Ball Park
date = "2024-08-14"  # Example date
time = "6:40PM"  # Example time

weather_data, max_precip_prob, total_rain = fetch_weather_data(latitude, longitude, date, time)

if weather_data:
    print("Weather Data:")
    print(f"Temperature: {weather_data['Temperature']}°F")
    print(f"Humidity: {weather_data['Humidity']}%")
    print(f"Rain Probability at Game Start: {weather_data['RainProbability']}%")
    print(f"Rain Probability first two hours: {max_precip_prob if max_precip_prob is not None else 'N/A'}%")
    print(f"Total Rain first two hours: {total_rain if total_rain is not None else 'N/A'} in")
    print(f"Wind Speed: {weather_data['WindSpeed']} mph")
    print(f"Wind Direction: {weather_data['WindDirection']}°")
    print(f"Wind Gusts: {weather_data['WindGusts']} mph")
else:
    print("No weather data available.")
