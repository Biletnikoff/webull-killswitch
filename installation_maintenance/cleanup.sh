#!/bin/bash
# Cleanup script for the Webull Kill Switch
# This script forcefully terminates all monitor and watchdog processes

# Safety delay to prevent impulsive usage
echo ""
echo "⚠️ ⚠️ ⚠️  CRITICAL WARNING  ⚠️ ⚠️ ⚠️"
echo ""
echo "This will PERMANENTLY TERMINATE all kill switch monitoring processes."
echo "Your Webull account will be COMPLETELY UNPROTECTED against losses."
echo ""
echo "THIS IS IRREVERSIBLE WITHOUT MANUAL RESTART."
echo ""
echo "Are you ABSOLUTELY CERTAIN you want to disable all trading protection? (yes/no)"
read -r confirm

if [[ "$confirm" != "yes" ]]; then
    echo "Cleanup cancelled. Your protection remains active."
    exit 0
fi

# Generate random confirmation code
CONFIRM_CODE=$(cat /dev/urandom | LC_ALL=C tr -dc 'A-Z0-9' | fold -w 6 | head -n 1)

echo ""
echo "To confirm this critical action, please type the following code: $CONFIRM_CODE"
read -r user_code

if [[ "$user_code" != "$CONFIRM_CODE" ]]; then
    echo "Code mismatch. Cleanup cancelled. Your protection remains active."
    exit 0
fi

echo ""
echo "Final warning: Cleanup will begin in 30 seconds."
echo "Press Ctrl+C to cancel and maintain trading protection."
for i in {30..1}; do
    echo -ne "DISABLING ALL PROTECTION in $i seconds...\r"
    sleep 1
done
echo -e "\nProceeding with cleanup..."

echo "Forcefully terminating all Webull Kill Switch processes..."

# Kill all monitor and watchdog processes with SIGKILL
pkill -9 -f "monitor_pnl"
pkill -9 -f "watchdog.py"
pkill -9 -f "simple_watchdog.py"
pkill -9 -f "production_watchdog.py"

# Verify that all processes are terminated
sleep 1
REMAINING=$(ps aux | grep -E "monitor_pnl|watchdog.py|simple_watchdog.py|production_watchdog.py" | grep -v grep | wc -l)

if [ $REMAINING -gt 0 ]; then
    echo "WARNING: $REMAINING processes still running. Trying once more..."
    pkill -9 -f "monitor_pnl"
    pkill -9 -f "watchdog.py"
    pkill -9 -f "simple_watchdog.py"
    pkill -9 -f "production_watchdog.py"
    sleep 1
    REMAINING=$(ps aux | grep -E "monitor_pnl|watchdog.py|simple_watchdog.py|production_watchdog.py" | grep -v grep | wc -l)
    
    if [ $REMAINING -gt 0 ]; then
        echo "ERROR: Unable to terminate all processes. Please restart your computer."
    else
        echo "All processes terminated successfully."
    fi
else
    echo "All processes terminated successfully."
fi

# Remove the watchdog.py file if it exists
if [ -f "watchdog.py" ]; then
    rm watchdog.py
    echo "Removed watchdog.py file."
fi

echo ""
echo "⚠️ ⚠️ ⚠️  CLEANUP COMPLETE  ⚠️ ⚠️ ⚠️"
echo ""
echo "CRITICAL: Your Webull account is now COMPLETELY UNPROTECTED."
echo "No automatic protection against losses is active."
echo ""
echo "To restore protection, run: python3 production_watchdog.py" 