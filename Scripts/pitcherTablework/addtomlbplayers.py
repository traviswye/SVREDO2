import csv

def generate_sql_insert_statements(csv_file_path):
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row if present
        
        for row in csv_reader:
            full_name, current_team, bbref_id = row
            sql_statement = f"INSERT INTO [NRFI].[dbo].[MLBplayers] (bbrefId, fullName, currentTeam) VALUES ('{bbref_id}', '{full_name}', '{current_team}');"
            print(sql_statement)

# Replace 'path_to_csv_file.csv' with the actual path to your CSV file
csv_file_path = 'allpitchers_unique.csv'
generate_sql_insert_statements(csv_file_path)
