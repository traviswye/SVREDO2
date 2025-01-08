import requests

# Define the base URL for the API
base_url = "https://localhost:44346/api"

# Define the date you want to query
query_date = "2024-09-07"
query_date2 = "24-09-07"


# Endpoints
game_previews_url = f"{base_url}/GamePreviews/{query_date2}"
pitcher_history_vs_recency_url = f"{base_url}/Blending/todaysSPHistoryVsRecency?date={query_date}"
pitcher_advantage_url = f"{base_url}/Blending/startingPitcherAdvantage?date={query_date}"

def get_json_response(url):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()  # Try to parse JSON
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Error occurred during request: {err}")
    except ValueError:
        print(f"Response content is not valid JSON: {response.text}")
    return None  # Return None if there's an error

def format_advantage_message(home_team, away_team, pitcher, advantage_value, is_home):
    if 0 <= advantage_value <= 100:
        advantage_type = "slight"
    elif 100.0001 <= advantage_value <= 250:
        advantage_type = "definite"
    else:
        advantage_type = "Massive"

    team = home_team if is_home else away_team
    return f"{team} have a {advantage_type} pitching advantage: {pitcher} by {advantage_value:.2f}"

def format_recency_message(pitcher, recency_data):
    if not recency_data:
        return f"{pitcher} does not have a trend, his last 28-day split is not available - possibly has not pitched in last month, possibly small season sample size."
    
    # Check if all trend values exist and are 0.0, indicating a small sample size
    ba_trend = recency_data.get('bA_Trend', None)
    obp_trend = recency_data.get('obP_Trend', None)
    slg_trend = recency_data.get('slG_Trend', None)

    if ba_trend == 0 and obp_trend == 0 and slg_trend == 0:
        return f"{pitcher} pitchers season totals are all from last 28 days. Small sample size."

    return recency_data.get('message', f"{pitcher} does not have a trend message available.")


# Fetch data from the API endpoints
game_previews = get_json_response(game_previews_url)
pitcher_history_vs_recency = get_json_response(pitcher_history_vs_recency_url)
pitcher_advantage = get_json_response(pitcher_advantage_url)

# Check if all responses were successful
if game_previews and pitcher_history_vs_recency and pitcher_advantage:
    # Create a dictionary to hold the recency data by pitcher
    recency_data = {item['pitcher']: item for item in pitcher_history_vs_recency}

    # Iterate through game previews and match data
    for game in game_previews:
        home_pitcher = game['homePitcher']
        away_pitcher = game['awayPitcher']
        
        # Fetch the corresponding advantage details
        advantage = next((adv for adv in pitcher_advantage if adv['Game'] == f"{game['homeTeam']} vs {game['awayTeam']}"), None)
        
        # Fetch recency data for home and away pitchers
        home_pitcher_recency = recency_data.get(home_pitcher, {})
        away_pitcher_recency = recency_data.get(away_pitcher, {})
        
        # Print the combined data for each game
        print(f"Time: {game['time']}")
        print(f"Home Team: {game['homeTeam']}")
        print(f"Away Team: {game['awayTeam']}")
        print(f"Venue: {game['venue']}")
        print(f"Home Pitcher: {home_pitcher}")
        print(format_recency_message(home_pitcher, home_pitcher_recency))
        print(f"Away Pitcher: {away_pitcher}")
        print(format_recency_message(away_pitcher, away_pitcher_recency))
        if advantage:
            advantage_value_str = advantage['Advantage'].split('by')[-1].strip()
            advantage_value = float(advantage_value_str)
            is_home = "(Home)" in advantage['Advantage']
            advantage_message = format_advantage_message(game['homeTeam'], game['awayTeam'], home_pitcher if is_home else away_pitcher, advantage_value, is_home)
            print(advantage_message)
        print("\n" + "-"*50 + "\n")
else:
    print("Failed to retrieve data from one or more endpoints.")