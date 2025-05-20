#!/bin/bash
# Webull Kill Switch Uninstallation Script
# This script stops all processes and removes the launch agent

echo "=========================================================="
echo "          WEBULL KILL SWITCH UNINSTALLATION SCRIPT        "
echo "=========================================================="

# Stop all running processes first
echo "Stopping all running kill switch processes..."
"$HOME/webull-killswitch/cleanup.sh"

# Unload launch agent if it exists
LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.user.webull.killswitch.plist"
if [ -f "$LAUNCH_AGENT" ]; then
    echo "Unloading launch agent..."
    launchctl unload "$LAUNCH_AGENT" 2>/dev/null
    echo "✅ Launch agent unloaded"
    
    echo "Removing launch agent file..."
    rm "$LAUNCH_AGENT"
    echo "✅ Launch agent file removed"
else
    echo "⚠️ Launch agent not found, nothing to unload"
fi

echo -e "\n"
echo "✅ Webull Kill Switch has been uninstalled!"
echo "📝 Log files have been preserved in the logs directory"
echo "📁 Script files remain in the webull-killswitch directory"
echo -e "\n"
echo "To completely remove all files, you can manually delete:"
echo "  rm -rf $HOME/webull-killswitch"
echo -e "\n" 