# DigitalOcean Deployment Guide

## JWT MySQL Automation Service - Production Deployment

This guide covers multiple ways to deploy your JWT MySQL Automation Service to DigitalOcean.

## Prerequisites

1. **DigitalOcean Account**: Sign up at [digitalocean.com](https://digitalocean.com)
2. **doctl CLI**: DigitalOcean command-line tool
3. **Docker**: For local building and testing
4. **Git**: For version control

### Install doctl (DigitalOcean CLI)

```bash
# Linux/macOS
curl -sL https://github.com/digitalocean/doctl/releases/download/v1.100.0/doctl-1.100.0-linux-amd64.tar.gz | tar -xzv
sudo mv doctl /usr/local/bin

# Authenticate
doctl auth init
```

## Deployment Options

### Option 1: DigitalOcean App Platform (Recommended)

**Pros**: Fully managed, auto-scaling, built-in CI/CD
**Cons**: Higher cost for simple applications

#### Method 1A: Using Docker Hub

1. **Build and push to Docker Hub**:
   ```bash
   docker build -t yourusername/jwt-mysql-automation:latest .
   docker push yourusername/jwt-mysql-automation:latest
   ```

2. **Create App Platform application**:
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Choose "Docker Hub" as source
   - Enter your image: `yourusername/jwt-mysql-automation:latest`
   - Configure environment variables (see below)
   - Add MySQL database component

#### Method 1B: Using GitHub

1. **Push code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/jwt-mysql-automation.git
   git push -u origin main
   ```

2. **Create App Platform application**:
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App" 
   - Choose "GitHub" as source
   - Select your repository
   - DigitalOcean will auto-detect the Dockerfile

### Option 2: DigitalOcean Droplet + Docker Compose

**Pros**: Full control, cost-effective
**Cons**: Manual management, no auto-scaling

1. **Create a Droplet**:
   ```bash
   doctl compute droplet create jwt-mysql-app \
     --region nyc3 \
     --image docker-20-04 \
     --size s-2vcpu-2gb \
     --ssh-keys YOUR_SSH_KEY_ID
   ```

2. **SSH into the droplet**:
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

3. **Upload your project**:
   ```bash
   # From your local machine
   scp -r /path/to/your/project root@YOUR_DROPLET_IP:/root/jwt-mysql-app
   ```

4. **Run the application**:
   ```bash
   cd /root/jwt-mysql-app
   cp .env.example .env
   # Edit .env with your values
   nano .env
   docker-compose up -d
   ```

### Option 3: DigitalOcean Kubernetes

**Pros**: Enterprise-grade, high availability
**Cons**: Complex setup, higher cost

1. **Create a Kubernetes cluster**:
   ```bash
   doctl kubernetes cluster create jwt-k8s-cluster \
     --region nyc3 \
     --size s-2vcpu-2gb \
     --count 2
   ```

2. **Deploy using Kubernetes manifests** (create k8s/ directory with manifests)

## Environment Variables Configuration

### Required Environment Variables

```bash
# MySQL Configuration
MYSQL_HOST=your-mysql-host
MYSQL_USER=root
MYSQL_PASS=your-secure-password
MYSQL_DB=arkane_settings

# JWT Configuration  
JWT_SECRET=your-jwt-secret-key-here

# Optional: Database User
MYSQL_USER_NAME=arkane_user
MYSQL_USER_PASS=your-user-password
```

### App Platform Environment Variables Setup

1. In your App Platform dashboard
2. Go to "Settings" → "Environment Variables"
3. Add all required variables
4. Mark sensitive variables as "encrypted"

## Database Setup

### Option A: DigitalOcean Managed Database (Recommended)

1. **Create MySQL Database**:
   - Go to DigitalOcean Databases
   - Create MySQL 8.0 cluster
   - Choose appropriate size (starts at $15/month)

2. **Configure Connection**:
   - Use provided connection details
   - Update environment variables

### Option B: MySQL in Docker Container

- Uses the MySQL container defined in docker-compose.yml
- Data persisted in Docker volume
- Less reliable but cost-effective for development

## Security Considerations

1. **Environment Variables**: Never commit real secrets to Git
2. **Database Access**: Use strong passwords and restrict access
3. **Network Security**: Configure firewalls appropriately
4. **SSL/TLS**: Enable for production databases
5. **Regular Updates**: Keep Docker images updated

## Monitoring and Logs

### App Platform
- Built-in application metrics
- Log streaming in dashboard
- Resource usage monitoring

### Droplet
- SSH access for debugging
- Docker logs: `docker-compose logs -f`
- System monitoring with `htop`, `docker stats`

## Cost Estimation

### App Platform
- Basic app: ~$5/month
- MySQL database: ~$15/month
- Total: ~$20/month

### Droplet + Docker
- 2GB Droplet: $12/month
- Managed MySQL: $15/month
- Total: ~$27/month

### Self-hosted (Droplet only)
- 2GB Droplet: $12/month
- MySQL in container: $0
- Total: ~$12/month

## Quick Start Script

Use the provided deployment script:

```bash
./deploy.sh
```

This interactive script will guide you through:
1. Environment setup
2. Deployment method selection
3. Automated deployment process

## Troubleshooting

### Common Issues

1. **Connection Timeout**: Check firewall settings
2. **Authentication Failed**: Verify database credentials
3. **Container Won't Start**: Check logs with `docker logs`
4. **Database Not Ready**: Ensure MySQL is fully initialized

### Debug Commands

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs jwt_automation
docker-compose logs mysql

# Execute commands in container
docker-compose exec jwt_automation python check_token.py

# Database connection test
docker-compose exec mysql mysql -u root -p
```

## Support

For issues:
1. Check the logs first
2. Verify environment variables
3. Test database connectivity
4. Review DigitalOcean documentation

## Next Steps

After deployment:
1. Monitor application logs
2. Set up alerting (optional)
3. Configure backups
4. Plan for scaling if needed

---

**Note**: This is a production-ready setup. Always test in a staging environment first.
