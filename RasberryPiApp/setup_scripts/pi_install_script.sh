#!/bin/bash
# Classifier Installation Script for Raspberry Pi
# This script sets up everything needed for the classifier service

set -e 

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' 

# Configuration - Edit these variables
API_URL=""
API_KEY=""
INTERVAL=300  
THRESHOLD=0.5  
INSTALL_DIR="/home/pi/classifier"

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Raspberry Pi Classifier Installation   ${NC}"
echo -e "${GREEN}=========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (use sudo)${NC}"
  exit 1
fi

# Ensure we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
  echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi.${NC}"
  echo -n "Continue anyway? [y/N] "
  read -r response
  if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Installation aborted."
    exit 1
  fi
fi

echo -e "\n${GREEN}Installing required packages...${NC}"
apt-get update
apt-get install -y python3-pip python3-opencv libatlas-base-dev

echo -e "\n${GREEN}Installing Python dependencies...${NC}"
pip3 install requests pillow tflite-runtime

echo -e "\n${GREEN}Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
chown admin:admin "$INSTALL_DIR"

echo -e "\n${GREEN}Downloading classifier scripts...${NC}"

# If downloading from the web:
# wget -O "$INSTALL_DIR/pi_client.py" https://your-repo/pi_client.py
# wget -O "$INSTALL_DIR/classifier.service" https://your-repo/classifier.service

mkdir -p "$INSTALL_DIR/models"
mkdir -p "$INSTALL_DIR/images"
chown -R admin:admin "$INSTALL_DIR"

echo -e "\n${GREEN}Setting up systemd service...${NC}"
cat > /etc/systemd/system/classifier.service << EOF
[Unit]
Description=Image Classifier Service
After=network.target

[Service]
User=admin
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/pi_client.py --api $API_URL --interval $INTERVAL --threshold $THRESHOLD --apikey $API_KEY
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=classifier

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable classifier.service

echo -e "\n${GREEN}Starting classifier service...${NC}"
systemctl start classifier.service

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "The classifier service is now installed and will start automatically on boot."
echo -e "You can check its status with: ${YELLOW}sudo systemctl status classifier${NC}"
echo -e "View logs with: ${YELLOW}sudo journalctl -u classifier${NC}"
echo
echo -e "Service configuration:"
echo -e "  - API URL: ${YELLOW}$API_URL${NC}"
echo -e "  - Capture interval: ${YELLOW}$INTERVAL seconds${NC}"
echo -e "  - Confidence threshold: ${YELLOW}$THRESHOLD${NC}"
echo
echo -e "To modify these settings, edit /etc/systemd/system/classifier.service"
echo -e "then run: ${YELLOW}sudo systemctl daemon-reload && sudo systemctl restart classifier${NC}"