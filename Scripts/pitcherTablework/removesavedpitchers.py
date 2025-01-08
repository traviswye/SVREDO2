import csv
import requests

# File paths
input_file = 'C:/Users/travis.wye/Documents/tw/viz/Scripts/pitcherTablework/allpitchers_unique.csv'
output_file = 'C:/Users/travis.wye/Documents/tw/viz/Scripts/pitcherTablework/cleanedpitchers.csv'

# API URL (assuming it's running locally)
api_base_url = "https://localhost:44346/api/Pitchers/"

# Function to check if pitcher exists in the database
def pitcher_exists(bbrefID):
    url = f"{api_base_url}{bbrefID}"
    try:
        response = requests.get(url, verify=False)  # Disable SSL verification for localhost
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error checking pitcher {bbrefID}: {e}")
        return False

# Dictionary to store unique entries that need to be written back to the file
remaining_pitchers = {}
removed_pitchers = []  # List to store removed pitchers

# Read and process the input file
with open(input_file, mode='r') as file:
    csv_reader = csv.reader(file)
    
    # Process each row
    for row in csv_reader:
        bbrefID = row[-1]
        
        # Check if the pitcher already exists in the database
        if not pitcher_exists(bbrefID):
            # If pitcher does not exist, add to remaining pitchers
            remaining_pitchers[bbrefID] = row
        else:
            # If pitcher exists, add to removed pitchers list
            removed_pitchers.append(row)
            print(f"Pitcher {bbrefID} already exists in the database. Removing from file.")

# Write the remaining pitchers back to the output file (overwriting it)
with open(output_file, mode='w', newline='') as file:
    csv_writer = csv.writer(file)
    
    # Write each remaining row to the output file
    for pitcher in remaining_pitchers.values():
        csv_writer.writerow(pitcher)

# Print out removed pitchers and the total count
print(f"\nTotal pitchers removed: {len(removed_pitchers)}")
print("Removed pitchers:")
for pitcher in removed_pitchers:
    print(pitcher)

print(f"\nRemaining pitchers have been written to {output_file}")
