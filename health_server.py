#!/usr/bin/env python3
"""
Health check endpoint for the JWT MySQL Automation Service
This creates a simple HTTP server for health checks in production
"""

import os
import sys
import json
import mysql.connector
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import threading
import time

# Import configuration from main module
sys.path.append('/app')

MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASS', 'rootpassword')
MYSQL_DB = os.getenv('MYSQL_DB', 'arkane_settings')

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
            # Test database connection
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                connection_timeout=5
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
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                connection_timeout=5
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
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Start health server in background
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    print("Health check server started on port 8080")
    print("Endpoints:")
    print("  GET /health - Basic health check")
    print("  GET /status - Detailed status")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Health server stopped")
