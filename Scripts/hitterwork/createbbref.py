import csv

def process_csv(input_file, output_file):
    seen_elements = set()  # To track seen elements
    output_lines = []  # To store lines that will be written to the new file

    # Read the input CSV file from bottom to top
    with open(input_file, 'r', encoding='utf-8') as csvfile:  # Specify UTF-8 encoding
        reader = list(csv.reader(csvfile))
        
        for line in reversed(reader):
            last_element = line[-1]  # Get the last element of the line
            
            if last_element not in seen_elements:
                seen_elements.add(last_element)  # Add the last element to the set
                output_lines.append(line)  # Add the line to the output lines

    # Write the output lines to the new CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:  # Specify UTF-8 encoding
        writer = csv.writer(csvfile)
        # Writing in reversed order to maintain the original order
        for line in reversed(output_lines):
            writer.writerow(line)

# Specify the input and output file paths
input_file = 'allplayers.txt'  # Replace with your actual input file path
output_file = 'cleanoutput.csv'  # Replace with your desired output file path

# Process the CSV file
process_csv(input_file, output_file)
