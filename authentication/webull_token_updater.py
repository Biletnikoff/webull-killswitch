#!/usr/bin/env python3
"""
Webull Token Updater - Semi-automated token extraction
"""
import os
import sys
import json
import webbrowser
import logging
import time
from datetime import datetime, timedelta
import subprocess
import tempfile

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import WebullAuth
from authentication.webull_auth import WebullAuth

def print_instructions():
    """Print detailed instructions for token extraction"""
    print("\n" + "="*80)
    print("WEBULL TOKEN UPDATER".center(80))
    print("="*80)
    print("\nThis tool will open Webull in your browser and help you extract your authentication token.")
    print("\nInstructions:")
    print("1. A browser window will open to Webull's login page")
    print("2. Login with your Webull credentials")
    print("3. Press Enter when you've logged in successfully")
    print("4. Follow the instructions to capture network requests and extract the token")
    
    print("\nDetailed Steps for Chrome:")
    print("  a. After logging in, press F12 or right-click and select 'Inspect'")
    print("  b. Go to the Network tab in Developer Tools")
    print("  c. Refresh the page (F5) or click on any section in Webull")
    print("  d. In the Network tab, look for requests to webull.com APIs")
    print("  e. Click on a request and look for headers containing 'access_token' or 'authorization'")
    print("  f. Right-click the request and select 'Copy' > 'Copy as cURL (bash)'")
    print("  g. Paste the cURL command when prompted")
    
    print("\nDetailed Steps for Safari:")
    print("  a. First enable the Develop menu: Safari > Preferences > Advanced > Show Develop menu in menu bar")
    print("  b. After logging in, click Develop > Show Web Inspector")
    print("  c. Go to the Network tab")
    print("  d. Refresh the page or click on any section in Webull")
    print("  e. Find a request to webull.com and view its headers")
    print("  f. Look for headers containing 'access_token' or 'authorization'")
    print("  g. Copy these headers to paste when prompted")
    
    print("\nCAPTCHA Handling:")
    print("  • Webull may show a CAPTCHA or verification challenge during login")
    print("  • Complete it as requested - this script will wait")
    
    print("\n" + "="*80)

def capture_curl_command():
    """Get cURL command from user"""
    print("\nPlease paste the cURL command or headers containing your token:")
    print("(End with a single line containing just 'END' or press Ctrl+D)")
    print("\n> ", end="")
    
    curl_command = []
    try:
        while True:
            line = input()
            if line.strip().lower() == "end":
                break
            curl_command.append(line)
    except EOFError:
        pass
    
    return "\n".join(curl_command)

def create_browser_helper_script():
    """Create a temporary HTML file with helper tools for token extraction"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Webull Token Extractor Helper</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }
            h2 {
                color: #3498db;
                margin-top: 20px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px 0;
            }
            button:hover {
                background-color: #45a049;
            }
            code {
                background: #f4f4f4;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 2px 5px;
                font-family: monospace;
            }
            pre {
                background: #f4f4f4;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                overflow: auto;
                font-family: monospace;
            }
            textarea {
                width: 100%;
                height: 150px;
                margin: 10px 0;
                padding: 10px;
                box-sizing: border-box;
            }
            .success {
                color: #4CAF50;
                font-weight: bold;
            }
            .error {
                color: #f44336;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Webull Token Extractor Helper</h1>
            
            <div id="instructions">
                <h2>Instructions</h2>
                <ol>
                    <li>Open the Webull website in another tab: <a href="https://app.webull.com/trade" target="_blank">Webull Trading</a></li>
                    <li>Log in to your Webull account</li>
                    <li>Once logged in, open Developer Tools (F12 or right-click > Inspect)</li>
                    <li>Go to the Network tab</li>
                    <li>Refresh the page or click around on the Webull interface</li>
                    <li>Find a request to a Webull API (contains "webull" or "api" in the URL)</li>
                    <li>Select the request and look for headers with tokens</li>
                    <li>Use the buttons below to help extract tokens</li>
                </ol>
            </div>

            <div id="token-extraction">
                <h2>Token Extraction Tools</h2>
                
                <h3>Step 1: Copy Network Request</h3>
                <p>Right-click on a Webull API request and select "Copy as cURL"</p>
                <textarea id="curl-input" placeholder="Paste cURL command here..."></textarea>
                <button onclick="parseCurl()">Parse cURL Command</button>
                
                <h3>Step 2: Extract Token from Headers</h3>
                <p>Alternatively, you can directly paste request headers:</p>
                <textarea id="headers-input" placeholder="Paste request headers here..."></textarea>
                <button onclick="parseHeaders()">Parse Headers</button>
                
                <h3>Results:</h3>
                <pre id="token-output">No tokens extracted yet...</pre>
                
                <div id="token-data" style="display:none">
                    <h3>Token Data for Python Script:</h3>
                    <pre id="token-data-json"></pre>
                    <button onclick="copyTokenData()">Copy Token Data</button>
                    <span id="copy-status"></span>
                </div>
            </div>
        </div>
        
        <script>
            // Token extraction functions
            function parseCurl() {
                const curlCommand = document.getElementById('curl-input').value;
                if (!curlCommand) {
                    alert('Please paste a cURL command first');
                    return;
                }
                
                // Extract headers from cURL
                const headerRegex = /-H ['"]([^:]+):\s*([^'"]+)['"]/g;
                const headers = {};
                let match;
                
                while ((match = headerRegex.exec(curlCommand)) !== null) {
                    const headerName = match[1].toLowerCase();
                    const headerValue = match[2];
                    headers[headerName] = headerValue;
                }
                
                processHeaders(headers);
            }
            
            function parseHeaders() {
                const headersText = document.getElementById('headers-input').value;
                if (!headersText) {
                    alert('Please paste headers first');
                    return;
                }
                
                const headers = {};
                const lines = headersText.split('\\n');
                
                for (const line of lines) {
                    if (line.includes(':')) {
                        const parts = line.split(':');
                        const headerName = parts[0].trim().toLowerCase();
                        const headerValue = parts.slice(1).join(':').trim();
                        headers[headerName] = headerValue;
                    }
                }
                
                processHeaders(headers);
            }
            
            function processHeaders(headers) {
                const output = document.getElementById('token-output');
                const tokenData = {};
                
                // Check for access token in different formats
                if (headers['access_token']) {
                    tokenData.access_token = headers['access_token'];
                } else if (headers['authorization']) {
                    const auth = headers['authorization'];
                    if (auth.startsWith('Bearer ')) {
                        tokenData.access_token = auth.substring(7);
                    } else {
                        tokenData.access_token = auth;
                    }
                } else if (headers['t_token']) {
                    tokenData.access_token = headers['t_token'];
                }
                
                // Check for refresh token
                if (headers['refresh_token']) {
                    tokenData.refresh_token = headers['refresh_token'];
                } else if (headers['refreshtoken']) {
                    tokenData.refresh_token = headers['refreshtoken'];
                }
                
                // Check for device ID
                if (headers['did']) {
                    tokenData.device_id = headers['did'];
                } else if (headers['deviceid']) {
                    tokenData.device_id = headers['deviceid'];
                }
                
                // Check for user ID
                if (headers['user_id']) {
                    tokenData.user_id = headers['user_id'];
                } else if (headers['userid']) {
                    tokenData.user_id = headers['userid'];
                }
                
                // Display results
                if (tokenData.access_token) {
                    output.innerHTML = '<span class="success">Tokens found!</span>\\n';
                    
                    if (tokenData.access_token) {
                        const shortToken = tokenData.access_token.substring(0, 10) + '...';
                        output.innerHTML += `Access Token: ${shortToken}\\n`;
                    }
                    
                    if (tokenData.refresh_token) {
                        const shortRefresh = tokenData.refresh_token.substring(0, 10) + '...';
                        output.innerHTML += `Refresh Token: ${shortRefresh}\\n`;
                    }
                    
                    if (tokenData.device_id) {
                        output.innerHTML += `Device ID: ${tokenData.device_id}\\n`;
                    }
                    
                    if (tokenData.user_id) {
                        output.innerHTML += `User ID: ${tokenData.user_id}\\n`;
                    }
                    
                    // Show token data
                    document.getElementById('token-data').style.display = 'block';
                    document.getElementById('token-data-json').textContent = JSON.stringify(tokenData, null, 2);
                } else {
                    output.innerHTML = '<span class="error">No tokens found in the provided data.</span>\\n';
                    output.innerHTML += 'Please try another request with proper authentication headers.';
                }
            }
            
            function copyTokenData() {
                const tokenData = document.getElementById('token-data-json').textContent;
                navigator.clipboard.writeText(tokenData).then(() => {
                    const status = document.getElementById('copy-status');
                    status.textContent = '✓ Copied!';
                    status.className = 'success';
                    setTimeout(() => {
                        status.textContent = '';
                    }, 2000);
                });
            }
        </script>
    </body>
    </html>
    """
    
    # Create a temporary HTML file
    fd, path = tempfile.mkstemp(suffix='.html', prefix='webull_token_helper_')
    with os.fdopen(fd, 'w') as f:
        f.write(html_content)
    
    return path

def main():
    """Main function for token update"""
    # Print instructions
    print_instructions()
    
    # Check if Webull is already running or installed
    auth = WebullAuth()
    
    # First try to extract token from desktop app if installed
    if auth.extract_token_from_webull():
        print("\n✅ Successfully extracted token from Webull desktop app!")
        print(f"Access Token: {auth.access_token[:10]}..." if auth.access_token else "Access Token: None")
        print(f"Token saved to: {auth.token_file}")
        return 0
    
    # Create helper browser page
    helper_page = create_browser_helper_script()
    
    # Open Webull login page and the helper page in browser
    print("\nOpening Webull and token helper in your browser...")
    webull_url = "https://app.webull.com/trade"
    
    # Open the helper page first
    webbrowser.open(f"file://{helper_page}")
    time.sleep(1)
    
    # Open Webull login page
    webbrowser.open(webull_url)
    
    # Wait for user to login
    input("\nPress Enter after you've logged in to Webull...\n")
    
    # Get token from user
    curl_data = capture_curl_command()
    
    if not curl_data:
        print("\n❌ No data provided. Exiting.")
        # Clean up temp file
        os.unlink(helper_page)
        return 1
        
    # Update token
    success = auth.update_token_from_browser_data(curl_data)
    
    # Clean up temp file
    try:
        os.unlink(helper_page)
    except:
        pass
    
    if success:
        print("\n✅ Token updated successfully!")
        print(f"Access Token: {auth.access_token[:10]}..." if auth.access_token else "Access Token: None")
        print(f"Refresh Token: {auth.refresh_token[:10]}..." if auth.refresh_token else "Refresh Token: None")
        print(f"User ID: {auth.user_id}" if auth.user_id else "User ID: None")
        print(f"Device ID: {auth.device_id}" if auth.device_id else "Device ID: None")
        print(f"Token saved to: {auth.token_file}")
        print(f"Token will expire in approximately 24 hours.")
        
        # Set up a scheduled task to remind about token renewal
        try:
            # On macOS, use launchd
            if sys.platform == 'darwin':
                print("\nWould you like to set up a daily reminder to refresh your token? (y/n)")
                setup_reminder = input("> ").strip().lower()
                
                if setup_reminder == 'y':
                    # Create a reminder script
                    reminder_script = os.path.join(parent_dir, "token_reminder.sh")
                    with open(reminder_script, 'w') as f:
                        f.write(f"""#!/bin/bash
osascript -e 'display notification "Your Webull token will expire soon. Please run token updater." with title "Webull Token Reminder"'
""")
                    os.chmod(reminder_script, 0o755)
                    
                    # Use launchctl to schedule a daily reminder
                    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.webull.token.reminder.plist")
                    with open(plist_path, 'w') as f:
                        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.webull.token.reminder</string>
    <key>ProgramArguments</key>
    <array>
        <string>{reminder_script}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>""")
                    
                    # Load the plist
                    subprocess.run(["launchctl", "load", plist_path])
                    print(f"✅ Daily reminder set for 9:00 AM")
        except Exception as e:
            logger.error(f"Failed to set up reminder: {e}")
        
        return 0
    else:
        print("\n❌ Failed to update token.")
        print("Please check the data you provided and try again.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\n❌ An error occurred: {str(e)}")
        sys.exit(1) 