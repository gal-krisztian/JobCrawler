import oracledb
import inspect
from config import username, password, dsn
from functions import g_date_sql



# Connect to database with user
def open_database():
    connection = oracledb.connect(
        user = username,
        password = password,
        dsn = dsn
    ).cursor()

    return connection

# Close connection
def close_database(connection):
    connection.close()

def is_exists_table(cursor, schema, table):
    is_exists = None

    cursor.execute(f"select {schema}.is_exists_table('{schema}', '{table}') from dual")
    is_exists = list(cursor.fetchone())

    return is_exists[0]

def is_exists_column(cursor, schema, table, column):
    is_exists = None

    cursor.execute(f"select {schema}.is_exists_column('{schema}', '{table}', '{column}') from dual")
    is_exists = list(cursor.fetchone())

    return is_exists[0]

def create_table(cursor, schema, table, columns):

    sql = f"create table {schema}.{table} ("

    # Add static columns to the beginning of the table
    for column, datatype in columns.items():
        sql = sql + f"{column} {datatype}, "

    # Cut the last two character that I previously add ', ' and finish the query with ')'
    sql = sql[:-2] + ")"

    cursor.execute(sql)

def alter_table(cursor, schema, table, sql):
    cursor.execute(f"alter table {schema}.{table} {sql}")

def expand_table(cursor, schema, table, id, url, position, company_name, company_address, salary_details, emp_type, category1, category2):

    # Get object with 'signature', 'parameters' returns a dictionary like this: parameter name: parameter object; 'values' return all values from dictionary, exclude first three element
    parameters = list(inspect.signature(expand_table).parameters.values())[3:]
    
    for parameter in parameters:
        # Check the datatype of each input parameter
        if isinstance(locals().get(parameter.name), list):
            # if the parameter is a list then loop trough from 0 to length of list
            for list_index in range(0, len(locals().get(parameter.name))):
                # Check if column is already created
                if is_exists_column(cursor, schema, table, f"{parameter.name}_v{str(list_index+1)}") == 0:
                    # Add columns to table as varchar2(32767) for now
                    alter_table(cursor, schema, table, f"add {parameter.name}_v{str(list_index + 1)} varchar2(32767)")
        else:
            if is_exists_column(cursor, schema, table, parameter.name) == 0:
                alter_table(cursor, schema, table, f"add {parameter.name} varchar2(32767)")

def insert_values(cursor, schema, table, source, id, url, position, company_name, company_address, salary_details, emp_type, category1, category2):

    # Get object with 'signature', 'parameters' returns a dictionary like this: parameter name: parameter object; 'values' return all values from dictionary, exclude first three element
    parameters = list(inspect.signature(insert_values).parameters.values())[4:]

    # Create merge into to insert or modify row in table
    sql = f"merge into {schema}.{table} s using (select sysdate as tnd, '{source}' as source, 'A' as status, {g_date_sql} as status_from, {g_date_sql} as status_to"
    
    for parameter in parameters:
        # Check the datatype of each input parameter
        if isinstance(locals().get(parameter.name), list):
            # if the parameter is a list then loop trough from 0 to length of list
            for list_index in range(0,len(locals().get(parameter.name))):
                # Concatenate <value> as <column_name> into query in case of list
                sql = sql + f", q'[{locals().get(parameter.name)[list_index]}]' as {parameter.name}_v{str(list_index+1)}"
        else:
                # Concatenate <value> as <column_name> into query in case of single value
                sql = sql + f", q'[{locals().get(parameter.name)}]' as {parameter.name}"
    # Close and set condition
    sql = sql + " from dual) d on (s.url = d.url)"
    # Update/Delete clause
    # Insert clause
    sql = sql + " when not matched then insert (s.tnd, s.source, s.status, status_from, status_to"
    for parameter in parameters:
        # Check the datatype of each input parameter
        if isinstance(locals().get(parameter.name), list):
            # if the parameter is a list then loop trough from 0 to length of list
            for list_index in range(0,len(locals().get(parameter.name))):
                # List all dynamicly defined columns
                sql = sql + f", s.{parameter.name}_v{str(list_index+1)}"
        else:
            # List all dynamicly defined columns in case of single value
            sql = sql + f", s.{parameter.name}"
    # Repeat logic for values
    sql = sql + f") values (sysdate, '{source}', 'A', {g_date_sql}, {g_date_sql}"
    for parameter in parameters:
        if isinstance(locals().get(parameter.name), list):
            for list_index in range(0,len(locals().get(parameter.name))):
                sql = sql + f", q'[{locals().get(parameter.name, [])[list_index]}]'"
        else:
            sql = sql + f", q'[{str(locals().get(parameter.name))}]'"
    sql = sql + ")"
    # Error logging clause

    # Execute and handle errors
    try:
        cursor.execute(sql)
        cursor.execute("commit")
    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)

def get_values(p_cursor, p_schema, p_table, p_value, p_condition = "1 = 1"):
    
    try:
        sql = f"select {p_value} from {p_schema}.{p_table} where {p_condition}"

        p_cursor.execute(sql)

        # Get column names to match with values
        columns = [column[0] for column in p_cursor.description]

    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)

    finally:
        # Match values with column names and return as list of dictionaries
        return [dict(zip(columns, row)) for row in p_cursor.fetchall()]
    
def load_scrape_job(p_cursor, p_target_schema, p_target_table, p_source_schema, p_source_table, p_id, p_company_id, p_min_salary_by_hour, p_max_salary_by_hour, p_currency):
    
    sql = f"""
        insert into {p_target_schema}.{p_target_table} (
        tnd, source, status, status_from, status_to, id, url,
        position, company_id, employment_type, category1, category2,
        min_salary_by_hour, max_salary_by_hour, currency
        ) select 
        sysdate, source, status, status_from, status_to, id, url, 
        position, :company_id, emp_type, category1, category2, 
        :min_salary_by_hour, :max_salary_by_hour, :currency 
        from {p_source_schema}.{p_source_table} where id = {p_id}"""

    params = {
        "company_id": p_company_id,
        "min_salary_by_hour": p_min_salary_by_hour,
        "max_salary_by_hour": p_max_salary_by_hour,
        "currency": p_currency
    }

    try:
        p_cursor.execute(sql, params)
        p_cursor.execute("commit")
    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)
        print("p_id: ", p_id)

def load_scrape_company(p_cursor, p_schema, p_table, p_company_name, p_company_address, p_country, p_country_code, p_state, p_county, p_city, p_postcode, p_district, p_street, p_housenumber):
    company_id = p_cursor.var(oracledb.STRING, size=11)

    sql = f"""
        INSERT INTO {p_schema}.{p_table} (
            tnd, company_name, company_full_address,
            country, country_code, state, county, city,
            postcode, district, street, housenumber
        )
        VALUES (
            sysdate, :company_name, :company_address,
            :country, :country_code, :state, :county, :city,
            :postcode, :district, :street, :housenumber
        )
        RETURNING id INTO :company_id
    """

    params = {
        "company_name": p_company_name,
        "company_address": p_company_address,
        "country": p_country,
        "country_code": p_country_code,
        "state": p_state,
        "county": p_county,
        "city": p_city,
        "postcode": p_postcode,
        "district": p_district,
        "street": p_street,
        "housenumber": p_housenumber,
        "company_id": company_id
    }


    try:
        p_cursor.execute(sql, params)
        p_cursor.execute("commit")

        company_id = company_id.getvalue()[0]
        return company_id

    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)
        print("p_company_name: ", p_company_name, " p_company_address: ", p_company_address)

def update_value(p_cursor, p_schema, p_table, p_column, p_value, p_condition = "1 = 1"):
    pass

    sql = f"update {p_schema}.{p_table} set {p_column} = {p_value} where {p_condition}"

    try:
        p_cursor.execute(sql)
        p_cursor.execute("commit")
    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)

def delete_table(p_cursor, p_schema, p_table, p_condition = "1 = 1"):
    sql = f"delete from {p_schema}.{p_table} where {p_condition}"

    try:
        p_cursor.execute(sql)
        p_cursor.execute("commit")
    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)

def truncate_table(p_cursor, p_schema, p_table):
    sql = f"truncate table {p_schema}.{p_table}"

    try:
        p_cursor.execute(sql)
    except oracledb.DatabaseError as e:
        error, = e.args
        print("Error code: ", error.code, " Error message: ", error.message)