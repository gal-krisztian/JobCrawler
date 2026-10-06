from functions import g_date_sql
from database import close_database, get_values, load_scrape_job, load_scrape_company, update_value
from data import process_address, process_salary

def main_load(p_cursor):
    schema = "JOBCRAWLER"
    source_table = list(("SCRAPE_PROFESSION_RAW", "SCRAPE_KARRIERE_RAW", "SCRAPE_AMS_RAW", "SCRAPE_STEPSTONE_RAW"))
    target_tables = dict(job="SCRAPE_JOB", company="SCRAPE_COMPANY")

    for table in source_table:
        raw_ids = get_values(p_cursor, schema, table, "id, company_name, company_address", "status = 'A'")

        job_ids = get_values(p_cursor, schema, target_tables["job"], "id") # Put this back after dealing with deleted records in raw: , "status = 'A'

        company_ids = get_values(p_cursor, schema, target_tables["company"], "id, company_name, company_full_address")

        # Create set to check if company already exists
        existing_companies = set((company["COMPANY_NAME"].strip().lower(), company["COMPANY_FULL_ADDRESS"].strip().lower()) for company in company_ids)

        try:
            for id in raw_ids:
                company_id = None
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
                        
                    else:
                        company_name, company_address, country, country_code, state, county, city, postcode, district, street, housenumber = process_address(p_cursor, schema, table, id['ID'])
                    
                        company_id = load_scrape_company(p_cursor, schema, target_tables["company"], company_name, company_address, country, country_code, state, county, city, postcode, district, street, housenumber)

                        existing_companies.add((company_name.strip().lower(), company_address.strip().lower()))

                        company_ids.append({"ID": company_id, "COMPANY_NAME": company_name, "COMPANY_FULL_ADDRESS": company_address})

                min_salary_by_hour, max_salary_by_hour, currency = process_salary(p_cursor, schema, table, id['ID'])
                    
                load_scrape_job(p_cursor, schema, target_tables["job"], schema, table, id['ID'], company_id, min_salary_by_hour, max_salary_by_hour, currency)

        except Exception as e:
            print(f"Error while loading profession data: {e}; {id}")
            continue

    update_value(p_cursor, schema, target_tables["job"], "status", "'D'", f"trunc(status_to) < trunc({g_date_sql}) and status = 'A'")

    """ delete_table(p_cursor, schema, target_tables["job"], "status = 'D'")
    delete_table(p_cursor, schema, target_tables["company"], "id not in (select distinct company_id from JOBCRAWLER.SCRAPE_JOB)")

    for table in source_table:
        truncate_table(cursor, schema, table) """
    
    close_database(p_cursor)