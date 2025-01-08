import requests
import urllib3

# Suppress only the insecure request warning for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Define the date variables

date2 = '24-10-14'
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

# # Print top 10 outperformanceScore for each position (with adjustment for catcher)
# for pos, players_list in positions_dict.items():
#     if pos == "C":
#         print(f"\nTop 15 outperformanceScore for {pos}:")
#         print_top_n("outperformanceScore", players_list, n=15)
#     elif pos == "OF":
#         print(f"\nTop 30 outperformanceScore for OF combined:")
#         print_top_n("outperformanceScore", players_list, n=30)
#     elif pos == "UTIL":
#         print(f"\nTop 30 outperformanceScore for UTIL:")
#         print_top_n("outperformanceScore", players_list, n=30)
#     else:
#         print(f"\nTop 15 outperformanceScore for {pos}:")
#         print_top_n("outperformanceScore", players_list, n=15)

# Print top 20 slG_Difference
# print("\nTop 20 slG_Difference:")
# print_top_n("slG_Difference", players, n=20)

# # Print top 20 bA_Difference
# print("\nTop 20 bA_Difference:")
# print_top_n("bA_Difference", players, n=20)

# # Print top 20 outperformanceScore where rostered > 50
# print("\nTop 20 outperformanceScore with rostered > 50:")
# filtered_players = [p for p in players if p['rostered'] > 50]
# print_top_n("outperformanceScore", filtered_players, n=20)

# # Print top 20 outperformanceScore where rostered < 50
# print("\nTop 20 outperformanceScore with rostered < 50:")
# filtered_players = [p for p in players if p['rostered'] < 50]
# print_top_n("outperformanceScore", filtered_players, n=20)

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

def initial_classification(pitcher_adv_teams, value_teams):
    """
    Perform the initial classification of teams based on pitching advantage.
    """
    strong_list = []
    slight_list = []
    weak_list = []
    avoid_list = []

    # Classify teams based on pitching advantage score
    for team, score in pitcher_adv_teams.items():
        if score > 300:
            strong_list.append(team)
        elif 200 < score <= 300:
            slight_list.append(team)
        elif 100 < score <= 200:
            weak_list.append(team)
        elif 0 < score <= 100:
            if team in value_teams:
                weak_list.append(team)
            else:
                avoid_list.append(team)

    print("\nInitial Classification:")
    print(f"Strong: {strong_list}")
    print(f"Slight: {slight_list}")
    print(f"Weak: {weak_list}")
    print(f"Avoid: {avoid_list}")

    return strong_list, slight_list, weak_list, avoid_list

def refine_classification(strong_list, slight_list, weak_list, avoid_list, pitcher_adv_teams):
    """
    Refine the classification lists based on lineup scores and records.
    Avoid list should persist unless specific conditions move teams out.
    """
    # Start by printing current lists before refinement
    print("\nStarting refinement process...")

    # Example refinement conditions
    for team in avoid_list[:]:  # Process a copy of the list to avoid modifying it during iteration
        sp_adv = pitcher_adv_teams.get(team, 0)
        if sp_adv > 100:  # Move the team out of Avoid if its SP advantage rises above a threshold
            avoid_list.remove(team)
            weak_list.append(team)
            print(f"{team} moved from Avoid to Weak due to SP advantage of {sp_adv:.2f}")

    print("\nRefinement Complete:")
    print(f"Strong: {strong_list}")
    print(f"Slight: {slight_list}")
    print(f"Weak: {weak_list}")
    print(f"Avoid: {avoid_list}")

    return strong_list, slight_list, weak_list, avoid_list

def refine_classification_with_locks(strong_list, slight_list, weak_list, avoid_list, locks, pitcher_adv_teams, team_scores, game_previews):
    """
    This function adds teams to the Locks list based on pitching advantage, average team score, and opponent's average team score.
    Teams are added to Locks if:
    - They have a pitching advantage.
    - Their average team score is positive.
    - Their opponent's average team score is negative.
    """
    # Iterate through each game in the previews
    for game in game_previews:
        home_team = game['homeTeam']
        away_team = game['awayTeam']

        # Get the team scores (average scores)
        home_team_avg_score = team_scores.get(home_team, {'total_score': 0.0, 'avg_score': 0.0})['avg_score']
        away_team_avg_score = team_scores.get(away_team, {'total_score': 0.0, 'avg_score': 0.0})['avg_score']

        # Check for pitching advantage and team avg_score conditions
        if home_team in pitcher_adv_teams and pitcher_adv_teams[home_team] > 0 and home_team_avg_score > 0 and away_team_avg_score < 0:
            if home_team not in locks:
                locks.append(home_team)
                print(f"{home_team} added to Locks (Pitching Advantage, Positive Avg Score: {home_team_avg_score}, Negative Opponent Avg Score: {away_team_avg_score})")

        if away_team in pitcher_adv_teams and pitcher_adv_teams[away_team] > 0 and away_team_avg_score > 0 and home_team_avg_score < 0:
            if away_team not in locks:
                locks.append(away_team)
                print(f"{away_team} added to Locks (Pitching Advantage, Positive Avg Score: {away_team_avg_score}, Negative Opponent Avg Score: {home_team_avg_score})")

    print("\nLocks Updated:")
    print(f"Locks: {locks}")
    
    return locks




# Adjust the game analysis function to include the new initial classification step
def game_analysis_with_initial_classification(pitcher_adv_teams, value_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict):
    # Step 1: Initial classification
    strong_list, slight_list, weak_list, avoid_list = initial_classification(pitcher_adv_teams, value_teams)
    
    # Step 2: Refine classification using lineup score, records, etc.
    strong_list, slight_list, weak_list, avoid_list = refine_classification(
        strong_list, slight_list, weak_list, avoid_list, 
        pitcher_adv_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict
    )

    return strong_list, slight_list, weak_list, avoid_list

# Function to handle the entire classification process
def classify_teams(pitcher_adv_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict):
    # Step 1: Initial classification and lock identification
    strong_list, slight_list, weak_list, avoid_list, locks = initial_classification_with_locks(pitcher_adv_teams, team_scores)

    # Step 2: Refinement of lists based on additional logic (records, streaks, etc.)
    strong_list, slight_list, weak_list, avoid_list, locks = refine_classification_with_locks(
        strong_list, slight_list, weak_list, avoid_list, locks, pitcher_adv_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict
    )

    # Final lists after refinement
    print("\nFinal Classification after Refinement:")
    print(f"Strong: {strong_list}")
    print(f"Slight: {slight_list}")
    print(f"Weak: {weak_list}")
    print(f"Avoid: {avoid_list}")
    print(f"Locks: {locks}")

    return strong_list, slight_list, weak_list, avoid_list, locks

def game_analysis(pitcher_adv_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict, game_odds_data, 
                  strong_list, slight_list, weak_list, avoid_list, dawgs_list, locks_list):
    # Function to move a team down one tier (or to Dawgs if odds are positive and the team is about to move to Avoid)
    def move_team_down_one_tier(team, current_tier, positive_odds, reason):
        if current_tier == 'Strong':
            strong_list.remove(team)  # Remove from Strong
            slight_list.append(team)  # Move down to Slight
            print(f"{team} moved down to Slight ({reason})")
        elif current_tier == 'Slight':
            slight_list.remove(team)  # Remove from Slight
            weak_list.append(team)  # Move down to Weak
            print(f"{team} moved down to Weak ({reason})")
        elif current_tier == 'Weak':
            weak_list.remove(team)  # Remove from Weak
            if positive_odds:
                dawgs_list.append(team)  # Add to Dawgs instead of moving to Avoid
                print(f"{team} moved to Dawgs (positive odds despite failing criteria)")
            else:
                avoid_list.append(team)  # Move down to Avoid
                print(f"{team} moved down to Avoid ({reason})")
        elif current_tier == 'Avoid':
            print(f"{team} remains in Avoid ({reason})")  # If already in Avoid, no further action

    # Identify the current tier for the advantage team
    def get_current_tier(team):
        if team in strong_list:
            return 'Strong'
        elif team in slight_list:
            return 'Slight'
        elif team in weak_list:
            return 'Weak'
        elif team in avoid_list:
            return 'Avoid'
        return None

    for game in game_previews:
        home_team = game['homeTeam']
        away_team = game['awayTeam']
        home_pitcher_id = game.get('homePitcher')
        away_pitcher_id = game.get('awayPitcher')

        # Determine if home and away pitchers are RHP or LHP
        home_is_lhp = pitcher_hand_dict.get(home_pitcher_id, "RHP") == "LHP"
        away_is_lhp = pitcher_hand_dict.get(away_pitcher_id, "RHP") == "LHP"

        # Get pitching advantage for home and away teams, using negative infinity for missing data
        home_team_adv = pitcher_adv_teams.get(home_team, float('-inf'))
        away_team_adv = pitcher_adv_teams.get(away_team, float('-inf'))

        # Determine the stronger side for SP advantage
        if home_team_adv > away_team_adv:
            adv_team = home_team
            opposing_team = away_team
        else:
            adv_team = away_team
            opposing_team = home_team

        # Get team splits for both teams
        home_team_splits = next((team for team in teamsplits_data if team['team'] == home_team), {})
        away_team_splits = next((team for team in teamsplits_data if team['team'] == away_team), {})

        # Extract vsHand and home/away records
        home_vs_hand = home_team_splits.get('vsLHP' if away_is_lhp else 'vsRHP', "N/A")
        away_vs_hand = away_team_splits.get('vsLHP' if home_is_lhp else 'vsRHP', "N/A")
        home_home_record = home_team_splits.get('homeRec', "N/A")
        away_away_record = away_team_splits.get('awayRec', "N/A")

        # Get lineup scores for both teams
        home_lineup_score = team_scores.get(home_team, {'total_score': 0.0, 'avg_score': 0.0})
        away_lineup_score = team_scores.get(away_team, {'total_score': 0.0, 'avg_score': 0.0})

        # Check odds
        team_odds = {}
        for odds in game_odds_data:
            if odds['homeTeam'] == home_team or odds['awayTeam'] == away_team:
                team_odds = {
                    'home_odds': {
                        'fanduel': odds.get('fanduelHomeOdds'),
                        'draftkings': odds.get('draftkingsHomeOdds'),
                        'betmgm': odds.get('betmgmHomeOdds')
                    },
                    'away_odds': {
                        'fanduel': odds.get('fanduelAwayOdds'),
                        'draftkings': odds.get('draftkingsAwayOdds'),
                        'betmgm': odds.get('betmgmAwayOdds')
                    }
                }
                break

        # Determine if the odds are positive for the advantage team
        positive_odds = False
        if adv_team == home_team:
            home_odds = team_odds.get('home_odds', {})
            positive_odds = all([odds > 0 for odds in home_odds.values() if odds is not None])
        else:
            away_odds = team_odds.get('away_odds', {})
            positive_odds = all([odds > 0 for odds in away_odds.values() if odds is not None])

        # Determine if records pass
        adv_team_record_check = home_vs_hand if adv_team == home_team else away_vs_hand
        try:
            adv_wins, adv_losses = map(int, adv_team_record_check.split('-'))
            record_check = adv_wins > adv_losses
            home_or_away_record = home_home_record if adv_team == home_team else away_away_record
            record_criteria = int(home_or_away_record.split('-')[0]) > int(home_or_away_record.split('-')[1])
        except (ValueError, KeyError):
            record_check = record_criteria = False

        # Get current tier for the advantage team
        current_tier = get_current_tier(adv_team)

        # Adjust team placement based on conditions
        if record_check and record_criteria:
            print(f"{adv_team} stays in {current_tier} (passed SP adv, lineup, and records)")
        else:
            move_team_down_one_tier(adv_team, current_tier, positive_odds, "failed criteria")

    return strong_list, slight_list, weak_list, avoid_list, dawgs_list, locks_list





def adjust_lists_by_sp_adv(strong_list, slight_list, weak_list, avoid_list, pitcher_adv_teams, teamsplits_data, pitcher_hand_dict, game_previews):
    avoid_list = []  # Reset avoid list as it will be repopulated

    # Helper functions
    def get_team_streak(team_name):
        team_data = next((team for team in teamsplits_data if team['team'] == team_name), None)
        return team_data.get('streak', '') if team_data else ''

    def check_losing_streak(streak):
        return streak.startswith('L') and int(streak[1:]) >= 3

    def check_opponent_vs_hand(adv_team, opponent_team):
        game = next((game for game in game_previews if game['homeTeam'] == adv_team or game['awayTeam'] == adv_team), None)
        if not game:
            return False, None

        opponent_team_splits = next((team for team in teamsplits_data if team['team'] == opponent_team), None)
        if not opponent_team_splits:
            return False, None

        adv_pitcher_id = game['homePitcher'] if game['homeTeam'] == adv_team else game['awayPitcher']
        pitcher_hand = pitcher_hand_dict.get(adv_pitcher_id, "RHP")

        vs_hand_record = opponent_team_splits.get('vsLHP' if pitcher_hand == "LHP" else 'vsRHP', "N/A")
        try:
            wins, losses = map(int, vs_hand_record.split('-'))
            return wins < losses, vs_hand_record, pitcher_hand
        except ValueError:
            return False, vs_hand_record, pitcher_hand

    def move_team_down_tiers(team, current_tier, move_by, failed_conditions):
        if team not in pitcher_adv_teams:
            print(f"Skipping {team} since it doesn't have a pitching advantage.")
            return

        target_tier = min(current_tier + move_by, 3)
        failed_conditions_str = " and ".join(failed_conditions)

        if target_tier == 1:  # Move to slight
            strong_list.remove(team) if team in strong_list else None
            slight_list.append(team)
            print(f"Moving {team} to Slight list (failed {failed_conditions_str})")
        elif target_tier == 2:  # Move to weak
            strong_list.remove(team) if team in strong_list else None
            slight_list.remove(team) if team in slight_list else None
            weak_list.append(team)
            print(f"Moving {team} to Weak list (failed {failed_conditions_str})")
        elif target_tier == 3:  # Move to avoid
            strong_list.remove(team) if team in strong_list else None
            slight_list.remove(team) if team in slight_list else None
            weak_list.remove(team) if team in weak_list else None
            avoid_list.append(team)
            print(f"Moving {team} to Avoid list (failed {failed_conditions_str})")

    # Process teams from weak to strong
    for team in weak_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        failed_conditions = []

        if sp_adv < 100:
            opponent_team = next((game['awayTeam'] if game['homeTeam'] == team else game['homeTeam'] for game in game_previews if game['homeTeam'] == team or game['awayTeam'] == team), None)
            losing_record, opponent_vs_hand, pitcher_hand = check_opponent_vs_hand(team, opponent_team)

            if not losing_record:
                move_by += 1
                failed_conditions.append(f"SP adv < 50")
        
        if check_losing_streak(streak):
            move_by += 1
            failed_conditions.append(f"Losing streak {streak}")

        if move_by > 0:
            move_team_down_tiers(team, 2, move_by, failed_conditions)

    # Handle slight and strong lists similarly
    for team in slight_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        failed_conditions = []

        if sp_adv < 100:
            opponent_team = next((game['awayTeam'] if game['homeTeam'] == team else game['homeTeam'] for game in game_previews if game['homeTeam'] == team or game['awayTeam'] == team), None)
            losing_record, opponent_vs_hand, pitcher_hand = check_opponent_vs_hand(team, opponent_team)

            if not losing_record:
                move_by += 1
                failed_conditions.append("SP adv < 50")

        if check_losing_streak(streak):
            move_by += 1
            failed_conditions.append(f"Losing streak {streak}")

        if move_by > 0:
            move_team_down_tiers(team, 1, move_by, failed_conditions)

    for team in strong_list[:]:
        sp_adv = pitcher_adv_teams.get(team, 0)
        streak = get_team_streak(team)
        move_by = 0
        failed_conditions = []

        if sp_adv < 100:
            opponent_team = next((game['awayTeam'] if game['homeTeam'] == team else game['homeTeam'] for game in game_previews if game['homeTeam'] == team or game['awayTeam'] == team), None)
            losing_record, opponent_vs_hand, pitcher_hand = check_opponent_vs_hand(team, opponent_team)

            if not losing_record:
                move_by += 1
                failed_conditions.append("SP adv < 50")

        if check_losing_streak(streak):
            move_by += 1
            failed_conditions.append(f"Losing streak {streak}")

        if move_by > 0:
            move_team_down_tiers(team, 0, move_by, failed_conditions)

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



def initial_classification_with_locks(pitcher_adv_teams, team_scores):
    strong_list = []
    slight_list = []
    weak_list = []
    avoid_list = []
    locks = []

    # Classify teams based on pitching advantage score
    for team, adv_score in pitcher_adv_teams.items():
        if adv_score >= 300:
            strong_list.append(team)
        elif 200 <= adv_score < 300:
            slight_list.append(team)
        elif 100 <= adv_score < 200:
            weak_list.append(team)
        else:
            avoid_list.append(team)

    # Now check each team's lineup score and compare with the opponent's lineup score to add to Locks list
    for game in game_previews:
        home_team = game['homeTeam']
        away_team = game['awayTeam']

        home_team_score = team_scores.get(home_team, {'total_score': 0.0, 'avg_score': 0.0})['total_score']
        away_team_score = team_scores.get(away_team, {'total_score': 0.0, 'avg_score': 0.0})['total_score']

        # Check if the team is already in one of the initial classification lists before adding to Locks
        if home_team in (strong_list + slight_list + weak_list + avoid_list):
            if home_team_score > 0 and away_team_score < 0:
                locks.append(home_team)

        if away_team in (strong_list + slight_list + weak_list + avoid_list):
            if away_team_score > 0 and home_team_score < 0:
                locks.append(away_team)

    print("\nInitial Classification:")
    print(f"Strong: {strong_list}")
    print(f"Slight: {slight_list}")
    print(f"Weak: {weak_list}")
    print(f"Avoid: {avoid_list}")
    print(f"Lineup Adv and SP adv: {locks}")

    return strong_list, slight_list, weak_list, avoid_list, locks


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


# Main Execution Flow

# Main Execution Flow

# Call the pitching_advantage method and print the teams with an advantage and their score
pitcher_adv_teams = pitching_advantage()
print("\nTeams with Pitching Advantage and their Scores:")
for team, score in pitcher_adv_teams.items():
    print(f"{team}: {score:.2f}")

# Step 1: Get value and chalk output from the ValueModel function
value_output, chalk_output = ValueModel(pitcher_adv_teams, game_odds_data)
print("\nValue Model Output (Positive Odds):", value_output)
print("\nChalk Model Output (Negative Odds):", chalk_output)

# Step 2: Initial classification based on pitching advantage and value_output
strong_list, slight_list, weak_list, avoid_list = initial_classification(pitcher_adv_teams, value_output)

# Step 3: Refine classification (e.g., adjust based on lineup scores or records)
strong_list, slight_list, weak_list, avoid_list = refine_classification(
    strong_list, slight_list, weak_list, avoid_list, pitcher_adv_teams
)

# Step 4: Identify Locks and refine further (based on pitching advantage and team scores)
locks = []
locks = refine_classification_with_locks(strong_list, slight_list, weak_list, avoid_list, locks, pitcher_adv_teams, team_scores, game_previews)


# Final Output of Lists after refinement
print("\nFinal Classification after Refinement:")
print(f"Strong: {strong_list}")
print(f"Slight: {slight_list}")
print(f"Weak: {weak_list}")
print(f"Avoid: {avoid_list}")
print(f"Locks: {locks}")
print('------------------------------------------------------------------------------')

# Step 2: Adjust classifications with game analysis, keeping Locks unchanged
strong_list, slight_list, weak_list, avoid_list, dawgs_list, locks_list = game_analysis(
    pitcher_adv_teams, team_scores, game_previews, teamsplits_data, pitcher_hand_dict, game_odds_data,
    strong_list, slight_list, weak_list, avoid_list, dawgs_list=[], locks_list=locks
)

# Print final output
print("\nFinal Classification after game analysis:")

print(f"Strong: {strong_list}")
print(f"Slight: {slight_list}")
print(f"Weak: {weak_list}")
print(f"Dawgs: {dawgs_list}")
print(f"Avoid: {avoid_list}")


print(f"Specialized lists")
print(f"Lineup Adv and SP adv: {locks}")


