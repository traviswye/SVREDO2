import csv
import requests

# File paths
input_file = 'C:/Users/travis.wye/Documents/tw/viz/Scripts/pitcherTablework/unprocessed_pitchers.csv'
unprocessed_file = 'C:/Users/travis.wye/Documents/tw/viz/Scripts/pitcherTablework/unprocessed_pitchers2.csv'

# API URL (assuming it's running locally)
api_url = "https://localhost:44346/api/Pitchers/Basic"

# Team abbreviation to team name dictionary
team_abbreviation_to_name = {
    "CIN": "Reds",
    "SDP": "Padres",
    "NYM": "Mets",
    "WSN": "Nationals",
    "PHI": "Phillies",
    "ARI": "Diamondbacks",
    "CHC": "Cubs",
    "MIA": "Marlins",
    "MIL": "Brewers",
    "LAD": "Dodgers",
    "PIT": "Pirates",
    "COL": "Rockies",
    "STL": "Cardinals",
    "TOT": "2Teams",
    "ATL": "Braves",
    "SFG": "Giants",
    "LAA": "Angels",
    "OAK": "Athletics",
    "BOS": "Red Sox",
    "CHW": "White Sox",
    "CLE": "Guardians",
    "DET": "Tigers",
    "HOU": "Astros",
    "KCR": "Royals",
    "MIN": "Twins",
    "NYY": "Yankees",
    "SEA": "Mariners",
    "TBR": "Rays",
    "TEX": "Rangers",
    "TOR": "Blue Jays",
    "BAL": "Orioles",
}

# Team to league dictionary
team_to_league = {
    "Reds": "NL",
    "Padres": "NL",
    "Mets": "NL",
    "Nationals": "NL",
    "Phillies": "NL",
    "Diamondbacks": "NL",
    "Cubs": "NL",
    "Marlins": "NL",
    "Brewers": "NL",
    "Dodgers": "NL",
    "Pirates": "NL",
    "Rockies": "NL",
    "Cardinals": "NL",
    "Braves": "NL",
    "Giants": "NL",
    "Angels": "AL",
    "Athletics": "AL",
    "Red Sox": "AL",
    "White Sox": "AL",
    "Guardians": "AL",
    "Tigers": "AL",
    "Astros": "AL",
    "Royals": "AL",
    "Twins": "AL",
    "Yankees": "AL",
    "Mariners": "AL",
    "Rays": "AL",
    "Rangers": "AL",
    "Blue Jays": "AL",
    "Orioles": "AL",
}

# Function to post pitcher data to the API
def post_pitcher_data(pitcher_data):
    try:
        response = requests.post(api_url, json=pitcher_data, verify=False)  # Disable SSL verification for localhost
        if response.status_code == 200:
            print(f"Successfully posted data for {pitcher_data['bbrefId']}")
        else:
            print(f"Failed to post data for {pitcher_data['bbrefId']}. Status code: {response.status_code}")
            print(f"Response content: {response.content}")
    except requests.RequestException as e:
        print(f"Error posting data for {pitcher_data['bbrefId']}: {e}")

# Prepare to write unprocessed pitchers to a new file
with open(unprocessed_file, mode='w', newline='') as unprocessed_csv:
    unprocessed_writer = csv.writer(unprocessed_csv)

    # Read and process the input file
    with open(input_file, mode='r') as file:
        csv_reader = csv.reader(file)
        
        # Process each row
        for row in csv_reader:
            bbrefID = row[-1]
            team_abbr = row[3]
            age = int(row[2])

            # Convert team abbreviation to full team name
            team_name = team_abbreviation_to_name.get(team_abbr)
            league = team_to_league.get(team_name) if team_name else None

            # Check if both team name and league are found
            if team_name and league:
                # Create the payload for the API request
                pitcher_data = {
                    "bbrefId": bbrefID,
                    "team": team_name,
                    "age": age,
                    "lg": league
                }

                # Post the pitcher data
                post_pitcher_data(pitcher_data)
            else:
                # If the team name or league is missing, write the row to the unprocessed file
                print(f"Unprocessed pitcher due to missing team/league: {bbrefID}")
                unprocessed_writer.writerow(row)

print(f"Completed posting pitcher data. Unprocessed pitchers have been written to {unprocessed_file}")
