import time
import requests
import random
import warnings
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from joblib import Parallel, delayed
import multiprocessing
from requests.exceptions import ConnectionError

# Suppress warnings globally for the main thread
urllib3.disable_warnings(InsecureRequestWarning)
warnings.simplefilter('ignore', InsecureRequestWarning)

# List of all MLB teams
mlb_teams = [
    "Los Angeles Dodgers"
]

# mlb_teams2 = [
#     "Arizona Diamondbacks", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox", "Chicago Cubs", 
#     "Cleveland Guardians", "Houston Astros", "Kansas City Royals", "Los Angeles Dodgers", 
#     "Milwaukee Brewers", "Minnesota Twins", "New York Mets", "New York Yankees", 
#     "Philadelphia Phillies", "San Diego Padres", "San Francisco Giants", 
#     "Seattle Mariners", "St. Louis Cardinals", "Tampa Bay Rays", "Texas Rangers", "Detroit Tigers"
# ]

# Initialize cumulative variables
best_total_wins = 0
best_total_losses = float('inf')
best_weights = {}
total_pushes = 0  # New variable to track pushes

# Weight ranges to try (you can modify these ranges for more fine-tuned control)
weight_ranges = {
    "AB_R": [0, 0.5, 1, 1.5],
    "AB_H": [0, 0.5, 1, 1.5],
    "PA_HR": [0, 0.5, 1, 1.5],
    "AB_SB": [0, 0.01, 0.05, 0.1],
    "SB_SB_CS": [0, 0.1, 0.5, 1],
    "PA_BB": [0, 0.5, 1, 1.5],
    "AB_SO": [0, 0.1, 0.5, 1],
    "SOW": [0, 0.1, 0.5, 1],
    "BA": [0, 0.5, 1, 1.5],
    "OBP": [0, 0.5, 1, 1.5],
    "SLG": [0, 0.5, 1, 1.5],
    "OPS": [0, 0.5, 1, 1.5],
    "PA_TB": [0, 0.5, 1, 1.5],
    "AB_GDP": [0, 0.1, 0.5, 1],
    "BAbip": [0, 0.5, 1, 1.5],
    "tOPSPlus": [0, 0.5, 1, 1.5],
    "sOPSPlus": [0, 0.5, 1, 1.5]
}

# API result caching
api_cache = {}

# Retry mechanism with exponential backoff and session reuse for optimized connections
session = requests.Session()

def make_request_with_retry(url, retries=5, backoff=0.5):
    if url in api_cache:
        return api_cache[url]
    
    for i in range(retries):
        try:
            response = session.get(url, verify=False)
            if response.status_code == 404:
                return None  # Skip this request if 404
            response.raise_for_status()
            api_cache[url] = response
            return response
        except ConnectionError:
            if i < retries - 1:
                time.sleep(backoff * (2 ** i))  # Exponential backoff
            else:
                raise

# Function to process each team's games
def process_team_games(team_name, weights):
    total_wins = 0
    total_losses = 0
    pushes = 0  # Track pushes

    # Fetch game results for the team
    #response = make_request_with_retry(f"https://localhost:44346/api/GameResults/hometeam/{team_name}")
    response = make_request_with_retry(f"https://localhost:44346/api/GameResults")
    if not response:  # Skip if 404
        return

    games = response.json()

    # Process each game
    for game in games:
        home_pitcher = game['homeSP']
        away_pitcher = game['awaySP']
        f5_result = game['f5Result']  # F5Result: HomeWin, AwayWin, Push

        # Skip games without pitcher info or F5 result
        if not home_pitcher or not away_pitcher or not f5_result:
            continue

        # Compare the pitchers using compare2spCustom endpoint with custom weights
        custom_weights = '&'.join([f"{key}={weights[key]}" for key in weight_ranges.keys()])
        comparison_response = make_request_with_retry(
            f"https://localhost:44346/api/Blending/compare2spCustom?pitcheraId={home_pitcher}&pitcherbId={away_pitcher}&{custom_weights}"
        )

        # Add a small delay to avoid overloading the API
        time.sleep(0.1)

        if not comparison_response:  # Skip if 404
            continue

        comparison_data = comparison_response.json()
        advantage = comparison_data.get('Advantage', '')

        # Process results based on advantage and F5Result
        if away_pitcher in advantage:
            if f5_result == "AwayWin":
                total_wins += 1
            elif f5_result == "HomeWin":
                total_losses += 1
            elif f5_result == "Push":
                pushes += 1

        if home_pitcher in advantage:
            if f5_result == "HomeWin":
                total_wins += 1
            elif f5_result == "AwayWin":
                total_losses += 1
            elif f5_result == "Push":
                pushes += 1

    return total_wins, total_losses, pushes

# Function to sample random weights from the range
def sample_random_weights():
    return {key: random.choice(weight_ranges[key]) for key in weight_ranges}

# Function to process weight combinations in parallel
def process_weight_combination(weights, team):
    warnings.simplefilter('ignore', InsecureRequestWarning)
    wins, losses, pushes = process_team_games(team, weights)
    return wins, losses, pushes, weights

# Batched processing for weight combinations
def batch_process_teams(teams, weights, batch_size=5):
    results = []
    for i in range(0, len(teams), batch_size):
        team_batch = teams[i:i + batch_size]
        batch_results = Parallel(n_jobs=num_cores)(
            delayed(process_weight_combination)(weights, team) for team in team_batch
        )
        time.sleep(1)  # Add a delay between batches to give server breathing time
        results.extend(batch_results)
    return results

# Pre-generate weights to reduce overhead
pre_generated_weights = [sample_random_weights() for _ in range(100)]

# Reduce number of concurrent jobs to prevent socket exhaustion
num_cores = multiprocessing.cpu_count()
# num_cores = min(multiprocessing.cpu_count() // 2, 8)

# Perform batched requests
best_total_wins = 0
best_total_losses = float('inf')
total_pushes = 0
best_weights = {}

for weights in pre_generated_weights:
    results = batch_process_teams(mlb_teams, weights)
    
    # Find the best result
    for wins, losses, pushes, weights in results:
        if wins > best_total_wins or (wins == best_total_wins and losses < best_total_losses):
            best_total_wins = wins
            best_total_losses = losses
            total_pushes = pushes
            best_weights = weights

# Print the best results and corresponding weights
print(f"Best Weights: {best_weights}")
print(f"Total Wins: {best_total_wins}, Total Losses: {best_total_losses}, Total Pushes: {total_pushes}")
