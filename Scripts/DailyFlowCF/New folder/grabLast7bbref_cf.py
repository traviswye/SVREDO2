import cloudscraper
import requests
from bs4 import BeautifulSoup
import statistics
from datetime import date
import json
import urllib3
import time
import random
import sys
import argparse

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

def is_away_game(game_data):
    """
    Determine if a game is away or home based on the data row
    Returns True if away, False if home
    """
    # Check the standard home/away indicator in column 4
    if len(game_data) > 4 and game_data[4] == '@':
        return True
    
    # Additional checks if the standard indicator is missing or unclear
    for i, value in enumerate(game_data):
        if value == '@':
            return True
    
    # If we get here, assume it's a home game
    return False
    
def safe_convert(value, to_type=float, default=0):
    """Safely convert a value to the specified type with a default fallback"""
    if value is None or value == '':
        return default
    try:
        # Remove percentage sign and other non-numeric characters if present
        if isinstance(value, str):
            value = value.replace('%', '').replace(',', '')
        return to_type(value)
    except (ValueError, TypeError):
        return default

def calculate_pa(ab, bb, hbp, sh, sf):
    """Calculate plate appearances from component stats"""
    # PA = AB + BB + HBP + SH + SF
    return ab + bb + hbp + sh + sf

def calculate_batting_stats(h, ab, bb=0, hbp=0, sf=0, doubles=0, triples=0, hr=0):
    """Calculate batting average, OBP, SLG, and OPS"""
    # Default values if denominators are zero
    ba, obp, slg, ops = 0.0, 0.0, 0.0, 0.0
    
    if ab > 0:
        ba = h / ab
        slg = (h + doubles + 2*triples + 3*hr) / ab
    
    if (ab + bb + hbp + sf) > 0:
        obp = (h + bb + hbp) / (ab + bb + hbp + sf)
    
    ops = obp + slg
    
    return ba, obp, slg, ops

# Replace your current table-finding logic with this more flexible approach
def scrape_last_8_games_with_opponents(scraper, bbrefid, year):
    # Add random delay before fetching
    delay = random.uniform(3, 6)
    print(f"Waiting for {delay:.2f} seconds before fetching data for {bbrefid}...")
    time.sleep(delay)
    
    # Construct the URL
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={bbrefid}&t=b&year={year}"
    print(f"Attempting to scrape URL: {url}")

    try:
        # Add referer for more realistic request
        scraper.headers.update({'Referer': 'https://www.baseball-reference.com/players/'})
        
        # Fetch the page content
        response = scraper.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page for player {bbrefid} in year {year}. HTTP Status Code: {response.status_code}")
            return None
            
        # Add small delay to mimic human reading time
        time.sleep(random.uniform(1, 2))
        
        # Check if we might be getting a captcha or empty response
        if len(response.content) < 5000:  # Suspiciously small response
            print(f"Warning: Very small response received ({len(response.content)} bytes). Possible captcha or block.")
            return None

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Try multiple possible div IDs for the game log table
        possible_div_ids = ['div_batting_gamelogs', 'div_players_standard_batting', 'div_game_log', 'div_gamelogs']
        table_div = None
        
        # Try to find the table container by any of the possible IDs
        for div_id in possible_div_ids:
            table_div = soup.find('div', id=div_id)
            if table_div:
                print(f"Found game log table in div with id: {div_id}")
                break
        
        # If still not found, try a more general approach
        if not table_div:
            # Look for any table with "game log" or "batting" in the caption
            tables = soup.find_all('table')
            for table in tables:
                caption = table.find('caption')
                if caption and ('batting' in caption.text.lower() or 'game log' in caption.text.lower() or 'standard' in caption.text.lower()):
                    print(f"Found game log table with caption: {caption.text}")
                    table_div = table.parent  # get the div containing this table
                    break
            
            # If still not found, look for any div that might contain the game log
            if not table_div:
                divs = soup.find_all('div', class_='table_container')
                if divs:
                    table_div = divs[0]  # Take the first table container
                    print(f"Using first table container div found")

        if not table_div:
            print(f"Game log table not found for player {bbrefid} in year {year}")
            # Save HTML for debugging
            with open(f"{bbrefid}_debug.html", 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"Saved HTML to {bbrefid}_debug.html for debugging")
            return None

        # Extract the actual table from the div
        table = table_div.find('table')
        if not table:
            print(f"Table element not found within the game log div for player {bbrefid} in year {year}")
            return None

        # Process the table rows - exclude thead rows explicitly
        thead_rows = table.find_all('tr', class_=lambda x: x and 'thead' in x)
        all_rows = table.find_all('tr')
        rows = [row for row in all_rows if row not in thead_rows and not row.get('class') or 'thead' not in ' '.join(row.get('class', []))]
        
        if len(rows) < 2:
            print(f"Not enough rows to process for player {bbrefid}, found {len(rows)} rows")
            with open(f"{bbrefid}_rows_debug.html", 'w', encoding='utf-8') as f:
                f.write(str(table))
            return None

        # Get the last 8 rows, with the 8th being the season totals
        # Make sure we have enough rows first
        if len(rows) >= 8:
            last_8_rows = rows[-8:]
        else:
            last_8_rows = rows  # Use all available rows
            
        season_totals = last_8_rows[-1]  # The season totals row
        last_7_rows = last_8_rows[:-1] if len(last_8_rows) > 1 else [last_8_rows[0]]  # At least one row for last 7

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

        # Debug counters for opponent IDs
        opp_data_found = 0
        home_away_found = 0

        # Process every row in the table to extract opponent IDs
        for row in rows:
            cells = row.find_all(['td', 'th'])  # Include th for flexibility
            if not cells:
                continue

            # Extract data-stat attribute from cells
            cell_data = {}
            for cell in cells:
                if cell.get('data-stat'):
                    cell_data[cell.get('data-stat')] = cell.get_text(strip=True)
            
            # First attempt to extract team and opponent info
            # Try different possible attribute names for home/away indicators
            team_homeORaway = ''
            for key in ['game_location', 'team_homeORaway']:
                if key in cell_data:
                    team_homeORaway = cell_data[key]
                    home_away_found += 1
                    break
            
            # Try different possible attribute names for opponent team
            opp_ID = ''
            for key in ['opp_name_abbr', 'opp_ID']:
                if key in cell_data and cell_data[key]:
                    opp_ID = cell_data[key]
                    opp_data_found += 1
                    break
            
            # Check if this contains a team abbreviation
            team_abbr = ''
            for key in ['team_name_abbr', 'team_ID']:
                if key in cell_data and cell_data[key]:
                    team_abbr = cell_data[key]
                    
                    # If this is the first valid team we find, use it for homeTeam
                    if homeTeam == "TODO" and team_abbr:
                        homeTeam = team_abbr
                    break
            
            # Check for link to opponent team in the row
            if not opp_ID:
                opp_links = row.find_all('a', href=lambda x: x and '/teams/' in x)
                for link in opp_links:
                    href = link.get('href', '')
                    if '/teams/' in href and '/teams/' + team_abbr not in href:
                        opp_ID = link.get_text(strip=True)
                        opp_data_found += 1
                        break
            
            # Update opponent tracking
            if team_homeORaway == '@':
                if opp_ID:
                    away_opp_ids.append(opp_ID)  # Add opponent ID to the list
            else:
                home_counter += 1  # Increment the counter for home games

        # Print debug info about opponent data
        print(f"Found opponent data in {opp_data_found} rows, home/away indicators in {home_away_found} rows")
        
        # If we couldn't find opponent IDs, generate defaults
        if not away_opp_ids and not home_counter:
            print("Warning: Could not find opponent IDs in any rows. Using default values.")
            away_opp_ids = ["OPP"]
            home_counter = 1
            
        # Process the last 7 rows for aggregation with updated data-stat keys
        game_count = 0  # Initialize the game count
        for row in last_7_rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            game_count += 1  # Increment the game count for each game processed

            # Create a dictionary using data-stat attribute
            cell_data = {}
            for cell in cells:
                if cell.get('data-stat'):
                    cell_data[cell.get('data-stat')] = cell.get_text(strip=True)
            
            # Extract team_ID with fallback
            for key in ['team_name_abbr', 'team_ID']:
                if key in cell_data and cell_data[key]:
                    homeTeam = cell_data[key]
                    break
            
            # Map new column names to old ones for compatibility
            stat_mapping = {
                'b_pa': 'PA', 'PA': 'PA',
                'b_ab': 'AB', 'AB': 'AB',
                'b_r': 'R', 'R': 'R',
                'b_h': 'H', 'H': 'H',
                'b_doubles': '2B', '2B': '2B',
                'b_triples': '3B', '3B': '3B',
                'b_hr': 'HR', 'HR': 'HR',
                'b_rbi': 'RBI', 'RBI': 'RBI',
                'b_bb': 'BB', 'BB': 'BB',
                'b_ibb': 'IBB', 'IBB': 'IBB',
                'b_so': 'SO', 'SO': 'SO',
                'b_hbp': 'HBP', 'HBP': 'HBP',
                'b_sh': 'SH', 'SH': 'SH',
                'b_sf': 'SF', 'SF': 'SF',
                'b_roe': 'ROE', 'ROE': 'ROE',
                'b_gidp': 'GDP', 'GDP': 'GDP',
                'b_sb': 'SB', 'SB': 'SB',
                'b_cs': 'CS', 'CS': 'CS'
            }

            # Update aggregate variables using the mapping
            for new_key, old_key in stat_mapping.items():
                if new_key in cell_data:
                    value = cell_data.get(new_key, '0')
                    try:
                        aggregate[old_key] += int(value or 0)
                    except ValueError:
                        # Handle non-integer values
                        pass

            # Safely convert values to float with error handling
            def safe_float(value, default=0.0):
                try:
                    # Remove percentage sign if present
                    if isinstance(value, str):
                        value = value.replace('%', '')
                    # Return float value or default if conversion fails
                    return float(value or default)
                except (ValueError, TypeError):
                    return default

            # Update additional aggregate variables with new keys
            try:
                # Try multiple possible keys for each stat
                cWPA = 0.0
                for key in ['b_cwpa', 'cwpa_bat']:
                    if key in cell_data:
                        cWPA_text = cell_data[key].replace('%', '')
                        if cWPA_text and cWPA_text != 'cWPA':  # Skip header row value
                            cWPA = safe_float(cWPA_text, 0.0) / 100  # Convert from percentage to decimal
                        break
                
                aLI = 0.0
                for key in ['b_leverage_index_avg', 'leverage_index_avg']:
                    if key in cell_data:
                        aLI = safe_float(cell_data[key], 0.0)
                        break

                acLI = 0.0
                for key in ['b_cli_avg', 'cli_avg']:
                    if key in cell_data:
                        acLI = safe_float(cell_data[key], 0.0)
                        break

                WPA = 0.0
                for key in ['b_wpa', 'wpa_bat']:
                    if key in cell_data:
                        WPA = safe_float(cell_data[key], 0.0)
                        break

                RE24 = 0.0
                for key in ['b_baseout_runs', 're24_bat']:
                    if key in cell_data:
                        RE24 = safe_float(cell_data[key], 0.0)
                        break

                DFS_DK = 0.0
                for key in ['b_draftkings_points', 'draftkings_points']:
                    if key in cell_data:
                        DFS_DK = safe_float(cell_data[key], 0.0)
                        break

                DFS_FD = 0.0
                for key in ['b_fanduel_points', 'fanduel_points']:
                    if key in cell_data:
                        DFS_FD = safe_float(cell_data[key], 0.0)
                        break

                # Update aggregate totals
                aggregate['WPA'] += WPA
                aggregate['cWPA'] += cWPA
                aggregate['RE24'] += RE24
                aggregate['DFS_DK'] += DFS_DK
                aggregate['DFS_FD'] += DFS_FD

                # Collect lists for mode and averaging calculations
                if aLI > 0:
                    aLI_list.append(aLI)
                if acLI > 0:
                    acLI_list.append(acLI)
                
                # Get batting order position
                bop = 0
                for key in ['b_lineup_position', 'batting_order_position']:
                    if key in cell_data and cell_data[key]:
                        try:
                            bop = int(cell_data[key] or 0)
                            if bop > 0:  # Only add valid BOP values
                                BOP_list.append(bop)
                            break
                        except ValueError:
                            pass

                # Check home or away for last 7 rows
                home_or_away = ''
                for key in ['game_location', 'team_homeORaway']:
                    if key in cell_data:
                        home_or_away = cell_data[key]
                        break

                if home_or_away == '@':
                    # Extract opponent ID
                    opp = ''
                    for key in ['opp_name_abbr', 'opp_ID']:
                        if key in cell_data and cell_data[key]:
                            opp = cell_data[key]
                            break
                    
                    # If still no opponent, try looking for links
                    if not opp:
                        opp_links = row.find_all('a', href=lambda x: x and '/teams/' in x)
                        for link in opp_links:
                            href = link.get('href', '')
                            if '/teams/' in href and team_abbr and '/teams/' + team_abbr not in href:
                                opp = link.get_text(strip=True)
                                break
                    
                    # If we found an opponent, add it to the list
                    if opp:
                        away_opp_ids_last7.append(opp)
                    else:
                        away_opp_ids_last7.append('OPP')  # Default if we can't find one
                else:
                    home_counter_last7 += 1

            except Exception as e:
                print(f"Error processing advanced stats in row: {e}")

        # If we couldn't find opponent IDs for last 7 games, use defaults
        if not away_opp_ids_last7 and not home_counter_last7:
            print("Warning: Could not find opponent IDs in last 7 rows. Using default values.")
            away_opp_ids_last7 = ["OPP"]
            home_counter_last7 = 1

        # Calculate aggregated stats (BA, OBP, SLG, OPS)
        BA = aggregate['H'] / aggregate['AB'] if aggregate['AB'] > 0 else 0.0
        OBP = (aggregate['H'] + aggregate['BB'] + aggregate['HBP']) / (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) if (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) > 0 else 0.0
        SLG = (aggregate['H'] + (2 * aggregate['2B']) + (3 * aggregate['3B']) + (4 * aggregate['HR'])) / aggregate['AB'] if aggregate['AB'] > 0 else 0.0
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

        # Print aggregate stats
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

        # Extract the season totals and adapt to the new format
        # Get cell values more flexibly
        season_totals_data = []
        for cell in season_totals.find_all(['td', 'th']):
            season_totals_data.append(cell.get_text(strip=True))

        # Extract the second-to-last row for SingleGame payload
        single_game_row = rows[-2] if len(rows) >= 2 else rows[0]  # Fallback to first row if needed
        single_game_data = []
        for cell in single_game_row.find_all(['td', 'th']):
            single_game_data.append(cell.get_text(strip=True))

        single_game_data2 = None
        # Check if there was a doubleheader (looks for "(1)" or "(2)" in date column)
        if len(rows) >= 3 and len(single_game_data) > 2 and ('(' in single_game_data[2] or ')' in single_game_data[2]):
            single_game_row2 = rows[-3]  # third-to-last row as there was a double header
            single_game_data2 = []
            for cell in single_game_row2.find_all(['td', 'th']):
                single_game_data2.append(cell.get_text(strip=True))
            
        # Default subset for season totals - this might need adjustment based on table structure
        subset_season_totals = season_totals_data[8:-1] if len(season_totals_data) > 9 else season_totals_data

        # Fill single_game_data to ensure it has enough elements
        while len(single_game_data) < 38:
            single_game_data.append('')

        if single_game_data2 is not None:
            while len(single_game_data2) < 38:
                single_game_data2.append('')

        # Ensure we have enough elements in subset_season_totals
        while len(subset_season_totals) < 30:
            subset_season_totals.append('0')

        print(f"Successfully scraped data for {bbrefid}")
        print(f"Away opponents: {away_opp_ids}")
        print(f"Home games: {home_counter}")
        print(f"Last 7 away opponents: {away_opp_ids_last7}")
        print(f"Last 7 home games: {home_counter_last7}")

        # Return last_7_rows as part of the result
        return single_game_data, single_game_data2, homeTeam, subset_season_totals, aggregated_data, away_opp_ids, home_counter, home_counter_last7, away_opp_ids_last7, last_7_rows, rows, season_totals
        
    except Exception as e:
        print(f"Error scraping data for player {bbrefid}: {e}")
        import traceback
        traceback.print_exc()
        return None


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


def process_and_post_trailing_gamelogs(scraper, api_session, bbrefid, year):
    # Add delay before starting processing
    delay = random.uniform(1, 3)
    print(f"Starting to process player {bbrefid}. Waiting {delay:.2f} seconds first...")
    time.sleep(delay)
    
    try:
        # Scrape data
        result = scrape_last_8_games_with_opponents(scraper, bbrefid, year)
        
        if result is None:
            print(f"Failed to scrape data for {bbrefid}. Skipping...")
            return False
            
        # Correctly unpacking all 12 values returned by scrape_last_8_games_with_opponents
        single_game_data, single_game_data2, homeTeam, subset_season_totals, aggregated_data, away_opp_ids, home_counter, home_counter_last7, away_opp_ids_last7, last_7_rows, rows, season_totals = result
        
        # We need to properly count home and away games for Last7G
        home_games_last7 = 0
        away_games_last7 = 0
        
        # Process the last_7_rows directly to count home/away games
        for row in last_7_rows:
            row_data = []
            for cell in row.find_all(['td', 'th']):
                row_data.append(cell.get_text(strip=True))
            
            if is_away_game(row_data):
                away_games_last7 += 1
            else:
                home_games_last7 += 1
        
        # Update the home_counter_last7 and away_opp_ids_last7 length with correct counts
        home_counter_last7 = home_games_last7
        # Keep away_opp_ids_last7 as is, but make sure we use the correct count
        away_games_last7_count = away_games_last7
        
        # Prepare payloads for normalization API
        payload = {
            "bbrefId": bbrefid,
            "oppIds": away_opp_ids,
            "homeGames": home_counter - 1
        }
        payload2 = {
            "bbrefId": bbrefid,
            "oppIds": away_opp_ids_last7,
            "homeGames": home_counter_last7
        }
        
        # Determine if single game is home or away
        is_away_game_fn = False
        if len(single_game_data) > 4:
            is_away_game_fn = single_game_data[4] == '@'
        
        # Find the correct opponent ID
        opp_ID = None
        
        # First check if we have valid away_opp_ids or home_counter from the data we already processed
        if is_away_game_fn and len(away_opp_ids) > 0:
            # Use the most recent away opponent (first in the list)
            opp_ID = away_opp_ids[0]
        elif not is_away_game_fn and home_counter > 0:
            # For home games, look for the opponent ID in the relevant data structure
            # Since the HTML structure can vary, we need to search more extensively
            
            # Try to extract from single_game_data directly - check common positions
            possible_opp_columns = [5, 6, 7]  # Common positions for opponent IDs
            for col in possible_opp_columns:
                if len(single_game_data) > col:
                    value = single_game_data[col]
                    # Check if it looks like a team abbreviation (2-3 uppercase letters)
                    if value and len(value) in [2, 3] and value.isupper() and value != '@':
                        opp_ID = value
                        break
        
        # If we still don't have an opponent ID, use a fallback
        if not opp_ID:
            # Try to find it by examining the data more carefully
            for i in range(len(single_game_data)):
                value = single_game_data[i]
                # Look for anything that resembles a team abbreviation
                if value and len(value) in [2, 3, 4] and value.isupper() and value != '@' and value != homeTeam:
                    # Skip values that are likely not team abbreviations
                    if value not in ['RF', 'CF', 'LF', '1B', '2B', '3B', 'SS', 'C', 'P', 'DH', 'PH']:
                        opp_ID = value
                        break
        
        # Last resort fallback
        if not opp_ID:
            print(f"WARNING: Could not determine opponent ID for {bbrefid}. Using first available opponent.")
            print(f"Single game data: {single_game_data}")
            # Use the first opponent from full list as fallback
            if away_opp_ids:
                opp_ID = away_opp_ids[0]
            else:
                opp_ID = "OPP"  # Default fallback if nothing else works
        
        payload3 = {
            "bbrefId": bbrefid,
            "oppIds": [opp_ID],
            "homeGames": 0 if is_away_game_fn else 1
        }
        
        print(f"Created payload3 for single game: {payload3}")

        # Normalize ParkFactors API endpoint
        normalize_api_url = "https://localhost:44346/api/ParkFactors/normalize"
        trailing_gamelog_api_url = "https://localhost:44346/api/TrailingGameLogSplits"

        # Add small delay before API call
        time.sleep(random.uniform(0.5, 1.5))
        
        try:
            response = api_session.post(normalize_api_url, json=payload, verify=False)
            response.raise_for_status()
            api_response = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling normalize API for full season: {e}")
            print(f"{payload}")
            return False

        time.sleep(random.uniform(0.5, 1))
        
        try:
            response2 = api_session.post(normalize_api_url, json=payload2, verify=False)
            response2.raise_for_status()
            api_response2 = response2.json()
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling normalize API for last 7 games: {e}")
            print(f"{payload2}")
            return False

        time.sleep(random.uniform(0.5, 1))
        
        try:
            response3 = api_session.post(normalize_api_url, json=payload3, verify=False)
            response3.raise_for_status()
            api_response3 = response3.json()
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling normalize API for last 1 game: {e}")
            print(f"{payload3}")
            return False

        # LAST7G PAYLOAD - Update with correct home/away games
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
            "homeGames": home_games_last7,
            "awayGames": away_games_last7_count,
            "homeParkFactor": api_response2["homeParkFactor"],
            "awayParkFactorAvg": api_response2["avgAwayParkFactor"],
            "dateUpdated": date.today().isoformat()
        }

        # SEASON PAYLOAD - Complete rewrite
        # Get totals directly from the season_totals row
        season_totals_data = []
        for cell in season_totals.find_all(['td', 'th']):
            season_totals_data.append(cell.get_text(strip=True))
        
        # Default subset for season totals (adjust based on your table structure)
        # This should properly extract the stats starting at the right position
        subset_season_totals = []
        
        # Look for the start of stats (usually after Gtm, Date, etc.)
        stats_start_index = 0
        for i, value in enumerate(season_totals_data):
            # Look for PA or AB as indicators of where stats begin
            if value == 'PA' or value == 'AB':
                stats_start_index = i
                break
        
        # If we couldn't find the start, use a reasonable default
        if stats_start_index == 0:
            stats_start_index = 8  # Common position in season totals row
        
        # Extract the stats properly
        subset_season_totals = season_totals_data[stats_start_index:]
        
        # Ensure we have enough elements
        while len(subset_season_totals) < 30:
            subset_season_totals.append('0')
        
        # Count the actual games from the individual game rows
        season_games = len(rows) - 1  # Exclude the totals row
        
        # Count home and away games properly for the season
        season_home_games = 0
        season_away_games = 0
        
        for row in rows[:-1]:  # Exclude the season totals row
            row_data = []
            for cell in row.find_all(['td', 'th']):
                row_data.append(cell.get_text(strip=True))
            
            if is_away_game(row_data):
                season_away_games += 1
            else:
                season_home_games += 1
        
        # Print the season_totals_data for debugging
        print(f"Season totals data for {bbrefid}: {season_totals_data}")
        
        # Try to extract primary stats directly using data-stat attributes
        cell_data = {}
        for cell in season_totals.find_all(['td', 'th']):
            if cell.get('data-stat'):
                cell_data[cell.get('data-stat')] = cell.get_text(strip=True)
        
        # Initialize season stats variables
        season_pa = 0
        season_ab = 0
        season_r = 0
        season_h = 0
        season_2b = 0
        season_3b = 0
        season_hr = 0
        season_rbi = 0
        
        # Extract stats using multiple possible keys
        for key_options, var_name in [
            (['PA', 'b_pa'], 'season_pa'),
            (['AB', 'b_ab'], 'season_ab'),
            (['R', 'b_r'], 'season_r'),
            (['H', 'b_h'], 'season_h'),
            (['2B', 'b_doubles'], 'season_2b'),
            (['3B', 'b_triples'], 'season_3b'),
            (['HR', 'b_hr'], 'season_hr'),
            (['RBI', 'b_rbi'], 'season_rbi'),
            # Add more stat mappings as needed
        ]:
            for key in key_options:
                if key in cell_data:
                    value = safe_convert(cell_data[key], int, 0)
                    locals()[var_name] = value
                    break
        
        # If stats are still 0, try to extract from the subset_season_totals
        if season_pa == 0 and len(subset_season_totals) > 0:
            season_pa = safe_convert(subset_season_totals[0], int, 0)
        if season_ab == 0 and len(subset_season_totals) > 1:
            season_ab = safe_convert(subset_season_totals[1], int, 0)
        if season_r == 0 and len(subset_season_totals) > 2:
            season_r = safe_convert(subset_season_totals[2], int, 0)
        if season_h == 0 and len(subset_season_totals) > 3:
            season_h = safe_convert(subset_season_totals[3], int, 0)
        if season_2b == 0 and len(subset_season_totals) > 4:
            season_2b = safe_convert(subset_season_totals[4], int, 0)
        if season_3b == 0 and len(subset_season_totals) > 5:
            season_3b = safe_convert(subset_season_totals[5], int, 0)
        if season_hr == 0 and len(subset_season_totals) > 6:
            season_hr = safe_convert(subset_season_totals[6], int, 0)
        if season_rbi == 0 and len(subset_season_totals) > 7:
            season_rbi = safe_convert(subset_season_totals[7], int, 0)
        
        # If the stats are still missing, sum them from the individual game rows
        if season_pa == 0 or season_ab == 0:
            all_pa = 0
            all_ab = 0
            all_r = 0
            all_h = 0
            all_2b = 0
            all_3b = 0
            all_hr = 0
            all_rbi = 0
            
            for row in rows[:-1]:  # Exclude the season totals row
                cell_data = {}
                for cell in row.find_all(['td', 'th']):
                    if cell.get('data-stat'):
                        cell_data[cell.get('data-stat')] = cell.get_text(strip=True)
                
                # Add up stats from each game
                for key, var_name in [
                    (['PA', 'b_pa'], 'all_pa'),
                    (['AB', 'b_ab'], 'all_ab'),
                    (['R', 'b_r'], 'all_r'),
                    (['H', 'b_h'], 'all_h'),
                    (['2B', 'b_doubles'], 'all_2b'),
                    (['3B', 'b_triples'], 'all_3b'),
                    (['HR', 'b_hr'], 'all_hr'),
                    (['RBI', 'b_rbi'], 'all_rbi'),
                ]:
                    for k in key:
                        if k in cell_data:
                            value = safe_convert(cell_data[k], int, 0)
                            locals()[var_name] += value
                            break
            
            # Use these sums if the season totals were missing
            if season_pa == 0:
                season_pa = all_pa
            if season_ab == 0:
                season_ab = all_ab
            if season_r == 0:
                season_r = all_r
            if season_h == 0:
                season_h = all_h
            if season_2b == 0:
                season_2b = all_2b
            if season_3b == 0:
                season_3b = all_3b
            if season_hr == 0:
                season_hr = all_hr
            if season_rbi == 0:
                season_rbi = all_rbi
        
        # If PA is still 0 but we have AB, calculate PA
        if season_pa == 0 and season_ab > 0:
            season_bb = safe_convert(subset_season_totals[8], int, 0)
            season_hbp = safe_convert(subset_season_totals[11], int, 0)
            season_sh = safe_convert(subset_season_totals[12], int, 0)
            season_sf = safe_convert(subset_season_totals[13], int, 0)
            season_pa = calculate_pa(season_ab, season_bb, season_hbp, season_sh, season_sf)
        
        # Extract all other stats directly from subset_season_totals
        season_bb = safe_convert(subset_season_totals[8], int, 0)
        season_ibb = safe_convert(subset_season_totals[9], int, 0)
        season_so = safe_convert(subset_season_totals[10], int, 0)
        season_hbp = safe_convert(subset_season_totals[11], int, 0)
        season_sh = safe_convert(subset_season_totals[12], int, 0)
        season_sf = safe_convert(subset_season_totals[13], int, 0)
        season_roe = safe_convert(subset_season_totals[14], int, 0)
        season_gdp = safe_convert(subset_season_totals[15], int, 0)
        season_sb = safe_convert(subset_season_totals[16], int, 0)
        season_cs = safe_convert(subset_season_totals[17], int, 0)
        
        # Calculate batting stats
        season_ba, season_obp, season_slg, season_ops = calculate_batting_stats(
            season_h, season_ab, season_bb, season_hbp, season_sf, season_2b, season_3b, season_hr
        )
        
        # Create the updated Season payload
        json_payloadTOT = {
            "bbrefId": bbrefid,
            "team": homeTeam,
            "split": "Season",
            "splitParkFactor": api_response["totalParkFactor"],
            "g": season_games,
            "pa": season_pa,
            "ab": season_ab,
            "r": season_r,
            "h": season_h,
            "doubles": season_2b,
            "triples": season_3b,
            "hr": season_hr,
            "rbi": season_rbi,
            "bb": season_bb,
            "ibb": season_ibb,
            "so": season_so,
            "hbp": season_hbp,
            "sh": season_sh,
            "sf": season_sf,
            "roe": season_roe,
            "gdp": season_gdp,
            "sb": season_sb,
            "cs": season_cs,
            "ba": round(season_ba, 3),
            "obp": round(season_obp, 3),
            "slg": round(season_slg, 3),
            "ops": round(season_ops, 3),
            "bop": safe_convert(subset_season_totals[22], int, -1) if len(subset_season_totals) > 22 and subset_season_totals[22] else -1,
            "ali": safe_convert(subset_season_totals[23], float, 0.0) if len(subset_season_totals) > 23 else 0.0,
            "wpa": safe_convert(subset_season_totals[24], float, 0.0) if len(subset_season_totals) > 24 else 0.0,
            "acLI": safe_convert(subset_season_totals[25], float, 0.0) if len(subset_season_totals) > 25 else 0.0,
            "cwpa": f"{safe_convert(subset_season_totals[26], float, 0.0)}%" if len(subset_season_totals) > 26 else "0%",
            "rE24": safe_convert(subset_season_totals[27], float, 0.0) if len(subset_season_totals) > 27 else 0.0,
            "dfsDk": safe_convert(subset_season_totals[28], float, 0.0) if len(subset_season_totals) > 28 else 0.0,
            "dfsFd": safe_convert(subset_season_totals[29], float, 0.0) if len(subset_season_totals) > 29 else 0.0,
            "homeGames": season_home_games,
            "awayGames": season_away_games,
            "homeParkFactor": api_response["homeParkFactor"],
            "awayParkFactorAvg": api_response["avgAwayParkFactor"],
            "dateUpdated": date.today().isoformat()
        }

        # SINGLEGAME PAYLOAD - Fix date and stats issues
        # Make sure we're correctly identifying if the single game is home or away
        is_single_game_away = is_away_game(single_game_data)
        sg_homeGames = 0 if is_single_game_away else 1
        sg_awayGames = 1 if is_single_game_away else 0
        
        converted_date = convert_date(single_game_data[2])
        if converted_date is None:
            # If date conversion failed, use today's date as fallback
            converted_date = date.today().isoformat()

        # Extract values with proper type conversion
        sg_ab = safe_convert(single_game_data[9], int, 0)
        sg_r = safe_convert(single_game_data[10], int, 0)
        sg_h = safe_convert(single_game_data[11], int, 0)
        sg_doubles = safe_convert(single_game_data[12], int, 0)
        sg_triples = safe_convert(single_game_data[13], int, 0)
        sg_hr = safe_convert(single_game_data[14], int, 0)
        sg_rbi = safe_convert(single_game_data[15], int, 0)
        sg_bb = safe_convert(single_game_data[16], int, 0)
        sg_ibb = safe_convert(single_game_data[17], int, 0)
        sg_so = safe_convert(single_game_data[18], int, 0)
        sg_hbp = safe_convert(single_game_data[19], int, 0)
        sg_sh = safe_convert(single_game_data[20], int, 0)
        sg_sf = safe_convert(single_game_data[21], int, 0)
        sg_roe = safe_convert(single_game_data[22], int, 0)
        sg_gdp = safe_convert(single_game_data[23], int, 0)
        sg_sb = safe_convert(single_game_data[24], int, 0)
        sg_cs = safe_convert(single_game_data[25], int, 0)

        # Calculate PA if it's missing or zero
        sg_pa = safe_convert(single_game_data[8], int, 0)
        if sg_pa == 0:
            sg_pa = calculate_pa(sg_ab, sg_bb, sg_hbp, sg_sh, sg_sf)

        # Calculate batting statistics
        sg_ba, sg_obp, sg_slg, sg_ops = calculate_batting_stats(
            sg_h, sg_ab, sg_bb, sg_hbp, sg_sf, sg_doubles, sg_triples, sg_hr
        )

        json_payloadSG = {
            "bbrefId": bbrefid,
            "team": homeTeam,
            "split": "SingleGame",
            "splitParkFactor": api_response3["totalParkFactor"],
            "g": 1,
            "pa": sg_pa,
            "ab": sg_ab,
            "r": sg_r,
            "h": sg_h,
            "doubles": sg_doubles,
            "triples": sg_triples,
            "hr": sg_hr,
            "rbi": sg_rbi,
            "bb": sg_bb,
            "ibb": sg_ibb,
            "so": sg_so,
            "hbp": sg_hbp,
            "sh": sg_sh,
            "sf": sg_sf,
            "roe": sg_roe,
            "gdp": sg_gdp,
            "sb": sg_sb,
            "cs": sg_cs,
            "ba": round(sg_ba, 3),
            "obp": round(sg_obp, 3),
            "slg": round(sg_slg, 3),
            "ops": round(sg_ops, 3),
            "bop": safe_convert(single_game_data[30], int, -1) if len(single_game_data) > 30 and single_game_data[30] else -1,
            "ali": safe_convert(single_game_data[31], float, 0.0) if len(single_game_data) > 31 else 0.0,
            "wpa": safe_convert(single_game_data[32], float, 0.0) if len(single_game_data) > 32 else 0.0,
            "acLI": safe_convert(single_game_data[33], float, 0.0) if len(single_game_data) > 33 else 0.0,
            "cwpa": f"{safe_convert(single_game_data[34].replace('%', ''), float, 0.0)}%" if len(single_game_data) > 34 and single_game_data[34] else "0%",
            "rE24": safe_convert(single_game_data[35], float, 0.0) if len(single_game_data) > 35 else 0.0,
            "dfsDk": safe_convert(single_game_data[36], float, 0.0) if len(single_game_data) > 36 else 0.0,
            "dfsFd": safe_convert(single_game_data[37], float, 0.0) if len(single_game_data) > 37 else 0.0,
            "homeGames": sg_homeGames,
            "awayGames": sg_awayGames,
            "homeParkFactor": api_response3["homeParkFactor"],
            "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
            "dateUpdated": converted_date
        }

        # Handle doubleheader games in the same way
        json_payloadSG2 = None
        if single_game_data2 is not None:
            # Check if second game is home or away
            is_single_game2_away = is_away_game(single_game_data2)
            sg2_homeGames = 0 if is_single_game2_away else 1
            sg2_awayGames = 1 if is_single_game2_away else 0
            
            sg2_ab = safe_convert(single_game_data2[9], int, 0)
            sg2_r = safe_convert(single_game_data2[10], int, 0)
            sg2_h = safe_convert(single_game_data2[11], int, 0)
            sg2_doubles = safe_convert(single_game_data2[12], int, 0)
            sg2_triples = safe_convert(single_game_data2[13], int, 0)
            sg2_hr = safe_convert(single_game_data2[14], int, 0)
            sg2_rbi = safe_convert(single_game_data2[15], int, 0)
            sg2_bb = safe_convert(single_game_data2[16], int, 0)
            sg2_ibb = safe_convert(single_game_data2[17], int, 0)
            sg2_so = safe_convert(single_game_data2[18], int, 0)
            sg2_hbp = safe_convert(single_game_data2[19], int, 0)
            sg2_sh = safe_convert(single_game_data2[20], int, 0)
            sg2_sf = safe_convert(single_game_data2[21], int, 0)
            sg2_roe = safe_convert(single_game_data2[22], int, 0)
            sg2_gdp = safe_convert(single_game_data2[23], int, 0)
            sg2_sb = safe_convert(single_game_data2[24], int, 0)
            sg2_cs = safe_convert(single_game_data2[25], int, 0)
            
            # Calculate PA if it's missing or zero
            sg2_pa = safe_convert(single_game_data2[8], int, 0)
            if sg2_pa == 0:
                sg2_pa = calculate_pa(sg2_ab, sg2_bb, sg2_hbp, sg2_sh, sg2_sf)
            
            # Calculate batting statistics
            sg2_ba, sg2_obp, sg2_slg, sg2_ops = calculate_batting_stats(
                sg2_h, sg2_ab, sg2_bb, sg2_hbp, sg2_sf, sg2_doubles, sg2_triples, sg2_hr
            )
            
            json_payloadSG2 = {
                "bbrefId": bbrefid,
                "team": homeTeam,
                "split": "SingleGame2",
                "splitParkFactor": api_response3["totalParkFactor"],
                "g": 1,
                "pa": sg2_pa,
                "ab": sg2_ab,
                "r": sg2_r,
                "h": sg2_h,
                "doubles": sg2_doubles,
                "triples": sg2_triples,
                "hr": sg2_hr,
                "rbi": sg2_rbi,
                "bb": sg2_bb,
                "ibb": sg2_ibb,
                "so": sg2_so,
                "hbp": sg2_hbp,
                "sh": sg2_sh,
                "sf": sg2_sf,
                "roe": sg2_roe,
                "gdp": sg2_gdp,
                "sb": sg2_sb,
                "cs": sg2_cs,
                "ba": round(sg2_ba, 3),
                "obp": round(sg2_obp, 3),
                "slg": round(sg2_slg, 3),
                "ops": round(sg2_ops, 3),
                "bop": safe_convert(single_game_data2[30], int, -1) if len(single_game_data2) > 30 and single_game_data2[30] else -1,
                "ali": safe_convert(single_game_data2[31], float, 0.0) if len(single_game_data2) > 31 else 0.0,
                "wpa": safe_convert(single_game_data2[32], float, 0.0) if len(single_game_data2) > 32 else 0.0,
                "acLI": safe_convert(single_game_data2[33], float, 0.0) if len(single_game_data2) > 33 else 0.0,
                "cwpa": f"{safe_convert(single_game_data2[34].replace('%', ''), float, 0.0)}%" if len(single_game_data2) > 34 and single_game_data2[34] else "0%",
                "rE24": safe_convert(single_game_data2[35], float, 0.0) if len(single_game_data2) > 35 else 0.0,
                "dfsDk": safe_convert(single_game_data2[36], float, 0.0) if len(single_game_data2) > 36 else 0.0,
                "dfsFd": safe_convert(single_game_data2[37], float, 0.0) if len(single_game_data2) > 37 else 0.0,
                "homeGames": sg2_homeGames,
                "awayGames": sg2_awayGames,
                "homeParkFactor": api_response3["homeParkFactor"],
                "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
                "dateUpdated": converted_date
            }
            
        # Post data to TrailingGameLogSplits API
        # Add small delay between API calls
        time.sleep(random.uniform(0.5, 1.5))
        
        try:
            responseL7 = api_session.post(trailing_gamelog_api_url, json=json_payloadL7, verify=False)
            responseL7.raise_for_status()
            print(f"Successfully posted Last7G data for {bbrefid}: {responseL7.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting Last7G data for {bbrefid}: {e}")
            return False

        time.sleep(random.uniform(0.5, 1))
        
        try:
            responseTOT = api_session.post(trailing_gamelog_api_url, json=json_payloadTOT, verify=False)
            responseTOT.raise_for_status()
            print(f"Successfully posted Season data for {bbrefid}: {responseTOT.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting Season data for {bbrefid}: {e}")
            # Print the payload for debugging
            print(f"Season payload that caused error: {json.dumps(json_payloadTOT)}")
            return False

        time.sleep(random.uniform(0.5, 1))
        
        try:
            responseSG = api_session.post(trailing_gamelog_api_url, json=json_payloadSG, verify=False)
            responseSG.raise_for_status()
            print(f"Successfully posted SingleGame data for {bbrefid}: {responseSG.status_code}")
            
            if json_payloadSG2 is not None:
                time.sleep(random.uniform(0.5, 1))
                responseSG2 = api_session.post(trailing_gamelog_api_url, json=json_payloadSG2, verify=False)
                responseSG2.raise_for_status()
                print(f"Successfully posted SingleGame2 data for {bbrefid}: {responseSG2.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error posting SingleGame data for {bbrefid}: {e}")
            print(f"SingleGame payload that caused error: {json.dumps(json_payloadSG)}")
            if json_payloadSG2 is not None:
                print(f"SingleGame2 payload that caused error: {json.dumps(json_payloadSG2)}")
            return False
            
        # If we made it here, all requests succeeded
        return True
        
    except Exception as e:
        print(f"Error processing player {bbrefid}: {e}")
        import traceback
        traceback.print_exc()  # Print detailed stack trace for debugging
        return False

def get_todays_hitters(api_session, date_str):
    url = f"{API_BASE_URL}/Hitters/todaysHitters/{date_str}"
    print(f"Fetching today's hitters from: {url}")
    
    try:
        response = api_session.get(url)
        if response.status_code == 200:
            hitters = response.json()
            print(f"Successfully retrieved {len(hitters)} hitters for {date_str}")
            return hitters
        else:
            print(f"Failed to retrieve today's hitters. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting today's hitters: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Baseball Reference Batter Statistics Scraper")
    parser.add_argument("--date", "-d", help="Date in format yy-MM-dd (e.g., 25-03-29) to scrape players scheduled for games on this date")
    parser.add_argument("--input", "-i", help="Input file containing bbrefids to scrape", default="bbrefids.txt")
    parser.add_argument("--year", "-y", help="Year to scrape data for", type=int, default=2025)
    args = parser.parse_args()

    print("Starting Baseball Reference Batter Statistics Scraper with Enhanced Anti-Detection Measures")
    
    year = args.year  # Default or from command line
    
    try:
        # Create a CloudScraper session for Baseball Reference
        scraper = create_scraper_session()
        
        # Simulate human browsing to avoid detection
        if not simulate_human_browsing(scraper):
            print("Failed to establish browsing pattern. Exiting...")
            return
            
        # Create a regular session for API calls
        api_session = create_api_session()
        
        # Determine which players to process
        bbrefids = []
        if args.date:
            # Use the date to get today's hitters from the API
            print(f"Using date parameter: {args.date} to get players scheduled for games today")
            bbrefids = get_todays_hitters(api_session, args.date)
            if not bbrefids:
                print("No hitters found for today's games. Exiting...")
                return
        else:
            # Use the input file to get the list of players
            input_file = args.input
            print(f"Reading player IDs from file: {input_file}")
            try:
                with open(input_file, "r", encoding="utf-8") as infile:
                    bbrefids = [line.strip() for line in infile if line.strip()]  # Remove empty lines
            except FileNotFoundError:
                print(f"Error: The file {input_file} was not found. Please ensure it exists in the same directory.")
                return
            
        print(f"Found {len(bbrefids)} players to process")
        
        # Add a delay before starting to scrape players
        time.sleep(random.uniform(2, 3))
        
        # Process players with random order to appear less bot-like
        random.shuffle(bbrefids)
        
        # Loop through each bbrefid and process it
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        for idx, bbrefid in enumerate(bbrefids):
            print(f"Processing player {idx+1}/{len(bbrefids)}: {bbrefid}")
            
            # Process the player data
            if process_and_post_trailing_gamelogs(scraper, api_session, bbrefid, year):
                success_count += 1
            else:
                failure_count += 1
                
            # Calculate and show progress statistics
            elapsed_time = time.time() - start_time
            players_processed = idx + 1
            avg_time_per_player = elapsed_time / players_processed
            remaining_players = len(bbrefids) - players_processed
            est_remaining_time = remaining_players * avg_time_per_player
            
            # Display progress information
            print(f"Progress: {players_processed}/{len(bbrefids)} players processed")
            print(f"Success rate: {success_count}/{players_processed} ({(success_count/players_processed)*100:.1f}%)")
            
            # Format remaining time nicely
            remaining_hours = int(est_remaining_time // 3600)
            remaining_minutes = int((est_remaining_time % 3600) // 60)
            print(f"Estimated time remaining: {remaining_hours}h {remaining_minutes}m")
                
            # Add a longer delay between players to avoid detection
            if idx < len(bbrefids) - 1:  # Don't delay after the last player
                delay = random.uniform(5, 10)
                print(f"Waiting {delay:.2f} seconds before processing next player...")
                time.sleep(delay)
                
        # Calculate final statistics
        total_time = time.time() - start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        # Display final summary
        print("\n" + "="*60)
        print("Processing Summary")
        print("="*60)
        print(f"Total players processed: {len(bbrefids)}")
        print(f"Successfully processed: {success_count} ({(success_count/len(bbrefids))*100:.1f}%)")
        print(f"Failed to process: {failure_count} ({(failure_count/len(bbrefids))*100:.1f}%)")
        print(f"Total execution time: {hours}h {minutes}m {seconds}s")
        print(f"Average time per player: {(total_time/len(bbrefids)):.2f} seconds")
        print("="*60)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()  # Print detailed stack trace for debugging

if __name__ == "__main__":
    main()