#!/usr/bin/env python3
"""
Docker version of the token checker script
"""
import mysql.connector
import jwt
import os
from datetime import datetime

# Configuration from environment variables
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASS', 'rootpassword')
MYSQL_DB = os.getenv('MYSQL_DB', 'arkane_settings')
TABLE_NAME = 'arkane_settings'
JWT_SECRET = os.getenv('JWT_SECRET', 'docker_jwt_secret_key_2025')
JWT_ALGO = 'HS256'
TYPE = 'Arkane'

def check_token():
    """Check and display current token information"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST, 
            user=MYSQL_USER, 
            password=MYSQL_PASS, 
            database=MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Get the current token
        cursor.execute(f"SELECT AccessToken, updated_at FROM {TABLE_NAME} WHERE Type = %s", (TYPE,))
        result = cursor.fetchone()
        
        if result:
            token, updated_at = result
            print(f"Token found in database:")
            print(f"Last updated: {updated_at}")
            print(f"Token: {token}")
            print("")
            
            if token:
                try:
                    # Decode the token
                    decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO], options={"verify_aud": False})
                    exp_time = datetime.fromtimestamp(decoded['exp'])
                    iat_time = datetime.fromtimestamp(decoded['iat'])
                    
                    print("Token Details:")
                    print(f"  Subject: {decoded.get('sub', 'N/A')}")
                    print(f"  Issuer: {decoded.get('iss', 'N/A')}")
                    print(f"  Audience: {decoded.get('aud', 'N/A')}")
                    print(f"  Environment: {decoded.get('env', 'N/A')}")
                    print(f"  Issued at: {iat_time}")
                    print(f"  Expires at: {exp_time}")
                    print(f"  Token ID: {decoded.get('jti', 'N/A')}")
                    
                    now = datetime.now()
                    if exp_time > now:
                        time_left = exp_time - now
                        print(f"  Status: ✓ Valid (expires in {time_left})")
                    else:
                        print(f"  Status: ✗ Expired")
                        
                except jwt.ExpiredSignatureError:
                    print("⚠ Token has expired!")
                except jwt.InvalidTokenError as e:
                    print(f"⚠ Invalid token: {e}")
            else:
                print("No token stored in database yet")
        else:
            print(f"No record found for Type '{TYPE}'")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== JWT Token Checker (Docker) ===")
    check_token()
