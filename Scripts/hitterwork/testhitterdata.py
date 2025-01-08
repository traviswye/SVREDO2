import csv

# File path to your CSV file
file_path = 'C:/Users/OWM2/CodeRoot/SharpViz/SharpViz/Scripts/hitterwork/allplayers.txt'

# Read and print the first few lines of the file
with open(file_path, 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    
    # Print the header
    header = next(reader)
    print("Header:")
    print(header)
    
    print("\nFirst few lines of data:")
    for i, row in enumerate(reader):
        print(row)
        if i >= 9:  # Change this number if you want more or fewer rows
            break
