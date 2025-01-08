from datetime import datetime
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_date(date_str, year):
    """Converts date like 'Sep 29' into 'YYYY-MM-DD' format."""
    date_str = date_str.replace("\xa0", " ")
    return datetime.strptime(f"{date_str} {year}", "%b %d %Y").strftime("%Y-%m-%d")

def get_park_factor(team):
    """Gets the park factor for the team."""
    url = f"https://localhost:44346/api/ParkFactors/getParkFactor?teamAbbreviation={team}"
    response = requests.get(url, verify=False)  # Ignore SSL verification
    if response.status_code == 200:
        return response.json()["parkFactorRating"]  # Extract park factor rating
    else:
        print(f"Failed to fetch park factor for team {team}. Status: {response.status_code}")
        return 0


def get_bbrefid(first_initial, last_name, team):
    """Gets the bbrefid for a pitcher."""
    url = f"https://localhost:44346/api/MLBPlayer/searchAbr?firstInitial={first_initial}&lastName={last_name}&team={team}"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        data = response.json()
        if "bbrefId" in data:
            return data["bbrefId"]  # Extract only the bbrefId
    print(f"Failed to fetch bbrefid for {first_initial} {last_name} on team {team}. Status: {response.status_code}")
    return None


def extract_pitcher_data(pitcher_str, is_sp):
    """Extracts individual pitcher data from string."""
    try:
        name, stats = pitcher_str.split(" ")
        first_initial, last_name = name.split(".")
        stats = stats.strip("()")
        parts = stats.split("-")

        # Extract days of rest and SP score
        days_of_rest = int(parts[0]) if parts[0].isdigit() else 0
        sp_score = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

        # Parse result suffixes
        results = {"W": 0, "H": 0, "L": 0, "Sv": 0, "Bsv": 0}
        for part in parts[1:]:
            for key in results.keys():
                if key in part:
                    results[key] = 1

        return {
            "firstInitial": first_initial,
            "lastName": last_name,
            "daysOfRest": days_of_rest,
            "SPscore": sp_score if is_sp else 0,
            **results
        }
    except Exception as e:
        print(f"Error extracting pitcher data: {e}")
        return None


def process_row(row, year, team):
    """Processes a single row of the table into a dictionary of game data."""
    try:
        # Debug: Print raw HTML for the row
        # print(f"Raw HTML: {row}")

        # Locate the team game number
        team_game_number_cell = row.find('td', {'data-stat': 'team_game_num'})
        team_game_number = team_game_number_cell.get_text(strip=True) if team_game_number_cell else None

        # Other row data extraction
        date_pitched_cell = row.find('td', {'data-stat': 'date_game'})
        date_pitched_url = date_pitched_cell.find('a')['href'] if date_pitched_cell and date_pitched_cell.find('a') else None
        date_pitched = parse_date(date_pitched_cell.get_text(strip=True), year) if date_pitched_cell else None

        opponent = row.find('td', {'data-stat': 'opp_ID'}).get_text(strip=True) if row.find('td', {'data-stat': 'opp_ID'}) else None
        result = row.find('td', {'data-stat': 'game_result'}).get_text(strip=True) if row.find('td', {'data-stat': 'game_result'}) else None
        innings_pitched = row.find('td', {'data-stat': 'IP'}).get_text(strip=True) if row.find('td', {'data-stat': 'IP'}) else None
        extra_innings = 1 if innings_pitched and float(innings_pitched) > 9.0 else 0
        home_or_away = row.find('td', {'data-stat': 'homeORaway'}).get_text(strip=True) if row.find('td', {'data-stat': 'homeORaway'}) else None
        ballpark = opponent if home_or_away == "@" else "Home"
        pitchers_number = row.find('td', {'data-stat': 'pitchers_number'}).get_text(strip=True) if row.find('td', {'data-stat': 'pitchers_number'}) else None
        umpire = row.find('td', {'data-stat': 'umpire_hp'}).get_text(strip=True) if row.find('td', {'data-stat': 'umpire_hp'}) else None
        pitchers_used = row.find('td', {'data-stat': 'pitchers_number_desc'}).get_text(strip=True) if row.find('td', {'data-stat': 'pitchers_number_desc'}) else None

        # Prepare dictionary
        game_data = {
            "teamGameNumber": int(team_game_number) if team_game_number else None,
            "datePitched": date_pitched,
            "opponent": opponent,
            "result": result,
            "extraInnings": extra_innings,
            "homeOrAway": ballpark,
            "pitchersNumber": int(pitchers_number) if pitchers_number else None,
            "umpire": umpire,
            "boxScoreUrl": f"https://www.baseball-reference.com{date_pitched_url}" if date_pitched_url else None,
            "pitchersUsed": [p.strip() for p in pitchers_used.split(",")] if pitchers_used else [],
            "team": team
        }

        return game_data
    except Exception as e:
        print(f"Error processing row: {e}")
        return None


def process_game_data(game_data, missing_pitchers):
    """Processes the game data for each pitcher and posts it."""
    print("Processing game data for:", game_data)

    # Get park factor
    park_factor = get_park_factor(game_data["team"] if game_data["homeOrAway"] == "Home" else game_data["opponent"])
    game_data["parkFactor"] = park_factor

    # Extract SP score from the first pitcher
    sp_score = None
    if game_data["pitchersUsed"]:
        first_pitcher_data = extract_pitcher_data(game_data["pitchersUsed"][0], is_sp=True)
        if first_pitcher_data:
            sp_score = first_pitcher_data["SPscore"]

    # Process each pitcher
    for order, pitcher in enumerate(game_data["pitchersUsed"], start=1):
        is_sp = (order == 1)  # First pitcher is the SP
        pitcher_data = extract_pitcher_data(pitcher, is_sp)
        if not pitcher_data:
            print(f"Skipping invalid pitcher data: {pitcher}")
            continue

        print("Extracted Pitcher Data:", pitcher_data)

        # Get bbrefid
        bbrefid = get_bbrefid(pitcher_data["firstInitial"], pitcher_data["lastName"], game_data["team"])
        if not bbrefid:
            pitcher_name = f"{pitcher_data['firstInitial']}.{pitcher_data['lastName']}"
            if pitcher_name not in missing_pitchers:
                missing_pitchers.append(pitcher_name)
            print(f"Skipping pitcher {pitcher_name}, bbrefid not found.")
            continue

        # Build payload
        payload = {
            "bbrefid": bbrefid,
            "teamGameNumber": game_data["teamGameNumber"],
            "name": f"{pitcher_data['firstInitial']}.{pitcher_data['lastName']}",
            "team": game_data["team"],
            "year": 2024,  # Hardcoded for now, can be adjusted
            "datePitched": game_data["datePitched"],
            "daysOfRest": pitcher_data["daysOfRest"],
            "pitcherOrder": order,
            "sPscore": pitcher_data["SPscore"],
            "win": pitcher_data["W"],
            "loss": pitcher_data["L"],
            "hold": pitcher_data["H"],
            "sv": pitcher_data["Sv"],
            "bsv": pitcher_data["Bsv"],
            "umpire": game_data["umpire"],
            "opponent": game_data["opponent"],
            "ballparkFactor": game_data["parkFactor"],
            "result": game_data["result"],
            "extraInnings": game_data["extraInnings"],
            "boxScoreUrl": game_data["boxScoreUrl"],
        }

        print("Payload being sent:", payload)
        post_bullpen_usage(payload)


def process_all_rows(table, year, team):
    """Processes all rows of the table."""
    rows = table.find_all('tr')
    print(f"Found {len(rows)} rows.")
    missing_pitchers = []
    for row in rows:
        game_data = process_row(row, year, team)
        if game_data:
            print("Processed Data:", game_data)  # Debugging output
            process_game_data(game_data, missing_pitchers)

    # Print missing pitchers at the end
    if missing_pitchers:
        print("Pitchers with missing bbrefid:", missing_pitchers)
    else:
        print("No missing pitchers!")

def post_bullpen_usage(payload):
    """Posts the payload to the BullpenUsage API."""
    url = "https://localhost:44346/api/BullpenUsage"
    print("Payload being sent:", payload)  # Debugging payload
    response = requests.post(url, json=payload, verify=False)
    if response.status_code == 201:
        print(f"Successfully posted data for {payload['bbrefid']}")
    else:
        print(f"Failed to post data for {payload['bbrefid']}. Status: {response.status_code}")

if __name__ == "__main__":
    # Fetch the table from Baseball-Reference
    team = "COL"
    year = 2024
    url = f"https://www.baseball-reference.com/teams/tgl.cgi?team={team}&t=p&year={year}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')

    table_div = soup.find('div', id='div_team_pitching_gamelogs')
    table = table_div.find('table', id='team_pitching_gamelogs') if table_div else None

    if table:
        process_all_rows(table, year, team)  # Pass team here
    else:
        print("Table not found.")

