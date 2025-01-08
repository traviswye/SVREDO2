import csv

def generate_sql_update_statements(csv_file_path):
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row if present
        
        for row in csv_reader:
            full_name, bbref_id = row
            throws = 'LHP' if '*' in full_name else 'RHP'
            sql_statement = f"UPDATE Pitchers SET Throws = '{throws}' WHERE bbrefId = '{bbref_id}';"
            print(sql_statement)

# Replace 'path_to_csv_file.csv' with the actual path to your CSV file
csv_file_path = 'allpitchers_unique.csv'
generate_sql_update_statements(csv_file_path)
