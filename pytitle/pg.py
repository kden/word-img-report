import psycopg2
from psycopg2._psycopg import AsIs

OUTPUT_DATE = "%Y-%m-%d"


def run_update(con, statement):
    cursor = con.cursor()
    con.rollback()
    try:
        cursor.execute(statement)
        row_count = cursor.rowcount
        print(statement)
        print("Updated " + str(row_count) + " rows")
    except psycopg2.Error as error:
        print(error)
        print(error.pgcode)
        print(error.pgerror)
        con.rollback()
    con.commit()


def insert_row(con, table_name, id_name, row):
    row_insert = 'insert into ' + table_name + ' (%s) values %s on conflict do nothing returning ' + id_name
    row_columns = row.keys()
    row_values = [row[col] for col in row_columns]
    arguments = (AsIs(','.join(row_columns)), tuple(row_values))
    populated_sql = row_insert % arguments
    cursor = con.cursor()
    con.rollback()
    #print("Inserting row" + str(row))
    #print(populated_sql)
    result = None
    try:
        cursor.execute(row_insert, arguments)
        # row_count = cursor.rowcount
        id = cursor.fetchone()
        if id is not None:
            result = id[0]
        con.commit()
    except psycopg2.Error as error:
        print(populated_sql)
        print(error)
        print(error.pgcode)
        print(error.pgerror)
        con.rollback()

    return result

