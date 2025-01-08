import requests
import sys
import urllib3

# Suppress only the insecure request warning for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

date2 = '2024-09-18'
# Define the endpoint
evaluation_endpoint = f'https://localhost:44346/api/Evaluation/evaluateNRFI/{date2}'

# Fetch data from the evaluation endpoint
response = requests.get(evaluation_endpoint, verify=False)  # verify=False to ignore SSL certs
if response.status_code == 200:
    games_data = response.json()
else:
    print(f"Failed to fetch data from evaluation endpoint: {response.status_code}")
    exit()

# Process and store the data
games_list = []

for game in games_data:
    # Check if either pitcher is missing by verifying if 'stats' is not None
    if not game.get('homePitcher') or not game['homePitcher'].get('stats') or not game.get('awayPitcher') or not game['awayPitcher'].get('stats'):
        print(f"Skipping game {game['homeTeam']} vs {game['awayTeam']}: NO PITCHER ANNOUNCED FOR AT LEAST ONE TEAM AVOID")
        continue

    # Safely access pitcher stats
    home_pitcher_fip = game['homePitcher']['stats'].get('fip', None)
    away_pitcher_fip = game['awayPitcher']['stats'].get('fip', None)
    
    # Handle cases where the first inning stats might be missing
    if game['homePitcher'].get('firstInningStats') is None or game['awayPitcher'].get('firstInningStats') is None:
        print(f"Skipping game {game['homeTeam']} vs {game['awayTeam']}: One of the starters has no 1st inning data")
        continue

    home_pitcher_1st_era = game['homePitcher']['firstInningStats'].get('era', None)
    away_pitcher_1st_era = game['awayPitcher']['firstInningStats'].get('era', None)
    
    home_pitcher_hr9 = game['homePitcher']['stats'].get('hR9', None)
    away_pitcher_hr9 = game['awayPitcher']['stats'].get('hR9', None)
    
    # If any of the stats are missing, set them as "N/A"
    combined_fip = (home_pitcher_fip + away_pitcher_fip) / 2 if home_pitcher_fip is not None and away_pitcher_fip is not None else "N/A"
    combined_1st_era = (home_pitcher_1st_era + away_pitcher_1st_era) / 2 if home_pitcher_1st_era is not None and away_pitcher_1st_era is not None else "N/A"
    combined_hr9 = (home_pitcher_hr9 + away_pitcher_hr9) / 2 if home_pitcher_hr9 is not None and away_pitcher_hr9 is not None else "N/A"
    
    # Calculate the combined runs per first inning for both teams
    combined_runs_per_first = game['homeTeamNRFI']['runsAtHome'] + game['awayTeamNRFI']['runsAtAway']

    # Extract venue information
    venue = game['venue']
    park_factor_rating = game['venueDetails']['parkFactorRating']
    park_hr_rating = game['venueDetails']['hr']
    roof_type = game['venueDetails'].get('roofType', "N/A")
    temperature = game['venueDetails'].get('temperature', "N/A")
    humidity = game['venueDetails'].get('humidity', "N/A")
    rain_probability = game['venueDetails'].get('rainProbability', "N/A")
    rain_prob_2hr = game['venueDetails'].get('rainProb2hr', "N/A")
    total_rain = game['venueDetails'].get('totalRain', "N/A")
    wind_speed = game['venueDetails'].get('windSpeed', "N/A")
    wind_gusts = game['venueDetails'].get('windGusts', "N/A")
    wind_description = game['venueDetails'].get('windDescription', "N/A")


    # Store the results in a dictionary
    game_summary = {
        "matchup": f"{game['homeTeam']} vs {game['awayTeam']}",
        "home_pitcher": game['homePitcher']['stats']['bbrefId'],
        "away_pitcher": game['awayPitcher']['stats']['bbrefId'],
        "combined_runs_per_first": combined_runs_per_first,
        "home_pitcher_fip" : home_pitcher_fip,
        "away_pitcher_fip" : away_pitcher_fip,
        "combined_fip": combined_fip,
        "homePitcher_1st_era" : home_pitcher_1st_era,
        "awayPitcher_1st_era" : away_pitcher_1st_era,
        "combined_1st_era": combined_1st_era,
        "combined_hr9": combined_hr9,
        "venue": venue,
        "park_factor_rating": park_factor_rating,
        "park_hr_rating": park_hr_rating,
        "roof_type": roof_type,
        "temperature": temperature,
        "humidity": humidity,
        "rain_probability": rain_probability,
        "rain_prob_2hr": rain_prob_2hr,
        "total_rain": total_rain,
        "wind_speed": wind_speed,
        "wind_gusts": wind_gusts,
        "wind_description": wind_description
    }
    games_list.append(game_summary)

# Sort the games by the lowest 1st Inning Runs first
games_list = sorted(games_list, key=lambda x: x.get('combined_runs_per_first', float('inf')))

# Output the results for each game
for game in games_list:
    print(f"{game['matchup']}")
    print(f"{game['matchup'].split(' vs ')[0]} pitcher: {game['home_pitcher']}")
    print(f"{game['matchup'].split(' vs ')[1]} pitcher: {game['away_pitcher']}")
    print(f"Combined 1st Inning Runs on Avg: {game['combined_runs_per_first']:.2f}")
    print(f"Home Pitchers FIP: {game['home_pitcher_fip']}")
    print(f"Away Pitchers FIP: {game['away_pitcher_fip']}")
    print(f"Home Pitcher ERA 1st Inning: {game['homePitcher_1st_era']}")
    print(f"Away Pitcher ERA 1st Inning: {game['awayPitcher_1st_era']}")
    print(f"Combined Pitchers FIP: {game['combined_fip']}")
#    print(f"Combined ERA 1st Inning: {game['combined_1st_era']}")
    print(f"Combined HR/9: {game['combined_hr9']}")
    print(f"Venue: {game['venue']}")
    print(f"Park Factor Rating: {game['park_factor_rating']}")
    print(f"Park HR Rating: {game['park_hr_rating']}")
    print(f"Roof Type: {game['roof_type']}")
    print(f"Temperature: {game['temperature']}°F")
    print(f"Humidity: {game['humidity']}%")
    print(f"Chance of Rain at Game Start: {game['rain_probability']}%")
    print(f"Chance of Rain First 2 Hours: {game['rain_prob_2hr']}%")
    print(f"Total Rain First 2 Hours: {game['total_rain']} in")
    print(f"Wind Speed: {game['wind_speed']}mph")
    print(f"Wind Gusts: {game['wind_gusts']}mph")
    print(f"Wind: {game['wind_description']}")
    print("\n")
