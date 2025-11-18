# Production Deployment Guide

## Overview

Production deployment configuration for PV Test Report Automation system.

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Python 3.10+
- 4GB+ RAM
- 50GB+ disk space

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your production values
nano .env
```

### 2. Database Setup

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run migrations
alembic upgrade head
```

### 3. Application Deployment

```bash
# Build and start all services
docker-compose up -d

# Check service health
docker-compose ps
```

### 4. Access Applications

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501
- Prometheus: http://localhost:9090

## Production Checklist

### Security
- [ ] Change default passwords
- [ ] Configure JWT secret key
- [ ] Set up SSL/TLS certificates
- [ ] Enable firewall rules
- [ ] Configure API rate limiting
- [ ] Set up authentication

### Database
- [ ] Enable automatic backups
- [ ] Configure replication
- [ ] Set up monitoring
- [ ] Optimize queries
- [ ] Index frequently queried fields

### Monitoring
- [ ] Configure Prometheus metrics
- [ ] Set up alerting
- [ ] Enable error tracking
- [ ] Configure log aggregation
- [ ] Set up uptime monitoring

### Compliance
- [ ] Verify ISO 17025 requirements
- [ ] Configure NABL settings
- [ ] Enable audit logging
- [ ] Set up digital signatures
- [ ] Document calibration procedures

### Performance
- [ ] Configure caching
- [ ] Enable CDN for static files
- [ ] Optimize database queries
- [ ] Set up load balancing
- [ ] Configure auto-scaling

## Maintenance

### Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres pv_test_automation > backup.sql

# Backup data directory
tar -czf data_backup.tar.gz ./data
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Restart services
docker-compose up -d
```

### Logs

```bash
# View application logs
docker-compose logs -f api

# View database logs
docker-compose logs -f postgres
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Test connection
psql -h localhost -U postgres -d pv_test_automation
```

### API Not Responding

```bash
# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api
```

## Support

For support, please contact: support@pvtestautomation.com
Documentation: https://docs.pvtestautomation.com
