import mysql.connector
import jwt
import time
import schedule
import os
import logging
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone

# Environment config
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASS', 'rootpassword')
MYSQL_DB = os.getenv('MYSQL_DB', 'arkane_settings')
JWT_SECRET = os.getenv('JWT_SECRET', 'docker_jwt_secret_key_2025')
JWT_ALGO = 'HS256'
TABLE_NAME = 'arkane_settings'
TYPE = 'Arkane'
CA_CERT_PATH = os.path.join(os.path.dirname(__file__), 'ca-certificate.crt')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/jwt_automation.log') if os.path.exists('/app/logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

def wait_for_mysql(max_retries=30, delay=2):
    """Wait for MySQL to be available"""
    for attempt in range(max_retries):
        try:
            ssl_config = {
                'ssl_disabled': False,
                'ssl_ca': CA_CERT_PATH
            } if MYSQL_HOST not in ['localhost', 'mysql'] else {}
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                connection_timeout=10,
                **ssl_config
            )
            conn.close()
            logger.info("✓ MySQL connection successful")
            return True
        except mysql.connector.Error as err:
            logger.warning(f"MySQL connection attempt {attempt + 1}/{max_retries} failed: {err}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error("Failed to connect to MySQL after all retries")
                return False
    return False

def init_db():
    """Ensure the arkane_settings database and table exist."""
    try:
        ssl_config = {
            'ssl_disabled': False,
            'ssl_ca': CA_CERT_PATH
        } if MYSQL_HOST not in ['localhost', 'mysql'] else {}
        conn = mysql.connector.connect(
            host=MYSQL_HOST, 
            port=MYSQL_PORT,
            user=MYSQL_USER, 
            password=MYSQL_PASS,
            **ssl_config
        )
        cursor = conn.cursor()
        # Create database if needed
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}`;")
        logger.info(f"Database '{MYSQL_DB}' created or already exists")
        conn.database = MYSQL_DB
        # Create the arkane_settings table if needed
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                AccessToken TEXT,
                Type VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
        """)
        logger.info(f"Table '{TABLE_NAME}' created or already exists")
        # Ensure a row with Type='Arkane' exists
        cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_NAME}` WHERE Type = %s", (TYPE,))
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute(f"INSERT INTO `{TABLE_NAME}` (AccessToken, Type) VALUES ('', %s);", (TYPE,))
            logger.info(f"Initial record for Type '{TYPE}' created")
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database initialization completed successfully")
    except mysql.connector.Error as err:
        logger.error(f"Database initialization error: {err}")
        raise

def generate_jwt():
    """Generate a new JWT token with 5-minute expiration"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "arkane_user",
        "iss": "arkane_system_docker",
        "aud": "arkane_services",
        "exp": now + timedelta(minutes=5),
        "iat": now,
        "jti": str(int(time.time())),  # Unique token ID
        "env": "docker"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def update_token():
    """Generate new JWT token and update it in the database"""
    try:
        token = generate_jwt()
        ssl_config = {
            'ssl_disabled': False,
            'ssl_ca': CA_CERT_PATH
        } if MYSQL_HOST not in ['localhost', 'mysql'] else {}
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB,
            **ssl_config
        )
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE `{TABLE_NAME}` SET AccessToken=%s, updated_at=CURRENT_TIMESTAMP WHERE Type=%s",
            (token, TYPE)
        )
        if cursor.rowcount > 0:
            logger.info(f"✓ Token updated successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger.warning(f"⚠ No rows updated - Type '{TYPE}' not found")
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        logger.error(f"Database error during token update: {err}")
    except Exception as e:
        logger.error(f"Error updating token: {e}")

def get_current_token():
    """Retrieve and display the current token from database"""
    try:
        ssl_config = {
            'ssl_disabled': False,
            'ssl_ca': CA_CERT_PATH
        } if MYSQL_HOST not in ['localhost', 'mysql'] else {}
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB,
            **ssl_config
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT AccessToken FROM `{TABLE_NAME}` WHERE Type = %s", (TYPE,))
        result = cursor.fetchone()
        if result:
            token = result[0]
            logger.info(f"Current token: {token[:50]}..." if len(token) > 50 else f"Current token: {token}")
            # Decode and show token info
            try:
                decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO], options={"verify_aud": False})
                exp_time = datetime.fromtimestamp(decoded['exp'])
                logger.info(f"Token expires at: {exp_time}")
                logger.info(f"Time until expiration: {exp_time - datetime.now(timezone.utc)}")
            except jwt.ExpiredSignatureError:
                logger.warning("⚠ Token has expired!")
            except Exception as e:
                logger.error(f"Could not decode token: {e}")
        else:
            logger.warning("No token found in database")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")

# ...rest of your code is unchanged...

# Only update: schedule calls and DB/table logic as above

if __name__ == "__main__":
    # ... main() function and others unchanged ...
    # Use schedule.every(5).minutes.do(update_token)
    # On first run: init_db(), update_token(), get_current_token(), etc.
    pass  # (the rest of your script continues as before)
