# JWT MySQL Automation Service

A containerized service that automatically generates and updates JWT tokens in a MySQL database every 5 minutes.

## Features

- 🔐 Automatic JWT token generation and rotation
- 🗄️ MySQL database integration
- 🐳 Fully containerized with Docker
- 🚀 Production-ready for DigitalOcean deployment
- 📊 Comprehensive logging and monitoring
- 🔄 Automatic database initialization
- 💪 Health checks and recovery mechanisms

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd jwt-mysql-automation
   cp .env.example .env
   # Edit .env with your values
   ```

2. **Run locally**:
   ```bash
   docker-compose up -d
   ```

3. **Check status**:
   ```bash
   docker-compose logs -f jwt_automation
   ```

## Deployment to DigitalOcean

### Option 1: Quick Deploy (Recommended)
```bash
./deploy.sh
```

### Option 2: Manual Steps
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MYSQL_HOST` | MySQL server hostname | `mysql` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASS` | MySQL password | `secure_root_password_2025` |
| `MYSQL_DB` | Database name | `arkane_settings` |
| `JWT_SECRET` | JWT signing secret | `secure_jwt_secret_key_2025` |

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  JWT Service    │───▶│  MySQL Database │
│  (Python)       │    │  (arkane_settings)│
└─────────────────┘    └─────────────────┘
         │
         ▼
    Updates every 5min
```

## Database Schema

```sql
CREATE TABLE arkane_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    AccessToken TEXT,
    Type VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## JWT Token Structure

```json
{
  "sub": "arkane_user",
  "iss": "arkane_system_docker", 
  "aud": "arkane_services",
  "exp": 1640995200,
  "iat": 1640995200,
  "jti": "unique_token_id",
  "env": "docker"
}
```

## Health Monitoring

The service includes built-in health checks:

- Database connectivity testing
- Token validation
- Automatic recovery mechanisms
- Detailed logging

## Production Considerations

- ✅ Non-root user execution
- ✅ Secrets management via environment variables
- ✅ Database connection pooling
- ✅ Graceful error handling
- ✅ Docker multi-stage builds
- ✅ Health checks

## Troubleshooting

### Common Issues

**Database Connection Failed**:
```bash
docker-compose logs mysql
# Check if MySQL is ready
```

**Token Not Updating**:
```bash
docker-compose exec jwt_automation python check_token.py
```

**Permission Issues**:
```bash
docker-compose exec jwt_automation ls -la /app/logs
```

## Development

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python jwt_mysql_automation_docker.py
```

### Testing
```bash
python check_token_docker.py
```

## Security

- JWT tokens expire after 5 minutes
- Database credentials via environment variables
- Non-root container execution
- Secure MySQL authentication

## License

MIT License - see LICENSE file for details.

## Support

For deployment issues, see [DEPLOYMENT.md](DEPLOYMENT.md).
For technical issues, check the logs and container health status.
