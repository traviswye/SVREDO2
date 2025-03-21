import requests
from datetime import datetime, date
import pytz
import certifi
from pprint import pprint
import argparse

def fetch_contests():
    url = "https://www.draftkings.com/lobby/getcontests?sport=MLB"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(
            url, 
            headers=headers,
            verify=certifi.where()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.SSLError as e:
        response = requests.get(url, headers=headers, verify=False)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contests: {e}")
        return None

def get_unique_classic_contests(contests_data, target_date=None):
    if not contests_data:
        return {}
    
    # Use provided target date or default to today
    est_tz = pytz.timezone('US/Eastern')
    if target_date:
        # If target_date is a string, convert it to date object
        if isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                print(f"Invalid date format: {target_date}. Using today's date instead.")
                target_date = datetime.now(est_tz).date()
    else:
        # Default to today
        target_date = datetime.now(est_tz).date()
    
    print(f"Looking for contests on: {target_date}")
    
    unique_contests = {}
    
    for contest in contests_data.get('Contests', []):
        if contest.get('gameType') == 'Classic':
            sd = contest.get('sd')
            # Convert contest date to EST and check if it matches the target date
            contest_date = convert_dk_time_to_est_datetime(sd).date()
            
            if contest_date == target_date:
                if sd not in unique_contests:
                    unique_contests[sd] = {
                        'id': contest.get('id'),
                        'sdstring': contest.get('sdstring'),
                        'date': contest_date.strftime('%Y-%m-%d')
                    }
    
    return unique_contests

def fetch_contest_details(contest_id):
    url = f"https://api.draftkings.com/contests/v1/contests/{contest_id}?format=json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(
            url, 
            headers=headers,
            verify=certifi.where()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.SSLError as e:
        response = requests.get(url, headers=headers, verify=False)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contest details for ID {contest_id}: {e}")
        return None

def fetch_draftables(draftgroup_id):
    url = f"https://api.draftkings.com/draftgroups/v1/draftgroups/{draftgroup_id}/draftables"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(
            url, 
            headers=headers,
            verify=certifi.where()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.SSLError as e:
        response = requests.get(url, headers=headers, verify=False)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching draftables for ID {draftgroup_id}: {e}")
        return None

def get_total_games_from_draftables(draftables_data):
    if not draftables_data or 'draftables' not in draftables_data:
        return 0
    
    # Use a set to track unique game IDs
    unique_games = set()
    
    for player in draftables_data['draftables']:
        game_id = player.get('competition', {}).get('competitionId')
        if game_id:
            unique_games.add(game_id)
    
    return len(unique_games)


def convert_dk_time_to_est(dk_time):
    return convert_dk_time_to_est_datetime(dk_time).strftime('%Y-%m-%d %I:%M %p EST')

def convert_dk_time_to_est_datetime(dk_time):
    timestamp = int(dk_time.replace("/Date(", "").replace(")/", "")) / 1000
    utc_time = datetime.fromtimestamp(timestamp, pytz.UTC)
    est_tz = pytz.timezone('US/Eastern')
    return utc_time.astimezone(est_tz)

def convert_utc_to_est(utc_time_str):
    # Remove additional zeros if present
    utc_time_str = utc_time_str.replace('.0000000', '')
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    utc_time = pytz.utc.localize(utc_time)
    est_tz = pytz.timezone('US/Eastern')
    est_time = utc_time.astimezone(est_tz)
    return est_time.strftime('%Y-%m-%d %I:%M %p EST')

def process_draftables(draftables_data, sport="MLB"):
    if not draftables_data or 'draftables' not in draftables_data:
        return []
    
    processed_players = {}  # Use dict for O(1) lookup of playerDkId
    ppg_attribute_id = 219 if sport == "NBA" else 408  # 219 for NBA, 408 for MLB
    
    for player in draftables_data['draftables']:
        player_dk_id = player.get('playerDkId')
        
        # Skip if we've already processed this player
        if player_dk_id in processed_players:
            continue
            
        # Get DraftStatAttributes values
        dk_ppg = next((attr['value'] for attr in player.get('draftStatAttributes', []) 
                      if attr['id'] == ppg_attribute_id), None)
        opp_rank = next((attr['value'] for attr in player.get('draftStatAttributes', []) 
                        if attr['id'] == -2), None)
        
        # Get UTC time and convert to expected format
        utc_time = player.get('competition', {}).get('startTime', '').replace('.0000000Z', 'Z')
        
        # Helper function to safely convert to float
        def safe_float(value):
            if not value or value == '-' or value == 'N/A':
                return 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0

        # Print for debugging
        print(f"Processing player {player.get('displayName')} - Status: {player['status']}")  # Direct access since we know it exists

        # Create processed player object
        processed_player = {
            'fullName': player.get('displayName', ''),
            'playerDkId': player_dk_id,
            'position': player.get('position', ''),
            'salary': player.get('salary', 0),
            'status': player['status'],  # Direct access since we know it exists
            'gameId': player.get('competition', {}).get('competitionId', 0),
            'game': player.get('competition', {}).get('name', ''),
            'gameStart': utc_time,
            'team': player.get('teamAbbreviation', ''),
            'dkppg': safe_float(dk_ppg),
            'oppRank': opp_rank if opp_rank not in ['-', 'N/A'] else None
        }
        
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
    
    try:
        response = requests.post(url, json=payload, headers=headers, verify=False)  # verify=False for local development
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting to API for draft group {draftgroup_id}: {e}")
        return None

def post_pools_to_map(unique_contests):
    url = "https://localhost:44346/api/DKPoolsMap/batch"
    headers = {
        'Content-Type': 'application/json'
    }
    
    pools_data = []
    for sd, contest in unique_contests.items():
        # Get contest details to get draftgroup ID
        contest_details = fetch_contest_details(contest['id'])
        if not contest_details:
            continue
            
        draftgroup_id = contest_details.get('contestDetail', {}).get('draftGroupId')
        if not draftgroup_id:
            continue
            
        # Fetch draftables to calculate total games
        draftables_data = fetch_draftables(draftgroup_id)
        total_games = get_total_games_from_draftables(draftables_data) if draftables_data else 0
            
        # Use the date from the contest info
        pool_entry = {
            "sport": "MLB",
            "draftGroupId": draftgroup_id,
            "date": contest['date'],  # Using the date from contest info
            "startTime": contest['sdstring'],
            "gameType": "Classic",
            "totalGames": total_games
        }
        pools_data.append(pool_entry)
    
    try:
        response = requests.post(url, json=pools_data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting to pools map API: {e}")
        return None

def list_all_available_dates(contests_data):
    """List all available dates from the contests data"""
    if not contests_data:
        return []
    
    est_tz = pytz.timezone('US/Eastern')
    dates = set()
    
    for contest in contests_data.get('Contests', []):
        if contest.get('gameType') == 'Classic':
            sd = contest.get('sd')
            # Convert contest date to EST
            contest_date = convert_dk_time_to_est_datetime(sd).date()
            dates.add(contest_date)
    
    return sorted(list(dates))

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process DraftKings contests')
    parser.add_argument('--date', type=str, help='Target date in YYYY-MM-DD format (e.g., 2025-03-27)')
    parser.add_argument('--list-dates', action='store_true', help='List all available dates with contests')
    args = parser.parse_args()
    
    # Step 1: Fetch all contests
    print("Fetching contests...")
    contests_data = fetch_contests()
    
    if not contests_data:
        print("Failed to fetch contests data. Exiting...")
        return
    
    # If --list-dates flag is provided, list all available dates and exit
    if args.list_dates:
        available_dates = list_all_available_dates(contests_data)
        print("\nAvailable dates with contests:")
        for date_obj in available_dates:
            print(f"- {date_obj.strftime('%Y-%m-%d')}")
        return
    
    # Step 2: Get unique classic contests for the specified date or today
    unique_contests = get_unique_classic_contests(contests_data, args.date)
    
    if not unique_contests:
        print(f"No classic contests found for the specified date: {args.date or 'today'}")
        # List available dates to help the user
        available_dates = list_all_available_dates(contests_data)
        print("\nAvailable dates with contests:")
        for date_obj in available_dates:
            print(f"- {date_obj.strftime('%Y-%m-%d')}")
        return
    
    print(f"\nFound {len(unique_contests)} unique Classic contests for {args.date or 'today'}:")
    for sd, contest in unique_contests.items():
        print(f"ID: {contest['id']} - Start Time: {convert_dk_time_to_est(sd)} ({contest['sdstring']})")
    
    # Step 2.5: Post pools to map
    print("\nPosting pools to DKPoolsMap...")
    pools_map_response = post_pools_to_map(unique_contests)
    if pools_map_response:
        print("Successfully posted pools to map")
        print(f"API Response: {pools_map_response}")
    else:
        print("Failed to post pools to map")
    
    # Step 3: Process each contest
    draftgroup_players = {}  # Dictionary to store players by draftgroup ID
    
    print("\nFetching and processing draftable players:")
    for sd, contest in unique_contests.items():
        contest_details = fetch_contest_details(contest['id'])
        if not contest_details:
            continue
            
        draftgroup_id = contest_details.get('contestDetail', {}).get('draftGroupId')
        
        if draftgroup_id:
            print(f"\nProcessing Draft Group ID: {draftgroup_id}")
            print(f"Contest Start Time: {convert_dk_time_to_est(sd)}")
            
            draftables_data = fetch_draftables(draftgroup_id)
            if draftables_data:
                processed_players = process_draftables(draftables_data, sport="MLB")
                draftgroup_players[draftgroup_id] = processed_players
    
    # Post each draftgroup's players to the API
    print("\nPosting players to API:")
    for draftgroup_id, players in draftgroup_players.items():
        print(f"\nPosting Draft Group ID: {draftgroup_id}")
        print(f"Total players to post: {len(players)}")
        
        response = post_to_api(draftgroup_id, players)
        if response:
            print(f"Successfully posted players for draft group {draftgroup_id}")
            print(f"API Response: {response}")
        else:
            print(f"Failed to post players for draft group {draftgroup_id}")
        
        # Print first 3 players for verification
        print(f"\nFirst 3 players posted:")
        for player in players[:3]:
            pprint(player)
        print("-" * 50)

if __name__ == "__main__":
    main()