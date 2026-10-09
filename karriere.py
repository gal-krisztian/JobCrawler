from playwright.async_api import async_playwright
from database import is_exists_table, create_table, get_values, insert_values, update_value, expand_table
from functions import g_date_sql, manage_request, load_soup
import json

async def get_id():
    start_url = "https://www.karriere.at/"
    search_location = "tirol"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, slow_mo=1000)
        page = await browser.new_page()
        await page.goto(start_url)

        # Scroll down to trigger cookie popup
        await page.keyboard.press("End")
        await accept_cookies(page)

        # Fill in search criteria
        await page.locator('input[name="locations"]').fill(search_location)

        # Click search
        await page.get_by_role("button", name="Jobs finden").click()

        # Keep clicking "Load more jobs" until it disappears
        while True:
            try:
                await page.locator('button.m-loadMoreJobsButton__button').click()
            except:
                break

        # Collect all job IDs
        elements = await page.locator('li.m-jobsList__item').all()
        ids = []
        for element in elements:
            try:
                job_url = await element.locator('a.m-jobsListItem__titleLink').get_attribute('href')
            except:
                continue
            job_id = job_url.split('/')[-1] if job_url else None
            if job_id:
                ids.append(job_id)

        await browser.close()

    return ids

async def accept_cookies(p_page):
    try:
        await p_page.locator("#onetrust-accept-btn-handler").click(timeout=60000)
        print("Cookies accepted.")
    except:
        print("No cookie popup shown.")


def get_position(p_data):
        position = p_data.get("title", "")

        return position

def get_company_name(p_data):
        company_name = p_data.get("hiringOrganization", {}).get("name", "")
        
        return company_name
        
def get_company_address(p_data):
        company_address = ", ".join(location.get("address", {}).get("addressLocality", "") for location in p_data["jobLocation"])
        
        return company_address
       
def get_salary_details(p_data):
        salary_details = p_data.get("baseSalary", {}).get("currency", "") + " " + str(p_data.get("baseSalary", {}).get("value", {}).get("value", "")) + " " + p_data.get("baseSalary", {}).get("value", {}).get("unitText", "")
        return salary_details

async def scrape_karriere(p_cursor):
    source = "Karriere"
    start_url = "https://www.karriere.at/"
    schema = "JOBCRAWLER"
    table = "SCRAPE_KARRIERE_RAW"

    # Check if the table exists for the raw data, if not create it
    if is_exists_table(p_cursor, schema, table) == 0:
        columns = dict(tnd="date", source="varchar2(30)", status="varchar2(1)", status_from="date", status_to="date")

        create_table(p_cursor, schema, table, columns)

    saved_ids = get_values(p_cursor, schema, "scrape_job", "id", f"status = 'A' and source = '{source}'")

    ids = await get_id()

    # Open all the IDs of the job listings one by one
    for id in ids:
        if any(id in saved_id['ID'] for saved_id in saved_ids):
            update_value(p_cursor, schema, "scrape_job", "status_to", g_date_sql, f"id = {id}")
            continue
        
        url = f"{start_url}jobs/{id}"
        
        page = manage_request(url)

        if page is None:
            continue

        soup = load_soup(page)

        # Get the data via json containing job details
        script = soup.find("script", type="application/ld+json")

        if not script:
            print(f"No JSON script found for {url}")
            continue

        data = json.loads(script.string)

        position = get_position(data)

        if data.get("hiringOrganization", "") == "confidential":
            company_name = f"Employer does not wish to disclose any information for {url}"
            continue
        else:
            company_name = get_company_name(data)

        company_address = get_company_address(data)

        salary_details = get_salary_details(data)

        expand_table(p_cursor, schema, table, id, url, position, company_name, company_address, salary_details, None, None, None)

        insert_values(p_cursor, schema, table, source, id, url, position, company_name, company_address, salary_details, None, None, None)

    print("Karriere: kész.")