import math
import json
import requests
from datetime import datetime

def calculate_win_probability(home_runs, away_runs):
    """
    Calculate win probability based on expected runs.
    Uses a modified Pythagorean expectation formula.
    """
    run_diff = home_runs - away_runs
    # Convert run differential to win probability using logistic function
    return 1 / (1 + math.exp(-0.8 * run_diff))  # 0.8 is a scaling factor based on MLB data

def calculate_odds(probability):
    """
    Convert probability to American, Decimal, and Fractional odds
    """
    if probability > 0.5:
        american = -100 * (probability / (1 - probability))
        decimal = 1 + (1 - probability) / probability
    else:
        american = 100 * ((1 - probability) / probability)
        decimal = 1 + probability / (1 - probability)
    
    return {
        'american': round(american),
        'decimal': round(decimal, 2),
        'probability': round(probability * 100, 1)
    }

def analyze_game(game):
    """
    Analyze a single game and return betting odds
    """
    home_runs = game['homeTeam']['adjustedExpectedRuns']
    away_runs = game['awayTeam']['adjustedExpectedRuns']
    run_diff = game['runDifferential']
    
    # Calculate win probability using expected runs
    win_prob = calculate_win_probability(home_runs, away_runs)
    
    # Calculate odds for both teams
    home_odds = calculate_odds(win_prob)
    away_odds = calculate_odds(1 - win_prob)
    
    return {
        'gameId': game['gameId'],
        'homeTeam': {
            'team': game['homeTeam']['team'],
            'expectedRuns': round(home_runs, 2),
            'odds': home_odds
        },
        'awayTeam': {
            'team': game['awayTeam']['team'],
            'expectedRuns': round(away_runs, 2),
            'odds': away_odds
        },
        'runDifferential': round(run_diff, 2)
    }

def fetch_and_analyze_games(date=None):
    """
    Fetch data from API and analyze all games
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
        
    url = f'https://localhost:44346/api/Blending/adjustedRunExpectancyF5?date={date}'
    
    try:
        # Disable SSL verification for localhost
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data['games']:
            results.append(analyze_game(game))
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def print_odds(odds):
    """
    Print odds in a readable format
    """
    for game in odds:
        print(f"\n{game['homeTeam']['team']} vs {game['awayTeam']['team']}")
        print(f"Run Differential: {game['runDifferential']}")
        print(f"{game['homeTeam']['team']}:")
        print(f"  Expected Runs: {game['homeTeam']['expectedRuns']}")
        print(f"  American: {game['homeTeam']['odds']['american']}")
        print(f"  Decimal: {game['homeTeam']['odds']['decimal']}")
        print(f"  Win Probability: {game['homeTeam']['odds']['probability']}%")
        print(f"{game['awayTeam']['team']}:")
        print(f"  Expected Runs: {game['awayTeam']['expectedRuns']}")
        print(f"  American: {game['awayTeam']['odds']['american']}")
        print(f"  Decimal: {game['awayTeam']['odds']['decimal']}")
        print(f"  Win Probability: {game['awayTeam']['odds']['probability']}%")
        print("-" * 50)

if __name__ == "__main__":
    # Analyze games for a specific date
    odds = fetch_and_analyze_games('2024-09-09')
    if odds:
        print_odds(odds)