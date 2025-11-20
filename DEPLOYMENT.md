# PV Test Report Automation - Deployment Guide

## 🚀 Production Deployment Guide

This document provides step-by-step instructions for deploying the PV Test Report Automation System in a production environment.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or Docker-compatible environment
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Storage**: Minimum 100GB SSD
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

### Required Ports
- 80 (HTTP)
- 443 (HTTPS)
- 8501 (Streamlit - internal)
- 8000 (API - internal)
- 5432 (PostgreSQL - internal)
- 6379 (Redis - internal)
- 9000, 9001 (MinIO - internal)
- 5672, 15672 (RabbitMQ - internal)

## 🔧 Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**CRITICAL: Update the following in `.env`:**

```env
# Database - Use strong passwords
DB_USER=pv_admin
DB_PASSWORD=<STRONG_PASSWORD_HERE>

# MinIO Storage
MINIO_USER=admin
MINIO_PASSWORD=<STRONG_PASSWORD_HERE>

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=<STRONG_PASSWORD_HERE>

# Application Secret Keys
SECRET_KEY=<RANDOM_32_CHAR_STRING>
JWT_SECRET_KEY=<RANDOM_32_CHAR_STRING>

# LLM API Keys (Optional but recommended)
ANTHROPIC_API_KEY=<your_key>
OPENAI_API_KEY=<your_key>
GOOGLE_API_KEY=<your_key>

# Lab Accreditation
ACCREDITATION_NUMBER=<your_nabl_number>
LAB_NAME=<your_lab_name>
LAB_ADDRESS=<your_lab_address>
```

### 3. Prepare Assets

```bash
# Create assets directory
mkdir -p assets

# Add your logos
# - NABL logo: assets/nabl_logo.png
# - ILAC logo: assets/ilac_logo.png
# - Company logo: assets/company_logo.png
```

### 4. Build and Deploy

```bash
# Build all Docker images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Verify Deployment

```bash
# Run health check
python healthcheck.py

# Check individual services
docker-compose ps

# Check service health
curl http://localhost/health
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

## 🔍 Service Status

All services should show as "Up" and "healthy":

```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
pv_postgres         Up (healthy)        5432/tcp
pv_redis            Up (healthy)        6379/tcp
pv_minio            Up (healthy)        9000-9001/tcp
pv_rabbitmq         Up (healthy)        5672/tcp, 15672/tcp
pv_api_server       Up (healthy)        8000/tcp
pv_celery_worker    Up                  -
pv_streamlit_app    Up (healthy)        8501/tcp
pv_nginx            Up (healthy)        80/tcp, 443/tcp
```

## 📊 Access Applications

### Streamlit Web Application
- **URL**: http://localhost (or your domain)
- **Default Login**:
  - Username: `admin`
  - Password: `admin123` (⚠️ CHANGE IMMEDIATELY)

### API Documentation
- **Swagger UI**: http://localhost/api/docs
- **ReDoc**: http://localhost/api/redoc

### Service Admin Panels
- **MinIO Console**: http://localhost:9001
- **RabbitMQ Management**: http://localhost:15672

## 🔐 Security Configuration

### 1. Change Default Passwords

```bash
# Update .env with strong passwords
# Restart services
docker-compose down
docker-compose up -d
```

### 2. Enable HTTPS (Production)

```bash
# Generate SSL certificates (or use Let's Encrypt)
mkdir -p nginx/ssl

# Copy certificates
cp /path/to/cert.pem nginx/ssl/
cp /path/to/key.pem nginx/ssl/

# Edit nginx/nginx.conf to enable HTTPS server block
# Restart nginx
docker-compose restart nginx
```

### 3. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📈 Database Initialization

Database schema is automatically initialized on first startup via `database/init/01_init_schema.sql`.

### Manual Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U pv_admin -d pv_test_automation

# Run migrations (if needed)
# docker-compose exec api-server alembic upgrade head
```

## 🔄 Backup and Restore

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U pv_admin pv_test_automation > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U pv_admin pv_test_automation < backup_20241120.sql
```

### MinIO Data Backup

```bash
# Backup MinIO data
docker-compose exec minio mc mirror /data /backup/minio_$(date +%Y%m%d)
```

## 📊 Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f streamlit-app
docker-compose logs -f api-server
docker-compose logs -f celery-worker
```

### Resource Monitoring

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## 🔧 Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin production-deployment

# Rebuild and restart
docker-compose build
docker-compose down
docker-compose up -d
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (⚠️ CAUTION: This removes data)
docker volume prune
```

## ⚠️ Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Rebuild service
docker-compose build <service-name>
docker-compose up -d <service-name>
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify database is running
docker-compose exec postgres pg_isready -U pv_admin

# Check connection from API
docker-compose exec api-server env | grep DATABASE_URL
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Scale workers if needed
docker-compose up -d --scale celery-worker=4
```

## 📞 Support

For issues and support:
- GitHub Issues: https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues
- Documentation: See README.md

## ✅ Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] Default passwords changed
- [ ] HTTPS configured (production)
- [ ] Firewall configured
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Accreditation logos added
- [ ] LLM API keys configured
- [ ] Test workflow end-to-end
- [ ] User accounts created
- [ ] Equipment inventory added
- [ ] Calibration certificates uploaded

---

**Version**: 1.0.0
**Last Updated**: November 2024
**Deployment Status**: ✅ Production Ready
