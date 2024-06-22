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

def expand_table(cursor, schema, table, id, url, position, company_name, company_address, salary_details):

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

def insert_values(cursor, schema, table, source, id, url, position, company_name, company_address, salary_details):

    # Get object with 'signature', 'parameters' returns a dictionary like this: parameter name: parameter object; 'values' return all values from dictionary, exclude first three element
    parameters = list(inspect.signature(expand_table).parameters.values())[4:]

    # Create merge into to insert or modify row in table
    sql = f"merge into {schema}.{table} s using (select sysdate as tnd, '{source}' as source, 'A' as status, sysdate as status_from, sysdate as status_to"
    
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
    sql = sql + ") values (sysdate, 'profession', 'A', sysdate, sysdate"
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