import requests
import random
from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime

g_date_sql = f"to_date('{datetime.now().strftime("%Y-%m-%d")}', 'YYYY-MM-DD')"

def manage_request(p_href, params=None, headers=None):
    page = None
    max_retries = 3
    retry_count = 0

    # Send request but if it raises a timeout error tries again up to 2 times
    while retry_count < max_retries:
        try:
            page = requests.get(p_href, params=params, headers=headers, timeout=30)
            wait(0.2, 0.5)
            retry_count = 3
            return page
            
        except requests.exceptions.ConnectTimeout as error:
            print(f"Connection timed out: {error}")
            retry_count += 1
            page = None

def load_soup(p_page):
    
    # If p_page is a requests.Response, use .content
    if hasattr(p_page, "content"):
        return BeautifulSoup(p_page.content, "html.parser")
    # If it's already a string (like from Playwright)
    elif isinstance(p_page, str):
        return BeautifulSoup(p_page, "html.parser")
    else:
        raise TypeError("Unsupported type!")

def wait(min_wait, max_wait):
    sleep(random.uniform(min_wait, max_wait))

# The rest exists for testing purposes

def save_file(p_path, p_page=None):
    with open(p_path, "w", encoding="utf-8") as file:
        file.write(p_page.text)

def load_file(p_path="./Files"):
    with open(p_path, "r", encoding="utf-8") as file:
        return file.read()
    
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_number(p_number = 0):
    clean_number = p_number.replace(" ", "").replace(",", ".")

    try:
        return float(clean_number)
    except ValueError:
        print(f"Error parsing number: {p_number}")
        return 0