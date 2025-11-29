#!/bin/bash

# Quick deployment script for config service to remote server
# Usage: ./quick-deploy.sh [remote_host] [remote_user]

REMOTE_HOST=${1:-"192.168.88.120"}
REMOTE_USER=${2:-"steelburn"}
REMOTE_PATH="~/Development/ai-stack-build"

echo "🚀 Quick Deploy: Config Service to $REMOTE_HOST"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Transferring files to $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH${NC}"

# Transfer deployment scripts
scp deploy-config-service.sh "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
scp test-config-service.sh "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
scp CONFIG_SERVICE_DEPLOYMENT.md "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"

# Transfer config service directory
echo "Transferring config-service directory..."
rsync -avz --delete config-service/ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/config-service/"

echo -e "${GREEN}Files transferred successfully!${NC}"
echo ""
echo "Now SSH to the remote server and run:"
echo "  ssh $REMOTE_USER@$REMOTE_HOST"
echo "  cd $REMOTE_PATH"
echo "  ./deploy-config-service.sh"
echo "  ./test-config-service.sh"
echo ""
echo "Then access: http://$REMOTE_HOST:8083"