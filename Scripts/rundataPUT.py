import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

def fetch_mlb_stats():
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
                "RunsAtAway": row["Away Runs"]
            }
            records.append(record)

        with open('nrfi_records.json', 'w') as f:
            json.dump(records, f, indent=4)
        print("Data successfully saved to nrfi_records.json")

        # Make PUT requests to the API for each record
        for record in records:
            url = f"https://localhost:44346/api/NRFIRecords2024/{record['Team']}"
            try:
                response = requests.put(url, json=record, verify=False)  # Disable SSL verification
                if response.status_code == 200:
                    print(f"Successfully updated {record['Team']}")
                else:
                    print(f"Failed to update {record['Team']}. Status code: {response.status_code}")
            except requests.exceptions.SSLError as e:
                print(f"SSL error occurred while updating {record['Team']}: {e}")
    else:
        print("Failed to retrieve the webpage. Status code:", response.status_code)

fetch_mlb_stats()
