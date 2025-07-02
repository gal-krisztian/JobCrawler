import re

# Getting the maximum number of pages
def get_page_count(p_soup):
    page_count = None

    page_count = p_soup.find("span", class_="jump-forward").a

    page_count = int(page_count["data-total"])

    return page_count

# Getting urls of "cards"
def get_page_urls(p_soup):
    job_card_urls = []

    job_cards = p_soup.find("ul", class_="job-cards").find_all("li")

    for job_card in job_cards:
        job_card_urls.append(job_card.get("data-link"))

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

    id = re.search("([0-9]{7})", p_url).group(1)

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

    job_details = p_soup.body.div.main.find("ul", class_="job-details-list p-0").find_all("h3", class_="sr-only")

    for job_detail in job_details:
        if job_detail.text.strip() == "Cég neve":
            company_name = p_soup.body.div.main.find("ul", class_="job-details-list p-0").find("h2", class_="my-auto").text.strip()

        elif job_detail.text.strip() == "Munkavégzés helye":
            try:
                company_address = p_soup.body.div.main.find("ul", class_="job-details-list p-0").find("span", itemprop="addressLocality").text.strip()
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
                    if line.strip() == "Számolja ki a nettó fizetést bérkalkulátorunkkal!" or line.strip() == "":
                        continue
                    else:
                        salary_details.append(line.strip())
        else:
            print(f"Egyéb kategória: {job_detail.text.strip()}:\n{p_url}")
    
    return company_name, company_address, salary_details