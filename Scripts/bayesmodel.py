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
mlb_teams = ["Arizona Diamondbacks", "Texas Rangers"]

# Initialize the optimal weights as a starting point
optimal_weights = {
    "AB_R": 0.5, "AB_H": 0.5, "PA_HR": 1.5, "AB_SB": 0.1,
    "SB_SB_CS": 0.5, "PA_BB": 1.5, "AB_SO": 0.1, "SOW": 1,
    "BA": 0.5, "OBP": 1, "SLG": 0.5, "OPS": 1, "PA_TB": 0.5,
    "AB_GDP": 0.5, "BAbip": 0.5, "tOPSPlus": 1.5, "sOPSPlus": 0.5
}

# Define a perturbation factor to vary the weights (adjust as needed)
perturbation_factor = 0.25

# Retry mechanism with exponential backoff
def make_request_with_retry(url, retries=5, backoff=0.5):
    for i in range(retries):
        try:
            response = requests.get(url, verify=False)
            if response.status_code == 404:
                return None  # Skip this request if 404
            response.raise_for_status()
            return response
        except ConnectionError:
            if i < retries - 1:
                time.sleep(backoff * (2 ** i))  # Exponential backoff
            else:
                raise  # If all retries fail, raise the exception

# Function to process each team's games and accumulate the total results
def process_team_games(team_name, weights):
    total_wins = 0
    total_losses = 0

    # Fetch game results for the team
    response = make_request_with_retry(f"https://localhost:44346/api/GameResultsWithOdds/team?teamName={team_name}")
    if not response:  # Skip if 404
        return 0, 0  # Return 0 wins, 0 losses if team data is not available

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

        # Compare the pitchers using compare2spCustom endpoint with custom weights
        custom_weights = '&'.join([f"{key}={weights[key]}" for key in optimal_weights.keys()])
        comparison_response = make_request_with_retry(
            f"https://localhost:44346/api/Blending/compare2spCustom?pitcheraId={pitcher}&pitcherbId={opposing_pitcher}&{custom_weights}"
        )

        # Add a delay to avoid overloading the API
        time.sleep(0.1)

        if not comparison_response:  # Skip if 404
            continue

        comparison_data = comparison_response.json()
        advantage = comparison_data.get('Advantage', '')

        # Increment win/loss based on the result and advantage
        if pitcher in advantage:
            if result == 'W':
                total_wins += 1
            elif result == 'L':
                total_losses += 1

    return total_wins, total_losses

# Function to perturb the optimal weights slightly
def perturb_weights():
    return {key: max(0, value + random.uniform(-perturbation_factor, perturbation_factor) * value) for key, value in optimal_weights.items()}

# Function to process weight combinations in parallel
def process_weight_combination(weights, teams):
    # Suppress warnings in each thread
    urllib3.disable_warnings(InsecureRequestWarning)
    warnings.simplefilter('ignore', InsecureRequestWarning)

    cumulative_wins = 0
    cumulative_losses = 0

    # Process all teams and accumulate wins/losses
    for team in teams:
        wins, losses = process_team_games(team, weights)
        cumulative_wins += wins
        cumulative_losses += losses

    return cumulative_wins, cumulative_losses, weights

# Parallelize the execution of weight combinations
num_cores = 16  # Reduce number of concurrent jobs to prevent socket exhaustion
max_iterations = 1000  # Number of perturbations to test

# Process the weight combinations for all teams together
results = Parallel(n_jobs=num_cores)(
    delayed(process_weight_combination)(perturb_weights(), mlb_teams) for _ in range(max_iterations)
)

# Find the best result across all teams
best_total_wins = 0
best_total_losses = float('inf')
best_weights = {}

for wins, losses, weights in results:
    if wins > best_total_wins or (wins == best_total_wins and losses < best_total_losses):
        best_total_wins = wins
        best_total_losses = losses
        best_weights = weights

# Print the best results and corresponding weights
print(f"Best Weights: {best_weights}")
print(f"Total Wins: {best_total_wins}, Total Losses: {best_total_losses}")
