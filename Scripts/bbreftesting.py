import time
import logging
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_driver(chromedriver_path, headless=True):
    """Set up and return a configured Chrome WebDriver"""
    logger.info("Setting up Chrome WebDriver...")
    
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Skip SSL certificate verification (for corporate environments)
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    
    # Initialize the Chrome WebDriver with the configured options
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def test_access_player_page(chromedriver_path):
    """Test accessing a Baseball-Reference player page with Selenium"""
    driver = setup_driver(chromedriver_path, headless=True)
    url = "https://www.baseball-reference.com/players/c/correca01.shtml"
    
    try:
        logger.info(f"Accessing URL: {url}")
        driver.get(url)
        
        # Wait for Cloudflare challenge to complete
        logger.info("Waiting for page to load (allowing time for Cloudflare challenge)...")
        time.sleep(10)  # Wait for Cloudflare to process
        
        # Check the current URL to see if we've been redirected
        current_url = driver.current_url
        logger.info(f"Current URL after waiting: {current_url}")
        
        # Get the page title
        title = driver.title
        logger.info(f"Page title: {title}")
        
        # Check if we got past Cloudflare
        if "Just a moment" in title:
            logger.warning("Still on Cloudflare challenge page after waiting")
        else:
            logger.info("Successfully bypassed Cloudflare challenge!")
            
            # Try to find the player name element
            try:
                player_name_elements = driver.find_elements(By.CSS_SELECTOR, "h1[itemprop='name']")
                if player_name_elements:
                    logger.info(f"Found player name: {player_name_elements[0].text}")
                else:
                    logger.info("Could not find player name element with CSS selector")
                    
                    # Try a more general approach
                    h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                    if h1_elements:
                        logger.info(f"Found h1 element: {h1_elements[0].text}")
                    else:
                        logger.info("No h1 elements found on page")
            except Exception as e:
                logger.error(f"Error finding player name element: {e}")
            
            # Get page source
            page_source = driver.page_source
            logger.info(f"Page source length: {len(page_source)} characters")
            logger.info(f"First 500 characters of page source: {page_source[:500]}...")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Closing WebDriver...")
        driver.quit()

if __name__ == "__main__":
    logger.info("Starting test script")
    
    # Set path to ChromeDriver
    # You need to download ChromeDriver from https://chromedriver.chromium.org/downloads
    # and place it in the same directory as this script or specify the full path
    default_chromedriver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    
    # Allow specifying chromedriver path as command-line argument
    chromedriver_path = sys.argv[1] if len(sys.argv) > 1 else default_chromedriver_path
    
    if not os.path.exists(chromedriver_path):
        logger.error(f"ChromeDriver not found at {chromedriver_path}")
        logger.error("Please download ChromeDriver from https://chromedriver.chromium.org/downloads")
        logger.error("and place it in the same directory as this script or specify the path as an argument.")
        sys.exit(1)
    
    logger.info(f"Using ChromeDriver at {chromedriver_path}")
    test_access_player_page(chromedriver_path)