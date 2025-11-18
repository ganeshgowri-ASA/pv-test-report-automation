#!/bin/bash
# Deployment script for PV Test Report Automation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
NAMESPACE="pvtest"

echo -e "${GREEN}PV Test Report Automation - Deployment Script${NC}"
echo "================================================"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Namespace: $NAMESPACE"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}kubectl not found. Please install kubectl.${NC}"
        exit 1
    fi

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}docker not found. Please install docker.${NC}"
        exit 1
    fi

    echo -e "${GREEN}Prerequisites OK${NC}"
}

# Function to build Docker image
build_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"

    cd ..
    docker build -t pvtest/automation:$VERSION -f deployment/Dockerfile .

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Docker image built successfully${NC}"
    else
        echo -e "${RED}Docker build failed${NC}"
        exit 1
    fi
}

# Function to push image to registry
push_image() {
    echo -e "${YELLOW}Pushing image to registry...${NC}"

    docker push pvtest/automation:$VERSION

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Image pushed successfully${NC}"
    else
        echo -e "${RED}Image push failed${NC}"
        exit 1
    fi
}

# Function to create namespace
create_namespace() {
    echo -e "${YELLOW}Creating namespace...${NC}"

    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${GREEN}Namespace ready${NC}"
}

# Function to apply Kubernetes manifests
apply_manifests() {
    echo -e "${YELLOW}Applying Kubernetes manifests...${NC}"

    # Apply in order
    kubectl apply -f deployment/kubernetes/configmap.yaml
    kubectl apply -f deployment/kubernetes/deployment.yaml
    kubectl apply -f deployment/kubernetes/ingress.yaml

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Manifests applied successfully${NC}"
    else
        echo -e "${RED}Failed to apply manifests${NC}"
        exit 1
    fi
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"

    kubectl rollout status deployment/pv-test-automation -n $NAMESPACE --timeout=5m

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Deployment ready${NC}"
    else
        echo -e "${RED}Deployment failed${NC}"
        exit 1
    fi
}

# Function to run smoke tests
run_smoke_tests() {
    echo -e "${YELLOW}Running smoke tests...${NC}"

    # Get service URL
    SERVICE_URL=$(kubectl get ingress pv-test-automation -n $NAMESPACE -o jsonpath='{.spec.rules[0].host}')

    # Check health endpoint
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$SERVICE_URL/health || echo "000")

    if [ "$HEALTH_STATUS" = "200" ]; then
        echo -e "${GREEN}Smoke tests passed${NC}"
    else
        echo -e "${RED}Smoke tests failed (HTTP $HEALTH_STATUS)${NC}"
        exit 1
    fi
}

# Function to display deployment info
display_info() {
    echo ""
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "================================================"
    echo "Namespace: $NAMESPACE"
    echo "Pods:"
    kubectl get pods -n $NAMESPACE
    echo ""
    echo "Services:"
    kubectl get svc -n $NAMESPACE
    echo ""
    echo "Ingress:"
    kubectl get ingress -n $NAMESPACE
}

# Main deployment flow
main() {
    check_prerequisites

    if [ "$ENVIRONMENT" = "production" ]; then
        read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Deployment cancelled"
            exit 0
        fi
    fi

    build_image
    push_image
    create_namespace
    apply_manifests
    wait_for_deployment
    run_smoke_tests
    display_info

    echo -e "${GREEN}Deployment successful!${NC}"
}

# Run main function
main
