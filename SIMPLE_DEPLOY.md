# 🚀 Simple Deployment Guide

## Quick Setup (5 minutes)

### 1. Setup Docker Hub Secrets
Go to GitHub repo → **Settings** → **Secrets** → **Actions**

Add these:
- `DOCKERHUB_USERNAME`: `kronotitans`
- `DOCKERHUB_TOKEN`: (get from Docker Hub → Settings → Security)

### 2. Push Code (Auto-builds Docker image)
```bash
git push origin main
```
✅ GitHub Actions automatically builds and pushes to Docker Hub

### 3. Deploy to DigitalOcean

#### Option A: App Platform (Easiest)
1. Go to https://cloud.digitalocean.com/apps
2. **Create App** → **Docker Hub**
3. **Image**: `kronotitans/jwt-mysql-automation:latest`
4. **Add Environment Variables**:
   ```
   JWT_SECRET=your-secret-key-here
   MYSQL_HOST=your-db-host
   MYSQL_USER=your-db-user
   MYSQL_PASS=your-db-password
   MYSQL_DB=arkane_settings
   ```
5. **Add MySQL Database** (optional - or use included one)
6. **Deploy**

#### Option B: Docker Run (Simple)
```bash
# Pull latest image
docker pull kronotitans/jwt-mysql-automation:latest

# Run with environment file
docker run -d \
  --name jwt-automation \
  -e JWT_SECRET=your-secret-key \
  -e MYSQL_HOST=your-db-host \
  -e MYSQL_USER=your-db-user \
  -e MYSQL_PASS=your-db-password \
  -e MYSQL_DB=arkane_settings \
  -p 8080:8080 \
  kronotitans/jwt-mysql-automation:latest
```

## ✅ That's it! 

**Health Check**: `http://your-app:8080/health`

**Every time you push code** → New Docker image builds automatically → Redeploy on DigitalOcean

---

**Repository**: https://github.com/kronotitans/jwt-mysql-automation  
**Docker Image**: `kronotitans/jwt-mysql-automation:latest`
