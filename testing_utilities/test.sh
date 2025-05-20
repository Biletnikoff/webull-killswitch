#!/bin/bash
# Simple test script

echo "===== Testing Environment ====="

# Check if .env file exists
if [ -f .env ]; then
    echo ".env file exists"
    echo "Contents (masking passwords):"
    grep -v "PASSWORD" .env | cat
    grep "PASSWORD" .env | sed 's/=.*/=********/' | cat
else
    echo ".env file does not exist"
fi

# Check if the killTradingApp.scpt exists
if [ -f killTradingApp.scpt ]; then
    echo "killTradingApp.scpt exists"
    ls -l killTradingApp.scpt
else
    echo "killTradingApp.scpt does not exist"
fi

# List all Python files
echo -e "\nPython files in current directory:"
ls -la *.py

# Check if Webull app is installed
if [ -d "/Applications/Webull.app" ]; then
    echo "Webull app is installed"
else
    echo "Webull app is not installed"
fi

# Check if Google Chrome is installed
if [ -d "/Applications/Google Chrome.app" ]; then
    echo "Google Chrome is installed"
else
    echo "Google Chrome is not installed"
fi

echo -e "\nEnvironment test completed" 