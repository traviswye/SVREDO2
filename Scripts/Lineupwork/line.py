import requests
from bs4 import BeautifulSoup
from datetime import datetime

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

def get_player_id_from_link(link):
    """Extract player ID from the player link."""
    return link.split('/')[-1].replace('.shtml', '')

def scrape_team_lineup(url):
    """Scrape team lineup from the provided URL."""
    try:
        response = requests.get(url, headers=headers, verify=False)  # Disable SSL verification
        response.raise_for_status()  # Raise exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
        
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
                date = datetime.strptime(f"{date_portion}/2024", "%m/%d/%Y").strftime("%m/%d/%y")
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
            opposing_sp = opposing_sp['title'].replace('facing: ', '') if opposing_sp else "N/A"

            # Extract batting order (players)
            players = [get_player_id_from_link(td.find('a')['href']) if td.find('a') else None for td in row.find_all('td', {'class': 'left'})]

            lineup_data = {
                'GameNumber': game_number,
                'Date': date,
                'HomeAway': "Home" if "vs" in opponent_info else "Away",
                'Opponent': opponent,
                'Result': result,
                'Score': score,
                'LHP': lhp,
                'OpposingSP': opposing_sp,
                'BattingOrder': players  # List of player IDs in order
            }

            print(lineup_data)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")

# Example usage
url = "https://www.baseball-reference.com/teams/LAD/2024-batting-orders.shtml"
scrape_team_lineup(url)
