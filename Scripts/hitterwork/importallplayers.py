import csv
import requests
import json
import time

def post_player_data(player_data):
    url = "https://localhost:44346/api/MLBPlayer"
    headers = {
        "accept": "text/plain",
        "Content-Type": "application/json"
    }
    
    payload = {
        "bbrefId": player_data[-1],  # bbrefId
        "fullName": player_data[1],  # Full Name
        "currentTeam": player_data[3]  # Current Team
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
            
            if response.status_code == 201:
                print(f"Successfully added: {player_data[1]} ({player_data[-1]})")
                break  # Exit the retry loop on success
            else:
                print(f"Failed to add: {player_data[1]} ({player_data[-1]}) - Status Code: {response.status_code}")
                # Retry only if a server error occurs (5xx status codes)
                if 500 <= response.status_code < 600:
                    time.sleep(2)  # Wait before retrying
                else:
                    break  # Do not retry for other errors like 4xx
        except Exception as e:
            print(f"Error occurred for player {player_data[1]} ({player_data[-1]}): {e}")
            time.sleep(2)  # Wait before retrying
        else:
            break  # Exit the loop if no exception occurred

def process_csv(input_file):
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        
        # Loop through each line in the CSV file
        for line in reader:
            post_player_data(line)

# Specify the input CSV file path
input_file = 'C:/Users/OWM2/CodeRoot/SharpViz/SharpViz/Scripts/hitterwork/cleanoutput.csv'  # Replace with your actual input file path

# Process the CSV file and send POST requests
process_csv(input_file)
