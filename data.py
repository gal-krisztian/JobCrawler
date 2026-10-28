import oracledb
import re
from functions import manage_request, wait, parse_number
from database import get_values

def process_address(p_cursor, p_schema, p_table, p_id):
    company_name = None
    company_address = None
    country = None
    country_code = None
    state = None
    county = None
    city = None
    postcode = None
    district = None
    street = None
    housenumber = None

    try:
        sql = f"select company_name, company_address from {p_schema}.{p_table} where id = '{p_id}'"

        p_cursor.execute(sql)

        company_name, company_address = p_cursor.fetchone()

    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)

    page = manage_request("https://nominatim.openstreetmap.org/search", 
                        params={"q": company_address, "addressdetails": 1, "format": "geocodejson", "limit": 1}, 
                        headers={"User-Agent": "my-mail-address-TODO"})
    
    wait(1, 2)
    
    data = page.json()

    if data and data.get("features"):
        country = data["features"][0]["properties"]["geocoding"].get("country")
        country_code = data["features"][0]["properties"]["geocoding"].get("country_code")
        state = data["features"][0]["properties"]["geocoding"].get("state")
        county = data["features"][0]["properties"]["geocoding"].get("county")
        city = data["features"][0]["properties"]["geocoding"].get("city")
        postcode = data["features"][0]["properties"]["geocoding"].get("postcode")
        district = data["features"][0]["properties"]["geocoding"].get("district")
        street = data["features"][0]["properties"]["geocoding"].get("street")
        housenumber = data["features"][0]["properties"]["geocoding"].get("housenumber")

    return company_name, company_address, country, country_code, state, county, city, postcode, district, street, housenumber

def process_salary(p_cursor, p_schema, p_table, p_id):

    max_salary_by_hour = 0
    min_salary_by_hour = 0
    currency = None
    suffix = {"e": 1000, "M": 1000000}
    gross_value = {"Br.": 1, "Nettó": 0.64}

    salary_columns = get_values(p_cursor, "sys", "all_tab_columns", "column_name", f"table_name = '{p_table.upper()}' and column_name like '%SALARY_DETAILS%'")

    salary_column = salary_columns[0]["COLUMN_NAME"]

    salary = get_values(p_cursor, p_schema, p_table, f"{salary_column}", f"id = '{p_id}'")[0]

    if salary.get(salary_column) is None:
        return 0, 0, None
    
    min_salary = None
    max_salary = None

    # Make difference between interval and single value salary

    try:    
        if "-" in salary.get(salary_column):
            interval = True
            net_gross, min_salary, multiplier_min, max_salary, multiplier_max, currency, recurrence = re.search(r"^([^\s]+)\s+([\d\s,]+?)\s*([eM])?\s*-\s*([\d\s,]+?)\s*([eM])?\s+([a-zA-ZÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)(?:\/|\s+)([^\s]+)", salary.get(salary_column)).group(1, 2, 3, 4, 5, 6, 7)
        else:
            interval = False
            net_gross, min_salary, multiplier_min, currency, recurrence = re.search(r"^([^\s]+)\s+([\d\s,]+?)\s*([eM])?\s+([a-zA-ZÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)(?:\/|\s+)([^\s]+)", salary.get(salary_column)).group(1, 2, 3, 4, 5)
    except Exception as e:
        print(f"Error parsing salary details for ID: {p_id}. Error: {e}")
        return 0, 0, None
    
    if min_salary is None:
        return 0, 0, None
    elif min_salary is not None and max_salary is None:
        max_salary = 0
        min_salary = parse_number(min_salary)
    elif min_salary is not None and max_salary is not None:
        min_salary = parse_number(min_salary)
        max_salary = parse_number(max_salary)

    if recurrence == "óra":
        min_salary_by_hour = min_salary * suffix.get(multiplier_min, 1) / gross_value.get(net_gross, 1)
        max_salary_by_hour = max_salary * suffix.get(multiplier_max, 1) / gross_value.get(net_gross, 1) if interval == True else None
    elif recurrence == "havi":
        # Salary multiplied by 12 months and divided by 252 (average) working days in a year
        min_salary_by_hour = min_salary * suffix.get(multiplier_min, 1) / gross_value.get(net_gross, 1) * 12 / 252 / 8
        max_salary_by_hour = max_salary * suffix.get(multiplier_max, 1) / gross_value.get(net_gross, 1) * 12 / 252 / 8 if interval == True else None
        
        currency = currency

    return min_salary_by_hour, max_salary_by_hour, currency
