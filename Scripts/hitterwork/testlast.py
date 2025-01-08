import requests
import json

# Define the API URL
url = 'https://localhost:44346/api/HitterLast7'

# Define the payload
payload = {
    "id": 0,
    "bbrefId": "wilsoja05",
    "dateUpdated": "2024-08-28T13:23:56.777262",
    "team": "OAK",
    "pos": "SS",
    "name": "Jacob Wilson",
    "ab": 4,
    "r": 1,
    "hr": 0,
    "rbi": 0,
    "sb": 0,
    "avg": 0.25,
    "obp": 0.25,
    "h": 1,
    "twoB": 0,
    "threeB": 0,
    "bb": 0,
    "k": 1,
    "slg": 0.25,
    "ops": 0.5,
    "rostered": 5.0
}

# Make the POST request to the API with SSL verification disabled
try:
    response = requests.post(url, json=payload, verify=False)
    if response.status_code == 201:
        print("Successfully posted data:", response.json())
    else:
        print(f"Failed to post data: {response.status_code}, {response.text}")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
