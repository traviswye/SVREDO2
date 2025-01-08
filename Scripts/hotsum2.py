import requests
import urllib3

# Suppress only the insecure request warning for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the date variables

date2 = '24-09-21'
date = '20'+date2

# API endpoints
outperformers_api = f"https://localhost:44346/api/HitterLast7/outperformers/{date}"
lineups_api = f"https://localhost:44346/api/Lineups/Actual/{date}"
PredLineups_api = f"https://localhost:44346/api/Lineups/Predictions/date/{date}"
blending_api = f"https://localhost:44346/api/Blending/todaysSPHistoryVsRecency?date={date}"
teamsplits_api = "https://localhost:44346/api/TeamRecSplits"
gamepreviews_api = f"https://localhost:44346/api/GamePreviews/{date2}"
pitcher_api = f'https://localhost:44346/api/Pitchers/'
gameOdds_api = f'https://localhost:44346/api/GameOdds/date/{date}'

# Function to safely get JSON from a response
def safe_get_json(response):
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Failed to parse JSON response")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

# Get the outperformers data
response = requests.get(outperformers_api, verify=False)
print(f"Outperformers API status code: {response.status_code}")
players = safe_get_json(response)

if not players:
    print("No players data retrieved.")
    exit(1)

# Create a dictionary to map bbrefId to a tuple (playerName, outperformanceScore)
player_scores = {p['bbrefId']: (p['playerName'], p['outperformanceScore']) for p in players}

# Get the blending data
response = requests.get(blending_api, verify=False)
print(f"Blending API status code: {response.status_code}")
blending_data = safe_get_json(response)

if not blending_data:
    print("No blending data retrieved.")
    exit(1)

# Create a dictionary to map pitcher IDs to their message, using a default value if message is missing
pitcher_trends = {
    p['pitcher']: p.get('message', p.get('results', 'No data available'))
    for p in blending_data
}

# Get the team splits data
response = requests.get(teamsplits_api, verify=False)
print(f"TeamSplits API status code: {response.status_code}")
teamsplits_data = safe_get_json(response)

if not teamsplits_data:
    print("No team splits data retrieved.")
    exit(1)

# Create a dictionary to map team names to their vsLHP and vsRHP records
team_vs_records = {
    t['team']: {'vsLHP': t['vsLHP'], 'vsRHP': t['vsRHP']}
    for t in teamsplits_data
}

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

# Extract all pitchers from gamePreviews and get their "throws" information
def get_pitcher_hand(game_previews):
    # Collect all unique pitcher IDs from the game previews
    pitcher_ids = set()
    for game in game_previews:
        if game.get('homePitcher'):
            pitcher_ids.add(game['homePitcher'])
        if game.get('awayPitcher'):
            pitcher_ids.add(game['awayPitcher'])

    if not pitcher_ids:
        print("No pitchers found in game previews.")
        return {}

    pitcher_hand_dict = {}

    # Iterate over each pitcher ID and make a request for each one
    for pitcher_id in pitcher_ids:
        # Create the individual request URL for the pitcher
        pitcher_api_url = f"https://localhost:44346/api/Pitchers/{pitcher_id}"

        # Send request to the pitcher API to retrieve data about the pitcher
        response = requests.get(pitcher_api_url, verify=False)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} for pitcher {pitcher_id}")
            print(f"Response content: {response.text}")
            continue

        pitcher_data = safe_get_json(response)

        # Add to the dictionary if the pitcher has "throws" information
        if pitcher_data and 'throws' in pitcher_data:
            pitcher_hand_dict[pitcher_id] = pitcher_data['throws']
        else:
            print(f"Warning: No 'throws' data found for pitcher {pitcher_id}")

    return pitcher_hand_dict

# Call this function to retrieve pitcher hand data
pitcher_hand_dict = get_pitcher_hand(game_previews)

# Function to filter players by position, including logic for UTIL
def filter_by_position(players, positions, exact=False):
    if exact:
        return [p for p in players if any(pos == p['pos'] or p['pos'].startswith(f"{pos},") for pos in positions)]
    return [p for p in players if any(pos in p['pos'] for pos in positions)]

# Function to sort and print the top N results
def print_top_n(stat, players, n=10):
    sorted_players = sorted(players, key=lambda x: x[stat], reverse=True)[:n]
    for p in sorted_players:
        print(f"{p[stat]:.2f} {p['playerName']} {p['team']} {p['pos']} {p['bbrefId']}")

# Function to count positive outperformanceScore by team
def count_positive_scores_by_team(players):
    team_counts = {}
    for player in players:
        if player['outperformanceScore'] > 0:
            team = player['team']
            if team in team_counts:
                team_counts[team] += 1
            else:
                team_counts[team] = 1
    return team_counts

# Positions to filter by, including the new UTIL position
positions_dict = {
    "C": [],
    "1B": [],
    "2B": [],
    "3B": [],
    "SS": [],
    "OF": [],
    "UTIL": []
}

# Categorize players into the appropriate positions, including the new OF category
for player in players:
    player_positions = player['pos'].split(',')
    
    # Normalize LF, CF, RF to OF
    normalized_positions = set()
    for pos in player_positions:
        if pos in ["LF", "CF", "RF"]:
            normalized_positions.add("OF")
        else:
            normalized_positions.add(pos)

    # If the player has more than 2 normalized positions, categorize as UTIL
    if len(normalized_positions) > 2:
        positions_dict["UTIL"].append(player)
    else:
        for pos in normalized_positions:
            if pos in positions_dict:
                positions_dict[pos].append(player)

# Print top 10 outperformanceScore for each position (with adjustment for catcher)
for pos, players_list in positions_dict.items():
    if pos == "C":
        print(f"\nTop 15 outperformanceScore for {pos}:")
        print_top_n("outperformanceScore", players_list, n=15)
    elif pos == "OF":
        print(f"\nTop 30 outperformanceScore for OF combined:")
        print_top_n("outperformanceScore", players_list, n=30)
    elif pos == "UTIL":
        print(f"\nTop 30 outperformanceScore for UTIL:")
        print_top_n("outperformanceScore", players_list, n=30)
    else:
        print(f"\nTop 15 outperformanceScore for {pos}:")
        print_top_n("outperformanceScore", players_list, n=15)

# Print top 20 slG_Difference
print("\nTop 20 slG_Difference:")
print_top_n("slG_Difference", players, n=20)

# Print top 20 bA_Difference
print("\nTop 20 bA_Difference:")
print_top_n("bA_Difference", players, n=20)

# Print top 20 outperformanceScore where rostered > 50
print("\nTop 20 outperformanceScore with rostered > 50:")
filtered_players = [p for p in players if p['rostered'] > 50]
print_top_n("outperformanceScore", filtered_players, n=20)

# Print top 20 outperformanceScore where rostered < 50
print("\nTop 20 outperformanceScore with rostered < 50:")
filtered_players = [p for p in players if p['rostered'] < 50]
print_top_n("outperformanceScore", filtered_players, n=20)

# Count positive outperformanceScore by team and print the results
team_counts = count_positive_scores_by_team(players)
print("\nPositive outperformanceScore counts by team:")
for team, count in team_counts.items():
    print(f"{team} = {count}")

# Function to map ordinal suffixes (1st, 2nd, 3rd, etc.)
def ordinal_suffix(i):
    if 11 <= i % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(i % 10, "th")
    return suffix

# Function to print actual lineups with overperformance scores, with fallback to predicted lineups
def print_actual_or_predicted_lineups_with_scores(predicted_lineups):
    response = requests.get(lineups_api, verify=False)
    actual_lineups = safe_get_json(response) if response.status_code == 200 else []

    actual_lineups_dict = {lineup['team']: lineup for lineup in actual_lineups}

    team_scores = {}  # Dictionary to hold the total and avg score for each team

    for game in game_previews:
        home_team = game['homeTeam']
        away_team = game['awayTeam']

        for team in [home_team, away_team]:
            # Use actual lineup if available, otherwise fall back to predicted lineup
            lineup = actual_lineups_dict.get(team)
            is_predictive = False

            if not lineup:
                lineup = predicted_lineups.get(team)
                is_predictive = True

            if not lineup:
                print(f"Warning: No lineup found for {team} (neither actual nor predicted).")
                continue

            opponent = home_team if team == away_team else away_team
            opposingSP = game['homePitcher'] if team == away_team else game['awayPitcher']
            lhp = bool(game.get('lhp'))

            # Get the blending message for the opposing pitcher
            blending_message = pitcher_trends.get(opposingSP, "No data available")

            # Determine the vsLHP or vsRHP record for the team
            vs_record = team_vs_records.get(team, {}).get('vsLHP' if lhp else 'vsRHP', "No record available")

            # Get the batting order, considering ordinal suffixes
            batting_order = [
                lineup.get(f"batting{i}{ordinal_suffix(i)}", None) for i in range(1, 10)
            ]

            print(f"\nTeam: {team}")
            print(f"Opponent: {opponent}")
            print(f"Opposing SP: {blending_message}")
            if lhp:
                print(f"(Team vs LHP record: {vs_record})")
            else:
                print(f"(Team vs RHP record: {vs_record})")

            total_score = 0
            valid_player_count = 0  # Keep track of players with valid scores (not N/A)

            for i, player_id in enumerate(batting_order, start=1):
                if player_id:  # Check if player_id is not None
                    # Normalize player_id for consistent matching
                    player_id = player_id.strip().lower()
                    player_info = player_scores.get(player_id)

                    if player_info:
                        player_name, score = player_info
                        print(f"Batting {i}: {player_name} ({score:.2f})")
                        total_score += score
                        valid_player_count += 1  # Increment valid player count
                    else:
                        print(f"Batting {i}: {player_id} (N/A)")
                else:
                    print(f"Batting {i}: N/A")

            # Calculate the average score, using valid_player_count instead of 9
            avg_score = total_score / valid_player_count if valid_player_count > 0 else 0

            print(f"\n{team} lineup total = {total_score:.2f}")
            print(f"\n{team} lineup avg = {avg_score:.2f}")
            
            if is_predictive:
                print(f"{team} using Predictive Lineup Service")

            # Store total and avg score in the dictionary
            team_scores[team] = {'total_score': total_score, 'avg_score': avg_score}

    return team_scores  # Return the dictionary with the scores


# Function to get predictive lineups
def get_predictive_lineups():
    response = requests.get(PredLineups_api, verify=False)
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code} for predicted lineups")
        print(f"Response content: {response.text}")
        return {}

    predicted_lineups = safe_get_json(response) or []
    
    # Convert the list of predicted lineups to a dictionary
    return {lineup['team']: lineup for lineup in predicted_lineups}



# New function to fetch and process pitching advantage data
def pitching_advantage():
    # Define the endpoint URL
    pitching_adv_api = f"https://localhost:44346/api/Blending/startingPitcherAdvantage?date={date2}"
    
    # Get the pitching advantage data
    response = requests.get(pitching_adv_api, verify=False)
    print(f"Pitching Advantage API status code: {response.status_code}")
    
    pitching_data = safe_get_json(response)
    
    if not pitching_data:
        print("No pitching advantage data retrieved.")
        return {}

    # Initialize an empty dictionary to store teams with their advantage score
    pitcher_adv_teams = {}

    # Iterate through each game in the response
    for game in pitching_data:
        game_info = game.get("Game", "")
        advantage_info = game.get("Advantage", "")

        if "Not enough data to determine advantage" in advantage_info:
            score = 0  # Set the advantage score to 0 for this case
            print(f"No team has the advantage in {game_info}, look manually.")
        else:
            # Extract the advantage score (the last part of the advantage string)
            try:
                score = float(advantage_info.split("by")[-1].strip())
            except ValueError:
                print(f"Error: Could not extract advantage score for {game_info}.")
                score = 0

        # Determine whether it's the home or away team that has the advantage
        if "Home" in advantage_info:
            home_team = game_info.split(" vs ")[0].strip()
            pitcher_adv_teams[home_team] = score
        elif "Away" in advantage_info:
            away_team = game_info.split(" vs ")[1].strip()
            pitcher_adv_teams[away_team] = score

    return pitcher_adv_teams  # Return the dictionary of teams with their advantage score




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

        # Determine if home and away pitchers are RHP or LHP
        home_is_lhp = pitcher_hand_dict.get(home_pitcher_id, "RHP") == "LHP"
        away_is_lhp = pitcher_hand_dict.get(away_pitcher_id, "RHP") == "LHP"

        # Get pitching advantage for home and away teams
        home_team_adv = pitcher_adv_teams.get(home_team, None)
        away_team_adv = pitcher_adv_teams.get(away_team, None)

        # Safely handle cases where home_team_adv or away_team_adv is None
        if home_team_adv is None:
            home_team_adv = float('-inf')
        if away_team_adv is None:
            away_team_adv = float('-inf')

        # Determine the stronger side for the SP advantage
        if home_team_adv > away_team_adv:
            sp_adv = f"{home_team} {home_team_adv:.2f}"
        elif away_team_adv > home_team_adv:
            sp_adv = f"{away_team} {away_team_adv:.2f}"
        else:
            sp_adv = "No SP advantage data"

        # Get team splits for both teams
        home_team_splits = next((team for team in teamsplits_data if team['team'] == home_team), None)
        away_team_splits = next((team for team in teamsplits_data if team['team'] == away_team), None)

        # Get RHP or LHP data based on pitcher hand information
        if home_team_splits and away_team_splits:
            home_vs_hand = home_team_splits.get('vsLHP' if away_is_lhp else 'vsRHP', "N/A")
            away_vs_hand = away_team_splits.get('vsLHP' if home_is_lhp else 'vsRHP', "N/A")
            home_home_record = home_team_splits.get('homeRec', "N/A")  # Home record for home team
            away_away_record = away_team_splits.get('awayRec', "N/A")  # Away record for away team
        else:
            home_vs_hand = away_vs_hand = home_home_record = away_away_record = "N/A"

        # Get lineup scores for both teams, using total_score and avg_score
        home_lineup_score = team_scores.get(home_team, {'total_score': 0.0, 'avg_score': 0.0})
        away_lineup_score = team_scores.get(away_team, {'total_score': 0.0, 'avg_score': 0.0})

        # Format the game analysis output
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

        # Classification into Strong, Slight, or Weak based on conditions
        adv_team = home_team if home_team_adv > away_team_adv else away_team
        opposing_team = away_team if adv_team == home_team else home_team
        adv_team_hand = home_vs_hand if adv_team == home_team else away_vs_hand
        adv_team_lineup = home_lineup_score if adv_team == home_team else away_lineup_score
        opposing_team_lineup = away_lineup_score if adv_team == home_team else home_lineup_score
        home_or_away_record = home_home_record if adv_team == home_team else away_away_record
        opp_home_or_away_record = away_away_record if adv_team == home_team else home_home_record

        if int(adv_team_hand.split('-')[0]) > int(adv_team_hand.split('-')[1]) and int(home_or_away_record.split('-')[0]) > int(home_or_away_record.split('-')[1]):
            if adv_team_lineup['total_score'] > opposing_team_lineup['total_score'] and adv_team_lineup['avg_score'] > opposing_team_lineup['avg_score']:
                print(f"{adv_team} to Strong list because it passed all conditions (SP adv, lineup, records)")
                strong_list.append(adv_team)
            else:
                print(f"{adv_team} to Slight list because lineup score is lower despite passing SP adv and records")
                slight_list.append(adv_team)
        else:
            print(f"{adv_team} to Weak list because it failed either vsHand or home/away record")
            weak_list.append(adv_team)

        game_outputs.append(game_output)

    print("\nStrong list:")
    print(strong_list)

    print("\nSlight list:")
    print(slight_list)

    print("\nWeak list:")
    print(weak_list)

    return game_outputs, strong_list, slight_list, weak_list  # Return the lists


def adjust_lists_by_sp_adv(strong_list, slight_list, weak_list, pitcher_adv_teams, teamsplits_data, pitcher_hand_dict, game_previews):
    avoid_list = []

    # Helper functions
    def get_team_streak(team_name):
        """Helper function to get the streak value for a team from teamsplits_data."""
        team_data = next((team for team in teamsplits_data if team['team'] == team_name), None)
        if team_data and 'streak' in team_data:
            return team_data['streak']
        return None

    def check_losing_streak(streak):
        """Helper function to check if the streak is L3 or worse."""
        if streak and streak.startswith('L'):
            try:
                losing_streak_count = int(streak[1:])
                return losing_streak_count >= 3
            except ValueError:
                return False
        return False

    def check_opponent_vs_hand(adv_team, opponent_team, pitcher_hand_dict, game_previews):
        """Check if the opponent has a losing record vs the adv team's pitcher hand (LHP or RHP)."""
        # Find the game for the teams
        game = next((game for game in game_previews if game['homeTeam'] == adv_team or game['awayTeam'] == adv_team), None)
        if not game:
            return False, None

        opponent_team_splits = next((team for team in teamsplits_data if team['team'] == opponent_team), None)
        if not opponent_team_splits:
            return False, None

        # Determine if the pitcher is LHP or RHP
        adv_pitcher_id = game['homePitcher'] if game['homeTeam'] == adv_team else game['awayPitcher']
        pitcher_hand = pitcher_hand_dict.get(adv_pitcher_id, "RHP")

        # Check opponent's record vs LHP or RHP
        if pitcher_hand == "LHP":
            vs_hand_record = opponent_team_splits.get('vsLHP', "N/A")
        else:
            vs_hand_record = opponent_team_splits.get('vsRHP', "N/A")

        # Determine if it's a losing record
        try:
            wins, losses = map(int, vs_hand_record.split('-'))
            return wins < losses, vs_hand_record, pitcher_hand
        except ValueError:
            return False, vs_hand_record, pitcher_hand

    def move_team_down_tiers(team, current_tier, move_by, failed_conditions):
        """Move a team down by 'move_by' number of tiers and log which conditions they failed."""
        target_tier = current_tier + move_by
        target_tier = min(target_tier, 3)  # Ensure we don't go lower than the 'avoid' tier (tier 3)

        failed_conditions_str = " and ".join(failed_conditions)

        if target_tier == 1:  # Move to slight
            strong_list.remove(team)
            slight_list.append(team)
            print(f"Moving {team} to Slight list (failed {move_by} condition{'s' if move_by > 1 else ''}: {failed_conditions_str})")
        elif target_tier == 2:  # Move to weak
            if team in strong_list:
                strong_list.remove(team)
            elif team in slight_list:
                slight_list.remove(team)
            weak_list.append(team)
            print(f"Moving {team} to Weak list (failed {move_by} condition{'s' if move_by > 1 else ''}: {failed_conditions_str})")
        elif target_tier == 3:  # Move to avoid
            if team in strong_list:
                strong_list.remove(team)
            elif team in slight_list:
                slight_list.remove(team)
            elif team in weak_list:
                weak_list.remove(team)
            avoid_list.append(team)
            print(f"Moving {team} to Avoid list (failed {move_by} condition{'s' if move_by > 1 else ''}: {failed_conditions_str})")

    # Process the teams starting from the weakest tier to the strongest
    for team in weak_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        failed_conditions = []

        # Check SP advantage condition
        if sp_adv < 50:
            opponent_team = next((game['awayTeam'] if game['homeTeam'] == team else game['homeTeam'] for game in game_previews if game['homeTeam'] == team or game['awayTeam'] == team), None)
            losing_record, opponent_vs_hand, pitcher_hand = check_opponent_vs_hand(team, opponent_team, pitcher_hand_dict, game_previews)
            
            if not losing_record:
                move_by += 1
                failed_conditions.append("SP adv < 50")
            else:
                print(f"Canceled moving {team} to Avoid (failed 1 condition: SP adv < 50; Opponent record vs{pitcher_hand}: {opponent_vs_hand})")

        # Check losing streak condition
        if check_losing_streak(streak):
            move_by += 1
            failed_conditions.append(f"Losing streak ({streak})")

        if move_by > 0:
            move_team_down_tiers(team, 2, move_by, failed_conditions)  # weak = tier 2

    for team in slight_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        failed_conditions = []

        # Check SP advantage condition
        if sp_adv < 50:
            opponent_team = next((game['awayTeam'] if game['homeTeam'] == team else game['homeTeam'] for game in game_previews if game['homeTeam'] == team or game['awayTeam'] == team), None)
            losing_record, opponent_vs_hand, pitcher_hand = check_opponent_vs_hand(team, opponent_team, pitcher_hand_dict, game_previews)
            
            if not losing_record:
                move_by += 1
                failed_conditions.append("SP adv < 50")
            else:
                print(f"Canceled moving {team} to Weak (failed 1 condition: SP adv < 50; Opponent record vs{pitcher_hand}: {opponent_vs_hand})")

        # Check losing streak condition
        if check_losing_streak(streak):
            move_by += 1
            failed_conditions.append(f"Losing streak ({streak})")

        if move_by > 0:
            move_team_down_tiers(team, 1, move_by, failed_conditions)  # slight = tier 1

    for team in strong_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        failed_conditions = []

        # Check SP advantage condition
        if sp_adv < 50:
            opponent_team = next((game['awayTeam'] if game['homeTeam'] == team else game['homeTeam'] for game in game_previews if game['homeTeam'] == team or game['awayTeam'] == team), None)
            losing_record, opponent_vs_hand, pitcher_hand = check_opponent_vs_hand(team, opponent_team, pitcher_hand_dict, game_previews)
            
            if not losing_record:
                move_by += 1
                failed_conditions.append("SP adv < 50")
            else:
                print(f"Canceled moving {team} to Slight (failed 1 condition: SP adv < 50; Opponent record vs{pitcher_hand}: {opponent_vs_hand})")

        # Check losing streak condition
        if check_losing_streak(streak):
            move_by += 1
            failed_conditions.append(f"Losing streak ({streak})")

        if move_by > 0:
            move_team_down_tiers(team, 0, move_by, failed_conditions)  # strong = tier 0

    return strong_list, slight_list, weak_list, avoid_list


# Function to calculate the average odds for a team with special handling for negative odds
def calculate_average_odds(team, game):
    # Determine if the team is home or away
    if game['homeTeam'] == team:
        # Get the home team odds
        odds_list = [game['fanduelHomeOdds'], game['draftkingsHomeOdds'], game['betmgmHomeOdds']]
    elif game['awayTeam'] == team:
        # Get the away team odds
        odds_list = [game['fanduelAwayOdds'], game['draftkingsAwayOdds'], game['betmgmAwayOdds']]
    else:
        return None  # Return None if the team is not found

    # Calculate the average of the absolute values
    abs_avg_odds = sum(abs(odds) for odds in odds_list) / len(odds_list)

    # Count how many odds were negative originally
    negative_count = sum(1 for odds in odds_list if odds < 0)

    # If two or more odds were negative, make the result negative
    if negative_count >= 2:
        avg_odds = -abs_avg_odds
    else:
        avg_odds = abs_avg_odds

    return {team: avg_odds}

# Function to get average odds for teams in a list
def get_avg_odds_for_list(teams_list, game_odds_data):
    team_odds_dict = {}

    # Check the structure of game_odds_data
    if not isinstance(game_odds_data, list):
        print("Error: game_odds_data is not a list. Current type:", type(game_odds_data))
        return team_odds_dict

    for team in teams_list:
        team_odds = None

        # Check if each game in game_odds_data is a dictionary
        for game in game_odds_data:
            if not isinstance(game, dict):
                print(f"Error: Found an invalid game entry. Expected a dictionary but got {type(game)}")
                continue

            # Search for the team's odds in the game odds data
            if game.get('homeTeam') == team or game.get('awayTeam') == team:
                # Calculate average odds for this team (either home or away)
                team_odds = calculate_average_odds(team, game)
                break

        if team_odds:
            team_odds_dict.update(team_odds)
            print(f"{team} average odds: {team_odds[team]:.2f}")
        else:
            print(f"No odds data found for {team}.")

    return team_odds_dict

# Function to calculate the average odds for each list
def print_and_return_avg_odds_lists(strong_list, slight_list, weak_list, avoid_list, game_odds_data):
    print("\nCalculating average odds for Strong list:")
    strong_odds = get_avg_odds_for_list(strong_list, game_odds_data)
    
    print("\nCalculating average odds for Slight list:")
    slight_odds = get_avg_odds_for_list(slight_list, game_odds_data)

    print("\nCalculating average odds for Weak list:")
    weak_odds = get_avg_odds_for_list(weak_list, game_odds_data)

    print("\nCalculating average odds for Avoid list:")
    avoid_odds = get_avg_odds_for_list(avoid_list, game_odds_data)

    return strong_odds, slight_odds, weak_odds, avoid_odds


# Function to calculate the value model based on the pitcher advantage and team odds
def ValueModel(pitcher_adv_teams, game_odds_data):
    value = {}  # To store teams with positive average odds
    chalk = {}  # To store teams with negative average odds

    # Iterate over each team in the pitcher_adv_teams
    for team in pitcher_adv_teams:
        team_odds = None

        # Find the game in game_odds_data where this team is either home or away
        for game in game_odds_data:
            if game['homeTeam'] == team or game['awayTeam'] == team:
                # Calculate average odds for the team
                team_odds = calculate_average_odds(team, game)
                break

        # If odds were found for the team, classify them into value or chalk
        if team_odds:
            avg_odds = team_odds[team]
            if avg_odds > 0:
                value[team] = avg_odds  # Positive odds go to value
            else:
                chalk[team] = avg_odds  # Negative odds go to chalk

    return value, chalk

# Call the pitching_advantage method and print the teams with an advantage and their score
pitcher_adv_teams = pitching_advantage()
print("\nTeams with Pitching Advantage and their Scores:")
for team, score in pitcher_adv_teams.items():
    print(f"{team}: {score:.2f}")


# Get predicted lineups ahead of time
predicted_lineups = get_predictive_lineups()

# Get the scores for each team
team_scores = print_actual_or_predicted_lineups_with_scores(predicted_lineups)

# Print the returned dictionary
print("\nTeam Scores:")
for team, scores in team_scores.items():
    print(f"{team}: Total = {scores['total_score']:.2f}, Avg = {scores['avg_score']:.2f}")


pitcher_adv_teams = pitching_advantage()
print("\nTeams with Pitching Advantage:")
print(pitcher_adv_teams)

# Example call to the method
game_outputs, strong_list, slight_list, weak_list = game_analysis(
    pitcher_adv_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict
)

# Print the formatted output for each game
for game_output in game_outputs:
    for key, value in game_output.items():
        print(f"{key}: {value}")
    print("\n" + "-" * 40 + "\n")


# After generating the strong, slight, and weak lists, call the function to adjust them
strong_list, slight_list, weak_list, avoid_list = adjust_lists_by_sp_adv(
    strong_list, slight_list, weak_list, pitcher_adv_teams, teamsplits_data, pitcher_hand_dict, game_previews,
)

# Call the function to calculate average odds for each list
strong_odds, slight_odds, weak_odds, avoid_odds = print_and_return_avg_odds_lists(
    strong_list, slight_list, weak_list, avoid_list, game_odds_data
)


value_output, chalk_output = ValueModel(pitcher_adv_teams, game_odds_data)

# Print the final lists
print("\nFinal Strong list:")
print(strong_list)

print("\nFinal Slight list:")
print(slight_list)

print("\nFinal Weak list:")
print(weak_list)

print("\nAvoid list:")
print(avoid_list)

print("\nValue:")
print(value_output)

print("\nChalk:")
print(chalk_output)
print(pitcher_adv_teams)

# Create a filtered copy of dict1 with keys that exist in dict2
filtered_dict = {key: value for key, value in pitcher_adv_teams.items() if key in chalk_output}

game_analysis(
    filtered_dict, team_scores, game_previews, teamsplits_data, pitcher_hand_dict
)





# Debugging step: Inspect the structure of the fetched data
#print("Inspecting game_odds_data:", game_odds_data)