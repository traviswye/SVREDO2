import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from datetime import datetime
import urllib3

# Suppress only the insecure request warning for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Path to your ChromeDriver
chrome_driver_path = "C:/buns/tw/SVREDO2/prodScripts/SeleniumVersions/chromedriver.exe"
# chrome_driver_path = "C:/Users/travi/source/repos/SVREDO2/prodScripts/SeleniumVersions/chromedriver.exe"


# Set Chrome options to run headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Initialize the Selenium WebDriver (Chrome in this case)
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Load the webpage
url = "https://stathead.com/baseball/versus-finder.cgi?request=1&match=versus_today"
driver.get(url)

# Wait for the page to fully load
time.sleep(6)

# Parse the page source with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Close the WebDriver after the page is loaded
driver.quit()

# Try finding the table by id
table = soup.find('table', {'id': 'stats'})
if not table:
    print("Table not found.")
    exit()

# Extract the rows from the table (skip the header row)
rows = table.find_all('tr', {'data-row': True})

# List to store the data
hitter_vs_pitcher_data = []

# Function to safely extract integer or float values
def extract_stat(row, stat_name, data_type=int):
    element = row.find('td', {'data-stat': stat_name})
    if element:
        text = element.text.strip()
        if data_type == int:
            return int(text or 0)
        elif data_type == float:
            return float(text or 0)
    return 0

# Iterate over the rows and extract each cell based on 'data-stat' attributes
for row in rows:
    pitcher_link_tag = row.find('td', {'data-stat': 'name_display_p'})
    hitter_link_tag = row.find('td', {'data-stat': 'name_display_b'})
    details_link_tag = row.find('td', {'data-stat': 'details_pa'})

    if pitcher_link_tag and pitcher_link_tag.find('a'):
        pitcher_link = pitcher_link_tag.find('a')['href']
        pitcher = pitcher_link.split('/')[-1].split('.')[0]
    else:
        pitcher = "Unknown"

    if hitter_link_tag and hitter_link_tag.find('a'):
        hitter_link = hitter_link_tag.find('a')['href']
        hitter = hitter_link.split('/')[-1].split('.')[0]
    else:
        hitter = "Unknown"

    # Extract the correct matchup URL
    if details_link_tag and details_link_tag.find('a'):
        matchup_url = "https://stathead.com/baseball/" + details_link_tag.find('a')['href']
    else:
        matchup_url = url  # Fallback to the main URL if not found

    # Create a dictionary for each row
    data = {
        "pitcher": pitcher,
        "hitter": hitter,
        "pa": extract_stat(row, 'b_pa', int),
        "hits": extract_stat(row, 'b_h', int),
        "hr": extract_stat(row, 'b_hr', int),
        "rbi": extract_stat(row, 'b_rbi', int),
        "bb": extract_stat(row, 'b_bb', int),
        "so": extract_stat(row, 'b_so', int),
        "ba": extract_stat(row, 'b_batting_avg', float),
        "obp": extract_stat(row, 'b_onbase_perc', float),
        "slg": extract_stat(row, 'b_slugging_perc', float),
        "ops": extract_stat(row, 'b_onbase_plus_slugging', float),
        "sh": extract_stat(row, 'b_sh', int),
        "sf": extract_stat(row, 'b_sf', int),
        "ibb": extract_stat(row, 'b_ibb', int),
        "hbp": extract_stat(row, 'b_hbp', int),
        "matchupURL": matchup_url  # Use the correct URL for the matchup
    }

    hitter_vs_pitcher_data.append(data)

# Step 1: Fetch Game Previews for Today's Date (Corrected Date Format)
today = datetime.now().strftime('%y-%m-%d')  # Changed to 'DD-MM-YY'
game_previews_url = f"https://localhost:44346/api/GamePreviews/{today}"

try:
    game_previews_response = requests.get(game_previews_url, verify=False)  # Added verify=False here
    game_previews_response.raise_for_status()
    game_previews = game_previews_response.json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching game previews: {e}")
    exit()

# Step 2: Match pitchers to game previews and send data to the API
hitter_vs_pitcher_api_url = "https://localhost:44346/api/HitterVsPitcher"

for hitter_vs_pitcher in hitter_vs_pitcher_data:
    pitcher_id = hitter_vs_pitcher["pitcher"]

    # Match the pitcher to a game preview
    matched_game_preview = next(
        (game for game in game_previews if game["homePitcher"] == pitcher_id or game["awayPitcher"] == pitcher_id), None
    )

    if matched_game_preview:
        # Set the gamePreviewID in the payload
        hitter_vs_pitcher["gamePreviewID"] = matched_game_preview["id"]
    else:
        hitter_vs_pitcher["gamePreviewID"] = 0  # Default to 0 if no match is found

    # Send POST request to HitterVsPitcher API
    try:
        response = requests.post(hitter_vs_pitcher_api_url, json=hitter_vs_pitcher, verify=False, headers={
            'accept': 'text/plain',
            'Content-Type': 'application/json'
        })
        response.raise_for_status()
        print(f"Successfully added data for pitcher {pitcher_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending data for pitcher {pitcher_id}: {e}")
