# Import required libraries
import requests
from bs4 import BeautifulSoup, Comment
import time
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Create a session object
session = requests.Session()

# Define common headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com',
    'DNT': '1',  # Do Not Track Request Header
    'Connection': 'keep-alive',
}

# Attach the headers to the session
session.headers.update(headers)

# Function to get the first letter of the pitcher_id for URL construction
def get_url_letter(pitcher_id):
    return pitcher_id[0]

# Function to check if the pitcher exists in the database
def pitcher_1st_inning_exists(session, bbrefID):
    url = f"https://localhost:44346/api/Pitcher1stInning/{bbrefID}"
    print(f"Checking if pitcher exists in the database: {bbrefID}")
    
    response = session.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} exists in the database.")
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} does not exist in the database.")
    else:
        print(f"Error checking pitcher existence. Status code: {response.status_code}")
    
    return response.status_code == 200

# Function to check if a home/away split exists in the database
def pitcher_home_away_split_exists(session, bbrefID, year, split):
    url = f"https://localhost:44346/api/PitcherHomeAwaySplits/{bbrefID}/{year}/{split}"
    print(f"Checking if pitcher home/away split exists in the database: {bbrefID}, {year}, {split}")
    
    response = session.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} {split} split for {year} exists in the database.")
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} {split} split for {year} does not exist in the database.")
    else:
        print(f"Error checking pitcher home/away split existence. Status code: {response.status_code}")
    
    return response.status_code == 200



def post_to_api(session, endpoint, data, is_update=False):
    if data is None:
        print(f"No data to post to {endpoint}.")
        return
    
    url = f"https://localhost:44346/api/{endpoint}"
    
    # Handle 'PitcherHomeAwaySplits' endpoint separately with Year and Split in the URL
    if is_update and 'Year' in data and 'Split' in data:
        url += f"/{data['bbrefID']}/{data['Year']}/{data['Split']}"
    elif is_update:
        url += f"/{data['bbrefID']}"  # For 'Pitcher1stInning' or other endpoints
    
    json_data = json.dumps(data)  # Convert the data to a JSON string
    
    # Print the CURL equivalent command for debugging
    curl_command = f"curl -X {'PUT' if is_update else 'POST'} \\\n  '{url}' \\\n  -H 'Content-Type: application/json' \\\n  -d '{json_data}'"
    print(f"Equivalent CURL command:\n{curl_command}\n")
    
    response = session.put(url, data=json_data, headers={'Content-Type': 'application/json'}, verify=False) if is_update else session.post(url, data=json_data, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code in [200, 201, 204]:
        print(f"Successfully {'updated' if is_update else 'posted'} data to {endpoint} for {data['bbrefID']}.")
    elif response.status_code == 429:
        print(f"Rate limit exceeded while trying to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefID']}.")
    else:
        print(f"Failed to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefID']}. Status code: {response.status_code}")
        print(f"Response content: {response.content}")




# Function to get the list of pitchers from the GamePreviews API by date
def get_pitchers_from_game_previews(session, date):
    url = f"https://localhost:44346/api/GamePreviews/{date}"
    response = session.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    
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

# Combined scraping function to scrape both first inning and home/away splits data
def scrape_and_post_pitcher_data(session, pitcher_id, year):
# Wait for 5 seconds to avoid hitting rate limits
    time.sleep(5)
    url = f"https://www.baseball-reference.com/players/split.fcgi?id={pitcher_id}&year={year}&t=p"
    print(f"Scraping data from URL: {url}")
    
    response = session.get(url, verify=False)
    if response.status_code != 200:
        print(f"Failed to retrieve page for pitcher {pitcher_id}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Scrape First Inning Data
    inning_div = soup.find('div', id='all_innng')
    if inning_div:
        print(f"Found 'all_innng' div for pitcher {pitcher_id}")
        comments = inning_div.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            div_inning = comment_soup.find('div', id='div_innng')
            if div_inning:
                print(f"Found 'div_innng' div within comment for pitcher {pitcher_id}")
                inning_table = div_inning.find('table', id='innng')
                if inning_table:
                    print(f"Found 'innng' table for pitcher {pitcher_id}")
                    tbody = inning_table.find('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        for row in rows:
                            first_column = row.find('th', {'data-stat': 'split_name'})
                            if first_column and first_column.text.strip() == '1st inning':
                                print(f"Found 1st inning data for pitcher {pitcher_id}")
                                try:
                                    doubles = int(row.find(attrs={'data-stat': '2B'}).text or 0)
                                    triples = int(row.find(attrs={'data-stat': '3B'}).text or 0)
                                    pitcher_1st_inning_data = {
                                        "bbrefID": pitcher_id,
                                        "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
                                        "IP": float(row.find(attrs={'data-stat': 'IP'}).text or 0),
                                        "ER": int(row.find(attrs={'data-stat': 'ER'}).text or 0),
                                        "ERA": float(row.find(attrs={'data-stat': 'earned_run_avg'}).text or 0),
                                        "PA": int(row.find(attrs={'data-stat': 'PA'}).text or 0),
                                        "AB": int(row.find(attrs={'data-stat': 'AB'}).text or 0),
                                        "R": int(row.find(attrs={'data-stat': 'R'}).text or 0),
                                        "H": int(row.find(attrs={'data-stat': 'H'}).text or 0),
                                        "TwoB": doubles,
                                        "ThreeB": triples,
                                        "HR": int(row.find(attrs={'data-stat': 'HR'}).text or 0),
                                        "SB": int(row.find(attrs={'data-stat': 'SB'}).text or 0),
                                        "CS": int(row.find(attrs={'data-stat': 'CS'}).text or 0),
                                        "BB": int(row.find(attrs={'data-stat': 'BB'}).text or 0),
                                        "SO": int(row.find(attrs={'data-stat': 'SO'}).text or 0),
                                        "SO_W": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
                                        "BA": float(row.find(attrs={'data-stat': 'batting_avg'}).text or 0),
                                        "OBP": float(row.find(attrs={'data-stat': 'onbase_perc'}).text or 0),
                                        "SLG": float(row.find(attrs={'data-stat': 'slugging_perc'}).text or 0),
                                        "OPS": float(row.find(attrs={'data-stat': 'onbase_plus_slugging'}).text or 0),
                                        "TB": int(row.find(attrs={'data-stat': 'TB'}).text or 0),
                                        "GDP": int(row.find(attrs={'data-stat': 'GIDP'}).text or 0),
                                        "HBP": int(row.find(attrs={'data-stat': 'HBP'}).text or 0),
                                        "SH": int(row.find(attrs={'data-stat': 'SH'}).text or 0),
                                        "SF": int(row.find(attrs={'data-stat': 'SF'}).text or 0),
                                        "IBB": int(row.find(attrs={'data-stat': 'IBB'}).text or 0),
                                        "ROE": int(row.find(attrs={'data-stat': 'ROE'}).text or 0),
                                        "BAbip": float(row.find(attrs={'data-stat': 'batting_avg_bip'}).text or 0),
                                        "tOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_total'}).text or 0),
                                        "sOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_lg'}).text or 0),
                                    }
                                    if pitcher_1st_inning_exists(session, pitcher_id):
                                        post_to_api(session, 'Pitcher1stInning', pitcher_1st_inning_data, is_update=True)
                                    else:
                                        post_to_api(session, 'Pitcher1stInning', pitcher_1st_inning_data)
                                except AttributeError as e:
                                    print(f"Error parsing first inning data for pitcher: {pitcher_id}. Error: {e}")

    # Scrape Home/Away Splits Data
    content_div = soup.find('div', id='content')
    if content_div:
        all_divs = content_div.find_all('div', id=lambda value: value and value.startswith('all_'))
        if len(all_divs) >= 3:
            target_div = all_divs[2]
            comments = target_div.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                div_hmvis = comment_soup.find('div', id='div_hmvis')
                if div_hmvis:
                    print(f"Found 'div_hmvis' div within comment for pitcher {pitcher_id}")
                    home_away_table = div_hmvis.find('table', id='hmvis')
                    if home_away_table:
                        print(f"Found 'hmvis' table for pitcher {pitcher_id}")
                        tbody = home_away_table.find('tbody')
                        if tbody:
                            rows = tbody.find_all('tr')
                            for row in rows:
                                split_type = row.find('th', {'data-stat': 'split_name'}).text.strip()
                                home_away_data = {
                                    "bbrefID": pitcher_id,
                                    "Year": 2024,
                                    "Split": split_type,
                                    "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
                                    "IP": float((int(row.find(attrs={'data-stat': 'PA'}).text or 0) - int(row.find(attrs={'data-stat': 'H'}).text or 0) - int(row.find(attrs={'data-stat': 'BB'}).text or 0)) / 3),
                                    "PA": int(row.find(attrs={'data-stat': 'PA'}).text or 0),
                                    "AB": int(row.find(attrs={'data-stat': 'AB'}).text or 0),
                                    "R": int(row.find(attrs={'data-stat': 'R'}).text or 0),
                                    "H": int(row.find(attrs={'data-stat': 'H'}).text or 0),
                                    "TwoB": int(row.find(attrs={'data-stat': '2B'}).text or 0),
                                    "ThreeB": int(row.find(attrs={'data-stat': '3B'}).text or 0),
                                    "HR": int(row.find(attrs={'data-stat': 'HR'}).text or 0),
                                    "SB": int(row.find(attrs={'data-stat': 'SB'}).text or 0),
                                    "CS": int(row.find(attrs={'data-stat': 'CS'}).text or 0),
                                    "BB": int(row.find(attrs={'data-stat': 'BB'}).text or 0),
                                    "SO": int(row.find(attrs={'data-stat': 'SO'}).text or 0),
                                    "SO/W": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
                                    "BA": float(row.find(attrs={'data-stat': 'batting_avg'}).text or 0),
                                    "OBP": float(row.find(attrs={'data-stat': 'onbase_perc'}).text or 0),
                                    "SLG": float(row.find(attrs={'data-stat': 'slugging_perc'}).text or 0),
                                    "OPS": float(row.find(attrs={'data-stat': 'onbase_plus_slugging'}).text or 0),
                                    "TB": int(row.find(attrs={'data-stat': 'TB'}).text or 0),
                                    "GDP": int(row.find(attrs={'data-stat': 'GIDP'}).text or 0),
                                    "HBP": int(row.find(attrs={'data-stat': 'HBP'}).text or 0),
                                    "SH": int(row.find(attrs={'data-stat': 'SH'}).text or 0),
                                    "SF": int(row.find(attrs={'data-stat': 'SF'}).text or 0),
                                    "IBB": int(row.find(attrs={'data-stat': 'IBB'}).text or 0),
                                    "ROE": int(row.find(attrs={'data-stat': 'ROE'}).text or 0),
                                    "BAbip": float(row.find(attrs={'data-stat': 'batting_avg_bip'}).text or 0),
                                    "tOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_total'}).text or 0),
                                    "sOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_lg'}).text or 0),
                                }
                                if pitcher_home_away_split_exists(session, pitcher_id, year, split_type):
                                    post_to_api(session, f'PitcherHomeAwaySplits', home_away_data, is_update=True)
                                else:
                                    post_to_api(session, 'PitcherHomeAwaySplits', home_away_data)

# Main script execution
date = "24-08-24"  # Example date string
year = 2024

# Get the list of pitchers from the GamePreviews API
pitchers = get_pitchers_from_game_previews(session, date)

# Loop through each pitcher and scrape & post data for both endpoints
for pitcher_id in pitchers:
    if pitcher_id.lower() == "unannounced":
        print(f"Skipping pitcher: {pitcher_id}")
        continue
    
    print(f"Processing pitcher: {pitcher_id}")
    
    # Scrape and post both first inning data and home/away splits data from the same URL
    scrape_and_post_pitcher_data(session, pitcher_id, year)
