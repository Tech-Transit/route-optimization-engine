import csv
import mysql.connector

# Database Configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'foo',
    'password': 'foo',
    'database': 'routes_db'
}

# Function to establish a database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Function to create the database
def create_database():
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS routes_db")
    conn.close()

# Function to create the table
def create_table():
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS routes")
    cursor.execute("""
        CREATE TABLE routes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            facility_name VARCHAR(255),
            code VARCHAR(255),
            country VARCHAR(255),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            type VARCHAR(255),
            transit_time_hours INT,
            distance_km DECIMAL(10, 2),
            border_crossings VARCHAR(255),  -- FIXED: Changed from INT to VARCHAR(255)
            currency VARCHAR(255)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Function to import CSV data into the database
def import_csv_to_db(csv_file):
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    with open(csv_file, newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            query = """
                INSERT INTO routes (facility_name, code, country, latitude, longitude, type, 
                                   transit_time_hours, distance_km, border_crossings, currency) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                row['Facility Name'], row['Code'], row['Country'], row['Latitude'], row['Longitude'], row['Type'], 
                row['Transit Time (hrs)'], row['Distance (km)'], row['Border Crossings'], row['Currency']
            ))

    conn.commit()
    print("✅ Data imported successfully")
    cursor.close()
    conn.close()

# Main execution
if __name__ == "__main__":
    create_database()  # Ensure database exists
    create_table()     # Create table with correct schema
    import_csv_to_db('logistics_facilities_updated.csv')  # Import CSV data
