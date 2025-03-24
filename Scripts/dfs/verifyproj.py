import requests
import urllib3
from enum import Enum
import re
import json
import time

# Disable SSL warnings for local development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ParseState(Enum):
    START = 0
    YEAR = 1
    TEAM_LINEUP = 2
    LINEUP_PLAYERS = 3
    TEAM_BENCH = 4
    BENCH_PLAYERS = 5
    TEAM_ROTATION = 6
    ROTATION_PLAYERS = 7

# Cache for player validation results to avoid redundant API calls
player_cache = {}

def validate_player(bbref_id):
    """
    Validates a player by checking the MLB Player API
    Returns a tuple of (is_valid, current_team)
    """
    # Check cache first
    if bbref_id in player_cache:
        return player_cache[bbref_id]
    
    api_url = f"https://localhost:44346/api/MLBPlayer/{bbref_id}"
    
    try:
        response = requests.get(api_url, verify=False, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            result = (True, data.get("currentTeam", "Unknown"))
        else:
            result = (False, None)
        
        # Cache the result
        player_cache[bbref_id] = result
        return result
    except requests.exceptions.Timeout:
        print(f"Timeout checking player {bbref_id}")
        return False, "Timeout"
    except Exception as e:
        print(f"Error checking player {bbref_id}: {e}")
        return False, None

def process_file(input_file, output_file):
    state = ParseState.START
    current_year = None
    current_team = None
    current_section = None
    
    lineup_count = 0
    bench_count = 0
    rotation_count = 0
    
    issues = []
    validation_results = []
    
    print(f"Reading file: {input_file}")
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    total_lines = len(lines)
    print(f"Processing {total_lines} lines...")
    
    player_count = 0
    start_time = time.time()
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Print progress every 20 lines
        if i % 20 == 0:
            elapsed = time.time() - start_time
            print(f"Processing line {i+1}/{total_lines} ({(i+1)/total_lines*100:.1f}%) - Elapsed: {elapsed:.1f}s")
            if player_count > 0:
                print(f"Processed {player_count} players so far")
        
        if state == ParseState.START or state == ParseState.YEAR:
            if re.match(r'^\d{4}$', line):
                # Year line
                current_year = line
                state = ParseState.YEAR
                validation_results.append(f"{current_year}")
                continue
            
        if state == ParseState.YEAR or state == ParseState.TEAM_LINEUP:
            if re.match(r'^[A-Z]{3}\s+Lineup$', line):
                # Team lineup line
                current_team = line.split()[0]
                current_section = "Lineup"
                state = ParseState.TEAM_LINEUP
                lineup_count = 0
                validation_results.append(f"{current_team} {current_section}")
                continue
                
        if state == ParseState.TEAM_LINEUP or state == ParseState.LINEUP_PLAYERS:
            if re.match(r'^[A-Z]{3}\s+Bench$', line):
                # Team bench line
                if lineup_count != 9:
                    issues.append(f"Line {line_num}: {current_team} Lineup has {lineup_count} players, expected 9")
                
                current_team = line.split()[0]
                current_section = "Bench"
                state = ParseState.TEAM_BENCH
                bench_count = 0
                validation_results.append(f"{current_team} {current_section}")
                continue
            elif re.match(r'^[a-z0-9]{5,}$', line):
                # Player line
                state = ParseState.LINEUP_PLAYERS
                lineup_count += 1
                player_count += 1
                
                # Validate player
                is_valid, player_team = validate_player(line)
                if not is_valid:
                    validation_results.append(f"{line} - not found")
                elif player_team != current_team:
                    validation_results.append(f"{line} - {player_team}")
                
                continue
                
        if state == ParseState.TEAM_BENCH or state == ParseState.BENCH_PLAYERS:
            if re.match(r'^[A-Z]{3}\s+Rotation$', line):
                # Team rotation line
                if bench_count != 4:
                    issues.append(f"Line {line_num}: {current_team} Bench has {bench_count} players, expected 4")
                
                current_team = line.split()[0]
                current_section = "Rotation"
                state = ParseState.TEAM_ROTATION
                rotation_count = 0
                validation_results.append(f"{current_team} {current_section}")
                continue
            elif re.match(r'^[a-z0-9]{5,}$', line):
                # Player line
                state = ParseState.BENCH_PLAYERS
                bench_count += 1
                player_count += 1
                
                # Validate player
                is_valid, player_team = validate_player(line)
                if not is_valid:
                    validation_results.append(f"{line} - not found")
                elif player_team != current_team:
                    validation_results.append(f"{line} - {player_team}")
                
                continue
                
        if state == ParseState.TEAM_ROTATION or state == ParseState.ROTATION_PLAYERS:
            if re.match(r'^\d{4}$', line):
                # New year, check if the previous rotation had enough players
                if rotation_count < 5:
                    issues.append(f"Line {line_num}: {current_team} Rotation has {rotation_count} players, expected at least 5")
                
                current_year = line
                state = ParseState.YEAR
                validation_results.append(f"{current_year}")
                continue
            elif re.match(r'^[A-Z]{3}\s+Lineup$', line):
                # New team, check if the previous rotation had enough players
                if rotation_count < 5:
                    issues.append(f"Line {line_num}: {current_team} Rotation has {rotation_count} players, expected at least 5")
                
                current_team = line.split()[0]
                current_section = "Lineup"
                state = ParseState.TEAM_LINEUP
                lineup_count = 0
                validation_results.append(f"{current_team} {current_section}")
                continue
            elif re.match(r'^[a-z0-9]{5,}$', line):
                # Player line
                state = ParseState.ROTATION_PLAYERS
                rotation_count += 1
                player_count += 1
                
                # Validate player
                is_valid, player_team = validate_player(line)
                if not is_valid:
                    validation_results.append(f"{line} - not found")
                elif player_team != current_team:
                    validation_results.append(f"{line} - {player_team}")
                
                continue
                
    # Check if the last team's rotation had enough players
    if state == ParseState.ROTATION_PLAYERS and rotation_count < 5:
        issues.append(f"EOF: {current_team} Rotation has {rotation_count} players, expected at least 5")
    
    total_time = time.time() - start_time
    print(f"Processing complete. Total time: {total_time:.2f}s")
    print(f"Processed {player_count} players total")
    print(f"API cache hit rate: {(player_count - len(player_cache))/player_count*100 if player_count > 0 else 0:.1f}%")
    
    # Write validation results to output file
    print(f"Writing results to {output_file}")
    with open(output_file, 'w') as f:
        f.write("=== VALIDATION ISSUES ===\n")
        if issues:
            for issue in issues:
                f.write(f"{issue}\n")
        else:
            f.write("No structure validation issues found.\n")
        
        f.write("\n=== PLAYER VALIDATION RESULTS ===\n")
        for result in validation_results:
            f.write(f"{result}\n")
    
    print(f"Results written to {output_file}")

if __name__ == "__main__":
    input_file = "projteam.txt"
    output_file = "validation_results.txt"
    process_file(input_file, output_file)