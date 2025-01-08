# Define input and output file names
input_file = "hitterstoclean.txt"
output_file = "cleaned_bbrefids.txt"

try:
    # Open the input file with utf-8 encoding to handle special characters
    with open(input_file, "r", encoding="utf-8") as infile:
        lines = infile.readlines()

    # Process each line to extract the bbrefid (last field)
    bbrefids = [line.strip().split(",")[-1] for line in lines]

    # Write the extracted bbrefids to the output file
    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(bbrefids))

    print(f"Processed {len(bbrefids)} lines. Saved bbrefids to {output_file}.")
except FileNotFoundError:
    print(f"Error: The file {input_file} was not found. Please ensure it exists in the same directory as this script.")
except Exception as e:
    print(f"An error occurred: {e}")
