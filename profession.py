from database import g_date_sql, is_exists_table, create_table, get_values, update_value, expand_table, insert_values
from functions import manage_request, load_soup, timestamp
import re

# Getting the maximum number of pages
def get_page_count(p_soup):
    page_count = None

    page_count = p_soup.find("div", class_="dsx-pagination-jump-item jump-forward").find_next("a")

    page_count = int(page_count.text.strip())

    return page_count

# Getting urls of "cards"
def get_page_urls(p_soup):
    job_card_urls = []

    job_cards = p_soup.find("div", class_="list-page-content").find_all("li", class_="advertisement-result-list-item")

    for job_card in job_cards:
        if job_card.get("data-link"):
            job_card_urls.append(job_card.get("data-link"))
        else:
            None

    return job_card_urls

# Getting url of a job
def get_url(p_soup):
    url = None

    url = p_soup.head.find(rel = "canonical")

    if url:
        url = url.get("href")

    return url

# Getting id via regular expression out of url
def get_id(p_url):
    id = None

    try:
        id = re.search("allas.*([0-9]{7})", p_url).group(1)
    except TypeError:
        print(f"Attribute error, get_id: {p_url}")

    return id

# Getting the name of the position
def get_position(p_soup):
    position = None

    position = p_soup.body.div.main.find(id="job-title")

    if position:
        position = position.text.strip()
    
    return position

# Getting a company's name, address and salary (and benefits in some cases like bonus or premium)
def get_co_info_salary(p_soup, p_url):
    company_name = None
    company_address = None
    unfiltered_salary_details = []
    salary_details = []

    try:
        job_details = p_soup.body.div.main.find("ul", class_="job-details-list p-0").find_all("h3", class_="sr-only")
    except AttributeError:
        print(f"Attribute error, job_details: {p_url}")
        return

    for job_detail in job_details:
        if job_detail.text.strip() == "Cég neve":
            company_name = p_soup.body.div.main.find("ul", class_="job-details-list p-0").find("h2", class_="my-auto").text.strip()

        elif job_detail.text.strip() == "Munkavégzés helye":
            try:
                company_address = p_soup.body.div.main.find("ul", class_="job-details-list p-0").find("span", itemprop="addressLocality").text.strip()
            except AttributeError:
                try:
                    company_address = job_detail.find_next("div").text.strip()
                except AttributeError:
                    print(f"Attribute error, Munkavégzés helye: {p_url}")

        elif job_detail.text.strip() == "Fizetés":
            salary = p_soup.body.div.main.find("div", class_="my-auto salary-info")

            if salary.find(True).name == "div":
                salary_details.append(salary.text.splitlines()[1].strip())

            elif salary.find(True).name == "span":
                salary_alt = salary.find_all("span")

                for salary in salary_alt:
                    unfiltered_salary_details.append(f"{salary.text.strip()} {salary.next_sibling.strip()}")
                for line in unfiltered_salary_details:
                    if line.strip() == "Számolja ki a nettó fizetést bérkalkulátorunkkal!" or line.strip() == "" or line.strip() == "Számold ki a nettó fizetést bérkalkulátorunkkal!":
                        continue
                    else:
                        salary_details.append(line.strip())
        else:
            print(f"Egyéb kategória: {job_detail.text.strip()}:\n{p_url}")
    
    return company_name, company_address, salary_details

def get_job_properties(p_soup):
    time_properties = []
    emp_type = None    

    job_properties = p_soup.body.div.main.find("div", class_="side-box__content d-block ecom-preview-d-block").find_all("div", class_="data-box")

    for job_property in job_properties:
        if job_property.find(alt="Munkaidő és munkarend ikon"):
            time_details = job_property.find_all("span")
            for time_detail in time_details[1:]:
                time_properties.append(f"{time_detail.text.strip()} {time_detail.next_sibling.strip()}")

    for time_property in time_properties:
        if time_property.strip() in ["Teljes munkaidő", "Részmunkaidő"]:
            emp_type = time_property
            break
        else:
            emp_type = ""

    return emp_type

def get_category(p_soup):
    job_category = p_soup.body.main.find("div", class_="separator-parent").find_all("span")

    category1, category2 = job_category[:2]

    return category1.text.strip(), category2.text.strip()

def scrape_profession(p_cursor):
    source = "Profession"
    start_url = "https://www.profession.hu/allasok"
    schema = "JOBCRAWLER"
    table = "SCRAPE_PROFESSION_RAW"

    # Check if the table exists for the raw data, if not create it
    if is_exists_table(p_cursor, schema, table) == 0:
        columns = dict(tnd = "date", source = "varchar2(30)", status = "varchar2(1)", status_from = "date", status_to = "date")

        create_table(p_cursor, schema, table, columns)

    # Load the initial page
    page = manage_request(start_url)

    # If there is no page to load then abort running
    if page is None:
        return
    
    # Parsing page
    soup = load_soup(page)

    # Get maximum page number to loop through
    page_count = get_page_count(soup)

    # Getting all the ids that are already in the database
    saved_ids = get_values(p_cursor, schema, "scrape_job", "id", f"status = 'A' and source = '{source}'")

    # Loop through every page
    for page_number in range(1, page_count + 1, 1):
        
        recent_page = f"{start_url}/{page_number}"

        page = manage_request(recent_page)

        if page is None:
            continue

        soup = load_soup(page)

        # In case of a page was deleted since starting the scraping
        try:
            job_card_urls = get_page_urls(soup)
        except AttributeError as e:
            print(f"{recent_page}\nError message: {e}")
            continue

        # Loop through every job's page
        for recent_url in job_card_urls:
            try:
                id = get_id(recent_url)

                if any(id in saved_id['ID'] for saved_id in saved_ids):
                    update_value(p_cursor, schema, "scrape_job", "status_to", g_date_sql, f"id = {id}")
                    continue

            except Exception as e:
                #error, = e.args
                #print(f"{recent_url}\nError code: {error.code}, Error message: {error.message}")
                print(e.args)
                continue

            page = manage_request(recent_url)

            if page is None:
                continue
            
            try:

                soup = load_soup(page)

                url = get_url(soup)

                position = get_position(soup)

                company_name, company_address, salary_details = get_co_info_salary(soup, url)

                emp_type = get_job_properties(soup)

                category1, category2 = get_category(soup)

            except Exception as e:
                print(f"{recent_url}\nError: {e}")
                continue

            expand_table(p_cursor, schema, table, id, url, position, company_name, company_address, salary_details, emp_type, category1, category2)

            insert_values(p_cursor, schema, table, source, id, url, position, company_name, company_address, salary_details, emp_type, category1, category2)

        print(f"Profession: {page_number} oldal van kész a {page_count}-ból. {timestamp()}")