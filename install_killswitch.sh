#!/bin/bash
# Webull Kill Switch Installation Script
# This script sets up the Webull Kill Switch system for automatic startup

echo "=========================================================="
echo "          WEBULL KILL SWITCH INSTALLATION SCRIPT          "
echo "=========================================================="

# Create log directory if it doesn't exist
mkdir -p "$HOME/webull-killswitch/logs"
echo "✅ Created logs directory"

# Make scripts executable
chmod +x "$HOME/webull-killswitch/cleanup.sh"
chmod +x "$HOME/webull-killswitch/monitor_pnl_hardened.py"
chmod +x "$HOME/webull-killswitch/respawn_monitor.py"
chmod +x "$HOME/webull-killswitch/check_status.py"
echo "✅ Made scripts executable"

# Create launch agent directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create launch agent plist file
cat > "$HOME/Library/LaunchAgents/com.user.webull.killswitch.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.webull.killswitch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>respawn_monitor.py</string>
        <string>--threshold=-500</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$HOME/webull-killswitch</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/webull-killswitch/logs/launchd_out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/webull-killswitch/logs/launchd_err.log</string>
</dict>
</plist>
EOF
echo "✅ Created launch agent plist"

# Set correct permissions
chmod 644 "$HOME/Library/LaunchAgents/com.user.webull.killswitch.plist"
echo "✅ Set launch agent permissions"

# Clean up any existing processes
echo "Cleaning up any existing kill switch processes..."
"$HOME/webull-killswitch/cleanup.sh"

# Load the launch agent
launchctl load "$HOME/Library/LaunchAgents/com.user.webull.killswitch.plist"
echo "✅ Loaded launch agent"

echo -e "\n"
echo "✅ Webull Kill Switch installation complete!"
echo "🚀 The kill switch will now start automatically when you log in"
echo "🔍 Use 'python3 check_status.py' to verify the system status"
echo "💰 Default P/L threshold is set to -$500"
echo -e "\n"

# Run the status check
echo "Running status check..."
python3 "$HOME/webull-killswitch/check_status.py" 