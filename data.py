import oracledb
from functions import manage_request

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

