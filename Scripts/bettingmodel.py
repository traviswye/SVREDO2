import requests

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

# Get the team splits data
response = requests.get(teamsplits_api, verify=False)
print(f"TeamSplits API status code: {response.status_code}")
teamsplits_data = safe_get_json(response)

if not teamsplits_data:
    print("No team splits data retrieved.")
    exit(1)

# Get the game previews for the date
response = requests.get(gamepreviews_api, verify=False)
print(f"GamePreviews API status code: {response.status_code}")
game_previews = safe_get_json(response)

if not game_previews:
    print("No game previews retrieved.")
    exit(1)

# Fetch game odds data and inspect it
response = requests.get(gameOdds_api, verify=False)
print(f"GameOdds API status code: {response.status_code}")
game_odds_data = safe_get_json(response)

if not game_odds_data:
    print("No game odds data retrieved.")
    exit(1)

# Function to retrieve pitcher hand data
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

# Retrieve pitcher hand data
pitcher_hand_dict = get_pitcher_hand(game_previews)

# Fetch and process pitching advantage data
def pitching_advantage():
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

# Analyze game and classify teams into strong, slight, and weak lists
def game_analysis(pitcher_adv_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict):
    game_outputs = []
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

        if home_team_adv > away_team_adv:
            sp_adv = f"{home_team} {home_team_adv:.2f}"
        elif away_team_adv > home_team_adv:
            sp_adv = f"{away_team} {away_team_adv:.2f}"
        else:
            sp_adv = "No SP advantage data"

        home_team_splits = next((team for team in teamsplits_data if team['team'] == home_team), None)
        away_team_splits = next((team for team in teamsplits_data if team['team'] == away_team), None)

        if home_team_splits and away_team_splits:
            home_vs_hand = home_team_splits.get('vsLHP' if away_is_lhp else 'vsRHP', "N/A")
            away_vs_hand = away_team_splits.get('vsLHP' if home_is_lhp else 'vsRHP', "N/A")
            home_home_record = home_team_splits.get('homeRec', "N/A")
            away_away_record = away_team_splits.get('awayRec', "N/A")
        else:
            home_vs_hand = away_vs_hand = home_home_record = away_away_record = "N/A"

        home_lineup_score = team_scores.get(home_team, {'total_score': 0.0, 'avg_score': 0.0})
        away_lineup_score = team_scores.get(away_team, {'total_score': 0.0, 'avg_score': 0.0})

        game_output = {
            'game': f"{home_team} vs {away_team}",
            'SP adv': sp_adv,
            f'{away_team} vs {"LHP" if home_is_lhp else "RHP"}': away_vs_hand,
            f'{home_team} vs {"LHP" if away_is_lhp else "RHP"}': home_vs_hand,
            f'{home_team} @ home': home_home_record,
            f'{away_team} away': away_away_record,
            f'{away_team} lineup': f"Total = {away_lineup_score['total_score']:.2f}, Avg = {away_lineup_score['avg_score']:.2f}",
            f'{home_team} lineup': f"Total = {home_lineup_score['total_score']:.2f}, Avg = {home_lineup_score['avg_score']:.2f}"
        }

        adv_team = home_team if home_team_adv > away_team_adv else away_team
        opposing_team = away_team if adv_team == home_team else home_team
        adv_team_hand = home_vs_hand if adv_team == home_team else away_vs_hand
        adv_team_lineup = home_lineup_score if adv_team == home_team else away_lineup_score
        opposing_team_lineup = away_lineup_score if adv_team == home_team else home_lineup_score
        home_or_away_record = home_home_record if adv_team == home_team else away_away_record

        if int(adv_team_hand.split('-')[0]) > int(adv_team_hand.split('-')[1]) and int(home_or_away_record.split('-')[0]) > int(home_or_away_record.split('-')[1]):
            if adv_team_lineup['total_score'] > opposing_team_lineup['total_score'] and adv_team_lineup['avg_score'] > opposing_team_lineup['avg_score']:
                strong_list.append(adv_team)
            else:
                slight_list.append(adv_team)
        else:
            weak_list.append(adv_team)

        game_outputs.append(game_output)

    return game_outputs, strong_list, slight_list, weak_list

# Adjust the lists (strong, slight, weak) based on certain conditions
def adjust_lists_by_sp_adv(strong_list, slight_list, weak_list, pitcher_adv_teams, teamsplits_data, pitcher_hand_dict, game_previews):
    avoid_list = []
    def get_team_streak(team_name):
        team_data = next((team for team in teamsplits_data if team['team'] == team_name), None)
        return team_data.get('streak', None) if team_data else None

    def move_team_down_tiers(team, current_tier, move_by, failed_conditions):
        target_tier = current_tier + move_by
        if target_tier == 1:
            strong_list.remove(team)
            slight_list.append(team)
        elif target_tier == 2:
            if team in strong_list:
                strong_list.remove(team)
            slight_list.remove(team)
            weak_list.append(team)
        elif target_tier == 3:
            if team in strong_list:
                strong_list.remove(team)
            elif team in slight_list:
                slight_list.remove(team)
            elif team in weak_list:
                weak_list.remove(team)
            avoid_list.append(team)

    # Process teams
    for team in weak_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        if sp_adv < 50:
            move_by += 1
        if streak and streak.startswith('L'):
            move_by += 1
        if move_by > 0:
            move_team_down_tiers(team, 2, move_by, [])

    for team in slight_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        if sp_adv < 50:
            move_by += 1
        if streak and streak.startswith('L'):
            move_by += 1
        if move_by > 0:
            move_team_down_tiers(team, 1, move_by, [])

    for team in strong_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        if sp_adv < 50:
            move_by += 1
        if streak and streak.startswith('L'):
            move_by += 1
        if move_by > 0:
            move_team_down_tiers(team, 0, move_by, [])

    return strong_list, slight_list, weak_list, avoid_list

# Calculate average odds for a team with special handling for negative odds
def calculate_average_odds(team, game):
    odds_list = [game.get(f'{team}Odds') for team in ['fanduelHome', 'draftkingsHome', 'betmgmHome']] if game['homeTeam'] == team else \
                [game.get(f'{team}Odds') for team in ['fanduelAway', 'draftkingsAway', 'betmgmAway']]
    abs_avg_odds = sum(abs(odds) for odds in odds_list) / len(odds_list)
    negative_count = sum(1 for odds in odds_list if odds < 0)
    return -abs_avg_odds if negative_count >= 2 else abs_avg_odds

# Get average odds for a list of teams
def get_avg_odds_for_list(teams_list, game_odds_data):
    team_odds_dict = {}
    for team in teams_list:
        for game in game_odds_data:
            if game['homeTeam'] == team or game['awayTeam'] == team:
                team_odds = calculate_average_odds(team, game)
                if team_odds:
                    team_odds_dict[team] = team_odds
    return team_odds_dict

# Calculate average odds for the strong, slight, weak, and avoid lists
def print_and_return_avg_odds_lists(strong_list, slight_list, weak_list, avoid_list, game_odds_data):
    strong_odds = get_avg_odds_for_list(strong_list, game_odds_data)
    slight_odds = get_avg_odds_for_list(slight_list, game_odds_data)
    weak_odds = get_avg_odds_for_list(weak_list, game_odds_data)
    avoid_odds = get_avg_odds_for_list(avoid_list, game_odds_data)

    return strong_odds, slight_odds, weak_odds, avoid_odds

# Value Model calculation based on pitcher advantage and odds
def ValueModel(pitcher_adv_teams, game_odds_data):
    value, chalk = {}, {}
    for team in pitcher_adv_teams:
        for game in game_odds_data:
            if game['homeTeam'] == team or game['awayTeam'] == team:
                team_odds = calculate_average_odds(team, game)
                if team_odds > 0:
                    value[team] = team_odds
                else:
                    chalk[team] = team_odds
    return value, chalk

# Call the pitching_advantage method and print the teams with an advantage and their score
pitcher_adv_teams = pitching_advantage()
print("\nTeams with Pitching Advantage and their Scores:")
for team, score in pitcher_adv_teams.items():
    print(f"{team}: {score:.2f}")

# Example call to the method
game_outputs, strong_list, slight_list, weak_list = game_analysis(
    pitcher_adv_teams, {}, game_previews, teamsplits_data, pitcher_hand_dict
)

# Print the formatted output for each game
for game_output in game_outputs:
    for key, value in game_output.items():
        print(f"{key}: {value}")
    print("\n" + "-" * 40 + "\n")

# Adjust lists based on SP advantage and team records
strong_list, slight_list, weak_list, avoid_list = adjust_lists_by_sp_adv(
    strong_list, slight_list, weak_list, pitcher_adv_teams, teamsplits_data, pitcher_hand_dict, game_previews
)

# Calculate average odds for each list
strong_odds, slight_odds, weak_odds, avoid_odds = print_and_return_avg_odds_lists(
    strong_list, slight_list, weak_list, avoid_list, game_odds_data
)

# Value and chalk model output
value_output, chalk_output = ValueModel(pitcher_adv_teams, game_odds_data)

# Print final lists
print("\nFinal Strong list:", strong_list)
print("\nFinal Slight list:", slight_list)
print("\nFinal Weak list:", weak_list)
print("\nAvoid list:", avoid_list)
print("\nValue teams:", value_output)
print("\nChalk teams:", chalk_output)
