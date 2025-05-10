#!/bin/bash
# Cleanup script for the Webull Kill Switch
# This script forcefully terminates all monitor and watchdog processes

# Safety delay to prevent impulsive usage
echo "WARNING: This will terminate all kill switch monitoring processes."
echo "Your Webull account will no longer be protected by the automatic kill switch."
echo ""
echo "Are you sure you want to proceed? (y/n)"
read -r confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo "Cleanup will begin in 10 seconds. Press Ctrl+C to cancel."
for i in {10..1}; do
    echo -ne "Starting cleanup in $i seconds...\r"
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

echo "Cleanup complete."
echo "REMINDER: Your Webull account is NO LONGER protected by the kill switch."
echo "To restart protection, run: python3 production_watchdog.py" 