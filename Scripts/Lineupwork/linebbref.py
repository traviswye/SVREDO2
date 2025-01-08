import requests
from bs4 import BeautifulSoup
from datetime import datetime
import unicodedata

# Disable SSL verification and set headers to avoid tracking
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com',
    'DNT': '1',  # Do Not Track Request Header
    'Connection': 'keep-alive',
}

# Dictionary for team abbreviation to full name mapping
TEAM_NAME_MAP = {
    "ARI": "Diamondbacks",
    "ATL": "Braves",
    "BAL": "Orioles",
    "BOS": "Red Sox",
    "CHC": "Cubs",
    "CWS": "White Sox",
    "CIN": "Reds",
    "CLE": "Guardians",
    "COL": "Rockies",
    "DET": "Tigers",
    "HOU": "Astros",
    "KC": "Royals",
    "LAA": "Angels",
    "LAD": "Dodgers",
    "MIA": "Marlins",
    "MIL": "Brewers",
    "MIN": "Twins",
    "NYM": "Mets",
    "NYY": "Yankees",
    "OAK": "Athletics",
    "PHI": "Phillies",
    "PIT": "Pirates",
    "SDP": "Padres",
    "SEA": "Mariners",
    "SFG": "Giants",
    "STL": "Cardinals",
    "TBR": "Rays",
    "TEX": "Rangers",
    "TOR": "Blue Jays",
    "WSN": "Nationals"
}

# List to store pitchers not found in the database
not_found_pitchers = []

# Lineup API URL (assuming it's running locally)
lineup_api_url = "https://localhost:44346/api/Lineups"

def cleanse_name(name):
    """Replace accented characters with non-accented counterparts."""
    # Normalize the string to decompose accented characters
    normalized_name = unicodedata.normalize('NFD', name)
    
    # Remove accents and replace common special characters manually
    cleansed_name = ''.join(
        c if not unicodedata.combining(c) else '' 
        for c in normalized_name
    )
    
    # Manual replacements for common accented characters
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ñ': 'N'
    }
    
    for original, replacement in replacements.items():
        cleansed_name = cleansed_name.replace(original, replacement)
    
    return cleansed_name

def get_player_id_from_link(link):
    """Extract player ID from the player link."""
    return link.split('/')[-1].replace('.shtml', '')

def generate_bbref_id(player_name, attempt=1):
    """Generate the bbrefId from the player's name and attempt number."""
    # Cleanse the player's name to remove accents and special characters
    cleansed_name = cleanse_name(player_name)
    
    names = cleansed_name.split(' ')
    last_name, first_name = names[0], names[1]
    
    # Generate the bbrefId based on the correct logic with attempt number
    bbref_id = f"{first_name[:5].lower()}{last_name[:2].lower()}{str(attempt).zfill(2)}"
    
    return bbref_id

def check_pitcher_in_db(bbref_id):
    """Check if the generated bbrefId exists in the Pitchers table."""
    api_url = f"https://localhost:44346/api/Pitchers/exists/{bbref_id}"
    try:
        response = requests.get(api_url, headers=headers, verify=False)
        if response.status_code == 200:
            print(f"Pitcher {bbref_id} found in the database.")
            return True  # Pitcher exists in the database
        else:
            print(f"Pitcher {bbref_id} not found in the database.")
            return False  # Pitcher not found
    except requests.exceptions.RequestException as e:
        print(f"Error checking pitcher in database: {e}")
        return False

def post_lineup(lineup_data):
    """Post lineup data to the Lineups API."""
    try:
        response = requests.post(lineup_api_url, json=lineup_data, headers=headers, verify=False)
        if response.status_code == 201:
            print(f"Successfully posted lineup for game {lineup_data['gameNumber']}")
        else:
            print(f"Failed to post lineup. Status code: {response.status_code}")
            print(f"Response content: {response.content}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting lineup: {e}")

def scrape_team_lineup(url):
    """Scrape team lineup from the provided URL."""
    try:
        response = requests.get(url, headers=headers, verify=False)  # Disable SSL verification
        response.raise_for_status()  # Raise exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract team abbreviation from the URL
        team_abbr = url.split('/')[-2]
        team_name = TEAM_NAME_MAP.get(team_abbr, "Unknown Team")

        # Find the table containing the lineup information by ID
        table = soup.find('table', id='grid_table_782451')
        if not table:
            print("Lineup table not found.")
            return None

        rows = table.find('tbody').find_all('tr')

        for row in rows:
            # Extract Game Number
            game_number = row.find('th').text.strip().split('.')[0]  # Extract just the number (e.g., '1')

            # Extract Date
            opponent_info = row.find('th').get_text().strip()
            try:
                # Extract the date portion, which is in the format `Wed,8/14`
                date_portion = opponent_info.split(' ')[1]  # This should get '8/14'
                date_portion = date_portion.split(',')[1]   # This should get '8/14'
                date = datetime.strptime(f"{date_portion}/2024", "%m/%d/%Y").strftime("%Y-%m-%dT%H:%M:%S")
            except (ValueError, IndexError):
                print(f"Failed to parse date: {opponent_info}")
                continue

            # Extract Opponent abbreviation from the last <a> tag in the <th> element
            last_a_tag = row.find('th').find_all('a')[-1]  # Get the last <a> tag in the <th>
            opponent_abbr = last_a_tag.text.strip() if last_a_tag else "N/A"
            opponent = TEAM_NAME_MAP.get(opponent_abbr, opponent_abbr) if opponent_abbr else "N/A"

            # Extract result and score
            try:
                # The W or L should come before the score in parentheses
                result_score = row.find('th').text.strip().split('(')
                if len(result_score) > 1:
                    result = result_score[0].strip().split()[-1]  # Extract 'W' or 'L'
                    score = result_score[1].strip(')#')  # Extract the score without parentheses
                else:
                    result = "N/A"
                    score = "N/A"
            except IndexError:
                result = "N/A"
                score = "N/A"

            # Extract LHP status
            lhp = '#' in row.find('th').text.strip()

            # Extract Opposing SP
            opposing_sp = row.find('a', title=lambda title: title and 'facing' in title)
            opposing_sp_name = opposing_sp['title'].replace('facing: ', '') if opposing_sp else "N/A"

            # Generate bbrefId for OpposingSP and check the database
            if opposing_sp_name != "N/A":
                found_in_db = False
                for attempt in range(1, 11):  # Try up to 10 variations
                    generated_bbref_id = generate_bbref_id(opposing_sp_name, attempt)
                    print(f"Generated bbrefId for {opposing_sp_name}: {generated_bbref_id}")
                    if check_pitcher_in_db(generated_bbref_id):
                        opposing_sp = generated_bbref_id  # Update OpposingSP with bbrefId
                        found_in_db = True
                        break
                if not found_in_db:
                    print(f"{opposing_sp_name} not found in DB after multiple attempts.")
                    opposing_sp = cleanse_name(opposing_sp_name)  # Clean the name if bbrefId is not found
                    not_found_pitchers.append(opposing_sp)
            else:
                print("No opposing SP found.")
                opposing_sp = "N/A"

            # Extract batting order (players)
            players = [get_player_id_from_link(td.find('a')['href']) if td.find('a') else None for td in row.find_all('td', {'class': 'left'})]

            # Lineup data to be sent to the API
            lineup_data = {
                'team': team_name,  # Use the actual team name based on the URL
                'gameNumber': int(game_number),
                'date': date,
                'opponent': opponent,
                'opposingSP': opposing_sp,  # Now it should be either the bbrefId or the full name
                'lhp': lhp,
                'result': result,
                'score': score,
                'batting1st': players[0] if players else None,
                'batting2nd': players[1] if players else None,
                'batting3rd': players[2] if players else None,
                'batting4th': players[3] if players else None,
                'batting5th': players[4] if players else None,
                'batting6th': players[5] if players else None,
                'batting7th': players[6] if players else None,
                'batting8th': players[7] if players else None,
                'batting9th': players[8] if players else None
            }

            # Post the lineup data to the API
            post_lineup(lineup_data)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")

# Example usage
mlb_batting_order_urls = [
    "https://www.baseball-reference.com/teams/ARI/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/ATL/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/BAL/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/BOS/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/CHC/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/CWS/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/CIN/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/CLE/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/COL/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/DET/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/HOU/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/KC/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/LAA/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/LAD/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/MIA/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/MIL/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/MIN/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/NYM/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/NYY/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/OAK/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/PHI/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/PIT/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/SDP/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/SEA/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/SFG/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/STL/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/TBR/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/TEX/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/TOR/2024-batting-orders.shtml",
    "https://www.baseball-reference.com/teams/WSN/2024-batting-orders.shtml"
]
for url in mlb_batting_order_urls:
    scrape_team_lineup(url)

# Print pitchers not found in the database
print("Pitchers not found in the database:", not_found_pitchers)
