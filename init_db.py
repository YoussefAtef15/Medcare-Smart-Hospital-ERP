import sqlite3
import os

# ==========================================
# CONFIGURATION & PATHS
# ==========================================
# Get the absolute path of the current directory to avoid routing issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the paths for the database file and the SQL setup script
DB_PATH = os.path.join(BASE_DIR, 'Smart Hospital System.db')
SQL_SCRIPT_PATH = os.path.join(BASE_DIR, 'database_setup.sql')


def initialize_database():
    """
    Reads the SQL setup file and executes it to build and populate the SQLite database.
    This is primarily used for server deployment (e.g., Render.com) to initialize
    the ephemeral file system automatically.
    """
    print("[INFO] Starting database initialization process...")

    # Step 1: Check if the SQL schema file exists
    if not os.path.exists(SQL_SCRIPT_PATH):
        print(f"[ERROR] SQL setup file not found at: {SQL_SCRIPT_PATH}")
        return

    try:
        # Step 2: Read the SQL script securely
        print(f"[INFO] Reading SQL script from: {SQL_SCRIPT_PATH}")
        with open(SQL_SCRIPT_PATH, 'r', encoding='utf-8') as sql_file:
            sql_script = sql_file.read()

        # Step 3: Connect to the SQLite database (Creates the .db file if it doesn't exist)
        print(f"[INFO] Connecting to database at: {DB_PATH}")
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        # Step 4: Execute the entire SQL script (Creates tables and inserts dummy data)
        print("[INFO] Executing SQL script... This might take a moment.")
        cursor.executescript(sql_script)

        # Step 5: Save (Commit) changes and close the connection
        connection.commit()
        connection.close()

        print("[SUCCESS] ✅ Database has been successfully created and populated!")

    except sqlite3.Error as db_error:
        print(f"[ERROR] A database error occurred: {db_error}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")


if __name__ == '__main__':
    # Execute the initialization function when the script is run directly
    initialize_database()