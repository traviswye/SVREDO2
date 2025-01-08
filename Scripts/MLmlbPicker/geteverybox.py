import requests
from bs4 import BeautifulSoup
import time
import csv
from datetime import datetime, timedelta

# Function to generate the URL for each day
def generate_url(year, month, day):
    return f"https://www.baseball-reference.com/boxes/index.fcgi?year={year}&month={month}&day={day}"

# Function to scrape the page for box score links
def scrape_box_scores(year, month, day):
    url = generate_url(year, month, day)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links that match the desired pattern
    box_scores = []
    for link in soup.find_all('a', href=True):
        if "/boxes/" in link['href'] and link['href'].endswith(".shtml"):
            box_scores.append(link['href'])
    
    return box_scores

# Function to save the box scores to a CSV file
def save_to_csv(data, filename='box_scores.csv'):
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def main():
    start_date = datetime(2024, 3, 20)
    end_date = datetime(2024, 9, 12)
    current_date = start_date

    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        day = current_date.day
        
        print(f"Scraping data for {month}/{day}/{year}...")
        
        box_scores = scrape_box_scores(year, month, day)
        data_to_save = [[current_date.strftime('%m/%d/%y'), link] for link in box_scores]
        
        if data_to_save:
            save_to_csv(data_to_save)
            print(f"Found {len(data_to_save)} box score(s) for {month}/{day}/{year}.")
        
        time.sleep(3)  # Wait for 3 seconds before the next request
        current_date += timedelta(days=1)

    print("Scraping completed!")

if __name__ == "__main__":
    main()
