import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the specific InsecureRequestWarning from urllib3
warnings.simplefilter('ignore', InsecureRequestWarning)

# List of all MLB teams
mlb_teams = [
    "Arizona Diamondbacks", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox", "Chicago Cubs", 
    "Cleveland Guardians", 
    "Houston Astros", "Kansas City Royals", "Los Angeles Dodgers", 
    "Milwaukee Brewers", "Minnesota Twins", "New York Mets", "New York Yankees", 
    "Philadelphia Phillies", "San Diego Padres", "San Francisco Giants", 
    "Seattle Mariners", "St. Louis Cardinals", "Tampa Bay Rays", "Texas Rangers", "Detroit Tigers"
]

# Threshold values
lower_advantage_threshold = 100  # Lower boundary for SP advantage
upper_advantage_threshold = 900  # Upper boundary for SP advantage
odds_threshold = -251  # Skip games with odds worse than this value (e.g., -201 or worse)

# Initialize individual and cumulative variables
cumulative_total_games_with_sp_adv = 0
cumulative_dog_wins = 0
cumulative_dog_loses = 0
cumulative_fav_wins = 0
cumulative_fav_loses = 0
cumulative_total_wins = 0
cumulative_total_loses = 0
cumulative_total_better = 0
cumulative_dog_better = 0
cumulative_fav_better = 0
cumulative_dis_wins = 0
cumulative_dis_losses = 0
cumulative_dis_dog_wins = 0
cumulative_dis_dog_loses = 0
cumulative_dis_fav_wins = 0
cumulative_dis_fav_loses = 0
cumulative_dis_dog_better = 0
cumulative_dis_fav_better = 0

# Array to keep track of failed pitcher comparisons
failed_comparisons = []

# Function to calculate winnings for negative odds (favorites)
def calculate_fav_winnings(odds):
    return 100 * (100 / abs(odds))

# Function to process each team's games
def process_team_games(team_name):
    global cumulative_total_games_with_sp_adv, cumulative_dog_wins, cumulative_dog_loses
    global cumulative_fav_wins, cumulative_fav_loses, cumulative_total_wins, cumulative_total_loses
    global cumulative_total_better, cumulative_dog_better, cumulative_fav_better
    global cumulative_dis_wins, cumulative_dis_losses, cumulative_dis_dog_wins, cumulative_dis_dog_loses
    global cumulative_dis_fav_wins, cumulative_dis_fav_loses, cumulative_dis_dog_better, cumulative_dis_fav_better

    # Initialize team-specific variables
    total_games_with_sp_adv = 0
    dog_wins = 0
    dog_loses = 0
    fav_wins = 0
    fav_loses = 0
    total_wins = 0
    total_loses = 0
    dog_better = 0
    fav_better = 0
    dis_wins = 0
    dis_losses = 0
    dis_dog_wins = 0
    dis_dog_loses = 0
    dis_fav_wins = 0
    dis_fav_loses = 0
    dis_dog_better = 0
    dis_fav_better = 0

    # Fetch game results for the team
    response = requests.get(f"https://localhost:44346/api/GameResultsWithOdds/team?teamName={team_name}", verify=False)

    if response.status_code != 200:
        print(f"Failed to retrieve games for {team_name}. Status code: {response.status_code}")
        return

    games = response.json()

    # Process each game
    for game in games:
        pitcher = game['pitcher']
        opposing_pitcher = game['opposingPitcher']
        result = game['result']
        odds = int(game['odds'])
        
        # Skip games without pitcher info or stats
        if not pitcher or not opposing_pitcher:
            continue

        # Skip games if odds are worse than the threshold
        if odds < odds_threshold:
            print(f"Skipping game: {game['date']} - {team_name}. Odds: {odds} are worse than threshold {odds_threshold}")
            continue

        # Compare the pitchers using compare2sp endpoint
        comparison_response = requests.get(
            f"https://localhost:44346/api/Blending/compare2sp?pitchera={pitcher}&pitcherb={opposing_pitcher}", verify=False
        )
        
        if comparison_response.status_code in (404, 500):
            # Add the failed comparison to the array
            failed_comparisons.append({
                "team": team_name,
                "date": game["date"],
                "pitcher": pitcher,
                "opposing_pitcher": opposing_pitcher,
                "status_code": comparison_response.status_code
            })
            print(f"Skipping game: {game['date']} - {team_name}. Reason: No relevant stats.")
            continue
        
        comparison_data = comparison_response.json()
        advantage = comparison_data.get('Advantage', '')
        advantage_value = float(advantage.split(' ')[-1])  # Extract the advantage score from the string

        # Check if the advantage falls within the specified range
        if lower_advantage_threshold <= advantage_value <= upper_advantage_threshold:
            select_game = True
        else:
            select_game = False

        # If the game is not selected, we continue to the next game
        if not select_game:
            #print(f"Skipping game: {game['date']} - {team_name}. Advantage: {advantage_value}, Odds: {odds}")
            continue

        # If opposing pitcher has the advantage, update disWins/disLosses and skip
        if opposing_pitcher in advantage:
            if result == 'W':
                dis_wins += 1
                if odds > 0:  # As underdog
                    dis_dog_wins += 1
                    dis_dog_better += odds  # Underdog won
                else:  # As favorite
                    dis_fav_wins += 1
                    dis_fav_better += calculate_fav_winnings(odds)  # Favorite won
            elif result == 'L':
                dis_losses += 1
                if odds > 0:  # As underdog
                    dis_dog_loses += 1
                    dis_dog_better -= 100  # Underdog lost
                else:  # As favorite
                    dis_fav_loses += 1
                    dis_fav_better -= 100  # Favorite lost
            continue

        # Increment the number of games where the team had sp_adv
        total_games_with_sp_adv += 1

        # Update win/loss and better variables based on the result and odds
        if result == 'W':
            total_wins += 1
            if odds > 0:  # As underdog
                dog_wins += 1
                dog_better += odds
            else:  # As favorite
                fav_wins += 1
                fav_better += calculate_fav_winnings(odds)
        elif result == 'L':
            total_loses += 1
            if odds > 0:  # As underdog
                dog_loses += 1
                dog_better -= 100
            else:  # As favorite
                fav_loses += 1
                fav_better -= 100

    # Print the current stats for the team
    print(f"\nTeam: {team_name}")
    print(f"Total games with SP advantage: {total_games_with_sp_adv}")
    print(f"Dog Wins: {dog_wins}, Dog Losses: {dog_loses}")
    print(f"Fav Wins: {fav_wins}, Fav Losses: {fav_loses}")
    print(f"Total Wins: {total_wins}, Total Losses: {total_loses}")
    print(f"Dog Better: {dog_better}")
    print(f"Fav Better: {fav_better}")
    print(f"Disadvantaged Wins: {dis_wins}, Disadvantaged Losses: {dis_losses}")
    print(f"Disadvantaged Dog Wins: {dis_dog_wins}, Disadvantaged Dog Losses: {dis_dog_loses}")
    print(f"Disadvantaged Fav Wins: {dis_fav_wins}, Disadvantaged Fav Losses: {dis_fav_loses}")
    print(f"Disadvantaged Dog Better: {dis_dog_better}")
    print(f"Disadvantaged Fav Better: {dis_fav_better}\n")

    # Update cumulative totals
    cumulative_total_games_with_sp_adv += total_games_with_sp_adv
    cumulative_dog_wins += dog_wins
    cumulative_dog_loses += dog_loses
    cumulative_fav_wins += fav_wins
    cumulative_fav_loses += fav_loses
    cumulative_total_wins += total_wins
    cumulative_total_loses += total_loses
    cumulative_dog_better += dog_better
    cumulative_fav_better += fav_better
    cumulative_dis_wins += dis_wins
    cumulative_dis_losses += dis_losses
    cumulative_dis_dog_wins += dis_dog_wins
    cumulative_dis_dog_loses += dis_dog_loses
    cumulative_dis_fav_wins += dis_fav_wins
    cumulative_dis_fav_loses += dis_fav_loses
    cumulative_dis_dog_better += dis_dog_better
    cumulative_dis_fav_better += dis_fav_better

# Loop through each MLB team and process their games
for team in mlb_teams:
    process_team_games(team)

# Print cumulative totals after processing all teams
print(f"\nCumulative Results for All Teams:")
print(f"Total games with SP advantage: {cumulative_total_games_with_sp_adv}")
print(f"Dog Wins: {cumulative_dog_wins}, Dog Losses: {cumulative_dog_loses}")
print(f"Fav Wins: {cumulative_fav_wins}, Fav Losses: {cumulative_fav_loses}")
print(f"Total Wins: {cumulative_total_wins}, Total Losses: {cumulative_total_loses}")
print(f"Dog Better: {cumulative_dog_better}")
print(f"Fav Better: {cumulative_fav_better}")
print(f"Disadvantaged Wins: {cumulative_dis_wins}, Disadvantaged Losses: {cumulative_dis_losses}")
print(f"Disadvantaged Dog Wins: {cumulative_dis_dog_wins}, Disadvantaged Dog Losses: {cumulative_dis_dog_loses}")
print(f"Disadvantaged Fav Wins: {cumulative_dis_fav_wins}, Disadvantaged Fav Losses: {cumulative_dis_fav_loses}")
print(f"Disadvantaged Dog Better: {cumulative_dis_dog_better}")
print(f"Disadvantaged Fav Better: {cumulative_dis_fav_better}\n")

# Print failed comparisons
print(f"\nFailed Comparisons:")
for comparison in failed_comparisons:
    print(f"Date: {comparison['date']}, Team: {comparison['team']}, Pitcher: {comparison['pitcher']}, Opposing Pitcher: {comparison['opposing_pitcher']}, Status Code: {comparison['status_code']}")
