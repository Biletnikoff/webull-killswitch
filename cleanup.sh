#!/bin/bash
# Cleanup script for the Webull Kill Switch
# This script forcefully terminates all monitor and watchdog processes

echo "Forcefully terminating all Webull Kill Switch processes..."

# Kill all monitor and watchdog processes with SIGKILL
pkill -9 -f "monitor_pnl"
pkill -9 -f "watchdog.py"

# Verify that all processes are terminated
sleep 1
REMAINING=$(ps aux | grep -E "monitor_pnl|watchdog.py" | grep -v grep | wc -l)

if [ $REMAINING -gt 0 ]; then
    echo "WARNING: $REMAINING processes still running. Trying once more..."
    pkill -9 -f "monitor_pnl"
    pkill -9 -f "watchdog.py"
    sleep 1
    REMAINING=$(ps aux | grep -E "monitor_pnl|watchdog.py" | grep -v grep | wc -l)
    
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