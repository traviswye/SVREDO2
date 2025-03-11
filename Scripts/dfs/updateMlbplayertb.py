import requests
import re
import time
import random
from bs4 import BeautifulSoup
import os
import argparse
import logging
from urllib.parse import quote
import urllib3

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bbref_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def extract_name_team(line):
    """Extract player name and team from input line."""
    match = re.match(r'(.*?)\s*\((.*?)\)', line.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    else:
        return line.strip(), None

def search_bbref_id(player_name, team):
    """
    Search DuckDuckGo for the Baseball Reference player URL using a query
    like "Lucas Giolito BOS site:baseball-reference.com/players" and extract
    the player id from the first five links that match the expected pattern.
    """
    query = f"{player_name} {team} site:baseball-reference.com/players"
    # Use the HTML version of DuckDuckGo
    search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    logger.info(f"Searching for: {player_name} ({team})")
    logger.info(f"Search URL: {search_url}")
    
    try:
        response = requests.get(search_url, headers=headers, verify=False)
        response.raise_for_status()
        
        # Save the HTML for debugging if needed
        with open(f"debug_{player_name.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all("a", href=True)
        logger.info(f"Found {len(links)} links in search results")
        
        # Define a regex pattern for the MLB player URL on baseball-reference.com
        pattern = re.compile(r'baseball-reference\.com/players/[a-z]/([^/]+)\.shtml')
        
        # Only check the first 5 links in order
        for link in links[:5]:
            href = link['href']
            if 'baseball-reference.com/players/' in href:
                logger.info(f"Candidate link: {href}")
                match = pattern.search(href)
                if match:
                    bbref_id = match.group(1)
                    if '000' not in bbref_id:
                        logger.info(f"Found major league ID: {bbref_id} for {player_name}")
                        return bbref_id
        
        logger.warning(f"No Baseball Reference ID found for {player_name} ({team})")
        return None
        
    except Exception as e:
        logger.error(f"Error searching for {player_name}: {e}")
        logger.error(f"Exception details: {str(e)}")
        raise SystemExit("Script stopped due to search failure.")

def post_player_to_api(bbref_id, name, team, api_url):
    """Post player info to the API."""
    data = {
        "bbrefId": bbref_id,
        "fullName": name,
        "currentTeam": team
    }
    
    try:
        response = requests.post(
            api_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            verify=False  # For local development
        )
        
        if response.status_code in (200, 201):
            logger.info(f"Successfully added {name} ({bbref_id}) to database")
            return True
        else:
            logger.error(f"Failed to add {name}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error posting {name} to API: {e}")
        return False

def process_players_file(filename, api_url, delay_min=2, delay_max=5):
    """Process each line in the players file."""
    success_count = 0
    skipped_count = 0
    error_count = 0
    last_successful_player = None
    
    with open(filename, 'r', encoding='utf-8') as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if not line:
                continue
            
            try:    
                player_name, team = extract_name_team(line)
                if not team:
                    logger.warning(f"Line {line_num}: Could not extract team for '{line}', skipping")
                    skipped_count += 1
                    continue
                    
                bbref_id = search_bbref_id(player_name, team)
                
                # Add delay to avoid rate limiting
                delay = random.uniform(delay_min, delay_max)
                logger.info(f"Waiting for {delay:.1f} seconds before next request")
                time.sleep(delay)
                
                if not bbref_id:
                    logger.warning(f"Line {line_num}: Could not find Baseball Reference ID for '{player_name} ({team})'")
                    skipped_count += 1
                    continue
                    
                # Skip IDs with '000' in them (minor league players)
                if '000' in bbref_id:
                    logger.info(f"Line {line_num}: Skipping minor league player '{player_name}' with ID '{bbref_id}'")
                    skipped_count += 1
                    continue
                    
                # Post to API
                success = post_player_to_api(bbref_id, player_name, team, api_url)
                if success:
                    success_count += 1
                    last_successful_player = f"{player_name} ({team}) - {bbref_id}"
                    logger.info(f"Added to database: {player_name} ({team}) with ID {bbref_id}")
                else:
                    error_count += 1
                    logger.error(f"Failed to add to database: {player_name} ({team}) with ID {bbref_id}")
                    
                # Add delay between API calls
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Process interrupted by user. Returning current results.")
                break
            except SystemExit as e:
                logger.critical(f"Critical error: {str(e)}")
                logger.info(f"Last successful player processed: {last_successful_player or 'None'}")
                return {
                    "success": success_count,
                    "skipped": skipped_count,
                    "error": error_count,
                    "last_successful": last_successful_player
                }
            except Exception as e:
                logger.error(f"Error processing line {line_num} ({line}): {e}")
                error_count += 1
                continue
    
    return {
        "success": success_count,
        "skipped": skipped_count,
        "error": error_count,
        "last_successful": last_successful_player
    }

def main():
    parser = argparse.ArgumentParser(description='Import baseball players from a list to API')
    parser.add_argument('file', help='Path to file containing player list')
    parser.add_argument('--api-url', default='https://localhost:44346/api/MLBPlayer', 
                       help='API endpoint URL (default: https://localhost:44346/api/MLBPlayer)')
    parser.add_argument('--min-delay', type=float, default=2.0, 
                       help='Minimum delay between searches (default: 2.0 seconds)')
    parser.add_argument('--max-delay', type=float, default=5.0, 
                       help='Maximum delay between searches (default: 5.0 seconds)')
    parser.add_argument('--no-verify', action='store_true',
                       help='Disable SSL verification for all requests')
    parser.add_argument('--start-from', type=str, default='',
                       help='Start processing from a specific player name (skip until this player is found)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        return
    
    # Always disable SSL verification to avoid certificate issues
    logger.info("SSL verification disabled for all requests")
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()
        
    logger.info(f"Starting to process player list from {args.file}")
    logger.info(f"Using API endpoint: {args.api_url}")
    
    # Preprocess file if starting from a specific player
    if args.start_from:
        logger.info(f"Will start processing from player containing: '{args.start_from}'")
        temp_file = f"{args.file}.temp"
        start_found = False
        with open(args.file, 'r', encoding='utf-8') as infile, open(temp_file, 'w', encoding='utf-8') as outfile:
            for line in infile:
                if start_found or args.start_from.lower() in line.lower():
                    start_found = True
                    outfile.write(line)
        
        if start_found:
            logger.info(f"Created temporary file starting from '{args.start_from}'")
            args.file = temp_file
        else:
            logger.warning(f"Player '{args.start_from}' not found in file, processing entire file")
    
    stats = process_players_file(args.file, args.api_url, args.min_delay, args.max_delay)
    
    # Clean up temp file if created
    if args.start_from and os.path.exists(f"{args.file}.temp"):
        os.remove(f"{args.file}.temp")
    
    logger.info("Processing complete!")
    logger.info(f"Summary: {stats['success']} added, {stats['skipped']} skipped, {stats['error']} errors")
    logger.info(f"Last successful player: {stats.get('last_successful', 'None')}")

if __name__ == "__main__":
    main()
