# Import required libraries if not already imported
import re
import random
import time
import json
import statistics
from datetime import date
from bs4 import BeautifulSoup
import cloudscraper
import requests
import urllib3
import traceback
import argparse

# Suppress HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
def extract_row_data(row):
    """
    Extract all relevant data from a table row with accurate mapping.
    
    Args:
        row: BeautifulSoup row object
        
    Returns:
        Tuple containing:
        - data: List of all cell texts
        - stats_dict: Dictionary mapping specific stats to their values
    """
    # Extract all text from cells
    data = []
    for cell in row.find_all(['td', 'th']):
        data.append(cell.get_text(strip=True))
    
    # Create a dictionary to store all stats with proper mapping
    stats_dict = {}
    
    # Extract by data-stat attribute for accuracy
    for cell in row.find_all(['td', 'th']):
        data_stat = cell.get('data-stat')
        if data_stat:
            stats_dict[data_stat] = cell.get_text(strip=True)
    
    # Extract specific key stats for convenient access
    extracted_stats = {
        # Basic stats
        'pa': stats_dict.get('b_pa', '0'),
        'ab': stats_dict.get('b_ab', '0'),
        'r': stats_dict.get('b_r', '0'),
        'h': stats_dict.get('b_h', '0'),
        '2b': stats_dict.get('b_doubles', '0'),
        '3b': stats_dict.get('b_triples', '0'),
        'hr': stats_dict.get('b_hr', '0'),
        'rbi': stats_dict.get('b_rbi', '0'),
        'bb': stats_dict.get('b_bb', '0'),
        'so': stats_dict.get('b_so', '0'),
        
        # Additional stats
        'sb': stats_dict.get('b_sb', '0'),
        'cs': stats_dict.get('b_cs', '0'),
        'hbp': stats_dict.get('b_hbp', '0'),
        'sh': stats_dict.get('b_sh', '0'),
        'sf': stats_dict.get('b_sf', '0'),
        'ibb': stats_dict.get('b_ibb', '0'),
        'gdp': stats_dict.get('b_gidp', '0'),
        
        # Batting stats
        'ba': stats_dict.get('b_batting_avg_cume', '0.000'),
        'obp': stats_dict.get('b_onbase_perc_cume', '0.000'),
        'slg': stats_dict.get('b_slugging_perc_cume', '0.000'),
        'ops': stats_dict.get('b_onbase_plus_slugging_cume', '0.000'),
        
        # Advanced metrics
        'ali': stats_dict.get('b_leverage_index_avg', '0.0'),
        'wpa': stats_dict.get('b_wpa', '0.0'),
        'acli': stats_dict.get('b_cli_avg', '0.0'),
        'cwpa': stats_dict.get('b_cwpa', '0.0%'),
        're24': stats_dict.get('b_baseout_runs', '0.0'),
        
        # DFS stats
        'dfs_dk': stats_dict.get('b_draftkings_points', '0.0'),
        'dfs_fd': stats_dict.get('b_fanduel_points', '0.0'),
        
        # Other
        'bop': stats_dict.get('b_lineup_position', '0'),
        'date': stats_dict.get('date', ''),
        'team': stats_dict.get('team_name_abbr', ''),
        'opp': stats_dict.get('opp_name_abbr', ''),
        'is_away': stats_dict.get('game_location', '') == '@'
    }
    
    return data, extracted_stats
    
def scrape_player_data(scraper, bbrefid, year):
    """
    Scrape a player's game log data from Baseball Reference with improved data extraction
    
    Args:
        scraper: The cloudscraper session
        bbrefid: The player's Baseball Reference ID
        year: The year to scrape
        
    Returns:
        A tuple containing various player data elements
    """
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
        
        if not table_div:
            print(f"Game log table not found for player {bbrefid} in year {year}")
            return None

        # Extract the actual table from the div
        table = table_div.find('table')
        if not table:
            print(f"Table element not found within the game log div for player {bbrefid} in year {year}")
            return None

        # Get tbody and tfoot sections
        tbody = table.find('tbody')
        tfoot = table.find('tfoot')
        
        if not tbody or not tfoot:
            print(f"Could not find tbody or tfoot for player {bbrefid}")
            return None
            
        # Get all individual game rows from tbody
        game_rows = tbody.find_all('tr')
        
        # Get the season total row from tfoot
        season_total_row = tfoot.find('tr')
        
        if not game_rows or not season_total_row:
            print(f"Could not find game rows or season total row for player {bbrefid}")
            return None
            
        print(f"Found {len(game_rows)} game rows for player {bbrefid}")
        
        # Get the most recent game (last row in tbody)
        most_recent_game = game_rows[-1] if game_rows else None
        
        # Check if the second-to-last game was part of a doubleheader
        second_game = None
        if len(game_rows) >= 2:
            # Check date columns to see if they're the same date (indicating doubleheader)
            recent_date = most_recent_game.find('td', {'data-stat': 'date'}).get_text(strip=True) if most_recent_game else ""
            prev_date = game_rows[-2].find('td', {'data-stat': 'date'}).get_text(strip=True)
            
            if recent_date and recent_date == prev_date:
                second_game = game_rows[-2]
        
        # Get the last 7 games (or all if less than 7)
        last_7_games = game_rows[-7:] if len(game_rows) >= 7 else game_rows
        
        # Extract the home team from the most recent game
        home_team_elem = most_recent_game.find('td', {'data-stat': 'team_name_abbr'}) if most_recent_game else None
        homeTeam = home_team_elem.get_text(strip=True) if home_team_elem else "UNKNOWN"
        
        # Extract data from the rows using the new, more accurate function
        single_game_data, single_game_stats = extract_row_data(most_recent_game) if most_recent_game else ([], {})
        
        if second_game:
            single_game_data2, single_game_stats2 = extract_row_data(second_game)
        else:
            single_game_data2, single_game_stats2 = None, {}
            
        season_totals_data, season_stats = extract_row_data(season_total_row)
        
        # Track home and away games
        away_opp_ids = []
        home_counter = 0
        away_opp_ids_last7 = []
        home_counter_last7 = 0
        
        # Process all game rows to count home/away games
        for row in game_rows:
            # Check for home/away indicator
            game_location = row.find('td', {'data-stat': 'game_location'})
            is_away = game_location and game_location.get_text(strip=True) == '@'
            
            # Get opponent
            opp_elem = row.find('td', {'data-stat': 'opp_name_abbr'})
            opp_id = opp_elem.get_text(strip=True) if opp_elem else "UNKNOWN"
            
            if is_away:
                away_opp_ids.append(opp_id)
            else:
                home_counter += 1
        
        # Process last 7 games to count home/away games
        for row in last_7_games:
            # Check for home/away indicator
            game_location = row.find('td', {'data-stat': 'game_location'})
            is_away = game_location and game_location.get_text(strip=True) == '@'
            
            # Get opponent
            opp_elem = row.find('td', {'data-stat': 'opp_name_abbr'})
            opp_id = opp_elem.get_text(strip=True) if opp_elem else "UNKNOWN"
            
            if is_away:
                away_opp_ids_last7.append(opp_id)
            else:
                home_counter_last7 += 1
                
        # Aggregate stats from the last 7 games
        aggregated_data = aggregate_stats_from_rows(last_7_games)
        
        print(f"Successfully scraped data for {bbrefid}")
        print(f"Away opponents: {away_opp_ids}")
        print(f"Home games: {home_counter}")
        print(f"Last 7 away opponents: {away_opp_ids_last7}")
        print(f"Last 7 home games: {home_counter_last7}")
        
        # Return the data with the new extracted stats dictionaries
        return (
            single_game_data,
            single_game_data2,
            homeTeam,
            season_totals_data,
            aggregated_data,
            away_opp_ids,
            home_counter,
            home_counter_last7,
            away_opp_ids_last7,
            last_7_games,
            game_rows,
            season_total_row,
            single_game_stats,
            single_game_stats2,
            season_stats
        )
    
    except Exception as e:
        print(f"Error scraping data for player {bbrefid}: {e}")
        import traceback
        traceback.print_exc()
        return None

def aggregate_stats_from_rows(rows):
    """
    Aggregate statistics from a list of game rows
    
    Args:
        rows: List of BeautifulSoup tr elements representing games
        
    Returns:
        Dictionary of aggregated statistics
    """
    # Initialize aggregate stats
    aggregate = {
        'G': len(rows),
        'PA': 0, 'AB': 0, 'R': 0, 'H': 0, '2B': 0, '3B': 0, 'HR': 0, 'RBI': 0,
        'BB': 0, 'IBB': 0, 'SO': 0, 'HBP': 0, 'SH': 0, 'SF': 0, 'ROE': 0,
        'GDP': 0, 'SB': 0, 'CS': 0, 'WPA': 0, 'cWPA': 0, 'RE24': 0,
        'DFS_DK': 0, 'DFS_FD': 0
    }
    
    # For calculating mode and averages
    BOP_list = []
    aLI_list = []
    acLI_list = []
    
    # Map data-stat attributes to keys in our aggregate dict
    stat_mapping = {
        'b_pa': 'PA',
        'b_ab': 'AB',
        'b_r': 'R',
        'b_h': 'H',
        'b_doubles': '2B',
        'b_triples': '3B',
        'b_hr': 'HR',
        'b_rbi': 'RBI',
        'b_bb': 'BB',
        'b_ibb': 'IBB',
        'b_so': 'SO',
        'b_hbp': 'HBP',
        'b_sh': 'SH',
        'b_sf': 'SF',
        'b_roe': 'ROE',
        'b_gidp': 'GDP',
        'b_sb': 'SB',
        'b_cs': 'CS'
    }
    
    # Advanced stat mappings
    adv_stat_mapping = {
        'b_wpa': 'WPA',
        'b_cwpa': 'cWPA',
        'b_baseout_runs': 'RE24',
        'b_draftkings_points': 'DFS_DK',
        'b_fanduel_points': 'DFS_FD',
        'b_leverage_index_avg': 'aLI',
        'b_cli_avg': 'acLI',
        'b_lineup_position': 'BOP'
    }
    
    # Process each row
    for row in rows:
        # For each stat in our mapping, find the corresponding cell and add its value
        for data_stat, agg_key in stat_mapping.items():
            cell = row.find('td', {'data-stat': data_stat})
            if cell:
                value = cell.get_text(strip=True)
                try:
                    aggregate[agg_key] += int(value or 0)
                except (ValueError, TypeError):
                    # Skip if we can't convert to int
                    pass
        
        # Process advanced stats
        for data_stat, agg_key in adv_stat_mapping.items():
            cell = row.find('td', {'data-stat': data_stat})
            if cell:
                value = cell.get_text(strip=True)
                
                # Handle BOP separately (collect for mode calculation)
                if agg_key == 'BOP':
                    try:
                        bop_val = int(value or 0)
                        if bop_val > 0:
                            BOP_list.append(bop_val)
                    except (ValueError, TypeError):
                        pass
                # Handle aLI and acLI separately (collect for averaging)
                elif agg_key in ['aLI', 'acLI']:
                    try:
                        if value and value != agg_key:  # Skip header values
                            float_val = float(value.replace('%', '') or 0)
                            if agg_key == 'aLI':
                                aLI_list.append(float_val)
                            else:
                                acLI_list.append(float_val)
                    except (ValueError, TypeError):
                        pass
                # Handle percentages in cWPA
                elif agg_key == 'cWPA':
                    try:
                        if value and value != 'cWPA':  # Skip header values
                            float_val = float(value.replace('%', '') or 0) / 100  # Convert to decimal
                            aggregate[agg_key] += float_val
                    except (ValueError, TypeError):
                        pass
                # Handle other numeric stats
                elif agg_key in ['WPA', 'RE24', 'DFS_DK', 'DFS_FD']:
                    try:
                        if value and value != agg_key:  # Skip header values
                            float_val = float(value or 0)
                            aggregate[agg_key] += float_val
                    except (ValueError, TypeError):
                        pass
    
    # Calculate derived statistics
    if aggregate['AB'] > 0:
        aggregate['BA'] = round(aggregate['H'] / aggregate['AB'], 3)
        
        # Total bases for SLG calculation
        tb = aggregate['H'] + aggregate['2B'] + (2 * aggregate['3B']) + (3 * aggregate['HR'])
        aggregate['SLG'] = round(tb / aggregate['AB'], 3)
    else:
        aggregate['BA'] = 0.0
        aggregate['SLG'] = 0.0
    
    # Calculate OBP
    pa_for_obp = aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']
    if pa_for_obp > 0:
        aggregate['OBP'] = round((aggregate['H'] + aggregate['BB'] + aggregate['HBP']) / pa_for_obp, 3)
    else:
        aggregate['OBP'] = 0.0
    
    # Calculate OPS
    aggregate['OPS'] = round(aggregate['OBP'] + aggregate['SLG'], 3)
    
    # Calculate most common BOP
    try:
        aggregate['BOP'] = statistics.mode(BOP_list) if BOP_list else 0
    except statistics.StatisticsError:
        aggregate['BOP'] = max(BOP_list, key=BOP_list.count) if BOP_list else 0
    
    # Calculate average aLI and acLI
    aggregate['aLI'] = round(sum(aLI_list) / len(aLI_list), 3) if aLI_list else 0.0
    aggregate['acLI'] = round(sum(acLI_list) / len(acLI_list), 3) if acLI_list else 0.0
    
    # Format cWPA as a percentage string
    aggregate['cWPA'] = f"{round(aggregate['cWPA'] * 100, 2)}%"
    
    return aggregate

def create_single_game_payload(bbrefid, homeTeam, single_game_data, park_factor_response, is_away_game, single_game_stats=None):
    """
    Create a payload for a single game with accurate data extraction and correct BA/OBP/SLG/OPS calculation
    
    Args:
        bbrefid: Baseball Reference ID
        homeTeam: Player's home team
        single_game_data: Data extracted from the single game row (legacy)
        park_factor_response: Response from the park factor normalization API
        is_away_game: Boolean indicating if this was an away game
        single_game_stats: Dictionary of extracted stats (new approach)
        
    Returns:
        Dictionary with the payload for the API
    """
    # Use the new stats dictionary if available, otherwise fall back to old method
    if single_game_stats:
        # Initialize game stats by extracting from stats dictionary
        sg_pa = safe_convert(single_game_stats.get('pa', '0'), int, 0)
        sg_ab = safe_convert(single_game_stats.get('ab', '0'), int, 0)
        sg_r = safe_convert(single_game_stats.get('r', '0'), int, 0)
        sg_h = safe_convert(single_game_stats.get('h', '0'), int, 0)
        sg_doubles = safe_convert(single_game_stats.get('2b', '0'), int, 0)
        sg_triples = safe_convert(single_game_stats.get('3b', '0'), int, 0)
        sg_hr = safe_convert(single_game_stats.get('hr', '0'), int, 0)
        sg_rbi = safe_convert(single_game_stats.get('rbi', '0'), int, 0)
        sg_sb = safe_convert(single_game_stats.get('sb', '0'), int, 0)
        sg_cs = safe_convert(single_game_stats.get('cs', '0'), int, 0)
        sg_bb = safe_convert(single_game_stats.get('bb', '0'), int, 0)
        sg_so = safe_convert(single_game_stats.get('so', '0'), int, 0)
        
        # Additional stats
        sg_hbp = safe_convert(single_game_stats.get('hbp', '0'), int, 0)
        sg_sh = safe_convert(single_game_stats.get('sh', '0'), int, 0)
        sg_sf = safe_convert(single_game_stats.get('sf', '0'), int, 0)
        sg_ibb = safe_convert(single_game_stats.get('ibb', '0'), int, 0)
        sg_gdp = safe_convert(single_game_stats.get('gdp', '0'), int, 0)
        sg_roe = 0  # ROE might not be directly available
        
        # Advanced metrics - properly captured now
        sg_ali = safe_convert(single_game_stats.get('ali', '0.0'), float, 0.0)
        sg_wpa = safe_convert(single_game_stats.get('wpa', '0.0'), float, 0.0)
        sg_acli = safe_convert(single_game_stats.get('acli', '0.0'), float, 0.0)
        sg_cwpa = single_game_stats.get('cwpa', '0.0%')  # Keep as string with %
        sg_re24 = safe_convert(single_game_stats.get('re24', '0.0'), float, 0.0)
        
        # DFS points
        sg_dfs_dk = safe_convert(single_game_stats.get('dfs_dk', '0.0'), float, 0.0)
        sg_dfs_fd = safe_convert(single_game_stats.get('dfs_fd', '0.0'), float, 0.0)
        
        # Batting Order Position
        sg_bop = safe_convert(single_game_stats.get('bop', '0'), int, 0)
        
        # Get the date
        game_date = single_game_stats.get('date', '')
        converted_date = convert_date(game_date)
        if not converted_date:
            converted_date = date.today().isoformat()
    else:
        # Legacy extraction method as fallback (should not be needed)
        # Helper function to safely extract values
        def safe_get(data, index, default=0):
            try:
                if index < len(data) and data[index]:
                    return data[index]
                return default
            except IndexError:
                return default
        
        # Initialize game stats from the array (legacy approach)
        sg_pa = safe_convert(safe_get(single_game_data, 9), int, 0)
        sg_ab = safe_convert(safe_get(single_game_data, 10), int, 0)
        sg_r = safe_convert(safe_get(single_game_data, 11), int, 0)
        sg_h = safe_convert(safe_get(single_game_data, 12), int, 0)
        sg_doubles = safe_convert(safe_get(single_game_data, 13), int, 0)
        sg_triples = safe_convert(safe_get(single_game_data, 14), int, 0)
        sg_hr = safe_convert(safe_get(single_game_data, 15), int, 0)
        sg_rbi = safe_convert(safe_get(single_game_data, 16), int, 0)
        sg_sb = safe_convert(safe_get(single_game_data, 17), int, 0)
        sg_cs = safe_convert(safe_get(single_game_data, 18), int, 0)
        sg_bb = safe_convert(safe_get(single_game_data, 19), int, 0)
        sg_so = safe_convert(safe_get(single_game_data, 20), int, 0)
        
        # Extract date
        game_date = safe_get(single_game_data, 3, "")
        converted_date = convert_date(game_date)
        if not converted_date:
            converted_date = date.today().isoformat()
        
        # Additional stats
        sg_hbp = safe_convert(safe_get(single_game_data, 28), int, 0)
        sg_sh = safe_convert(safe_get(single_game_data, 29), int, 0)
        sg_sf = safe_convert(safe_get(single_game_data, 30), int, 0)
        sg_ibb = safe_convert(safe_get(single_game_data, 31), int, 0)
        sg_gdp = safe_convert(safe_get(single_game_data, 27), int, 0)
        sg_roe = 0  # ROE might not be directly available
        
        # Likely wrong indices - we'll default to zeros
        sg_ali = 0.0
        sg_wpa = 0.0
        sg_acli = 0.0
        sg_cwpa = "0.0%"
        sg_re24 = 0.0
        sg_dfs_dk = 0.0
        sg_dfs_fd = 0.0
        sg_bop = 0
    
    # IMPORTANT: Calculate batting average stats for this specific game
    # rather than using the extracted values (which might be season totals)
    if sg_ab > 0:
        sg_ba = round(sg_h / sg_ab, 3)
        
        # Total bases calculation
        tb = sg_h + sg_doubles + (2 * sg_triples) + (3 * sg_hr)
        sg_slg = round(tb / sg_ab, 3)
    else:
        sg_ba = 0.0
        sg_slg = 0.0
        
    # OBP calculation for this specific game
    obp_denominator = sg_ab + sg_bb + sg_hbp + sg_sf
    if obp_denominator > 0:
        sg_obp = round((sg_h + sg_bb + sg_hbp) / obp_denominator, 3)
    else:
        sg_obp = 0.0
        
    # OPS calculation for this specific game
    sg_ops = round(sg_obp + sg_slg, 3)
    
    # Determine home/away counts
    sg_homegames = 0 if is_away_game else 1
    sg_awaygames = 1 if is_away_game else 0
    
    # For home games, use the home park factor directly
    if sg_homegames == 1:
        split_park_factor = park_factor_response["homeParkFactor"]
    else:
        # For away games, use the opponent park factor or average if not available
        split_park_factor = safe_convert(park_factor_response["avgAwayParkFactor"], float, 100.0)
    
    # Create the payload
    return {
        "bbrefId": bbrefid,
        "team": homeTeam,
        "split": "SingleGame",
        "splitParkFactor": split_park_factor,
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
        "ba": sg_ba,
        "obp": sg_obp,
        "slg": sg_slg,
        "ops": sg_ops,
        "bop": sg_bop,
        "ali": round(sg_ali, 3),
        "wpa": round(sg_wpa, 3),
        "acLI": round(sg_acli, 3),
        "cwpa": sg_cwpa,
        "rE24": round(sg_re24, 2),
        "dfsDk": round(sg_dfs_dk, 1),
        "dfsFd": round(sg_dfs_fd, 1),
        "homeGames": sg_homegames,
        "awayGames": sg_awaygames,
        "homeParkFactor": park_factor_response["homeParkFactor"],
        "awayParkFactorAvg": park_factor_response["avgAwayParkFactor"],
        "dateUpdated": converted_date
    }

def create_single_game_payload(bbrefid, homeTeam, single_game_data, park_factor_response, is_away_game, single_game_stats=None):
    """
    Create a payload for a single game with accurate data extraction
    
    Args:
        bbrefid: Baseball Reference ID
        homeTeam: Player's home team
        single_game_data: Data extracted from the single game row (legacy)
        park_factor_response: Response from the park factor normalization API
        is_away_game: Boolean indicating if this was an away game
        single_game_stats: Dictionary of extracted stats (new approach)
        
    Returns:
        Dictionary with the payload for the API
    """
    # Use the new stats dictionary if available, otherwise fall back to old method
    if single_game_stats:
        # Initialize game stats by extracting from stats dictionary
        sg_pa = safe_convert(single_game_stats.get('pa', '0'), int, 0)
        sg_ab = safe_convert(single_game_stats.get('ab', '0'), int, 0)
        sg_r = safe_convert(single_game_stats.get('r', '0'), int, 0)
        sg_h = safe_convert(single_game_stats.get('h', '0'), int, 0)
        sg_doubles = safe_convert(single_game_stats.get('2b', '0'), int, 0)
        sg_triples = safe_convert(single_game_stats.get('3b', '0'), int, 0)
        sg_hr = safe_convert(single_game_stats.get('hr', '0'), int, 0)
        sg_rbi = safe_convert(single_game_stats.get('rbi', '0'), int, 0)
        sg_sb = safe_convert(single_game_stats.get('sb', '0'), int, 0)
        sg_cs = safe_convert(single_game_stats.get('cs', '0'), int, 0)
        sg_bb = safe_convert(single_game_stats.get('bb', '0'), int, 0)
        sg_so = safe_convert(single_game_stats.get('so', '0'), int, 0)
        
        # Additional stats
        sg_hbp = safe_convert(single_game_stats.get('hbp', '0'), int, 0)
        sg_sh = safe_convert(single_game_stats.get('sh', '0'), int, 0)
        sg_sf = safe_convert(single_game_stats.get('sf', '0'), int, 0)
        sg_ibb = safe_convert(single_game_stats.get('ibb', '0'), int, 0)
        sg_gdp = safe_convert(single_game_stats.get('gdp', '0'), int, 0)
        sg_roe = 0  # ROE might not be directly available
        
        # Advanced metrics - properly captured now
        sg_ba = safe_convert(single_game_stats.get('ba', '0.000'), float, 0.0)
        sg_obp = safe_convert(single_game_stats.get('obp', '0.000'), float, 0.0)
        sg_slg = safe_convert(single_game_stats.get('slg', '0.000'), float, 0.0)
        sg_ops = safe_convert(single_game_stats.get('ops', '0.000'), float, 0.0)
        
        sg_ali = safe_convert(single_game_stats.get('ali', '0.0'), float, 0.0)
        sg_wpa = safe_convert(single_game_stats.get('wpa', '0.0'), float, 0.0)
        sg_acli = safe_convert(single_game_stats.get('acli', '0.0'), float, 0.0)
        sg_cwpa = single_game_stats.get('cwpa', '0.0%')  # Keep as string with %
        sg_re24 = safe_convert(single_game_stats.get('re24', '0.0'), float, 0.0)
        
        # DFS points
        sg_dfs_dk = safe_convert(single_game_stats.get('dfs_dk', '0.0'), float, 0.0)
        sg_dfs_fd = safe_convert(single_game_stats.get('dfs_fd', '0.0'), float, 0.0)
        
        # Batting Order Position
        sg_bop = safe_convert(single_game_stats.get('bop', '0'), int, 0)
        
        # Get the date
        game_date = single_game_stats.get('date', '')
        converted_date = convert_date(game_date)
        if not converted_date:
            converted_date = date.today().isoformat()
    else:
        # Legacy extraction method as fallback (should not be needed)
        # Helper function to safely extract values
        def safe_get(data, index, default=0):
            try:
                if index < len(data) and data[index]:
                    return data[index]
                return default
            except IndexError:
                return default
        
        # Initialize game stats from the array (legacy approach)
        sg_pa = safe_convert(safe_get(single_game_data, 9), int, 0)
        sg_ab = safe_convert(safe_get(single_game_data, 10), int, 0)
        sg_r = safe_convert(safe_get(single_game_data, 11), int, 0)
        sg_h = safe_convert(safe_get(single_game_data, 12), int, 0)
        sg_doubles = safe_convert(safe_get(single_game_data, 13), int, 0)
        sg_triples = safe_convert(safe_get(single_game_data, 14), int, 0)
        sg_hr = safe_convert(safe_get(single_game_data, 15), int, 0)
        sg_rbi = safe_convert(safe_get(single_game_data, 16), int, 0)
        sg_sb = safe_convert(safe_get(single_game_data, 17), int, 0)
        sg_cs = safe_convert(safe_get(single_game_data, 18), int, 0)
        sg_bb = safe_convert(safe_get(single_game_data, 19), int, 0)
        sg_so = safe_convert(safe_get(single_game_data, 20), int, 0)
        
        # Extract date
        game_date = safe_get(single_game_data, 3, "")
        converted_date = convert_date(game_date)
        if not converted_date:
            converted_date = date.today().isoformat()
        
        # Calculate batting stats
        sg_ba, sg_obp, sg_slg, sg_ops = calculate_batting_stats(
            sg_h, sg_ab, sg_bb, 0, 0, sg_doubles, sg_triples, sg_hr
        )
        
        # Additional stats
        sg_hbp = safe_convert(safe_get(single_game_data, 28), int, 0)
        sg_sh = safe_convert(safe_get(single_game_data, 29), int, 0)
        sg_sf = safe_convert(safe_get(single_game_data, 30), int, 0)
        sg_ibb = safe_convert(safe_get(single_game_data, 31), int, 0)
        sg_gdp = safe_convert(safe_get(single_game_data, 27), int, 0)
        sg_roe = 0  # ROE might not be directly available
        
        # Likely wrong indices - we'll default to zeros
        sg_ali = 0.0
        sg_wpa = 0.0
        sg_acli = 0.0
        sg_cwpa = "0.0%"
        sg_re24 = 0.0
        sg_dfs_dk = 0.0
        sg_dfs_fd = 0.0
        sg_bop = 0
    
    # Determine home/away counts
    sg_homegames = 0 if is_away_game else 1
    sg_awaygames = 1 if is_away_game else 0
    
    # For home games, use the home park factor directly
    if sg_homegames == 1:
        split_park_factor = park_factor_response["homeParkFactor"]
    else:
        # For away games, use the opponent park factor or average if not available
        split_park_factor = safe_convert(park_factor_response["avgAwayParkFactor"], float, 100.0)
    
    # Create the payload
    return {
        "bbrefId": bbrefid,
        "team": homeTeam,
        "split": "SingleGame",
        "splitParkFactor": split_park_factor,
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
        "bop": sg_bop,
        "ali": round(sg_ali, 3),
        "wpa": round(sg_wpa, 3),
        "acLI": round(sg_acli, 3),
        "cwpa": sg_cwpa,
        "rE24": round(sg_re24, 2),
        "dfsDk": round(sg_dfs_dk, 1),
        "dfsFd": round(sg_dfs_fd, 1),
        "homeGames": sg_homegames,
        "awayGames": sg_awaygames,
        "homeParkFactor": park_factor_response["homeParkFactor"],
        "awayParkFactorAvg": park_factor_response["avgAwayParkFactor"],
        "dateUpdated": converted_date
    }

def create_season_payload(bbrefid, homeTeam, season_totals_data, park_factor_response, home_games, away_games, season_stats=None):
    """
    Create a payload for the season totals with accurate data extraction
    
    Args:
        bbrefid: Baseball Reference ID
        homeTeam: Player's home team
        season_totals_data: Data extracted from the season totals row (legacy)
        park_factor_response: Response from the park factor normalization API
        home_games: Number of home games
        away_games: Number of away games
        season_stats: Dictionary of extracted stats (new approach)
        
    Returns:
        Dictionary with the payload for the API
    """
    # Get game count
    games = home_games + away_games
    
    # Use the new stats dictionary if available
    if season_stats:
        # Core stats - extracted directly from data-stat attributes
        season_pa = safe_convert(season_stats.get('pa', '0'), int, 0)
        season_ab = safe_convert(season_stats.get('ab', '0'), int, 0)
        season_r = safe_convert(season_stats.get('r', '0'), int, 0)
        season_h = safe_convert(season_stats.get('h', '0'), int, 0)
        season_2b = safe_convert(season_stats.get('2b', '0'), int, 0)
        season_3b = safe_convert(season_stats.get('3b', '0'), int, 0)
        season_hr = safe_convert(season_stats.get('hr', '0'), int, 0)
        season_rbi = safe_convert(season_stats.get('rbi', '0'), int, 0)
        season_sb = safe_convert(season_stats.get('sb', '0'), int, 0)
        season_cs = safe_convert(season_stats.get('cs', '0'), int, 0)
        season_bb = safe_convert(season_stats.get('bb', '0'), int, 0)
        season_so = safe_convert(season_stats.get('so', '0'), int, 0)
        
        # Additional stats - directly from data-stat attributes
        season_ba = safe_convert(season_stats.get('ba', '0.000'), float, 0.0)
        season_obp = safe_convert(season_stats.get('obp', '0.000'), float, 0.0)
        season_slg = safe_convert(season_stats.get('slg', '0.000'), float, 0.0)
        season_ops = safe_convert(season_stats.get('ops', '0.000'), float, 0.0)
        
        # More advanced stats
        season_gdp = safe_convert(season_stats.get('gdp', '0'), int, 0)
        season_hbp = safe_convert(season_stats.get('hbp', '0'), int, 0)
        season_sh = safe_convert(season_stats.get('sh', '0'), int, 0)
        season_sf = safe_convert(season_stats.get('sf', '0'), int, 0)
        season_ibb = safe_convert(season_stats.get('ibb', '0'), int, 0)
        season_roe = 0  # ROE might not be directly available
        
        # Advanced metrics - accurately extracted by attribute
        season_ali = safe_convert(season_stats.get('ali', '0.0'), float, 0.0)
        season_wpa = safe_convert(season_stats.get('wpa', '0.0'), float, 0.0)
        season_acli = safe_convert(season_stats.get('acli', '0.0'), float, 0.0)
        season_cwpa = season_stats.get('cwpa', '0.0%')  # Keep as string with %
        season_re24 = safe_convert(season_stats.get('re24', '0.0'), float, 0.0)
        
        # DFS points
        season_dfs_dk = safe_convert(season_stats.get('dfs_dk', '0.0'), float, 0.0)
        season_dfs_fd = safe_convert(season_stats.get('dfs_fd', '0.0'), float, 0.0)
        
        # BOP
        season_bop = safe_convert(season_stats.get('bop', '0'), int, 0)
    else:
        # Legacy extraction method (fallback - should not be needed)
        def safe_get(data, index, default=0):
            try:
                if index < len(data) and data[index]:
                    return data[index]
                return default
            except IndexError:
                return default
        
        # Core stats - using the array indices (legacy approach)
        season_pa = safe_convert(safe_get(season_totals_data, 9), int, 0)
        season_ab = safe_convert(safe_get(season_totals_data, 10), int, 0)
        season_r = safe_convert(safe_get(season_totals_data, 11), int, 0)
        season_h = safe_convert(safe_get(season_totals_data, 12), int, 0)
        season_2b = safe_convert(safe_get(season_totals_data, 13), int, 0)
        season_3b = safe_convert(safe_get(season_totals_data, 14), int, 0)
        season_hr = safe_convert(safe_get(season_totals_data, 15), int, 0)
        season_rbi = safe_convert(safe_get(season_totals_data, 16), int, 0)
        season_sb = safe_convert(safe_get(season_totals_data, 17), int, 0)
        season_cs = safe_convert(safe_get(season_totals_data, 18), int, 0)
        season_bb = safe_convert(safe_get(season_totals_data, 19), int, 0)
        season_so = safe_convert(safe_get(season_totals_data, 20), int, 0)
        
        # Additional stats - these indices are likely wrong
        # Just recalculate from the core stats
        if season_ab > 0:
            season_ba = round(season_h / season_ab, 3)
            season_slg = round((season_h + season_2b + 2*season_3b + 3*season_hr) / season_ab, 3)
        else:
            season_ba = 0.0
            season_slg = 0.0
            
        if (season_ab + season_bb) > 0:
            season_obp = round((season_h + season_bb) / (season_ab + season_bb), 3)
        else:
            season_obp = 0.0
            
        season_ops = round(season_obp + season_slg, 3)
        
        # These will likely be wrong from indices, so just set to 0
        season_gdp = 0
        season_hbp = 0
        season_sh = 0
        season_sf = 0
        season_ibb = 0
        season_roe = 0
        
        # Advanced metrics - likely wrong indices so default to 0
        season_ali = 0.0
        season_wpa = 0.0
        season_acli = 0.0
        season_cwpa = "0.0%"
        season_re24 = 0.0
        
        # DFS
        season_dfs_dk = 0.0
        season_dfs_fd = 0.0
        
        # BOP
        season_bop = 0
    
    # Create the payload
    return {
        "bbrefId": bbrefid,
        "team": homeTeam,
        "split": "Season",
        "splitParkFactor": park_factor_response["totalParkFactor"],
        "g": games,
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
        "bop": season_bop,
        "ali": round(season_ali, 3),
        "wpa": round(season_wpa, 3),
        "acLI": round(season_acli, 3),
        "cwpa": season_cwpa,
        "rE24": round(season_re24, 2),
        "dfsDk": round(season_dfs_dk, 1),
        "dfsFd": round(season_dfs_fd, 1),
        "homeGames": home_games,
        "awayGames": away_games,
        "homeParkFactor": park_factor_response["homeParkFactor"],
        "awayParkFactorAvg": park_factor_response["avgAwayParkFactor"],
        "dateUpdated": date.today().isoformat()
    }

def create_last7g_payload(bbrefid, homeTeam, aggregated_data, park_factor_response, home_games_last7, away_games_last7):
    """
    Create a payload for the last 7 games
    
    Args:
        bbrefid: Baseball Reference ID
        homeTeam: Player's home team
        aggregated_data: Data aggregated from last 7 games (or all if less than 7)
        park_factor_response: Response from the park factor normalization API
        home_games_last7: Number of home games in last 7
        away_games_last7: Number of away games in last 7
        
    Returns:
        Dictionary with the payload for the API
    """    
    # Create the payload
    return {
        "bbrefId": bbrefid,
        "team": homeTeam,
        "split": "Last7G",
        "splitParkFactor": park_factor_response["totalParkFactor"],
        "g": aggregated_data["G"],
        "pa": aggregated_data.get("PA", 0),
        "ab": aggregated_data.get("AB", 0),
        "r": aggregated_data.get("R", 0),
        "h": aggregated_data.get("H", 0),
        "doubles": aggregated_data.get("2B", 0),
        "triples": aggregated_data.get("3B", 0),
        "hr": aggregated_data.get("HR", 0),
        "rbi": aggregated_data.get("RBI", 0),
        "bb": aggregated_data.get("BB", 0),
        "ibb": aggregated_data.get("IBB", 0),
        "so": aggregated_data.get("SO", 0),
        "hbp": aggregated_data.get("HBP", 0),
        "sh": aggregated_data.get("SH", 0),
        "sf": aggregated_data.get("SF", 0),
        "roe": aggregated_data.get("ROE", 0),
        "gdp": aggregated_data.get("GDP", 0),
        "sb": aggregated_data.get("SB", 0),
        "cs": aggregated_data.get("CS", 0),
        "ba": aggregated_data.get("BA", 0.0),
        "obp": aggregated_data.get("OBP", 0.0),
        "slg": aggregated_data.get("SLG", 0.0),
        "ops": aggregated_data.get("OPS", 0.0),
        "bop": aggregated_data.get("BOP", 0),
        "ali": aggregated_data.get("aLI", 0.0),
        "wpa": aggregated_data.get("WPA", 0.0),
        "acLI": aggregated_data.get("acLI", 0.0),
        "cwpa": aggregated_data.get("cWPA", "0%"),
        "rE24": aggregated_data.get("RE24", 0.0),
        "dfsDk": aggregated_data.get("DFS_DK", 0.0),
        "dfsFd": aggregated_data.get("DFS_FD", 0.0),
        "homeGames": home_games_last7,
        "awayGames": away_games_last7,
        "homeParkFactor": park_factor_response["homeParkFactor"],
        "awayParkFactorAvg": park_factor_response["avgAwayParkFactor"],
        "dateUpdated": date.today().isoformat()
    }

def process_and_post_trailing_gamelogs(scraper, api_session, bbrefid, year):
    """
    Process a player's game log data and post it to the API using the improved data extraction
    
    Args:
        scraper: CloudScraper session for web scraping
        api_session: Requests session for API calls
        bbrefid: The player's Baseball Reference ID
        year: The year to scrape
        
    Returns:
        Boolean indicating success/failure
    """
    # Add delay before starting processing
    delay = random.uniform(1, 3)
    print(f"Starting to process player {bbrefid}. Waiting {delay:.2f} seconds first...")
    time.sleep(delay)
    
    try:
        # Scrape data using our improved function
        result = scrape_player_data(scraper, bbrefid, year)
        
        if result is None:
            print(f"Failed to scrape data for {bbrefid}. Skipping...")
            return False
            
        # Unpack the return values
        (
            single_game_data, 
            single_game_data2, 
            homeTeam, 
            season_totals_data, 
            aggregated_data, 
            away_opp_ids, 
            home_counter, 
            home_counter_last7, 
            away_opp_ids_last7, 
            last_7_games, 
            all_games, 
            season_totals,
            single_game_stats,
            single_game_stats2,
            season_stats
        ) = result
        
        # Count total games
        total_games = len(all_games)
        
        # Determine if the single game is home or away
        is_single_game_away = single_game_stats.get('is_away', False) if single_game_stats else False
        if not is_single_game_away and not single_game_stats:
            # Fallback to old method of detection
            for i, value in enumerate(single_game_data):
                if value == '@':
                    is_single_game_away = True
                    break
        
        # Prepare payloads for normalization API
        # For the entire season
        payload_season = {
            "bbrefId": bbrefid,
            "oppIds": away_opp_ids,
            "homeGames": home_counter
        }
        
        # For the last 7 games
        payload_last7 = {
            "bbrefId": bbrefid,
            "oppIds": away_opp_ids_last7,
            "homeGames": home_counter_last7
        }
        
        # For the most recent single game
        # Find the correct opponent ID
        opp_ID = single_game_stats.get('opp', '') if single_game_stats else None
        if not opp_ID:
            # Fallback methods for finding opponent
            if is_single_game_away and away_opp_ids:
                opp_ID = away_opp_ids[0]  # Most recent away opponent
            else:
                # Try to extract from single_game_data
                # First try dedicated opponent cell
                for i, val in enumerate(single_game_data):
                    # Look for team abbreviations - typically 2-3 uppercase letters
                    if val and len(val) in [2, 3, 4] and val.isupper() and val != '@' and val != homeTeam:
                        # Skip values that are positions
                        if val not in ['RF', 'CF', 'LF', '1B', '2B', '3B', 'SS', 'C', 'P', 'DH', 'PH']:
                            opp_ID = val
                            break
        
        # Fallback
        if not opp_ID:
            print(f"Could not determine opponent ID for {bbrefid}. Using default.")
            opp_ID = "OPP"
            
        payload_single = {
            "bbrefId": bbrefid,
            "oppIds": [opp_ID],
            "homeGames": 0 if is_single_game_away else 1
        }
        
        print(f"Created payload for single game: {payload_single}")

        # Normalize ParkFactors API endpoint
        normalize_api_url = "https://localhost:44346/api/ParkFactors/normalize"
        trailing_gamelog_api_url = "https://localhost:44346/api/TrailingGameLogSplits"

        # Add small delay before API call
        time.sleep(random.uniform(0.5, 1.5))
        
        # Make API calls with error handling
        try:
            # Season normalization
            response_season = api_session.post(normalize_api_url, json=payload_season, verify=False)
            response_season.raise_for_status()
            api_response_season = response_season.json()
            
            # Last 7 games normalization
            time.sleep(random.uniform(0.5, 1))
            response_last7 = api_session.post(normalize_api_url, json=payload_last7, verify=False)
            response_last7.raise_for_status()
            api_response_last7 = response_last7.json()
            
            # Single game normalization
            time.sleep(random.uniform(0.5, 1))
            response_single = api_session.post(normalize_api_url, json=payload_single, verify=False)
            response_single.raise_for_status()
            api_response_single = response_single.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling normalize API: {e}")
            print(f"Payload that caused error: {payload_season}")
            return False

        # Create the payloads for the TrailingGameLogSplits API
        json_payload_last7 = create_last7g_payload(
            bbrefid, 
            homeTeam, 
            aggregated_data, 
            api_response_last7, 
            home_counter_last7, 
            len(away_opp_ids_last7)
        )
        
        json_payload_season = create_season_payload(
            bbrefid, 
            homeTeam, 
            season_totals_data, 
            api_response_season, 
            home_counter, 
            len(away_opp_ids),
            season_stats
        )
        
        json_payload_single = create_single_game_payload(
            bbrefid, 
            homeTeam, 
            single_game_data, 
            api_response_single, 
            is_single_game_away,
            single_game_stats
        )
        
        # Handle doubleheader second game if it exists
        json_payload_single2 = None
        if single_game_data2:
            is_single_game2_away = single_game_stats2.get('is_away', False) if single_game_stats2 else False
            if not is_single_game2_away and not single_game_stats2:
                # Fallback
                for i, value in enumerate(single_game_data2):
                    if value == '@':
                        is_single_game2_away = True
                        break
                    
            # For simplicity, reuse the same normalization response
            json_payload_single2 = create_single_game_payload(
                bbrefid, 
                homeTeam, 
                single_game_data2, 
                api_response_single, 
                is_single_game2_away,
                single_game_stats2
            )
            # Mark as second game of doubleheader
            json_payload_single2["split"] = "SingleGame2"
        
        # Post data to TrailingGameLogSplits API
        # Add small delay between API calls
        time.sleep(random.uniform(0.5, 1.5))
        
        # Post Last7G data
        try:
            response_l7 = api_session.post(trailing_gamelog_api_url, json=json_payload_last7, verify=False)
            response_l7.raise_for_status()
            print(f"Successfully posted Last7G data for {bbrefid}: {response_l7.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting Last7G data for {bbrefid}: {e}")
            print(f"Payload that caused error: {json.dumps(json_payload_last7)}")
            return False

        # Post Season data
        time.sleep(random.uniform(0.5, 1))
        try:
            response_season = api_session.post(trailing_gamelog_api_url, json=json_payload_season, verify=False)
            response_season.raise_for_status()
            print(f"Successfully posted Season data for {bbrefid}: {response_season.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting Season data for {bbrefid}: {e}")
            print(f"Payload that caused error: {json.dumps(json_payload_season)}")
            return False

        # Post SingleGame data
        time.sleep(random.uniform(0.5, 1))
        try:
            response_sg = api_session.post(trailing_gamelog_api_url, json=json_payload_single, verify=False)
            response_sg.raise_for_status()
            print(f"Successfully posted SingleGame data for {bbrefid}: {response_sg.status_code}")
            
            # If doubleheader second game exists, post it too
            if json_payload_single2:
                time.sleep(random.uniform(0.5, 1))
                response_sg2 = api_session.post(trailing_gamelog_api_url, json=json_payload_single2, verify=False)
                response_sg2.raise_for_status()
                print(f"Successfully posted SingleGame2 data for {bbrefid}: {response_sg2.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error posting SingleGame data for {bbrefid}: {e}")
            print(f"Payload that caused error: {json.dumps(json_payload_single)}")
            if json_payload_single2:
                print(f"SingleGame2 payload that caused error: {json.dumps(json_payload_single2)}")
            return False
            
        # If we made it here, all requests succeeded
        return True
        
    except Exception as e:
        print(f"Error processing player {bbrefid}: {e}")
        import traceback
        traceback.print_exc()  # Print detailed stack trace for debugging
        return False

def safe_convert(value, to_type=float, default=0):
    """
    Safely convert a value to the specified type with a default fallback
    
    Args:
        value: The value to convert
        to_type: The type to convert to (int, float, etc.)
        default: The default value to return if conversion fails
        
    Returns:
        The converted value or the default
    """
    if value is None or value == '':
        return default
    try:
        # Remove percentage sign and other non-numeric characters if present
        if isinstance(value, str):
            value = value.replace('%', '').replace(',', '')
        return to_type(value)
    except (ValueError, TypeError):
        return default

def calculate_pa(ab, bb=0, hbp=0, sh=0, sf=0):
    """
    Calculate plate appearances from component stats
    
    Args:
        ab: At bats
        bb: Walks
        hbp: Hit by pitch
        sh: Sacrifice hits
        sf: Sacrifice flies
        
    Returns:
        The calculated plate appearances
    """
    return ab + bb + hbp + sh + sf

def calculate_batting_stats(h, ab, bb=0, hbp=0, sf=0, doubles=0, triples=0, hr=0):
    """
    Calculate batting average, OBP, SLG, and OPS
    
    Args:
        h: Hits
        ab: At bats
        bb: Walks
        hbp: Hit by pitch
        sf: Sacrifice flies
        doubles: Doubles
        triples: Triples
        hr: Home runs
        
    Returns:
        Tuple of (BA, OBP, SLG, OPS)
    """
    # Default values if denominators are zero
    ba, obp, slg, ops = 0.0, 0.0, 0.0, 0.0
    
    if ab > 0:
        ba = h / ab
        
        # Calculate total bases: singles + 2*doubles + 3*triples + 4*hr
        singles = h - doubles - triples - hr
        tb = singles + 2*doubles + 3*triples + 4*hr
        slg = tb / ab
    
    if (ab + bb + hbp + sf) > 0:
        obp = (h + bb + hbp) / (ab + bb + hbp + sf)
    
    ops = obp + slg
    
    return ba, obp, slg, ops

def convert_date(date_string):
    """
    Convert a date string from Baseball Reference format to ISO format
    
    Args:
        date_string: Date string from Baseball Reference
        
    Returns:
        The date in ISO format (yyyy-mm-dd) or None if conversion fails
    """
    # Handle various date formats
    try:
        # If it's already in ISO format, just return it
        if re.match(r'\d{4}-\d{2}-\d{2}', date_string):
            return date_string
            
        # Map month abbreviations to their numeric values
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }
    
        # Remove anything starting from '('
        cleaned_date = date_string.split('(')[0].strip()
        
        # Try to extract components from different formats
        
        # Format 1: MMM DD, YYYY (e.g. "Mar 29, 2025")
        match = re.match(r'(\w{3})\s+(\d{1,2}),?\s+(\d{4})', cleaned_date)
        if match:
            month_abbr, day, year = match.groups()
            month = month_map.get(month_abbr)
            if month:
                # Add leading zero to day if necessary
                day = day.zfill(2)
                return f"{year}-{month}-{day}"
        
        # Format 2: YYYY-MM-DD (already handled above)
        
        # Format 3: MMM DD (e.g. "Mar 29") - we'll add the current year
        match = re.match(r'(\w{3})\s+(\d{1,2})', cleaned_date)
        if match:
            month_abbr, day = match.groups()
            month = month_map.get(month_abbr)
            if month:
                # Add leading zero to day if necessary
                day = day.zfill(2)
                year = date.today().year
                return f"{year}-{month}-{day}"
        
        # If we get here, the format is not recognized
        print(f"Could not parse date: {date_string}")
        return None
        
    except Exception as e:
        print(f"Error parsing date '{date_string}': {e}")
        return None

def simulate_human_browsing(scraper):
    """
    Simulate human browsing behavior to avoid detection
    
    Args:
        scraper: The CloudScraper session
        
    Returns:
        Boolean indicating success/failure
    """
    print("Simulating human browsing pattern...")
    
    # First visit the homepage
    homepage_url = "https://www.baseball-reference.com"
    print(f"Visiting homepage: {homepage_url}")
    try:
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
        visit_count = random.randint(2, 3)
        for _ in range(visit_count):
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
                # Continue to next link even if this one fails
        
        print("Human browsing simulation completed")
        return True
        
    except Exception as e:
        print(f"Error simulating human browsing: {e}")
        return False

def create_scraper_session():
    """
    Create a CloudScraper session with headers to mimic a real browser
    
    Returns:
        A configured CloudScraper session
    """
    # Sample user agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ]
    
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

def create_api_session():
    """
    Create a session for API requests
    
    Returns:
        A configured requests session
    """
    session = requests.Session()
    session.verify = False
    return session

def get_todays_hitters(api_session, date_str):
    """
    Get the list of hitters scheduled for games today
    
    Args:
        api_session: The API session
        date_str: Date string in the format yy-MM-dd
        
    Returns:
        List of Baseball Reference IDs for today's hitters
    """
    url = f"https://localhost:44346/api/Hitters/todaysHitters/{date_str}"
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
    """
    Main function to run the Baseball Reference scraper
    """
    parser = argparse.ArgumentParser(description="Baseball Reference Batter Statistics Scraper")
    parser.add_argument("--date", "-d", help="Date in format yy-MM-dd (e.g., 25-03-29) to scrape players scheduled for games on this date")
    parser.add_argument("--input", "-i", help="Input file containing bbrefids to scrape", default="bbrefids.txt")
    parser.add_argument("--year", "-y", help="Year to scrape data for", type=int, default=2025)
    parser.add_argument("--debug", help="Enable debug mode with extra logging", action="store_true")
    parser.add_argument("--resume", help="Resume from a specific player index", type=int, default=0)
    args = parser.parse_args()

    print("Starting Baseball Reference Batter Statistics Scraper with Enhanced Anti-Detection Measures")
    

    
    year = args.year  # Default or from command line
    debug_mode = args.debug
    resume_index = args.resume
    
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
        # Shuffling the list can make patterns harder to detect
        random.shuffle(bbrefids)
        
        # If resuming from a specific index, slice the list
        if resume_index > 0:
            if resume_index >= len(bbrefids):
                print(f"Error: Resume index {resume_index} is greater than the number of players {len(bbrefids)}")
                return
            print(f"Resuming from player index {resume_index}")
            bbrefids = bbrefids[resume_index:]
        
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
        print(f"An error occurred in the main function: {e}")
        traceback.print_exc()  # Print detailed stack trace for debugging

if __name__ == "__main__":
    main()