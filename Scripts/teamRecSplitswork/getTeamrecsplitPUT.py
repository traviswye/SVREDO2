import requests
from bs4 import BeautifulSoup
import datetime

# URLs for the tables
regular_season_standard_url = "https://www.mlb.com/standings/?tableType=regularSeasonStandard"
regular_season_expanded_url = "https://www.mlb.com/standings/?tableType=regularSeasonExpanded"

# API endpoint template for PUT
api_url_template = "https://localhost:44346/api/TeamRecSplits/{}"

# Function to format the win percentage correctly
def format_win_percentage(win_percentage):
    if win_percentage.startswith('.'):
        return '0' + win_percentage
    return win_percentage

# Function to convert '-' to '0' for GB and WCGB
def convert_gb_wcgb(value):
    return '0' if value == '-' else value

# Function to extract the last word of the team name
def extract_last_word(team_name):
    if team_name.split()[-1] == 'Sox':
        return team_name.split()[-2]
    if team_name.split()[-1] == 'Jays':
        return team_name.split()[-2]
    return team_name.split()[-1]

# Function to scrape data from the standard standings URL
def scrape_standard_standings(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the relevant table container
    table_container = soup.find('div', class_='StandingsTablestyle__StandingsTableWrapper-sc-1l6jbjt-0')
    table_element = table_container.find('table')

    if not table_element:
        print("Could not find the table element on the page.")
        return []

    print("Table element found, extracting data...")
    
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
            if not cols or not cols[0].text.strip().isdigit():
                print("Skipping header or invalid row")
                continue
            
            try:
                team_name = row.find('th').text.strip()  # Team name is inside <th>
                team_data = {
                    'Team': extract_last_word(team_name),
                    'Wins': int(cols[0].text.strip()),
                    'Losses': int(cols[1].text.strip()),
                    'WinPercentage': float(format_win_percentage(cols[2].text.strip())),
                    'GB': convert_gb_wcgb(cols[3].text.strip()),
                    'WCGB': convert_gb_wcgb(cols[4].text.strip()),
                    'L10': cols[5].text.strip(),
                    'Streak': cols[6].text.strip(),
                    'RunsScored': int(cols[7].text.strip()),
                    'RunsAgainst': int(cols[8].text.strip()),
                    'Diff': int(cols[9].text.strip().replace('+', '').replace('-', '')),  # Handle + and - signs
                    'ExpectedRecord': cols[10].text.strip(),
                    'HomeRec': cols[11].text.strip(),
                    'AwayRec': cols[12].text.strip(),
                    'vs500Plus': cols[13].text.strip(),
                    'NextGame': cols[14].text.strip(),
                    'DateLastModified': datetime.datetime.now().isoformat(),
                    # These will be filled from the expanded data
                    'Xtra': None,
                    'OneRun': None,
                    'Day': None,
                    'Night': None,
                    'Grass': None,
                    'Turf': None,
                    'East': None,
                    'Central': None,
                    'West': None,
                    'Inter': None,
                    'vsRHP': None,
                    'vsLHP': None,
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
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the relevant table container
    table_container = soup.find('div', class_='StandingsTablestyle__StandingsTableWrapper-sc-1l6jbjt-0')
    table_element = table_container.find('table')

    if not table_element:
        print("Could not find the table element on the page.")
        return []

    print("Table element found, extracting data...")
    
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
            if not cols or not cols[0].text.strip().isdigit():
                print("Skipping header or invalid row")
                continue
            
            try:
                team_name = row.find('th').text.strip()  # Team name is inside <th>
                team_data = {
                    'Team': extract_last_word(team_name),
                    'Xtra': cols[5].text.strip(),
                    'OneRun': cols[6].text.strip(),
                    'Day': cols[7].text.strip(),
                    'Night': cols[8].text.strip(),
                    'Grass': cols[9].text.strip(),
                    'Turf': cols[10].text.strip(),
                    'East': cols[11].text.strip(),
                    'Central': cols[12].text.strip(),
                    'West': cols[13].text.strip(),
                    'Inter': cols[14].text.strip(),
                    'vsRHP': cols[15].text.strip(),
                    'vsLHP': cols[16].text.strip(),
                }
                data.append(team_data)
                print(f"Added data for team: {team_data['Team']}")
            except Exception as e:
                print(f"Error processing row: {e}")
                continue

    return data

# Function to merge the standard and expanded data
def merge_data(standard_data, expanded_data):
    # Create a dictionary from the expanded data for quick lookup
    expanded_dict = {team['Team']: team for team in expanded_data}

    # Merge the expanded data into the standard data
    for team in standard_data:
        if team['Team'] in expanded_dict:
            team.update(expanded_dict[team['Team']])  # Merge matching team data

    return standard_data

# Function to update data via PUT method
def update_data_via_put(data, api_url_template):
    headers = {'Content-Type': 'application/json'}
    for team_data in data:
        team_name = team_data['Team']
        api_url = api_url_template.format(team_name)
        print(f"Updating data for team: {team_data} at {api_url}")
        response = requests.put(api_url, json=team_data, headers=headers, verify=False)
        if response.status_code == 200:  # Assuming 200 is the success status code for PUT
            print(f"Successfully updated data for {team_name}")
        else:
            print(f"Failed to update data for {team_name} - Status code: {response.status_code}")

# Scrape data from both tables
standard_data = scrape_standard_standings(regular_season_standard_url)
expanded_data = scrape_expanded_standings(regular_season_expanded_url)

# Merge the data
merged_data = merge_data(standard_data, expanded_data)

# Update the data using the PUT method
update_data_via_put(merged_data, api_url_template)
