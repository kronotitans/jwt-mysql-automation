#!/bin/bash

# DigitalOcean Deployment Script for JWT MySQL Automation Service
# This script helps deploy the application to DigitalOcean

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== DigitalOcean JWT MySQL Automation Deployment ===${NC}"

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}Error: doctl is not installed. Please install it first:${NC}"
    echo "curl -sL https://github.com/digitalocean/doctl/releases/download/v1.100.0/doctl-1.100.0-linux-amd64.tar.gz | tar -xzv"
    echo "sudo mv doctl /usr/local/bin"
    exit 1
fi

# Check if user is authenticated
if ! doctl auth list &> /dev/null; then
    echo -e "${RED}Error: Please authenticate with DigitalOcean first:${NC}"
    echo "doctl auth init"
    exit 1
fi

# Function to create .env file
create_env_file() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file from template...${NC}"
        cp .env.example .env
        echo -e "${GREEN}Please edit .env file with your actual values before proceeding.${NC}"
        echo -e "${YELLOW}Press Enter to continue after editing .env file...${NC}"
        read
    fi
}

# Function to deploy using Docker Hub
deploy_docker_hub() {
    echo -e "${BLUE}Option 1: Deploy using Docker Hub${NC}"
    echo "1. Build and push image to Docker Hub"
    echo "2. Create DigitalOcean App Platform application"
    
    read -p "Enter your Docker Hub username: " DOCKER_USER
    read -p "Enter your image name (jwt-mysql-automation): " IMAGE_NAME
    IMAGE_NAME=${IMAGE_NAME:-jwt-mysql-automation}
    
    # Build and push to Docker Hub
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t $DOCKER_USER/$IMAGE_NAME:latest .
    
    echo -e "${YELLOW}Pushing to Docker Hub...${NC}"
    docker push $DOCKER_USER/$IMAGE_NAME:latest
    
    echo -e "${GREEN}Image pushed successfully!${NC}"
    echo -e "${BLUE}Now create an app on DigitalOcean App Platform using:${NC}"
    echo "Image: $DOCKER_USER/$IMAGE_NAME:latest"
}

# Function to deploy using GitHub
deploy_github() {
    echo -e "${BLUE}Option 2: Deploy using GitHub Repository${NC}"
    echo "1. Push code to GitHub repository"
    echo "2. Create DigitalOcean App Platform application"
    
    read -p "Enter your GitHub repository URL: " GITHUB_REPO
    
    if [ ! -d .git ]; then
        git init
        git add .
        git commit -m "Initial commit for DigitalOcean deployment"
        git remote add origin $GITHUB_REPO
        git push -u origin main
    else
        git add .
        git commit -m "Update for DigitalOcean deployment" || true
        git push
    fi
    
    echo -e "${GREEN}Code pushed to GitHub!${NC}"
    echo -e "${BLUE}Now create an app on DigitalOcean App Platform using the GitHub integration.${NC}"
}

# Function to create DigitalOcean Droplet
deploy_droplet() {
    echo -e "${BLUE}Option 3: Deploy to DigitalOcean Droplet${NC}"
    
    read -p "Enter droplet name (jwt-mysql-app): " DROPLET_NAME
    DROPLET_NAME=${DROPLET_NAME:-jwt-mysql-app}
    
    read -p "Enter region (nyc3): " REGION
    REGION=${REGION:-nyc3}
    
    # Create droplet
    echo -e "${YELLOW}Creating droplet...${NC}"
    doctl compute droplet create $DROPLET_NAME \
        --region $REGION \
        --image docker-20-04 \
        --size s-1vcpu-1gb \
        --ssh-keys $(doctl compute ssh-key list --format ID --no-header | head -1) \
        --wait
    
    # Get droplet IP
    DROPLET_IP=$(doctl compute droplet get $DROPLET_NAME --format PublicIPv4 --no-header)
    
    echo -e "${GREEN}Droplet created successfully!${NC}"
    echo -e "${BLUE}IP Address: $DROPLET_IP${NC}"
    echo -e "${YELLOW}You can now SSH into the droplet and run docker-compose up -d${NC}"
    echo "ssh root@$DROPLET_IP"
}

# Main menu
echo -e "${YELLOW}Choose deployment method:${NC}"
echo "1. Docker Hub + App Platform"
echo "2. GitHub + App Platform"  
echo "3. DigitalOcean Droplet"
echo "4. Exit"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        create_env_file
        deploy_docker_hub
        ;;
    2) 
        create_env_file
        deploy_github
        ;;
    3)
        create_env_file
        deploy_droplet
        ;;
    4)
        echo -e "${BLUE}Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Deployment process completed!${NC}"
