# Import required libraries
import requests
import cloudscraper
from bs4 import BeautifulSoup, Comment
import time
import json
from datetime import datetime
import sys
import random

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import requests and disable its warnings too
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Sample user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

# Create a cloudscraper session
def create_scraper_session():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': random.choice(USER_AGENTS)
    }
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    scraper.headers.update(headers)
    return scraper

# Mimic human browsing behavior
def simulate_human_browsing(scraper):
    print("Simulating human browsing pattern...")
    
    # First visit the homepage
    homepage_url = "https://www.baseball-reference.com"
    print(f"Visiting homepage: {homepage_url}")
    homepage_response = scraper.get(homepage_url)
    
    if homepage_response.status_code != 200:
        print(f"Failed to access homepage: {homepage_response.status_code}")
        return False
    
    # Parse the homepage to find random links to visit
    soup = BeautifulSoup(homepage_response.content, "html.parser")
    links = soup.find_all("a", href=True)
    
    # Filter out external links, focus on internal navigation
    internal_links = [link['href'] for link in links if link['href'].startswith('/') 
                     and not link['href'].startswith('//') 
                     and not 'javascript:' in link['href']]
    
    # Visit 2-3 random pages to establish browsing pattern
    for _ in range(random.randint(2, 3)):
        if not internal_links:
            break
            
        random_link = random.choice(internal_links)
        internal_links.remove(random_link)
        
        full_url = f"https://www.baseball-reference.com{random_link}"
        print(f"Visiting random page: {full_url}")
        
        try:
            random_page_response = scraper.get(full_url)
            print(f"Status code: {random_page_response.status_code}")
            
            # Add random delay between page visits (2-5 seconds)
            delay = random.uniform(2, 5)
            print(f"Waiting for {delay:.2f} seconds...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error visiting random page: {e}")
    
    print("Human browsing simulation completed")
    return True

# Create API session for non-BR requests
def create_api_session():
    session = requests.Session()
    session.verify = False
    return session

# Function to get the first letter of the pitcher_id for URL construction
def get_url_letter(pitcher_id):
    return pitcher_id[0]

# Function to check if the pitcher exists in the database
def pitcher_1st_inning_exists(api_session, bbrefID, year):
    url = f"https://localhost:44346/api/Pitcher1stInning/{bbrefID}/{year}"
    print(f"Checking if pitcher exists in the database: {bbrefID}/{year}")
    
    response = api_session.get(url, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} exists in the database.")
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} does not exist in the database.")
    else:
        print(f"Error checking pitcher existence. Status code: {response.status_code}")
    
    return response.status_code == 200

# Function to check if a home/away split exists in the database
def pitcher_home_away_split_exists(api_session, bbrefID, year, split):
    url = f"https://localhost:44346/api/PitcherHomeAwaySplits/{bbrefID}/{year}/{split}"
    print(f"Checking if pitcher home/away split exists in the database: {bbrefID}, {year}, {split}")
    
    response = api_session.get(url, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} {split} split for {year} exists in the database.")
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} {split} split for {year} does not exist in the database.")
    else:
        print(f"Error checking pitcher home/away split existence. Status code: {response.status_code}")
    
    return response.status_code == 200

# Function to check if a platoon and track record exists in the database
def pitcher_platoon_and_track_record_exists(api_session, bbrefID, year, split):
    url = f"https://localhost:44346/api/PitcherPlatoonAndTrackRecord/{bbrefID}/{year}/{split}"
    print(f"Checking if pitcher split exists in the database: {bbrefID}, {year}, {split}")
    
    response = api_session.get(url, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} {split} split for {year} exists in the database.")
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} {split} split for {year} does not exist in the database.")
    else:
        print(f"Error checking pitcher split existence. Status code: {response.status_code}")
    
    return response.status_code == 200

# Updated post_to_api function to handle all scenarios
def post_to_api(api_session, endpoint, data, is_update=False):
    if data is None:
        print(f"No data to post to {endpoint}.")
        return

    # Add DateModified field with current timestamp
    data["DateModified"] = datetime.utcnow().isoformat() + "Z"  # Adding UTC timestamp

    url = f"https://localhost:44346/api/{endpoint}"
    
    # Handle specific endpoints with additional parameters in the URL
    if is_update and 'Year' in data and 'Split' in data:
        url += f"/{data['bbrefID']}/{data['Year']}/{data['Split']}"
    elif is_update:
        url += f"/{data['bbrefID']}/{data['Year']}"  # General case for 1st inning or other endpoints
    
    json_data = json.dumps(data)  # Convert the data to a JSON string
    
    # Print the CURL equivalent command for debugging
    curl_command = f"curl -X {'PUT' if is_update else 'POST'} \\\n  '{url}' \\\n  -H 'Content-Type: application/json' \\\n  -d '{json_data}'"
    print(f"Equivalent CURL command:\n{curl_command}\n")
    
    response = api_session.put(url, data=json_data, headers={'Content-Type': 'application/json'}) if is_update else api_session.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    
    if response.status_code in [200, 201, 204]:
        print(f"Successfully {'updated' if is_update else 'posted'} data to {endpoint} for {data['bbrefID']}.")
    elif response.status_code == 429:
        print(f"Rate limit exceeded while trying to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefID']}.")
    else:
        print(f"Failed to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefID']}. Status code: {response.status_code}")
        print(f"Response content: {response.content}")

# Function to check if a pitcher's totals exist
def pitcher_totals_exists(api_session, bbrefID, year):
    url = f"https://localhost:44346/api/PitcherPlatoonAndTrackRecord/{bbrefID}/{year}/Totals"
    print(f"Checking if pitcher totals exist for {year}: {bbrefID}")
    
    response = api_session.get(url, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} totals for {year} exist.")
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} totals for {year} do not exist.")
    else:
        print(f"Error checking pitcher totals existence for {year}. Status code: {response.status_code}")
    
    return response.status_code == 200

# Function to get the list of pitchers from the GamePreviews API by date
def get_pitchers_from_game_previews(api_session, date):
    url = f"https://localhost:44346/api/GamePreviews/{date}"
    response = api_session.get(url, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        games = response.json()
        pitchers = []
        for game in games:
            if game.get('homePitcher') and game['homePitcher'] != "Unannounced":
                pitchers.append(game['homePitcher'])
            if game.get('awayPitcher') and game['awayPitcher'] != "Unannounced":
                pitchers.append(game['awayPitcher'])
        print(f"Found {len(pitchers)} announced pitchers for {date}")
        return pitchers
    else:
        print(f"Failed to retrieve game previews for {date}. Status code: {response.status_code}")
        return []

# Function to scrape totals for a specific year
def scrape_pitcher_totals_for_year(scraper, api_session, pitcher_id, year):
    # Add random delay before fetching historical data
    delay = random.uniform(5, 8)
    print(f"Waiting for {delay:.2f} seconds before fetching {year} data for {pitcher_id}...")
    time.sleep(delay)
    
    url = f"https://www.baseball-reference.com/players/split.fcgi?id={pitcher_id}&year={year}&t=p"
    print(f"Scraping data from URL: {url}")

    try:
        # Update referer to look more realistic
        scraper.headers.update({'Referer': f"https://www.baseball-reference.com/players/{pitcher_id[0]}/"})
        response = scraper.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page for pitcher {pitcher_id} in {year}. Status code: {response.status_code}")
            return None
            
        # Check if we might be getting a captcha or empty response
        if len(response.content) < 5000:  # Suspiciously small response
            print(f"Warning: Very small response received ({len(response.content)} bytes). Possible captcha or block.")
            return None

        # Add small delay to mimic human reading time
        time.sleep(random.uniform(1, 3))
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Scrape Season Totals Data
        content_div = soup.find('div', id='content')
        if content_div:
            all_divs = content_div.find_all('div', id=lambda value: value and value.startswith('all_'))

            # Scrape Season Totals Data (all_divs[0])
            if len(all_divs) >= 1:
                target_div = all_divs[0]
                comments = target_div.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    div_totals = comment_soup.find('div', id='div_total')
                    if div_totals:
                        print(f"Found 'div_total' div within comment for pitcher {pitcher_id}")
                        totals_table = div_totals.find('table', id='total')
                        if totals_table:
                            print(f"Found 'total' table for pitcher {pitcher_id}")
                            tbody = totals_table.find('tbody')
                            if tbody:
                                rows = tbody.find_all('tr')
                                split_mapping = {
                                    f'{year} Totals': 'Totals',
                                }
                                for row in rows:
                                    split_name = row.find('th', {'data-stat': 'split_name'}).text.strip()
                                    if split_name in split_mapping:
                                        split_type = split_mapping[split_name]
                                        season_totals_data = {
                                            "bbrefID": pitcher_id,
                                            "Year": year,
                                            "Split": split_type,
                                            "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
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
                                            "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
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
                                    if pitcher_home_away_split_exists(api_session, pitcher_id, year, split_type):
                                        post_to_api(api_session, f'PitcherHomeAwaySplits', home_away_data, is_update=True)
                                    else:
                                        post_to_api(api_session, 'PitcherHomeAwaySplits', home_away_data)
        
        # Add a small delay before processing next section
        time.sleep(random.uniform(1, 2))
        
        # Last number of days stats
        content_div = soup.find('div', id='content')
        if content_div:
            all_divs = content_div.find_all('div', id=lambda value: value and value.startswith('all_'))

            # Scrape Season Totals Data (all_divs[0])
            if len(all_divs) >= 1:
                target_div = all_divs[0]
                
                # Add a slight delay before processing comments
                time.sleep(random.uniform(0.5, 1))
                
                comments = target_div.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    div_totals = comment_soup.find('div', id='div_total')
                    if div_totals:
                        print(f"Found 'div_total' div within comment for pitcher {pitcher_id}")
                        totals_table = div_totals.find('table', id='total')
                        if totals_table:
                            print(f"Found 'total' table for pitcher {pitcher_id}")
                            tbody = totals_table.find('tbody')
                            if tbody:
                                rows = tbody.find_all('tr')
                                split_mapping = {
                                    f'{year} Totals': 'Totals',
                                    'Last 7 days': 'last7',
                                    'Last 14 days': 'last14',
                                    'Last 28 days': 'last28'
                                }
                                for row in rows:
                                    split_name = row.find('th', {'data-stat': 'split_name'}).text.strip()
                                    if split_name in split_mapping:
                                        split_type = split_mapping[split_name]
                                        season_totals_data = {
                                            "bbrefID": pitcher_id,
                                            "Year": year,
                                            "Split": split_type,
                                            "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
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
                                            "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
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
                                        # Post or update the scraped data to your API
                                        if pitcher_platoon_and_track_record_exists(api_session, pitcher_id, year, split_type):
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', season_totals_data, is_update=True)
                                        else:
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', season_totals_data)
            
            # Scrape Platoon Splits Data (all_divs[1])
            if len(all_divs) >= 2:
                target_div = all_divs[1]
                # Add a slight delay before processing
                time.sleep(random.uniform(0.5, 1))
                comments = target_div.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    div_platoon = comment_soup.find('div', id='div_plato')
                    if div_platoon:
                        print(f"Found 'div_plato' div within comment for pitcher {pitcher_id}")
                        platoon_table = div_platoon.find('table', id='plato')
                        if platoon_table:
                            print(f"Found 'plato' table for pitcher {pitcher_id}")
                            tbody = platoon_table.find('tbody')
                            if tbody:
                                rows = tbody.find_all('tr')
                                split_mapping = {
                                    'vs RHB': 'vsRHB',
                                    'vs LHB': 'vsLHB'
                                }
                                for row in rows:
                                    split_name = row.find('th', {'data-stat': 'split_name'}).text.strip()
                                    if split_name in split_mapping:
                                        split_type = split_mapping[split_name]
                                        platoon_data = {
                                            "bbrefID": pitcher_id,
                                            "Year": year,
                                            "Split": split_type,
                                            "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
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
                                            "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
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
                                        if pitcher_platoon_and_track_record_exists(api_session, pitcher_id, year, split_type):
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', platoon_data, is_update=True)
                                        else:
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', platoon_data)
    except Exception as e:
        print(f"Error scraping data for pitcher {pitcher_id}: {e}")
        return None


# Combined scraping function to scrape both first inning and home/away splits data
def scrape_and_post_pitcher_data(scraper, api_session, pitcher_id, year):
    # Wait to avoid hitting rate limits - use random delay
    delay = random.uniform(6, 10)
    print(f"Waiting for {delay:.2f} seconds before fetching data for {pitcher_id}...")
    time.sleep(delay)
    
    url = f"https://www.baseball-reference.com/players/split.fcgi?id={pitcher_id}&year={year}&t=p"
    print(f"Scraping data from URL: {url}")
    
    try:
        # Add referer for more realistic request
        scraper.headers.update({'Referer': 'https://www.baseball-reference.com/players/'})
        response = scraper.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page for pitcher {pitcher_id}. Status code: {response.status_code}")
            return None
            
        # Add small delay to mimic human reading time
        time.sleep(random.uniform(2, 4))
        
        # Check if we might be getting a captcha or empty response
        if len(response.content) < 5000:  # Suspiciously small response
            print(f"Warning: Very small response received ({len(response.content)} bytes). Possible captcha or block.")
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
                                            "Year": year,
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
                                        if pitcher_1st_inning_exists(api_session, pitcher_id, year):
                                            post_to_api(api_session, 'Pitcher1stInning', pitcher_1st_inning_data, is_update=True)
                                        else:
                                            post_to_api(api_session, 'Pitcher1stInning', pitcher_1st_inning_data)
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
                                        "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
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
                                    if pitcher_home_away_split_exists(api_session, pitcher_id, year, split_type):
                                        post_to_api(api_session, f'PitcherHomeAwaySplits', home_away_data, is_update=True)
                                    else:
                                        post_to_api(api_session, 'PitcherHomeAwaySplits', home_away_data)
        
        # Add a small delay before processing next section
        time.sleep(random.uniform(1, 2))
        
        # Last number of days stats
        content_div = soup.find('div', id='content')
        if content_div:
            all_divs = content_div.find_all('div', id=lambda value: value and value.startswith('all_'))

            # Scrape Season Totals Data (all_divs[0])
            if len(all_divs) >= 1:
                target_div = all_divs[0]
                
                # Add a slight delay before processing comments
                time.sleep(random.uniform(0.5, 1))
                
                comments = target_div.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    div_totals = comment_soup.find('div', id='div_total')
                    if div_totals:
                        print(f"Found 'div_total' div within comment for pitcher {pitcher_id}")
                        totals_table = div_totals.find('table', id='total')
                        if totals_table:
                            print(f"Found 'total' table for pitcher {pitcher_id}")
                            tbody = totals_table.find('tbody')
                            if tbody:
                                rows = tbody.find_all('tr')
                                split_mapping = {
                                    f'{year} Totals': 'Totals',
                                    'Last 7 days': 'last7',
                                    'Last 14 days': 'last14',
                                    'Last 28 days': 'last28'
                                }
                                for row in rows:
                                    split_name = row.find('th', {'data-stat': 'split_name'}).text.strip()
                                    if split_name in split_mapping:
                                        split_type = split_mapping[split_name]
                                        season_totals_data = {
                                            "bbrefID": pitcher_id,
                                            "Year": year,
                                            "Split": split_type,
                                            "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
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
                                            "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
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
                                        # Post or update the scraped data to your API
                                        if pitcher_platoon_and_track_record_exists(api_session, pitcher_id, year, split_type):
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', season_totals_data, is_update=True)
                                        else:
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', season_totals_data)
            
            # Scrape Platoon Splits Data (all_divs[1])
            if len(all_divs) >= 2:
                target_div = all_divs[1]
                # Add a slight delay before processing
                time.sleep(random.uniform(0.5, 1))
                comments = target_div.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    div_platoon = comment_soup.find('div', id='div_plato')
                    if div_platoon:
                        print(f"Found 'div_plato' div within comment for pitcher {pitcher_id}")
                        platoon_table = div_platoon.find('table', id='plato')
                        if platoon_table:
                            print(f"Found 'plato' table for pitcher {pitcher_id}")
                            tbody = platoon_table.find('tbody')
                            if tbody:
                                rows = tbody.find_all('tr')
                                split_mapping = {
                                    'vs RHB': 'vsRHB',
                                    'vs LHB': 'vsLHB'
                                }
                                for row in rows:
                                    split_name = row.find('th', {'data-stat': 'split_name'}).text.strip()
                                    if split_name in split_mapping:
                                        split_type = split_mapping[split_name]
                                        platoon_data = {
                                            "bbrefID": pitcher_id,
                                            "Year": year,
                                            "Split": split_type,
                                            "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
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
                                            "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
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
                                        if pitcher_platoon_and_track_record_exists(api_session, pitcher_id, year, split_type):
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', platoon_data, is_update=True)
                                        else:
                                            post_to_api(api_session, 'PitcherPlatoonAndTrackRecord', platoon_data)
    except Exception as e:
        print(f"Error scraping data for pitcher {pitcher_id}: {e}")
        return None

# Main scraping logic for pitchers, now with checks for 2024 totals
def scrape_and_post_pitcher_data_helper(scraper, api_session, pitcher_id, year):
    # Check if 2024 totals exist before proceeding with 2025
    if not pitcher_totals_exists(api_session, pitcher_id, 2024):
        print(f"Scraping and posting 2024 totals for pitcher: {pitcher_id}")
        # Scrape 2024 totals only
        scrape_pitcher_totals_for_year(scraper, api_session, pitcher_id, 2024)
        # Add a longer delay after scraping 2024 data
        delay = random.uniform(8, 12)
        print(f"Waiting {delay:.2f} seconds after processing 2024 data...")
        time.sleep(delay)

    # Continue with scraping and posting 2025 data
    print(f"Scraping and posting 2025 data for pitcher: {pitcher_id}")
    scrape_and_post_pitcher_data(scraper, api_session, pitcher_id, 2025)

# Main execution function
def main():
    print("Starting Baseball Reference data scraper with enhanced anti-detection measures")
    
    # Check if a date argument is provided via command line
    if len(sys.argv) > 1:
        date = sys.argv[1]  # Use the first argument as the date
    else:
        # Fallback to the default date if not provided
        date = "25-03-31"  # Today's date by default
    
    year = 2025  # Current season
    
    # Create a CloudScraper session for Baseball Reference
    scraper = create_scraper_session()
    
    # Simulate human browsing to avoid detection
    if not simulate_human_browsing(scraper):
        print("Failed to establish browsing pattern. Exiting...")
        return
    
    # Create a regular session for API calls
    api_session = create_api_session()
    
    # Get the list of pitchers from the GamePreviews API
    pitchers = get_pitchers_from_game_previews(api_session, date)
    
    if not pitchers:
        print(f"No pitchers found for date {date}. Exiting...")
        return
    
    print(f"Found {len(pitchers)} pitchers to process for {date}")
    
    # Add a delay before starting to scrape pitchers
    time.sleep(random.uniform(3, 5))
    
    # Process pitchers with random order to appear less bot-like
    random.shuffle(pitchers)
    
    # Loop through each pitcher and scrape & post data
    for idx, pitcher_id in enumerate(pitchers):
        if pitcher_id.lower() == "unannounced":
            print(f"Skipping pitcher: {pitcher_id}")
            continue
        
        print(f"Processing pitcher {idx+1}/{len(pitchers)}: {pitcher_id}")
        
        # Scrape and post data from Baseball Reference
        scrape_and_post_pitcher_data_helper(scraper, api_session, pitcher_id, year)
        
        # Add a longer delay between pitchers to avoid detection
        if idx < len(pitchers) - 1:  # Don't delay after the last pitcher
            delay = random.uniform(12, 20)
            print(f"Waiting {delay:.2f} seconds before processing the next pitcher...")
            time.sleep(delay)
    
    print("All pitchers processed successfully!")

if __name__ == "__main__":
    main()