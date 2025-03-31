
import cloudscraper
from bs4 import BeautifulSoup
import statistics
from datetime import date, datetime
import json
import urllib3
import time
import random
import requests
import sys
import argparse

# Suppress HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
API_BASE_URL = "https://localhost:44346/api"

def create_scraper_session():
    """Create and return a cloudscraper session with browser-like headers"""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=5
    )
    
    # Add user-agent and additional headers to mimic a real browser
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    })
    
    return scraper

def simulate_human_browsing(scraper):
    """Simulate human browsing behavior on Baseball Reference to avoid detection"""
    print("Simulating human browsing behavior...")
    
    # Visit the homepage first
    homepage_url = "https://www.baseball-reference.com/"
    response = scraper.get(homepage_url)
    if response.status_code != 200:
        print(f"Failed to access homepage: {response.status_code}")
        return False
    
    # Random sleep to mimic reading the page
    time.sleep(random.uniform(3, 7))
    
    # Visit a few random pages to establish browsing pattern
    random_pages = [
        "https://www.baseball-reference.com/leagues/MLB/2024.shtml",
        "https://www.baseball-reference.com/teams/",
        "https://www.baseball-reference.com/leaders/"
    ]
    
    for page in random_pages:
        if random.random() > 0.7:  # 70% chance to visit each page
            print(f"Visiting {page}...")
            response = scraper.get(page)
            if response.status_code != 200:
                print(f"Failed to access {page}: {response.status_code}")
            
            # Random sleep between page visits
            time.sleep(random.uniform(2, 5))
    
    print("Human browsing simulation completed")
    return True

def get_todays_hitters(api_session, date_str):
    """Get today's hitters from the API endpoint"""
    url = f"{API_BASE_URL}/Hitters/todaysHitters/{date_str}"
    print(f"Fetching today's hitters from: {url}")
    
    try:
        response = api_session.get(url, verify=False)
        if response.status_code == 200:
            hitters = response.json()
            # Debug the response format
            print(f"Response type: {type(hitters)}")
            if isinstance(hitters, list):
                print(f"Successfully retrieved {len(hitters)} hitters for {date_str}")
                if len(hitters) > 0:
                    print(f"Sample first item type: {type(hitters[0])}")
            return hitters
        else:
            print(f"Failed to retrieve today's hitters. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting today's hitters: {e}")
        return None

def scrape_last_8_games_with_opponents(scraper, bbrefid, year):
    """
    Scrape the last 8 games with opponents using cloudscraper instead of requests
    """
    # Construct the URL
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={bbrefid}&t=b&year={year}"
    print(f"Attempting to scrape URL: {url}")

    # Add some randomization to avoid detection
    time.sleep(random.uniform(1, 3))

    # Fetch the page content with cloudscraper
    try:
        response = scraper.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page for player {bbrefid} in year {year}. HTTP Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None

    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Try different possible div IDs for the game log table
    possible_div_ids = [
        'div_batting_gamelogs',           # Standard format
        'div_players_standard_batting',   # Alternative format seen in examples
        'div_game_log',                   # Another possible format
        'batting_gamelogs',               # Format without div prefix
        'players_standard_batting'        # Format without div prefix
    ]
    
    table_div = None
    for div_id in possible_div_ids:
        div = soup.find('div', id=div_id)
        if div:
            table_div = div
            print(f"Found game log table in div with id: {div_id}")
            break
    
    # If still not found, try looking for any table with appropriate class or structure
    if not table_div:
        # Try to find a table with a class that might contain game logs
        tables = soup.find_all('table', class_=lambda c: c and ('game_log' in c.lower() or 'batting' in c.lower() or 'stats_table' in c.lower()))
        if tables:
            # Just use the first matching table's parent div as our container
            table_div = tables[0].parent
            print(f"Found game log table using class-based search")
    
    if not table_div:
        print(f"Game log table not found for player {bbrefid} in year {year}")
        return None

    # Extract the actual table from the div
    table = table_div.find('table')
    if not table:
        print(f"Table element not found within the game log div for player {bbrefid} in year {year}")
        return None
    
    # Debug the table structure
    print(f"Table found with {len(table.find_all('tr'))} rows")

    # Process the table rows
    rows = table.find_all('tr', class_=lambda x: x != 'thead')  # Ignore header rows
    
    # Filter out any non-data rows (like headers)
    rows = [row for row in rows if row.find('td')]
    
    if len(rows) < 2:
        print(f"Not enough rows to process for player {bbrefid}")
        return None

    # Get the last 8 rows, with the 8th being the season totals
    # Make sure we don't try to get more rows than exist
    num_rows = min(8, len(rows))
    last_8_rows = rows[-num_rows:]
    
    # The last row is usually the season totals
    season_totals = last_8_rows[-1]
    
    # All rows except the last one are game logs
    last_7_rows = last_8_rows[:-1]
    
    print(f"Processing {len(last_7_rows)} game rows and 1 season total row")

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

    # Process every row in the table
    for row in rows:
        # Check if the row has cells before attempting to extract data
        cells = row.find_all(['td', 'th'])
        if not cells or len(cells) < 5:  # Ensure there are enough cells to be a data row
            continue

        # Try to create a cell_data dictionary, handling different formats
        cell_data = {}
        
        # First attempt: use data-stat attribute (standard format)
        for cell in cells:
            if 'data-stat' in cell.attrs:
                cell_data[cell['data-stat']] = cell.get_text(strip=True)
        
        # If we couldn't get data using data-stat, try using cell position
        if not cell_data:
            # Common cell indices for important stats (may need adjustment)
            cell_indices = {
                'team_homeORaway': 4,  # Usually column 5 (index 4)
                'opp_ID': 5,          # Usually column 6 (index 5)
                'team_ID': 3          # Usually column 4 (index 3)
            }
            
            for stat, idx in cell_indices.items():
                if idx < len(cells):
                    cell_data[stat] = cells[idx].get_text(strip=True)
        
        # Extract team_homeORaway and opp_ID
        team_homeORaway = cell_data.get('team_homeORaway', '')
        opp_ID = cell_data.get('opp_ID', '')
        
        # If team_homeORaway is not found directly, try to infer it
        if not team_homeORaway and len(cells) > 4:
            # Sometimes @ symbol indicates away game
            text = cells[4].get_text(strip=True)
            if '@' in text:
                team_homeORaway = '@'
        
        # Check home or away and update the appropriate list/counter
        if team_homeORaway == '@':
            if opp_ID:  # Only add if we have an opponent ID
                away_opp_ids.append(opp_ID)  # Add opponent ID to the list
            else:
                # Try to extract opponent ID from the text if not found directly
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if text in ['ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 'COL', 'DET', 
                               'HOU', 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'OAK', 
                               'PHI', 'PIT', 'SDP', 'SEA', 'SFG', 'STL', 'TBR', 'TEX', 'TOR', 'WSN']:
                        away_opp_ids.append(text)
                        break
        else:
            home_counter += 1  # Increment the counter for home games

    # Process the last 7 rows for aggregation
    game_count = 0  # Initialize the game count
    for row in last_7_rows:
        # Check if the row has cells before attempting to extract data
        cells = row.find_all(['td', 'th'])
        if not cells or len(cells) < 8:  # Ensure there are enough cells
            continue

        game_count += 1  # Increment the game count for each game processed

        # Try to create a cell_data dictionary, handling different formats
        cell_data = {}
        
        # First attempt: use data-stat attribute (standard format)
        for cell in cells:
            if 'data-stat' in cell.attrs:
                cell_data[cell['data-stat']] = cell.get_text(strip=True)
        
        # If we couldn't get much data using data-stat, try using cell position
        if len(cell_data) < 5:  # Arbitrary threshold for "not enough data"
            # Map of common column positions for key stats
            stat_positions = {
                'team_ID': 4,
                'team_homeORaway': 5,
                'opp_ID': 6,
                'PA': 9,
                'AB': 10,
                'R': 11,
                'H': 12,
                '2B': 13,
                '3B': 14,
                'HR': 15,
                'RBI': 16,
                'SB': 17,
                'CS': 18,
                'BB': 19,
                'SO': 20,
                'BA': 21,
                'OBP': 22,
                'SLG': 23,
                'OPS': 24,
                'TB': 25,
                'GDP': 26,
                'HBP': 27,
                'SH': 28,
                'SF': 29,
                'IBB': 30,
                'leverage_index_avg': 31,
                'wpa_bat': 32,
                'cli_avg': 33,
                'cwpa_bat': 34,
                're24_bat': 35,
                'draftkings_points': 36,
                'fanduel_points': 37,
                'batting_order_position': 38
            }
            
            for stat, idx in stat_positions.items():
                if idx < len(cells):
                    cell_data[stat] = cells[idx].get_text(strip=True)
        
        # Extract team_ID with a fallback to "TODO"
        homeTeam = cell_data.get('team_ID', 'TODO') if cell_data.get('team_ID') else 'TODO'
        
        # If team_ID is not found directly, try to extract it from another cell
        if homeTeam == 'TODO' and len(cells) > 4:
            team_text = cells[4].get_text(strip=True)
            if team_text in ['ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 'COL', 'DET', 
                           'HOU', 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'OAK', 
                           'PHI', 'PIT', 'SDP', 'SEA', 'SFG', 'STL', 'TBR', 'TEX', 'TOR', 'WSN']:
                homeTeam = team_text

        # Update aggregate variables for PA to CS
        stats = {
            'PA': 'PA', 'AB': 'AB', 'R': 'R', 'H': 'H', '2B': '2B', '3B': '3B', 
            'HR': 'HR', 'RBI': 'RBI', 'BB': 'BB', 'IBB': 'IBB', 'SO': 'SO', 
            'HBP': 'HBP', 'SH': 'SH', 'SF': 'SF', 'ROE': 'ROE', 'GDP': 'GDP', 
            'SB': 'SB', 'CS': 'CS'
        }

        for key, stat in stats.items():
            # Try to get value from cell_data, with fallback
            value_str = cell_data.get(stat, '0')
            if not value_str:
                value_str = '0'
                
            # Clean the value string and convert to int
            try:
                value = int(value_str)
            except ValueError:
                # Try to clean the string if it contains non-numeric characters
                value_str = ''.join(c for c in value_str if c.isdigit() or c == '.')
                try:
                    value = int(float(value_str or 0))
                except ValueError:
                    value = 0
                    
            aggregate[key] += value

        # Update additional aggregate variables
        try:
            # Remove percentage symbols and convert to float
            cWPA_text = cell_data.get('cwpa_bat', '0').replace('%', '')
            if not cWPA_text:
                cWPA_text = '0'
            cWPA = float(cWPA_text) / 100  # Convert from percentage to decimal

            aLI_text = cell_data.get('leverage_index_avg', '0').replace('%', '')
            if not aLI_text:
                aLI_text = '0'
            aLI = float(aLI_text)

            acLI_text = cell_data.get('cli_avg', '0').replace('%', '')
            if not acLI_text:
                acLI_text = '0'
            acLI = float(acLI_text)

            WPA_text = cell_data.get('wpa_bat', '0')
            if not WPA_text:
                WPA_text = '0'
            WPA = float(WPA_text)

            RE24_text = cell_data.get('re24_bat', '0')
            if not RE24_text:
                RE24_text = '0'
            RE24 = float(RE24_text)

            DFS_DK_text = cell_data.get('draftkings_points', '0')
            if not DFS_DK_text:
                DFS_DK_text = '0'
            DFS_DK = float(DFS_DK_text)

            DFS_FD_text = cell_data.get('fanduel_points', '0')
            if not DFS_FD_text:
                DFS_FD_text = '0'
            DFS_FD = float(DFS_FD_text)

            # Update aggregate totals
            aggregate['WPA'] += WPA
            aggregate['cWPA'] += cWPA
            aggregate['RE24'] += RE24
            aggregate['DFS_DK'] += DFS_DK
            aggregate['DFS_FD'] += DFS_FD

            # Collect lists for mode and averaging calculations
            aLI_list.append(aLI)
            acLI_list.append(acLI)
            
            # Get batting order position with fallback
            bop_text = cell_data.get('batting_order_position', '0')
            if not bop_text:
                bop_text = '0'
                
            try:
                bop = int(bop_text)
            except ValueError:
                # Try to extract the first digit if the string contains non-digits
                bop_digits = ''.join(c for c in bop_text if c.isdigit())
                bop = int(bop_digits[0]) if bop_digits else 0
                
            BOP_list.append(bop)

            # Check home or away for last 7 rows
            if cell_data.get('team_homeORaway', '') == '@':
                opp_ID = cell_data.get('opp_ID', '')
                if opp_ID:
                    away_opp_ids_last7.append(opp_ID)
                else:
                    # Try to find opponent ID from the cells
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        if text in ['ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 'COL', 'DET', 
                                   'HOU', 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'OAK', 
                                   'PHI', 'PIT', 'SDP', 'SEA', 'SFG', 'STL', 'TBR', 'TEX', 'TOR', 'WSN']:
                            away_opp_ids_last7.append(text)
                            break
            else:
                home_counter_last7 += 1

        except ValueError as e:
            print(f"Error parsing value in row: {e}")

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

    # Aggregate stats
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

    # Extract the last row (season totals)
    season_totals = rows[-1]
    season_totals_data = [cell.get_text(strip=True) for cell in season_totals.find_all('td')]

    # Extract the second-to-last row for SingleGame payload
    single_game_row = rows[-2]  # Second-to-last row
    single_game_data = [cell.get_text(strip=True) for cell in single_game_row.find_all('td')]

    single_game_data2 = None
    if single_game_data and len(single_game_data) > 2 and '(' in single_game_data[2]:
        single_game_row2 = rows[-3]  # third-to-last row as there was a double header
        single_game_data2 = [cell.get_text(strip=True) for cell in single_game_row2.find_all('td')]
    
    # Extract data from index 8 to len(season_totals_data) - 2
    subset_season_totals = season_totals_data[8:-1]

    # Extract the last row (season totals)
    season_totals_data = []
    
    if season_totals:
        # Try with data-stat attribute first
        cells = season_totals.find_all(['td', 'th'])
        if cells:
            season_totals_data = [cell.get_text(strip=True) for cell in cells]
            
        # If we got cells but they don't have the stats we need, retry with more targeted extraction
        if len(season_totals_data) < 10:  # Not enough data
            # Season totals are often in a row with a "Totals" label or special class
            season_rows = table.find_all('tr', class_=lambda c: c and ('total' in c.lower() or 'sum' in c.lower()))
            
            if season_rows:
                season_totals = season_rows[0]
                cells = season_totals.find_all(['td', 'th'])
                season_totals_data = [cell.get_text(strip=True) for cell in cells]
            else:
                # Look for any row with "Totals" text in the first few cells
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if cells and any('total' in cell.get_text(strip=True).lower() for cell in cells[:3]):
                        season_totals_data = [cell.get_text(strip=True) for cell in cells]
                        break
    
    # If still empty, create a dummy season totals
    if not season_totals_data or len(season_totals_data) < 10:
        print(f"Could not find proper season totals row, creating estimated totals")
        # Calculate season totals from the aggregate data
        season_totals_data = [""] * 8  # Empty cells for non-stat columns
        
        # Add the key stats in order
        season_totals_data.extend([
            str(aggregate['PA']), str(aggregate['AB']), str(aggregate['R']), 
            str(aggregate['H']), str(aggregate['2B']), str(aggregate['3B']), 
            str(aggregate['HR']), str(aggregate['RBI']), str(aggregate['BB']), 
            str(aggregate['IBB']), str(aggregate['SO']), str(aggregate['HBP']), 
            str(aggregate['SH']), str(aggregate['SF']), str(aggregate['ROE']), 
            str(aggregate['GDP']), str(aggregate['SB']), str(aggregate['CS']),
            str(round(aggregate['H'] / aggregate['AB'], 3)) if aggregate['AB'] > 0 else "0.000",
            str(round((aggregate['H'] + aggregate['BB'] + aggregate['HBP']) / 
                (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']), 3)) 
                if (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) > 0 else "0.000",
            str(round((aggregate['H'] + 2*aggregate['2B'] + 3*aggregate['3B'] + 4*aggregate['HR']) / 
                aggregate['AB'], 3)) if aggregate['AB'] > 0 else "0.000",
            # Add more calculated fields for OPS, etc.
        ])

    # Extract the second-to-last row for SingleGame payload
    single_game_row = rows[-2] if len(rows) >= 2 else None
    
    single_game_data = []
    if single_game_row:
        cells = single_game_row.find_all(['td', 'th'])
        single_game_data = [cell.get_text(strip=True) for cell in cells]
    
    # If single_game_data is too short, try to pad it
    if len(single_game_data) < 38:
        # Pad with empty strings to ensure we have enough elements
        single_game_data.extend([''] * (38 - len(single_game_data)))

    single_game_data2 = None
    
    # Check for doubleheader by looking for "(1)" or "(2)" in the date field
    if single_game_data and len(single_game_data) > 2:
        date_field = single_game_data[2]
        if '(' in date_field and len(rows) >= 3:
            single_game_row2 = rows[-3]
            cells = single_game_row2.find_all(['td', 'th'])
            single_game_data2 = [cell.get_text(strip=True) for cell in cells]
            
            # Pad second game data if needed
            if len(single_game_data2) < 38:
                single_game_data2.extend([''] * (38 - len(single_game_data2)))
    
    # Extract data from season_totals_data for stats (normally from index 8 onward)
    subset_season_totals = []
    
    # If season_totals_data has enough elements, extract the subset
    if len(season_totals_data) >= 10:
        start_idx = min(8, len(season_totals_data) - 1)
        end_idx = len(season_totals_data) - 1
        subset_season_totals = season_totals_data[start_idx:end_idx]
    
    # If we couldn't get a proper subset, create an estimate
    if not subset_season_totals or len(subset_season_totals) < 15:
        print(f"Creating estimated season totals subset from aggregate data")
        
        # Create estimated season totals from aggregate data
        ba = aggregate['H'] / aggregate['AB'] if aggregate['AB'] > 0 else 0.0
        obp = (aggregate['H'] + aggregate['BB'] + aggregate['HBP']) / (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) if (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) > 0 else 0.0
        slg = (aggregate['H'] + (2 * aggregate['2B']) + (3 * aggregate['3B']) + (4 * aggregate['HR'])) / aggregate['AB'] if aggregate['AB'] > 0 else 0.0
        ops = obp + slg
        
        subset_season_totals = [
            str(aggregate['PA']), str(aggregate['AB']), str(aggregate['R']), 
            str(aggregate['H']), str(aggregate['2B']), str(aggregate['3B']), 
            str(aggregate['HR']), str(aggregate['RBI']), str(aggregate['BB']), 
            str(aggregate['IBB']), str(aggregate['SO']), str(aggregate['HBP']), 
            str(aggregate['SH']), str(aggregate['SF']), str(aggregate['ROE']), 
            str(aggregate['GDP']), str(aggregate['SB']), str(aggregate['CS']),
            str(round(ba, 3)), str(round(obp, 3)), str(round(slg, 3)), str(round(ops, 3)),
            str(BOP_list[0] if BOP_list else 0),  # Use first BOP as estimate
            str(round(sum(aLI_list) / len(aLI_list), 2)) if aLI_list else "0.00",
            str(round(aggregate['WPA'], 3)),
            str(round(sum(acLI_list) / len(acLI_list), 2)) if acLI_list else "0.00",
            str(round(aggregate['cWPA'] * 100, 2)) + "%",
            str(round(aggregate['RE24'], 2)),
            str(round(aggregate['DFS_DK'], 1)),
            str(round(aggregate['DFS_FD'], 1))
        ]

    return single_game_data, single_game_data2, homeTeam, subset_season_totals, aggregated_data, away_opp_ids, home_counter, home_counter_last7, away_opp_ids_last7

    return single_game_data, single_game_data2, homeTeam, subset_season_totals, aggregated_data, away_opp_ids, home_counter, home_counter_last7, away_opp_ids_last7

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
    Process and post trailing gamelogs using the cloudscraper session
    """
    # Scrape data
    try:
        result = scrape_last_8_games_with_opponents(scraper, bbrefid, year)
        if not result:
            print(f"Failed to scrape data for {bbrefid}")
            return False
            
        single_game_data, single_game_data2, homeTeam, subset_season_totals, aggregated_data, away_opp_ids, home_counter, home_counter_last7, away_opp_ids_last7 = result
    except Exception as e:
        print(f"Error processing data for {bbrefid}: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return False

    # If we have no data in away_opp_ids or home_counter is 0, something went wrong
    if not away_opp_ids and home_counter <= 1:
        print(f"No valid game data found for {bbrefid}")
        return False

    # Handle case where single_game_data might not have enough elements
    if not single_game_data or len(single_game_data) < 6:
        print(f"Invalid single game data for {bbrefid}")
        return False

    # Prepare payloads for normalization API
    try:
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
        
        # Get opponent ID from single_game_data - handle different possible formats
        opp_id = None
        if len(single_game_data) > 6:
            opp_id = single_game_data[5]
        else:
            # Try to find team abbreviations in the data
            team_abbrs = ['ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 'COL', 'DET', 
                         'HOU', 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'OAK', 
                         'PHI', 'PIT', 'SDP', 'SEA', 'SFG', 'STL', 'TBR', 'TEX', 'TOR', 'WSN']
            
            for cell in single_game_data:
                if cell in team_abbrs:
                    opp_id = cell
                    break
        
        if not opp_id:
            print(f"Could not determine opponent ID for {bbrefid}, using placeholder")
            opp_id = "NYY"  # Placeholder
            
        # Determine if home game based on team_homeORaway field
        is_home = True
        if len(single_game_data) > 5:
            is_home = single_game_data[4] != '@'
        
        payload3 = {
            "bbrefId": bbrefid,
            "oppIds": [opp_id],
            "homeGames": 1 if is_home else 0
        }
        
        if debug:
            print(f"Payloads for {bbrefid}:")
            print(f"Full season: {payload}")
            print(f"Last 7 games: {payload2}")
            print(f"Single game: {payload3}")
    except Exception as e:
        print(f"Error preparing payloads for {bbrefid}: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return False

    # Normalize ParkFactors API endpoint
    normalize_api_url = f"{API_BASE_URL}/ParkFactors/normalize"
    trailing_gamelog_api_url = f"{API_BASE_URL}/TrailingGameLogSplits"

    # Process API calls with better error handling
    try:
        # Full season normalization
        response = api_session.post(normalize_api_url, json=payload, verify=False)
        response.raise_for_status()
        api_response = response.json()
        
        # Last 7 games normalization
        response2 = api_session.post(normalize_api_url, json=payload2, verify=False)
        response2.raise_for_status()
        api_response2 = response2.json()
        
        # Single game normalization
        response3 = api_session.post(normalize_api_url, json=payload3, verify=False)
        response3.raise_for_status()
        api_response3 = response3.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while calling normalize API for {bbrefid}: {e}")
        return False
    except ValueError as e:
        print(f"Invalid JSON response from normalize API for {bbrefid}: {e}")
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

    json_payloadTOT = {
        "bbrefId": bbrefid,
        "team": homeTeam,
        "split": "Season",
        "splitParkFactor": api_response["totalParkFactor"],
        "g": len(away_opp_ids) + home_counter - 1,
        "pa": subset_season_totals[0],
        "ab": subset_season_totals[1],
        "r": subset_season_totals[2],
        "h": subset_season_totals[3],
        "doubles": subset_season_totals[4],
        "triples": subset_season_totals[5],
        "hr": subset_season_totals[6],
        "rbi": subset_season_totals[7],
        "bb": subset_season_totals[8],
        "ibb": subset_season_totals[9],
        "so": subset_season_totals[10],
        "hbp": subset_season_totals[11],
        "sh": subset_season_totals[12],
        "sf": subset_season_totals[13],
        "roe": subset_season_totals[14],
        "gdp": subset_season_totals[15],
        "sb": subset_season_totals[16],
        "cs": subset_season_totals[17],
        "ba": subset_season_totals[18],
        "obp": subset_season_totals[19],
        "slg": subset_season_totals[20],
        "ops": subset_season_totals[21],
        "bop": subset_season_totals[22] if subset_season_totals[22] else -1,  # Set to -1 if null or empty
        "ali": subset_season_totals[23],
        "wpa": subset_season_totals[24],
        "acLI": subset_season_totals[25],
        "cwpa": subset_season_totals[26],
        "rE24": subset_season_totals[27],
        "dfsDk": subset_season_totals[28],
        "dfsFd": subset_season_totals[29],
        "homeGames": home_counter - 1,
        "awayGames": len(away_opp_ids),
        "homeParkFactor": api_response["homeParkFactor"],
        "awayParkFactorAvg": api_response["avgAwayParkFactor"],
        "dateUpdated": date.today().isoformat()
    }

    converted_date = convert_date(single_game_data[2])

    json_payloadSG = {
        "bbrefId": bbrefid,
        "team": homeTeam,
        "split": "SingleGame",
        "splitParkFactor": api_response3["totalParkFactor"],
        "g": 1,
        "pa": single_game_data[8],
        "ab": single_game_data[9],
        "r": single_game_data[10],
        "h": single_game_data[11],
        "doubles": single_game_data[12],
        "triples": single_game_data[13],
        "hr": single_game_data[14],
        "rbi": single_game_data[15],
        "bb": single_game_data[16],
        "ibb": single_game_data[17] if single_game_data[17] else 0,
        "so": single_game_data[18],
        "hbp": single_game_data[19],
        "sh": single_game_data[20],
        "sf": single_game_data[21] if single_game_data and single_game_data[21] else 0,
        "roe": single_game_data[22],
        "gdp": single_game_data[23] if single_game_data and single_game_data[23] else 0,
        "sb": single_game_data[24],
        "cs": single_game_data[25],
        "ba": single_game_data[26],
        "obp": single_game_data[27],
        "slg": single_game_data[28],
        "ops": single_game_data[29],
        "bop": single_game_data[30] if single_game_data[30] else -1,  # Set to -1 if null or empty
        "ali": single_game_data[31] if single_game_data[31] else 0.0,
        "wpa": single_game_data[32] if single_game_data[32] else 0.0,
        "acLI": single_game_data[33] if single_game_data[33] else 0.0,
        "cwpa": str(single_game_data[34]) if single_game_data and single_game_data[34].strip() else "0%",
        "rE24": single_game_data[35] if single_game_data[35] else 0.0,
        "dfsDk": single_game_data[36],
        "dfsFd": single_game_data[37],
        "homeGames": 1 if single_game_data[4] == '' else 0,
        "awayGames": 1 if single_game_data[4] == '@' else 0,
        "homeParkFactor": api_response3["homeParkFactor"],
        "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
        "dateUpdated": converted_date
    }

    if single_game_data2 is not None:
        json_payloadSG2 = {
            "bbrefId": bbrefid,
            "team": homeTeam,
            "split": "SingleGame2",
            "splitParkFactor": api_response3["totalParkFactor"],
            "g": 1,
            "pa": single_game_data2[8],
            "ab": single_game_data2[9],
            "r": single_game_data2[10],
            "h": single_game_data2[11],
            "doubles": single_game_data2[12],
            "triples": single_game_data2[13],
            "hr": single_game_data2[14],
            "rbi": single_game_data2[15],
            "bb": single_game_data2[16],
            "ibb": single_game_data2[17] if single_game_data2[17] else 0,
            "so": single_game_data2[18],
            "hbp": single_game_data2[19],
            "sh": single_game_data2[20],
            "sf": single_game_data2[21] if single_game_data2 and single_game_data2[21] else 0,
            "roe": single_game_data2[22],
            "gdp": single_game_data2[23] if single_game_data2 and single_game_data2[23] else 0,
            "sb": single_game_data2[24],
            "cs": single_game_data2[25],
            "ba": single_game_data2[26],
            "obp": single_game_data2[27],
            "slg": single_game_data2[28],
            "ops": single_game_data2[29],
            "bop": single_game_data2[30] if single_game_data2 and single_game_data2[30] else -1,
            "ali": single_game_data2[31] if single_game_data2 and single_game_data2[31] else 0.0,
            "wpa": single_game_data2[32] if single_game_data2 and single_game_data2[32] else 0.0,
            "acLI": single_game_data2[33] if single_game_data2 and single_game_data2[33] else 0.0,
            "cwpa": str(single_game_data2[34]) if single_game_data2 and single_game_data2[34].strip() else "0%",
            "rE24": single_game_data2[35] if single_game_data2 and single_game_data2[35] else 0.0,
            "dfsDk": single_game_data2[36],
            "dfsFd": single_game_data2[37],
            "homeGames": 1 if single_game_data2[4] == '' else 0,
            "awayGames": 1 if single_game_data2[4] == '@' else 0,
            "homeParkFactor": api_response3["homeParkFactor"],
            "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
            "dateUpdated": converted_date
        }

    # Post data to TrailingGameLogSplits API
    success = True
    
    try:
        responseL7 = api_session.post(trailing_gamelog_api_url, json=json_payloadL7, verify=False)
        responseL7.raise_for_status()
        print(f"Successfully posted Last7G data for {bbrefid}: {responseL7.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting Last7G data for {bbrefid}: {e}")
        success = False

    try:
        responseTOT = api_session.post(trailing_gamelog_api_url, json=json_payloadTOT, verify=False)
        responseTOT.raise_for_status()
        print(f"Successfully posted Season data for {bbrefid}: {responseTOT.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting Season data for {bbrefid}: {e}")
        success = False

    try:
        responseSG = api_session.post(trailing_gamelog_api_url, json=json_payloadSG, verify=False)
        responseSG.raise_for_status()
        print(f"Successfully posted SingleGame data for {bbrefid}: {responseSG.status_code}")
        
        if single_game_data2 is not None:
            responseSG2 = api_session.post(trailing_gamelog_api_url, json=json_payloadSG2, verify=False)
            responseSG2.raise_for_status()
            print(f"Successfully posted SingleGame2 data for {bbrefid}: {responseSG2.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting SingleGame data for {bbrefid}: {e}")
        success = False
        
    return success

def main():
    parser = argparse.ArgumentParser(description='Scrape Baseball Reference and post data to API')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format', default=date.today().isoformat())
    parser.add_argument('--file', type=str, help='Path to file with bbrefids (optional)')
    parser.add_argument('--year', type=int, help='Year to scrape data for', default=date.today().year)
    parser.add_argument('--delay', type=float, help='Delay between requests in seconds', default=3.5)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with additional output')
    parser.add_argument('--retry', type=int, help='Number of retry attempts for failed requests', default=2)
    parser.add_argument('--max-players', type=int, help='Maximum number of players to process', default=None)
    args = parser.parse_args()

    # Create API session
    api_session = requests.Session()
    
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
            with open(args.file, "r", encoding="utf-8") as infile:
                bbrefids = [line.strip() for line in infile if line.strip()]  # Remove empty lines

            print(f"Found {len(bbrefids)} bbrefids in file")
        else:
            # Get today's hitters from API
            print(f"Getting today's hitters for {args.date}...")
            hitters = get_todays_hitters(api_session, args.date)
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
                    if isinstance(hitters['hitters'][0], dict) and 'bbrefId' in hitters['hitters'][0]:
                        bbrefids = [hitter['bbrefId'] for hitter in hitters['hitters']]
                elif 'data' in hitters and isinstance(hitters['data'], list):
                    if len(hitters['data']) > 0:
                        if isinstance(hitters['data'][0], str):
                            bbrefids = hitters['data']
                        elif isinstance(hitters['data'][0], dict) and 'bbrefId' in hitters['data'][0]:
                            bbrefids = [item['bbrefId'] for item in hitters['data'] if 'bbrefId' in item]
                
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
        
        for i, bbrefid in enumerate(bbrefids):
            print(f"Processing {i+1}/{len(bbrefids)}: {bbrefid}")
            
            # Add variable delay to avoid detection
            delay = args.delay + random.uniform(0.5, 2.0)
            
            # Try multiple times if needed
            for attempt in range(args.retry + 1):
                if attempt > 0:
                    print(f"Retry attempt {attempt}/{args.retry} for {bbrefid}")
                    # Increase delay for retry attempts
                    delay = delay * 1.5
                    time.sleep(delay)
                
                if process_and_post_trailing_gamelogs(scraper, api_session, bbrefid, args.year, args.debug):
                    successful += 1
                    break
                elif attempt == args.retry:  # Last attempt failed
                    failed += 1
                
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

        print(f"Processing complete. Successful: {successful}, Failed: {failed}")
    except FileNotFoundError:
        print(f"Error: The file {args.file} was not found. Please ensure it exists.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Main block
if __name__ == "__main__":
    main()