import requests
from bs4 import BeautifulSoup
import statistics
from datetime import date
import json
import urllib3
import time
import random
import cloudscraper
import argparse
import os

# API base URL
API_BASE_URL = "https://localhost:44346/api"

# Suppress HTTPS warnings
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

# Functions for safer data handling to avoid crashes
def safe_float(value, default=0.0):
    """Safely convert a value to float with better error handling"""
    if value is None:
        return default
    
    if isinstance(value, str):
        # Remove percentage signs and other non-numeric characters
        value = value.replace('%', '').replace(',', '')
        # Handle empty strings
        if not value.strip():
            return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert a value to int with better error handling"""
    try:
        # First try to convert to float, then to int
        float_val = safe_float(value, default)
        return int(float_val)
    except (ValueError, TypeError):
        return default

def safe_get_value(data_list, index, default_value='0'):
    """Safely get a value from a list with better error handling"""
    try:
        if not data_list or index >= len(data_list):
            return default_value
        value = data_list[index]
        return value if value and str(value).strip() else default_value
    except (IndexError, AttributeError, TypeError):
        return default_value

def safe_get_field(cell_data, field_names, default='0'):
    """Get a field value from multiple possible field names"""
    if not cell_data or not field_names:
        return default
        
    for field in field_names:
        if field in cell_data and cell_data[field]:
            return cell_data[field]
    
    return default

def extract_html_content(scraper, bbrefid, year, debug=False):
    """Save HTML content to a file for debugging"""
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={bbrefid}&t=b&year={year}"
    try:
        response = scraper.get(url)
        if response.status_code == 200:
            # Create debug directory if it doesn't exist
            debug_dir = "debug_html"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            filename = f"{debug_dir}/{bbrefid}_{year}_debug.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Saved HTML content to {filename}")
            return True
        else:
            print(f"Failed to retrieve page: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error saving HTML: {e}")
        return False

def try_multiple_row_extraction_methods(table, debug=False):
    """Try multiple methods to extract rows from a table"""
    rows = []
    
    # Method 1: Standard method
    try:
        rows = table.find_all('tr', class_=lambda x: x != 'thead')
        if rows and len(rows) > 1:
            if debug:
                print(f"Method 1 found {len(rows)} rows")
            return rows
    except Exception as e:
        if debug:
            print(f"Method 1 error: {e}")
    
    # Method 2: Find all tr elements and filter out headers
    try:
        all_rows = table.find_all('tr')
        rows = [row for row in all_rows if not row.find('th', scope='col')]
        if rows and len(rows) > 1:
            if debug:
                print(f"Method 2 found {len(rows)} rows")
            return rows
    except Exception as e:
        if debug:
            print(f"Method 2 error: {e}")
    
    # Method 3: Get rows from tbody
    try:
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            if rows and len(rows) > 1:
                if debug:
                    print(f"Method 3 found {len(rows)} rows")
                return rows
    except Exception as e:
        if debug:
            print(f"Method 3 error: {e}")
    
    # Method 4: Direct CSS selector
    try:
        rows = table.select('tr:not(.thead)')
        if rows and len(rows) > 1:
            if debug:
                print(f"Method 4 found {len(rows)} rows")
            return rows
    except Exception as e:
        if debug:
            print(f"Method 4 error: {e}")
    
    if debug:
        print("All row extraction methods failed")
    return []

def extract_cell_data(row, debug=False):
    """
    Extract data from all cells in a row with multiple fallback methods
    """
    cell_data = {}
    
    # Method 1: Use data-stat attribute
    try:
        cells = row.find_all('td')
        cell_data = {cell['data-stat']: cell.get_text(strip=True) for cell in cells if 'data-stat' in cell.attrs}
        if cell_data and len(cell_data) > 5:  # Reasonable number of columns
            return cell_data
    except Exception as e:
        if debug:
            print(f"Method 1 cell extraction error: {e}")
    
    # Method 2: Use column index if data-stat is not available
    try:
        cells = row.find_all('td')
        # Standard column mapping for Baseball Reference (adjust based on observed structure)
        standard_columns = [
            'game_num', 'date', 'team_ID', 'team_homeORaway', 'opp_ID', 
            'game_result', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 
            'SB', 'CS', 'BB', 'SO', 'BA', 'OBP', 'SLG', 'OPS'
        ]
        
        # Map column index to column name for as many cells as we have
        for i, cell in enumerate(cells):
            if i < len(standard_columns):
                cell_data[standard_columns[i]] = cell.get_text(strip=True)
        
        if cell_data and len(cell_data) > 5:
            return cell_data
    except Exception as e:
        if debug:
            print(f"Method 2 cell extraction error: {e}")
    
    # Method 3: Just get cell text in order
    try:
        cell_texts = [cell.get_text(strip=True) for cell in row.find_all('td')]
        if cell_texts and len(cell_texts) > 5:
            # Just return a dictionary with numeric keys
            return {str(i): text for i, text in enumerate(cell_texts)}
    except Exception as e:
        if debug:
            print(f"Method 3 cell extraction error: {e}")
    
    # Fall back to empty dict if all methods fail
    return {}

def convert_date(month_day):
    # Map month abbreviations to their numeric values
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }

    # Remove anything starting from '('
    month_day = month_day.split('(')[0].strip()

    # Split the input into month and day
    parts = month_day.split()
    if len(parts) != 2:
        return None  # Handle cases where the format is unexpected

    month_abbr, day = parts
    month = month_map.get(month_abbr)

    if not month:
        return None  # Handle invalid month abbreviations

    # Add leading zero to the day if necessary
    day = day.zfill(2)

    # Use the current year
    current_year = date.today().year

    # Combine into the desired format
    return f"{current_year}-{month}-{day}"


def process_and_post_trailing_gamelogs(scraper, api_session, bbrefid, year, debug=False):
    """
    Scrape data from Baseball Reference and post to API with improved error handling
    
    Args:
        scraper: The cloudscraper session for web scraping
        api_session: The API session for making API calls
        bbrefid: Baseball Reference player ID
        year: Year to scrape data for
        debug: Whether to print debug information
        
    Returns:
        bool: Whether processing was successful
    """

    # Normalize ParkFactors API endpoint
    normalize_api_url = f"{API_BASE_URL}/ParkFactors/normalize"
    trailing_gamelog_api_url = f"{API_BASE_URL}/TrailingGameLogSplits"
    try:
        # Scrape data using the scraper passed in from main
        if debug:
            print(f"Scraping data for {bbrefid} for year {year}")
        
        # Construct the URL
        url = f"https://www.baseball-reference.com/players/gl.fcgi?id={bbrefid}&t=b&year={year}"
        
        # Alternative URL if player hasn't played in the current year yet
        alt_url = f"https://www.baseball-reference.com/players/{bbrefid[0]}/{bbrefid}.shtml"
        
        if debug:
            print(f"Requesting URL: {url}")
        
        # Add random delay before accessing the player page (1-3 seconds)
        time.sleep(random.uniform(1, 3))
        
        # Fetch the page content using cloudscraper
        response = scraper.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve game log page for player {bbrefid} in year {year}. HTTP Status Code: {response.status_code}")
            print(f"Trying alternative player page: {alt_url}")
            
            # Try the alternative URL
            alt_response = scraper.get(alt_url)
            if alt_response.status_code != 200:
                print(f"Failed to retrieve alternative page for player {bbrefid}. HTTP Status Code: {alt_response.status_code}")
                return False
                
            response = alt_response
            print(f"Found player page. Now checking for most recent year's data.")
            
            # Parse the alt page to find the most recent year
            alt_soup = BeautifulSoup(response.content, 'html.parser')
            year_links = alt_soup.select('a[href*="year="]')
            
            if not year_links:
                print(f"No year links found for player {bbrefid}")
                return False
                
            # Extract years from the links
            years = []
            for link in year_links:
                href = link.get('href', '')
                if 'year=' in href:
                    try:
                        year_val = int(href.split('year=')[1].split('&')[0])
                        years.append(year_val)
                    except (ValueError, IndexError):
                        continue
            
            if not years:
                print(f"No valid years found for player {bbrefid}")
                return False
                
            # Find the most recent year
            most_recent_year = max(years)
            print(f"Most recent year found: {most_recent_year}")
            
            # Try fetching the most recent year's data
            recent_url = f"https://www.baseball-reference.com/players/gl.fcgi?id={bbrefid}&t=b&year={most_recent_year}"
            print(f"Trying most recent year URL: {recent_url}")
            
            time.sleep(random.uniform(1, 3))
            recent_response = scraper.get(recent_url)
            
            if recent_response.status_code != 200:
                print(f"Failed to retrieve most recent year page for player {bbrefid}. HTTP Status Code: {recent_response.status_code}")
                return False
                
            response = recent_response
            year = most_recent_year
            print(f"Using data from year {year} for player {bbrefid}")

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if the page is redirecting to the player's main page
        # This happens when there's no game log for the year requested
        if soup.title and "Player Page" in soup.title.string and "Game Logs" not in soup.title.string:
            print(f"No game logs available for {bbrefid} in year {year}. Redirected to player page.")
            return False
            
        # Find the game log table - try multiple approaches since Baseball Reference has different formats
        # First try the standard id
        table_div = soup.find('div', id='div_batting_gamelogs')

        # If not found, try looking for the table structure in the alternative format
        if not table_div:
            table_div = soup.find('div', class_='table_container tabbed current is_setup', id=lambda x: x and x.startswith('div_players_'))

        # If still not found, try a more general approach
        if not table_div:
            # Look for any table container that has batting statistics
            table_div = soup.find('div', class_='table_container', id=lambda x: x and ('batting' in x or 'players' in x))

        # If still not found, try finding the table directly
        table = None
        if not table_div:
            table = soup.find('table', class_=lambda x: x and ('stats_table' in x or 'sortable' in x))
            if table:
                # If we found a table directly, we can use it
                if debug:
                    print(f"Found table directly without container for {bbrefid}")
            else:
                print(f"Game log table not found for player {bbrefid} in year {year}")
                if debug:
                    # Print all div ids to help debug
                    all_divs = soup.find_all('div', id=True)
                    div_ids = [div.get('id') for div in all_divs]
                    print(f"Available divs: {div_ids[:10]}...")
                return False

        # Extract the actual table from the div - if we found a div
        if table_div and not table:
            table = table_div.find('table', class_=lambda x: x and ('stats_table' in x or 'sortable' in x))
            
            # If no table found with those classes, try more general approach
            if not table:
                table = table_div.find('table')
                
        if not table:
            print(f"Table element not found within any container for player {bbrefid} in year {year}")
            if debug:
                # Print soup structure to aid debugging
                print(f"Page structure overview: {soup.title.string if soup.title else 'No title'}")
            return False

        if debug:
            print(f"Found table with id: {table.get('id', 'No ID')} and classes: {table.get('class', 'No classes')}")

        # Process the table rows
        try:
            rows = try_multiple_row_extraction_methods(table, debug)
            if not rows or len(rows) < 2:
                print(f"Not enough rows to process for player {bbrefid}")
                if debug:
                    # Save HTML for debugging
                    extract_html_content(scraper, bbrefid, year, debug)
                    # Try to print table structure
                    print(f"Table structure: {table.prettify()[:500]}...")
                return False

            if debug:
                print(f"Found {len(rows)} rows in the table")
        except Exception as e:
            print(f"Error extracting rows: {e}")
            if debug:
                extract_html_content(scraper, bbrefid, year, debug)
            return False

        # Get the last 8 rows, with the 8th being the season totals
        last_8_rows = rows[-8:] if len(rows) >= 8 else rows
        season_totals = last_8_rows[-1] if last_8_rows else None  # The season totals row
        last_7_rows = last_8_rows[:-1] if last_8_rows else []

        # Initialize all aggregate variables
        aggregate = {
            'PA': 0, 'AB': 0, 'R': 0, 'H': 0, '2B': 0, '3B': 0, 'HR': 0, 'RBI': 0,
            'BB': 0, 'IBB': 0, 'SO': 0, 'HBP': 0, 'SH': 0, 'SF': 0, 'ROE': 0,
            'GDP': 0, 'SB': 0, 'CS': 0, 'WPA': 0, 'cWPA': 0, 'RE24': 0,
            'DFS_DK': 0, 'DFS_FD': 0
        }
        BOP_list = []
        aLI_list = []
        acLI_list = []

        # Variables to track all rows
        away_opp_ids = []
        home_counter = 0

        # Variables to track last 7 rows
        away_opp_ids_last7 = []
        home_counter_last7 = 0
        # Initialize homeTeam with a default value
        homeTeam = "TODO"

        # Process each row in the table
        for row in rows:
            cell_data = extract_cell_data(row, debug)
            
            if not cell_data:
                if debug:
                    print(f"Could not extract cell data from row: {row}")
                continue

            # For debugging, print the first few rows of data
            if debug and len(away_opp_ids) + home_counter < 3:
                print(f"Row {len(away_opp_ids) + home_counter} data sample: {list(cell_data.items())[:5]}...")
                
            # Extract team_homeORaway with fallbacks
            team_homeORaway = (
                cell_data.get('team_homeORaway', '') or 
                cell_data.get('game_location', '') or
                cell_data.get('4', '')  # Using indexed fallback
            )
            
            # Extract opp_ID with fallbacks
            opp_ID = (
                cell_data.get('opp_ID', '') or 
                cell_data.get('opp_name_abbr', '') or
                cell_data.get('5', '')  # Using indexed fallback
            )

            # Check home or away and update the appropriate list/counter
            if team_homeORaway == '@':
                away_opp_ids.append(opp_ID)  # Add opponent ID to the list
            else:
                home_counter += 1  # Increment the counter for home games

        # Process the last 7 rows for aggregation
        game_count = 0  # Initialize the game count
        for row in last_7_rows:
            cell_data = extract_cell_data(row, debug)
            
            if not cell_data:
                if debug:
                    print(f"Could not extract cell data from row in last 7: {row}")
                continue

            game_count += 1  # Increment the game count for each game processed
            
            # Extract team_ID with a fallback to "TODO"
            homeTeam = (
                cell_data.get('team_ID', '') or 
                cell_data.get('team_name_abbr', '') or 
                cell_data.get('3', '') or 
                "TODO"
            )
            if not homeTeam or homeTeam == '':
                homeTeam = 'TODO'

            # Map the field names for both old and new formats
            stat_mapping = {
                'PA': ['PA', 'b_pa', '8'],
                'AB': ['AB', 'b_ab', '9'],
                'R': ['R', 'b_r', '10'],
                'H': ['H', 'b_h', '11'],
                '2B': ['2B', 'b_doubles', '12'],
                '3B': ['3B', 'b_triples', '13'],
                'HR': ['HR', 'b_hr', '14'],
                'RBI': ['RBI', 'b_rbi', '15'],
                'BB': ['BB', 'b_bb', '16'],
                'IBB': ['IBB', 'b_ibb', '17'],
                'SO': ['SO', 'b_so', '18'],
                'HBP': ['HBP', 'b_hbp', '19'],
                'SH': ['SH', 'b_sh', '20'],
                'SF': ['SF', 'b_sf', '21'],
                'ROE': ['ROE', 'b_roe', '22'],
                'GDP': ['GDP', 'b_gidp', '23'],
                'SB': ['SB', 'b_sb', '24'],
                'CS': ['CS', 'b_cs', '25']
            }

        # Add random delay between API calls
        time.sleep(random.uniform(0.5, 1.5))
        
        # Post data to TrailingGameLogSplits API
        try:
            responseL7 = api_session.post(trailing_gamelog_api_url, json=json_payloadL7, verify=False)
            responseL7.raise_for_status()
            print(f"Successfully posted Last7G data for {bbrefid}: {responseL7.status_code}")
            if debug:
                print(f"Last7G response: {responseL7.text[:100]}...")
        except requests.exceptions.RequestException as e:
            print(f"Error posting Last7G data for {bbrefid}: {e}")
            if debug:
                print(f"Last7G payload: {json.dumps(json_payloadL7, indent=2)}")
            return False

        time.sleep(random.uniform(0.5, 1.5))
        
        try:
            responseTOT = api_session.post(trailing_gamelog_api_url, json=json_payloadTOT, verify=False)
            responseTOT.raise_for_status()
            print(f"Successfully posted Season data for {bbrefid}: {responseTOT.status_code}")
            if debug:
                print(f"Season response: {responseTOT.text[:100]}...")
        except requests.exceptions.RequestException as e:
            print(f"Error posting Season data for {bbrefid}: {e}")
            if debug:
                print(f"Season payload: {json.dumps(json_payloadTOT, indent=2)}")
            return False

        time.sleep(random.uniform(0.5, 1.5))
        
        # Only post single game data if we have it
        if json_payloadSG:
            try:
                responseSG = api_session.post(trailing_gamelog_api_url, json=json_payloadSG, verify=False)
                responseSG.raise_for_status()
                print(f"Successfully posted SingleGame data for {bbrefid}: {responseSG.status_code}")
                if debug:
                    print(f"SingleGame response: {responseSG.text[:100]}...")
            except requests.exceptions.RequestException as e:
                print(f"Error posting SingleGame data for {bbrefid}: {e}")
                if debug:
                    print(f"SingleGame Payload: {json.dumps(json_payloadSG, indent=2)}")
                # Don't return False here, as we can still continue with other data
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Post second single game data if we have it (for double headers)
        if json_payloadSG2:
            try:
                responseSG2 = api_session.post(trailing_gamelog_api_url, json=json_payloadSG2, verify=False)
                responseSG2.raise_for_status()
                print(f"Successfully posted SingleGame2 data for {bbrefid}: {responseSG2.status_code}")
                if debug:
                    print(f"SingleGame2 response: {responseSG2.text[:100]}...")
            except requests.exceptions.RequestException as e:
                print(f"Error posting SingleGame2 data for {bbrefid}: {e}")
                if debug:
                    print(f"SingleGame2 Payload: {json.dumps(json_payloadSG2, indent=2)}")
                # Don't return False here, as we can still continue with other data

        # Provide a summary of what was posted
        print(f"Data processing complete for {bbrefid}:")
        print(f"  - Last7G: {aggregated_data['G']} games")
        print(f"  - Season: {season_games} games")
        print(f"  - Single Game data: {'Yes' if json_payloadSG else 'No'}")
        print(f"  - Double Header data: {'Yes' if json_payloadSG2 else 'No'}")
        print("-------------------------------------------------------------------------------")
        
        return True
        
    except Exception as e:
        print(f"Error processing {bbrefid}: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return False

        json_payloadSG2 = None
        if single_game_data2 and len(single_game_data2) >= 38:
            json_payloadSG2 = {
                "bbrefId": bbrefid,
                "team": homeTeam,
                "split": "SingleGame2",
                "splitParkFactor": api_response3["totalParkFactor"],
                "g": 1,
                "pa": safe_get_sg_value(single_game_data2, 8),
                "ab": safe_get_sg_value(single_game_data2, 9),
                "r": safe_get_sg_value(single_game_data2, 10),
                "h": safe_get_sg_value(single_game_data2, 11),
                "doubles": safe_get_sg_value(single_game_data2, 12),
                "triples": safe_get_sg_value(single_game_data2, 13),
                "hr": safe_get_sg_value(single_game_data2, 14),
                "rbi": safe_get_sg_value(single_game_data2, 15),
                "bb": safe_get_sg_value(single_game_data2, 16),
                "ibb": safe_get_sg_value(single_game_data2, 17, '0'),
                "so": safe_get_sg_value(single_game_data2, 18),
                "hbp": safe_get_sg_value(single_game_data2, 19),
                "sh": safe_get_sg_value(single_game_data2, 20),
                "sf": safe_get_sg_value(single_game_data2, 21, '0'),
                "roe": safe_get_sg_value(single_game_data2, 22),
                "gdp": safe_get_sg_value(single_game_data2, 23, '0'),
                "sb": safe_get_sg_value(single_game_data2, 24),
                "cs": safe_get_sg_value(single_game_data2, 25),
                "ba": safe_get_sg_value(single_game_data2, 26),
                "obp": safe_get_sg_value(single_game_data2, 27),
                "slg": safe_get_sg_value(single_game_data2, 28),
                "ops": safe_get_sg_value(single_game_data2, 29),
                "bop": -1 if not safe_get_sg_value(single_game_data2, 30) else safe_get_sg_value(single_game_data2, 30),
                "ali": safe_get_sg_value(single_game_data2, 31, '0.0'),
                "wpa": safe_get_sg_value(single_game_data2, 32, '0.0'),
                "acLI": safe_get_sg_value(single_game_data2, 33, '0.0'),
                "cwpa": str(safe_get_sg_value(single_game_data2, 34, '0%')),
                "rE24": safe_get_sg_value(single_game_data2, 35, '0.0'),
                "dfsDk": safe_get_sg_value(single_game_data2, 36),
                "dfsFd": safe_get_sg_value(single_game_data2, 37),
                "homeGames": 1 if len(single_game_data2) > 4 and single_game_data2[4] == '' else 0,
                "awayGames": 1 if len(single_game_data2) > 4 and single_game_data2[4] == '@' else 0,
                "homeParkFactor": api_response3["homeParkFactor"],
                "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
                "dateUpdated": converted_date
            }

            for key, stat_keys in stat_mapping.items():
                value = safe_int(safe_get_field(cell_data, stat_keys, '0'))
                aggregate[key] += value

            # Update additional aggregate variables
            try:
                # Map the field names for both old and new formats
                field_mapping = {
                    'cWPA': ['cwpa_bat', 'b_cwpa', '34'],
                    'aLI': ['leverage_index_avg', 'b_leverage_index_avg', '31'],
                    'acLI': ['cli_avg', 'b_cli_avg', '33'],
                    'WPA': ['wpa_bat', 'b_wpa', '32'],
                    'RE24': ['re24_bat', 'b_baseout_runs', '35'],
                    'DFS_DK': ['draftkings_points', 'b_draftkings_points', '36'],
                    'DFS_FD': ['fanduel_points', 'b_fanduel_points', '37'],
                    'BOP': ['batting_order_position', 'b_lineup_position', '38']
                }
                
                # Get values using the field mapping
                cWPA_text = safe_get_field(cell_data, field_mapping['cWPA'], '0')
                cWPA_text = cWPA_text.replace('%', '') if cWPA_text else '0'
                cWPA = safe_float(cWPA_text) / 100  # Convert from percentage to decimal
                
                aLI_text = safe_get_field(cell_data, field_mapping['aLI'], '0')
                aLI_text = aLI_text.replace('%', '') if aLI_text else '0'
                aLI = safe_float(aLI_text)
                
                acLI_text = safe_get_field(cell_data, field_mapping['acLI'], '0')
                acLI_text = acLI_text.replace('%', '') if acLI_text else '0'
                acLI = safe_float(acLI_text)
                
                WPA = safe_float(safe_get_field(cell_data, field_mapping['WPA'], '0'))
                RE24 = safe_float(safe_get_field(cell_data, field_mapping['RE24'], '0'))
                DFS_DK = safe_float(safe_get_field(cell_data, field_mapping['DFS_DK'], '0'))
                DFS_FD = safe_float(safe_get_field(cell_data, field_mapping['DFS_FD'], '0'))

                # Update aggregate totals
                aggregate['WPA'] += WPA
                aggregate['cWPA'] += cWPA
                aggregate['RE24'] += RE24
                aggregate['DFS_DK'] += DFS_DK
                aggregate['DFS_FD'] += DFS_FD

                # Collect lists for mode and averaging calculations
                aLI_list.append(aLI)
                acLI_list.append(acLI)
                
                BOP_value = safe_int(safe_get_field(cell_data, field_mapping['BOP'], '0'))
                BOP_list.append(BOP_value)

                # Check home or away for last 7 rows - handle both formats
                team_homeORaway = (
                    cell_data.get('team_homeORaway', '') or 
                    cell_data.get('game_location', '') or
                    cell_data.get('4', '')
                )
                
                if team_homeORaway == '@':
                    opp_id = (
                        cell_data.get('opp_ID', '') or 
                        cell_data.get('opp_name_abbr', '') or
                        cell_data.get('5', '')
                    )
                    away_opp_ids_last7.append(opp_id)
                else:
                    home_counter_last7 += 1

            except ValueError as e:
                print(f"Error parsing value in row: {e}")
                if debug:
                    print(f"Cell data: {cell_data}")

        # Calculate aggregated stats (BA, OBP, SLG, OPS)
        BA = safe_float(aggregate['H']) / safe_float(aggregate['AB']) if safe_float(aggregate['AB']) > 0 else 0.0
        OBP = (safe_float(aggregate['H'] + aggregate['BB'] + aggregate['HBP'])) / safe_float(aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) if safe_float(aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) > 0 else 0.0
        SLG = safe_float(aggregate['H'] + (2 * aggregate['2B']) + (3 * aggregate['3B']) + (4 * aggregate['HR'])) / safe_float(aggregate['AB']) if safe_float(aggregate['AB']) > 0 else 0.0
        OPS = OBP + SLG

        # Get the most common BOP
        try:
            BOP = statistics.mode(BOP_list) if BOP_list else 0
        except statistics.StatisticsError:
            BOP = 0  # Handle cases where no mode is found

        # Calculate averages for aLI, acLI
        aLI = sum(aLI_list) / len(aLI_list) if aLI_list else 0.0
        acLI = sum(acLI_list) / len(acLI_list) if acLI_list else 0.0

        # Get today's date in yyyy-mm-dd format
        today = date.today().isoformat()

        # Create aggregated data
        aggregated_data = {
            'G': game_count,
            'PA': aggregate['PA'],
            'AB': aggregate['AB'],
            'R': aggregate['R'],
            'H': aggregate['H'],
            '2B': aggregate['2B'],
            '3B': aggregate['3B'],
            'HR': aggregate['HR'],
            'RBI': aggregate['RBI'],
            'BB': aggregate['BB'],
            'IBB': aggregate['IBB'],
            'SO': aggregate['SO'],
            'HBP': aggregate['HBP'],
            'SH': aggregate['SH'],
            'SF': aggregate['SF'],
            'ROE': aggregate['ROE'],
            'GDP': aggregate['GDP'],
            'SB': aggregate['SB'],
            'CS': aggregate['CS'],
            'BA': round(BA, 3),
            'OBP': round(OBP, 3),
            'SLG': round(SLG, 3),
            'OPS': round(OPS, 3),
            'BOP': BOP,
            'aLI': round(aLI, 8),
            'WPA': round(aggregate['WPA'], 3),
            'acLI': round(acLI, 8),
            'cWPA': f"{round(aggregate['cWPA'] * 100, 2)}%",  # Display cWPA as percentage
            'RE24': round(aggregate['RE24'], 2),
            'DFS_DK': round(aggregate['DFS_DK'], 1),
            'DFS_FD': round(aggregate['DFS_FD'], 1),
            'date': today
        }

        # Extract the season totals
        season_totals_data = []
        if season_totals:
            season_totals_data = [cell.get_text(strip=True) for cell in season_totals.find_all('td')]

        # Extract the second-to-last row for SingleGame payload
        single_game_data = []
        single_game_data2 = None
        
        if len(rows) >= 2:
            single_game_row = rows[-2]  # Second-to-last row
            single_game_data = [cell.get_text(strip=True) for cell in single_game_row.find_all('td')]
            
            # Check if there's a double header
            if single_game_data and len(single_game_data) >= 3 and '(' in str(single_game_data[2]):
                if len(rows) >= 3:
                    single_game_row2 = rows[-3]  # third-to-last row as there was a double header
                    single_game_data2 = [cell.get_text(strip=True) for cell in single_game_row2.find_all('td')]
        
        # Make sure we have enough data in season_totals_data
        subset_season_totals = []
        if len(season_totals_data) >= 9:
            # Extract data from index 8 to len(season_totals_data) - 2
            subset_season_totals = season_totals_data[8:-1]
        else:
            print(f"Not enough data in season totals for player {bbrefid}")
            subset_season_totals = ['0'] * 30  # Default values
        
        # Prepare payloads for normalization API
        payload = {
            "bbrefId": bbrefid,
            "oppIds": away_opp_ids,
            "homeGames": home_counter - 1 if home_counter > 0 else 0
        }
        
        payload2 = {
            "bbrefId": bbrefid,
            "oppIds": away_opp_ids_last7,
            "homeGames": home_counter_last7
        }
        
        # Make sure single_game_data has enough elements before using it
        if single_game_data and len(single_game_data) > 5:
            payload3 = {
                "bbrefId": bbrefid,
                "oppIds": [single_game_data[5]],
                "homeGames": 1 if single_game_data[4] == '' else 0
            }
        else:
            if debug:
                print(f"Single game data incomplete for {bbrefid}")
            payload3 = {
                "bbrefId": bbrefid,
                "oppIds": ["UNK"],
                "homeGames": 0
            }


        # Add random delay between API calls to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
        
        if debug:
            print(f"Calling normalize API for full season with payload: {payload}")
            
        try:
            response = api_session.post(normalize_api_url, json=payload, verify=False)
            response.raise_for_status()
            api_response = response.json()
            
            if debug:
                print(f"Normalize API response for full season: {api_response}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling normalize API for full season: {e}")
            if debug:
                print(f"Payload: {payload}")
            return False

        time.sleep(random.uniform(0.5, 1.5))
        
        if debug:
            print(f"Calling normalize API for last 7 games with payload: {payload2}")
            
        try:
            response2 = api_session.post(normalize_api_url, json=payload2, verify=False)
            response2.raise_for_status()
            api_response2 = response2.json()
            
            if debug:
                print(f"Normalize API response for last 7 games: {api_response2}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling normalize API for last 7 games: {e}")
            if debug:
                print(f"Payload: {payload2}")
            return False

        time.sleep(random.uniform(0.5, 1.5))
        
        if debug:
            print(f"Calling normalize API for last 1 game with payload: {payload3}")
            
        try:
            response3 = api_session.post(normalize_api_url, json=payload3, verify=False)
            response3.raise_for_status()
            api_response3 = response3.json()
            
            if debug:
                print(f"Normalize API response for last 1 game: {api_response3}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling normalize API for last 1 game: {e}")
            if debug:
                print(f"Payload: {payload3}")
            return False

        # Prepare JSON payloads for TrailingGameLogSplits API
        json_payloadL7 = {
            "bbrefId": bbrefid,
            "team": homeTeam,
            "split": "Last7G",
            "splitParkFactor": api_response2["totalParkFactor"],
            "g": aggregated_data["G"],
            "pa": aggregated_data["PA"],
            "ab": aggregated_data["AB"],
            "r": aggregated_data["R"],
            "h": aggregated_data["H"],
            "doubles": aggregated_data["2B"],
            "triples": aggregated_data["3B"],
            "hr": aggregated_data["HR"],
            "rbi": aggregated_data["RBI"],
            "bb": aggregated_data["BB"],
            "ibb": aggregated_data["IBB"],
            "so": aggregated_data["SO"],
            "hbp": aggregated_data["HBP"],
            "sh": aggregated_data["SH"],
            "sf": aggregated_data["SF"],
            "roe": aggregated_data["ROE"],
            "gdp": aggregated_data["GDP"],
            "sb": aggregated_data["SB"],
            "cs": aggregated_data["CS"],
            "ba": aggregated_data["BA"],
            "obp": aggregated_data["OBP"],
            "slg": aggregated_data["SLG"],
            "ops": aggregated_data["OPS"],
            "bop": aggregated_data["BOP"],
            "ali": aggregated_data["aLI"],
            "wpa": aggregated_data["WPA"],
            "acLI": aggregated_data["acLI"],
            "cwpa": aggregated_data["cWPA"],
            "rE24": aggregated_data["RE24"],
            "dfsDk": aggregated_data["DFS_DK"],
            "dfsFd": aggregated_data["DFS_FD"],
            "homeGames": home_counter_last7,
            "awayGames": len(away_opp_ids_last7),
            "homeParkFactor": api_response2["homeParkFactor"],
            "awayParkFactorAvg": api_response2["avgAwayParkFactor"],
            "dateUpdated": date.today().isoformat()
        }

        # Safely process season totals data
        def safe_get_value(data_list, index, default_value='0'):
            try:
                value = data_list[index] if data_list and index < len(data_list) else default_value
                return value if value and str(value).strip() else default_value
            except (IndexError, AttributeError, TypeError):
                return default_value
        
        # Ensure converted date exists before processing single game data
        converted_date = None
        if single_game_data and len(single_game_data) > 2:
            converted_date = convert_date(single_game_data[2])
        if not converted_date:
            converted_date = date.today().isoformat()
        
        # Calculate season games
        season_games = len(away_opp_ids) + home_counter - 1 if home_counter > 0 else len(away_opp_ids)
        
        json_payloadTOT = {
            "bbrefId": bbrefid,
            "team": homeTeam,
            "split": "Season",
            "splitParkFactor": api_response["totalParkFactor"],
            "g": season_games,
            "pa": safe_get_value(subset_season_totals, 0),
            "ab": safe_get_value(subset_season_totals, 1),
            "r": safe_get_value(subset_season_totals, 2),
            "h": safe_get_value(subset_season_totals, 3),
            "doubles": safe_get_value(subset_season_totals, 4),
            "triples": safe_get_value(subset_season_totals, 5),
            "hr": safe_get_value(subset_season_totals, 6),
            "rbi": safe_get_value(subset_season_totals, 7),
            "bb": safe_get_value(subset_season_totals, 8),
            "ibb": safe_get_value(subset_season_totals, 9),
            "so": safe_get_value(subset_season_totals, 10),
            "hbp": safe_get_value(subset_season_totals, 11),
            "sh": safe_get_value(subset_season_totals, 12),
            "sf": safe_get_value(subset_season_totals, 13),
            "roe": safe_get_value(subset_season_totals, 14),
            "gdp": safe_get_value(subset_season_totals, 15),
            "sb": safe_get_value(subset_season_totals, 16),
            "cs": safe_get_value(subset_season_totals, 17),
            "ba": safe_get_value(subset_season_totals, 18),
            "obp": safe_get_value(subset_season_totals, 19),
            "slg": safe_get_value(subset_season_totals, 20),
            "ops": safe_get_value(subset_season_totals, 21),
            "bop": -1 if not safe_get_value(subset_season_totals, 22) or safe_get_value(subset_season_totals, 22) == "" else safe_get_value(subset_season_totals, 22),
            "ali": safe_get_value(subset_season_totals, 23),
            "wpa": safe_get_value(subset_season_totals, 24),
            "acLI": safe_get_value(subset_season_totals, 25),
            "cwpa": safe_get_value(subset_season_totals, 26),
            "rE24": safe_get_value(subset_season_totals, 27),
            "dfsDk": safe_get_value(subset_season_totals, 28),
            "dfsFd": safe_get_value(subset_season_totals, 29),
            "homeGames": home_counter - 1 if home_counter > 0 else 0,
            "awayGames": len(away_opp_ids),
            "homeParkFactor": api_response["homeParkFactor"],
            "awayParkFactorAvg": api_response["avgAwayParkFactor"],
            "dateUpdated": date.today().isoformat()
        }
        
        # Create SingleGame payload with proper error handling
        def safe_get_sg_value(data_list, index, default_value='0'):
            if not data_list or index >= len(data_list):
                return default_value
            value = data_list[index]
            if not value or str(value).strip() == '':
                return default_value
            return value

        json_payloadSG = None
        if single_game_data and len(single_game_data) >= 38:  # Ensure we have enough data
            json_payloadSG = {
                "bbrefId": bbrefid,
                "team": homeTeam,
                "split": "SingleGame",
                "splitParkFactor": api_response3["totalParkFactor"],
                "g": 1,
                "pa": safe_get_sg_value(single_game_data, 8),
                "ab": safe_get_sg_value(single_game_data, 9),
                "r": safe_get_sg_value(single_game_data, 10),
                "h": safe_get_sg_value(single_game_data, 11),
                "doubles": safe_get_sg_value(single_game_data, 12),
                "triples": safe_get_sg_value(single_game_data, 13),
                "hr": safe_get_sg_value(single_game_data, 14),
                "rbi": safe_get_sg_value(single_game_data, 15),
                "bb": safe_get_sg_value(single_game_data, 16),
                "ibb": safe_get_sg_value(single_game_data, 17, '0'),
                "so": safe_get_sg_value(single_game_data, 18),
                "hbp": safe_get_sg_value(single_game_data, 19),
                "sh": safe_get_sg_value(single_game_data, 20),
                "sf": safe_get_sg_value(single_game_data, 21, '0'),
                "roe": safe_get_sg_value(single_game_data, 22),
                "gdp": safe_get_sg_value(single_game_data, 23, '0'),
                "sb": safe_get_sg_value(single_game_data, 24),
                "cs": safe_get_sg_value(single_game_data, 25),
                "ba": safe_get_sg_value(single_game_data, 26),
                "obp": safe_get_sg_value(single_game_data, 27),
                "slg": safe_get_sg_value(single_game_data, 28),
                "ops": safe_get_sg_value(single_game_data, 29),
                "bop": -1 if not safe_get_sg_value(single_game_data, 30) else safe_get_sg_value(single_game_data, 30),
                "ali": safe_get_sg_value(single_game_data, 31, '0.0'),
                "wpa": safe_get_sg_value(single_game_data, 32, '0.0'),
                "acLI": safe_get_sg_value(single_game_data, 33, '0.0'),
                "cwpa": str(safe_get_sg_value(single_game_data, 34, '0%')),
                "rE24": safe_get_sg_value(single_game_data, 35, '0.0'),
                "dfsDk": safe_get_sg_value(single_game_data, 36),
                "dfsFd": safe_get_sg_value(single_game_data, 37),
                "homeGames": 1 if len(single_game_data) > 4 and single_game_data[4] == '' else 0,
                "awayGames": 1 if len(single_game_data) > 4 and single_game_data[4] == '@' else 0,
                "homeParkFactor": api_response3["homeParkFactor"],
                "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
                "dateUpdated": converted_date
            }



def get_todays_hitters(api_session, date_str, debug=False):
    """Get today's hitters from the API endpoint with improved error handling"""
    url = f"{API_BASE_URL}/Hitters/todaysHitters/{date_str}"
    print(f"Fetching today's hitters from: {url}")
    
    try:
        response = api_session.get(url, verify=False)
        if response.status_code == 200:
            try:
                hitters = response.json()
                # Debug the response format
                print(f"Response type: {type(hitters)}")
                if isinstance(hitters, list):
                    print(f"Successfully retrieved {len(hitters)} hitters for {date_str}")
                    if hitters and debug:
                        print(f"Sample first item: {hitters[0]}")
                        print(f"Sample first item type: {type(hitters[0])}")
                return hitters
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                if debug:
                    print(f"Response text: {response.text[:500]}...")
                return None
        else:
            print(f"Failed to retrieve today's hitters. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try an alternative date format if the original fails
            if '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    alt_date = f"{parts[0]}/{parts[1]}/{parts[2]}"
                    print(f"Trying alternative date format: {alt_date}")
                    return get_todays_hitters(api_session, alt_date, debug)
            return None
    except Exception as e:
        print(f"Error getting today's hitters: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Scrape Baseball Reference and post data to API')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format', default=date.today().isoformat())
    parser.add_argument('--file', type=str, help='Path to file with bbrefids (optional)')
    parser.add_argument('--year', type=int, help='Year to scrape data for', default=date.today().year)
    parser.add_argument('--delay', type=float, help='Delay between requests in seconds', default=3.5)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with additional output')
    parser.add_argument('--retry', type=int, help='Number of retry attempts for failed requests', default=2)
    parser.add_argument('--max-players', type=int, help='Maximum number of players to process', default=None)
    parser.add_argument('--save-html', action='store_true', help='Save HTML content for debugging')
    parser.add_argument('--alternative-year', type=int, help='Alternative year to try if current year fails', default=None)
    args = parser.parse_args()

    # Fix date format if needed
    if args.date and len(args.date) == 8 and '-' not in args.date and '/' not in args.date:
        # Format like 20250329
        args.date = f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:8]}"
        if args.debug:
            print(f"Reformatted date to: {args.date}")
            
    # Special handling for issues with leading zeros in date
    if args.date and '-' in args.date:
        parts = args.date.split('-')
        if len(parts) == 3:
            try:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                args.date = f"{year}-{month:02d}-{day:02d}"
                if args.debug:
                    print(f"Normalized date format to: {args.date}")
            except ValueError:
                pass

    # Create API session
    api_session = create_api_session()
    
    if args.debug:
        print(f"Debug mode enabled")
    
    # Create scraper session and simulate human browsing
    print(f"Initializing scraper and simulating human browsing...")
    scraper = create_scraper_session()
    if not simulate_human_browsing(scraper):
        print("Failed to simulate human browsing. Exiting.")
        return

    try:
        if args.file:
            # Process from file if specified
            print(f"Reading bbrefids from file: {args.file}")
            try:
                with open(args.file, "r", encoding="utf-8") as infile:
                    bbrefids = [line.strip() for line in infile if line.strip()]  # Remove empty lines
                print(f"Found {len(bbrefids)} bbrefids in file")
            except UnicodeDecodeError:
                # Try alternative encodings
                print("UTF-8 encoding failed, trying other encodings...")
                encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        with open(args.file, "r", encoding=encoding) as infile:
                            bbrefids = [line.strip() for line in infile if line.strip()]
                        print(f"Successfully read file with {encoding} encoding")
                        print(f"Found {len(bbrefids)} bbrefids in file")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print(f"Failed to read file with any encoding")
                    return
        else:
            # Get today's hitters from API
            print(f"Getting today's hitters for {args.date}...")
            hitters = get_todays_hitters(api_session, args.date, args.debug)
            if not hitters:
                print("No hitters found for today. Exiting.")
                return

            # Extract bbrefids from hitters response
            bbrefids = []
            
            # Handle different response formats
            if isinstance(hitters, list):
                if len(hitters) > 0:
                    if args.debug:
                        print(f"First hitter in response: {hitters[0]}")
                    
                    # Check if the list contains strings (bbrefIds directly)
                    if isinstance(hitters[0], str):
                        bbrefids = hitters
                    # Check if the list contains dictionaries with a bbrefId key
                    elif isinstance(hitters[0], dict) and 'bbrefId' in hitters[0]:
                        bbrefids = [hitter['bbrefId'] for hitter in hitters if 'bbrefId' in hitter]
                    # Try alternative keys that might contain the bbrefId
                    elif isinstance(hitters[0], dict):
                        # Look for likely key names
                        possible_keys = ['id', 'bbref_id', 'baseballReferenceId', 'playerId']
                        for key in possible_keys:
                            if key in hitters[0]:
                                bbrefids = [hitter[key] for hitter in hitters if key in hitter]
                                if args.debug:
                                    print(f"Used alternate key '{key}' to extract bbrefIds")
                                break
            elif isinstance(hitters, dict):
                # Try various possible structures
                if 'bbrefIds' in hitters:
                    bbrefids = hitters['bbrefIds']
                elif 'hitters' in hitters and isinstance(hitters['hitters'], list):
                    if len(hitters['hitters']) > 0 and isinstance(hitters['hitters'][0], dict) and 'bbrefId' in hitters['hitters'][0]:
                        bbrefids = [hitter['bbrefId'] for hitter in hitters['hitters']]
                elif 'data' in hitters and isinstance(hitters['data'], list):
                    if len(hitters['data']) > 0:
                        if isinstance(hitters['data'][0], str):
                            bbrefids = hitters['data']
                        elif isinstance(hitters['data'][0], dict) and 'bbrefId' in hitters['data'][0]:
                            bbrefids = [item['bbrefId'] for item in hitters['data'] if 'bbrefId' in item]
            
            # If string response, try to parse as JSON
            elif isinstance(hitters, str):
                try:
                    json_data = json.loads(hitters)
                    if isinstance(json_data, list):
                        if len(json_data) > 0:
                            if isinstance(json_data[0], str):
                                bbrefids = json_data
                            elif isinstance(json_data[0], dict) and 'bbrefId' in json_data[0]:
                                bbrefids = [item['bbrefId'] for item in json_data if 'bbrefId' in item]
                except json.JSONDecodeError:
                    pass
                
            # Print detailed info in debug mode
            if args.debug:
                print(f"API response type: {type(hitters)}")
                print(f"Sample of API response: {str(hitters)[:500]}...")
                
            if not bbrefids:
                print("Could not extract bbrefIds from the API response.")
                print("Response structure not recognized. Please check the API or use a file instead.")
                return
                
            print(f"Found {len(bbrefids)} bbrefids from API")

        # Process each bbrefid
        successful = 0
        failed = 0
        skipped = 0
        
        for i, bbrefid in enumerate(bbrefids):
            print(f"Processing {i+1}/{len(bbrefids)}: {bbrefid}")
            
            # Skip invalid bbrefids
            if not bbrefid or len(bbrefid) < 4:
                print(f"Skipping invalid bbrefid: {bbrefid}")
                skipped += 1
                continue
                
            # Add variable delay to avoid detection
            delay = args.delay + random.uniform(0.5, 2.0)
            
            # Try multiple times if needed
            for attempt in range(args.retry + 1):
                if attempt > 0:
                    print(f"Retry attempt {attempt}/{args.retry} for {bbrefid}")
                    # Increase delay for retry attempts
                    delay = delay * 1.5
                    time.sleep(delay)
                
                # Try current year first
                if process_and_post_trailing_gamelogs(scraper, api_session, bbrefid, args.year, args.debug):
                    successful += 1
                    break
                # If current year fails and alternative year is specified, try that
                elif args.alternative_year and attempt == args.retry - 1:
                    print(f"Trying alternative year {args.alternative_year} for {bbrefid}")
                    if process_and_post_trailing_gamelogs(scraper, api_session, bbrefid, args.alternative_year, args.debug):
                        successful += 1
                        break
                elif attempt == args.retry:  # Last attempt failed
                    failed += 1
                    if args.save_html:
                        # Save HTML for debugging
                        extract_html_content(scraper, bbrefid, args.year, args.debug)
            
            # Delay between requests
            if i < len(bbrefids) - 1:  # No need to delay after the last request
                print(f"Waiting {delay:.2f} seconds before next request...")
                time.sleep(delay)
                
                # Every 10 requests, re-simulate human browsing to maintain session
                if (i + 1) % 10 == 0:
                    print("Re-simulating human browsing to maintain session...")
                    simulate_human_browsing(scraper)
                    
            # Stop if we've reached the maximum number of players to process
            if args.max_players and i + 1 >= args.max_players:
                print(f"Reached maximum number of players to process ({args.max_players})")
                break

        print(f"Processing complete. Successful: {successful}, Failed: {failed}, Skipped: {skipped}")
        if successful + failed > 0:
            print(f"Success rate: {successful/(successful+failed)*100:.1f}% (excluding skipped)")
    except FileNotFoundError:
        print(f"Error: The file {args.file} was not found. Please ensure it exists.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

# Main block
if __name__ == "__main__":
    main()