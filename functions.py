import requests
import random
from time import sleep
from bs4 import BeautifulSoup

def manage_request(p_href, params=None, headers=None):
    page = None
    max_retries = 3
    retry_count = 0

    # Send request but if it raises a timeout error tries again up to 2 times
    while retry_count < max_retries:
        try:
            page = requests.get(p_href, params=params, headers=headers, timeout=10)
            wait(1, 2) 
            retry_count = 3
            
        except requests.exceptions.ConnectTimeout as e:
            error, = e.args
            print(f"Error code: {error.code}, Error message: {error.message}")
            retry_count += 1
        
    return page

def load_soup(p_page):
    soup = None
    
    soup = BeautifulSoup(p_page.content, "html.parser")

    return soup

def wait(min_wait, max_wait):
    sleep(random.randint(min_wait, max_wait))