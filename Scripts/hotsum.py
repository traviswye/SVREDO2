import requests

# Define the date variables

date2 = '24-09-06'
date = '20'+date2

# API endpoints
outperformers_api = f"https://localhost:44346/api/HitterLast7/outperformers/{date}"
lineups_api = f"https://localhost:44346/api/Lineups/Actual/{date}"
PredLineups_api = f"https://localhost:44346/api/Lineups/Predictions/date/{date}"
blending_api = f"https://localhost:44346/api/Blending/todaysSPHistoryVsRecency?date={date}"
teamsplits_api = "https://localhost:44346/api/TeamRecSplits"
gamepreviews_api = f"https://localhost:44346/api/GamePreviews/{date2}"

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
            for i, player_id in enumerate(batting_order, start=1):
                if player_id:  # Check if player_id is not None
                    # Normalize player_id for consistent matching
                    player_id = player_id.strip().lower()
                    player_info = player_scores.get(player_id)

                    if player_info:
                        player_name, score = player_info
                        print(f"Batting {i}: {player_name} ({score:.2f})")
                        total_score += score
                    else:
                        print(f"Batting {i}: {player_id} (N/A)")
                else:
                    print(f"Batting {i}: N/A")

            avg_score = total_score / 9 if total_score > 0 else 0  # Calculate the average score

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

# Get predicted lineups ahead of time
predicted_lineups = get_predictive_lineups()

# Get the scores for each team
team_scores = print_actual_or_predicted_lineups_with_scores(predicted_lineups)

# Print the returned dictionary
print("\nTeam Scores:")
for team, scores in team_scores.items():
    print(f"{team}: Total = {scores['total_score']:.2f}, Avg = {scores['avg_score']:.2f}")