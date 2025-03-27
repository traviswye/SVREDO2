import requests
from bs4 import BeautifulSoup
import datetime
import urllib3
import re

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URLs for the tables
regular_season_standard_url = "https://www.mlb.com/standings/?tableType=regularSeasonStandard"
regular_season_expanded_url = "https://www.mlb.com/standings/?tableType=regularSeasonExpanded"

# Base URL for API calls
base_api_url = "https://localhost:44346/api/TeamRecSplits"

# Function to clean team names and handle special cases
def get_team_name(full_name):
    # First clean up any playoff indicators
    full_name = re.sub(r'[zwxy]$', '', full_name).strip()
    
    # Special handling for Sox teams with truncated "So"
    if "Boston Red So" in full_name:
        return "Red Sox"
    if "Chicago White So" in full_name:
        return "White Sox"
    
    # Handle special cases for teams with two words in their name
    if "Sox" in full_name:
        return " ".join(full_name.split()[-2:])
    if "Jays" in full_name:
        return " ".join(full_name.split()[-2:])
    
    # For all other teams, get the last word which is usually the team nickname
    parts = full_name.split()
    if parts:
        # Handle the case where "So" is the last word (should be "Sox")
        if parts[-1] == "So" and len(parts) >= 2:
            if parts[-2] == "Red":
                return "Red Sox"
            if parts[-2] == "White":
                return "White Sox"
        return parts[-1]
    
    return full_name
# Function to format the win percentage correctly
def format_win_percentage(win_percentage):
    if win_percentage.startswith('.'):
        return '0' + win_percentage
    return win_percentage

# Function to convert '-' to '0' for GB and WCGB
def convert_gb_wcgb(value):
    return '0' if value == '-' else value

# Function to provide default value for empty or None data
def default_if_empty(value, default="0-0"):
    if value is None or value.strip() == "":
        return default
    return value

# Function to scrape data from the standard standings URL
def scrape_standard_standings(url):
    response = requests.get(url, verify=False)  # Disable SSL verification
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the relevant table container
    table_container = soup.find('div', class_='StandingsTablestyle__StandingsTableWrapper-sc-1l6jbjt-0')
    if not table_container:
        print("Could not find the table container on the page.")
        return []
        
    table_element = table_container.find('table')
    if not table_element:
        print("Could not find the table element on the page.")
        return []

    print("Table element found, extracting data...")
    
    # Find the header row to identify column positions
    header_row = table_element.find('thead').find('tr')
    headers = [th.text.strip() for th in header_row.find_all('th')]
    print(f"Headers: {headers}")
    
    # Find the index of key columns
    vs500_index = None
    for i, header in enumerate(headers):
        if ">500" in header or ">.500" in header:
            vs500_index = i
            print(f"Found >.500 column at header index {vs500_index}")
            break

    # Default fallback if header not found
    if vs500_index is None:
        print("WARNING: Could not find >500 column, using default header index 13")
        vs500_index = 13

    # Adjust index for actual data extraction (td columns start after th)
    data_vs500_index = vs500_index - 1
    

        # Handling WCGB column dynamically
    wcgb_index = None
    for i, header in enumerate(headers):
        if "WCGB" in header:
            wcgb_index = i - 1  # adjust for the <th> offset
            print(f"WCGB found at index: {wcgb_index}")
            break

    wcgb_value = cols[wcgb_index].text.strip() if wcgb_index and wcgb_index < len(cols) else ""
    # Extract the data from all <tbody> elements (each division)
    data = []
    all_divisions = table_element.find_all('tbody')
    
    print(f"Found {len(all_divisions)} divisions")

    for division in all_divisions:
        rows = division.find_all('tr')
        print(f"Found {len(rows)} rows in a division")

        for row in rows:
            cols = row.find_all('td')
            # Check if the first cell contains a valid number (e.g., team wins)
            if not cols or len(cols) < 10 or not cols[0].text.strip().isdigit():
                print("Skipping header or invalid row")
                continue
            
            try:
                # Get the full team name from the TH element
                th_element = row.find('th')
                full_team = th_element.text.strip() if th_element else ""
                team_name = get_team_name(full_team)
                
                print(f"Processing team: {full_team} -> {team_name}")
                
                # Make sure vs500_index is in range
                if data_vs500_index < len(cols):
                    vs500_plus = cols[data_vs500_index].text.strip()
                else:
                    print(f"WARNING: data_vs500_index {data_vs500_index} out of range for {team_name}, using default")
                    vs500_plus = "0-0"
                
                team_data = {
                    'Team': team_name,
                    'Wins': int(cols[0].text.strip()),
                    'Losses': int(cols[1].text.strip()),
                    'WinPercentage': float(format_win_percentage(cols[2].text.strip())),
                    'GB': convert_gb_wcgb(cols[3].text.strip()),
                    'WCGB': convert_gb_wcgb(wcgb_value),
                    'L10': default_if_empty(cols[4].text.strip()),
                    'Streak': default_if_empty(cols[5].text.strip()),
                    'RunsScored': int(cols[6].text.strip()),
                    'RunsAgainst': int(cols[7].text.strip()),
                    'Diff': int(cols[8].text.strip()),
                    'ExpectedRecord': default_if_empty(cols[9].text.strip()),
                    'HomeRec': default_if_empty(cols[10].text.strip()),
                    'AwayRec': default_if_empty(cols[11].text.strip()),
                    'Vs500Plus': default_if_empty(cols[12].text.strip()),
                    'DateLastModified': datetime.datetime.now().isoformat(),
                    # Expanded defaults
                    'Xtra': "0-0",
                    'OneRun': "0-0",
                    'Day': "0-0",
                    'Night': "0-0",
                    'Grass': "0-0",
                    'Turf': "0-0",
                    'East': "0-0",
                    'Central': "0-0",
                    'West': "0-0",
                    'Inter': "0-0",
                    'VsRHP': "0-0",
                    'VsLHP': "0-0",
                    'L20': None,
                    'L30': None
                }

                data.append(team_data)
                print(f"Added data for team: {team_data['Team']}")
            except Exception as e:
                print(f"Error processing row: {e}")
                continue

    return data

# Function to scrape data from the expanded standings URL
def scrape_expanded_standings(url):
    try:
        response = requests.get(url, verify=False)  # Disable SSL verification
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the relevant table container
        table_container = soup.find('div', class_='StandingsTablestyle__StandingsTableWrapper-sc-1l6jbjt-0')
        if not table_container:
            print("Could not find the table container on the page.")
            return []
            
        table_element = table_container.find('table')
        if not table_element:
            print("Could not find the table element on the page.")
            return []

        print("Table element found, extracting data...")
        
        # Find the header row to identify column positions
        header_row = table_element.find('thead').find('tr')
        headers = [th.text.strip() for th in header_row.find_all('th')]
        print(f"Expanded Headers: {headers}")
        
        # Extract the data from all <tbody> elements (each division)
        data = []
        all_divisions = table_element.find_all('tbody')
        
        print(f"Found {len(all_divisions)} divisions")

        for division in all_divisions:
            rows = division.find_all('tr')
            print(f"Found {len(rows)} rows in a division")

            for row in rows:
                cols = row.find_all('td')
                # Check if there are enough columns and the first cell contains a valid number
                if not cols or len(cols) < 5 or not cols[0].text.strip().isdigit():
                    print("Skipping header or invalid row")
                    continue
                
                try:
                    # Get the full team name from the TH element
                    th_element = row.find('th')
                    full_team = th_element.text.strip() if th_element else ""
                    team_name = get_team_name(full_team)
                    
                    # Make sure we have enough columns, but don't error out - just use defaults
                    team_data = {
                        'Team': team_name,
                        'Xtra': default_if_empty(cols[4].text.strip()),
                        'OneRun': default_if_empty(cols[5].text.strip()),
                        'Day': default_if_empty(cols[6].text.strip()),
                        'Night': default_if_empty(cols[7].text.strip()),
                        'Grass': default_if_empty(cols[8].text.strip()),
                        'Turf': default_if_empty(cols[9].text.strip()),
                        'East': default_if_empty(cols[10].text.strip()),
                        'Central': default_if_empty(cols[11].text.strip()),
                        'West': default_if_empty(cols[12].text.strip()),
                        'Inter': default_if_empty(cols[13].text.strip()),
                        'VsRHP': default_if_empty(cols[14].text.strip()),
                        'VsLHP': default_if_empty(cols[15].text.strip())
                    }

                    
                    # Only add columns that exist
                    # if len(cols) > 5:
                    #     team_data['Xtra'] = default_if_empty(cols[5].text.strip())
                    # if len(cols) > 6:
                    #     team_data['OneRun'] = default_if_empty(cols[6].text.strip())
                    # if len(cols) > 7:
                    #     team_data['Day'] = default_if_empty(cols[7].text.strip())
                    # if len(cols) > 8:
                    #     team_data['Night'] = default_if_empty(cols[8].text.strip())
                    # if len(cols) > 9:
                    #     team_data['Grass'] = default_if_empty(cols[9].text.strip())
                    # if len(cols) > 10:
                    #     team_data['Turf'] = default_if_empty(cols[10].text.strip())
                    # if len(cols) > 11:
                    #     team_data['East'] = default_if_empty(cols[11].text.strip())
                    # if len(cols) > 12:
                    #     team_data['Central'] = default_if_empty(cols[12].text.strip())
                    # if len(cols) > 13:
                    #     team_data['West'] = default_if_empty(cols[13].text.strip())
                    # if len(cols) > 14:
                    #     team_data['Inter'] = default_if_empty(cols[14].text.strip())
                    # if len(cols) > 15:
                    #     team_data['VsRHP'] = default_if_empty(cols[15].text.strip())
                    # if len(cols) > 16:
                    #     team_data['VsLHP'] = default_if_empty(cols[16].text.strip())
                    
                    data.append(team_data)
                    print(f"Added expanded data for team: {team_data['Team']}")
                except Exception as e:
                    print(f"Error processing expanded row: {str(e)}")
                    continue

        return data
    except Exception as e:
        print(f"Error scraping expanded standings: {str(e)}")
        return []

# Function to merge the standard and expanded data
def merge_data(standard_data, expanded_data):
    # Create a dictionary from the expanded data for quick lookup
    expanded_dict = {team['Team']: team for team in expanded_data}

    # Merge the expanded data into the standard data
    for team in standard_data:
        if team['Team'] in expanded_dict:
            team.update(expanded_dict[team['Team']])  # Merge matching team data

    return standard_data

# Function to update data using the regular PUT endpoint
def update_data_via_put(data, base_url):
    headers = {'Content-Type': 'application/json'}
    
    # Print the teams we found
    team_names = [team['Team'] for team in data]
    print(f"Teams found: {team_names}")
    
    for team_data in data:
        team_name = team_data['Team']
        
        # Skip empty team names
        if not team_name:
            print("Skipping empty team name")
            continue
        
        # First use the regular PUT endpoint to update the team
        put_url = f"{base_url}/{team_name}"
        print(f"Updating team: {team_name} at {put_url}")
        
        try:
            response = requests.put(put_url, json=team_data, headers=headers, verify=False)
            if response.status_code == 204 or response.status_code == 200:  # Success for PUT
                print(f"Successfully updated team {team_name}")
            else:
                print(f"Failed to update team {team_name} - Status code: {response.status_code}")
                print(f"Response: {response.text}")
                
                # If team doesn't exist, try to create it
                if response.status_code == 404:
                    create_url = base_url
                    print(f"Team {team_name} not found, creating it...")
                    create_response = requests.post(create_url, json=team_data, headers=headers, verify=False)
                    if create_response.status_code == 201:
                        print(f"Successfully created team {team_name}")
                    else:
                        print(f"Failed to create team {team_name} - Status code: {create_response.status_code}")
                        print(f"Response: {create_response.text}")
        except Exception as e:
            print(f"Error updating team {team_name}: {str(e)}")

# Main execution block
if __name__ == "__main__":
    try:
        print("Starting MLB standings data collection...")
        # Scrape data from both tables
        standard_data = scrape_standard_standings(regular_season_standard_url)
        
        if not standard_data:
            print("No standard data found, check the URL or HTML structure")
            exit(1)
            
        expanded_data = scrape_expanded_standings(regular_season_expanded_url)
        
        if not expanded_data:
            print("No expanded data found, check the URL or HTML structure")
            # Continue anyway, just with default values for expanded data
            
        # Merge the data
        merged_data = merge_data(standard_data, expanded_data)
        
        # Update the data
        update_data_via_put(merged_data, base_api_url)
        
        print("Script completed successfully")
    except Exception as e:
        print(f"An error occurred during script execution: {str(e)}")