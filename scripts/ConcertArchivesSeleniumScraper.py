import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from datetime import datetime
from selenium.webdriver.chrome.service import Service

class ConcertScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with Chrome options"""
        self.options = Options()
        
        # Advanced anti-detection measures
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-gpu')
        
        # More realistic browser behavior
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-plugins')
        self.options.add_argument('--disable-images')
        self.options.add_argument('--disable-javascript-harmony-shipping')
        self.options.add_argument('--disable-background-timer-throttling')
        self.options.add_argument('--disable-backgrounding-occluded-windows')
        self.options.add_argument('--disable-renderer-backgrounding')
        self.options.add_argument('--disable-features=TranslateUI')
        
        # Media and autoplay related fixes
        self.options.add_argument('--autoplay-policy=no-user-gesture-required')
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--disable-features=VizDisplayCompositor')
        self.options.add_argument('--mute-audio')
        
        # Console log suppression
        self.options.add_argument('--log-level=3')
        self.options.add_argument('--disable-logging')
        self.options.add_argument('--silent')
        
        # Randomize user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Add additional headers to appear more human-like
        self.options.add_argument('--accept-language=en-US,en;q=0.9')
        
        if headless:
            self.options.add_argument('--headless')
            
        self.driver = None
        self.concerts_data = []
        
    def start_driver(self):
        """Start the Chrome driver"""
        self.driver = webdriver.Chrome(options=self.options)
        
        # Execute script to hide webdriver property and other automation indicators
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Override the plugins array to make it look more realistic
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        
        # Override the languages property
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
        # Set window size to appear more human-like
        self.driver.set_window_size(1920, 1080)
        
        # Suppress console errors and warnings
        try:
            self.driver.execute_cdp_cmd('Log.enable', {})
            self.driver.execute_cdp_cmd('Log.clear', {})
            
            # Set autoplay policy
            self.driver.execute_cdp_cmd('Page.setAutoplayPolicy', {'policy': 'no-user-gesture-required'})
        except Exception as e:
            print(f"Warning: Could not set CDP commands: {e}")
    
    def simulate_human_behavior(self):
        """Simulate human-like behavior"""
        # Random mouse movements
        actions = ActionChains(self.driver)
        
        # Move mouse to random positions
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1000)
            y = random.randint(100, 600)
            actions.move_by_offset(x, y)
            time.sleep(random.uniform(0.1, 0.3))
        
        actions.perform()
        
        # Random scroll
        scroll_amount = random.randint(100, 500)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
        time.sleep(random.uniform(0.5, 1.5))
        
        # Scroll back up
        self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount})")
        time.sleep(random.uniform(0.5, 1.0))
        
    def wait_for_cloudflare(self, timeout=60):
        """Wait for Cloudflare validation to complete"""
        print("Waiting for Cloudflare validation...")
        print("Please complete any manual verification if prompted...")
        
        # Wait for the page to load and Cloudflare to complete
        try:
            # Wait for the concert table to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.ID, "concert-table"))
            )
            print("✓ Cloudflare validation completed")
            return True
        except TimeoutException:
            print("⚠ Timeout waiting for Cloudflare validation")
            return False
    
    def extract_concert_data(self):
        """Extract concert data from the current page"""
        try:
            # Wait for the table to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "concert-table"))
            )
            
            # Find all concert rows
            table = self.driver.find_element(By.ID, "concert-table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            page_concerts = []
            
            for row in rows[1:]:  # Skip header row
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:  # Ensure we have enough columns
                        date = cells[0].text.strip()
                        concert = cells[1].text.strip()
                        venue = cells[2].text.strip()
                        location = cells[3].text.strip()
                        
                        concert_data = {
                            'date': date,
                            'concert': concert,
                            'venue': venue,
                            'location': location
                        }
                        
                        page_concerts.append(concert_data)
                        
                except Exception as e:
                    print(f"Error extracting row data: {e}")
                    continue
            
            return page_concerts
            
        except Exception as e:
            print(f"Error extracting concert data: {e}")
            return []
    
    def scrape_page(self, page_num, retry_count=0):
        """Scrape a single page with retry logic"""
        url = f"https://www.concertarchives.org/locations/detroit-mi?date=past&page={page_num}#concert-table"
        
        print(f"Scraping page {page_num}...")
        
        try:
            # Start with a clean session if retrying
            if retry_count > 0:
                print(f"Retry attempt {retry_count} for page {page_num}")
                time.sleep(random.uniform(5, 10))
            
            # Navigate to the page
            self.driver.get(url)
            
            # Check if we got a 403 or other error
            if "403" in self.driver.title or "forbidden" in self.driver.title.lower():
                print(f"403 Forbidden error on page {page_num}")
                if retry_count < 3:
                    print("Attempting to bypass 403 error...")
                    
                    # Try going to the main page first
                    self.driver.get("https://www.concertarchives.org/")
                    time.sleep(random.uniform(3, 6))
                    
                    # Simulate human behavior
                    self.simulate_human_behavior()
                    
                    # Now try the actual page
                    return self.scrape_page(page_num, retry_count + 1)
                else:
                    print(f"Max retries reached for page {page_num}")
                    return []
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Wait for Cloudflare validation on first page or if needed
            if page_num == 89 or retry_count > 0:  # First page or retry
                if not self.wait_for_cloudflare():
                    print(f"Failed to load page {page_num}")
                    return []
            else:
                # For subsequent pages, wait a bit and check if loaded
                time.sleep(random.uniform(2, 4))
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "concert-table"))
                    )
                except TimeoutException:
                    print(f"Page {page_num} didn't load properly, may need manual intervention")
                    
                    # Check for 403 error
                    if "403" in self.driver.page_source or "forbidden" in self.driver.page_source.lower():
                        print("Detected 403 error, attempting workaround...")
                        if retry_count < 3:
                            return self.scrape_page(page_num, retry_count + 1)
                    
                    input("Press Enter after resolving any issues...")
            
            # Extract data from current page
            page_data = self.extract_concert_data()
            print(f"✓ Extracted {len(page_data)} concerts from page {page_num}")
            
            return page_data
            
        except Exception as e:
            print(f"Error scraping page {page_num}: {e}")
            if retry_count < 3:
                return self.scrape_page(page_num, retry_count + 1)
            return []
    
    def scrape_all_pages(self, start_page=89, end_page=143):
        """Scrape all pages from start_page to end_page"""
        if not self.driver:
            self.start_driver()
        
        total_concerts = 0
        
        # Start with the main page to establish session
        print("Establishing session...")
        self.driver.get("https://www.concertarchives.org/")
        time.sleep(random.uniform(3, 6))
        self.simulate_human_behavior()
        
        for page_num in range(start_page, end_page + 1):
            try:
                page_data = self.scrape_page(page_num)
                self.concerts_data.extend(page_data)
                total_concerts += len(page_data)
                
                print(f"Total concerts collected so far: {total_concerts}")
                
                # Add random delay between pages to be more human-like
                delay = random.uniform(3, 8)
                print(f"Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
                
            except KeyboardInterrupt:
                print("\nScraping interrupted by user")
                break
            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                # Ask user if they want to continue
                choice = input("Continue to next page? (y/n): ").lower()
                if choice != 'y':
                    break
        
        print(f"\n✓ Scraping completed! Total concerts collected: {len(self.concerts_data)}")
        return self.concerts_data
    
    def save_to_csv(self, filename=None):
        """Save scraped data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detroit_concerts_{timestamp}.csv"
        
        if not self.concerts_data:
            print("No data to save")
            return
        
        df = pd.DataFrame(self.concerts_data)
        df.to_csv(filename, index=False)
        print(f"✓ Data saved to {filename}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"Total concerts: {len(self.concerts_data)}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Unique venues: {df['venue'].nunique()}")
        
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

# Alternative approach using requests session (add this after the main class)
import requests
from bs4 import BeautifulSoup

class RequestsConcertScraper:
    """Alternative scraper using requests session"""
    
    def __init__(self):
        self.session = requests.Session()
        self.concerts_data = []
        self.setup_session()
    
    def setup_session(self):
        """Setup session with headers to mimic a real browser"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        self.session.headers.update(headers)
    
    def scrape_page_requests(self, page_num):
        """Scrape using requests instead of Selenium"""
        url = f"https://www.concertarchives.org/locations/detroit-mi?date=past&page={page_num}"
        
        try:
            # First visit main page to establish session
            if page_num == 89:
                main_response = self.session.get("https://www.concertarchives.org/")
                if main_response.status_code != 200:
                    print(f"Failed to access main page: {main_response.status_code}")
                    return []
                time.sleep(2)
            
            # Now get the actual page
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 403:
                print(f"403 Forbidden for page {page_num}")
                return []
            elif response.status_code != 200:
                print(f"Error {response.status_code} for page {page_num}")
                return []
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the concert table
            table = soup.find('table', {'id': 'concert-table'})
            if not table:
                print(f"No concert table found on page {page_num}")
                return []
            
            # Extract data
            concerts = []
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    concert_data = {
                        'date': cells[0].get_text(strip=True),
                        'concert': cells[1].get_text(strip=True),
                        'venue': cells[2].get_text(strip=True),
                        'location': cells[3].get_text(strip=True)
                    }
                    concerts.append(concert_data)
            
            print(f"✓ Extracted {len(concerts)} concerts from page {page_num}")
            return concerts
            
        except Exception as e:
            print(f"Error scraping page {page_num}: {e}")
            return []

# Usage function combining both approaches
def scrape_with_fallback(start_page=89, end_page=143):
    """Try Selenium first, fallback to requests if needed"""
    print("Attempting to scrape with Selenium...")
    
    selenium_scraper = ConcertScraper(headless=False)
    
    try:
        # Try first page with Selenium
        selenium_scraper.start_driver()
        test_data = selenium_scraper.scrape_page(start_page)
        
        if test_data:
            print("✓ Selenium working, continuing with full scrape...")
            concerts = selenium_scraper.scrape_all_pages(start_page, end_page)
            selenium_scraper.save_to_csv()
            return concerts
        else:
            print("✗ Selenium failed, trying requests approach...")
            
    except Exception as e:
        print(f"Selenium error: {e}")
        print("Falling back to requests...")
        
    finally:
        selenium_scraper.close()
    
    # Try requests approach
    print("Attempting to scrape with requests...")
    requests_scraper = RequestsConcertScraper()
    
    all_concerts = []
    for page_num in range(start_page, end_page + 1):
        page_data = requests_scraper.scrape_page_requests(page_num)
        all_concerts.extend(page_data)
        
        if page_data:
            print(f"Total concerts so far: {len(all_concerts)}")
        
        # Random delay
        time.sleep(random.uniform(2, 5))
    
    # Save results
    if all_concerts:
        df = pd.DataFrame(all_concerts)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detroit_concerts_requests_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"✓ Saved {len(all_concerts)} concerts to {filename}")
    
    return all_concerts
    # Initialize scraper
    scraper = ConcertScraper(headless=False)  # Set to True for headless mode
    
    try:
        # Scrape pages 89-143
        concerts = scraper.scrape_all_pages(start_page=89, end_page=143)
        
        # Save to CSV
        scraper.save_to_csv()
        
        # Display first few records
        if concerts:
            print("\nFirst 5 concerts:")
            for i, concert in enumerate(concerts[:5]):
                print(f"{i+1}. {concert['date']} - {concert['concert']} at {concert['venue']}, {concert['location']}")
                
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()

# Alternative: Manual page-by-page scraping if you need more control
def manual_scrape_single_page(page_num):
    """Function to scrape a single page manually"""
    scraper = ConcertScraper(headless=False)
    scraper.start_driver()
    
    try:
        data = scraper.scrape_page(page_num)
        print(f"Found {len(data)} concerts on page {page_num}")
        
        # Save this page's data
        if data:
            df = pd.DataFrame(data)
            df.to_csv(f"page_{page_num}_concerts.csv", index=False)
            print(f"Saved to page_{page_num}_concerts.csv")
        
        return data
    finally:
        scraper.close()

# Utility function to combine multiple CSV files
def combine_csv_files(file_pattern="page_*_concerts.csv", output_file="all_concerts.csv"):
    """Combine multiple CSV files into one"""
    import glob
    
    files = glob.glob(file_pattern)
    if not files:
        print(f"No files found matching pattern: {file_pattern}")
        return
    
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_csv(output_file, index=False)
    print(f"Combined {len(files)} files into {output_file}")
    print(f"Total concerts: {len(combined_df)}")