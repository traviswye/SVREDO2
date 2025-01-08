import csv
import requests
import json

def post_player_data(player_data):
    url = "https://localhost:44346/api/MLBPlayer"
    headers = {
        "accept": "text/plain",
        "Content-Type": "application/json"
    }
    
    payload = {
        "bbrefId": player_data[5],  # bbrefId
        "fullName": player_data[1],  # Full Name
        "currentTeam": player_data[3]  # Current Team
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    
    if response.status_code == 201:
        print(f"Successfully added: {player_data[1]} ({player_data[5]})")
    else:
        print(f"Failed to add: {player_data[1]} ({player_data[5]}) - Status Code: {response.status_code}")

def process_csv(input_file):
    with open(input_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        
        # Loop through each line in the CSV file
        for line in reader:
            post_player_data(line)

# Specify the input CSV file path
input_file = '"C:/Users/OWM2/CodeRoot/SharpViz/SharpViz/Scripts/hitterwork/cleanoutput.csv"'  # Replace with your actual input file path

# Process the CSV file and send POST requests
process_csv(input_file)
