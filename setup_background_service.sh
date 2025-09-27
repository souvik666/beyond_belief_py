#!/bin/bash

# Beyond Belief Background Service Setup Script
# This script sets up the automation to run even when laptop lid is closed

set -e

echo "🚀 Setting up Beyond Belief Background Service..."
echo "================================================"

# Get current directory
CURRENT_DIR=$(pwd)
USER_NAME=$(whoami)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please run this script as a regular user, not as root"
    exit 1
fi

print_status "Current directory: $CURRENT_DIR"
print_status "User: $USER_NAME"

# Step 1: Configure laptop lid settings
print_status "Step 1: Configuring laptop lid settings..."

# Backup original logind.conf
sudo cp /etc/systemd/logind.conf /etc/systemd/logind.conf.backup 2>/dev/null || true

# Configure logind to ignore lid close
print_status "Configuring systemd-logind to ignore lid close..."
sudo tee /etc/systemd/logind.conf.d/99-ignore-lid.conf > /dev/null << EOF
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
EOF

print_success "Lid close settings configured"

# Step 2: Create systemd service
print_status "Step 2: Creating systemd service..."

SERVICE_NAME="beyond-belief-automation"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Create the service file
sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Beyond Belief Facebook Automation Service
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$CURRENT_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/main.py start --interval 10
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=beyond-belief

# Resource limits
MemoryMax=1G
CPUQuota=50%

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=false
ReadWritePaths=$CURRENT_DIR

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service created: $SERVICE_FILE"

# Step 3: Create management scripts
print_status "Step 3: Creating management scripts..."

# Create start script
cat > start_service.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Beyond Belief Automation Service..."
sudo systemctl start beyond-belief-automation
sudo systemctl enable beyond-belief-automation
echo "✅ Service started and enabled for auto-start"
echo "📊 Service status:"
sudo systemctl status beyond-belief-automation --no-pager
EOF

# Create stop script
cat > stop_service.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Beyond Belief Automation Service..."
sudo systemctl stop beyond-belief-automation
sudo systemctl disable beyond-belief-automation
echo "✅ Service stopped and disabled"
EOF

# Create status script
cat > check_service.sh << 'EOF'
#!/bin/bash
echo "📊 Beyond Belief Automation Service Status:"
echo "==========================================="
sudo systemctl status beyond-belief-automation --no-pager
echo ""
echo "📋 Recent logs:"
echo "==============="
sudo journalctl -u beyond-belief-automation --no-pager -n 20
EOF

# Create restart script
cat > restart_service.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting Beyond Belief Automation Service..."
sudo systemctl restart beyond-belief-automation
echo "✅ Service restarted"
echo "📊 Service status:"
sudo systemctl status beyond-belief-automation --no-pager
EOF

# Create logs script
cat > view_logs.sh << 'EOF'
#!/bin/bash
echo "📋 Beyond Belief Automation Service Logs:"
echo "========================================="
echo "Press Ctrl+C to exit log viewing"
echo ""
sudo journalctl -u beyond-belief-automation -f
EOF

# Make scripts executable
chmod +x start_service.sh stop_service.sh check_service.sh restart_service.sh view_logs.sh

print_success "Management scripts created"

# Step 4: Configure power management
print_status "Step 4: Configuring power management..."

# Create power management configuration
sudo tee /etc/systemd/sleep.conf.d/99-beyond-belief.conf > /dev/null << EOF
[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowSuspendThenHibernate=no
AllowHybridSleep=no
EOF

print_success "Power management configured"

# Step 5: Create environment check script
print_status "Step 5: Creating environment check script..."

cat > check_environment.sh << 'EOF'
#!/bin/bash
echo "🔍 Beyond Belief Environment Check"
echo "=================================="

# Check Python
echo "🐍 Python version:"
python3 --version

# Check required packages
echo ""
echo "📦 Checking required packages..."
python3 -c "
import sys
packages = ['praw', 'meta_ai_api', 'schedule', 'requests', 'python-dotenv']
missing = []
for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f'✅ {pkg}')
    except ImportError:
        print(f'❌ {pkg} - MISSING')
        missing.append(pkg)

if missing:
    print(f'\n⚠️  Missing packages: {missing}')
    print('Run: pip install ' + ' '.join(missing))
    sys.exit(1)
else:
    print('\n✅ All required packages are installed')
"

# Check .env file
echo ""
echo "🔧 Checking configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    # Check for required variables (without showing values)
    required_vars=("REDDIT_CLIENT_ID" "REDDIT_CLIENT_SECRET" "FACEBOOK_PAGE_ACCESS_TOKEN")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            echo "✅ $var is set"
        else
            echo "❌ $var is missing"
        fi
    done
else
    echo "❌ .env file not found"
fi

# Check network connectivity
echo ""
echo "🌐 Checking network connectivity..."
if ping -c 1 google.com &> /dev/null; then
    echo "✅ Internet connection available"
else
    echo "❌ No internet connection"
fi

echo ""
echo "🎯 Environment check complete"
EOF

chmod +x check_environment.sh

print_success "Environment check script created"

# Step 6: Reload systemd and apply changes
print_status "Step 6: Applying system changes..."

# Reload systemd
sudo systemctl daemon-reload

# Restart logind to apply lid settings
sudo systemctl restart systemd-logind

print_success "System changes applied"

# Step 7: Create uninstall script
print_status "Step 7: Creating uninstall script..."

cat > uninstall_service.sh << 'EOF'
#!/bin/bash
echo "🗑️  Uninstalling Beyond Belief Background Service..."

# Stop and disable service
sudo systemctl stop beyond-belief-automation 2>/dev/null || true
sudo systemctl disable beyond-belief-automation 2>/dev/null || true

# Remove service file
sudo rm -f /etc/systemd/system/beyond-belief-automation.service

# Remove configuration files
sudo rm -f /etc/systemd/logind.conf.d/99-ignore-lid.conf
sudo rm -f /etc/systemd/sleep.conf.d/99-beyond-belief.conf

# Restore original logind.conf if backup exists
if [ -f /etc/systemd/logind.conf.backup ]; then
    sudo mv /etc/systemd/logind.conf.backup /etc/systemd/logind.conf
fi

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl restart systemd-logind

# Remove management scripts
rm -f start_service.sh stop_service.sh check_service.sh restart_service.sh view_logs.sh check_environment.sh

echo "✅ Beyond Belief Background Service uninstalled"
echo "ℹ️  You may need to reboot for all changes to take effect"
EOF

chmod +x uninstall_service.sh

print_success "Uninstall script created"

# Final summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Available commands:"
echo "  ./start_service.sh     - Start the background service"
echo "  ./stop_service.sh      - Stop the background service"
echo "  ./restart_service.sh   - Restart the background service"
echo "  ./check_service.sh     - Check service status and logs"
echo "  ./view_logs.sh         - View live service logs"
echo "  ./check_environment.sh - Check if environment is properly configured"
echo "  ./uninstall_service.sh - Remove the background service"
echo ""
echo "🔧 What was configured:"
echo "  ✅ Laptop lid close is now ignored (won't suspend)"
echo "  ✅ System sleep/hibernation disabled"
echo "  ✅ Systemd service created for background operation"
echo "  ✅ Auto-restart on failure configured"
echo "  ✅ Resource limits applied for stability"
echo ""
echo "🚀 Next steps:"
echo "  1. Run: ./check_environment.sh (to verify setup)"
echo "  2. Run: ./start_service.sh (to start the service)"
echo "  3. Close your laptop lid - the service will keep running!"
echo ""
echo "📊 Monitor with: ./check_service.sh or ./view_logs.sh"
echo ""
print_warning "Note: You may need to reboot for lid settings to take full effect"
