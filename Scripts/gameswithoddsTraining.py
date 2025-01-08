import requests
from bs4 import BeautifulSoup
import re

# Dictionary containing URLs for all MLB teams
mlb_team_urls = {
    "Oakland Athletics": "https://www.covers.com/sport/baseball/mlb/teams/main/oakland-athletics",
    #"Arizona Diamondbacks": "https://www.covers.com/sport/baseball/mlb/teams/main/arizona-diamondbacks",
    "Atlanta Braves": "https://www.covers.com/sport/baseball/mlb/teams/main/atlanta-braves",
    "Baltimore Orioles": "https://www.covers.com/sport/baseball/mlb/teams/main/baltimore-orioles",
    "Boston Red Sox": "https://www.covers.com/sport/baseball/mlb/teams/main/boston-red-sox",
    "Chicago Cubs": "https://www.covers.com/sport/baseball/mlb/teams/main/chicago-cubs",
    "Chicago White Sox": "https://www.covers.com/sport/baseball/mlb/teams/main/chicago-white-sox",
    "Cincinnati Reds": "https://www.covers.com/sport/baseball/mlb/teams/main/cincinnati-reds",
    "Cleveland Guardians": "https://www.covers.com/sport/baseball/mlb/teams/main/cleveland-guardians",
    "Colorado Rockies": "https://www.covers.com/sport/baseball/mlb/teams/main/colorado-rockies",
    "Detroit Tigers": "https://www.covers.com/sport/baseball/mlb/teams/main/detroit-tigers",
    "Houston Astros": "https://www.covers.com/sport/baseball/mlb/teams/main/houston-astros",
    "Kansas City Royals": "https://www.covers.com/sport/baseball/mlb/teams/main/kansas-city-royals",
    "Los Angeles Angels": "https://www.covers.com/sport/baseball/mlb/teams/main/los-angeles-angels",
    "Los Angeles Dodgers": "https://www.covers.com/sport/baseball/mlb/teams/main/los-angeles-dodgers",
    "Miami Marlins": "https://www.covers.com/sport/baseball/mlb/teams/main/miami-marlins",
    "Milwaukee Brewers": "https://www.covers.com/sport/baseball/mlb/teams/main/milwaukee-brewers",
    "Minnesota Twins": "https://www.covers.com/sport/baseball/mlb/teams/main/minnesota-twins",
    "New York Mets": "https://www.covers.com/sport/baseball/mlb/teams/main/new-york-mets",
    "New York Yankees": "https://www.covers.com/sport/baseball/mlb/teams/main/new-york-yankees",
    "Philadelphia Phillies": "https://www.covers.com/sport/baseball/mlb/teams/main/philadelphia-phillies",
    "Pittsburgh Pirates": "https://www.covers.com/sport/baseball/mlb/teams/main/pittsburgh-pirates",
    "San Diego Padres": "https://www.covers.com/sport/baseball/mlb/teams/main/san-diego-padres",
    "San Francisco Giants": "https://www.covers.com/sport/baseball/mlb/teams/main/san-francisco-giants",
    "Seattle Mariners": "https://www.covers.com/sport/baseball/mlb/teams/main/seattle-mariners",
    "St. Louis Cardinals": "https://www.covers.com/sport/baseball/mlb/teams/main/st.-louis-cardinals",
    "Tampa Bay Rays": "https://www.covers.com/sport/baseball/mlb/teams/main/tampa-bay-rays",
    "Texas Rangers": "https://www.covers.com/sport/baseball/mlb/teams/main/texas-rangers",
    "Toronto Blue Jays": "https://www.covers.com/sport/baseball/mlb/teams/main/toronto-blue-jays",
    "Washington Nationals": "https://www.covers.com/sport/baseball/mlb/teams/main/washington-nationals"
}

# Team name to abbreviation mapping (with edge cases handled)
team_abbreviation_mapping = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KCR",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SDP",
    "San Francisco Giants": "SFG",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TBR",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WAS"
}

# API base URLs
gameresults_api = "https://localhost:44346/api/gameresultswithodds"
player_search_api = "https://localhost:44346/api/MLBPlayer/search"

# Function to get the bbrefId for a pitcher by name and team abbreviation
def get_bbref_id(pitcher_name, team_abbreviation):
    full_name = pitcher_name.replace("-", " ").strip()  # Clean up the name
    params = {
        "fullName": full_name,
        "team": team_abbreviation.lower()
    }

    # Print the payload being sent to the player search API
    #print(f"Searching for pitcher: {full_name}, Team: {team_abbreviation}")

    # Send the request to the player search API
    response = requests.get(player_search_api, params=params, verify=False)  # Disable SSL verification for localhost

    # Print the response from the player search API
    #print(f"Search Response for {full_name}: {response.status_code} - {response.text}")

    if response.status_code == 200 and response.json():
        return response.json()[0].get('bbrefId')
    return None

# Function to process the date and convert to YYYY-MM-DD
def extract_date(date_string):
    # Mapping of month names to their numeric equivalent
    month_mapping = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    parts = date_string.split(" ")
    month = parts[0]
    day_match = re.match(r"(\d+)", parts[1])
    if day_match:
        day = day_match.group(1).zfill(2)  # Ensure day is 2 digits
        month_num = month_mapping.get(month, "01")  # Default to Jan if month not found
        year = "2024"  # You can dynamically adjust the year if needed
        return f"{year}-{month_num}-{day}"
    return "2024-01-01"  # Default fallback

# Function to extract the pitcher's full name from the href attribute and remove 'Jr.' if present
def extract_pitcher_full_name(pitcher_cell):
    link = pitcher_cell.find('a')
    if link and 'href' in link.attrs:
        href = link['href']
        # Extract the part of the href that contains the name (e.g., "/sport/baseball/mlb/players/247070/justin-verlander")
        name_part = href.split("/")[-1].replace("-", " ")  # Convert hyphens to spaces
        # Remove 'Jr.' if it exists at the end of the name
        if name_part.endswith(" jr."):
            name_part = name_part[:-3].strip()
        return name_part
    return pitcher_cell.get_text(strip=True)  # Fallback to text if no link is found

# Function to handle the edge cases for opponent abbreviation
def clean_opponent_abbreviation(opponent):
    opponent = opponent.replace("@", "").strip()

    if opponent == "SF":
        return "SFG"
    if opponent == "KC":
        return "KCR"
    if opponent == "TB":
        return "TBR"
    if opponent == "SD":
        return "SDP"
    if opponent == "WAS":
        return "WSN"
    
    return team_abbreviation_mapping.get(opponent, opponent)

# Function to calculate winnings for negative odds
def calculate_fav_winnings(odds):
    return 100 * (100 / abs(odds))

# Function to process each team's page
def process_team(team_name, url):
    # Initialize tracking variables
    overall_wins, overall_losses = 0, 0
    fav_wins, fav_losses = 0, 0
    dog_wins, dog_losses = 0, 0
    overall_better, dog_better, fav_better = 0.0, 0.0, 0.0

    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
    else:
        print(f"Failed to retrieve {team_name}'s webpage. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='table covers-CoversMatchups-Table covers-CoversResults-Table covers-CoversSticky-table have-2ndCol-sticky')

    if not table:
        print(f"Could not find the table for {team_name}.")
        return

    team_abbreviation = team_abbreviation_mapping.get(team_name)
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')[::-1] if tbody else []

    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 7:
            date_info = extract_date(cells[0].get_text(strip=True))
            opponent = cells[1].get_text(strip=True).strip()
            opponent_abbreviation = clean_opponent_abbreviation(opponent)

            score = cells[2].get_text(strip=True)
            result = score[0]
            odds = int(cells[3].get_text(strip=True)[1:])
            over_under = cells[4].get_text(strip=True)[1:]
            over_under_res = cells[4].get_text(strip=True)[0]

            pitcher = extract_pitcher_full_name(cells[5])
            opposing_pitcher = extract_pitcher_full_name(cells[6])

            pitcher_bbref_id = get_bbref_id(pitcher, team_abbreviation)
            opposing_pitcher_bbref_id = get_bbref_id(opposing_pitcher, opponent_abbreviation)

            # Update the overall record
            if result == 'W':
                overall_wins += 1
            elif result == 'L':
                overall_losses += 1

            # Update records and financial tracking based on odds
            if odds > 0:  # Underdog
                if result == 'W':
                    dog_wins += 1
                    dog_better += odds
                    overall_better += odds
                else:
                    dog_losses += 1
                    dog_better -= 100
                    overall_better -= 100
            else:  # Favorite
                if result == 'W':
                    fav_wins += 1
                    fav_better += calculate_fav_winnings(odds)
                    overall_better += calculate_fav_winnings(odds)
                else:
                    fav_losses += 1
                    fav_better -= 100
                    overall_better -= 100

            # Prepare the payload for posting to the API
            payload = {
                "id": 0,
                "team": team_name,
                "date": date_info,
                "opponent": opponent,  # Retain the "@" here
                "score": score,
                "result": result,
                "odds": str(odds),
                "overUnder": over_under,
                "overUnderRes": over_under_res,
                "pitcher": pitcher_bbref_id if pitcher_bbref_id else pitcher,
                "opposingPitcher": opposing_pitcher_bbref_id if opposing_pitcher_bbref_id else opposing_pitcher,
                "recordAsFav": f"{fav_wins}-{fav_losses}",
                "recordAsDog": f"{dog_wins}-{dog_losses}",
                "overallRecord": f"{overall_wins}-{overall_losses}",
                "overallBetter": overall_better,
                "dogBetter": dog_better,
                "favBetter": fav_better
            }

            post_response = requests.post(gameresults_api, json=payload, verify=False)
            if post_response.status_code in [200, 201]:
                print(f"Successfully posted game result for {team_name} on {date_info}.")
            else:
                print(f"Failed to post game result for {team_name} on {date_info}. Status code: {post_response.status_code}")

# Loop through each team and process their page
for team_name, url in mlb_team_urls.items():
    process_team(team_name, url)
