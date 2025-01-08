import time
import requests
import warnings
import random
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from joblib import Parallel, delayed
import multiprocessing
from requests.exceptions import ConnectionError

# Suppress warnings globally for the main thread
urllib3.disable_warnings(InsecureRequestWarning)
warnings.simplefilter('ignore', InsecureRequestWarning)

# List of all MLB teams
mlb_teams = ["Los Angeles Dodgers"]

# Initialize cumulative variables
best_total_wins = 0
best_total_losses = float('inf')
best_weights = {}
total_pushes = 0  # New variable to track pushes

# Weight ranges to try
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
session = requests.Session()

# Retry mechanism with exponential backoff
def make_request_with_retry(url, retries=5, backoff=0.5):
    if url in api_cache:
        return api_cache[url]
    
    for i in range(retries):
        try:
            response = session.get(url, verify=False)
            if response.status_code == 404:
                return None  # Skip if 404
            response.raise_for_status()
            api_cache[url] = response
            return response
        except ConnectionError:
            if i < retries - 1:
                time.sleep(backoff * (2 ** i))  # Exponential backoff
            else:
                raise

# Function to process each team's games
def process_game_comparison(home_pitcher, away_pitcher, f5_result, weights):
    # Compare the pitchers using compare2spCustom endpoint with custom weights
    custom_weights = '&'.join([f"{key}={weights[i]}" for i, key in enumerate(weight_ranges)])
    comparison_response = make_request_with_retry(
        f"https://localhost:44346/api/Blending/compare2spCustom?pitcheraId={home_pitcher}&pitcherbId={away_pitcher}&{custom_weights}"
    )
    if not comparison_response:
        return 0, 0, 0  # No data for this game

    comparison_data = comparison_response.json()
    advantage = comparison_data.get('Advantage', '')

    # Process results based on advantage and F5Result
    total_wins = total_losses = pushes = 0
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

# Function to process games in parallel
def process_team_games(team_name, weights, games):
    results = Parallel(n_jobs=num_cores)(
        delayed(process_game_comparison)(game['homeSP'], game['awaySP'], game['f5Result'], weights)
        for game in games if game['homeSP'] and game['awaySP'] and game['f5Result']
    )

    # Aggregate the results
    total_wins = sum(result[0] for result in results)
    total_losses = sum(result[1] for result in results)
    pushes = sum(result[2] for result in results)

    return total_wins, total_losses, pushes

# Function to fetch all game results in one request
def fetch_game_results():
    response = make_request_with_retry(f"https://localhost:44346/api/GameResults")
    if not response:
        return []
    return response.json()

# Function to sample random weights from the range
def sample_random_weights():
    return [random.choice(weight_ranges[key]) for key in weight_ranges]

# Pre-generate weights to reduce overhead
pre_generated_weights = [sample_random_weights() for _ in range(100)]

# Reduce number of concurrent jobs to prevent socket exhaustion
num_cores = multiprocessing.cpu_count()

# Perform batched requests
best_total_wins = 0
best_total_losses = float('inf')
total_pushes = 0
best_weights = {}

# Fetch all game results once
games = fetch_game_results()

# Test different weights in parallel
for weights in pre_generated_weights:
    wins, losses, pushes = process_team_games("Los Angeles Dodgers", weights, games)
    
    # Find the best result
    if wins > best_total_wins or (wins == best_total_wins and losses < best_total_losses):
        best_total_wins = wins
        best_total_losses = losses
        total_pushes = pushes
        best_weights = weights

# Print the best results and corresponding weights
print(f"Best Weights: {best_weights}")
print(f"Total Wins: {best_total_wins}, Total Losses: {best_total_losses}, Total Pushes: {total_pushes}")
