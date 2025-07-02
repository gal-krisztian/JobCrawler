from functions import manage_request, load_soup, wait
from profession import get_page_count, get_page_urls, get_url, get_id, get_position, get_co_info_salary
from database import open_database, close_database, is_exists_table, create_table, expand_table, insert_values

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
            wait()
            try:
                id = get_id(recent_url)
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

cursor = open_database()

profession()

close_database(cursor)