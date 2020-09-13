import psycopg2

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
