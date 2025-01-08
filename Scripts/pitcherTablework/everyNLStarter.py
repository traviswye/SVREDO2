import requests
from bs4 import BeautifulSoup

# Disable SSL verification and set headers to avoid tracking
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Windows NT 10.0; Win64; x64) Chrome/104.0.5112.79 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com',
    'DNT': '1',  # Do Not Track Request Header
    'Connection': 'keep-alive',
}

# Function to get the pitching data
def scrape_pitcher_data():
    url = "https://www.baseball-reference.com/leagues/NL/2024-standard-pitching.shtml"

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Ensure we raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error retrieving data from {url}: {e}")
        return None

    # Find the table with the title "Player Standard Pitching"
    pitching_table = soup.find('table', {'id': 'players_standard_pitching'})
    if pitching_table is None:
        print("Player Standard Pitching table not found.")
        return None

    rows = pitching_table.find('tbody').find_all('tr')
    pitchers_data = []

    for row in rows:
        # Check for GS > 1 (Game Started)
        gs = row.find(attrs={'data-stat': 'GS'})
        if gs and int(gs.text) <= 1:
            continue  # Skip if GS <= 1

        # Extract bbrefID from the player's link
        pitcher_link = row.find('td', {'data-stat': 'player'})
        if pitcher_link and pitcher_link.find('a'):
            pitcher_id = pitcher_link['data-append-csv']
        else:
            continue  # Skip if pitcher_id is not found

        # Extract other pitcher data
        try:
            wins = row.find(attrs={'data-stat': 'W'}).text
            losses = row.find(attrs={'data-stat': 'L'}).text
            win_loss_record = f"{wins}-{losses}"

            pitcher_data = {
                "bbrefID": pitcher_id,
                "Year": 2024,  # Always 2024
                "Age": int(row.find(attrs={'data-stat': 'age'}).text) if row.find(attrs={'data-stat': 'age'}) else None,
                "Team": row.find(attrs={'data-stat': 'team_ID'}).text if row.find(attrs={'data-stat': 'team_ID'}) else None,
                "Lg": "NL",  # Always NL
                "WL": win_loss_record,
                "WLPercentage": float(row.find(attrs={'data-stat': 'win_loss_perc'}).text or 0) if row.find(attrs={'data-stat': 'win_loss_perc'}) else 0,
                "ERA": float(row.find(attrs={'data-stat': 'earned_run_avg'}).text or 0) if row.find(attrs={'data-stat': 'earned_run_avg'}) else 0,
                "G": int(row.find(attrs={'data-stat': 'G'}).text or 0) if row.find(attrs={'data-stat': 'G'}) else 0,
                "GS": int(row.find(attrs={'data-stat': 'GS'}).text or 0) if row.find(attrs={'data-stat': 'GS'}) else 0,
                "GF": int(row.find(attrs={'data-stat': 'GF'}).text or 0) if row.find(attrs={'data-stat': 'GF'}) else 0,
                "CG": int(row.find(attrs={'data-stat': 'CG'}).text or 0) if row.find(attrs={'data-stat': 'CG'}) else 0,
                "SHO": int(row.find(attrs={'data-stat': 'SHO'}).text or 0) if row.find(attrs={'data-stat': 'SHO'}) else 0,
                "SV": int(row.find(attrs={'data-stat': 'SV'}).text or 0) if row.find(attrs={'data-stat': 'SV'}) else 0,
                "IP": float(row.find(attrs={'data-stat': 'IP'}).text or 0) if row.find(attrs={'data-stat': 'IP'}) else 0,
                "H": int(row.find(attrs={'data-stat': 'H'}).text or 0) if row.find(attrs={'data-stat': 'H'}) else 0,
                "R": int(row.find(attrs={'data-stat': 'R'}).text or 0) if row.find(attrs={'data-stat': 'R'}) else 0,
                "ER": int(row.find(attrs={'data-stat': 'ER'}).text or 0) if row.find(attrs={'data-stat': 'ER'}) else 0,
                "HR": int(row.find(attrs={'data-stat': 'HR'}).text or 0) if row.find(attrs={'data-stat': 'HR'}) else 0,
                "BB": int(row.find(attrs={'data-stat': 'BB'}).text or 0) if row.find(attrs={'data-stat': 'BB'}) else 0,
                "IBB": int(row.find(attrs={'data-stat': 'IBB'}).text or 0) if row.find(attrs={'data-stat': 'IBB'}) else 0,
                "SO": int(row.find(attrs={'data-stat': 'SO'}).text or 0) if row.find(attrs={'data-stat': 'SO'}) else 0,
                "HBP": int(row.find(attrs={'data-stat': 'HBP'}).text or 0) if row.find(attrs={'data-stat': 'HBP'}) else 0,
                "BK": int(row.find(attrs={'data-stat': 'BK'}).text or 0) if row.find(attrs={'data-stat': 'BK'}) else 0,
                "WP": int(row.find(attrs={'data-stat': 'WP'}).text or 0) if row.find(attrs={'data-stat': 'WP'}) else 0,
                "BF": int(row.find(attrs={'data-stat': 'batters_faced'}).text or 0) if row.find(attrs={'data-stat': 'batters_faced'}) else 0,
                "ERAPlus": int(row.find(attrs={'data-stat': 'earned_run_avg_plus'}).text or 0) if row.find(attrs={'data-stat': 'earned_run_avg_plus'}) else 0,
                "FIP": float(row.find(attrs={'data-stat': 'fip'}).text or 0) if row.find(attrs={'data-stat': 'fip'}) else 0,
                "WHIP": float(row.find(attrs={'data-stat': 'whip'}).text or 0) if row.find(attrs={'data-stat': 'whip'}) else 0,
                "H9": float(row.find(attrs={'data-stat': 'hits_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'hits_per_nine'}) else 0,
                "HR9": float(row.find(attrs={'data-stat': 'home_runs_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'home_runs_per_nine'}) else 0,
                "BB9": float(row.find(attrs={'data-stat': 'bases_on_balls_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'bases_on_balls_per_nine'}) else 0,
                "SO9": float(row.find(attrs={'data-stat': 'strikeouts_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'strikeouts_per_nine'}) else 0,
                "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0) if row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}) else 0,
            }
            
            pitchers_data.append(pitcher_data)

        except AttributeError as e:
            print(f"Error parsing row data for pitcher: {pitcher_id}. Error: {e}")
            continue

    return pitchers_data

# Function to check if the pitcher exists in the database
def pitcher_exists(bbrefID):
    url = f"https://localhost:44346/api/Pitchers/{bbrefID}"
    response = requests.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    return response.status_code == 200

# Function to post to the API
def post_to_api(endpoint, data, is_update=False):
    if data is None:
        print(f"No data to post to {endpoint}.")
        return
    
    if is_update:
        url = f"https://localhost:44346/api/{endpoint}/{data['bbrefID']}"
        response = requests.put(url, json=data, headers={'Content-Type': 'application/json'}, verify=False)
    else:
        url = f"https://localhost:44346/api/{endpoint}"
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, verify=False)

    if response.status_code == 200:
        print(f"Successfully {'updated' if is_update else 'posted'} data to {endpoint}.")
    else:
        print(f"Failed to {'update' if is_update else 'post'} data to {endpoint}. Status code: {response.status_code}")
        print(f"Response content: {response.content}")

# Main script execution
pitchers = scrape_pitcher_data()

# Loop through each pitcher and post data
for pitcher_data in pitchers:
    pitcher_id = pitcher_data["bbrefID"]
    
    if pitcher_exists(pitcher_id):
        post_to_api('Pitchers', pitcher_data, is_update=True)
    else:
        post_to_api('Pitchers', pitcher_data)
