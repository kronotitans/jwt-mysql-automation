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

# Configuration from environment variables with defaults
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASS', 'rootpassword')
MYSQL_DB = os.getenv('MYSQL_DB', 'arkane_settings')
TABLE_NAME = 'arkane_settings'
JWT_SECRET = os.getenv('JWT_SECRET', 'docker_jwt_secret_key_2025')
JWT_ALGO = 'HS256'
TYPE = 'Arkane'
CA_CERT_PATH = os.path.join(os.path.dirname(__file__), 'ca-certificate.crt')

# Setup logging
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
    """Initialize database and table if they don't exist"""
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
            **ssl_config)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB};")
        logger.info(f"Database '{MYSQL_DB}' created or already exists")
        
        # Switch to the database
        conn.database = MYSQL_DB
        
        # Create table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INT PRIMARY KEY AUTO_INCREMENT,
                AccessToken TEXT,
                Type VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
        """)
        logger.info(f"Table '{TABLE_NAME}' created or already exists")
        
        # Insert initial record if it doesn't exist
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE Type = %s", (TYPE,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute
            cursor.execute(f"INSERT INTO {TABLE_NAME} (AccessToken, Type) VALUES ('', %s);", (TYPE,))
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
        "iss": "arkane_system_docker",
        "aud": "arkane_services",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "iat": datetime.now(timezone.utc),
        "jti": str(int(time.time())),  # Unique token ID
        "env": "docker"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token

def update_token():
    """Generate new JWT token and update it in the database"""
    try:
        token = generate_jwt()
        
        # Use SSL for managed databases
        ssl_config = {
            'ssl_disabled': False,
            'ssl_verify_cert': True,
            'ssl_verify_identity': False
        } if MYSQL_HOST != 'localhost' and MYSQL_HOST != 'mysql' else {}
        
        conn = mysql.connector.connect(
            host=MYSQL_HOST, 
            port=MYSQL_PORT,
            user=MYSQL_USER, 
            password=MYSQL_PASS, 
            database=MYSQL_DB,
            **ssl_config
        )
        cursor = conn.cursor()
        
        # Update the token
        cursor.execute(
            f"UPDATE {TABLE_NAME} SET AccessToken=%s WHERE Type=%s", 
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
        # Use SSL for managed databases
        ssl_config = {
            'ssl_disabled': False,
            'ssl_verify_cert': True,
            'ssl_verify_identity': False
        } if MYSQL_HOST != 'localhost' and MYSQL_HOST != 'mysql' else {}
        
        conn = mysql.connector.connect(
            host=MYSQL_HOST, 
            port=MYSQL_PORT,
            user=MYSQL_USER, 
            password=MYSQL_PASS, 
            database=MYSQL_DB,
            **ssl_config
        )
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT AccessToken FROM {TABLE_NAME} WHERE Type = %s", (TYPE,))
        result = cursor.fetchone()
        
        if result:
            token = result[0]
            logger.info(f"Current token: {token[:50]}..." if len(token) > 50 else f"Current token: {token}")
            
            # Decode and show token info
            try:
                decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO], options={"verify_aud": False})
                exp_time = datetime.fromtimestamp(decoded['exp'])
                logger.info(f"Token expires at: {exp_time}")
                logger.info(f"Time until expiration: {exp_time - datetime.now()}")
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
                'ssl_verify_cert': True,
                'ssl_verify_identity': False
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
                "service": "jwt-mysql-automation",
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
                'ssl_verify_cert': True,
                'ssl_verify_identity': False
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

def main():
    """Main function to run the JWT automation service"""
    logger.info("=== JWT MySQL Automation Service (Docker) ===")
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
        
        # Schedule token updates every 5 minutes
        schedule.every(5).minutes.do(update_token)
        
        # Generate initial token
        logger.info("Generating initial token...")
        update_token()
        get_current_token()
        
        # Start health check server
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        logger.info("Service is running. Press Ctrl+C to stop.")
        logger.info("Token will be updated every 5 minutes...")
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
