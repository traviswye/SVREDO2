import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
import os
import urllib3
from typing import List, Dict, Any

# Disable SSL warnings to avoid certificate verification issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_player_projections(first_name: str, last_name: str) -> pd.DataFrame:
    """
    Scrapes a player's projections from FantasyPros.
    
    Args:
        first_name: Player's first name
        last_name: Player's last name
        
    Returns:
        DataFrame containing the player's projection data or None if not found
    """
    """
    Scrapes a player's projections from FantasyPros.
    
    Args:
        first_name: Player's first name
        last_name: Player's last name
        
    Returns:
        DataFrame containing the player's projection data
    """
    url = f"https://www.fantasypros.com/mlb/projections/{first_name.lower()}-{last_name.lower()}.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    }
    
    # Add delay to avoid rate limiting
    time.sleep(1)
    
    try:
        # Set verify to False to bypass SSL certificate verification
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the table with "Season (2025)" caption
        season_table = soup.find('table', class_='table table-bordered')
        
        # Alternative lookup method - search for caption with Season (2025)
        if not season_table:
            caption = soup.find('caption', string=lambda text: text and 'Season' in text and '2025' in text)
            if caption:
                season_table = caption.parent
                
        if not season_table:
            print(f"Could not find 2025 projections table for {first_name} {last_name}")
            return None
        
        if not season_table:
            print(f"Could not find projection table for {first_name} {last_name}")
            return None
            
        # Parse the table into a DataFrame
        data = []
        headers = []
        
        # Get headers
        header_row = season_table.find('thead').find('tr')
        for th in header_row.find_all('th'):
            headers.append(th.text.strip())
            
        # Get data rows
        tbody = season_table.find('tbody')
        for row in tbody.find_all('tr'):
            row_data = []
            for td in row.find_all('td'):
                row_data.append(td.text.strip())
            
            # Create a dictionary with source and values
            row_dict = {}
            for i, value in enumerate(row_data):
                if i < len(headers):
                    row_dict[headers[i]] = value
                    
            data.append(row_dict)
            
        return pd.DataFrame(data)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {first_name} {last_name}: {e}")
        return None
    except Exception as e:
        print(f"Error processing data for {first_name} {last_name}: {e}")
        return None

def process_projections(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Process the projections data to calculate statistics.
    
    Args:
        df: DataFrame containing the player's projections
        
    Returns:
        Dictionary with averaged and calculated statistics
    """
    if df is None or df.empty:
        return None
        
    # Convert numeric columns to proper types
    numeric_cols = ['PA', 'AB', 'R', 'HR', 'RBI', 'SB', 'H', '2B', '3B', 'BB', 'SO']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate averages for numeric columns
    averages = {}
    for col in numeric_cols:
        if col in df.columns:
            averages[col] = round(df[col].mean())
    
    # Calculate AVG, OBP, SLG, and OPS
    if 'H' in averages and 'AB' in averages and averages['AB'] > 0:
        averages['AVG'] = round(averages['H'] / averages['AB'], 3)
    else:
        averages['AVG'] = 0.0
        
    if 'H' in averages and 'BB' in averages and 'PA' in averages and averages['PA'] > 0:
        # Simple OBP calculation (H + BB) / PA - doesn't account for HBP and SF
        averages['OBP'] = round((averages['H'] + averages['BB']) / averages['PA'], 3)
    else:
        averages['OBP'] = 0.0
        
    if 'H' in averages and '2B' in averages and '3B' in averages and 'HR' in averages and 'AB' in averages and averages['AB'] > 0:
        # SLG = (1B + 2*2B + 3*3B + 4*HR) / AB
        singles = averages['H'] - averages['2B'] - averages['3B'] - averages['HR']
        total_bases = singles + (2 * averages['2B']) + (3 * averages['3B']) + (4 * averages['HR'])
        averages['SLG'] = round(total_bases / averages['AB'], 3)
    else:
        averages['SLG'] = 0.0
        
    # OPS = OBP + SLG
    averages['OPS'] = round(averages['OBP'] + averages['SLG'], 3)
    
    return averages

def create_payload(player_name: str, stats: Dict[str, Any], year: int = 2025, proj_type: str = 'AggProj') -> Dict[str, Any]:
    """
    Creates a payload with the player's projection data.
    
    Args:
        player_name: Full name of the player
        stats: Dictionary with the player's statistics
        year: Projection year
        proj_type: Type of projection
        
    Returns:
        Dictionary with the complete payload
    """
    if stats is None:
        return None
        
    payload = {
        "name": player_name,
        "year": year,
        "type": proj_type,
        "stats": stats
    }
    
    return payload

def process_player_list(player_list: List[str]) -> List[Dict[str, Any]]:
    """
    Process a list of players and get their projections.
    
    Args:
        player_list: List of player names in "FirstName LastName" format
        
    Returns:
        List of payloads with player projections
    """
    results = []
    
    for player in player_list:
        parts = player.strip().split(' ', 1)
        if len(parts) < 2:
            print(f"Invalid player name format: {player}. Use 'FirstName LastName'")
            continue
            
        first_name, last_name = parts
        print(f"Processing {first_name} {last_name}...")
        
        df = scrape_player_projections(first_name, last_name)
        if df is not None:
            stats = process_projections(df)
            if stats is not None:
                payload = create_payload(player, stats)
                results.append(payload)
    
    return results

def save_results(results: List[Dict[str, Any]], filename: str = "player_projections.json"):
    """
    Save the results to a JSON file.
    
    Args:
        results: List of player projection payloads
        filename: Name of the output file
    """
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filename}")

# Example usage
if __name__ == "__main__":
    # List of players to process
    players = [
        "Patrick Bailey",
        "Pete Alonso",
        "Jose Altuve",
        # Add more players as needed
    ]
    
    results = process_player_list(players)
    save_results(results)
    
    print(f"Processed {len(results)} player projections successfully.")