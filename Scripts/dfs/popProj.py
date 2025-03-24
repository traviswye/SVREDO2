import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import csv
import time
import urllib3
from typing import List, Dict, Any, Optional

# Disable SSL warnings to avoid certificate verification issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_player_field(player_text):
    """
    Parses the player field to extract name, team, position, and MiLB status
    Example inputs:
    - "Shohei Ohtani (LAD - SP,DH)"
    - "Billy Hamilton (CF,RF,LF) FA"
    - "Coco Montes (TB - 2B) MiLB"
    """
    result = {
        'name': '',
        'team': '',
        'position': '',
        'milb': 'no'
    }
    
    # Check for MiLB designation
    if "MiLB" in player_text:
        result['milb'] = "yes"
        player_text = player_text.replace("MiLB", "").strip()
    
    # Check for FA designation
    fa_designation = False
    if "FA" in player_text.split():
        fa_designation = True
        player_text = player_text.replace("FA", "").strip()
    
    # Parse name and team/position
    match = re.search(r'(.*?)\s*\((.*?)\)', player_text)
    if match:
        # Get player name
        result['name'] = match.group(1).strip()
        
        # Get team and position
        team_pos = match.group(2).strip()
        
        if " - " in team_pos:
            # Format: "LAD - SP,DH"
            parts = team_pos.split(" - ", 1)
            result['team'] = parts[0].strip()
            result['position'] = parts[1].strip()
        else:
            # Format: "CF,RF,LF" (no team specified in parentheses)
            result['position'] = team_pos
            result['team'] = 'FA' if fa_designation else ''
    else:
        # No parentheses, just a name
        result['name'] = player_text.strip()
    
    return result

def scrape_hitter_projections():
    """
    Scrapes the hitter projections from FantasyPros main hitters page
    Returns a DataFrame of all hitter projections
    """
    url = "https://www.fantasypros.com/mlb/projections/hitters.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main data table
        table = soup.find('table', id='data')
        if not table:
            print("Could not find the projections table")
            return None
        
        # Get headers
        headers = []
        header_row = table.find('thead').find('tr')
        for th in header_row.find_all('th'):
            headers.append(th.text.strip())
        
        # Get data rows
        rows = []
        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            row = {}
            
            # Get all cell data first
            cells = tr.find_all('td')
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row[headers[i]] = cell.text.strip()
            
            # Add row to results
            rows.append(row)
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        
        # Debug - print the DataFrame columns
        print(f"DataFrame columns: {list(df.columns)}")
        
        # Debug - print first 5 rows
        if not df.empty:
            print("Sample data (first 5 rows):")
            print(df.head())
        
        return df
    
    except Exception as e:
        print(f"Error scraping hitter projections: {e}")
        return None

def scrape_pitcher_projections():
    """
    Scrapes the pitcher projections from FantasyPros main pitchers page
    Returns a DataFrame of all pitcher projections
    """
    url = "https://www.fantasypros.com/mlb/projections/pitchers.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main data table
        table = soup.find('table', id='data')
        if not table:
            print("Could not find the projections table")
            return None
        
        # Get headers
        headers = []
        header_row = table.find('thead').find('tr')
        for th in header_row.find_all('th'):
            headers.append(th.text.strip())
        
        # Get data rows
        rows = []
        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            row = {}
            
            # Get all cell data
            cells = tr.find_all('td')
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row[headers[i]] = cell.text.strip()
            
            rows.append(row)
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        
        # Debug - print sample data
        if not df.empty:
            print("Sample pitcher data (first 5 rows):")
            print(df.head())
            
        return df
    
    except Exception as e:
        print(f"Error scraping pitcher projections: {e}")
        return None

def get_bbref_id(player_name: str, team: str) -> Optional[str]:
    """
    Tries to get the Baseball Reference ID for a player
    using the MLB Player API endpoint
    """
    # Replace spaces with %20 for the URL
    encoded_name = player_name.replace(' ', '%20')
    api_url = f"https://localhost:44346/api/MLBPlayer/search?fullName={encoded_name}&team={team}"
    
    headers = {
        "accept": "text/plain"
    }
    
    try:
        # Disable SSL verification for local development
        response = requests.get(api_url, headers=headers, verify=False)
        print(f"API response for {player_name} ({team}): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Check if we got a valid response with a bbrefid
            if data and isinstance(data, list) and len(data) > 0 and 'bbrefId' in data[0]:
                bbref_id = data[0]['bbrefId']
                print(f"Found bbrefId: {bbref_id} for {player_name}")
                return bbref_id
            else:
                print(f"No bbrefId found for {player_name} ({team}) in API response: {data}")
        else:
            print(f"API call failed for {player_name} ({team}): {response.status_code}")
        
        return None
    
    except Exception as e:
        print(f"Error fetching bbrefid for {player_name} ({team}): {e}")
        return None

def prepare_hitter_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares a player row for insertion into the projectedHitterStats table
    """
    # Get player name - use 'Player' instead of 'PlayerName'
    player_name = row.get('Player', '')
    
    # Parse player name, team and position from the player field
    player_info = parse_player_field(player_name)
    
    # Debug
    print(f"Processing hitter: {player_info['name']}, team: {player_info['team']}, position: {player_info['position']}")
    
    # Try to get bbrefID
    bbref_id = get_bbref_id(player_info['name'], player_info['team'])
    
    # Create the payload
    payload = {
        "bbrefId": bbref_id or f"{player_info['name'].replace(' ', '').lower()}_{player_info['team']}",
        "year": 2025,
        "name": player_info['name'],
        "team": player_info['team'],
        "position": player_info['position'],
        "milb": player_info['milb']
    }
    
    # Add stats
    # Convert and add numeric stats
    try:
        payload["PA"] = int(row.get('PA', '0'))
    except (ValueError, KeyError):
        payload["PA"] = 0
        
    try:
        payload["AB"] = int(row.get('AB', '0'))
    except (ValueError, KeyError):
        payload["AB"] = 0
    
    try:
        payload["R"] = int(row.get('R', '0'))
    except (ValueError, KeyError):
        payload["R"] = 0
        
    try:
        payload["HR"] = int(row.get('HR', '0'))
    except (ValueError, KeyError):
        payload["HR"] = 0
        
    try:
        payload["RBI"] = int(row.get('RBI', '0'))
    except (ValueError, KeyError):
        payload["RBI"] = 0
        
    try:
        payload["SB"] = int(row.get('SB', '0'))
    except (ValueError, KeyError):
        payload["SB"] = 0
    
    try:
        avg_str = row.get('AVG', '0.000')
        if avg_str.startswith('.'):
            avg_str = '0' + avg_str
        payload["AVG"] = float(avg_str)
    except (ValueError, KeyError):
        payload["AVG"] = 0.0
        
    try:
        avg_str = row.get('OBP', '0.000')
        if avg_str.startswith('.'):
            avg_str = '0' + avg_str
        payload["OBP"] = float(avg_str)
    except (ValueError, KeyError):
        payload["OBP"] = 0.0
    
    try:
        payload["H"] = int(row.get('H', '0'))
    except (ValueError, KeyError):
        payload["H"] = 0
        
    try:
        payload["doubles"] = int(row.get('2B', '0'))
    except (ValueError, KeyError):
        payload["doubles"] = 0
        
    try:
        payload["triples"] = int(row.get('3B', '0'))
    except (ValueError, KeyError):
        payload["triples"] = 0
        
    try:
        payload["BB"] = int(row.get('BB', '0'))
    except (ValueError, KeyError):
        payload["BB"] = 0
        
    try:
        payload["SO"] = int(row.get('SO', '0'))
    except (ValueError, KeyError):
        payload["SO"] = 0
        
    try:
        avg_str = row.get('SLG', '0.000')
        if avg_str.startswith('.'):
            avg_str = '0' + avg_str
        payload["SLG"] = float(avg_str)
        # payload["SLG"] = float(row.get('SLG', '0.000').replace('.', '0.'))
    except (ValueError, KeyError):
        payload["SLG"] = 0.0
        
    try:
        avg_str = row.get('OPS', '0.000')
        if avg_str.startswith('.'):
            avg_str = '0' + avg_str
        payload["OPS"] = float(avg_str)
        # payload["OPS"] = float(row.get('OPS', '0.000').replace('.', '0.'))
    except (ValueError, KeyError):
        payload["OPS"] = 0.0
    
    # Handle ROSTERED - strip percentage sign and convert to integer
    try:
        rost_str = row.get('Rost%', '0%').replace('%', '')
        payload["ROSTERED"] = int(rost_str)
    except (ValueError, KeyError):
        payload["ROSTERED"] = 0
    
    return payload

def prepare_pitcher_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares a player row for insertion into the projectedPitcherStats table
    """
    # Get player name - use 'Player' instead of 'PlayerName'
    player_name = row.get('Player', '')
    
    # Parse player name, team and position from the player field
    player_info = parse_player_field(player_name)
    
    # Debug
    print(f"Processing pitcher: {player_info['name']}, team: {player_info['team']}, position: {player_info['position']}")
    
    # Try to get bbrefID
    bbref_id = get_bbref_id(player_info['name'], player_info['team'])
    
    # Create the payload
    payload = {
        "bbrefId": bbref_id or f"{player_info['name'].replace(' ', '').lower()}_{player_info['team']}",
        "year": 2025,
        "name": player_info['name'],
        "team": player_info['team'],
        "position": player_info['position'],
        "milb": player_info['milb']
    }
    
    # Add stats
    # Convert and add numeric stats
    try:
        payload["IP"] = float(row.get('IP', '0.0'))
    except (ValueError, KeyError):
        payload["IP"] = 0.0
        
    try:
        payload["K"] = int(row.get('K', '0'))
    except (ValueError, KeyError):
        payload["K"] = 0
    
    try:
        payload["W"] = int(row.get('W', '0'))
    except (ValueError, KeyError):
        payload["W"] = 0
        
    try:
        payload["L"] = int(row.get('L', '0'))
    except (ValueError, KeyError):
        payload["L"] = 0
        
    try:
        payload["SV"] = int(row.get('SV', '0'))
    except (ValueError, KeyError):
        payload["SV"] = 0
    
    try:
        payload["ERA"] = float(row.get('ERA', '0.000'))
    except (ValueError, KeyError):
        payload["ERA"] = 0.0
        
    try:
        payload["WHIP"] = float(row.get('WHIP', '0.000'))
    except (ValueError, KeyError):
        payload["WHIP"] = 0.0
    
    try:
        payload["ER"] = int(row.get('ER', '0'))
    except (ValueError, KeyError):
        payload["ER"] = 0
        
    try:
        payload["H"] = int(row.get('H', '0'))
    except (ValueError, KeyError):
        payload["H"] = 0
        
    try:
        payload["BB"] = int(row.get('BB', '0'))
    except (ValueError, KeyError):
        payload["BB"] = 0
        
    try:
        payload["HR"] = int(row.get('HR', '0'))
    except (ValueError, KeyError):
        payload["HR"] = 0
    
    try:
        payload["G"] = int(row.get('G', '0'))
    except (ValueError, KeyError):
        payload["G"] = 0
        
    try:
        payload["GS"] = int(row.get('GS', '0'))
    except (ValueError, KeyError):
        payload["GS"] = 0
        
    try:
        payload["CG"] = int(row.get('CG', '0'))
    except (ValueError, KeyError):
        payload["CG"] = 0
    
    # Handle ROSTERED - strip percentage sign and convert to integer
    try:
        rost_str = row.get('Rost%', '0%').replace('%', '')
        payload["ROSTERED"] = int(rost_str)
    except (ValueError, KeyError):
        payload["ROSTERED"] = 0
    
    return payload

def post_to_api(payload: Dict[str, Any], player_type: str) -> bool:
    """
    Posts the payload to the appropriate API endpoint
    Returns True if successful, False otherwise
    """
    if player_type == 'hitter':
        api_url = "https://localhost:44346/api/ProjectedHitterStats"
    else:
        api_url = "https://localhost:44346/api/ProjectedPitcherStats"
    
    headers = {
        "Content-Type": "application/json",
        "accept": "*/*"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, verify=False)
        
        if response.status_code in [200, 201]:
            print(f"Successfully posted {player_type} {payload['name']}")
            return True
        else:
            print(f"Failed to post {player_type} {payload['name']}: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error posting {player_type} {payload['name']}: {e}")
        return False

def post_batch_to_api(payloads: List[Dict[str, Any]], player_type: str) -> bool:
    """
    Posts a batch of payloads to the appropriate API endpoint
    Returns True if successful, False otherwise
    """
    if player_type == 'hitter':
        api_url = "https://localhost:44346/api/ProjectedHitterStats/batch"
    else:
        api_url = "https://localhost:44346/api/ProjectedPitcherStats/batch"
    
    headers = {
        "Content-Type": "application/json",
        "accept": "*/*"
    }
    
    try:
        # Debug - print the first payload to see its structure
        if payloads and len(payloads) > 0:
            print(f"First {player_type} payload example:")
            print(json.dumps(payloads[0], indent=2))
        
        # Check if any payloads are missing required fields
        for i, payload in enumerate(payloads):
            if not payload.get('name'):
                print(f"Warning: Payload at index {i} is missing 'name' field")
                print(f"Payload keys: {list(payload.keys())}")
                print(f"Payload content: {payload}")
        
        response = requests.post(api_url, headers=headers, json=payloads, verify=False)
        
        if response.status_code == 200:
            print(f"Successfully posted batch of {len(payloads)} {player_type}s")
            return True
        else:
            print(f"Failed to post batch of {player_type}s: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error posting batch of {player_type}s: {e}")
        return False

def save_missing_players(missing_players: List[Dict[str, str]], filename: str = "missing_players.csv"):
    """
    Saves a list of players that couldn't be found in the MLB Player API
    """
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['name', 'team']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for player in missing_players:
            writer.writerow(player)

def main(test_mode=False):
    # Scrape hitter projections
    print("Scraping hitter projections...")
    hitters_df = scrape_hitter_projections()
    
    if hitters_df is not None:
        if test_mode:
            # In test mode, only process the first 5 hitters
            print("TEST MODE: Only processing first 5 hitters")
            hitters_df = hitters_df.head(5)
        
        print(f"Found {len(hitters_df)} hitter projections")
        
        # Prepare payloads for each hitter
        hitter_payloads = []
        missing_hitters = []
        
        for _, row in hitters_df.iterrows():
            payload = prepare_hitter_payload(row)
            
            # If bbrefId contains an underscore, it's a generated ID (not found in API)
            if '_' in payload['bbrefId']:
                missing_hitters.append({
                    'name': payload['name'],
                    'team': payload['team']
                })
            
            hitter_payloads.append(payload)
        
        # Save missing hitters to CSV
        if missing_hitters:
            save_missing_players(missing_hitters, "missing_hitters.csv")
            print(f"Saved {len(missing_hitters)} missing hitters to missing_hitters.csv")
        
        # Post hitters in batches (to reduce API calls)
        batch_size = 50
        for i in range(0, len(hitter_payloads), batch_size):
            batch = hitter_payloads[i:i+batch_size]
            post_batch_to_api(batch, 'hitter')
    
    # Scrape pitcher projections
    print("Scraping pitcher projections...")
    pitchers_df = scrape_pitcher_projections()
    
    if pitchers_df is not None:
        if test_mode:
            # In test mode, only process the first 5 pitchers
            print("TEST MODE: Only processing first 5 pitchers")
            pitchers_df = pitchers_df.head(5)
            
        print(f"Found {len(pitchers_df)} pitcher projections")
        
        # Prepare payloads for each pitcher
        pitcher_payloads = []
        missing_pitchers = []
        
        for _, row in pitchers_df.iterrows():
            payload = prepare_pitcher_payload(row)
            
            # If bbrefId contains an underscore, it's a generated ID (not found in API)
            if '_' in payload['bbrefId']:
                missing_pitchers.append({
                    'name': payload['name'],
                    'team': payload['team']
                })
            
            pitcher_payloads.append(payload)
        
        # Save missing pitchers to CSV
        if missing_pitchers:
            save_missing_players(missing_pitchers, "missing_pitchers.csv")
            print(f"Saved {len(missing_pitchers)} missing pitchers to missing_pitchers.csv")
        
        # Post pitchers in batches (to reduce API calls)
        batch_size = 50
        for i in range(0, len(pitcher_payloads), batch_size):
            batch = pitcher_payloads[i:i+batch_size]
            post_batch_to_api(batch, 'pitcher')

if __name__ == "__main__":
    # Set to True to only process the first 5 hitters and pitchers (for testing)
    # Set to False to process all players
    TEST_MODE = True
    # main(test_mode=TEST_MODE)
    main()