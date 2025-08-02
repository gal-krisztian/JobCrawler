from functions import manage_request, load_soup
from profession import get_page_count, get_page_urls, get_url, get_id, get_position, get_co_info_salary
from database import open_database, close_database, is_exists_table, create_table, expand_table, insert_values, get_values, load_scrape_job, load_scrape_company
from data import process_address

def profession():
    source = "Profession"
    start_url = "https://www.profession.hu/allasok"
    schema = "JOBCRAWLER"
    table = "SCRAPE_PROFESSION_RAW"

    if is_exists_table(cursor, schema, table) == 0:
        columns = dict(tnd = "date", source = "varchar2(30)", status = "varchar2(1)", status_from = "date", status_to = "date")

        create_table(cursor, schema, table, columns)

    page = manage_request(start_url)

    # If there is no page to load then abort running
    if page is None:
        return
    
    # Parsing page
    soup = load_soup(page)

    # Get maximum page number to loop through
    page_count = get_page_count(soup)

    # Getting an error if expand_table has not been run yet
    saved_ids = get_values(cursor, schema, table, "id", "status = 'A'")

    # Loop through every page
    for page_number in range(1, page_count + 1, 1):
        
        recent_page = f"{start_url}/{page_number}"

        page = manage_request(recent_page)

        if page is None:
            continue

        soup = load_soup(page)

        job_card_urls = get_page_urls(soup)

        # Loop through every job's page
        for recent_url in job_card_urls:
            try:
                id = get_id(recent_url)

                if any(id in saved_id['ID'] for saved_id in saved_ids):
                    continue

            except AttributeError as e:
                error, = e.args
                print(f"{recent_url}\nError code: {error.code}, Error message: {error.message}")
                continue

            page = manage_request(recent_url)

            soup = load_soup(page)

            url = get_url(soup)

            position = get_position(soup)

            company_name, company_address, salary_details = get_co_info_salary(soup, url)

            expand_table(cursor, schema, table, id, url, position, company_name, company_address, salary_details)

            insert_values(cursor, schema, table, source, id, url, position, company_name, company_address, salary_details)

        print(f"{page_number} oldal van kész a {page_count}-ból.")

def load_profession():
    schema = "JOBCRAWLER"
    table = "SCRAPE_PROFESSION_RAW"
    company_id = None

    raw_ids = get_values(cursor, "JOBCRAWLER", "SCRAPE_PROFESSION_RAW", "id, company_name, company_address", "status = 'A'")

    job_ids = get_values(cursor, "JOBCRAWLER", "SCRAPE_JOB", "id", "status = 'A'")

    company_ids = get_values(cursor, "JOBCRAWLER", "SCRAPE_COMPANY", "id, company_name, company_full_address")

    # Create set to check if company already exists
    existing_companies = set((company["COMPANY_NAME"].strip().lower(), company["COMPANY_FULL_ADDRESS"].strip().lower()) for company in company_ids)

    for id in raw_ids:
        if any(id['ID'] == job_id['ID'] for job_id in job_ids):
            continue

        else:

            raw_com_name = id['COMPANY_NAME'].strip().lower()
            raw_com_address = id['COMPANY_ADDRESS'].strip().lower()

            if (raw_com_name, raw_com_address) in existing_companies:
                for company in company_ids:
                    if (company["COMPANY_NAME"].strip().lower() == raw_com_name and company["COMPANY_FULL_ADDRESS"].strip().lower() == raw_com_address):
                        company_id = company["ID"]
                        break
                
                load_scrape_job(cursor, "JOBCRAWLER", "SCRAPE_JOB", id['ID'], company_id)
            else:
                company_name, company_address, country, country_code, state, county, city, postcode, district, street, housenumber = process_address(cursor, schema, table, id['ID'])
            
                company_id = load_scrape_company(cursor, "JOBCRAWLER", "SCRAPE_COMPANY", company_name, company_address, country, country_code, state, county, city, postcode, district, street, housenumber)

                existing_companies.add((company_name.strip().lower(), company_address.strip().lower()))

                load_scrape_job(cursor, "JOBCRAWLER", "SCRAPE_JOB", id['ID'], company_id)


cursor = open_database()

profession()

load_profession()

close_database(cursor)