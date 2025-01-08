import requests
from bs4 import BeautifulSoup, Comment

# Create a session object
session = requests.Session()

# Define common headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com',
    'DNT': '1',  # Do Not Track Request Header
    'Connection': 'keep-alive',
}

# Attach the headers to the session
session.headers.update(headers)

# Function to get the first letter of the pitcher_id for URL construction
def get_url_letter(pitcher_id):
    return pitcher_id[0]

# Function to scrape the pitcher's first inning data from Baseball Reference
def scrape_pitcher_first_inning(session, pitcher_id, year):
    letter = get_url_letter(pitcher_id)
    url = f"https://www.baseball-reference.com/players/split.fcgi?id={pitcher_id}&year={year}&t=p#all_innng"
    print(f"Scraping data from URL: {url}")
    
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page for pitcher {pitcher_id}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the div with id 'all_innng'
    inning_div = soup.find('div', id='all_innng')
    if inning_div:
        print(f"Found 'all_innng' div for pitcher {pitcher_id}")
        # Extract comments within the 'inning_div'
        comments = inning_div.find_all(string=lambda text: isinstance(text, Comment))
        
        # Iterate over the comments and check for the desired div
        for comment in comments:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            div_inning = comment_soup.find('div', id='div_innng')
            
            if div_inning:
                print(f"Found 'div_innng' div within comment for pitcher {pitcher_id}")
                # Find the table with id 'innng'
                inning_table = div_inning.find('table', id='innng')
                
                if inning_table:
                    print(f"Found 'innng' table for pitcher {pitcher_id}")
                    # Find the tbody and the rows within it
                    tbody = inning_table.find('tbody')
                    if tbody:
                        # Iterate over all rows in tbody
                        rows = tbody.find_all('tr')
                        for row in rows:
                            first_column = row.find('th', {'data-stat': 'split_name'})
                            if first_column and first_column.text.strip() == '1st inning':
                                print(f"Found 1st inning data for pitcher {pitcher_id}")
                                # Extract the first inning data into a dictionary
                                try:
                                    pitcher_1st_inning_data = {
                                        "bbrefID": pitcher_id,
                                        "G": int(row.find(attrs={'data-stat': 'G'}).text or 0),
                                        "IP": float(row.find(attrs={'data-stat': 'IP'}).text or 0),
                                        "ER": int(row.find(attrs={'data-stat': 'ER'}).text or 0),
                                        "ERA": float(row.find(attrs={'data-stat': 'earned_run_avg'}).text or 0),
                                        "PA": int(row.find(attrs={'data-stat': 'PA'}).text or 0),
                                        "AB": int(row.find(attrs={'data-stat': 'AB'}).text or 0),
                                        "R": int(row.find(attrs={'data-stat': 'R'}).text or 0),
                                        "H": int(row.find(attrs={'data-stat': 'H'}).text or 0),
                                        "2B": int(row.find(attrs={'data-stat': '2B'}).text or 0),
                                        "3B": int(row.find(attrs={'data-stat': '3B'}).text or 0),
                                        "HR": int(row.find(attrs={'data-stat': 'HR'}).text or 0),
                                        "SB": int(row.find(attrs={'data-stat': 'SB'}).text or 0),
                                        "CS": int(row.find(attrs={'data-stat': 'CS'}).text or 0),
                                        "BB": int(row.find(attrs={'data-stat': 'BB'}).text or 0),
                                        "SO": int(row.find(attrs={'data-stat': 'SO'}).text or 0),
                                        "SO_W": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0),
                                        "BA": float(row.find(attrs={'data-stat': 'batting_avg'}).text or 0),
                                        "OBP": float(row.find(attrs={'data-stat': 'onbase_perc'}).text or 0),
                                        "SLG": float(row.find(attrs={'data-stat': 'slugging_perc'}).text or 0),
                                        "OPS": float(row.find(attrs={'data-stat': 'onbase_plus_slugging'}).text or 0),
                                        "TB": int(row.find(attrs={'data-stat': 'TB'}).text or 0),
                                        "GDP": int(row.find(attrs={'data-stat': 'GIDP'}).text or 0),
                                        "HBP": int(row.find(attrs={'data-stat': 'HBP'}).text or 0),
                                        "SH": int(row.find(attrs={'data-stat': 'SH'}).text or 0),
                                        "SF": int(row.find(attrs={'data-stat': 'SF'}).text or 0),
                                        "IBB": int(row.find(attrs={'data-stat': 'IBB'}).text or 0),
                                        "ROE": int(row.find(attrs={'data-stat': 'ROE'}).text or 0),
                                        "BAbip": float(row.find(attrs={'data-stat': 'batting_avg_bip'}).text or 0),
                                        "tOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_total'}).text or 0),
                                        "sOPSPlus": int(row.find(attrs={'data-stat': 'onbase_plus_slugging_vs_lg'}).text or 0),
                                    }
                                    return pitcher_1st_inning_data
                                except AttributeError as e:
                                    print(f"Error parsing first inning data for pitcher: {pitcher_id}, Year: {year}. Error: {e}")
                                    return None
    else:
        print(f"Failed to find 'all_innng' div for pitcher {pitcher_id}")
    return None

# Function to check if the pitcher exists in the database
def pitcher_1st_inning_exists(session, bbrefID):
    url = f"https://localhost:44346/api/Pitcher1stInning/{bbrefID}"
    print(f"Checking if pitcher exists in the database: {bbrefID}")
    
    response = session.get(url, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code == 200:
        print(f"Pitcher {bbrefID} exists in the database.")
    elif response.status_code == 404:
        print(f"Pitcher {bbrefID} does not exist in the database.")
    else:
        print(f"Error checking pitcher existence. Status code: {response.status_code}")
    
    return response.status_code == 200

def post_to_api(session, endpoint, data, is_update=False):
    if data is None:
        print(f"No data to post to {endpoint}.")
        return
    
    url = f"https://localhost:44346/api/{endpoint}"
    if is_update:
        url += f"/{data['bbrefID']}"
    
    response = session.put(url, json=data, headers={'Content-Type': 'application/json'}, verify=False) if is_update else session.post(url, json=data, headers={'Content-Type': 'application/json'}, verify=False)
    
    if response.status_code == 200:
        print(f"Successfully {'updated' if is_update else 'posted'} data to {endpoint} for {data['bbrefID']}.")
    elif response.status_code == 429:
        print(f"Rate limit exceeded while trying to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefID']}.")
    else:
        print(f"Failed to {'update' if is_update else 'post'} data to {endpoint} for {data['bbrefID']}. Status code: {response.status_code}")
        print(f"Response content: {response.content}")

# List of pitcher IDs
pitchers = [
 'walketa01',
 'gombeau01',
 'rogertr01',
 'irvinja01',
 'rodried05',
 'ortizlu03',
 'gausmke01',
 'crawfku01',
 'Unannounced',
 'cortene01',
 'assadja01',
 'skubata01',
 'fulmeca01',
 'mortoch02',
 'stonega01',
 'bazsh01',
 'reaco01',
 'lugose01',
 'blackpa01',
 'kingmi01',
 'cannojo02',
 'kikucyu01',
 'feddeer01',
 'boydma01',
 'harriky01',
 'urenajo01',
 'greenhu01'
]

year = 2024

# Loop through each pitcher and scrape & post data
for pitcher_id in pitchers:
    if pitcher_id.lower() == "unannounced":
        print(f"Skipping pitcher: {pitcher_id}")
        continue
    
    print(f"Processing pitcher: {pitcher_id}")
    pitcher_1st_inning_data = scrape_pitcher_first_inning(session, pitcher_id, year)
    
    if pitcher_1st_inning_exists(session, pitcher_id):
        post_to_api(session, 'Pitcher1stInning', pitcher_1st_inning_data, is_update=True)
    else:
        post_to_api(session, 'Pitcher1stInning', pitcher_1st_inning_data)
