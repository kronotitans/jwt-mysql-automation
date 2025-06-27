# 🚀 Super Robust GitHub → Docker Hub → DigitalOcean Pipeline

This guide sets up a fully automated CI/CD pipeline: **GitHub** → **Docker Hub** → **DigitalOcean**

## 🏗️ Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   GitHub    │───▶│GitHub Actions│───▶│ Docker Hub  │───▶│DigitalOcean │
│   (Source)  │    │   (Build)   │    │  (Registry) │    │    (Run)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 📋 Prerequisites

### 1. GitHub Repository Setup
- ✅ Repository: `https://github.com/kronotitans/jwt-mysql-automation`
- ✅ Code pushed with GitHub Actions workflow

### 2. Docker Hub Account
- Create account at [hub.docker.com](https://hub.docker.com)
- Generate access token: **Settings** → **Security** → **New Access Token**

### 3. DigitalOcean Account
- Sign up at [digitalocean.com](https://digitalocean.com)
- Get API token: **API** → **Generate New Token**

## 🔐 Setup GitHub Secrets

In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**

Add these repository secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DOCKERHUB_USERNAME` | `kronotitans` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | `dckr_pat_xxxxx` | Docker Hub access token |

## 🔧 Step-by-Step Deployment

### Step 1: Push Code to GitHub (Already Done!)

Your repository is ready with:
- ✅ **GitHub Actions workflow** (`.github/workflows/docker-build.yml`)
- ✅ **Multi-stage Dockerfile** (optimized for production)
- ✅ **Environment configuration** (`.env.example`)
- ✅ **Health check endpoints** (built-in HTTP server)

### Step 2: Automatic Docker Build

When you push to `main` branch, GitHub Actions will:

1. **Build multi-platform image** (AMD64 + ARM64)
2. **Push to Docker Hub** as `kronotitans/jwt-mysql-automation:latest`
3. **Tag with version** for releases

### Step 3: Deploy to DigitalOcean

#### Option A: App Platform (Recommended)

1. **Go to DigitalOcean App Platform**:
   ```
   https://cloud.digitalocean.com/apps
   ```

2. **Create New App**:
   - Click **"Create App"**
   - Choose **"Docker Hub"** as source
   - Image: `kronotitans/jwt-mysql-automation:latest`

3. **Configure Environment Variables**:
   ```env
   MYSQL_HOST=mysql-cluster-do-user-xxxxx.db.ondigitalocean.com
   MYSQL_PORT=25060
   MYSQL_USER=doadmin
   MYSQL_PASS=your-secure-password
   MYSQL_DB=arkane_settings
   JWT_SECRET=super-secure-jwt-secret-2025
   ENVIRONMENT=production
   ```

4. **Add Database Component**:
   - **Engine**: MySQL 8
   - **Size**: Basic ($15/month)
   - **Nodes**: 1

5. **Configure Health Checks**:
   - **HTTP Path**: `/health`
   - **Port**: 8080

#### Option B: Droplet with Docker

1. **Create Droplet**:
   ```bash
   doctl compute droplet create jwt-production \
     --region nyc3 \
     --image docker-20-04 \
     --size s-2vcpu-2gb \
     --ssh-keys YOUR_SSH_KEY_ID
   ```

2. **Deploy Container**:
   ```bash
   # SSH into droplet
   ssh root@YOUR_DROPLET_IP
   
   # Pull and run the image
   docker pull kronotitans/jwt-mysql-automation:latest
   
   # Create environment file
   cat > .env << EOF
   MYSQL_HOST=your-managed-db-host.db.ondigitalocean.com
   MYSQL_PORT=25060
   MYSQL_USER=doadmin
   MYSQL_PASS=your-db-password
   MYSQL_DB=arkane_settings
   JWT_SECRET=super-secure-jwt-secret-2025
   EOF
   
   # Run container
   docker run -d \
     --name jwt-automation \
     --env-file .env \
     -p 8080:8080 \
     --restart unless-stopped \
     kronotitans/jwt-mysql-automation:latest
   ```

## 🔍 Monitoring & Health Checks

### Built-in Endpoints

Your service exposes these endpoints for monitoring:

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | Basic health check | `{"status": "healthy"}` |
| `GET /status` | Detailed status | Database + token info |

### Example Health Check
```bash
curl https://your-app.ondigitalocean.app/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-27T10:30:00Z",
  "service": "jwt-mysql-automation",
  "database": "connected"
}
```

## 🔄 Continuous Deployment

### Auto-Deploy on Code Changes

1. **Make changes** to your code locally
2. **Commit and push** to `main` branch:
   ```bash
   git add .
   git commit -m "Update JWT automation logic"
   git push origin main
   ```
3. **GitHub Actions automatically**:
   - Builds new Docker image
   - Pushes to Docker Hub
   - DigitalOcean pulls latest image (if configured)

### Manual Deployment Update

Force DigitalOcean to pull latest image:

```bash
# Using doctl CLI
doctl apps create-deployment YOUR_APP_ID

# Or through DigitalOcean dashboard
# Apps → Your App → Settings → Force Rebuild
```

## 🛡️ Security Features

### Production Security
- ✅ **Non-root container** execution
- ✅ **Environment-based secrets** (no hardcoded passwords)
- ✅ **Multi-stage Docker build** (smaller attack surface)
- ✅ **Health check monitoring**
- ✅ **Automatic JWT rotation** (5-minute expiry)

### Database Security
- ✅ **Managed database** with automatic backups
- ✅ **SSL/TLS encryption** in transit
- ✅ **Private networking** (VPC)
- ✅ **Strong password requirements**

## 📊 Cost Breakdown

### DigitalOcean App Platform
| Component | Cost | Description |
|-----------|------|-------------|
| Basic App | $5/month | Container hosting |
| MySQL DB | $15/month | Managed database |
| **Total** | **$20/month** | **Production-ready** |

### Self-Hosted Option
| Component | Cost | Description |
|-----------|------|-------------|
| Droplet | $12/month | 2GB RAM, 1 vCPU |
| Managed DB | $15/month | MySQL cluster |
| **Total** | **$27/month** | **More control** |

## 🔧 Troubleshooting

### Common Issues

**1. Docker Build Fails**
```bash
# Check GitHub Actions logs
# Usually missing Docker Hub credentials
```

**2. Container Won't Start**
```bash
# Check logs in DigitalOcean dashboard
# Usually environment variable issues
```

**3. Database Connection Failed**
```bash
# Verify database credentials
# Check network connectivity
curl https://your-app.ondigitalocean.app/health
```

**4. Health Check Failing**
```bash
# Check if port 8080 is accessible
# Verify health endpoints respond
curl https://your-app.ondigitalocean.app/status
```

## 🚀 Next Steps

### After Deployment
1. **Monitor logs** in DigitalOcean dashboard
2. **Set up alerts** for health check failures
3. **Configure backups** for your database
4. **Set up custom domain** (optional)

### Scaling
- **Horizontal**: Increase instance count
- **Vertical**: Upgrade to larger droplet/app size
- **Database**: Upgrade to cluster with read replicas

## 📞 Quick Deployment Commands

```bash
# 1. Push code (triggers auto-build)
git push origin main

# 2. Check build status
open https://github.com/kronotitans/jwt-mysql-automation/actions

# 3. Verify Docker image
docker pull kronotitans/jwt-mysql-automation:latest

# 4. Deploy to DigitalOcean
# Use App Platform GUI or doctl commands
```

---

**🎯 Result**: A fully automated, production-ready JWT automation service with zero-downtime deployments!
