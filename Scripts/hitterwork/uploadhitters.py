import requests
from datetime import datetime

# File path to your CSV file
file_path = 'C:/Users/OWM2/CodeRoot/SharpViz/SharpViz/Scripts/hitterwork/allhittercsv.csv'

# Position mapping
position_mapping = {
    'D': 'DH',
    '1': 'P',
    '2': 'C',
    '3': '1B',
    '4': '2B',
    '6': 'SS',
    '5': '3B',
    '7': 'LF',
    '8': 'CF',
    '9': 'RF'
}

# Function to map the position
def map_position(pos_string):
    if pos_string.startswith('*'):
        pos_string = pos_string[1:]
    first_position = pos_string[0]
    return position_mapping.get(first_position, 'Unknown')

# Initialize a set to track unique bbrefIds
unique_bbrefIds = set()

# API endpoint and headers
api_url = "https://localhost:44346/api/Hitters"
headers = {
    "accept": "text/plain",
    "Content-Type": "application/json"
}

# Read and process the file line by line
with open(file_path, 'r', encoding='utf-8') as file:
    next(file)  # Skip the header row

    for line in file:
        row = line.strip().split(',')

        # Ensure that all expected fields are present
        if len(row) < 34:  # Adjust to match the expected number of columns
            print(f"Skipping row due to unexpected number of columns: {row}")
            continue

        try:
            # Extract relevant data based on indexes
            bbrefId = row[-1].strip()  # Last column is bbrefId
            if bbrefId in unique_bbrefIds:
                continue  # Skip duplicates
            unique_bbrefIds.add(bbrefId)

            name = row[1].strip()
            age = int(row[2].strip() or 0)
            team = row[3].strip()
            lg = row[4].strip()
            war = float(row[5].strip() or 0.0)
            g = int(row[6].strip() or 0)
            pa = int(row[7].strip() or 0)
            ab = int(row[8].strip() or 0)
            r = int(row[9].strip() or 0)
            h = int(row[10].strip() or 0)
            doubles = int(row[11].strip() or 0)
            triples = int(row[12].strip() or 0)
            hr = int(row[13].strip() or 0)
            rbi = int(row[14].strip() or 0)
            sb = int(row[15].strip() or 0)
            cs = int(row[16].strip() or 0)
            bb = int(row[17].strip() or 0)
            so = int(row[18].strip() or 0)
            ba = float(row[19].strip() or 0.0)
            obp = float(row[20].strip() or 0.0)
            slg = float(row[21].strip() or 0.0)
            ops = float(row[22].strip() or 0.0)
            opsplus = int(row[23].strip() or 0)
            rOBA = float(row[24].strip() or 0.0)
            rbatplus = int(row[25].strip() or 0)
            tb = int(row[26].strip() or 0)
            gidp = int(row[27].strip() or 0)
            hbp = int(row[28].strip() or 0)
            sh = int(row[29].strip() or 0)
            sf = int(row[30].strip() or 0)
            ibb = int(row[31].strip() or 0)
            pos = map_position(row[32].strip())

            # Create the payload
            payload = {
                "bbrefId": bbrefId,
                "name": name,
                "age": age,
                "year": 2024,
                "team": team,
                "lg": lg,
                "war": war,
                "g": g,
                "pa": pa,
                "ab": ab,
                "r": r,
                "h": h,
                "doubles": doubles,
                "triples": triples,
                "hr": hr,
                "rbi": rbi,
                "sb": sb,
                "cs": cs,
                "bb": bb,
                "so": so,
                "ba": ba,
                "obp": obp,
                "slg": slg,
                "ops": ops,
                "opSplus": opsplus,
                "rOBA": rOBA,
                "rbatplus": rbatplus,
                "tb": tb,
                "gidp": gidp,
                "hbp": hbp,
                "sh": sh,
                "sf": sf,
                "ibb": ibb,
                "pos": pos,
                "date": datetime.now().isoformat()
            }

            # Make the POST request
            response = requests.post(api_url, headers=headers, json=payload, verify=False)
            if response.status_code == 201:
                print(f"Successfully posted {name} ({bbrefId}) to the database.")
            else:
                print(f"Failed to post {name} ({bbrefId}). Status Code: {response.status_code}, Response: {response.text}")

        except ValueError as e:
            print(f"Skipping row due to data conversion error: {row} - Error: {e}")
        except IndexError as e:
            print(f"Skipping row due to missing data: {row} - Error: {e}")
