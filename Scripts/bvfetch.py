import requests
from bs4 import BeautifulSoup

# Disable SSL warnings for localhost testing (not recommended for production)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API endpoints
mlbplayer_all_url = "https://localhost:44346/api/MLBPlayer/all"
player_lookup_post_url = "https://localhost:44346/api/playerlookup"

# Baseball Savant URL
savant_url = "https://baseballsavant.mlb.com/statcast_search"

def fetch_all_players():
    try:
        response = requests.get(mlbplayer_all_url, verify=False)
        response.raise_for_status()
        players = response.json()
        print(f"Fetched {len(players)} players from the API.")
        return players
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []

def scrape_savant_players():
    try:
        response = requests.get(savant_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        def parse_options(select_id):
            options = soup.select(f"#{select_id} option")
            player_dicts = []

            for option in options:
                value = option.get("value")
                data_last_first = option.get("data-last-first", "")
                data_first_last = option.get("data-first-last", "")
                text = option.text.strip()

                if "[" in text and "]" in text:
                    year_team, player_name = text.split("]", 1)
                    year_team = year_team.strip("[]")
                    year, team = year_team.split("-", 1)
                else:
                    year, team = None, None

                player_dict = {
                    "PlayerName": data_first_last.title(),
                    "BvID": int(value) if value and value.isdigit() else None,
                    "Year": int(year) if year and year.isdigit() else None,
                    "Team": team,
                }
                player_dicts.append(player_dict)

            return player_dicts

        # Parse batters and pitchers
        batters = parse_options("batters_lookup")
        pitchers = parse_options("pitchers_lookup")

        print(f"Parsed {len(batters)} batters and {len(pitchers)} pitchers.")
        return batters, pitchers

    except requests.exceptions.RequestException as e:
        print(f"Error fetching HTML from Baseball Savant: {e}")
        return [], []

def post_player(player_data):
    try:
        response = requests.post(player_lookup_post_url, json=player_data, verify=False)
        response.raise_for_status()
        print(f"Posted player: {player_data['fullName']}")
    except requests.exceptions.RequestException as e:
        print(f"Error posting player {player_data['fullName']}: {e}")

def main():
    # Fetch all players from API
    all_players = fetch_all_players()

    # Scrape Baseball Savant for batters and pitchers
    batters, pitchers = scrape_savant_players()

    # Combine batters and pitchers into one list
    savant_players = {p["PlayerName"].lower(): p for p in batters + pitchers}

    # Lists to track unmatched players
    unmatched_all_players = []
    unmatched_savant_players = list(savant_players.keys())

    # Process and match players
    for player in all_players:
        bbref_id = player["bbrefId"]
        full_name = player["fullName"].lower()
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        if full_name in savant_players:
            matched_player = savant_players[full_name]
            player_data = {
                "bbrefId": bbref_id,
                "bsID": matched_player["BvID"],
                "firstName": first_name,
                "lastName": last_name,
                "fullName": full_name.title(),
                "team": matched_player["Team"],
                "year": matched_player["Year"],
            }
            post_player(player_data)
            
            # Safely remove from unmatched_savant_players if it exists
            if full_name in unmatched_savant_players:
                unmatched_savant_players.remove(full_name)
        else:
            unmatched_all_players.append(bbref_id)

    print("\nUnmatched Players from mlbplayer/all:")
    print(unmatched_all_players)

    print("\nUnmatched Players from Baseball Savant:")
    print(unmatched_savant_players)

if __name__ == "__main__":
    main()
