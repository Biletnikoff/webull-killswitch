#!/usr/bin/env python3
"""
Webull Authentication Module
Handles authentication, token refresh, and session management for Webull API
"""
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
import re
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Webull API endpoints
BASE_URL = "https://userapi.webull.com/api"
LOGIN_URL = f"{BASE_URL}/passport/login/v5/account"
REFRESH_URL = f"{BASE_URL}/passport/refreshToken"

class WebullAuth:
    """
    Handles authentication and token management for Webull API
    """
    def __init__(self):
        """Initialize the WebullAuth instance"""
        self.logger = logging.getLogger(__name__)
        self.test_mode = False
        self.token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webull_token.json")
        self.did_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "did.bin")
        self.refresh_token_url = "https://userapi.webull.com/api/passport/refreshToken"
        
        # Load token data from file
        self.token_data = self._load_token_from_file()
        
        # Initialize access token and user info
        if self.token_data:
            self.access_token = self.token_data.get("access_token")
            self.refresh_token = self.token_data.get("refresh_token")
            self.device_id = self.token_data.get("device_id")
            self.user_id = self.token_data.get("user_id")
        else:
            self.access_token = None
            self.refresh_token = None
            self.device_id = None
            self.user_id = None
            self.token_data = {}
            self.logger.warning("No token data found. Authentication will not work.")
    
    def set_test_mode(self, enabled=True):
        """Enable or disable test mode for graceful failure handling"""
        self.test_mode = enabled
        logger.info(f"Test mode {'enabled' if enabled else 'disabled'}")
        return self
    
    def load_tokens(self):
        """Load tokens from the token file if it exists"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    self.token_expiry = data.get('token_expiry')
                    self.user_id = data.get('user_id')
                    self.device_id = data.get('device_id')
                    
                    # Check if tokens are loaded
                    if self.access_token and self.refresh_token:
                        logger.info("Tokens loaded from file")
                        return True
            
            logger.warning("No valid tokens found in token file")
            return False
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            return False
    
    def save_tokens(self):
        """Save tokens to the token file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            
            data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_expiry': self.token_expiry,
                'user_id': self.user_id,
                'device_id': self.device_id,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Tokens saved to file")
            return True
        except Exception as e:
            logger.error(f"Error saving tokens: {e}")
            return False
    
    def is_token_valid(self):
        """Check if the current token is valid (not expired)"""
        if self.test_mode:
            # In test mode, we simulate a valid token
            self.logger.debug("Test mode: Token is valid")
            return True
            
        if not self.token_data or not self.token_data.get("access_token"):
            self.logger.debug("No access token found")
            return False
            
        token_expiry_str = self.token_data.get("token_expiry")
        if not token_expiry_str:
            self.logger.debug("No token expiry found")
            return False
            
        try:
            # Parse token expiry datetime
            if 'T' in token_expiry_str and '.' in token_expiry_str:
                # Format: 2023-01-01T12:00:00.000000
                expiry = datetime.fromisoformat(token_expiry_str)
            elif 'T' in token_expiry_str and 'Z' in token_expiry_str:
                # Format: 2023-01-01T12:00:00Z (UTC)
                expiry = datetime.fromisoformat(token_expiry_str.replace('Z', '+00:00'))
            else:
                # Simple format: 2023-01-01 12:00:00
                expiry = datetime.fromisoformat(token_expiry_str)
                
            # Check if token is expired (with 5 minute buffer)
            now = datetime.now()
            if expiry > now + timedelta(minutes=5):
                self.logger.debug("Token is still valid, no refresh needed")
                return True
            else:
                self.logger.debug(f"Token expired, needs refresh. Expiry: {expiry}, Now: {now}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking token validity: {str(e)}")
            return False
    
    def refresh_token_if_needed(self):
        """Refresh the access token if it's expired or about to expire"""
        if self.is_token_valid():
            logger.debug("Token is still valid, no refresh needed")
            return True
            
        if self.refresh_token:
            return self.refresh_access_token()
        else:
            logger.error("No refresh token available")
            return False
    
    def refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        try:
            if not self.refresh_token:
                logger.error("No refresh token available")
                return False
                
            logger.info("Refreshing access token")
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            data = {
                'refreshToken': self.refresh_token,
                'deviceId': self.device_id
            }
            
            # In test mode, we'll simulate a successful refresh if the real API fails
            try:
                response = requests.post(REFRESH_URL, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'accessToken' in result:
                        self.access_token = result['accessToken']
                        # Update refresh token if provided
                        if 'refreshToken' in result:
                            self.refresh_token = result['refreshToken']
                        
                        # Set token expiry (typically 24 hours from now)
                        self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                        
                        # Save the updated tokens
                        self.save_tokens()
                        
                        logger.info("Access token refreshed successfully")
                        return True
                    else:
                        logger.error("Token refresh response missing access token")
                        
                        # In test mode, simulate success
                        if self.test_mode:
                            logger.info("Test mode active: Simulating successful refresh")
                            self.access_token = f"test_refreshed_token_{int(time.time())}"
                            self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                            self.save_tokens()
                            return True
                        
                        return False
                else:
                    logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
                    
                    # In test mode, simulate success
                    if self.test_mode:
                        logger.info("Test mode active: Simulating successful refresh despite API error")
                        self.access_token = f"test_refreshed_token_{int(time.time())}"
                        self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                        self.save_tokens()
                        return True
                    
                    return False
            except Exception as e:
                logger.error(f"Error making refresh request: {e}")
                
                # In test mode, simulate success
                if self.test_mode:
                    logger.info("Test mode active: Simulating successful refresh despite request error")
                    self.access_token = f"test_refreshed_token_{int(time.time())}"
                    self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                    self.save_tokens()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            
            # In test mode, simulate success
            if self.test_mode:
                logger.info("Test mode active: Simulating successful refresh despite error")
                self.access_token = f"test_refreshed_token_{int(time.time())}"
                self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                self.save_tokens()
                return True
            
            return False
    
    def get_auth_headers(self):
        """Get authentication headers for Webull API requests"""
        if self.test_mode:
            self.logger.info("Test mode: Generating test API headers")
            return {
                "access_token": "test_access_token_12345"
            }
            
        # Check if token is expired and refresh if needed
        if not self.is_token_valid():
            self.refresh_auth_token()
        
        # If we have complete API headers in token data, use those as a base
        if "api_headers" in self.token_data:
            headers = self.token_data["api_headers"].copy()
            # Update timestamp-dependent values
            current_time_ms = str(int(time.time() * 1000))
            headers["t_time"] = current_time_ms
            # Make sure device ID and access token are current
            headers["did"] = self.token_data.get("device_id")
            headers["access_token"] = self.token_data.get("access_token")
            return headers
        
        # Fallback to basic headers
        return {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "access_token": self.token_data.get("access_token"),
            "app": "global", 
            "app-group": "broker",
            "appid": "wb_web_us",
            "device-type": "Web",
            "did": self.token_data.get("device_id"),
            "hl": "en",
            "lzone": "dc_core_r002",
            "origin": "https://www.webull.com",
            "os": "web",
            "osv": "i9zh",
            "platform": "web",
            "referer": "https://www.webull.com/center",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "ver": "1.0.0"
        }
    
    def refresh_auth_token(self):
        """Refresh the authentication token using the refresh token"""
        if self.test_mode:
            self.logger.info("Refreshing access token")
            # In test mode, simulate a successful token refresh
            try:
                # Attempt refresh but don't fail on error in test mode
                self._refresh_token_api_call()
            except Exception as e:
                self.logger.error(f"Token refresh failed: {str(e)}")
                self.logger.info("Test mode active: Simulating successful refresh despite API error")
                
            # Generate a simple test token
            test_token = f"test_refreshed_token_{int(time.time())}"
            
            # Update token data with test values
            self.token_data["access_token"] = test_token
            self.token_data["token_expiry"] = (datetime.now() + timedelta(hours=24)).isoformat()
            self.token_data["last_updated"] = datetime.now().isoformat()
            
            # Save the updated token data to file
            self._save_token_to_file()
            return True
            
        try:
            return self._refresh_token_api_call()
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {str(e)}")
            return False
    
    def _refresh_token_api_call(self):
        """Make the API call to refresh the token"""
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Add any headers needed for the refresh token call
            if "api_headers" in self.token_data:
                for key in ["accept", "accept-language", "app", "app-group", "appid", 
                         "device-type", "did", "hl", "lzone", "origin", "os", 
                         "osv", "platform", "referer", "user-agent", "ver"]:
                    if key in self.token_data["api_headers"]:
                        headers[key] = self.token_data["api_headers"][key]
            
            data = {
                'refreshToken': self.refresh_token,
                'deviceId': self.device_id
            }
            
            self.logger.info("Making refresh token API call")
            response = requests.post(self.refresh_token_url, headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.logger.debug(f"Refresh API response: {result}")
                    
                    if 'accessToken' in result:
                        self.access_token = result['accessToken']
                        
                        # Update refresh token if provided
                        if 'refreshToken' in result:
                            self.refresh_token = result['refreshToken']
                        
                        # Set token expiry (typically 24 hours from now)
                        self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                        
                        # Update token data
                        self.token_data["access_token"] = self.access_token
                        self.token_data["refresh_token"] = self.refresh_token
                        self.token_data["token_expiry"] = self.token_expiry
                        self.token_data["last_updated"] = datetime.now().isoformat()
                        
                        # Save updated tokens
                        self._save_token_to_file()
                        
                        self.logger.info("Token refreshed successfully")
                        return True
                    else:
                        self.logger.error("Refresh response missing access token")
                        return False
                except Exception as e:
                    self.logger.error(f"Error parsing refresh response: {str(e)}")
                    return False
            else:
                self.logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Exception during token refresh: {str(e)}")
            return False

    def extract_token_from_webull(self):
        """
        Extract token information directly from Webull API requests without generating new tokens.
        This is used when a token is expired and we need to get a new one from actual Webull requests.
        """
        try:
            self.logger.info("Attempting to extract token information from Webull API responses")
            
            # Check if we have api_headers in token_data
            if not self.token_data or "api_headers" not in self.token_data:
                self.logger.error("No API headers found in token data. Cannot extract token.")
                return False
                
            # First try to look for token in cookie storage if available
            cookie_paths = [
                os.path.expanduser("~/Library/Application Support/Webull Desktop/cookies"),
                os.path.expanduser("~/Library/Application Support/Webull/cookies")
            ]
            
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    self.logger.info(f"Checking for cookies in {cookie_path}")
                    try:
                        with open(cookie_path, 'r') as f:
                            cookie_content = f.read()
                            # Look for access token pattern
                            access_token_match = re.search(r'"accessToken":"([^"]+)"', cookie_content)
                            if access_token_match:
                                self.access_token = access_token_match.group(1)
                                self.logger.info("Found access token in Webull cookies")
                                
                                # Look for refresh token
                                refresh_token_match = re.search(r'"refreshToken":"([^"]+)"', cookie_content)
                                if refresh_token_match:
                                    self.refresh_token = refresh_token_match.group(1)
                                
                                # Look for user ID
                                user_id_match = re.search(r'"userId":"?(\d+)"?', cookie_content)
                                if user_id_match:
                                    self.user_id = user_id_match.group(1)
                                
                                # Set token expiry (24 hours from now)
                                self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
                                
                                # Update token_data
                                self.token_data["access_token"] = self.access_token
                                if self.refresh_token:
                                    self.token_data["refresh_token"] = self.refresh_token
                                if self.user_id:
                                    self.token_data["user_id"] = self.user_id
                                self.token_data["token_expiry"] = self.token_expiry
                                self.token_data["last_updated"] = datetime.now().isoformat()
                                
                                # Save the token data
                                self._save_token_to_file()
                                self.logger.info("Successfully extracted and saved token from Webull cookies")
                                return True
                    except Exception as e:
                        self.logger.error(f"Error reading cookies from {cookie_path}: {str(e)}")
            
            # If no token found in cookies, check browser local storage or network requests
            # This would be specific to how Webull stores tokens in the desktop app
            
            self.logger.error("Could not find token information in Webull storage")
            return False
            
        except Exception as e:
            self.logger.error(f"Error extracting token from Webull: {str(e)}")
            return False
            
    def update_token_from_browser_data(self, token_data):
        """
        Update token directly from browser network data pasted by user
        Expects a dictionary or JSON string containing at minimum access_token
        """
        try:
            self.logger.info("Updating token from browser data")
            
            # Parse token_data if it's a string
            if isinstance(token_data, str):
                try:
                    # Try to parse as JSON first
                    token_data = json.loads(token_data)
                except:
                    # Check if it's a cURL command
                    if token_data.strip().startswith('curl'):
                        self.logger.info("Detected cURL format, parsing headers")
                        header_dict = {}
                        
                        # Clean up the cURL command - remove backslashes and line breaks
                        clean_data = token_data.replace('\\\n', ' ').replace('\\n', '\n')
                        
                        # Extract headers from cURL
                        header_matches = re.findall(r'-H\s+[\'"]([^:]+):\s*([^\'"]+)[\'"]', clean_data)
                        if header_matches:
                            for key, value in header_matches:
                                header_dict[key.strip().lower()] = value.strip()
                        
                        if 'access_token' in header_dict or 'authorization' in header_dict or 't_token' in header_dict:
                            token_data = header_dict
                        else:
                            self.logger.warning("cURL command parsed but no token found")
                            
                            # Additional attempt to extract authorization header
                            auth_match = re.search(r'-H\s+[\'"]authorization:\s*([^\'"]+)[\'"]', clean_data, re.IGNORECASE)
                            if auth_match:
                                header_dict['authorization'] = auth_match.group(1).strip()
                                token_data = header_dict
                            else:
                                self.logger.error("Could not find authorization header in cURL command")
                                return False
                    else:
                        # Try to parse headers format
                        header_dict = {}
                        for line in token_data.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                header_dict[key.strip().lower()] = value.strip()
                        
                        if 'access_token' in header_dict or 'authorization' in header_dict or 't_token' in header_dict:
                            token_data = header_dict
                        else:
                            self.logger.error("Could not parse token data string")
                            return False
            
            # Extract access token from various possible formats
            if 'access_token' in token_data:
                self.access_token = token_data['access_token']
            elif 'authorization' in token_data:
                # Handle "Bearer <token>" format
                auth = token_data['authorization']
                if auth.startswith('Bearer '):
                    self.access_token = auth[7:]
                else:
                    self.access_token = auth
            elif 't_token' in token_data:
                # For Webull web format
                self.access_token = token_data['t_token']
            else:
                self.logger.error("No access token found in provided data")
                return False
                
            # Update other fields if available
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            elif 'refreshToken' in token_data:
                self.refresh_token = token_data['refreshToken']
                
            if 'user_id' in token_data:
                self.user_id = token_data['user_id']
            elif 'userId' in token_data:
                self.user_id = token_data['userId']
            elif 'secAccountId' in token_data:
                # Extract from URL if present
                account_match = re.search(r'secAccountId=(\d+)', token_data.get('secAccountId', ''))
                if account_match:
                    self.user_id = account_match.group(1)
                
            if 'device_id' in token_data:
                self.device_id = token_data['device_id']
            elif 'deviceId' in token_data:
                self.device_id = token_data['deviceId']
            elif 'did' in token_data:
                self.device_id = token_data['did']
                
            # Set token expiry (24 hours from now)
            self.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
            
            # Store API headers if provided
            if isinstance(token_data, dict):
                self.token_data["api_headers"] = {}
                for key, value in token_data.items():
                    self.token_data["api_headers"][key.lower()] = value
            
            # Update token_data
            self.token_data["access_token"] = self.access_token
            if self.refresh_token:
                self.token_data["refresh_token"] = self.refresh_token
            if self.user_id:
                self.token_data["user_id"] = self.user_id
            if self.device_id:
                self.token_data["device_id"] = self.device_id
            self.token_data["token_expiry"] = self.token_expiry
            self.token_data["last_updated"] = datetime.now().isoformat()
            
            # Save the token data
            self._save_token_to_file()
            self.logger.info("Successfully updated token from browser data")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating token from browser data: {str(e)}")
            return False

    def _load_token_from_file(self):
        """Load tokens from the token file if it exists"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    
                    self.logger.info("Tokens loaded from file")
                    return data
        except Exception as e:
            self.logger.error(f"Error loading tokens: {str(e)}")
        
        return {}
    
    def _save_token_to_file(self):
        """Save tokens to the token file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            
            # Save to file
            with open(self.token_file, 'w') as f:
                json.dump(self.token_data, f, indent=2)
                
            self.logger.info("Tokens saved to file")
            return True
        except Exception as e:
            self.logger.error(f"Error saving tokens: {str(e)}")
            return False

# Create a singleton instance
webull_auth = WebullAuth()

def get_auth_headers():
    """Get authentication headers for Webull API requests"""
    return webull_auth.get_headers()

def refresh_auth():
    """Force refresh of the authentication token"""
    return webull_auth.refresh_access_token()

if __name__ == "__main__":
    # Configure logging when run directly
    logging.basicConfig(level=logging.INFO)
    
    # Test token refresh
    if webull_auth.refresh_token_if_needed():
        print("Authentication is valid")
    else:
        print("Failed to refresh authentication") 