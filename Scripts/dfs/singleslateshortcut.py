import requests
import pytz
from datetime import datetime
from pprint import pprint

def fetch_draftables(draftgroup_id):
    url = f"https://api.draftkings.com/draftgroups/v1/draftgroups/{draftgroup_id}/draftables"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching draftables for ID {draftgroup_id}: {e}")
        return None

def get_total_games_from_draftables(draftables_data):
    if not draftables_data or 'draftables' not in draftables_data:
        print("No draftables data found")
        return 0
    
    unique_games = set()
    for player in draftables_data['draftables']:
        game_id = player.get('competition', {}).get('competitionId')
        if game_id:
            unique_games.add(game_id)
            print(f"Found game ID: {game_id}")
    
    total = len(unique_games)
    print(f"Total unique games found: {total}")
    print(f"Unique game IDs: {unique_games}")
    return total

def convert_utc_to_est(utc_time_str):
    # Remove additional zeros if present
    utc_time_str = utc_time_str.replace('.0000000', '')
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    utc_time = pytz.utc.localize(utc_time)
    est_tz = pytz.timezone('US/Eastern')
    est_time = utc_time.astimezone(est_tz)
    return est_time

def process_draftables(draftables_data):
    if not draftables_data or 'draftables' not in draftables_data:
        return []
    
    processed_players = {}
    
    for player in draftables_data['draftables']:
        player_dk_id = player.get('playerDkId')
        
        if player_dk_id in processed_players:
            continue
            
        # For MLB, use attribute ID 408 for FPPG
        dk_ppg = next((attr['value'] for attr in player.get('draftStatAttributes', []) 
                      if attr['id'] == 408), '0')
        
        # For MLB, we'll set OppRank to 0 since it's not used
        opp_rank = '0'
        
        utc_time = player.get('competition', {}).get('startTime', '').replace('.0000000Z', 'Z')
        
        def safe_float(value):
            if not value or value == '-' or value == 'N/A':
                return 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0

        processed_player = {
            'fullName': player.get('displayName', ''),
            'playerDkId': player_dk_id,
            'position': player.get('position', ''),
            'salary': player.get('salary', 0),
            'status': player.get('status', 'None'),  # Ensure status is never null
            'gameId': player.get('competition', {}).get('competitionId', 0),
            'game': player.get('competition', {}).get('name', ''),
            'gameStart': utc_time,
            'team': player.get('teamAbbreviation', ''),
            'dkppg': safe_float(dk_ppg),
            'oppRank': opp_rank  # Set to '0' for MLB
        }
        
        # Print for debugging
        if len(processed_players) < 3:  # Print first 3 players for verification
            print(f"Processed player example: {processed_player}")
        
        processed_players[player_dk_id] = processed_player
    
    return list(processed_players.values())

def post_to_api(draftgroup_id, players):
    url = "https://localhost:44346/api/DKPlayerPools/batch"
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "draftGroupId": draftgroup_id,
        "players": players
    }
    
    # Print the first player for debugging
    print("Example payload player:", payload["players"][0] if players else "No players")
    
    try:
        response = requests.post(url, json=payload, headers=headers, verify=False)
        if response.status_code != 200:
            print(f"Error response: {response.text}")  # Print error details
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting to API for draft group {draftgroup_id}: {e}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        return None

def post_pool_to_map(draftgroup_id, start_time, total_games):
    url = "https://localhost:44346/api/DKPoolsMap/batch"
    headers = {
        'Content-Type': 'application/json'
    }
    
    pool_entry = [{
        "sport": "MLB",
        "draftGroupId": draftgroup_id,
        "date": start_time.strftime('%Y-%m-%d'),
        "startTime": start_time.strftime('%I:%M %p'),
        "gameType": "Classic",
        "totalGames": total_games
    }]
    
    print("\nPosting to DKPoolsMap:")
    print(f"Total games being sent: {total_games}")
    print(f"Full payload: {pool_entry}")
    
    try:
        response = requests.post(url, json=pool_entry, headers=headers, verify=False)
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting to pools map API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response body: {e.response.text}")
        return None

def main():
    # Hardcoded draftgroup ID
    #DRAFTGROUP_ID = 105201
    DRAFTGROUP_ID = 113201
    
    print(f"\nFetching and processing draftable players for DraftGroup {DRAFTGROUP_ID}:")
    
    # Fetch draftables data
    draftables_data = fetch_draftables(DRAFTGROUP_ID)
    if not draftables_data:
        print("Failed to fetch draftables data")
        return
    
    # Calculate total games
    total_games = get_total_games_from_draftables(draftables_data)
    print(f"Total games in draft group: {total_games}")
    
    # Process players
    processed_players = process_draftables(draftables_data)
    if not processed_players:
        print("No players to process")
        return
    
    # Get the earliest game start time for the pool map
    start_times = [convert_utc_to_est(player['gameStart']) 
                  for player in processed_players 
                  if player['gameStart']]
    earliest_start = min(start_times) if start_times else None
    
    if not earliest_start:
        print("Could not determine start time")
        return
    
    # Post to DKPoolsMap
    print("\nPosting to DKPoolsMap...")
    pools_map_response = post_pool_to_map(DRAFTGROUP_ID, earliest_start, total_games)
    if pools_map_response:
        print("Successfully posted to pools map")
        print(f"API Response: {pools_map_response}")
    
    # Post players
    print(f"\nPosting {len(processed_players)} players to API...")
    response = post_to_api(DRAFTGROUP_ID, processed_players)
    if response:
        print("Successfully posted players")
        print(f"API Response: {response}")
    
    # Print first 3 players for verification
    print("\nFirst 3 players posted:")
    for player in processed_players[:3]:
        pprint(player)
    print("-" * 50)

if __name__ == "__main__":
    main()