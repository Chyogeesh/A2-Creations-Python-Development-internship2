import time
import csv
import zipfile
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def setup_driver():
    """Set up headless Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_rfq_page(driver, url):
    """Scrape RFQ data from a single page."""
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "rfq-item"))
    )
    time.sleep(2)  # Allow dynamic content to load
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    rfq_items = soup.find_all('div', class_='rfq-item')
    rfq_data = []
    
    for item in rfq_items:
        try:
            title_elem = item.find('div', class_='title')
            title = title_elem.text.strip() if title_elem else 'N/A'
            
            quantity_elem = item.find('div', class_='quantity')
            quantity = quantity_elem.text.strip() if quantity_elem else 'N/A'
            
            date_elem = item.find('div', class_='date')
            date = date_elem.text.strip() if date_elem else 'N/A'
            
            country_elem = item.find('div', class_='country')
            country = country_elem.text.strip() if country_elem else 'N/A'
            
            rfq_id_elem = item.find('div', class_='rfq-id')
            rfq_id = rfq_id_elem.text.strip() if rfq_id_elem else 'N/A'
            
            details_link_elem = item.find('a', class_='rfq-detail-link')
            details_link = urljoin(url, details_link_elem['href']) if details_link_elem and details_link_elem.get('href') else 'N/A'
            
            rfq_data.append({
                'RFQ Title': title,
                'Quantity': quantity,
                'Date Posted': date,
                'Country': country,
                'RFQ ID': rfq_id,
                'Details Link': details_link
            })
        except Exception as e:
            print(f"Error processing RFQ item: {e}")
            continue
    
    return rfq_data

def get_next_page(driver, current_url):
    """Get the URL of the next page if it exists."""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        next_button = soup.find('a', class_='next')
        if next_button and next_button.get('href'):
            return urljoin(current_url, next_button['href'])
        return None
    except Exception as e:
        print(f"Error finding next page: {e}")
        return None

def save_to_csv(data Hawkins data, filename='rfq_data.csv'):
    """Save scraped data to a CSV file."""
    fieldnames = ['RFQ Title', 'Quantity', 'Date Posted', 'Country', 'RFQ ID', 'Details Link']
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def create_zip(py_file, csv_file, zip_name='rfq_scraper_output.zip'):
    """Create a ZIP file containing the Python script and CSV file."""
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(py_file)
        zf.write(csv_file)

def main():
    base_url = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm?spm=a2700.8073608.1998677541.1.82be65aaoUUItC&country=AE&recently=Y&tracelog=newest"
    driver = setup_driver()
    all_rfq_data = []
    
    try:
        current_url = base_url
        while current_url:
            print(f"Scraping page: {current_url}")
            rfq_data = scrape_rfq_page(driver, current_url)
            all_rfq_data.extend(rfq_data)
            current_url = get_next_page(driver, current_url)
        
        if all_rfq_data:
            save_to_csv(all_rfq_data)
            print(f"Data saved to rfq_data.csv. Total RFQs scraped: {len(all_rfq_data)}")
            
            # Create ZIP file
            create_zip('alibaba_rfq_scraper.py', 'rfq_data.csv')
            print("ZIP file 'rfq_scraper_output.zip' created successfully.")
        else:
            print("No RFQ data found.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
