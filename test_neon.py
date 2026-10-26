import os
import psycopg

database_url = os.environ.get("DATABASE_URL")

if not database_url:
    print("ERROR: DATABASE_URL is not set.")
else:
    try:
        connection = psycopg.connect(database_url)
        cursor = connection.cursor()

        cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)

        print("Neon connection successful!")
        print("Existing tables:", cursor.fetchall())

        cursor.close()
        connection.close()

    except Exception as error:
        print("Database error:", error)

