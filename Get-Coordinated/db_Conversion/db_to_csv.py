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

# Function to export database data to CSV
def export_db_to_csv(csv_file):
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM routes")
    
    rows = cursor.fetchall()
    headers = ['Facility Name', 'Code', 'Country', 'Latitude', 'Longitude', 'Type', 
               'Transit Time (hrs)', 'Distance (km)', 'Border Crossings', 'Currency']
    
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(headers)
        for row in rows:
            csv_writer.writerow(row[1:])  # Skip the 'id' column
    
    print("✅ Data exported successfully")
    cursor.close()
    conn.close()

# Main execution
if __name__ == "__main__":
    export_db_to_csv('exported_routes.csv')  # Export database data to CSV