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
MYSQL_PASS = os.getenv('MYSQL_PASS', 'root')
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
    payload = {
        "sub": "arkane_user",
        "iss": "arkane_system",
        "aud": "arkane_services",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "iat": datetime.now(timezone.utc),
        "jti": str(int(time.time()))  # Unique token ID
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token

def update_token():
    """Generate new demo token and update it in the database"""
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
            logger.info(f"Current token: {token}")
            logger.info(f"Token updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger.warning("No token found in database")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.health_check()
        elif self.path == '/status':
            self.status_check()
        else:
            self.send_error(404)

    def health_check(self):
        """Basic health check endpoint"""
        try:
            # Use SSL for managed databases
            ssl_config = {
                'ssl_disabled': False,
                'ssl_ca': CA_CERT_PATH
            } if MYSQL_HOST != 'localhost' and MYSQL_HOST != 'mysql' else {}
            
            # Test database connection
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                connection_timeout=10,
                **ssl_config
            )
            conn.close()
            
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "demo-token-mysql-automation",
                "database": "connected"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            response = {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "service": "jwt-mysql-automation",
                "error": str(e)
            }
            
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

    def status_check(self):
        """Detailed status endpoint"""
        try:
            # Use SSL for managed databases
            ssl_config = {
                'ssl_disabled': False,
                'ssl_ca': CA_CERT_PATH
            } if MYSQL_HOST != 'localhost' and MYSQL_HOST != 'mysql' else {}
            
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                connection_timeout=10,
                **ssl_config
            )
            cursor = conn.cursor()
            
            # Check if token exists
            cursor.execute("SELECT AccessToken, updated_at FROM arkane_settings WHERE Type = 'Arkane'")
            result = cursor.fetchone()
            
            response = {
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "service": "jwt-mysql-automation",
                "database": "connected",
                "token_exists": result is not None,
                "last_update": result[1].isoformat() if result and result[1] else None
            }
            
            cursor.close()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            response = {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "service": "jwt-mysql-automation",
                "error": str(e)
            }
            
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_health_server():
    """Start health check server in background thread"""
    try:
        server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
        logger.info("Health check server started on port 8080")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")

def init_demo_db():
    """Initialize demo database and users table with sample data if not present."""
    try:
        ssl_config = {
            'ssl_disabled': False,
            'ssl_ca': CA_CERT_PATH
        } if MYSQL_HOST != 'localhost' and MYSQL_HOST != 'mysql' else {}
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            **ssl_config
        )
        cursor = conn.cursor()
        # Create demo database
        cursor.execute("CREATE DATABASE IF NOT EXISTS demo;")
        conn.database = 'demo'
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Insert sample data
        sample_users = [
            'john_doe', 'jane_smith', 'bob_wilson', 'alice_johnson',
            'charlie_brown', 'sarah_connor', 'mike_tyson', 'emma_watson'
        ]
        for user in sample_users:
            cursor.execute("INSERT IGNORE INTO users (username) VALUES (%s)", (user,))
        conn.commit()
        logger.info("Demo database and users table initialized with sample data.")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        logger.error(f"Demo DB initialization error: {err}")

def main():
    """Main function to run the demo token automation service"""
    logger.info("=== Demo Token MySQL Automation Service (Docker) ===")
    logger.info(f"Starting at {datetime.now()}")
    logger.info(f"MySQL Host: {MYSQL_HOST}")
    logger.info(f"MySQL Port: {MYSQL_PORT}")
    logger.info(f"MySQL User: {MYSQL_USER}")
    logger.info(f"Database: {MYSQL_DB}")
    logger.info(f"Table: {TABLE_NAME}")
    logger.info(f"Update interval: 5 minutes")
    logger.info(f"SSL enabled for remote connections: {MYSQL_HOST not in ['localhost', 'mysql']}")
    logger.info("=" * 50)
    
    try:
        # Wait for MySQL to be available
        logger.info("Waiting for MySQL to be available...")
        if not wait_for_mysql():
            logger.error("Failed to connect to MySQL. Exiting.")
            logger.error("Please check your database credentials and network connectivity.")
            return
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        init_demo_db()
        
        # Schedule token updates every 5 minutes
        schedule.every(5).minutes.do(update_token)
        
        # Generate initial token
        logger.info("Generating initial demo token...")
        update_token()
        get_current_token()
        
        # Start health check server
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        logger.info("Service is running. Press Ctrl+C to stop.")
        logger.info("Demo token will be updated every 5 minutes...")
        logger.info("Health check available at http://localhost:8080/health")
        logger.info("Status check available at http://localhost:8080/status")
        
        # Main loop
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        logger.error("Check database connection and credentials")

if __name__ == "__main__":
    main()
