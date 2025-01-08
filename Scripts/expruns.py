import requests

# Define the URL of the API endpoint
url = "https://localhost:44346/api/Evaluation/evaluateNRFI1st/2024-09-18"

# Send a GET request to the API endpoint
response = requests.get(url, verify=False)  # Disable SSL verification for localhost

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    games = response.json()
    
    # Loop through each game and print the desired output
    for game in games:
        away_team = game["awayTeam"]
        home_team = game["homeTeam"]
        expected_runs = game["expectedRuns"]
        is_home_lineup_actual = game["isHomeLineupActual"]
        is_away_lineup_actual = game["isAwayLineupActual"]
        
        print(f"{away_team} vs {home_team}")
        print(f"Probability of YRFI (%): {expected_runs}")
        print(f"Home Lineup Actual: {is_home_lineup_actual}")
        print(f"Away Lineup Actual: {is_away_lineup_actual}\n")
    
    # Sort the games by expected_runs (Probability of YRFI) in descending order
    sorted_games = sorted(games, key=lambda x: x["expectedRuns"], reverse=True)
    
    print("\nGames sorted by Probability of YRFI (%):\n")
    
    # Print the games in the sorted format
    for game in sorted_games:
        away_team = game["awayTeam"]
        home_team = game["homeTeam"]
        expected_runs = game["expectedRuns"]
        
        # Print the game with aligned columns
        print(f"{away_team} vs {home_team:<25} {expected_runs}")
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
