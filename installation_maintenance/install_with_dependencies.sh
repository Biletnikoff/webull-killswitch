#!/bin/bash
# Webull Kill Switch Comprehensive Installer
# This script installs all dependencies and sets up the Webull Kill Switch service

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}${BOLD}===== Webull Kill Switch Installation =====${NC}"
echo -e "${BLUE}This script will install the Webull Kill Switch with all dependencies${NC}"
echo

# Check if Python 3 is installed
echo -e "${BLUE}${BOLD}Checking for Python 3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo -e "Please install Python 3 before continuing."
    exit 1
fi
echo -e "${GREEN}Python 3 is installed: $(python3 --version)${NC}"

# Check if pip is installed
echo -e "${BLUE}${BOLD}Checking for pip...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip is not installed.${NC}"
    echo -e "Please install pip before continuing."
    exit 1
fi
echo -e "${GREEN}pip is installed: $(pip3 --version)${NC}"

# Check if Homebrew is installed
echo -e "${BLUE}${BOLD}Checking for Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Warning: Homebrew is not installed.${NC}"
    echo -e "Would you like to install Homebrew? (y/n): "
    read -r install_brew
    if [[ $install_brew == "y" || $install_brew == "Y" ]]; then
        echo -e "${BLUE}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install Homebrew. Please install it manually.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Homebrew is required to install terminal-notifier.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Homebrew is installed.${NC}"

# Install terminal-notifier
echo -e "${BLUE}${BOLD}Installing terminal-notifier...${NC}"
if ! command -v terminal-notifier &> /dev/null; then
    brew install terminal-notifier
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install terminal-notifier. Please install it manually:${NC}"
        echo -e "brew install terminal-notifier"
        exit 1
    fi
    echo -e "${GREEN}terminal-notifier installed successfully.${NC}"
else
    echo -e "${GREEN}terminal-notifier is already installed.${NC}"
fi

# Install Python dependencies
echo -e "${BLUE}${BOLD}Installing Python dependencies...${NC}"
pip3 install -r "$SCRIPT_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install Python dependencies.${NC}"
    exit 1
fi
echo -e "${GREEN}Python dependencies installed successfully.${NC}"

# Create logs directory
echo -e "${BLUE}${BOLD}Creating logs directory...${NC}"
mkdir -p "$SCRIPT_DIR/logs"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create logs directory.${NC}"
    exit 1
fi

# Update the plist file with the correct path
echo -e "${BLUE}${BOLD}Configuring launch agent...${NC}"
sed -i '' "s|/Users/bo/webull-killswitch|$SCRIPT_DIR|g" "$SCRIPT_DIR/com.webull.killswitch.plist"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to update paths in the plist file.${NC}"
    exit 1
fi

# Copy the plist to LaunchAgents
echo -e "${BLUE}${BOLD}Installing launch agent...${NC}"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"
cp "$SCRIPT_DIR/com.webull.killswitch.plist" "$LAUNCH_AGENTS_DIR/"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to copy plist to LaunchAgents directory.${NC}"
    exit 1
fi

# Set permissions
chmod 644 "$LAUNCH_AGENTS_DIR/com.webull.killswitch.plist"

# Configure the hardened monitor script permissions
echo -e "${BLUE}${BOLD}Setting up monitor script...${NC}"
chmod +x "$SCRIPT_DIR/monitor_pnl_hardened.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to set executable permissions on monitor script.${NC}"
    exit 1
fi

# Ask user if they want to modify the P/L threshold
echo
echo -e "${BLUE}${BOLD}P/L Threshold Configuration${NC}"
echo -e "${BLUE}The current P/L threshold is set to -$500.00${NC}"
echo -e "${BLUE}Would you like to change this threshold? (y/n):${NC} "
read -r change_threshold
if [[ $change_threshold == "y" || $change_threshold == "Y" ]]; then
    echo -e "${BLUE}Enter new P/L threshold (negative number, e.g., -500):${NC} "
    read -r new_threshold
    
    # Validate that it's a negative number
    if [[ $new_threshold =~ ^-[0-9]+(\.[0-9]+)?$ ]]; then
        # Update the threshold in the hardened monitor script
        sed -i '' "s/PNL_THRESHOLD = -500.0/PNL_THRESHOLD = $new_threshold/" "$SCRIPT_DIR/monitor_pnl_hardened.py"
        echo -e "${GREEN}P/L threshold updated to $new_threshold${NC}"
    else
        echo -e "${RED}Invalid threshold. Must be a negative number.${NC}"
        echo -e "${YELLOW}Keeping default threshold of -500.00${NC}"
    fi
fi

# Load the launch agent
echo -e "${BLUE}${BOLD}Starting the kill switch service...${NC}"
launchctl unload -w "$LAUNCH_AGENTS_DIR/com.webull.killswitch.plist" 2>/dev/null
launchctl load -w "$LAUNCH_AGENTS_DIR/com.webull.killswitch.plist"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to load the launch agent.${NC}"
    exit 1
fi

# Verify it's running
sleep 2
if pgrep -f "python3.*monitor_pnl_hardened.py" > /dev/null; then
    echo -e "${GREEN}${BOLD}✅ Webull Kill Switch is now running in the background!${NC}"
    echo -e "${GREEN}It will start automatically on login and restart if terminated.${NC}"
    echo -e "${GREEN}The monitor will only run during market hours (6:30am-1:15pm PST, Mon-Fri).${NC}"
    echo
    echo -e "${BLUE}Logs are available at:${NC}"
    echo -e "  ${BOLD}$SCRIPT_DIR/logs/monitor_hardened.log${NC}"
    echo -e "  ${BOLD}$SCRIPT_DIR/logs/killswitch_out.log${NC}"
    echo -e "  ${BOLD}$SCRIPT_DIR/logs/killswitch_err.log${NC}"
else
    echo -e "${YELLOW}Warning: Kill switch service doesn't appear to be running.${NC}"
    echo -e "Check the logs for more information."
fi

echo -e "\n${BLUE}${BOLD}To uninstall the service, run:${NC}"
echo -e "./uninstall_killswitch.sh"
echo

# Make all scripts executable
chmod +x "$SCRIPT_DIR/install_killswitch.sh"
chmod +x "$SCRIPT_DIR/uninstall_killswitch.sh"
chmod +x "$SCRIPT_DIR/install_with_dependencies.sh" 