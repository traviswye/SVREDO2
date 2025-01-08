import requests
import sys

# Define the date variables
date2 = '24-09-06'
date = '20' + date2

# API endpoints
teamsplits_api = "https://localhost:44346/api/TeamRecSplits"
gamepreviews_api = f"https://localhost:44346/api/GamePreviews/{date2}"
pitcher_api = f'https://localhost:44346/api/Pitchers/'
gameOdds_api = f'https://localhost:44346/api/GameOdds/date/{date}'
blending_api = f"https://localhost:44346/api/Blending/todaysSPHistoryVsRecency?date={date}"

# Function to safely get JSON from a response
def safe_get_json(response):
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Failed to parse JSON response")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

# Function to retrieve the pitcher hand data
def get_pitcher_hand(game_previews):
    pitcher_ids = set()
    for game in game_previews:
        if game.get('homePitcher'):
            pitcher_ids.add(game['homePitcher'])
        if game.get('awayPitcher'):
            pitcher_ids.add(game['awayPitcher'])

    pitcher_hand_dict = {}
    for pitcher_id in pitcher_ids:
        pitcher_api_url = f"{pitcher_api}{pitcher_id}"
        response = requests.get(pitcher_api_url, verify=False)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} for pitcher {pitcher_id}")
            continue
        pitcher_data = safe_get_json(response)
        if pitcher_data and 'throws' in pitcher_data:
            pitcher_hand_dict[pitcher_id] = pitcher_data['throws']
    return pitcher_hand_dict

# Function to get the team splits
def get_team_splits():
    response = requests.get(teamsplits_api, verify=False)
    print(f"TeamSplits API status code: {response.status_code}")
    return safe_get_json(response)

# Function to get game previews
def get_game_previews():
    response = requests.get(gamepreviews_api, verify=False)
    print(f"GamePreviews API status code: {response.status_code}")
    return safe_get_json(response)

# Function to retrieve the pitching advantage data
def get_pitching_advantage():
    pitching_adv_api = f"https://localhost:44346/api/Blending/startingPitcherAdvantage?date={date2}"
    response = requests.get(pitching_adv_api, verify=False)
    print(f"Pitching Advantage API status code: {response.status_code}")
    pitching_data = safe_get_json(response)
    
    pitcher_adv_teams = {}
    for game in pitching_data:
        game_info = game.get("Game", "")
        advantage_info = game.get("Advantage", "")
        score = float(advantage_info.split("by")[-1].strip())
        if "Home" in advantage_info:
            home_team = game_info.split(" vs ")[0].strip()
            pitcher_adv_teams[home_team] = score
        elif "Away" in advantage_info:
            away_team = game_info.split(" vs ")[1].strip()
            pitcher_adv_teams[away_team] = score

    return pitcher_adv_teams

# Function to analyze pitching advantage only
def analyze_pitching_advantage(pitcher_adv_teams):
    strong_list = []
    slight_list = []
    weak_list = []

    for team, score in pitcher_adv_teams.items():
        if score >= 250:
            strong_list.append(team)
        elif score >= 100:
            slight_list.append(team)
        else:
            weak_list.append(team)

    return strong_list, slight_list, weak_list

# Function to categorize teams based on both pitching and lineups
def analyze_pitching_and_lineups(pitcher_adv_teams, teamsplits_data, pitcher_hand_dict, game_previews):
    strong_list = []
    slight_list = []
    weak_list = []

    for game in game_previews:
        home_team = game['homeTeam']
        away_team = game['awayTeam']
        home_pitcher_id = game.get('homePitcher')
        away_pitcher_id = game.get('awayPitcher')

        home_is_lhp = pitcher_hand_dict.get(home_pitcher_id, "RHP") == "LHP"
        away_is_lhp = pitcher_hand_dict.get(away_pitcher_id, "RHP") == "LHP"

        home_team_adv = pitcher_adv_teams.get(home_team, None)
        away_team_adv = pitcher_adv_teams.get(away_team, None)

        if home_team_adv is None:
            home_team_adv = float('-inf')
        if away_team_adv is None:
            away_team_adv = float('-inf')

        # Categorize based on both pitching and lineup performance
        if home_team_adv > away_team_adv:
            sp_adv = f"{home_team} {home_team_adv:.2f}"
            strong_list.append(home_team) if home_team_adv >= 250 else slight_list.append(home_team)
        elif away_team_adv > home_team_adv:
            sp_adv = f"{away_team} {away_team_adv:.2f}"
            strong_list.append(away_team) if away_team_adv >= 250 else slight_list.append(away_team)
        else:
            weak_list.append(home_team if home_team_adv >= away_team_adv else away_team)

    return strong_list, slight_list, weak_list

# Command handler to run the specific analysis
def analyze_data(parameter):
    # Fetch data
    teamsplits_data = get_team_splits()
    game_previews = get_game_previews()
    pitcher_adv_teams = get_pitching_advantage()
    pitcher_hand_dict = get_pitcher_hand(game_previews)

    # Run analysis based on the parameter passed
    if parameter == 'pit':
        # Analyze only pitching advantage
        strong_list, slight_list, weak_list = analyze_pitching_advantage(pitcher_adv_teams)
    elif parameter == 'pitlines':
        # Analyze pitching advantage and lineups
        strong_list, slight_list, weak_list = analyze_pitching_and_lineups(pitcher_adv_teams, teamsplits_data, pitcher_hand_dict, game_previews)
    else:
        print("Invalid parameter passed. Use 'pit' or 'pitlines'.")
        return

    # Print the results
    print(f"\nStrong Teams: {strong_list}")
    print(f"Slight Teams: {slight_list}")
    print(f"Weak Teams: {weak_list}")

# Main function to run the script
if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_data(sys.argv[1])
    else:
        print("Please provide a parameter ('pit' or 'pitlines').")
