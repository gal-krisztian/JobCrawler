import oracledb
import config
import inspect

# Connect to database with user
def open_database():
    connection = oracledb.connect(
        user = config.username,
        password = config.password,
        dsn = config.dsn
    ).cursor()

    return connection

# Close connection
def close_database(p_connection):
    p_connection.close()

def is_exists_table(p_cursor, p_schema, p_table):
    is_exists = None

    p_cursor.execute(f"select {p_schema}.is_exists_table('{p_schema}', '{p_table}') from dual")
    is_exists = list(p_cursor.fetchone())

    return is_exists[0]

def is_exists_column(p_cursor, p_schema, p_table, p_column):
    is_exists = None

    p_cursor.execute(f"select {p_schema}.is_exists_column('{p_schema}', '{p_table}', '{p_column}') from dual")
    is_exists = list(p_cursor.fetchone())

    return is_exists[0]

def create_table(p_cursor, p_schema, p_table, p_columns):

    sql = f"create table {p_schema}.{p_table} ("

    # Add static columns to the beginning of the table
    for column, datatype in p_columns.items():
        sql = sql + f"{column} {datatype}, "

    # Cut the last two character that I previously add ', ' and finish the query with ')'
    sql = sql[:-2] + ")"

    p_cursor.execute(sql)

def alter_table(p_cursor, p_schema, p_table, p_sql):
    p_cursor.execute(f"alter table {p_schema}.{p_table} {p_sql}")

def expand_table(p_cursor, p_schema, p_table, p_id, p_url, p_position, p_company_name, p_company_address, salary_details):

    # Get object with 'signature', 'parameters' returns a dictionary like this: parameter name: parameter object; 'values' return all values from dictionary, exclude first three element
    parameters = list(inspect.signature(expand_table).parameters.values())[3:]
    
    for parameter in parameters:
        # Check the datatype of each input parameter
        if isinstance(locals().get(parameter.name), list):
            # if the parameter is list then loop trough from 0 to length of list
            for list_index in range(0, len(locals().get(parameter.name))):
                # Check if column is already created
                if is_exists_column(p_cursor, p_schema, p_table, f"{parameter.name}_v{str(list_index+1)}") == 0:
                    # Add columns to table as varchar2(32767) for now
                    alter_table(p_cursor, p_schema, p_table, f"add {parameter.name}_v{str(list_index + 1)} varchar2(32767)")
        else:
            if is_exists_column(p_cursor, p_schema, p_table, parameter.name) == 0:
                alter_table(p_cursor, p_schema, p_table, f"add {parameter.name} varchar2(32767)")