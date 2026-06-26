import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "blood_donation")

    print(f"Connecting to database '{db_name}' on '{db_host}:{db_port}' as '{db_user}'...")
    try:
        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            auth_plugin="mysql_native_password"
        )
        cursor = conn.cursor()
        print("Connection successful!")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        print("\nPlease ensure your .env file is configured correctly for your remote database.")
        return

    sql_file_path = os.path.join(os.path.dirname(__file__), "blood_donation.sql")
    if not os.path.exists(sql_file_path):
        print(f"Error: Schema file '{sql_file_path}' not found.")
        return

    print(f"Reading schema from '{sql_file_path}'...")
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split SQL content into separate statements
    # Simple parser: splits by semicolon, handling comments
    statements = []
    current_statement = []
    
    for line in sql_content.splitlines():
        # Remove comments and whitespace
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("--") or clean_line.startswith("#"):
            continue
        
        current_statement.append(line)
        if clean_line.endswith(";"):
            statements.append("\n".join(current_statement))
            current_statement = []

    print(f"Executing database statements...")
    success_count = 0
    for stmt in statements:
        stmt_upper = stmt.strip().upper()
        # Skip database creation/switching since cloud providers pre-allocate the database
        if stmt_upper.startswith("CREATE DATABASE") or stmt_upper.startswith("USE "):
            print(f"Skipping command (cloud databases use pre-allocated databases): {stmt.strip()}")
            continue
        
        try:
            cursor.execute(stmt)
            success_count += 1
        except Exception as e:
            print(f"\nError executing statement:\n{stmt}")
            print(f"Error details: {e}")
            conn.rollback()
            return

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\nMigration completed successfully! Executed {success_count} SQL statements.")

if __name__ == "__main__":
    migrate()
