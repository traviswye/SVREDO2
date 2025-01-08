import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from io import StringIO

def fetch_mlb_stats():
    url = 'https://sports.betmgm.com/en/blog/mlb/nrfi-yrfi-stats-records-no-runs-first-inning-yes-runs-first-inning-runs-mlb-teams-bm03/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tables_divs = soup.find_all('div', class_='grid-container reuseable-table live-sheets-table')

        # Load both tables using StringIO to avoid FutureWarnings
        table1_html = str(tables_divs[0].find('table'))
        table2_html = str(tables_divs[1].find('table'))

        table1 = pd.read_html(StringIO(table1_html))[0]
        table2 = pd.read_html(StringIO(table2_html))[0]

        # Ensure the first column is 'Team' in both tables
        table1.columns = ['Team', 'NRFI Record', 'Home', 'Away']
        table2.columns = ['Team', 'Per Game', 'Last Game', 'Home', 'Away']

        # Drop the first row if it's a header row
        table1 = table1.iloc[1:]
        table2 = table2.iloc[1:]

        # Merge the tables based on the 'Team' column
        merged_table = pd.merge(table1, table2, on='Team')

        # Rename the columns to match the API model
        merged_table.columns = ['Team', 'NRFIRecord', 'Home', 'Away', 'RunsPerFirst', 'LastGame', 'RunsAtHome', 'RunsAtAway']

        # Convert to a list of dictionaries (JSON objects)
        records = merged_table.to_dict(orient='records')

        # Output the JSON objects to a file
        with open('nrfi_records.json', 'w') as f:
            json.dump(records, f, indent=4)

        print("Data successfully saved to nrfi_records.json")
    else:
        print("Failed to retrieve the webpage. Status code:", response.status_code)

fetch_mlb_stats()
