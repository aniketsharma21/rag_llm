
import sqlite3
import os

db_path = os.path.join(r"c:\Users\anike\PycharmProjects\rag_llm", "conversations.db")

if not os.path.exists(db_path):
    print(f"Database file not found at: {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get a list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database.")
        else:
            # For each table, print schema and data
            for table_name_tuple in tables:
                table_name = table_name_tuple[0]
                print(f"--- Table: {table_name} ---")

                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name});")
                schema = cursor.fetchall()
                print("Schema:")
                for column in schema:
                    print(f"  {column[1]}: {column[2]}")

                # Get first 10 rows of data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
                rows = cursor.fetchall()

                print("\nData (first 10 rows):")
                if not rows:
                    print("  No data in this table.")
                else:
                    for row in rows:
                        print(f"  {row}")
                print("\n")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
