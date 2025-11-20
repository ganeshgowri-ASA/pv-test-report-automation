# Deployment Guide

This directory contains deployment configurations and scripts for the PV Test Report Automation system.

## Contents

- `Dockerfile` - Production Docker image configuration
- `docker-compose.yml` - Local development with Docker Compose
- `.dockerignore` - Files to exclude from Docker build
- `.env.example` - Environment variables template
- `kubernetes/` - Kubernetes manifests
- `scripts/` - Deployment and maintenance scripts

## Quick Start

### Local Development with Docker Compose

1. Copy environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f app
   ```

4. Stop services:
   ```bash
   docker-compose down
   ```

### Building Docker Image

```bash
docker build -t pvtest/automation:latest -f deployment/Dockerfile .
```

### Running Tests in Docker

```bash
docker-compose run --rm app pytest tests/
```

## Production Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker registry access
- SSL certificates (for HTTPS)

### Deployment Steps

1. Build and push Docker image:
   ```bash
   docker build -t pvtest/automation:v1.0.0 -f deployment/Dockerfile .
   docker push pvtest/automation:v1.0.0
   ```

2. Create namespace:
   ```bash
   kubectl create namespace pvtest
   ```

3. Create secrets:
   ```bash
   kubectl create secret generic pv-test-secrets \
     --from-literal=database-url='postgresql://...' \
     --from-literal=redis-url='redis://...' \
     --from-literal=secret-key='...' \
     -n pvtest
   ```

4. Apply Kubernetes manifests:
   ```bash
   kubectl apply -f deployment/kubernetes/
   ```

5. Check deployment status:
   ```bash
   kubectl rollout status deployment/pv-test-automation -n pvtest
   ```

### Using Deployment Script

```bash
cd deployment/scripts
chmod +x deploy.sh
./deploy.sh staging v1.0.0
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Application secret key
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Resource Requirements

**Minimum:**
- CPU: 250m (0.25 cores)
- Memory: 512Mi

**Recommended:**
- CPU: 1000m (1 core)
- Memory: 1Gi

### Scaling

Horizontal Pod Autoscaler is configured to scale between 3-10 replicas based on:
- CPU utilization: 70%
- Memory utilization: 80%

Manual scaling:
```bash
kubectl scale deployment pv-test-automation --replicas=5 -n pvtest
```

## Health Checks

### Endpoints

- `/health` - Basic health check
- `/ready` - Readiness probe (includes dependency checks)
- `/metrics` - Prometheus metrics

### Manual Health Check

```bash
python deployment/scripts/health_check.py
```

## Monitoring

### Logs

View application logs:
```bash
kubectl logs -f deployment/pv-test-automation -n pvtest
```

### Metrics

Access Prometheus metrics:
```bash
kubectl port-forward svc/pv-test-automation 8000:80 -n pvtest
curl http://localhost:8000/metrics
```

## Troubleshooting

### Pod Not Starting

Check pod status:
```bash
kubectl describe pod <pod-name> -n pvtest
```

View logs:
```bash
kubectl logs <pod-name> -n pvtest
```

### Database Connection Issues

Test database connectivity:
```bash
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql postgresql://user:pass@postgres:5432/pvtest_db
```

### High Memory Usage

Check resource usage:
```bash
kubectl top pods -n pvtest
```

Scale up resources:
```bash
kubectl set resources deployment pv-test-automation \
  --limits=memory=2Gi \
  --requests=memory=1Gi \
  -n pvtest
```

## Backup and Recovery

### Database Backup

```bash
kubectl exec -it deployment/postgres -n pvtest -- \
  pg_dump -U pvtest pvtest_db > backup.sql
```

### Restore Database

```bash
kubectl exec -i deployment/postgres -n pvtest -- \
  psql -U pvtest pvtest_db < backup.sql
```

## CI/CD

GitHub Actions workflows are configured for:
- Automated testing on PR
- Docker image building
- Deployment to staging/production

See `.github/workflows/` for details.

## Security

- All secrets stored in Kubernetes secrets
- TLS/SSL enabled for external traffic
- Network policies to restrict pod communication
- Regular security scanning with Bandit and Safety

## Support

For issues or questions:
- Create an issue in the repository
- Contact the DevOps team
- Check the main README.md for general documentation
