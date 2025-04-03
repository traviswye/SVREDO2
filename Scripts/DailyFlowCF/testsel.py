import sys
import traceback

def scrape_with_selenium(url, driver_path=None):
    """Use Selenium to scrape a page, with improved handling of Cloudflare challenges"""
    try:
        logger.info("Attempting to scrape with Selenium...")
        
        # Selenium imports should already be available from the top of the script
        
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={get_random_user_agent()}")
        options.add_argument("--disable-blink-features=AutomationControlled")  # Try to prevent detection
        
        # Always use the direct path specified at the top of the script
        if driver_path:
            # Use explicitly provided path (from function parameter)
            service = Service(executable_path=driver_path)
        elif os.path.exists(CHROMEDRIVER_PATH):
            # Use the path defined at the top of the script
            service = Service(executable_path=CHROMEDRIVER_PATH)
        elif os.path.exists("./chromedriver.exe"):
            # Fallback to current directory (Windows)
            service = Service(executable_path="./chromedriver.exe")
        elif os.path.exists("./chromedriver"):
            # Fallback to current directory (Linux/Mac)
            service = Service(executable_path="./chromedriver")
        else:
            logger.error("No chromedriver found. Please specify the correct path at the top of the script.")
            return None
            
        driver = webdriver.Chrome(service=service, options=options)
        
        # Set timeout and get the page
        driver.set_page_load_timeout(60)  # Increased timeout for Cloudflare
        logger.info(f"Navigating to {url} with Selenium...")
        driver.get(url)
        
        # Add extra wait for Cloudflare challenge to resolve
        logger.info("Waiting for Cloudflare to resolve...")
        
        # Wait for the page to load
        try:
            # First, check if we're on a Cloudflare challenge page
            if "cloudflare" in driver.page_source.lower() or "challenge" in driver.page_source.lower():
                logger.info("Detected Cloudflare challenge, waiting for it to resolve...")
                # Wait longer for Cloudflare - try multiple times
                wait_time = 5
                max_attempts = 6  # Total wait time up to 30 seconds
                
                for attempt in range(max_attempts):
                    time.sleep(wait_time)
                    
                    # Check if we're still on the challenge page
                    if "cloudflare" not in driver.page_source.lower() and "challenge" not in driver.page_source.lower():
                        logger.info("Cloudflare challenge appears to be resolved!")
                        break
                    
                    logger.info(f"Still on Cloudflare page after {(attempt+1)*wait_time} seconds, continuing to wait...")
                    
                    # On the last attempt, try refreshing the page
                    if attempt == max_attempts - 2:
                        logger.info("Trying to refresh the page...")
                        driver.refresh()
            
            # Now wait for the actual content to load - look for tables
            try:
                wait = WebDriverWait(driver, 15)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                logger.info("Table element found on page, content appears to be loaded")
            except Exception as e:
                logger.info(f"Timed out waiting for table element, but continuing anyway: {e}")
                # Continue anyway as the page might still be usable
        
        except Exception as e:
            logger.warning(f"Exception during page load wait: {e}")
            # Continue anyway - we might still have useful content
        
        # Get the final page source
        html_content = driver.page_source
        
        # Save for debugging
        save_html_for_debugging(html_content, "selenium_result.html")
        
        # Close the driver
        driver.quit()
        
        logger.info("Selenium scraping completed successfully")
        return html_content
        
    except Exception as e:
        logger.error(f"Error using Selenium: {e}")
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        return None


# Wrap the entire script in a try/except to catch any silent errors
try:
    # Add this at the very beginning of your script
    print("Script starting...")
    
    # Import your existing modules
    import cloudscraper
    from bs4 import BeautifulSoup, Comment
    import json
    from datetime import datetime
    import re
    import time
    import urllib3
    import logging
    import os
    import ssl
    import random
    import requests
    import traceback
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from urllib3.exceptions import InsecureRequestWarning
    
    print("Modules imported successfully")
    
    # Configure logging - modify this to ensure logs are written to both console and file
    log_file = "bbref_scraper_debug.log"
    print(f"Setting up logging to {log_file}")
    
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG to capture more detailed information
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)  # Ensure logs go to console
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configured")
    
    # Check if chromedriver path exists
    CHROMEDRIVER_PATH = "C:/buns/tw/SVREDO2/prodScripts/SeleniumVersions/chromedriver.exe"
    print(f"Checking chromedriver path: {CHROMEDRIVER_PATH}")
    if os.path.exists(CHROMEDRIVER_PATH):
        print(f"Chromedriver exists at: {CHROMEDRIVER_PATH}")
    else:
        print(f"ERROR: Chromedriver NOT FOUND at: {CHROMEDRIVER_PATH}")
    
    # Try importing Selenium and check version
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        print(f"Selenium imports successful. Selenium version: {webdriver.__version__}")
        selenium_available = True
    except ImportError as e:
        print(f"ERROR importing Selenium: {e}")
        selenium_available = False
    except Exception as e:
        print(f"Unexpected error with Selenium: {e}")
        selenium_available = False
    
    # Test creating a webdriver
    print("Testing Chrome webdriver creation...")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome webdriver created successfully!")
        driver.quit()
    except Exception as e:
        print(f"ERROR creating Chrome webdriver: {e}")
        traceback.print_exc()
    
    # Now run your main function
    print("Starting main execution...")
    
    def main():
        print("Inside main function")
        try:
            # Your existing main function code here
            # Just for testing, let's only do the warm-up part
            print("Attempting to connect to Baseball Reference...")
            warm_up_url = "https://www.baseball-reference.com/"
            result = scrape_with_selenium(warm_up_url, driver_path=CHROMEDRIVER_PATH)
            if result:
                print("Successfully connected to Baseball Reference")
            else:
                print("Failed to connect to Baseball Reference")
        except Exception as e:
            print(f"Error in main function: {e}")
            traceback.print_exc()
    
    # Call main function
    if __name__ == "__main__":
        print("Calling main function")
        main()
        print("Script execution completed")

except Exception as e:
    print(f"FATAL ERROR: {e}")
    traceback.print_exc()
    
# Add a pause at the end to prevent the window from closing immediately
print("\nPress Enter to exit...")
input()