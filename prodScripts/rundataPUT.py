import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

def fetch_mlb_stats():
    # Current year
    current_year = 2025
    
    url = 'https://sports.betmgm.com/en/blog/mlb/nrfi-yrfi-stats-records-no-runs-first-inning-yes-runs-first-inning-runs-mlb-teams-bm03/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tables_divs = soup.find_all('div', class_='grid-container reuseable-table live-sheets-table')
        
        table1 = pd.read_html(str(tables_divs[0].find('table')))[0]
        table2 = pd.read_html(str(tables_divs[1].find('table')))[0]
        
        # Assign correct column names manually
        table1.columns = ['Team', 'NRFI Record', 'Home', 'Away']
        table2.columns = ['Team', 'Per Game', 'Last Game', 'Home Runs', 'Away Runs']
        
        # Print column names for debugging
        print("Table 1 Columns:", table1.columns)
        print("Table 2 Columns:", table2.columns)
        
        # Merge the tables on 'Team'
        merged_table = pd.merge(table1, table2, on='Team')
        
        records = []
        for _, row in merged_table.iterrows():
            record = {
                "Team": row["Team"],
                "NRFIRecord": row["NRFI Record"],
                "Home": row["Home"],
                "Away": row["Away"],
                "RunsPerFirst": row["Per Game"],
                "LastGame": row["Last Game"],
                "RunsAtHome": row["Home Runs"],
                "RunsAtAway": row["Away Runs"],
                "Year": current_year,  # Add the current year
                "DateModified": datetime.now().isoformat()  # Add current date/time
            }
            records.append(record)
        
        # Save to JSON file
        with open('nrfi_records.json', 'w') as f:
            json.dump(records, f, indent=4)
        print(f"Data successfully saved to nrfi_records.json with year {current_year}")
        
        # Make PUT requests to the API for each record
        for record in records:
            # Update URL to include both team and year parameters
            url = f"https://localhost:44346/api/NRFIRecords2024/{record['Team']}/{current_year}"
            
            try:
                response = requests.put(url, json=record, verify=False)  # Disable SSL verification
                if response.status_code == 200:
                    print(f"Successfully updated {record['Team']} for year {current_year}")
                else:
                    print(f"Failed to update {record['Team']} for year {current_year}. Status code: {response.status_code}")
                    print(f"Response: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Error occurred while updating {record['Team']} for year {current_year}: {e}")
    else:
        print("Failed to retrieve the webpage. Status code:", response.status_code)

# Execute the function
if __name__ == "__main__":
    fetch_mlb_stats()