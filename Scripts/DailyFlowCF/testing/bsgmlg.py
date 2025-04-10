import csv
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OUTPUT_DIR = "output"
SEASON = "2025"  # The season you want to scrape data for
SLEEP_TIME = 2  # Time to wait between requests to avoid rate limiting
CHROME_DRIVER_PATH = "C:/buns/tw/SVREDO2/prodScripts/SeleniumVersions/chromedriver.exe"  # Path to your ChromeDriver
WAIT_TIMEOUT = 10  # Maximum seconds to wait for elements to load

# Dictionary to manually map bbrefId to player info
# Format: "bbrefId": {"bsId": 123456, "firstName": "First", "lastName": "Last", "team": "TEA"}
PLAYER_MAPPING = {
    "rodrie01": {"bsId": 660730, "firstName": "Elvin", "lastName": "Rodriguez", "team": "LAA"},
    "abbotan01": {"bsId": 671096, "firstName": "Andrew", "lastName": "Abbott", "team": "CIN"},
    "anderty01": {"bsId": 542881, "firstName": "Tyler", "lastName": "Anderson", "team": "LAA"},
    "bassich01": {"bsId": 605135, "firstName": "Chris", "lastName": "Bassitt", "team": "TOR"},
    "bazsh01": {"bsId": 669358, "firstName": "Shane", "lastName": "Baz", "team": "TB"},
    "birdsha01": {"bsId": 806185, "firstName": "Hayden", "lastName": "Birdsong", "team": "SF"},
    "bradlta01": {"bsId": 671737, "firstName": "Taj", "lastName": "Bradley", "team": "TB"},
    "verlaju01": {"bsId": 434378, "firstName": "Justin", "lastName": "Verlander", "team": "HOU"},
    "webblo01": {"bsId": 657277, "firstName": "Logan", "lastName": "Webb", "team": "SF"},
    "skubata01": {"bsId": 669373, "firstName": "Tarik", "lastName": "Skubal", "team": "DET"},
    "glasnty01": {"bsId": 607192, "firstName": "Tyler", "lastName": "Glasnow", "team": "LAD"},
    "grayso01": {"bsId": 543243, "firstName": "Sonny", "lastName": "Gray", "team": "STL"},
    "alcansa01": {"bsId": 645261, "firstName": "Sandy", "lastName": "Alcantara", "team": "MIA"},
    "skenepa01": {"bsId": 694973, "firstName": "Paul", "lastName": "Skenes", "team": "PIT"},
    "lugose01": {"bsId": 607625, "firstName": "Seth", "lastName": "Lugo", "team": "KC"},
    "oberba01": {"bsId": 641927, "firstName": "Bailey", "lastName": "Ober", "team": "MIN"},
    "severlu01": {"bsId": 622663, "firstName": "Luis", "lastName": "Severino", "team": "NYM"},
    "crochga01": {"bsId": 676979, "firstName": "Garrett", "lastName": "Crochet", "team": "CWS"},
    "ceasedy01": {"bsId": 656302, "firstName": "Dylan", "lastName": "Cease", "team": "SD"},
    "rockeku01": {"bsId": 677958, "firstName": "Kumar", "lastName": "Rocker", "team": "TEX"},
    "rouppla01": {"bsId": 694738, "firstName": "Landen", "lastName": "Roupp", "team": "SF"},
    "rogerty01": {"bsId": 643511, "firstName": "Tyler", "lastName": "Rogers", "team": "SF"},
    "castilu02": {"bsId": 622491, "firstName": "Luis", "lastName": "Castillo", "team": "SEA"},
    "rasmudr01": {"bsId": 656876, "firstName": "Drew", "lastName": "Rasmussen", "team": "TB"},
    "treinbl01": {"bsId": 595014, "firstName": "Blake", "lastName": "Treinen", "team": "LAD"},
    "paddach01": {"bsId": 663978, "firstName": "Chris", "lastName": "Paddack", "team": "MIN"},
    "janseke01": {"bsId": 445276, "firstName": "Kenley", "lastName": "Jansen", "team": "BOS"}
}

# Uncomment this function when you're ready to use the API endpoint
"""
def get_player_lookup_from_api(base_url, bbref_ids):
    '''
    Fetch player information from the API for the given BBRef IDs
    
    Args:
        base_url (str): Base URL for the API
        bbref_ids (list): List of BBRef IDs to fetch
        
    Returns:
        dict: Mapping of BBRef IDs to player information
    '''
    player_mapping = {}
    
    try:
        # Create a request with SSL verification disabled
        response = requests.get(f"{base_url}/api/playerlookup", verify=False)
        
        if response.status_code == 200:
            players = response.json()
            # Filter players by the bbref_ids we're interested in
            for player in players:
                if player['bbrefId'] in bbref_ids:
                    player_mapping[player['bbrefId']] = {
                        'bsId': player['bsID'], 
                        'firstName': player['firstName'], 
                        'lastName': player['lastName'],
                        'team': player['team']
                    }
        else:
            print(f"Error fetching player data: {response.status_code}")
            
    except Exception as e:
        print(f"API error: {e}")
        
    return player_mapping
"""

def build_baseball_savant_url(first_name, last_name, bs_id, season):
    """
    Build a URL for Baseball Savant player page
    
    Args:
        first_name (str): Player's first name
        last_name (str): Player's last name
        bs_id (int): Baseball Savant ID
        season (str): Season to get data for
        
    Returns:
        str: Complete URL
    """
    # Create a hyphenated name: "first-last"
    player_slug = f"{first_name.lower()}-{last_name.lower()}-{bs_id}"
    return f"https://baseballsavant.mlb.com/savant-player/{player_slug}?stats=gamelogs-r-pitching-statcast&season={season}"

def initialize_webdriver():
    """Initialize and return a Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL errors
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_baseball_savant_stats():
    """
    Scrape the statistics table from Baseball Savant using Selenium
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Create a timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"baseball_savant_stats_{timestamp}.csv")
    
    # Initialize the CSV with headers
    fieldnames = [
        "BBRefID", "BSID", "Name", "Team", 
        "PA", "AB", "H", "1B", "2B", "3B", "HR", "SO", "BB", 
        "BA", "xBA", "HR%", "K%", "BB%", "Brls", "HardHit%", 
        "EV (MPH)", "LA (°)", "Dist (ft)"
    ]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Initialize the WebDriver
        driver = initialize_webdriver()
        
        try:
            # Process each player in our mapping
            for bbref_id, player in PLAYER_MAPPING.items():
                # Build URL
                first_name = player['firstName']
                last_name = player['lastName']
                bs_id = player['bsId']
                url = build_baseball_savant_url(first_name, last_name, bs_id, SEASON)
                
                print(f"Scraping {url}")
                
                try:
                    # Load the page with Selenium
                    driver.get(url)
                    
                    # Wait for the metrics table to load
                    # This is crucial - we need to wait for JavaScript to populate the div
                    print("Waiting for the metrics table to load...")
                    
                    try:
                        # First wait for the main div to be present
                        WebDriverWait(driver, WAIT_TIMEOUT).until(
                            EC.presence_of_element_located((By.ID, "gamelogs_metrics"))
                        )
                        
                        # Additional wait for the content to load within the div
                        # Wait for table inside the div to be present
                        WebDriverWait(driver, WAIT_TIMEOUT).until(
                            lambda d: len(d.find_element(By.ID, "gamelogs_metrics").find_elements(By.TAG_NAME, "table")) > 0
                        )
                        
                        # Final wait to ensure the tbody contains at least one row
                        WebDriverWait(driver, WAIT_TIMEOUT).until(
                            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#gamelogs_metrics tbody tr")) > 0
                        )
                        
                        print("Table has loaded!")
                    except Exception as wait_error:
                        print(f"Error waiting for table to load: {wait_error}")
                        print("Attempting to continue anyway...")
                    
                    # Get the HTML after JavaScript has rendered the content
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    
                    # Find the metrics table div
                    metrics_div = soup.find('div', id='gamelogs_metrics')
                    
                    if metrics_div:
                        print("Found metrics div in the HTML")
                        
                        # Find the table within the div
                        table = metrics_div.find('table')
                        
                        if table:
                            print("Found the table element")
                            
                            # Find all rows in the table
                            all_rows = table.find_all('tr')
                            print(f"Found {len(all_rows)} rows in the table")
                            
                            if len(all_rows) >= 3:  # We need the header rows and at least one data row
                                # The component row has the column headers
                                header_row = table.find('tr', class_='tr-component-row')
                                
                                if not header_row:
                                    print("Could not find header row with class 'tr-component-row', using second row instead")
                                    header_row = all_rows[1]  # Use the second row as header if class not found
                                
                                # Extract headers from th elements
                                headers = []
                                for th in header_row.find_all('th'):
                                    header_text = th.get_text(strip=True)
                                    if header_text:
                                        headers.append(header_text)
                                        
                                print(f"Extracted {len(headers)} headers:")
                                for i, header in enumerate(headers):
                                    print(f"  {i}: {header}")
                                
                                # Find the data row (first row in tbody)
                                data_row = table.find('tbody').find('tr')
                                
                                if data_row:
                                    # Extract data from td elements
                                    data = []
                                    for td in data_row.find_all('td'):
                                        # Try to find span inside td
                                        span = td.find('span')
                                        if span:
                                            value = span.get_text(strip=True)
                                        else:
                                            value = td.get_text(strip=True)
                                        data.append(value)
                                        
                                    print(f"Extracted {len(data)} data values:")
                                    for i, value in enumerate(data):
                                        print(f"  {i}: {value}")
                                    
                                    # Map data to a dictionary using column positions
                                    column_positions = {
                                        "PA": 0,
                                        "AB": 1,  # Use the first AB column
                                        "H": 3,
                                        "1B": 4,
                                        "2B": 5,
                                        "3B": 6,
                                        "HR": 7,
                                        "SO": 8,
                                        "BB": 9,
                                        "BA": 10,
                                        "xBA": 11,
                                        "HR%": 12,
                                        "K%": 13,
                                        "BB%": 14,
                                        "Brls": 15,
                                        "HardHit%": 16,
                                        "EV (MPH)": 17,  # Average EV
                                        "LA (°)": 18,
                                        "Dist (ft)": 19  # Average Distance
                                    }
                                    
                                    # Prepare the row for CSV
                                    row = {
                                        "BBRefID": bbref_id,
                                        "BSID": bs_id,
                                        "Name": f"{first_name} {last_name}",
                                        "Team": player['team']
                                    }
                                    
                                    # Extract values using the position mapping
                                    for field, pos in column_positions.items():
                                        if pos < len(data):
                                            row[field] = data[pos]
                                    
                                    # Write to CSV
                                    writer.writerow(row)
                                    print(f"Successfully scraped data for {first_name} {last_name}\n")
                                else:
                                    print("Could not find data row in the table\n")
                            else:
                                print("Not enough rows found in the table\n")
                        else:
                            print("Could not find table element inside the metrics div\n")
                            # Print the raw HTML for debugging
                            print("Raw HTML of metrics div:")
                            print(metrics_div.prettify()[:500])
                    else:
                        print("Could not find metrics div in the HTML\n")
                        
                except Exception as e:
                    print(f"Error scraping data for {first_name} {last_name}: {e}\n")
                    import traceback
                    traceback.print_exc()
                
                # Wait before next request
                time.sleep(SLEEP_TIME)
            
            print(f"Data has been saved to {output_file}")
            
        finally:
            # Always close the WebDriver
            driver.quit()

if __name__ == "__main__":
    scrape_baseball_savant_stats()