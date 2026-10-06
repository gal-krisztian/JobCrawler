from playwright.async_api import async_playwright
import json
import re
import itertools
from functions import load_soup, g_date_sql
from database import is_exists_table, create_table, get_values, insert_values, update_value, expand_table

async def get_urls(p_url):
    start_url = "https://www.stepstone.at"
    urls = []
    
    async with async_playwright() as pw:
        browser_ch = await pw.chromium.launch(headless=True, slow_mo=750)
        page_ch = await browser_ch.new_page()
        await page_ch.goto(p_url)

        try:
            await page_ch.click("text='Alles akzeptieren'")
        except:
            pass  # if button not found, ignore

        links = await page_ch.locator("xpath=//a[contains(@href, '/stellenangebote--')]").all()

        for link in links:
            href = await link.get_attribute("href")
            if href:
                urls.append(f"{start_url}{href}")

        await browser_ch.close()

        return urls
    
def get_id(p_url):
    id = None

    id = re.findall("([0-9]{6})", p_url)

    if id:
        return id[-1]

async def get_data(p_url):
    async with async_playwright() as pw:
        browser_ch = await pw.chromium.launch(headless=True, slow_mo=750)
        page_ch = await browser_ch.new_page()
    
        await page_ch.goto(p_url)

        html = await page_ch.content()
        soup = load_soup(html)
        script = soup.find("script", type="application/ld+json")
        
        if not script:
            print(f"No JSON script found for {p_url}")
            return None, None, None
            
        data = json.loads(script.string)

        position = data.get("title", "")
        company_name = data.get("hiringOrganization", {}).get("name", "")
        street = data.get("jobLocation", {}).get("address", {}).get("streetAddress", "")
        locality = data.get("jobLocation", {}).get("address", {}).get("addressLocality", "")
        company_address = f"{street}, {locality}".strip(", ")

        await browser_ch.close()

        return position, company_name, company_address

async def scrape_stepstone(p_cursor):
    source = "Stepstone"
    start_url = "https://www.stepstone.at"
    search_location = "tirol"
    schema = "JOBCRAWLER"
    table = "SCRAPE_STEPSTONE_RAW"
    urls = []

    if is_exists_table(p_cursor, schema, table) == 0:
        columns = dict(tnd="date", source="varchar2(30)", status="varchar2(1)", status_from="date", status_to="date")

        create_table(p_cursor, schema, table, columns)

    saved_urls = get_values(p_cursor, schema, "scrape_job", "url", f"status = 'A' and source = '{source}'")

    for i in itertools.count(1):
        urls.clear()
        recent_page = f"{start_url}/jobs/in-{search_location}?radius=5&page={i}&searchOrigin=Homepage_top-search"

        try:
            urls = await get_urls(recent_page)

            if urls == []:
                break

            for url in urls:
                id = get_id(url)

                if any(id in saved_url['URL'] for saved_url in saved_urls):
                    update_value(p_cursor, schema, "scrape_job", "status_to", g_date_sql, f"url = '{url}'")
                    continue
                else:
                    position, company_name, company_address = await get_data(url)

                    if position is None and company_name is None and company_address is None:
                        continue

                    salary_details = ""

                    expand_table(p_cursor, schema, table, id, url, position, company_name, company_address, salary_details)

                    insert_values(p_cursor, schema, table, source, id, url, position, company_name, company_address, salary_details)

        except Exception as e:
            break

        print(f"Stepstone: {i} oldal van kész.")