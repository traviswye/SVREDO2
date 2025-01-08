import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Headers to avoid tracking and SSL warnings
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com',
    'DNT': '1',
    'Connection': 'keep-alive',
}

# Dictionary mapping for team abbreviations
TEAM_NAME_MAP = {
    "ARI": "Diamondbacks", "ATL": "Braves", "BAL": "Orioles", "BOS": "Red Sox",
    "CHC": "Cubs", "CWS": "White Sox", "CIN": "Reds", "CLE": "Guardians",
    "COL": "Rockies", "DET": "Tigers", "HOU": "Astros", "KC": "Royals",
    "LAA": "Angels", "LAD": "Dodgers", "MIA": "Marlins", "MIL": "Brewers",
    "MIN": "Twins", "NYM": "Mets", "NYY": "Yankees", "OAK": "Athletics",
    "PHI": "Phillies", "PIT": "Pirates", "SDP": "Padres", "SEA": "Mariners",
    "SFG": "Giants", "STL": "Cardinals", "TBR": "Rays", "TEX": "Rangers",
    "TOR": "Blue Jays", "WSN": "Nationals"
}

# API URL
lineup_api_url = "https://localhost:44346/api/Lineups"

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

def scrape_last_lineup(team_abbr):
    """Scrape the last lineup for a given team."""
    url = f"https://www.baseball-reference.com/teams/{team_abbr}/2024-batting-orders.shtml"
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table containing the lineup information
        table = soup.find('table', id='grid_table_782451')
        if not table:
            print("Lineup table not found.")
            return None

        # Extract the last row (most recent game)
        last_row = table.find('tbody').find_all('tr')[-1]

        # Extract Game Number
        game_number = last_row.find('th').text.strip().split('.')[0]

        # Extract Date
        opponent_info = last_row.find('th').get_text().strip()
        try:
            date_portion = opponent_info.split(' ')[1].split(',')[1]  # Extract '8/14' part
            date = datetime.strptime(f"{date_portion}/2024", "%m/%d/%Y").strftime("%Y-%m-%dT%H:%M:%S")
        except (ValueError, IndexError):
            print(f"Failed to parse date: {opponent_info}")
            return None

        # Extract Opponent abbreviation from the last <a> tag in the <th> element
        last_a_tag = last_row.find('th').find_all('a')[-1]
        opponent_abbr = last_a_tag.text.strip() if last_a_tag else "N/A"
        opponent = TEAM_NAME_MAP.get(opponent_abbr, opponent_abbr) if opponent_abbr else "N/A"

        # Extract result and score
        try:
            result_score = last_row.find('th').text.strip().split('(')
            result = result_score[0].strip().split()[-1] if len(result_score) > 1 else "N/A"
            score = result_score[1].strip(')#') if len(result_score) > 1 else "N/A"
        except IndexError:
            result = "N/A"
            score = "N/A"

        # Extract LHP status
        lhp = '#' in last_row.find('th').text.strip()

        # Extract Opposing SP
        opposing_sp = last_row.find('a', title=lambda title: title and 'facing' in title)
        opposing_sp_name = opposing_sp['title'].replace('facing: ', '') if opposing_sp else "N/A"

        # Extract batting order (players)
        players = [td.find('a')['href'].split('/')[-1].replace('.shtml', '') if td.find('a') else None
                   for td in last_row.find_all('td', {'class': 'left'})]

        # Lineup data
        lineup_data = {
            'team': TEAM_NAME_MAP.get(team_abbr, team_abbr),
            'gameNumber': int(game_number),
            'date': date,
            'opponent': opponent,
            'opposingSP': opposing_sp_name,
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

# Call this function within your service whenever a new game preview is posted
def get_and_post_lineups_for_game(home_team, away_team):
    """Fetch and post the last lineups for both teams playing in the game."""
    scrape_last_lineup(home_team)
    scrape_last_lineup(away_team)


home_team = "Marlins"
away_team = "Mets"