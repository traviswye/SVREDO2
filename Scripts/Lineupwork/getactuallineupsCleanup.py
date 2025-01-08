import requests
from bs4 import BeautifulSoup

# URL of the page to scrape
url = 'https://www.mlb.com/starting-lineups'

# Make a request to get the page content
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the main container for the lineups
lineups_section = soup.find('section', class_='starting-lineups')

# Iterate over each matchup
for matchup in lineups_section.find_all('div', class_='starting-lineups__matchup'):
    # Extract teams
    away_team = matchup.find('span', class_='starting-lineups__team-name--away').get_text(strip=True)
    home_team = matchup.find('span', class_='starting-lineups__team-name--home').get_text(strip=True)
    print(f'{away_team} @ {home_team}')

    # Extract the away team's lineup
    print(f"{away_team} Lineup:")
    away_lineup = matchup.find('ol', class_='starting-lineups__team--away')
    if away_lineup:
        for player in away_lineup.find_all('li', class_='starting-lineups__player'):
            player_name = player.find('a').get_text(strip=True)
            player_position = player.find('span', class_='starting-lineups__player--position').get_text(strip=True)
            print(f"  {player_name} - {player_position}")
    else:
        print("  N/A - Lineup not announced")

    # Extract the home team's lineup
    print(f"{home_team} Lineup:")
    home_lineup = matchup.find('ol', class_='starting-lineups__team--home')
    if home_lineup:
        for player in home_lineup.find_all('li', class_='starting-lineups__player'):
            player_name = player.find('a').get_text(strip=True)
            player_position = player.find('span', class_='starting-lineups__player--position').get_text(strip=True)
            print(f"  {player_name} - {player_position}")
    else:
        print("  N/A - Lineup not announced")

    print("\n" + "="*50 + "\n")
