import time
import requests
import warnings
import random
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from joblib import Parallel, delayed
import multiprocessing
from requests.exceptions import ConnectionError
from skopt import gp_minimize
from skopt.space import Real

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

# Define the weight bounds for Bayesian Optimization
weight_bounds = [
    Real(0, 1.5),  # AB_R
    Real(0, 1.5),  # AB_H
    Real(0, 1.5),  # PA_HR
    Real(0.01, 0.1),  # AB_SB
    Real(0.1, 1),  # SB_SB_CS
    Real(0, 1.5),  # PA_BB
    Real(0, 1),  # AB_SO
    Real(0, 1),  # SOW
    Real(0, 1.5),  # BA
    Real(0, 1.5),  # OBP
    Real(0, 1.5),  # SLG
    Real(0, 1.5),  # OPS
    Real(0, 1.5),  # PA_TB
    Real(0.1, 1),  # AB_GDP
    Real(0, 1.5),  # BAbip
    Real(0.5, 1.5),  # tOPSPlus
    Real(0.5, 1.5)  # sOPSPlus
]

# Define weight ranges (needed for weight generation and processing)
weight_ranges = list(weight_bounds)

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
def process_team_games(weights, games):
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

# Define the optimization function to minimize (losses - wins)
def optimize_weights(weight_values):
    global best_total_wins, best_total_losses, total_pushes, best_weights

    wins, losses, pushes = process_team_games(weight_values, games)
    
    # Higher wins and lower losses = better score (we want to minimize losses - wins)
    score = losses - wins

    # Keep track of the best weights
    if wins > best_total_wins or (wins == best_total_wins and losses < best_total_losses):
        best_total_wins = wins
        best_total_losses = losses
        total_pushes = pushes
        best_weights = weight_values

    return score  # Return losses - wins as the score to minimize

# Bayesian optimization using skopt
def bayesian_optimization():
    result = gp_minimize(optimize_weights, weight_bounds, n_calls=100, random_state=42)
    return result

# Reduce number of concurrent jobs to prevent socket exhaustion
num_cores = multiprocessing.cpu_count()

# Perform the optimization
best_total_wins = 0
best_total_losses = float('inf')
total_pushes = 0
best_weights = {}

# Fetch all game results once
games = fetch_game_results()

# Run Bayesian optimization to find the best weights
result = bayesian_optimization()

# Print the best results and corresponding weights
print(f"Best Weights: {best_weights}")
print(f"Total Wins: {best_total_wins}, Total Losses: {best_total_losses}, Total Pushes: {total_pushes}")
