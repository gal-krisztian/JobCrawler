import requests
import random
from time import sleep
from bs4 import BeautifulSoup

def manage_request(p_href):
    max_retries = 3
    retry_count = 0
    page = None

    # Send request but if it raises a timeout error tries again up to 2 times
    while retry_count < max_retries:
        try:
            page = requests.get(p_href)
            retry_count = 3
            
        except requests.exceptions.ConnectTimeout as e:
            error, = e.args
            print(f"Error code: {error.code}, Error message: {error.message}")
            retry_count =+ 1
        
    return page

def load_soup(p_page):
    soup = None

    soup = BeautifulSoup(p_page.content, "html.parser")

    return soup

def wait():
    seconds_to_wait = random.randint(0, 2)
    sleep(seconds_to_wait)