import requests
import os
import json
from datetime import datetime, timedelta
import time
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OUTPUT_DIR = "output"
SEASON = "2025"  # The season you want to scrape data for
CHROME_DRIVER_PATH = "C:/buns/tw/SVREDO2/prodScripts/SeleniumVersions/chromedriver.exe"  # Path to your ChromeDriver
WAIT_TIMEOUT = 15  # Maximum seconds to wait for elements to load
SLEEP_TIME = 2  # Time to wait between requests to avoid rate limiting
API_BASE_URL = "https://localhost:44346/api"

def get_existing_records():
    """
    Fetch all existing StatcastPitcherData records for the year
    
    Returns:
        list: List of existing records
    """
    try:
        # Get records for the current year
        url = f"{API_BASE_URL}/StatcastPitcherData/Year/{SEASON}"
        response = requests.get(url, verify=False)
        response.raise_for_status()
        
        records = response.json()
        print(f"Found {len(records)} existing records for {SEASON}")
        return records
        
    except Exception as e:
        print(f"Error fetching existing records: {e}")
        return []

def initialize_webdriver():
    """Initialize and return a Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL errors
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Set window size
    
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def build_baseball_savant_url(first_name, last_name, bs_id, season):
    """Build URL for Baseball Savant player page"""
    player_slug = f"{first_name.lower()}-{last_name.lower()}-{bs_id}"
    return f"https://baseballsavant.mlb.com/savant-player/{player_slug}?stats=gamelogs-r-pitching-statcast&season={season}"

def extract_advanced_metrics(soup, include_raw_data=False, is_season_split=False):
    """
    Extract advanced metrics from the player page
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        include_raw_data (bool): Whether to include raw data in the result
        is_season_split (bool): Whether this is for a "Season" split (determines which fields to calculate)
        
    Returns:
        tuple or dict: Tuple of (metrics, raw_data) if include_raw_data is True, otherwise just metrics
    """
    metrics = {}
    raw_data = {}
    
    # Find the metrics table div
    metrics_div = soup.find('div', id='gamelogs_metrics')
    
    if not metrics_div or not metrics_div.find('table'):
        print("Could not find metrics table")
        if include_raw_data:
            return {}, {}
        return {}
    
    table = metrics_div.find('table')
    
    # Find all rows in the table
    all_rows = table.find_all('tr')
    
    if len(all_rows) < 3:
        print("Not enough rows in table")
        if include_raw_data:
            return {}, {}
        return {}
        
    # Get header row
    header_row = table.find('tr', class_='tr-component-row') or all_rows[1]
    
    # Get data row
    data_row = table.find('tbody').find('tr')
    
    if not header_row or not data_row:
        print("Could not find header or data row")
        if include_raw_data:
            return {}, {}
        return {}
    
    # Extract headers and data
    headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
    data = []
    for td in data_row.find_all('td'):
        span = td.find('span')
        if span:
            value = span.get_text(strip=True)
        else:
            value = td.get_text(strip=True)
        data.append(value)
    
    print(f"Debug - Full headers list: {headers}")
    print(f"Debug - Full data list: {data}")
    
    # Find positions of all required data points
    k_perc_pos = None
    hr_perc_pos = None
    ev_pos = None
    la_pos = None
    hardhit_perc_pos = None
    brls_pos = None
    pa_pos = None
    ab_pos = None
    h_pos = None
    doubles_pos = None
    triples_pos = None
    hr_pos = None
    so_pos = None
    bb_pos = None
    ba_pos = None
    xba_pos = None
    
    # Find the correct positions in the headers
    for i, header in enumerate(headers):
        if header == "K%":
            k_perc_pos = i
        elif header == "HR%":
            hr_perc_pos = i
        elif header == "EV (MPH)" and ev_pos is None:  # Take only the first EV column
            ev_pos = i
        elif header == "LA (°)":
            la_pos = i
        elif header == "HardHit%":
            hardhit_perc_pos = i
        elif header == "Brls":
            brls_pos = i
        elif header == "PA":
            pa_pos = i
        elif header == "AB" and ab_pos is None:  # Take only the first AB column
            ab_pos = i
        elif header == "H":
            h_pos = i
        elif header == "2B":
            doubles_pos = i
        elif header == "3B":
            triples_pos = i
        elif header == "HR":
            hr_pos = i
        elif header == "SO":
            so_pos = i
        elif header == "BB":
            bb_pos = i
        elif header == "BA":
            ba_pos = i
        elif header == "xBA":
            xba_pos = i
    
    # Print found positions for debugging
    print(f"Debug - Found positions: K%={k_perc_pos}, HR%={hr_perc_pos}, EV={ev_pos}, LA={la_pos}, " +
          f"HardHit%={hardhit_perc_pos}, Brls={brls_pos}, PA={pa_pos}, AB={ab_pos}, H={h_pos}, " +
          f"2B={doubles_pos}, 3B={triples_pos}, HR={hr_pos}, SO={so_pos}, BB={bb_pos}, " +
          f"BA={ba_pos}, xBA={xba_pos}")
    
    # Initialize all metrics to None
    metrics = {
        "k_perc": None,
        "hR_perc": None,
        "ev": None,
        "la": None,
        "barrel_perc": None,
        "hardHit_perc": None,
        "pa": None,
        "bip": None,
        "ba": None,
        "xBA": None
    }
    
    # Only calculate SLG and xaWoba for non-Season splits
    if not is_season_split:
        metrics["slg"] = None
        metrics["xaWoba"] = None
    
    # Extract PA
    if pa_pos is not None and pa_pos < len(data):
        try:
            metrics["pa"] = int(data[pa_pos])
            raw_data["pa"] = metrics["pa"]
        except (ValueError, TypeError):
            metrics["pa"] = None
    
    # Extract SO (K)
    so_value = None
    if so_pos is not None and so_pos < len(data):
        try:
            so_value = int(data[so_pos])
            raw_data["so"] = so_value
        except (ValueError, TypeError):
            so_value = None
    
    # Extract BB
    bb_value = None
    if bb_pos is not None and bb_pos < len(data):
        try:
            bb_value = int(data[bb_pos])
            raw_data["bb"] = bb_value
        except (ValueError, TypeError):
            bb_value = None
    
    # Calculate BIP (Ball in Play) = PA - BB - SO
    if metrics["pa"] is not None and bb_value is not None and so_value is not None:
        metrics["bip"] = metrics["pa"] - bb_value - so_value
    
    # Extract K%
    if k_perc_pos is not None and k_perc_pos < len(data):
        value = data[k_perc_pos]
        try:
            metrics["k_perc"] = float(value.strip('%')) / 100 if '%' in value else float(value)
        except (ValueError, AttributeError):
            metrics["k_perc"] = None
    
    # Extract HR%
    if hr_perc_pos is not None and hr_perc_pos < len(data):
        value = data[hr_perc_pos]
        try:
            metrics["hR_perc"] = float(value.strip('%')) / 100 if '%' in value else float(value)
        except (ValueError, AttributeError):
            metrics["hR_perc"] = None
    
    # Extract EV (first occurrence only)
    if ev_pos is not None and ev_pos < len(data):
        try:
            metrics["ev"] = float(data[ev_pos])
        except (ValueError, TypeError):
            metrics["ev"] = None
    
    # Extract LA
    if la_pos is not None and la_pos < len(data):
        try:
            metrics["la"] = float(data[la_pos])
        except (ValueError, TypeError):
            metrics["la"] = None
    
    # Extract HardHit%
    if hardhit_perc_pos is not None and hardhit_perc_pos < len(data):
        value = data[hardhit_perc_pos]
        try:
            metrics["hardHit_perc"] = float(value.strip('%')) / 100 if '%' in value else float(value)
        except (ValueError, AttributeError):
            metrics["hardHit_perc"] = None
    
    # Calculate barrel_perc if possible
    if brls_pos is not None and pa_pos is not None and brls_pos < len(data) and pa_pos < len(data):
        try:
            brls = float(data[brls_pos])
            pa = float(data[pa_pos])
            if pa > 0:
                metrics["barrel_perc"] = brls / pa
            else:
                metrics["barrel_perc"] = None
        except (ValueError, ZeroDivisionError):
            metrics["barrel_perc"] = None
    
    # Extract BA
    if ba_pos is not None and ba_pos < len(data):
        try:
            metrics["ba"] = float(data[ba_pos])
        except (ValueError, TypeError):
            metrics["ba"] = None
    
    # Extract xBA
    if xba_pos is not None and xba_pos < len(data):
        try:
            metrics["xBA"] = float(data[xba_pos])
        except (ValueError, TypeError):
            metrics["xBA"] = None
    
    # For non-Season splits, calculate SLG and xaWoba
    if not is_season_split:
        # Extract data needed for SLG calculation
        ab_value = None
        h_value = None
        doubles_value = None
        triples_value = None
        hr_value = None
        
        if ab_pos is not None and ab_pos < len(data):
            try:
                ab_value = int(data[ab_pos])
                raw_data["ab"] = ab_value
            except (ValueError, TypeError):
                ab_value = None
        
        if h_pos is not None and h_pos < len(data):
            try:
                h_value = int(data[h_pos])
                raw_data["h"] = h_value
            except (ValueError, TypeError):
                h_value = None
        
        if doubles_pos is not None and doubles_pos < len(data):
            try:
                doubles_value = int(data[doubles_pos])
                raw_data["2b"] = doubles_value
            except (ValueError, TypeError):
                doubles_value = None
        
        if triples_pos is not None and triples_pos < len(data):
            try:
                triples_value = int(data[triples_pos])
                raw_data["3b"] = triples_value
            except (ValueError, TypeError):
                triples_value = None
        
        if hr_pos is not None and hr_pos < len(data):
            try:
                hr_value = int(data[hr_pos])
                raw_data["hr"] = hr_value
            except (ValueError, TypeError):
                hr_value = None
        
        # Calculate SLG = (1B + 2*2B + 3*3B + 4*HR) / AB
        if (ab_value is not None and ab_value > 0 and
            h_value is not None and
            doubles_value is not None and
            triples_value is not None and
            hr_value is not None):
            # Singles = H - 2B - 3B - HR
            singles = h_value - doubles_value - triples_value - hr_value
            slg = (singles + 2*doubles_value + 3*triples_value + 4*hr_value) / ab_value
            # Round to 4 decimal places
            metrics["slg"] = round(slg, 4)
        
        # Calculate xwOBA using the formula: 0.4049−0.0044*EV−0.0016*LA+0.0018*Barrel%−0.0002*HardHit%+0.9572⋅xBA+1.0630*HR%+0.2227*K%
        if (metrics["ev"] is not None and
            metrics["la"] is not None and
            metrics["barrel_perc"] is not None and
            metrics["hardHit_perc"] is not None and
            metrics["xBA"] is not None and
            metrics["hR_perc"] is not None and
            metrics["k_perc"] is not None):
            
            # Convert barrel_perc and hardHit_perc to percentages (0-100 scale) for the formula
            barrel_perc_pct = metrics["barrel_perc"] * 100
            hardhit_perc_pct = metrics["hardHit_perc"] * 100
            
            xwoba = (0.4049 - 
                    0.0044 * metrics["ev"] - 
                    0.0016 * metrics["la"] + 
                    0.0018 * barrel_perc_pct - 
                    0.0002 * hardhit_perc_pct + 
                    0.9572 * metrics["xBA"] + 
                    1.0630 * metrics["hR_perc"] + 
                    0.2227 * metrics["k_perc"])
            
            # Round to 4 decimal places
            metrics["xaWoba"] = round(xwoba, 4)
    
    print(f"Debug - Extracted metrics: {metrics}")
    
    if include_raw_data:
        return metrics, raw_data
    else:
        return metrics

def update_pitcher_metrics(record):
    """
    Update advanced metrics for a pitcher
    
    Args:
        record (dict): Pitcher record
        
    Returns:
        bool: True if successful, False otherwise
    """
    bs_id = record["bsID"]
    first_name = record["firstName"]
    last_name = record["lastName"]
    split = record["split"]
    year = record["year"]
    
    # Determine if this is a Season split
    is_season_split = split.lower() == 'season'
    
    print(f"\nUpdating advanced metrics for {first_name} {last_name} (bsID: {bs_id})...")
    print(f"Split type: {split} (is_season_split: {is_season_split})")
    
    # Build the URL
    url = build_baseball_savant_url(first_name, last_name, bs_id, year)
    
    # Initialize WebDriver and set it to quit when done
    driver = initialize_webdriver()
    
    try:
        # Load the initial page and wait for it to be ready
        driver.get(url)
        
        # Wait for the page to load properly
        time.sleep(5)
        
        # Get metrics for the whole season
        print("Getting metrics for full season...")
        # Parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        metrics, raw_data = extract_advanced_metrics(soup, True, is_season_split)
        
        if not metrics:
            print("Failed to get metrics")
            return False
        
        print(f"Full season metrics: {json.dumps(metrics, indent=2)}")
        
        # Create an update payload with just the metrics we want to update
        update_payload = {**record}
        update_payload.update(metrics)
        
        # Save the payload for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_dir = os.path.join(OUTPUT_DIR, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        
        payload_path = os.path.join(metrics_dir, f"{last_name.lower()}_{first_name.lower()}_season_{timestamp}.json")
        with open(payload_path, 'w') as f:
            json.dump(update_payload, f, indent=2)
        
        # Send the update to the API
        update_url = f"{API_BASE_URL}/StatcastPitcherData/{bs_id}/{split}/{year}"
        
        response = requests.put(
            update_url,
            json=update_payload,
            verify=False,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        if response.status_code != 204:  # 204 No Content is success for PUT
            print(f"Error updating metrics: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print(f"Successfully updated full season metrics for {first_name} {last_name}")
        
        # Now get metrics for the last 14 days
        print("\nGetting metrics for last 14 days...")
        
        # Calculate date range (last 14 days to today) - use YYYY-MM-DD format
        today = datetime.now()
        two_weeks_ago = today - timedelta(days=14)
        
        start_date = two_weeks_ago.strftime("%Y-%m-%d")  # YYYY-MM-DD format
        end_date = today.strftime("%Y-%m-%d")            # YYYY-MM-DD format
        
        # Get metrics for the date range
        date_range_soup = get_metrics_with_date_range(driver, url, start_date, end_date)
        # For last14 split, we always want to calculate SLG and xaWoba
        last14_metrics, last14_raw_data = extract_advanced_metrics(date_range_soup, True, False)
        
        if not last14_metrics:
            print("Failed to get last 14 days metrics")
            return True  # We did update the season metrics, so return True
        
        print(f"Last 14 days metrics: {json.dumps(last14_metrics, indent=2)}")
        
        # Look for existing "last14" split record
        last14_record = get_player_by_split(bs_id, "last14", year)
        
        if last14_record:
            print("Found existing 'last14' record, updating...")
            
            # Update the existing record
            last14_update_payload = {**last14_record}
            last14_update_payload.update(last14_metrics)
            
            # Update the record
            last14_update_url = f"{API_BASE_URL}/StatcastPitcherData/{bs_id}/last14/{year}"
            
            last14_response = requests.put(
                last14_update_url,
                json=last14_update_payload,
                verify=False,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if last14_response.status_code != 204:
                print(f"Error updating 'last14' record: Status code {last14_response.status_code}")
                print(f"Response: {last14_response.text}")
            else:
                print(f"Successfully updated 'last14' record for {first_name} {last_name}")
        else:
            print("No existing 'last14' record, creating new one...")
            
            # Create new "last14" record based on the season record
            new_last14_record = create_last14_record(record, last14_metrics, last14_raw_data)
            
            # Save the new record for debugging
            last14_payload_path = os.path.join(metrics_dir, f"{last_name.lower()}_{first_name.lower()}_last14_{timestamp}.json")
            with open(last14_payload_path, 'w') as f:
                json.dump(new_last14_record, f, indent=2)
            
            # Post the new record
            create_response = requests.post(
                f"{API_BASE_URL}/StatcastPitcherData",
                json=new_last14_record,
                verify=False,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if create_response.status_code not in [200, 201]:
                print(f"Error creating 'last14' record: Status code {create_response.status_code}")
                print(f"Response: {create_response.text}")
            else:
                print(f"Successfully created 'last14' record for {first_name} {last_name}")
        
        return True
        
    except Exception as e:
        print(f"Error updating metrics: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Always close the WebDriver
        driver.quit()

def get_metrics_with_date_range(driver, url, start_date=None, end_date=None):
    """
    Get metrics by setting a custom date range
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        url (str): URL of the player page
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        BeautifulSoup: Parsed HTML after date range is applied
    """
    # Navigate to the page
    print(f"Loading {url} with date range: {start_date} to {end_date}")
    driver.get(url)
    
    # Wait for the metrics div to load
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "gamelogs_metrics"))
        )
        
        # Wait for the table to load
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            lambda d: len(d.find_element(By.ID, "gamelogs_metrics").find_elements(By.TAG_NAME, "table")) > 0
        )
        
        # Wait for data rows
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#gamelogs_metrics tbody tr")) > 0
        )
    except Exception as e:
        print(f"Error waiting for page elements: {e}")
        return BeautifulSoup("<html></html>", 'html.parser')  # Return empty soup
    
    # If date range is specified, try to set it
    if start_date or end_date:
        try:
            print("Attempting to set date range...")
            
            # Wait an extra second for all elements to be fully loaded
            time.sleep(1)
            
            if start_date:
                # Find and fill the start date input - use YYYY-MM-DD format
                start_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.ID, "gamelogs-type-dgt"))
                )
                
                # Clear the input first
                start_input.clear()
                
                # Click to make sure it's active
                start_input.click()
                
                # Send keys with the correct format
                start_input.send_keys(start_date)  # YYYY-MM-DD format
                start_input.send_keys(Keys.TAB)  # Tab out to trigger date change
                print(f"Set start date to {start_date}")
                
                # Wait a moment for the input to register
                time.sleep(1)
            
            if end_date:
                # Find and fill the end date input - use YYYY-MM-DD format
                end_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.ID, "gamelogs-type-dlt"))
                )
                
                # Clear the input first
                end_input.clear()
                
                # Click to make sure it's active
                end_input.click()
                
                # Send keys with the correct format
                end_input.send_keys(end_date)  # YYYY-MM-DD format
                end_input.send_keys(Keys.TAB)  # Tab out to trigger date change
                print(f"Set end date to {end_date}")
                
                # Wait a moment for the input to register
                time.sleep(1)
            
            # Simply press Enter on the last input field
            if end_date:
                end_input.send_keys(Keys.ENTER)
            elif start_date:
                start_input.send_keys(Keys.ENTER)
            
            # Give the page time to reload with the new date range
            time.sleep(5)
            
            # Check if the table still exists and has data
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "#gamelogs_metrics tbody tr")) > 0
            )
        except Exception as e:
            print(f"Error setting date range: {e}")
            import traceback
            traceback.print_exc()
    
    # Take a screenshot for debugging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = os.path.join(OUTPUT_DIR, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    player_name = url.split('/')[4].split('?')[0]
    screenshot_path = os.path.join(screenshot_dir, f"{player_name}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)
    print(f"Saved screenshot to {screenshot_path}")
    
    # Parse the updated page
    return BeautifulSoup(driver.page_source, 'html.parser')

def get_player_by_split(bs_id, split, year):
    """
    Get a player record by bsID, split, and year
    
    Args:
        bs_id (str): Baseball Savant ID
        split (str): Split value ('Season' or 'last14')
        year (int): Year
        
    Returns:
        dict: Player record or None if not found
    """
    try:
        # Build the URL to fetch the player
        url = f"{API_BASE_URL}/StatcastPitcherData/Player/{bs_id}/{split}/{year}"
        
        # Make the request
        response = requests.get(url, verify=False)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            print(f"Error fetching player data: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error fetching player: {e}")
        return None

def create_last14_record(record, metrics, raw_data=None):
    """
    Create a record for 'last14' split based on existing 'Season' record
    
    Args:
        record (dict): Existing 'Season' record
        metrics (dict): Metrics from the last 14 days
        raw_data (dict, optional): Raw data from scraping
        
    Returns:
        dict: New 'last14' record
    """
    # Create a copy of the base record
    new_record = dict(record)
    
    # Change the split to 'last14'
    new_record["split"] = "last14"
    
    # Update PA and BIP
    new_record["pa"] = metrics["pa"]
    new_record["bip"] = metrics["bip"]
    
    # Update K% and HR%
    new_record["k_perc"] = metrics["k_perc"]
    new_record["hR_perc"] = metrics["hR_perc"]
    
    # Update EV, LA, Barrel%, and HardHit%
    new_record["ev"] = metrics["ev"]
    new_record["la"] = metrics["la"]
    new_record["barrel_perc"] = metrics["barrel_perc"]
    new_record["hardHit_perc"] = metrics["hardHit_perc"]
    
    # Update BA and xBA
    new_record["ba"] = metrics["ba"]
    new_record["xBA"] = metrics["xBA"]
    
    # Update SLG
    new_record["slg"] = metrics["slg"]
    
    # Update xSLG - set to null as specified
    new_record["xSLG"] = None
    
    # Update xaWoba if available
    if "xaWoba" in metrics and metrics["xaWoba"] is not None:
        new_record["xaWoba"] = metrics["xaWoba"]
    
    # Keep aWoba, ERA, and xERA from the original record
    # These fields are kept from the parent record
    
    # Update dateAdded to today
    new_record["dateAdded"] = datetime.now().strftime("%Y-%m-%d")
    
    return new_record

def main():
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Get existing records
    records = get_existing_records()
    
    if not records:
        print("No records found to update")
        return
    
    # Filter only records with 'Season' split
    season_records = [record for record in records if record['split'].lower() == 'season']
    print(f"Found {len(season_records)} records with 'Season' split")
    
    # Process a subset for testing if needed
    season_records = season_records[:5]  # Process just the first 5 records
    
    # Update metrics for each record
    success_count = 0
    for record in season_records:
        if update_pitcher_metrics(record):
            success_count += 1
        
        # Add a small delay between requests
        time.sleep(SLEEP_TIME)
    
    print(f"\nSuccessfully updated {success_count} of {len(season_records)} records")

if __name__ == "__main__":
    main()