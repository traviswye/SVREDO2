import requests
import pandas as pd
import os
import json
from datetime import datetime
import urllib3
import time

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OUTPUT_DIR = "output"
YEAR = "2025"  # The season you want to scrape data for
API_BASE_URL = "https://localhost:44346/api"
API_ENDPOINT = f"{API_BASE_URL}/statcastPitcherData"

def download_expected_stats():
    """
    Download the CSV file from Baseball Savant's expected stats leaderboard for pitchers
    
    Returns:
        pandas.DataFrame: The downloaded data as a DataFrame
    """
    url = f"https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=pitcher&year={YEAR}&position=&team=&filterType=bip&min=q&csv=true"
    
    print(f"Downloading data from {url}")
    
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        # Timestamp for the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(OUTPUT_DIR, f"expected_stats_{timestamp}.csv")
        
        # Download the CSV
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Stream the CSV to a file
        with requests.get(url, headers=headers, verify=False, stream=True) as r:
            r.raise_for_status()
            with open(csv_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"CSV downloaded to {csv_path}")
        
        # Read the CSV into a DataFrame
        df = pd.read_csv(csv_path)
        
        return df, csv_path
        
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        return None, None

def get_existing_records():
    """
    Fetch all existing StatcastPitcherData records for the year
    
    Returns:
        dict: Dictionary of existing records keyed by bsID
    """
    try:
        # Get records for the current year
        url = f"{API_BASE_URL}/StatcastPitcherData/Year/{YEAR}"
        response = requests.get(url, verify=False)
        response.raise_for_status()
        
        # Convert to dictionary keyed by bsID for easy lookup
        records = response.json()
        record_dict = {record['bsID']: record for record in records}
        
        print(f"Found {len(record_dict)} existing records for {YEAR}")
        return record_dict
        
    except Exception as e:
        print(f"Error fetching existing records: {e}")
        return {}

def prepare_payloads(df, existing_records):
    """
    Process the dataframe to create payloads for new and updated records
    
    Args:
        df (pandas.DataFrame): The downloaded data
        existing_records (dict): Dictionary of existing records
        
    Returns:
        tuple: (new_records, update_records)
    """
    if df is None:
        return [], []
    
    # Split the "last_name, first_name" column into separate columns
    df[['lastName', 'firstName']] = df['last_name, first_name'].str.split(', ', expand=True)
    
    # Create today's date for DateAdded
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare the payloads
    new_records = []
    update_records = []
    
    for _, row in df.iterrows():
        # Create the bsID as a string
        bs_id = str(row['player_id'])
        
        # Base data that's included in both new and update records
        base_data = {
            "ba": float(row['ba']),
            "xBA": float(row['est_ba']),
            "slg": float(row['slg']),
            "xSLG": float(row['est_slg']),
            "aWoba": float(row['woba']),
            "xaWoba": float(row['est_woba']),
            "era": float(row['era']),
            "xERA": float(row['xera']),
            "dateAdded": today
        }
        
        # Check if this record already exists
        if bs_id in existing_records:
            # Create update payload - only includes the stats we want to update
            existing_record = existing_records[bs_id]
            
            # Verify this is the same 'split' value we're working with
            if existing_record['split'].lower() != 'season':
                print(f"Warning: bsID {bs_id} exists but has split '{existing_record['split']}' instead of 'Season'")
                continue
                
            # Create a copy of the existing record
            update_payload = {**existing_record}
            
            # Update only the specific fields we want to change
            for key, value in base_data.items():
                update_payload[key] = value
                
            update_records.append(update_payload)
        else:
            # Create new record payload - includes all fields
            new_payload = {
                "split": "Season",
                "bsID": bs_id,
                "firstName": row['firstName'],
                "lastName": row['lastName'],
                "bbrefId": None,
                "year": int(row['year']),
                "pa": int(row['pa']),
                "bip": int(row['bip']),
                "k_perc": None,
                "hR_perc": None,
                "ev": None,
                "la": None,
                "barrel_perc": None,
                "hardHit_perc": None,
                **base_data  # Include all the base data fields
            }
            
            new_records.append(new_payload)
    
    return new_records, update_records

def send_new_records(records):
    """
    Send new records to the API
    
    Args:
        records (list): List of new records to create
        
    Returns:
        int: Number of successful creations
    """
    success_count = 0
    
    for record in records:
        try:
            print(f"Creating new record for {record['firstName']} {record['lastName']} (bsID: {record['bsID']})...")
            
            response = requests.post(
                API_ENDPOINT,
                json=record,
                verify=False,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code not in [200, 201]:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text}")
            else:
                success_count += 1
                print(f"Successfully created record for {record['firstName']} {record['lastName']}")
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error creating record for {record['firstName']} {record['lastName']}: {e}")
    
    return success_count

def update_existing_records(records):
    """
    Update existing records via the API
    
    Args:
        records (list): List of records to update
        
    Returns:
        int: Number of successful updates
    """
    success_count = 0
    
    for record in records:
        try:
            bs_id = record['bsID']
            split = record['split']
            year = record['year']
            
            print(f"Updating record for {record['firstName']} {record['lastName']} (bsID: {bs_id})...")
            
            # Use PUT endpoint to update the record
            update_url = f"{API_ENDPOINT}/{bs_id}/{split}/{year}"
            
            response = requests.put(
                update_url,
                json=record,
                verify=False,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code != 204:  # 204 No Content is success for PUT
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text}")
            else:
                success_count += 1
                print(f"Successfully updated record for {record['firstName']} {record['lastName']}")
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error updating record for {record['firstName']} {record['lastName']}: {e}")
    
    return success_count

def main():
    # Download the CSV and convert to DataFrame
    df, csv_path = download_expected_stats()
    
    if df is not None:
        print(f"Downloaded data with {len(df)} rows")
        
        # Get existing records
        existing_records = get_existing_records()
        
        # Prepare payloads for new and updated records
        new_records, update_records = prepare_payloads(df, existing_records)
        
        print(f"Prepared {len(new_records)} new records and {len(update_records)} update records")
        
        # Save payloads to JSON for reference
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if new_records:
            new_records_path = os.path.join(OUTPUT_DIR, f"new_records_{timestamp}.json")
            with open(new_records_path, 'w') as f:
                json.dump(new_records, f, indent=2)
            print(f"New records saved to {new_records_path}")
        
        if update_records:
            update_records_path = os.path.join(OUTPUT_DIR, f"update_records_{timestamp}.json")
            with open(update_records_path, 'w') as f:
                json.dump(update_records, f, indent=2)
            print(f"Update records saved to {update_records_path}")
        
        # Process new records
        if new_records:
            print("\nCreating new records...")
            new_success = send_new_records(new_records)
            print(f"Successfully created {new_success} of {len(new_records)} new records")
        
        # Process update records
        if update_records:
            print("\nUpdating existing records...")
            update_success = update_existing_records(update_records)
            print(f"Successfully updated {update_success} of {len(update_records)} existing records")
        
        print("\nProcess complete!")
    else:
        print("Failed to download data")

if __name__ == "__main__":
    main()