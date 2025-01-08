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

# Function to check if the pitcher exists in the PitcherByInningStats database
def pitcher_inning_exists(session, bbrefID, inning):
    url = f"https://localhost:44346/api/PitcherByInningStats/{bbrefID}/{inning}"
    print(f"Checking if inning data exists in the database: {bbrefID}, Inning: {inning}")
    
    response = session.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code == 200:
        print(f"Inning data exists in the database for pitcher {bbrefID}, Inning: {inning}.")
        return True
    elif response.status_code == 404:
        print(f"Inning data does not exist in the database for pitcher {bbrefID}, Inning: {inning}.")
        return False
    else:
        print(f"Error checking inning data existence. Status code: {response.status_code}")
        return False

# Function to check if a home/away split exists in the database
def pitcher_home_away_split_exists(session, bbrefID, year, split):
    url = f"https://localhost:44346/api/PitcherHomeAwaySplits/{bbrefID}/{year}/{split}"
    print(f"Checking if pitcher home/away split exists in the database: {bbrefID}, {year}, {split}")
    
    response = session.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} {split} split for {year} exists in the database.")
        return True
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} {split} split for {year} does not exist in the database.")
        return False
    else:
        print(f"Error checking pitcher home/away split existence. Status code: {response.status_code}")
        return False

# Function to post or update data to the API
def post_to_api(session, endpoint, data, is_update=False):
    if data is None:
        print(f"No data to post to {endpoint}.")
        return
    
    url = f"https://localhost:44346/api/{endpoint}"
    
    # Modify the URL if it's an update (PUT request)
    if is_update:
        if 'inning' in data:
            url += f"/{data['bbrefId']}/{data['inning']}"  # Append bbrefId and inning for PitcherByInningStats
        elif 'Year' in data and 'Split' in data:
            url += f"/{data['bbrefID']}/{data['Year']}/{data['Split']}"  # Append Year and Split for PitcherHomeAwaySplits
    
    json_data = json.dumps(data)  # Convert the data to a JSON string
    
    # Print the CURL equivalent command for debugging
    curl_command = f"curl -X {'PUT' if is_update else 'POST'} \\\n  '{url}' \\\n  -H 'Content-Type: application/json' \\\n  -d '{json_data}'"
    print(f"Equivalent CURL command:\n{curl_command}\n")
    
    response = session.put(url, data=json_data, headers={'Content-Type': 'application/json'}, verify=False) if is_update else session.post(url, data=json_data, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code in [200, 201, 204]:
        if 'inning' in data:  # Success message for PitcherByInningStats
            print(f"Successfully {'updated' if is_update else 'posted'} data to {endpoint} for {data['bbrefId']}.")
        elif 'Year' in data and 'Split' in data:  # Success message for PitcherHomeAwaySplits
            print(f"Successfully {'updated' if is_update else 'posted'} data to {endpoint} for {data['bbrefID']}.")
    elif response.status_code == 429:
        if 'inning' in data:  # Rate limit message for PitcherByInningStats
            print(f"Rate limit exceeded while trying to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefId']}.")
        elif 'Year' in data and 'Split' in data:  # Rate limit message for PitcherHomeAwaySplits
            print(f"Rate limit exceeded while trying to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefID']}.")
    else:
        if 'inning' in data:  # Failure message for PitcherByInningStats
            print(f"Failed to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefId']}. Status code: {response.status_code}")
        elif 'Year' in data and 'Split' in data:  # Failure message for PitcherHomeAwaySplits
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

# Combined scraping function to scrape both inning-specific and home/away splits data
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

    # Scrape Inning Data (1st to 9th)
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
                            if first_column:
                                split_name = first_column.text.strip()
                                # Check if the first character is a digit between 1 and 9
                                if split_name and split_name[0].isdigit() and int(split_name[0]) in range(1, 10):
                                    # Extract inning number from split_name (e.g., "1st inning" -> 1)
                                    inning = int(split_name[0])
                                    print(f"Found {split_name} data for pitcher {pitcher_id} (Inning {inning})")
                                    
                                    try:
                                        doubles = int(row.find(attrs={'data-stat': '2B'}).text or 0)
                                        triples = int(row.find(attrs={'data-stat': '3B'}).text or 0)
                                        # Round IP to one decimal place
                                        ip = float(row.find(attrs={'data-stat': 'IP'}).text or 0)
                                        ip = round(ip, 1)  # Round to 1 decimal place

                                        pitcher_inning_data = {
                                            "bbrefId": pitcher_id,
                                            "inning": inning,  # Use the extracted inning number
                                            "g": int(row.find(attrs={'data-stat': 'G'}).text or 0),
                                            "ip": ip,  # Use the rounded IP value
                                            "er": int(row.find(attrs={'data-stat': 'ER'}).text or 0),
                                            "era": float(row.find(attrs={'data-stat': 'earned_run_avg'}).text or 0),
                                            "pa": int(row.find(attrs={'data-stat': 'PA'}).text or 0),
                                            "ab": int(row.find(attrs={'data-stat': 'AB'}).text or 0),
                                            "r": int(row.find(attrs={'data-stat': 'R'}).text or 0),
                                            "h": int(row.find(attrs={'data-stat': 'H'}).text or 0),
                                            "twoB": doubles,
                                            "threeB": triples,
                                            "hr": int(row.find(attrs={'data-stat': 'HR'}).text or 0),
                                            "sb": int(row.find(attrs={'data-stat': 'SB'}).text or 0),
                                            "cs": int(row.find(attrs={'data-stat': 'CS'}).text or 0),
                                            "bb": int(row.find(attrs={'data-stat': 'BB'}).text or 0),
                                            "so": int(row.find(attrs={'data-stat': 'SO'}).text or 0),
                                            "sO_W": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
                                            "ba": float(row.find(attrs={'data-stat': 'batting_avg'}).text or 0),
                                            "obp": float(row.find(attrs={'data-stat': 'onbase_perc'}).text or 0),
                                            "slg": float(row.find(attrs={'data-stat': 'slugging_perc'}).text or 0),
                                            "ops": float(row.find(attrs={'data-stat': 'onbase_plus_slugging'}).text or 0),
                                            "tb": int(row.find(attrs={'data-stat': 'TB'}).text or 0),
                                            "gdp": int(row.find(attrs={'data-stat': 'GIDP'}).text or 0),
                                            "hbp": int(row.find(attrs={'data-stat': 'HBP'}).text or 0),
                                            "sh": int(row.find(attrs={'data-stat': 'SH'}).text or 0),
                                            "sf": int(row.find(attrs={'data-stat': 'SF'}).text or 0),
                                            "ibb": int(row.find(attrs={'data-stat': 'IBB'}).text or 0),
                                            "roe": int(row.find(attrs={'data-stat': 'ROE'}).text or 0),
                                            "bAbip": float(row.find(attrs={'data-stat': 'batting_avg_bip'}).text or 0),
                                            "tOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_total'}).text or 0),
                                            "sOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_lg'}).text or 0),
                                            "dateModified": time.strftime('%Y-%m-%dT%H:%M:%S')
                                        }
                                        
                                        # Post data to API endpoint for each inning
                                        if pitcher_inning_exists(session, pitcher_id, inning):
                                            post_to_api(session, 'PitcherByInningStats', pitcher_inning_data, is_update=True)
                                        else:
                                            post_to_api(session, 'PitcherByInningStats', pitcher_inning_data)
                                    except AttributeError as e:
                                        print(f"Error parsing {inning} inning data for pitcher: {pitcher_id}. Error: {e}")
                                
                                elif "Ext inning" in split_name:
                                    inning = 10  # Set inning to 10 for extra innings
                                    print(f"Found {split_name} data for pitcher {pitcher_id} (Inning {inning})")

                                    try:
                                        doubles = int(row.find(attrs={'data-stat': '2B'}).text or 0)
                                        triples = int(row.find(attrs={'data-stat': '3B'}).text or 0)
                                        # Round IP to one decimal place
                                        ip = float(row.find(attrs={'data-stat': 'IP'}).text or 0)
                                        ip = round(ip, 1)  # Round to 1 decimal place

                                        pitcher_inning_data = {
                                            "bbrefId": pitcher_id,
                                            "inning": inning,  # Use inning 10 for extra innings
                                            "g": int(row.find(attrs={'data-stat': 'G'}).text or 0),
                                            "ip": ip,  # Use the rounded IP value
                                            "er": int(row.find(attrs={'data-stat': 'ER'}).text or 0),
                                            "era": float(row.find(attrs={'data-stat': 'earned_run_avg'}).text or 0),
                                            "pa": int(row.find(attrs={'data-stat': 'PA'}).text or 0),
                                            "ab": int(row.find(attrs={'data-stat': 'AB'}).text or 0),
                                            "r": int(row.find(attrs={'data-stat': 'R'}).text or 0),
                                            "h": int(row.find(attrs={'data-stat': 'H'}).text or 0),
                                            "twoB": doubles,
                                            "threeB": triples,
                                            "hr": int(row.find(attrs={'data-stat': 'HR'}).text or 0),
                                            "sb": int(row.find(attrs={'data-stat': 'SB'}).text or 0),
                                            "cs": int(row.find(attrs={'data-stat': 'CS'}).text or 0),
                                            "bb": int(row.find(attrs={'data-stat': 'BB'}).text or 0),
                                            "so": int(row.find(attrs={'data-stat': 'SO'}).text or 0),
                                            "sO_W": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
                                            "ba": float(row.find(attrs={'data-stat': 'batting_avg'}).text or 0),
                                            "obp": float(row.find(attrs={'data-stat': 'onbase_perc'}).text or 0),
                                            "slg": float(row.find(attrs={'data-stat': 'slugging_perc'}).text or 0),
                                            "ops": float(row.find(attrs={'data-stat': 'onbase_plus_slugging'}).text or 0),
                                            "tb": int(row.find(attrs={'data-stat': 'TB'}).text or 0),
                                            "gdp": int(row.find(attrs={'data-stat': 'GIDP'}).text or 0),
                                            "hbp": int(row.find(attrs={'data-stat': 'HBP'}).text or 0),
                                            "sh": int(row.find(attrs={'data-stat': 'SH'}).text or 0),
                                            "sf": int(row.find(attrs={'data-stat': 'SF'}).text or 0),
                                            "ibb": int(row.find(attrs={'data-stat': 'IBB'}).text or 0),
                                            "roe": int(row.find(attrs={'data-stat': 'ROE'}).text or 0),
                                            "bAbip": float(row.find(attrs={'data-stat': 'batting_avg_bip'}).text or 0),
                                            "tOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_total'}).text or 0),
                                            "sOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_lg'}).text or 0),
                                            "dateModified": time.strftime('%Y-%m-%dT%H:%M:%S')
                                        }

                                        # Post data for extra innings (inning 10)
                                        if pitcher_inning_exists(session, pitcher_id, inning):
                                            post_to_api(session, 'PitcherByInningStats', pitcher_inning_data, is_update=True)
                                        else:
                                            post_to_api(session, 'PitcherByInningStats', pitcher_inning_data)
                                    except AttributeError as e:
                                        print(f"Error parsing extra inning data for pitcher: {pitcher_id}. Error: {e}")
                                else:
                                    print(f"Skipping row with split_name: {split_name}")

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
                                    "Year": year,
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
    
    # Scrape and post both inning-specific data and home/away splits data
    scrape_and_post_pitcher_data(session, pitcher_id, year)
