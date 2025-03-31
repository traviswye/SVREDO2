import cloudscraper
from bs4 import BeautifulSoup
import datetime
import urllib3
import random
import time

# Suppress HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import requests and disable its warnings too
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Define the API endpoints
API_HITTING_ENDPOINT = "https://localhost:44346/api/TeamTotalBattingTracking"
API_PITCHING_ENDPOINT = "https://localhost:44346/api/TeamTotalPitchingTracking"

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
        'cache-control': 'no-cache',
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

def scrape_batting_data(scraper, url, year):
    try:
        print(f"Requesting batting data from: {url}")
        response = scraper.get(url)
        response.raise_for_status()
        
        # Add small delay to mimic human reading time
        time.sleep(random.uniform(3, 7))
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        league = "AL" if "AL" in url else "NL"
        table = soup.find("table", id="teams_standard_batting")
        if not table:
            print(f"No table found on URL: {url}")
            return []

        headers = [th.get("data-stat", th.text.strip()) for th in table.find("thead").find_all("th")]
        print(f"Headers found: {headers}")

        rows = table.find("tbody").find_all("tr")
        print(f"Number of rows found: {len(rows)}")

        data = []
        for row in rows:
            if not row.find("td") and not row.find("th", {"data-stat": "team_name"}):
                continue

            team_name_element = row.find("th", {"data-stat": "team_name"})
            team_name = team_name_element.text.strip() if team_name_element else "Unknown"

            if team_name == "League Average":
                team_name = f"{league} Average"

            cells = row.find_all("td")
            row_data = {headers[idx + 1]: cell.text.strip() for idx, cell in enumerate(cells)}

            if "2B" in row_data:
                row_data["Doubles"] = row_data.pop("2B")
            if "3B" in row_data:
                row_data["Triples"] = row_data.pop("3B")

            row_data["TeamName"] = team_name
            row_data["Year"] = year
            row_data["DateAdded"] = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Handle Athletics team special case
            if "AL" in url:
                row_data = handle_athletics_team(row_data, "AL")

            print(f"Processed team: {team_name}")
            send_to_api(scraper, row_data, API_HITTING_ENDPOINT)

            data.append(row_data)

        return data

    except Exception as e:
        print(f"Error occurred while scraping {url}: {e}")
        return []

def scrape_pitching_data(scraper, url, year):
    try:
        print(f"Requesting pitching data from: {url}")
        response = scraper.get(url)
        response.raise_for_status()
        
        # Add small delay to mimic human reading time
        time.sleep(random.uniform(3, 7))
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        league = "AL" if "AL" in url else "NL"
        table = soup.find("table", id="teams_standard_pitching")
        if not table:
            print(f"No table found on URL: {url}")
            return []

        table_headers = [th.get("data-stat", th.text.strip()) for th in table.find("thead").find_all("th")]
        print(f"Headers found: {table_headers}")

        rows = table.find("tbody").find_all("tr")
        print(f"Number of rows found: {len(rows)}")

        data = []
        for row in rows:
            if not row.find("td") and not row.find("th", {"data-stat": "team_name"}):
                continue

            team_name_element = row.find("th", {"data-stat": "team_name"})
            team_name = team_name_element.text.strip() if team_name_element else "Unknown"

            if team_name == "League Average":
                team_name = f"{league} Average"

            cells = row.find_all("td")
            row_data = {table_headers[idx + 1]: cell.text.strip() for idx, cell in enumerate(cells)}

            # Map all fields to EF columns
            key_mapping = {
                "Tm": "TeamName",
                "pitchers_used": "PitchersUsed",
                "age_pitch": "PAge",
                "runs_allowed_per_game": "RAG",
                "W": "W",
                "L": "L",
                "win_loss_perc": "WLPercentage",
                "earned_run_avg": "ERA",
                "G": "G",
                "GS": "GS",
                "GF": "GF",
                "CG": "CG",
                "SHO_team": "TSho",
                "SHO_cg": "CSho",
                "SV": "SV",
                "IP": "IP",
                "H": "H",
                "R": "R",
                "ER": "ER",
                "HR": "HR",
                "BB": "BB",
                "IBB": "IBB",
                "SO": "SO",
                "HBP": "HBP",
                "BK": "BK",
                "WP": "WP",
                "batters_faced": "BF",
                "earned_run_avg_plus": "ERAPlus",
                "fip": "FIP",
                "whip": "WHIP",
                "hits_per_nine": "H9",
                "home_runs_per_nine": "HR9",
                "bases_on_balls_per_nine": "BB9",
                "strikeouts_per_nine": "SO9",
                "strikeouts_per_base_on_balls": "SOW",
                "LOB": "LOB"
            }

            # Apply mapping
            mapped_data = {key_mapping.get(k, k): v for k, v in row_data.items()}

            # Add remaining required keys
            mapped_data["TeamName"] = team_name
            mapped_data["Year"] = year
            mapped_data["DateAdded"] = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Handle Athletics team special case
            if "AL" in url:
                mapped_data = handle_athletics_team(mapped_data, "AL")

            # Ensure all keys exist in the payload
            for column in key_mapping.values():
                if column not in mapped_data:
                    mapped_data[column] = None  # Add missing keys with `None`

            print(f"Processed team: {team_name}")
            send_to_api(scraper, mapped_data, API_PITCHING_ENDPOINT)

            data.append(mapped_data)

        return data

    except Exception as e:
        print(f"Error occurred while scraping {url}: {e}")
        return []

def send_to_api(scraper, row_data, base_endpoint):
    try:
        # Create a new session specifically for API calls with proper SSL settings
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        
        session = requests.Session()
        session.verify = False
        
        team_name = row_data['TeamName']
        year = row_data['Year']
        
        # First, check if the team already exists by trying to GET it
        get_endpoint = f"{base_endpoint}/{team_name}/{year}"
        try:
            get_response = session.get(get_endpoint)
            team_exists = get_response.status_code == 200
        except Exception:
            # If we can't determine if it exists, assume it doesn't
            team_exists = False
        
        if team_exists:
            # Team exists, use PUT to update
            put_endpoint = f"{base_endpoint}/{team_name}/{year}"
            response = session.put(put_endpoint, json=row_data)
            if response.status_code in [200, 204]:
                print(f"✓ Successfully updated data for {team_name} (Year: {year})")
            else:
                print(f"✗ Failed to update data for {team_name} (Year: {year}): {response.status_code} - {response.text}")
        else:
            # Team doesn't exist, use POST to create
            response = session.post(base_endpoint, json=row_data)
            if response.status_code == 201:
                print(f"+ Successfully created data for {team_name} (Year: {year})")
            else:
                print(f"✗ Failed to create data for {team_name} (Year: {year}): {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Error while sending data to API: {e}")

def handle_athletics_team(data, league="AL"):
    """Special handling for the Athletics team - ensures league is set correctly"""
    if data["TeamName"] == "Athletics":
        # Only set the league to AL (American League) if needed
        if "Lg" in data:
            data["Lg"] = league
    return data

def main():
    # URLs to scrape
    hitting_urls = [
        "https://www.baseball-reference.com/leagues/NL/2025-standard-batting.shtml",
        "https://www.baseball-reference.com/leagues/AL/2025-standard-batting.shtml"
    ]
    pitching_urls = [
        "https://www.baseball-reference.com/leagues/AL/2025-standard-pitching.shtml",
        "https://www.baseball-reference.com/leagues/NL/2025-standard-pitching.shtml"
    ]
    
    # Also add the majors URL
    majors_batting_url = "https://www.baseball-reference.com/leagues/majors/2025-standard-batting.shtml"
    
    # Create a scraper session
    scraper = create_scraper_session()
    
    # Try to simulate human browsing to establish cookies and session
    if not simulate_human_browsing(scraper):
        print("Failed to establish proper browsing session. Exiting.")
        return
    
    # Add random delay before starting the actual scraping
    delay = random.uniform(5, 10)
    print(f"Waiting for {delay:.2f} seconds before starting scraping...")
    time.sleep(delay)
    
    # Scrape hitting data
    print("\n==== Scraping Hitting Data ====")
    for url in hitting_urls:
        year = 2025
        print(f"\nScraping hitting data for {url}...")
        scrape_batting_data(scraper, url, year)
        
        # Add delay between different league pages
        time.sleep(random.uniform(8, 15))
    
    # Also scrape majors batting data
    print(f"\nScraping majors hitting data for {majors_batting_url}...")
    scrape_batting_data(scraper, majors_batting_url, 2025)
    
    # Add longer delay before switching to pitching data
    delay = random.uniform(10, 20)
    print(f"Waiting for {delay:.2f} seconds before starting pitching data scraping...")
    time.sleep(delay)
    
    # Scrape pitching data
    print("\n==== Scraping Pitching Data ====")
    for url in pitching_urls:
        year = 2025
        print(f"\nScraping pitching data for {url}...")
        scrape_pitching_data(scraper, url, year)
        
        # Add delay between different league pages
        time.sleep(random.uniform(8, 15))

if __name__ == "__main__":
    main()