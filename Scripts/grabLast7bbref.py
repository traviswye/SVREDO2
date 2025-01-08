import requests
from bs4 import BeautifulSoup
import statistics
from datetime import date
import json
import urllib3
import time

# Suppress HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_last_8_games_with_opponents(bbrefid, year):
    # Construct the URL
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={bbrefid}&t=b&year={year}"
    print(f"Attempting to scrape URL: {url}")

    # Fetch the page content
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve page for player {bbrefid} in year {year}. HTTP Status Code: {response.status_code}")
        return None

    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the game log table by looking for the specific div with id "div_batting_gamelogs"
    table_div = soup.find('div', id='div_batting_gamelogs')
    if not table_div:
        print(f"Game log table not found for player {bbrefid} in year {year}")
        return None

    # Extract the actual table from the div
    table = table_div.find('table')
    if not table:
        print(f"Table element not found within the game log div for player {bbrefid} in year {year}")
        return None

    # Process the table rows
    rows = table.find_all('tr', class_=lambda x: x != 'thead')  # Ignore header rows
    if len(rows) < 2:
        print(f"Not enough rows to process for player {bbrefid}")
        return None

    # Get the last 8 rows, with the 8th being the season totals
    last_8_rows = rows[-8:]
    season_totals = last_8_rows[-1]  # The season totals row
    last_7_rows = last_8_rows[:-1]

    # Initialize all aggregate variables
    aggregate = {
        'PA': 0, 'AB': 0, 'R': 0, 'H': 0, '2B': 0, '3B': 0, 'HR': 0, 'RBI': 0,
        'BB': 0, 'IBB': 0, 'SO': 0, 'HBP': 0, 'SH': 0, 'SF': 0, 'ROE': 0,
        'GDP': 0, 'SB': 0, 'CS': 0, 'WPA': 0, 'cWPA': 0, 'RE24': 0,
        'DFS_DK': 0, 'DFS_FD': 0
    }
    BOP_list = []
    aLI_list = []
    acLI_list = []

    # Variables to track all rows
    away_opp_ids = []
    home_counter = 0

    # Variables to track last 7 rows
    away_opp_ids_last7 = []
    home_counter_last7 = 0
    # Initialize homeTeam with a default value
    homeTeam = "TODO"

    # Process every row in the table
    for row in rows:
        cells = row.find_all('td')
        if not cells:
            continue

        # Extract relevant columns
        cell_data = {cell['data-stat']: cell.get_text(strip=True) for cell in cells}
        team_homeORaway = cell_data.get('team_homeORaway', '')
        opp_ID = cell_data.get('opp_ID', '')

        # Check home or away and update the appropriate list/counter
        if team_homeORaway == '@':
            away_opp_ids.append(opp_ID)  # Add opponent ID to the list
        else:
            home_counter += 1  # Increment the counter for home games

    # Process the last 7 rows for aggregation
    game_count = 0  # Initialize the game count
    for row in last_7_rows:
        cells = row.find_all('td')
        if not cells:
            continue

        game_count += 1  # Increment the game count for each game processed

        # Create a dictionary from data-stat attribute to cell value
        cell_data = {cell['data-stat']: cell.get_text(strip=True) for cell in cells}
        # Extract team_ID with a fallback to "TODO"
        homeTeam = cell_data.get('team_ID', 'TODO') if cell_data.get('team_ID') else 'TODO'

        # Update aggregate variables for PA to CS
        stats = {
            'PA': 'PA', 'AB': 'AB', 'R': 'R', 'H': 'H', '2B': '2B', '3B': '3B', 
            'HR': 'HR', 'RBI': 'RBI', 'BB': 'BB', 'IBB': 'IBB', 'SO': 'SO', 
            'HBP': 'HBP', 'SH': 'SH', 'SF': 'SF', 'ROE': 'ROE', 'GDP': 'GDP', 
            'SB': 'SB', 'CS': 'CS'
        }

        for key, stat in stats.items():
            value = int(cell_data.get(stat, '0') or 0)
            aggregate[key] += value

        # Update additional aggregate variables
        try:
            # Remove percentage symbols and convert to float
            cWPA_text = cell_data.get('cwpa_bat', '0').replace('%', '')
            cWPA = float(cWPA_text or 0.0) / 100  # Convert from percentage to decimal

            aLI_text = cell_data.get('leverage_index_avg', '0').replace('%', '')
            aLI = float(aLI_text or 0.0)

            acLI_text = cell_data.get('cli_avg', '0').replace('%', '')
            acLI = float(acLI_text or 0.0)

            WPA = float(cell_data.get('wpa_bat', '0') or 0.0)
            RE24 = float(cell_data.get('re24_bat', '0') or 0.0)
            DFS_DK = float(cell_data.get('draftkings_points', '0') or 0.0)
            DFS_FD = float(cell_data.get('fanduel_points', '0') or 0.0)

            # Update aggregate totals
            aggregate['WPA'] += WPA
            aggregate['cWPA'] += cWPA
            aggregate['RE24'] += RE24
            aggregate['DFS_DK'] += DFS_DK
            aggregate['DFS_FD'] += DFS_FD

            # Collect lists for mode and averaging calculations
            aLI_list.append(aLI)
            acLI_list.append(acLI)
            BOP_list.append(int(cell_data.get('batting_order_position', '0') or 0))

            # Check home or away for last 7 rows
            if cell_data.get('team_homeORaway', '') == '@':
                away_opp_ids_last7.append(cell_data.get('opp_ID', ''))
            else:
                home_counter_last7 += 1


        except ValueError as e:
            print(f"Error parsing value in row: {e}")

    # Calculate aggregated stats (BA, OBP, SLG, OPS)
    BA = aggregate['H'] / aggregate['AB'] if aggregate['AB'] > 0 else 0.0
    OBP = (aggregate['H'] + aggregate['BB'] + aggregate['HBP']) / (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) if (aggregate['AB'] + aggregate['BB'] + aggregate['HBP'] + aggregate['SF']) > 0 else 0.0
    SLG = (aggregate['H'] + (2 * aggregate['2B']) + (3 * aggregate['3B']) + (4 * aggregate['HR'])) / aggregate['AB'] if aggregate['AB'] > 0 else 0.0
    OPS = OBP + SLG

    # Get the most common BOP
    try:
        BOP = statistics.mode(BOP_list) if BOP_list else 0
    except statistics.StatisticsError:
        BOP = 0  # Handle cases where no mode is found

    # Calculate averages for aLI, acLI
    aLI = sum(aLI_list) / len(aLI_list) if aLI_list else 0.0
    acLI = sum(acLI_list) / len(acLI_list) if acLI_list else 0.0

    # Get today's date in yyyy-mm-dd format
    today = date.today().isoformat()

    # Print aggregate stats
    aggregated_data = {
        'G': game_count,
        'PA': aggregate['PA'],
        'AB': aggregate['AB'],
        'R': aggregate['R'],
        'H': aggregate['H'],
        '2B': aggregate['2B'],
        '3B': aggregate['3B'],
        'HR': aggregate['HR'],
        'RBI': aggregate['RBI'],
        'BB': aggregate['BB'],
        'IBB': aggregate['IBB'],
        'SO': aggregate['SO'],
        'HBP': aggregate['HBP'],
        'SH': aggregate['SH'],
        'SF': aggregate['SF'],
        'ROE': aggregate['ROE'],
        'GDP': aggregate['GDP'],
        'SB': aggregate['SB'],
        'CS': aggregate['CS'],
        'BA': round(BA, 3),
        'OBP': round(OBP, 3),
        'SLG': round(SLG, 3),
        'OPS': round(OPS, 3),
        'BOP': BOP,
        'aLI': round(aLI, 8),
        'WPA': round(aggregate['WPA'], 3),
        'acLI': round(acLI, 8),
        'cWPA': f"{round(aggregate['cWPA'] * 100, 2)}%",  # Display cWPA as percentage
        'RE24': round(aggregate['RE24'], 2),
        'DFS_DK': round(aggregate['DFS_DK'], 1),
        'DFS_FD': round(aggregate['DFS_FD'], 1),
        'date': today
    }

    # Extract the last row (season totals)
    season_totals = rows[-1]
    season_totals_data = [cell.get_text(strip=True) for cell in season_totals.find_all('td')]

        # Extract the second-to-last row for SingleGame payload
    single_game_row = rows[-2]  # Second-to-last row
    single_game_data = [cell.get_text(strip=True) for cell in single_game_row.find_all('td')]

    single_game_data2= None
    # print(single_game_data[2])
    if '(' in single_game_data[2]:
        single_game_row2 = rows[-3]  # third-to-last row as there was a double header
        single_game_data2 = [cell.get_text(strip=True) for cell in single_game_row2.find_all('td')]
    # Extract data from index 8 to len(season_totals_data) - 2
    subset_season_totals = season_totals_data[8:-1]
    # print(single_game_data)
    # print(single_game_data2)
    # print("Season Totals (Subset):", subset_season_totals)

    # print("Season Totals:", subset_season_totals)

    # print(f"Aggregated stats for player {bbrefid}: {aggregated_data}")
    # print(f"Season Totals: ", subset_season_totals)
    # print("-------------------------------------------------------------------------------")
    # print(f"Last 7 games - Home count: {home_counter_last7}, Away count: {len(away_opp_ids_last7)}, Opponent IDs: {away_opp_ids_last7}")
    # print(f"Total rows - Home count: {home_counter-1}, Away count: {len(away_opp_ids)}, Opponent IDs: {away_opp_ids}")

    return single_game_data, single_game_data2, homeTeam, subset_season_totals, aggregated_data, away_opp_ids, home_counter, home_counter_last7, away_opp_ids_last7


def convert_date(month_day):
    # Map month abbreviations to their numeric values
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }

    # Remove anything starting from '('
    month_day = month_day.split('(')[0].strip()

    # Split the input into month and day
    parts = month_day.split()
    if len(parts) != 2:
        return None  # Handle cases where the format is unexpected

    month_abbr, day = parts
    month = month_map.get(month_abbr)

    if not month:
        return None  # Handle invalid month abbreviations

    # Add leading zero to the day if necessary
    day = day.zfill(2)

    # Use the current year
    current_year = date.today().year

    # Combine into the desired format
    return f"{current_year}-{month}-{day}"


# New function to handle normalization and posting
def process_and_post_trailing_gamelogs(bbrefid, year):
    # Scrape data
    single_game_data, single_game_data2, homeTeam, subset_season_totals, aggregated_data, away_opp_ids, home_counter, home_counter_last7, away_opp_ids_last7 = scrape_last_8_games_with_opponents(bbrefid, year)
    # print(f"HOMETEAM{homeTeam}")
    # Prepare payloads for normalization API
    payload = {
        "bbrefId": bbrefid,
        "oppIds": away_opp_ids,
        "homeGames": home_counter - 1
    }
    payload2 = {
        "bbrefId": bbrefid,
        "oppIds": away_opp_ids_last7,
        "homeGames": home_counter_last7
    }
    payload3 = {
        "bbrefId": bbrefid,
        "oppIds": [single_game_data[5]],
        "homeGames": 1 if single_game_data[4] == '' else 0
    }

    # Normalize ParkFactors API endpoint
    normalize_api_url = "https://localhost:44346/api/ParkFactors/normalize"
    trailing_gamelog_api_url = "https://localhost:44346/api/TrailingGameLogSplits"

    try:
        response = requests.post(normalize_api_url, json=payload, verify=False)
        response.raise_for_status()
        api_response = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while calling normalize API for full season: {e}")
        print(f"{payload}")
        return

    try:
        response2 = requests.post(normalize_api_url, json=payload2, verify=False)
        response2.raise_for_status()
        api_response2 = response2.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while calling normalize API for last 7 games: {e}")
        print(f"{payload2}")
        return

    try:
        response3 = requests.post(normalize_api_url, json=payload3, verify=False)
        response3.raise_for_status()
        api_response3 = response3.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while calling normalize API for last 1 game: {e}")
        print(f"{payload3}")
        return

    # Prepare JSON payloads for TrailingGameLogSplits API
    json_payloadL7 = {
        "bbrefId": bbrefid,
        "team": homeTeam,  # Replace with appropriate team name
        "split": "Last7G",
        "splitParkFactor": api_response2["totalParkFactor"],
        "g": aggregated_data["G"],
        "pa": aggregated_data["PA"],
        "ab": aggregated_data["AB"],
        "r": aggregated_data["R"],
        "h": aggregated_data["H"],
        "doubles": aggregated_data["2B"],
        "triples": aggregated_data["3B"],
        "hr": aggregated_data["HR"],
        "rbi": aggregated_data["RBI"],
        "bb": aggregated_data["BB"],
        "ibb": aggregated_data["IBB"],
        "so": aggregated_data["SO"],
        "hbp": aggregated_data["HBP"],
        "sh": aggregated_data["SH"],
        "sf": aggregated_data["SF"],
        "roe": aggregated_data["ROE"],
        "gdp": aggregated_data["GDP"],
        "sb": aggregated_data["SB"],
        "cs": aggregated_data["CS"],
        "ba": aggregated_data["BA"],
        "obp": aggregated_data["OBP"],
        "slg": aggregated_data["SLG"],
        "ops": aggregated_data["OPS"],
        "bop": aggregated_data["BOP"],
        "ali": aggregated_data["aLI"],
        "wpa": aggregated_data["WPA"],
        "acLI": aggregated_data["acLI"],
        "cwpa": aggregated_data["cWPA"],
        "rE24": aggregated_data["RE24"],
        "dfsDk": aggregated_data["DFS_DK"],
        "dfsFd": aggregated_data["DFS_FD"],
        "homeGames": home_counter_last7,
        "awayGames": len(away_opp_ids_last7),
        "homeParkFactor": api_response2["homeParkFactor"],
        "awayParkFactorAvg": api_response2["avgAwayParkFactor"],
        "dateUpdated": date.today().isoformat()
    }

    json_payloadTOT = {
        "bbrefId": bbrefid,
        "team": homeTeam,  # Replace with appropriate team name
        "split": "Season",
        "splitParkFactor": api_response["totalParkFactor"],
        "g": len(away_opp_ids) + home_counter - 1,
        "pa": subset_season_totals[0],
        "ab": subset_season_totals[1],
        "r": subset_season_totals[2],
        "h": subset_season_totals[3],
        "doubles": subset_season_totals[4],
        "triples": subset_season_totals[5],
        "hr": subset_season_totals[6],
        "rbi": subset_season_totals[7],
        "bb": subset_season_totals[8],
        "ibb": subset_season_totals[9],
        "so": subset_season_totals[10],
        "hbp": subset_season_totals[11],
        "sh": subset_season_totals[12],
        "sf": subset_season_totals[13],
        "roe": subset_season_totals[14],
        "gdp": subset_season_totals[15],
        "sb": subset_season_totals[16],
        "cs": subset_season_totals[17],
        "ba": subset_season_totals[18],
        "obp": subset_season_totals[19],
        "slg": subset_season_totals[20],
        "ops": subset_season_totals[21],
        "bop": subset_season_totals[22] if subset_season_totals[22] else -1,  # Set to -1 if null or empty
        "ali": subset_season_totals[23],
        "wpa": subset_season_totals[24],
        "acLI": subset_season_totals[25],
        "cwpa": subset_season_totals[26],
        "rE24": subset_season_totals[27],
        "dfsDk": subset_season_totals[28],
        "dfsFd": subset_season_totals[29],
        "homeGames": home_counter - 1,
        "awayGames": len(away_opp_ids),
        "homeParkFactor": api_response["homeParkFactor"],
        "awayParkFactorAvg": api_response["avgAwayParkFactor"],
        "dateUpdated": date.today().isoformat()
    }

    # Assuming single_game_data[2] contains the value '2024-09-29.NYA202409290'

    converted_date = convert_date(single_game_data[2])
    # print(converted_date)  # Outputs: 2024-09-20

    json_payloadSG = {
        "bbrefId": bbrefid,
        "team": homeTeam,  # Replace with appropriate team name
        "split": "SingleGame",
        "splitParkFactor": api_response3["totalParkFactor"],
        "g": 1,
        "pa": single_game_data[8],
        "ab": single_game_data[9],
        "r": single_game_data[10],
        "h": single_game_data[11],
        "doubles": single_game_data[12],
        "triples": single_game_data[13],
        "hr": single_game_data[14],
        "rbi": single_game_data[15],
        "bb": single_game_data[16],
        "ibb": single_game_data[17] if single_game_data[17] else 0,
        "so": single_game_data[18],
        "hbp": single_game_data[19],
        "sh": single_game_data[20],
        "sf": single_game_data[21] if single_game_data and single_game_data[21] else 0,
        "roe": single_game_data[22],
        "gdp": single_game_data[23] if single_game_data and single_game_data[23] else 0,
        "sb": single_game_data[24],
        "cs": single_game_data[25],
        "ba": single_game_data[26],
        "obp": single_game_data[27],
        "slg": single_game_data[28],
        "ops": single_game_data[29],
        "bop": single_game_data[30] if single_game_data[30] else -1,  # Set to -1 if null or empty
        "ali": single_game_data[31] if single_game_data[31] else 0.0,
        "wpa": single_game_data[32] if single_game_data[32] else 0.0,
        "acLI": single_game_data[33] if single_game_data[33] else 0.0,
        "cwpa": str(single_game_data[34]) if single_game_data and single_game_data[34].strip() else "0%",
        "rE24": single_game_data[35] if single_game_data[35] else 0.0,
        "dfsDk": single_game_data[36],
        "dfsFd": single_game_data[37],
        "homeGames": 1 if single_game_data[4] == '' else 0,
        "awayGames": 1 if single_game_data[4] == '@' else 0,
        "homeParkFactor": api_response3["homeParkFactor"],
        "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
        "dateUpdated": converted_date
    }

    if single_game_data2 is not None:
        json_payloadSG2 = {
        "bbrefId": bbrefid,
        "team": homeTeam,  # Replace with appropriate team name
        "split": "SingleGame2",
        "splitParkFactor": api_response3["totalParkFactor"],
        "g": 1,
        "pa": single_game_data2[8],
        "ab": single_game_data2[9],
        "r": single_game_data2[10],
        "h": single_game_data2[11],
        "doubles": single_game_data2[12],
        "triples": single_game_data2[13],
        "hr": single_game_data2[14],
        "rbi": single_game_data2[15],
        "bb": single_game_data2[16],
        "ibb": single_game_data2[17] if single_game_data2[17] else 0,
        "so": single_game_data2[18],
        "hbp": single_game_data2[19],
        "sh": single_game_data2[20],
        "sf": single_game_data2[21] if single_game_data2 and single_game_data2[21] else 0,
        "roe": single_game_data2[22],
        "gdp": single_game_data2[23] if single_game_data2 and single_game_data2[23] else 0,
        "sb": single_game_data2[24],
        "cs": single_game_data2[25],
        "ba": single_game_data2[26],
        "obp": single_game_data2[27],
        "slg": single_game_data2[28],
        "ops": single_game_data2[29],
        "bop": single_game_data2[30] if single_game_data2 and single_game_data2[30] else -1,  # Set to -1 if null or empty
        "ali": single_game_data2[31] if single_game_data2 and single_game_data2[31] else 0.0,
        "wpa": single_game_data2[32] if single_game_data2 and single_game_data2[32] else 0.0,
        "acLI": single_game_data2[33] if single_game_data2 and single_game_data2[33] else 0.0,
        "cwpa": str(single_game_data2[34]) if single_game_data2 and single_game_data2[34].strip() else "0%",
        "rE24": single_game_data2[35] if single_game_data2 and single_game_data2[35] else 0.0,
        "dfsDk": single_game_data2[36],
        "dfsFd": single_game_data2[37],
        "homeGames": 1 if single_game_data2[4] == '' else 0,
        "awayGames": 1 if single_game_data2[4] == '@' else 0,
        "homeParkFactor": api_response3["homeParkFactor"],
        "awayParkFactorAvg": api_response3["avgAwayParkFactor"],
        "dateUpdated": converted_date
        }

    # Post data to TrailingGameLogSplits API
    try:
        responseL7 = requests.post(trailing_gamelog_api_url, json=json_payloadL7, verify=False)
        responseL7.raise_for_status()
        print(f"Successfully posted Last7G data: {responseL7.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting Last7G data: {e}")

    try:
        responseTOT = requests.post(trailing_gamelog_api_url, json=json_payloadTOT, verify=False)
        responseTOT.raise_for_status()
        print(f"Successfully posted Season data: {responseTOT.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting Season data: {e}")

    try:
        responseSG = requests.post(trailing_gamelog_api_url, json=json_payloadSG, verify=False)
        responseSG.raise_for_status()
        if single_game_data2 is not None:
            responseSG = requests.post(trailing_gamelog_api_url, json=json_payloadSG2, verify=False)
            responseSG.raise_for_status()
        print(f"Successfully posted SingleGame data: {responseTOT.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting SingleGame data: {e}")
        print(json_payloadSG)        
        print(json_payloadSG2)

# # Main block
# if __name__ == "__main__":
#     bbrefid = "lindofr01"
#     process_and_post_trailing_gamelogs(bbrefid, 2024)


    # Define the input file
input_file = "bbrefids.txt"

# Main block
if __name__ == "__main__":
    try:
        # Open the file and read bbrefids line by line
        with open(input_file, "r", encoding="utf-8") as infile:
            bbrefids = [line.strip() for line in infile if line.strip()]  # Remove empty lines

        # Loop through each bbrefid and process it
        for bbrefid in bbrefids:
            process_and_post_trailing_gamelogs(bbrefid, 2024)
            time.sleep(2.5)  # Pause for 2.5 seconds between calls

        print("Processing complete.")
    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found. Please ensure it exists in the same directory.")
    except Exception as e:
        print(f"An error occurred: {e}")