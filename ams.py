from playwright.async_api import async_playwright
from database import is_exists_table, create_table, get_values, insert_values, update_value, expand_table
from functions import g_date_sql
import itertools

async def get_urls(p_url):
    start_url = "https://jobs.ams.at"
    urls = []

    async with async_playwright() as pw:
        browser_ch = await pw.chromium.launch(headless=True, slow_mo=750)
        page_ch = await browser_ch.new_page()
        await page_ch.goto(p_url)

        # Accept cookies
        try:
            await page_ch.click("text='Einverstanden'")
        except:
            pass  # if button not found, ignore

        # Collect job links
        links = await page_ch.locator("xpath=//a[contains(@href, '/public/emps/jobs/')]").all() #uuid
        for link in links:
            href = await link.get_attribute("href")
            if href:
                urls.append(f"{start_url}{href}")
            else:
                print(f"No href found for link: {link}")

        if await page_ch.locator('button[title="nächste Seite"]').locator('..').get_attribute("class") == "ams-page-item": # There is next page 
            next_button = True
        elif await page_ch.locator('button[title="nächste Seite"]').locator('..').get_attribute("class") == "ams-page-item disabled": # No next page
            next_button = False

        await browser_ch.close()

    return urls, next_button

async def get_data(p_url):
    async with async_playwright() as pw:
        browser_ch = await pw.chromium.launch(headless=True, slow_mo=750)
        page_ch = await browser_ch.new_page()
        await page_ch.goto(p_url)

        # Accept cookies if the banner exists
        try:
            await page_ch.click("text='Einverstanden'")
        except:
            pass

        # Extract values
        id_locator = page_ch.locator("#ams-detail-adgId [data-testid='key-value-pair-content']")
        position_locator = page_ch.locator("#ams-detail-details-header.fw-semibold")
        company_name_locator = page_ch.locator("#ams-detail-companyname-text")
        company_address_locator = page_ch.locator("#ams-detail-location [data-testid='key-value-pair-content']")

        id = (await id_locator.text_content() or "").strip()
        position = (await position_locator.text_content() or "").strip()
        company_name = (await company_name_locator.text_content() or "").strip()
        company_address = (await company_address_locator.text_content() or "").strip()

        await browser_ch.close()

    return id, position, company_name, company_address

async def scrape_ams(p_cursor):
    source = "AMS"
    start_url = "https://jobs.ams.at"
    search_location = "tirol"
    schema = "JOBCRAWLER"
    table = "SCRAPE_AMS_RAW"

    if is_exists_table(p_cursor, schema, table) == 0:
        columns = dict(tnd="date", source="varchar2(30)", status="varchar2(1)", status_from="date", status_to="date")

        create_table(p_cursor, schema, table, columns)

    saved_urls = get_values(p_cursor, schema, "scrape_job", "url", f"status = 'A' and source = '{source}'")

    for i in itertools.count(1):
        recent_page = f"{start_url}/public/emps/jobs?page={i}&location={search_location}"
        
        try:
            urls, is_next_page = await get_urls(recent_page)

            for url in urls:
                if any(url in saved_url['URL'] for saved_url in saved_urls):
                    update_value(p_cursor, schema, "scrape_job", "status_to", g_date_sql, f"url = '{url}'")
                    continue
                else:
                    id, position, company_name, company_address = await get_data(url)

                    salary_details = ""

                    expand_table(p_cursor, schema, table, id, url, position, company_name, company_address, salary_details, None, None, None)

                    insert_values(p_cursor, schema, table, source, id, url, position, company_name, company_address, salary_details, None, None, None)

            if is_next_page is False:
                break

        except Exception as e:
            break

        print(f"AMS: {i} oldal van kész.")