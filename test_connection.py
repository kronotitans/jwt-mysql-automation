#!/usr/bin/env python3
"""
Test script to check if the DigitalOcean MySQL connection works
"""
import os
import mysql.connector
from datetime import datetime

# Get environment variables
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASS', 'rootpassword')
MYSQL_DB = os.getenv('MYSQL_DB', 'arkane_settings')

print("=== Database Connection Test ===")
print(f"Host: {MYSQL_HOST}")
print(f"Port: {MYSQL_PORT}")
print(f"User: {MYSQL_USER}")
print(f"Database: {MYSQL_DB}")
print(f"Time: {datetime.now()}")
print("=" * 40)

try:
    # Use SSL for managed databases
    ssl_config = {
        'ssl_disabled': False,
        'ssl_verify_cert': True,
        'ssl_verify_identity': False
    } if MYSQL_HOST not in ['localhost', 'mysql'] else {}
    
    print(f"SSL Config: {ssl_config}")
    
    # Test connection
    print("Attempting to connect...")
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        connection_timeout=10,
        **ssl_config
    )
    
    print("✓ Connection successful!")
    
    # Test database access
    cursor = conn.cursor()
    
    # Show databases
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    print(f"Available databases: {[db[0] for db in databases]}")
    
    # Try to use the target database
    try:
        conn.database = MYSQL_DB
        print(f"✓ Successfully connected to database '{MYSQL_DB}'")
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Tables in {MYSQL_DB}: {[table[0] for table in tables]}")
        
    except mysql.connector.Error as db_err:
        print(f"⚠ Database '{MYSQL_DB}' issue: {db_err}")
        
        # Try to create the database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
        print(f"✓ Database '{MYSQL_DB}' created or already exists")
    
    cursor.close()
    conn.close()
    print("✓ Connection test completed successfully")
    
except mysql.connector.Error as err:
    print(f"✗ MySQL Error: {err}")
    print("Please check your database credentials and network connectivity.")
except Exception as e:
    print(f"✗ General Error: {e}")

print("\nTo run the full service, use:")
print("export MYSQL_HOST=your_host")
print("export MYSQL_PORT=25060")  
print("export MYSQL_USER=doadmin")
print("export MYSQL_PASS=your_password")
print("export MYSQL_DB=arkane_settings")
print("python3 jwt_mysql_automation_docker.py")
