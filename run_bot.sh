#!/bin/bash

# Script to run the Telegram bot on Ubuntu using Docker
# This script provides start, stop, restart, status, and install commands

# Exit on any error
set -e

# Configuration
BOT_DIR="/opt/userinfobot"
SERVICE_NAME="userinfobot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to start the bot
start_bot() {
    print_status "Starting $SERVICE_NAME..."
    
    if [ ! -d "$BOT_DIR" ]; then
        print_error "Bot directory $BOT_DIR does not exist."
        exit 1
    fi

    cd $BOT_DIR

    # Check if .env file exists
    if [ ! -f .env ]; then
        print_error ".env file does not exist in $BOT_DIR"
        exit 1
    fi

    # Start the bot using Docker Compose
    docker-compose up -d
    
    print_status "$SERVICE_NAME started successfully."
}

# Function to stop the bot
stop_bot() {
    print_status "Stopping $SERVICE_NAME..."
    
    if [ ! -d "$BOT_DIR" ]; then
        print_error "Bot directory $BOT_DIR does not exist."
        exit 1
    fi

    cd $BOT_DIR

    # Stop the bot using Docker Compose
    docker-compose down
    
    print_status "$SERVICE_NAME stopped successfully."
}

# Function to restart the bot
restart_bot() {
    print_status "Restarting $SERVICE_NAME..."
    
    if [ ! -d "$BOT_DIR" ]; then
        print_error "Bot directory $BOT_DIR does not exist."
        exit 1
    fi

    cd $BOT_DIR

    # Restart the bot using Docker Compose
    docker-compose down
    docker-compose up -d
    
    print_status "$SERVICE_NAME restarted successfully."
}

# Function to check the status of the bot
status_bot() {
    if [ ! -d "$BOT_DIR" ]; then
        print_error "Bot directory $BOT_DIR does not exist."
        exit 1
    fi

    cd $BOT_DIR

    # Check the status of the bot using Docker Compose
    docker-compose ps
}

# Function to install the service
install_service() {
    print_status "Installing $SERVICE_NAME as a system service..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run this script as root (use sudo) to install the service."
        exit 1
    fi

    # Copy the script to /usr/local/bin
    cp "$0" /usr/local/bin/$SERVICE_NAME
    chmod +x /usr/local/bin/$SERVICE_NAME

    # Create systemd service file
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=UserInfoBot Telegram Bot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/$SERVICE_NAME start
ExecStop=/usr/local/bin/$SERVICE_NAME stop
ExecReload=/usr/local/bin/$SERVICE_NAME restart

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd daemon
    systemctl daemon-reload

    # Enable the service to start at boot
    systemctl enable $SERVICE_NAME

    print_status "$SERVICE_NAME service installed and enabled."
    print_warning "Please ensure the bot directory is located at $BOT_DIR and contains the required files."
}

# Function to show help
show_help() {
    echo "Usage: $0 {start|stop|restart|status|install}"
    echo
    echo "Commands:"
    echo "  start   - Start the bot container"
    echo "  stop    - Stop the bot container"
    echo "  restart - Restart the bot container"
    echo "  status  - Show the status of the bot container"
    echo "  install - Install the bot as a system service (requires root)"
    echo
    echo "Example: $0 start"
}

# Main script logic
case "$1" in
    start)
        check_docker
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        check_docker
        restart_bot
        ;;
    status)
        status_bot
        ;;
    install)
        install_service
        ;;
    *)
        show_help
        exit 1
        ;;
esac