import requests
from bs4 import BeautifulSoup

# Function to get the first letter of the pitcher_id for URL construction
def get_url_letter(pitcher_id):
    return pitcher_id[0]

# Function to scrape the pitcher's profile data from Baseball Reference
def scrape_pitcher_profile(pitcher_id, year):
    letter = get_url_letter(pitcher_id)
    url = f"https://www.baseball-reference.com/players/{letter}/{pitcher_id}.shtml"
    
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Ensure we raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error retrieving data from {url}: {e}")
        return None

    standard_pitching_table = soup.find('table', id='pitching_standard')
    if standard_pitching_table is None:
        print(f"Standard Pitching table not found for pitcher: {pitcher_id}")
        return None

    year_str = str(year)
    row = None
    for tr in standard_pitching_table.find('tbody').find_all('tr'):
        year_col = tr.find(attrs={'data-stat': 'year_ID'})
        league_col = tr.find(attrs={'data-stat': 'lg_ID'})
        # Ensure we're getting the MLB stats for the correct year
        if year_col and year_str in year_col.text.strip() and league_col and league_col.text.strip() in ['AL', 'NL']:
            row = tr
            break

    if row is None:
        print(f"Year {year} MLB data not found for pitcher: {pitcher_id}")
        return None

    try:
        wins = row.find(attrs={'data-stat': 'W'}).text
        losses = row.find(attrs={'data-stat': 'L'}).text
        win_loss_record = f"{wins}-{losses}"

        pitcher_data = {
            "bbrefID": pitcher_id,
            "Year": year,
            "Age": int(row.find(attrs={'data-stat': 'age'}).text) if row.find(attrs={'data-stat': 'age'}) else None,
            "Team": row.find(attrs={'data-stat': 'team_ID'}).text if row.find(attrs={'data-stat': 'team_ID'}) else None,
            "Lg": row.find(attrs={'data-stat': 'lg_ID'}).text if row.find(attrs={'data-stat': 'lg_ID'}) else None,
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

    except AttributeError as e:
        print(f"Error parsing row data for pitcher: {pitcher_id}, Year: {year}. Error: {e}")
        return None

    return pitcher_data

# Function to check if the pitcher exists in the database
def pitcher_exists(bbrefID):
    url = f"https://localhost:44346/api/Pitchers/exists/{bbrefID}"
    response = requests.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    return response.status_code == 200

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

    if response.status_code in [200, 204]:  # Considering 204 as successful for PUT/POST
        print(f"Successfully {'updated' if is_update else 'posted'} data to {endpoint}.")
    elif response.status_code == 409 and not is_update:  # Conflict error (duplicate entry) during POST
        print(f"Conflict detected when posting data to {endpoint}. Attempting to update instead.")
        post_to_api(endpoint, data, is_update=True)
    else:
        print(f"Failed to {'update' if is_update else 'post'} data to {endpoint}. Status code: {response.status_code}")
        print(f"Response content: {response.content}")

# Function to get the list of pitchers from the GamePreviews API by date
def get_pitchers_from_game_previews(date):
    url = f"https://localhost:44346/api/GamePreviews/{date}"
    response = requests.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code == 200:
        games = response.json()
        pitchers = []
        for game in games:
            if game.get('homePitcher') and game['homePitcher'] != "Unannounced":
                pitchers.append(game['homePitcher'])
            if game.get('awayPitcher') and game['awayPitcher'] != "Unannounced":
                pitchers.append(game['awayPitcher'])
        return pitchers
    else:
        print(f"Failed to retrieve game previews for {date}. Status code: {response.status_code}")
        return []

# Main script execution
date = "24-08-24"  # Example date string
year = 2024

# Get the list of pitchers from the GamePreviews API
pitchers = get_pitchers_from_game_previews(date)

# Loop through each pitcher and scrape & post data
for pitcher_id in pitchers:
    if pitcher_id.lower() == "unannounced":
        print(f"Skipping pitcher: {pitcher_id}")
        continue
    
    pitcher_data = scrape_pitcher_profile(pitcher_id, year)
    
    if pitcher_exists(pitcher_id):
        post_to_api('Pitchers', pitcher_data, is_update=True)
    else:
        post_to_api('Pitchers', pitcher_data)
