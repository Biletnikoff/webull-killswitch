#!/bin/bash
# Clean test script for Webull Kill Switch

echo "Stopping any running monitor processes..."
pkill -f "monitor_pnl_hardened.py" || true
sleep 1

# Make sure processes are really gone
if pgrep -f "monitor_pnl_hardened.py" > /dev/null; then
    echo "Forcing termination of monitor processes..."
    pkill -9 -f "monitor_pnl_hardened.py"
    sleep 1
fi

echo "Stopping any watchdog processes..."
pkill -f "watchdog.py" || true
sleep 1

# Remove existing log file to start fresh
echo "Cleaning logs..."
rm -f logs/monitor_hardened.log

echo "Starting monitor in test mode with 5 second interval..."
echo "Press Ctrl+C to stop the test (may require multiple attempts due to signal handling)"
echo

# Run with test mode and verbose output
python3 monitor_pnl_hardened.py --test --interval 5 --verbose 