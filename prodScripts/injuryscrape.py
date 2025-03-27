import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3

# Suppress all insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dictionary mapping team names to their abbreviations
team_abbr_dict = {
    "Arizona": "ARI",
    "Atlanta": "ATL",
    "Baltimore": "BAL",
    "Boston": "BOS",
    "Chi. Cubs": "CHC",
    "Chi. White Sox": "CWS",
    "Cincinnati": "CIN",
    "Cleveland": "CLE",
    "Colorado": "COL",
    "Detroit": "DET",
    "Houston": "HOU",
    "Kansas City": "KCR",
    "LA Angels": "LAA",
    "LA Dodgers": "LAD",
    "Miami": "MIA",
    "Milwaukee": "MIL",
    "Minnesota": "MIN",
    "NY Mets": "NYM",
    "NY Yankees": "NYY",
    "Oakland": "OAK",
    "Philadelphia": "PHI",
    "Pittsburgh": "PIT",
    "San Diego": "SDP",
    "San Francisco": "SFG",
    "Seattle": "SEA",
    "St. Louis": "STL",
    "Tampa Bay": "TBR",
    "Texas": "TEX",
    "Toronto": "TOR",
    "Washington": "WSN"
}

# Current year for all injury records
CURRENT_YEAR = 2025

# Function to lookup bbrefId for each player
def lookup_bbrefId(full_name, team_name):
    team_abbr = team_abbr_dict.get(team_name, None)
    if team_abbr is None:
        print(f"Team abbreviation not found for {team_name}")
        return None
    
    url = f"https://localhost:44346/api/MLBPlayer/search?fullName={full_name}&team={team_abbr}"
    headers = {"accept": "text/plain"}
    
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200 and response.json():
        bbrefId = response.json()[0].get("bbrefId")
        return bbrefId
    else:
        print(f"Failed to find bbrefId for {full_name} ({team_name})")
        return None

# Function to post injury data
def post_injury_data(bbrefId, injury_description, current_team):
    # Remove \r\n\r\n from the injury description
    cleaned_injury_description = injury_description.replace('\r\n', ' ').strip()
    
    current_date = datetime.now()
    
    payload = {
        "bbrefId": bbrefId,
        "InjuryDescription": cleaned_injury_description,
        "CurrentTeam": current_team,
        "Date": current_date.isoformat(),
        "Year": CURRENT_YEAR  # Add the current year to the payload
    }
    
    url = "https://localhost:44346/api/Injury"
    headers = {
        "accept": "text/plain",
        "Content-Type": "application/json"
    }
    
    print(f"Payload: {payload}")
    
    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 201:
        print(f"Successfully posted injury for bbrefId: {bbrefId} for year {CURRENT_YEAR}")
    else:
        print(f"Failed to post injury for bbrefId: {bbrefId} - Status Code: {response.status_code}")
        if response.text:
            print(f"Response: {response.text}")

# URL of the page containing the injuries
url = "https://www.covers.com/sport/baseball/mlb/injuries"

# Send a GET request to the URL with verify=False to ignore SSL certificate verification
response = requests.get(url, verify=False)

# Parse the HTML content of the page using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Initialize an empty list to store the injury data
injury_data = []
total_players = 0  # Counter for total players

print(f"Starting injury scraping for year {CURRENT_YEAR}...")

# Find all sections for teams (using the team anchors)
team_sections = soup.find_all('section')

for team_section in team_sections:
    # Initialize a list to hold team data
    team_data = []
    
    # Get the team name (from the alt attribute of the team image)
    team_img = team_section.find('img')
    if not team_img or 'alt' not in team_img.attrs:
        continue  # Skip if no team image found
        
    team_name = team_img['alt']
    
    # Find all rows of the injury table for this team
    injury_rows = team_section.find_all('tr', class_=lambda x: x != 'collapse')
    
    for row in injury_rows:
        # Check if the row contains the necessary elements
        player_link = row.find('a')
        cells = row.find_all('td')
        
        position_cell = cells[1] if len(cells) > 1 else None
        status_cell = cells[2] if len(cells) > 2 else None
        
        if player_link and position_cell and status_cell:
            # Get the player's name abbreviation
            player_name_abbr = player_link.text.strip()
            
            # Get the full name from the href
            href = player_link['href']
            full_name_hyphenated = href.split('/')[-1]  # Get the last part of the href
            full_name = ' '.join([part.capitalize() for part in full_name_hyphenated.split('-')])  # Convert to full name
            
            # Get the player's position
            position = position_cell.text.strip()
            
            # Get the player's injury status
            injury_status = status_cell.text.strip()
            
            # Lookup bbrefId for the player
            bbrefId = lookup_bbrefId(full_name, team_name)
            
            if bbrefId:
                # Post the injury data
                post_injury_data(bbrefId, injury_status, team_abbr_dict.get(team_name))
            
            # Append the player data to the team_data list
            team_data.append([full_name, bbrefId, position, injury_status])
            total_players += 1  # Increment the total players count
    
    # Append the team data to the injury_data list
    injury_data.append([team_name, team_data])

# Print the injury data
for team in injury_data:
    print(f"Team: {team[0]}")
    for player in team[1]:
        print(f"Player: {player[0]}, bbrefId: {player[1]} Position: {player[2]}, Status: {player[3]}")
    print("\n")

# Print the total number of players
print(f"Total number of injured players for {CURRENT_YEAR}: {total_players}")