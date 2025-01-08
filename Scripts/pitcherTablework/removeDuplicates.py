import csv

# Read the input file
input_file = 'allpitchers.csv'
output_file = 'allpitchers_unique.csv'

# Dictionary to store unique entries by bbrefID
unique_pitchers = {}

# Open and read the input file
with open(input_file, mode='r') as file:
    csv_reader = csv.reader(file)
    
    # Process each row
    for row in csv_reader:
        # Extract bbrefID (the last column in each row)
        bbrefID = row[-1]
        
        # If bbrefID is not already in the dictionary, add the row
        if bbrefID not in unique_pitchers:
            unique_pitchers[bbrefID] = row
        else:
            print(f"Duplicate found and removed: {row}")

# Write the unique entries to the output file
with open(output_file, mode='w', newline='') as file:
    csv_writer = csv.writer(file)
    
    # Write each unique row to the output file
    for pitcher in unique_pitchers.values():
        csv_writer.writerow(pitcher)

print(f"Unique pitchers have been written to {output_file}")
