import requests
from bs4 import BeautifulSoup
import pandas as pd

# Dictionary containing URLs for all MLB teams
mlb_team_urls = {
    #"Oakland Athletics": "https://www.covers.com/sport/baseball/mlb/teams/main/oakland-athletics",
    "Arizona Diamondbacks": "https://www.covers.com/sport/baseball/mlb/teams/main/arizona-diamondbacks",
    "Atlanta Braves": "https://www.covers.com/sport/baseball/mlb/teams/main/atlanta-braves",
    "Baltimore Orioles": "https://www.covers.com/sport/baseball/mlb/teams/main/baltimore-orioles",
    "Boston Red Sox": "https://www.covers.com/sport/baseball/mlb/teams/main/boston-red-sox",
    "Chicago Cubs": "https://www.covers.com/sport/baseball/mlb/teams/main/chicago-cubs",
    #"Chicago White Sox": "https://www.covers.com/sport/baseball/mlb/teams/main/chicago-white-sox",
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

# Initialize MLB totals
mlb_overall = 0.0
mlb_as_dog = 0.0
mlb_as_fav = 0.0
mlb_overall_wins = 0
mlb_overall_losses = 0
mlb_as_dog_wins = 0
mlb_as_dog_losses = 0
mlb_as_fav_wins = 0
mlb_as_fav_losses = 0

# Function to calculate winnings for negative odds
def calculate_fav_winnings(odds):
    return 100 * (100 / abs(odds))

# Function to process each team's page
def process_team(team_name, url):
    global mlb_overall, mlb_as_dog, mlb_as_fav, mlb_overall_wins, mlb_overall_losses, mlb_as_dog_wins, mlb_as_dog_losses, mlb_as_fav_wins, mlb_as_fav_losses

    # Send a GET request to the team's page
    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.content
    else:
        print(f"Failed to retrieve {team_name}'s webpage. Status code: {response.status_code}")
        return

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table by class name
    table = soup.find('table', class_='table covers-CoversMatchups-Table covers-CoversResults-Table covers-CoversSticky-table have-2ndCol-sticky')

    # Check if the table was found
    if not table:
        print(f"Could not find the table for {team_name}.")
        return

    # Initialize running totals and other metrics for the team
    overall = 0.0
    as_dog = 0.0
    as_fav = 0.0
    overall_wins = 0
    overall_losses = 0
    as_dog_wins = 0
    as_dog_losses = 0
    as_fav_wins = 0
    as_fav_losses = 0
    dog_total_odds = 0
    fav_total_odds = 0

    # Find all rows in the table body
    tbody = table.find('tbody')
    rows = tbody.find_all('tr') if tbody else []

    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 7:
            result = cells[2].get_text(strip=True)
            odds = cells[3].get_text(strip=True)

            if result and odds:
                odds_value = int(odds[1:])

                if odds.startswith('W'):
                    if odds_value > 0:
                        overall += odds_value
                        as_dog += odds_value
                        dog_total_odds += odds_value
                        overall_wins += 1
                        as_dog_wins += 1
                    else:
                        fav_winnings = calculate_fav_winnings(odds_value)
                        overall += fav_winnings
                        as_fav += fav_winnings
                        fav_total_odds += abs(odds_value)
                        overall_wins += 1
                        as_fav_wins += 1
                elif odds.startswith('L'):
                    overall -= 100
                    overall_losses += 1
                    if odds_value > 0:
                        as_dog -= 100
                        as_dog_losses += 1
                    else:
                        as_fav -= 100
                        as_fav_losses += 1

    # Update MLB totals
    mlb_overall += overall
    mlb_as_dog += as_dog
    mlb_as_fav += as_fav
    mlb_overall_wins += overall_wins
    mlb_overall_losses += overall_losses
    mlb_as_dog_wins += as_dog_wins
    mlb_as_dog_losses += as_dog_losses
    mlb_as_fav_wins += as_fav_wins
    mlb_as_fav_losses += as_fav_losses

    avg_dog_odds = dog_total_odds / as_dog_wins if as_dog_wins > 0 else 0
    avg_fav_odds = fav_total_odds / as_fav_wins if as_fav_wins > 0 else 0

    # Output the team's results
    print(f"{team_name}")
    print(f"Overall: {overall:.2f} {overall_wins}-{overall_losses} average odds = N/A (not applicable for overall)")
    print(f"As Dog: {as_dog:.2f} {as_dog_wins}-{as_dog_losses} average odds = {avg_dog_odds:.2f}")
    print(f"As Fav: {as_fav:.2f} {as_fav_wins}-{as_fav_losses} average odds = {avg_fav_odds:.2f}\n")

# Loop through each team and process their page
for team_name, url in mlb_team_urls.items():
    process_team(team_name, url)

# Output the cumulative MLB totals
print("MLB TOTAL")
print(f"Overall: {mlb_overall:.2f} {mlb_overall_wins}-{mlb_overall_losses}")
print(f"As Dog: {mlb_as_dog:.2f} {mlb_as_dog_wins}-{mlb_as_dog_losses}")
print(f"As Fav: {mlb_as_fav:.2f} {mlb_as_fav_wins}-{mlb_as_fav_losses}")
