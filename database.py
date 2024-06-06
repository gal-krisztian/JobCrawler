import oracledb
import config

def open_database():
    connection = oracledb.connect(
        user = config.username,
        password = config.password,
        dsn = config.dsn
    )

    return connection

def close_database(p_connection):
    p_connection.close()