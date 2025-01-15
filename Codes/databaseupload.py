import sqlite3
from sqlite3 import Error

# Define database file name
db_file = 'user_database.db'

try:
    # Connect to the database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create a table for user data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        age INTEGER,
        gender TEXT
    )
    ''')

    # Insert user data
    cursor.execute('''
    INSERT INTO users (username, email, password, age, gender)
    VALUES (?, ?, ?, ?, ?)
    ''', ("arvind", "arvind23138@iiitd.ac.in", "arvindhhh", 18, "male"))

    # Commit changes and close the connection
    conn.commit()
    print("User data inserted successfully!")
except Error as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
