import mysql.connector
import os

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rajas@1231',  # Add your MySQL password here
    'database': 'event_management'
}

def update_database():
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Connected to database successfully!")
        
        # Read the update schema file
        with open('update_schema.sql', 'r') as file:
            sql_commands = file.read()
        
        # Execute each command
        for command in sql_commands.split(';'):
            if command.strip():
                print(f"Executing: {command.strip()}")
                cursor.execute(command)
                conn.commit()
        
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating database: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_database() 