import requests
from bs4 import BeautifulSoup
import datetime
import urllib3

# Suppress HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the API endpoints
API_HITTING_ENDPOINT = "https://localhost:44346/api/TeamTotalBattingTracking"
API_PITCHING_ENDPOINT = "https://localhost:44346/api/TeamTotalPitchingTracking"

def scrape_batting_data(url, year):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        league = "AL" if "AL" in url else "NL"
        table = soup.find("table", id="teams_standard_batting")
        if not table:
            print(f"No table found on URL: {url}")
            return []

        headers = [th.get("data-stat", th.text.strip()) for th in table.find("thead").find_all("th")]
        print(f"Headers found: {headers}")

        rows = table.find("tbody").find_all("tr")
        print(f"Number of rows found: {len(rows)}")

        data = []
        for row in rows:
            if not row.find("td") and not row.find("th", {"data-stat": "team_name"}):
                continue

            team_name_element = row.find("th", {"data-stat": "team_name"})
            team_name = team_name_element.text.strip() if team_name_element else "Unknown"

            if team_name == "League Average":
                team_name = f"{league} Average"

            cells = row.find_all("td")
            row_data = {headers[idx + 1]: cell.text.strip() for idx, cell in enumerate(cells)}

            if "2B" in row_data:
                row_data["Doubles"] = row_data.pop("2B")
            if "3B" in row_data:
                row_data["Triples"] = row_data.pop("3B")

            row_data["TeamName"] = team_name
            row_data["Year"] = year
            row_data["DateAdded"] = datetime.datetime.now().strftime("%Y-%m-%d")

            print(row_data)
            post_to_api(row_data, API_HITTING_ENDPOINT)

            data.append(row_data)

        return data

    except Exception as e:
        print(f"Error occurred while scraping {url}: {e}")
        return []

def scrape_pitching_data(url, year):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        league = "AL" if "AL" in url else "NL"
        table = soup.find("table", id="teams_standard_pitching")
        if not table:
            print(f"No table found on URL: {url}")
            return []

        table_headers = [th.get("data-stat", th.text.strip()) for th in table.find("thead").find_all("th")]
        print(f"Headers found: {table_headers}")

        rows = table.find("tbody").find_all("tr")
        print(f"Number of rows found: {len(rows)}")

        data = []
        for row in rows:
            if not row.find("td") and not row.find("th", {"data-stat": "team_name"}):
                continue

            team_name_element = row.find("th", {"data-stat": "team_name"})
            team_name = team_name_element.text.strip() if team_name_element else "Unknown"

            if team_name == "League Average":
                team_name = f"{league} Average"

            cells = row.find_all("td")
            row_data = {table_headers[idx + 1]: cell.text.strip() for idx, cell in enumerate(cells)}

            # Map all fields to EF columns
            key_mapping = {
                "Tm": "TeamName",
                "pitchers_used": "PitchersUsed",
                "age_pitch": "PAge",
                "runs_allowed_per_game": "RAG",
                "W": "W",
                "L": "L",
                "win_loss_perc": "WLPercentage",
                "earned_run_avg": "ERA",
                "G": "G",
                "GS": "GS",
                "GF": "GF",
                "CG": "CG",
                "SHO_team": "TSho",
                "SHO_cg": "CSho",
                "SV": "SV",
                "IP": "IP",
                "H": "H",
                "R": "R",
                "ER": "ER",
                "HR": "HR",
                "BB": "BB",
                "IBB": "IBB",
                "SO": "SO",
                "HBP": "HBP",
                "BK": "BK",
                "WP": "WP",
                "batters_faced": "BF",
                "earned_run_avg_plus": "ERAPlus",
                "fip": "FIP",
                "whip": "WHIP",
                "hits_per_nine": "H9",
                "home_runs_per_nine": "HR9",
                "bases_on_balls_per_nine": "BB9",
                "strikeouts_per_nine": "SO9",
                "strikeouts_per_base_on_balls": "SOW",
                "LOB": "LOB"
            }

            # Apply mapping
            mapped_data = {key_mapping.get(k, k): v for k, v in row_data.items()}

            # Add remaining required keys
            mapped_data["TeamName"] = team_name
            mapped_data["Year"] = year
            mapped_data["DateAdded"] = datetime.datetime.now().strftime("%Y-%m-%d")

            # Ensure all keys exist in the payload
            for column in key_mapping.values():
                if column not in mapped_data:
                    mapped_data[column] = None  # Add missing keys with `None`

            print(mapped_data)
            post_to_api(mapped_data, API_PITCHING_ENDPOINT)

            data.append(mapped_data)

        return data

    except Exception as e:
        print(f"Error occurred while scraping {url}: {e}")
        return []



def post_to_api(row_data, endpoint):
    try:
        response = requests.post(endpoint, json=row_data, verify=False)
        if response.status_code == 201:
            print(f"Successfully posted data for {row_data['TeamName']} (Year: {row_data['Year']})")
        else:
            print(f"Failed to post data for {row_data['TeamName']} (Year: {row_data['Year']}): {response.text}")
    except Exception as e:
        print(f"Error while posting data to API: {e}")


# URLs to scrape
hitting_urls = [
    "https://www.baseball-reference.com/leagues/NL/2024-standard-batting.shtml",
    "https://www.baseball-reference.com/leagues/AL/2024-standard-batting.shtml"
]
pitching_urls = [
    "https://www.baseball-reference.com/leagues/AL/2024-standard-pitching.shtml",
    "https://www.baseball-reference.com/leagues/NL/2024-standard-pitching.shtml"
]

# Scrape hitting data
for url in hitting_urls:
    year = 2024
    print(f"Scraping hitting data for {url}...")
    scrape_batting_data(url, year)

# Scrape pitching data
for url in pitching_urls:
    year = 2024
    print(f"Scraping pitching data for {url}...")
    scrape_pitching_data(url, year)
