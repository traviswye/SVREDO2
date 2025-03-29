import cloudscraper
from bs4 import BeautifulSoup, Comment
import json
from datetime import datetime
import re
import time
import urllib3
import logging
import os
import ssl
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bbref_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a custom SSL context - disabling verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# List of user agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

# Custom retry strategy
retries = Retry(
    total=5,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Method 1: Enhanced cloudscraper
try:
    scraper1 = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=5,
        ssl_context=ssl_context,
        allow_brotli=True
    )
    scraper1.verify = False
    scraper1.trust_env = False
except Exception as e:
    logger.warning(f"Failed to create scraper1: {e}")
    scraper1 = None

# Method 2: Standard requests with proper headers
try:
    scraper2 = requests.Session()
    adapter = HTTPAdapter(max_retries=retries)
    scraper2.mount("http://", adapter)
    scraper2.mount("https://", adapter)
except Exception as e:
    logger.warning(f"Failed to create scraper2: {e}")
    scraper2 = None

current_datetime = datetime.now().isoformat()

# Team abbreviation dictionary
team_abbreviations = {
    'Diamondbacks': 'ARI', 'Braves': 'ATL', 'Orioles': 'BAL', 'Red Sox': 'BOS', 
    'Cubs': 'CHC', 'White Sox': 'CHW', 'Reds': 'CIN', 'Guardians': 'CLE',
    'Rockies': 'COL', 'Tigers': 'DET', 'Astros': 'HOU', 'Royals': 'KCR', 
    'Angels': 'LAA', 'Dodgers': 'LAD', 'Marlins': 'MIA', 'Brewers': 'MIL',
    'Twins': 'MIN', 'Mets': 'NYM', 'Yankees': 'NYY', 'Athletics': 'OAK',
    'Phillies': 'PHI', 'Pirates': 'PIT', 'Padres': 'SDP', 'Mariners': 'SEA',
    'Giants': 'SFG', 'Cardinals': 'STL', 'Rays': 'TBR', 'Rangers': 'TEX',
    'Blue Jays': 'TOR', 'Nationals': 'WSN'
}

# Team leagues mapping
team_leagues = {
    "ARI": "NL", "ATL": "NL", "BAL": "AL", "BOS": "AL", "CHC": "NL", "CHW": "AL",
    "CIN": "NL", "CLE": "AL", "COL": "NL", "DET": "AL", "HOU": "AL", "KCR": "AL",
    "LAA": "AL", "LAD": "NL", "MIA": "NL", "MIL": "NL", "MIN": "AL", "NYM": "NL",
    "NYY": "AL", "OAK": "AL", "PHI": "NL", "PIT": "NL", "SDP": "NL", "SEA": "AL",
    "SFG": "NL", "STL": "NL", "TBR": "AL", "TEX": "AL", "TOR": "AL", "WSN": "NL"
}

# Utility functions
def safe_int_conversion(value, default=0):
    try:
        return int(value) if value and value.strip() else default
    except (ValueError, TypeError, AttributeError):
        return default

def safe_float_conversion(value, default=0.0):
    try:
        return float(value) if value and value.strip() else default
    except (ValueError, TypeError, AttributeError):
        return default

def get_league_by_team(team_abbr):
    return team_leagues.get(team_abbr, "Unknown")

def get_team_from_row(row, team_col_index):
    try:
        team_cell = row.find_all('td')[team_col_index]
        if team_cell:
            team_text = team_cell.text.strip()
            if team_text.find('/') > -1:
                team_text = team_text.split('/')[-1].strip()
            return team_text
    except (IndexError, AttributeError) as e:
        logger.warning(f"Error extracting team: {e}")
    return None

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def get_random_header():
    """Generate a random-looking header that mimics a real browser."""
    user_agent = get_random_user_agent()
    accept_language = random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.9,en-US;q=0.8', 'en;q=0.9,fr;q=0.8'])
    accept_encoding = random.choice(['gzip, deflate, br', 'gzip, deflate'])
    
    headers = {
        'User-Agent': user_agent,
        'Accept-Language': accept_language,
        'Accept-Encoding': accept_encoding,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': random.choice(['none', 'same-origin']),
        'Sec-Fetch-User': '?1',
        'Cache-Control': random.choice(['max-age=0', 'no-cache']),
        'Pragma': random.choice(['no-cache', '']),
        'DNT': random.choice(['1', '0']),
        'Referer': 'https://www.google.com/'
    }
    
    # Add some randomness to the headers
    if random.random() > 0.5:
        headers['Sec-Ch-Ua'] = '"Google Chrome";v="123", "Not.A/Brand";v="8"'
        headers['Sec-Ch-Ua-Mobile'] = '?0'
        headers['Sec-Ch-Ua-Platform'] = '"Windows"'
    
    return headers

def send_data_to_db(endpoint, data, id_fields):
    """Generic function to send data to the database via API"""
    try:
        base_url = "https://localhost:44346/api"
        
        # Debug log to see exactly what data we're sending
        logger.debug(f"Sending data to {endpoint}: {json.dumps(data, indent=2)}")
        
        # Verify all required fields exist in the data dictionary
        missing_fields = [field for field in id_fields if field not in data]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            for field in missing_fields:
                logger.error(f"Available fields: {list(data.keys())}")
            raise KeyError(f"Missing required fields: {missing_fields}")
        
        # Handle both string and list formats for backward compatibility
        if isinstance(id_fields, str):
            # Old-style single field API
            id_path = data[id_fields]
        else:
            # New-style composite key API - ensure we're using keys that actually exist
            id_values = [str(data[field]) for field in id_fields]
            id_path = "/".join(id_values)
        
        api_url_get = f"{base_url}/{endpoint}/{id_path}"
        api_url_put = f"{base_url}/{endpoint}/{id_path}"
        api_url_post = f"{base_url}/{endpoint}"

        # Use a session with retry
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.verify = False

        # Check if the record exists
        response = session.get(api_url_get, verify=False)
        
        if response.status_code == 200:
            # Record exists, update
            put_response = session.put(api_url_put, json=data, verify=False)
            if put_response.status_code in [200, 204]:
                logger.info(f"Successfully updated {endpoint} {id_path}.")
            else:
                logger.error(f"Failed to update {endpoint} {id_path}. Response: {put_response.status_code} - {put_response.text}")
        elif response.status_code == 404:
            # Record does not exist, create
            post_response = session.post(api_url_post, json=data, verify=False)
            if post_response.status_code == 201:
                logger.info(f"Successfully created {endpoint} {id_path}.")
            else:
                logger.error(f"Failed to create {endpoint} {id_path}. Response: {post_response.status_code} - {post_response.text}")
        else:
            logger.error(f"Error checking existence of {endpoint} {id_path}. Response: {response.status_code} - {response.text}")

    except KeyError as ke:
        logger.error(f"Error sending data to the database: {ke}")
    except Exception as e:
        logger.error(f"Error sending data to the database: {e}")
def send_pitcher_data_to_db(pitcher_data, bbref_id):
    pitcher_data["bbrefID"] = bbref_id  # Ensure ID is consistent
    send_data_to_db("Pitchers", pitcher_data, ["bbrefID", "Year", "Team"])

def send_hitter_data_to_db(hitter_data, bbref_id):
    # Ensure ID is consistent
    hitter_data["bbrefId"] = bbref_id
    
    # Ensure all required fields use the correct capitalization expected by the API
    # This maps lowercase keys to their proper capitalized versions
    field_mapping = {
        "year": "Year",
        "team": "Team",
        "lg": "Lg"
    }
    
    # Apply the mappings to ensure proper case
    for lower_key, proper_key in field_mapping.items():
        if lower_key in hitter_data:
            # Create properly capitalized version if it doesn't exist
            if proper_key not in hitter_data:
                hitter_data[proper_key] = hitter_data[lower_key]
    
    # Send to the API with the composite key fields
    send_data_to_db("Hitters", hitter_data, ["bbrefId", "Year", "Team"])

def send_pitcher_data_to_db(pitcher_data, bbref_id):
    pitcher_data["bbrefID"] = bbref_id  # Ensure ID is consistent
    send_data_to_db("Pitchers", pitcher_data, ["bbrefID", "Year", "Team"])

def send_hitter_data_to_db(hitter_data, bbref_id):
    hitter_data["bbrefId"] = bbref_id  # Ensure ID is consistent
    send_data_to_db("Hitters", hitter_data, ["bbrefId", "Year", "Team"])


def wait_with_jitter(base_seconds=1):
    """Wait with random jitter to appear more human-like"""
    jitter = random.uniform(0.5, 1.5) * base_seconds
    time.sleep(jitter)

def save_html_for_debugging(html_content, filename="debug_response.html"):
    """Save HTML content for debugging purposes"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved HTML content to {filename} for debugging")
    except Exception as e:
        logger.error(f"Failed to save HTML for debugging: {e}")

def scrape_with_selenium(url, driver_path=None):
    """Use Selenium to scrape a page, with improved handling of Cloudflare challenges"""
    try:
        logger.info("Attempting to scrape with Selenium...")
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={get_random_user_agent()}")
        options.add_argument("--disable-blink-features=AutomationControlled")  # Try to prevent detection
        
        # Use local chromedriver if available
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=options)
        elif os.path.exists("./chromedriver.exe"):
            # Use local chromedriver in the current directory
            service = Service(executable_path="./chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=options)
        elif os.path.exists("./chromedriver"):
            # For Linux/Mac environments
            service = Service(executable_path="./chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Fall back to automatic installation
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.error(f"Could not set up chromedriver: {e}")
                return None
        
        # Set timeout and get the page
        driver.set_page_load_timeout(60)  # Increased timeout for Cloudflare
        logger.info(f"Navigating to {url} with Selenium...")
        driver.get(url)
        
        # Add extra wait for Cloudflare challenge to resolve
        logger.info("Waiting for Cloudflare to resolve...")
        
        # Wait for the page to load
        try:
            # First, check if we're on a Cloudflare challenge page
            if "cloudflare" in driver.page_source.lower() or "challenge" in driver.page_source.lower():
                logger.info("Detected Cloudflare challenge, waiting for it to resolve...")
                # Wait longer for Cloudflare - try multiple times
                wait_time = 5
                max_attempts = 6  # Total wait time up to 30 seconds
                
                for attempt in range(max_attempts):
                    time.sleep(wait_time)
                    
                    # Check if we're still on the challenge page
                    if "cloudflare" not in driver.page_source.lower() and "challenge" not in driver.page_source.lower():
                        logger.info("Cloudflare challenge appears to be resolved!")
                        break
                    
                    logger.info(f"Still on Cloudflare page after {(attempt+1)*wait_time} seconds, continuing to wait...")
                    
                    # On the last attempt, try refreshing the page
                    if attempt == max_attempts - 2:
                        logger.info("Trying to refresh the page...")
                        driver.refresh()
            
            # Now wait for the actual content to load - look for tables
            try:
                wait = WebDriverWait(driver, 15)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                logger.info("Table element found on page, content appears to be loaded")
            except Exception as e:
                logger.info(f"Timed out waiting for table element, but continuing anyway: {e}")
                # Continue anyway as the page might still be usable
        
        except Exception as e:
            logger.warning(f"Exception during page load wait: {e}")
            # Continue anyway - we might still have useful content
        
        # Get the final page source
        html_content = driver.page_source
        
        # Save for debugging
        save_html_for_debugging(html_content, "selenium_result.html")
        
        # Close the driver
        driver.quit()
        
        logger.info("Selenium scraping completed successfully")
        return html_content
        
    except Exception as e:
        logger.error(f"Error using Selenium: {e}")
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        return None

def scrape_page_with_multiple_methods(url, max_retries=1):
    """Use Selenium directly as the primary method since other methods are failing"""
    logger.info(f"Fetching data from {url} using Selenium")
    html_content = scrape_with_selenium(url)
    if html_content:
        return html_content
    
    # If Selenium fails, try the old methods as fallback (though they're likely to fail too)
    for attempt in range(max_retries):
        if attempt > 0:
            wait_time = random.uniform(3, 5)
            logger.info(f"Waiting {wait_time:.2f} seconds before fallback attempt...")
            time.sleep(wait_time)
        
        logger.info(f"Fallback attempt {attempt + 1}/{max_retries} for {url}")
        headers = get_random_header()
        
        # Try standard methods as fallback
        if scraper1:
            try:
                logger.info("Trying fallback method 1: Enhanced cloudscraper")
                response = scraper1.get(url, headers=headers, timeout=60)
                if response.status_code == 200:
                    logger.info("Fallback method 1 succeeded!")
                    return response.text
                else:
                    logger.warning(f"Fallback method 1 failed with status code: {response.status_code}")
            except Exception as e:
                logger.warning(f"Fallback method 1 exception: {e}")
        
        # Second fallback method
        if scraper2:
            try:
                logger.info("Trying fallback method 2: standard requests with proper headers")
                cookies = {'cf_clearance': ''}
                response = scraper2.get(url, headers=headers, cookies=cookies, timeout=60, verify=False)
                if response.status_code == 200:
                    logger.info("Fallback method 2 succeeded!")
                    return response.text
                else:
                    logger.warning(f"Fallback method 2 failed with status code: {response.status_code}")
            except Exception as e:
                logger.warning(f"Fallback method 2 exception: {e}")
    
    logger.error(f"All methods failed to fetch {url}")
    return None

def extract_table_from_html(html_content, table_search='players_standard_batting'):
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
    
    # Try multiple approaches to find the table
    
    # 1. Direct search
    table = soup.find('table', id=table_search)
    if table:
        logger.info(f"Found table with id '{table_search}' directly in HTML")
        return table
    
    # 2. Search in comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment_soup = BeautifulSoup(comment, 'html.parser')
        table = comment_soup.find('table', id=table_search)
        if table:
            logger.info(f"Found table with id '{table_search}' in HTML comment")
            return table
    
    # 3. Look for tables with specific class attributes that might indicate our target
    all_tables = soup.find_all('table')
    for table in all_tables:
        # Check if the table classes or attributes contain indicators
        if table.get('class') and any(cls for cls in table.get('class') if 'stats_table' in cls or 'players' in cls):
            logger.info(f"Found potential table with matching class: {table.get('class')}")
            return table
            
        # Check if the table has similar column structure
        headers = [th.get('data-stat', '') for th in table.find_all('th')]
        if 'name_display' in headers or 'player' in headers:
            logger.info(f"Found table with player name header: {table.get('id')}")
            return table
    
    # 4. Try more generic approach - find any table with statistics
    for table in all_tables:
        # Look for tables with a reasonable number of columns that might be our target
        if len(table.find_all('th')) > 10:  # Assuming stats tables have many columns
            logger.info(f"Found potential statistics table by column count: {table.get('id')}")
            return table
    
    logger.error(f"Could not find any suitable table in HTML")
    
    # Save the full HTML for debugging
    save_html_for_debugging(html_content, f"debug_missing_table_{table_search}.html")
    
    return None

def scrape_batting_data():
    url = "https://www.baseball-reference.com/leagues/majors/2025-standard-batting.shtml"
    logger.info(f"Fetching batting data from {url}")
    
    try:
        # Use Selenium directly
        html_content = scrape_with_selenium(url)
        if not html_content:
            logger.error("Failed to retrieve batting data")
            return
            
        # Save the content for inspection
        save_html_for_debugging(html_content, "debug_batting.html")
            
        table = extract_table_from_html(html_content, 'players_standard_batting')
        if not table:
            logger.error("Could not find batting table")
            return
            
        logger.info(f"Found batting table with id: {table.get('id', 'No ID')}")
        
        # Get table headers to determine column indices
        headers = [th.get('data-stat', '') for th in table.find('thead').find_all('th')]
        
        # Find indices for important columns using the new header names
        team_col_index = headers.index('team_name_abbr') if 'team_name_abbr' in headers else None
        pos_col_index = headers.index('pos') if 'pos' in headers else None
        
        if team_col_index is None or pos_col_index is None:
            logger.error(f"Could not find required column indices. Headers: {headers}")
            return
            
        # Process rows
        rows = table.find('tbody').find_all('tr')
        logger.info(f"Found {len(rows)} batting rows to process")
        
        processed_count = 0
        for row in rows:
            # Skip header rows or rows without data
            if row.get('class') and ('thead' in row.get('class') or 'stat_total' in row.get('class')):
                continue
                
            try:
                # Extract player info
                name_cell = row.find('td', {'data-stat': 'name_display'})
                
                # Skip if no player name found
                if not name_cell or not name_cell.find('a'):
                    continue
                    
                player_name = name_cell.text.strip()
                
                # Determine batting hand
                if '*' in player_name:
                    bats = 'LH'
                elif '#' in player_name:
                    bats = 'S'
                else:
                    bats = 'RH'
                
                # Clean player name
                player_name = re.sub(r'\s*\(.*\)$', '', player_name).replace('*', '').replace('#', '').strip()
                
                # Extract bbrefID
                href = name_cell.find('a')['href']
                bbref_id = href.split('/')[-1].replace('.shtml', '')
                
                # Extract team abbreviation
                team_abbr = row.find('td', {'data-stat': 'team_name_abbr'}).text.strip()
                if not team_abbr:
                    logger.warning(f"Could not determine team for {player_name}, skipping")
                    continue
                
                # Extract position
                pos_cell = row.find('td', {'data-stat': 'pos'})
                position = pos_cell.text.strip() if pos_cell else ""
                
                # Skip pitchers (we'll handle them in the pitching data)
                if position == 'P':
                    continue
                
                # Extract all the batting stats with the new column names
                age = safe_int_conversion(row.find('td', {'data-stat': 'age'}).text if row.find('td', {'data-stat': 'age'}) else "0")
                g = safe_int_conversion(row.find('td', {'data-stat': 'b_games'}).text if row.find('td', {'data-stat': 'b_games'}) else "0")
                pa = safe_int_conversion(row.find('td', {'data-stat': 'b_pa'}).text if row.find('td', {'data-stat': 'b_pa'}) else "0")
                ab = safe_int_conversion(row.find('td', {'data-stat': 'b_ab'}).text if row.find('td', {'data-stat': 'b_ab'}) else "0")
                r = safe_int_conversion(row.find('td', {'data-stat': 'b_r'}).text if row.find('td', {'data-stat': 'b_r'}) else "0")
                h = safe_int_conversion(row.find('td', {'data-stat': 'b_h'}).text if row.find('td', {'data-stat': 'b_h'}) else "0")
                doubles = safe_int_conversion(row.find('td', {'data-stat': 'b_doubles'}).text if row.find('td', {'data-stat': 'b_doubles'}) else "0")
                triples = safe_int_conversion(row.find('td', {'data-stat': 'b_triples'}).text if row.find('td', {'data-stat': 'b_triples'}) else "0")
                hr = safe_int_conversion(row.find('td', {'data-stat': 'b_hr'}).text if row.find('td', {'data-stat': 'b_hr'}) else "0")
                rbi = safe_int_conversion(row.find('td', {'data-stat': 'b_rbi'}).text if row.find('td', {'data-stat': 'b_rbi'}) else "0")
                sb = safe_int_conversion(row.find('td', {'data-stat': 'b_sb'}).text if row.find('td', {'data-stat': 'b_sb'}) else "0")
                cs = safe_int_conversion(row.find('td', {'data-stat': 'b_cs'}).text if row.find('td', {'data-stat': 'b_cs'}) else "0")
                bb = safe_int_conversion(row.find('td', {'data-stat': 'b_bb'}).text if row.find('td', {'data-stat': 'b_bb'}) else "0")
                so = safe_int_conversion(row.find('td', {'data-stat': 'b_so'}).text if row.find('td', {'data-stat': 'b_so'}) else "0")
                ba = safe_float_conversion(row.find('td', {'data-stat': 'b_batting_avg'}).text if row.find('td', {'data-stat': 'b_batting_avg'}) else "0")
                obp = safe_float_conversion(row.find('td', {'data-stat': 'b_onbase_perc'}).text if row.find('td', {'data-stat': 'b_onbase_perc'}) else "0")
                slg = safe_float_conversion(row.find('td', {'data-stat': 'b_slugging_perc'}).text if row.find('td', {'data-stat': 'b_slugging_perc'}) else "0")
                ops = safe_float_conversion(row.find('td', {'data-stat': 'b_onbase_plus_slugging'}).text if row.find('td', {'data-stat': 'b_onbase_plus_slugging'}) else "0")
                ops_plus = safe_int_conversion(row.find('td', {'data-stat': 'b_onbase_plus_slugging_plus'}).text if row.find('td', {'data-stat': 'b_onbase_plus_slugging_plus'}) else "0")
                tb = safe_int_conversion(row.find('td', {'data-stat': 'b_tb'}).text if row.find('td', {'data-stat': 'b_tb'}) else "0")
                gidp = safe_int_conversion(row.find('td', {'data-stat': 'b_gidp'}).text if row.find('td', {'data-stat': 'b_gidp'}) else "0")
                hbp = safe_int_conversion(row.find('td', {'data-stat': 'b_hbp'}).text if row.find('td', {'data-stat': 'b_hbp'}) else "0")
                sh = safe_int_conversion(row.find('td', {'data-stat': 'b_sh'}).text if row.find('td', {'data-stat': 'b_sh'}) else "0")
                sf = safe_int_conversion(row.find('td', {'data-stat': 'b_sf'}).text if row.find('td', {'data-stat': 'b_sf'}) else "0")
                ibb = safe_int_conversion(row.find('td', {'data-stat': 'b_ibb'}).text if row.find('td', {'data-stat': 'b_ibb'}) else "0")
                
                # Create hitter data payload
                # Create hitter data payload with correct field capitalization
                hitter_data = {
                    "bbrefId": bbref_id,
                    "name": player_name,
                    "age": age,
                    "year": 2025,
                    "Year": 2025,  # Add upper case version explicitly
                    "team": team_abbr,
                    "Team": team_abbr,  # Add upper case version explicitly
                    "lg": get_league_by_team(team_abbr),
                    "Lg": get_league_by_team(team_abbr),  # Add upper case version explicitly
                    "war": 0.0,  # Default value, will be preserved if exists
                    "g": g,
                    "pa": pa,
                    "ab": ab,
                    "r": r,
                    "h": h,
                    "doubles": doubles,
                    "triples": triples,
                    "hr": hr,
                    "rbi": rbi,
                    "sb": sb,
                    "cs": cs,
                    "bb": bb,
                    "so": so,
                    "ba": ba,
                    "obp": obp,
                    "slg": slg,
                    "ops": ops,
                    "opSplus": ops_plus,
                    "rOBA": 0.0,  # Default value, will be preserved if exists
                    "rbatplus": 0,  # Default value, will be preserved if exists
                    "tb": tb,
                    "gidp": gidp,
                    "hbp": hbp,
                    "sh": sh,
                    "sf": sf,
                    "ibb": ibb,
                    "pos": position,
                    "date": current_datetime,
                    "bats": bats
                }
                
                # Send to database
                send_hitter_data_to_db(hitter_data, bbref_id)
                processed_count += 1
                
                # Add a small delay to avoid overwhelming the API
                if processed_count % 10 == 0:
                    time.sleep(0.5)
                    logger.info(f"Processed {processed_count} hitters so far")
                    
            except Exception as e:
                logger.error(f"Error processing batting row: {e}")
                
        logger.info(f"Successfully processed {processed_count} hitters")
        
    except Exception as e:
        logger.error(f"Error scraping batting data: {e}")

def scrape_pitching_data():
    url = "https://www.baseball-reference.com/leagues/majors/2025-standard-pitching.shtml"
    logger.info(f"Fetching pitching data from {url}")
    
    try:
        # Use Selenium directly 
        html_content = scrape_with_selenium(url)
        if not html_content:
            logger.error("Failed to retrieve pitching data")
            return
            
        # Save the content for inspection
        save_html_for_debugging(html_content, "debug_pitching.html")
            
        table = extract_table_from_html(html_content, 'players_standard_pitching')
        if not table:
            logger.error("Could not find pitching table")
            return
            
        logger.info(f"Found pitching table with id: {table.get('id', 'No ID')}")
        
        # Get table headers
        headers = [th.get('data-stat', '') for th in table.find('thead').find_all('th')]
        
        # Find index for team column using the new header name
        team_col_index = headers.index('team_name_abbr') if 'team_name_abbr' in headers else None
        
        if team_col_index is None:
            logger.error(f"Could not find team column index. Headers: {headers}")
            return
            
        # Process rows
        rows = table.find('tbody').find_all('tr')
        logger.info(f"Found {len(rows)} pitching rows to process")
        
        processed_count = 0
        for row in rows:
            # Skip header rows or rows without data
            if row.get('class') and ('thead' in row.get('class') or 'stat_total' in row.get('class')):
                continue
                
            try:
                # Extract player info
                name_cell = row.find('td', {'data-stat': 'name_display'})
                
                # Skip if no player name found
                if not name_cell or not name_cell.find('a'):
                    continue
                    
                player_name = name_cell.text.strip()
                
                # Determine throwing hand
                if '*' in player_name:
                    throws = 'LHP'
                else:
                    throws = 'RHP'
                
                # Clean player name
                player_name = re.sub(r'\s*\(.*\)$', '', player_name).replace('*', '').replace('#', '').strip()
                
                # Extract bbrefID
                href = name_cell.find('a')['href']
                bbref_id = href.split('/')[-1].replace('.shtml', '')
                
                # Extract team abbreviation
                team_abbr = row.find('td', {'data-stat': 'team_name_abbr'}).text.strip()
                if not team_abbr:
                    logger.warning(f"Could not determine team for pitcher {player_name}, skipping")
                    continue
                
                # Extract win-loss record
                wins = safe_int_conversion(row.find('td', {'data-stat': 'p_w'}).text if row.find('td', {'data-stat': 'p_w'}) else "0")
                losses = safe_int_conversion(row.find('td', {'data-stat': 'p_l'}).text if row.find('td', {'data-stat': 'p_l'}) else "0")
                win_loss_record = f"{wins}-{losses}"
                
                # Extract all pitching stats with the new column names
                age = safe_int_conversion(row.find('td', {'data-stat': 'age'}).text if row.find('td', {'data-stat': 'age'}) else "0")
                wlp = safe_float_conversion(row.find('td', {'data-stat': 'p_win_loss_perc'}).text if row.find('td', {'data-stat': 'p_win_loss_perc'}) else "0")
                era = safe_float_conversion(row.find('td', {'data-stat': 'p_earned_run_avg'}).text if row.find('td', {'data-stat': 'p_earned_run_avg'}) else "0")
                g = safe_int_conversion(row.find('td', {'data-stat': 'p_g'}).text if row.find('td', {'data-stat': 'p_g'}) else "0")
                gs = safe_int_conversion(row.find('td', {'data-stat': 'p_gs'}).text if row.find('td', {'data-stat': 'p_gs'}) else "0")
                gf = safe_int_conversion(row.find('td', {'data-stat': 'p_gf'}).text if row.find('td', {'data-stat': 'p_gf'}) else "0")
                cg = safe_int_conversion(row.find('td', {'data-stat': 'p_cg'}).text if row.find('td', {'data-stat': 'p_cg'}) else "0")
                sho = safe_int_conversion(row.find('td', {'data-stat': 'p_sho'}).text if row.find('td', {'data-stat': 'p_sho'}) else "0")
                sv = safe_int_conversion(row.find('td', {'data-stat': 'p_sv'}).text if row.find('td', {'data-stat': 'p_sv'}) else "0")
                ip = safe_float_conversion(row.find('td', {'data-stat': 'p_ip'}).text if row.find('td', {'data-stat': 'p_ip'}) else "0")
                h = safe_int_conversion(row.find('td', {'data-stat': 'p_h'}).text if row.find('td', {'data-stat': 'p_h'}) else "0")
                r = safe_int_conversion(row.find('td', {'data-stat': 'p_r'}).text if row.find('td', {'data-stat': 'p_r'}) else "0")
                er = safe_int_conversion(row.find('td', {'data-stat': 'p_er'}).text if row.find('td', {'data-stat': 'p_er'}) else "0")
                hr = safe_int_conversion(row.find('td', {'data-stat': 'p_hr'}).text if row.find('td', {'data-stat': 'p_hr'}) else "0")
                bb = safe_int_conversion(row.find('td', {'data-stat': 'p_bb'}).text if row.find('td', {'data-stat': 'p_bb'}) else "0")
                ibb = safe_int_conversion(row.find('td', {'data-stat': 'p_ibb'}).text if row.find('td', {'data-stat': 'p_ibb'}) else "0")
                so = safe_int_conversion(row.find('td', {'data-stat': 'p_so'}).text if row.find('td', {'data-stat': 'p_so'}) else "0")
                hbp = safe_int_conversion(row.find('td', {'data-stat': 'p_hbp'}).text if row.find('td', {'data-stat': 'p_hbp'}) else "0")
                bk = safe_int_conversion(row.find('td', {'data-stat': 'p_bk'}).text if row.find('td', {'data-stat': 'p_bk'}) else "0")
                wp = safe_int_conversion(row.find('td', {'data-stat': 'p_wp'}).text if row.find('td', {'data-stat': 'p_wp'}) else "0")
                bf = safe_int_conversion(row.find('td', {'data-stat': 'p_bfp'}).text if row.find('td', {'data-stat': 'p_bfp'}) else "0")
                era_plus = safe_int_conversion(row.find('td', {'data-stat': 'p_earned_run_avg_plus'}).text if row.find('td', {'data-stat': 'p_earned_run_avg_plus'}) else "0")
                fip = safe_float_conversion(row.find('td', {'data-stat': 'p_fip'}).text if row.find('td', {'data-stat': 'p_fip'}) else "0")
                whip = safe_float_conversion(row.find('td', {'data-stat': 'p_whip'}).text if row.find('td', {'data-stat': 'p_whip'}) else "0")
                h9 = safe_float_conversion(row.find('td', {'data-stat': 'p_hits_per_nine'}).text if row.find('td', {'data-stat': 'p_hits_per_nine'}) else "0")
                hr9 = safe_float_conversion(row.find('td', {'data-stat': 'p_hr_per_nine'}).text if row.find('td', {'data-stat': 'p_hr_per_nine'}) else "0")
                bb9 = safe_float_conversion(row.find('td', {'data-stat': 'p_bb_per_nine'}).text if row.find('td', {'data-stat': 'p_bb_per_nine'}) else "0")
                so9 = safe_float_conversion(row.find('td', {'data-stat': 'p_so_per_nine'}).text if row.find('td', {'data-stat': 'p_so_per_nine'}) else "0")
                sow = safe_float_conversion(row.find('td', {'data-stat': 'p_strikeouts_per_base_on_balls'}).text if row.find('td', {'data-stat': 'p_strikeouts_per_base_on_balls'}) else "0")
                
                # Create pitcher data payload
                pitcher_data = {
                    "bbrefID": bbref_id,
                    "Year": 2025,
                    "Age": age,
                    "Team": team_abbr,
                    "Lg": get_league_by_team(team_abbr),
                    "WL": win_loss_record,
                    "WLPercentage": wlp,
                    "ERA": era,
                    "G": g,
                    "GS": gs,
                    "GF": gf,
                    "CG": cg,
                    "SHO": sho,
                    "SV": sv,
                    "IP": ip,
                    "H": h,
                    "R": r,
                    "ER": er,
                    "HR": hr,
                    "BB": bb,
                    "IBB": ibb,
                    "SO": so,
                    "HBP": hbp,
                    "BK": bk,
                    "WP": wp,
                    "BF": bf,
                    "ERAPlus": era_plus,
                    "FIP": fip,
                    "WHIP": whip,
                    "H9": h9,
                    "HR9": hr9,
                    "BB9": bb9,
                    "SO9": so9,
                    "SOW": sow,
                    "Throws": throws,
                    "DateModified": current_datetime
                }
                
                # Send to database
                send_pitcher_data_to_db(pitcher_data, bbref_id)
                processed_count += 1
                
                # Add a small delay to avoid overwhelming the API
                if processed_count % 10 == 0:
                    time.sleep(0.5)
                    logger.info(f"Processed {processed_count} pitchers so far")
                    
            except Exception as e:
                logger.error(f"Error processing pitching row: {e}")
                
        logger.info(f"Successfully processed {processed_count} pitchers")
        
    except Exception as e:
        logger.error(f"Error scraping pitching data: {e}")

def main():
    start_time = time.time()
    logger.info("Starting Baseball Reference data scraping with enhanced methods")
    
    try:
        # Try to solve Cloudflare once with Selenium before scraping
        try:
            # Warm up the connection to Baseball Reference
            logger.info("Warming up connection to Baseball Reference...")
            warm_up_url = "https://www.baseball-reference.com/"
            scrape_with_selenium(warm_up_url)
            
            # Add a delay to simulate human browsing
            wait_with_jitter(5)
        except Exception as e:
            logger.warning(f"Warm-up connection failed: {e}")
        
        # Scrape batting data
        scrape_batting_data()
        
        # Wait between requests
        wait_with_jitter(10)  # Longer wait between major sections
        
        # Scrape pitching data
        scrape_pitching_data()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Scraping completed in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        
if __name__ == "__main__":
    main()