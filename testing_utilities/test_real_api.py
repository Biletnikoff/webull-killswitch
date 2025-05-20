#!/usr/bin/env python3
"""
Test script to check the Webull API with a real token
"""
import json
import requests
import os
import time
import sys

def main():
    # Add parent directory to path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Load token from file in project root
    token_file = os.path.join(parent_dir, "webull_token.json")
    
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    print(f"Using token data:")
    print(f"Access Token: {token_data['access_token'][:10]}...")
    print(f"Device ID: {token_data['device_id']}")
    print(f"User ID: {token_data['user_id']}")
    
    # Set up headers for the API request
    if "api_headers" in token_data:
        # Use the exact headers from the token file
        headers = token_data["api_headers"].copy()
        # Update timestamp-dependent values
        current_time_ms = str(int(time.time() * 1000))
        headers["t_time"] = current_time_ms
        print(f"Using complete API headers from the token file")
    else:
        # Fallback to basic headers
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "access_token": token_data["access_token"],
            "app": "global",
            "app-group": "broker",
            "appid": "wb_web_us",
            "device-type": "Web",
            "did": token_data["device_id"],
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
        print(f"Using basic headers (no complete API headers found in token file)")
    
    # Try to get account summary data
    url = f"https://ustrade.webullfinance.com/api/trading/v1/webull/asset/future/summary"
    params = {"secAccountId": token_data["user_id"]}
    
    print(f"\nAttempting to connect to Webull API...")
    print(f"URL: {url}")
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            try:
                # Parse JSON and pretty print it
                data = response.json()
                print(f"Response (prettified):")
                print(json.dumps(data, indent=2))
                
                # Check for specific fields (if they exist)
                if "capital" in data:
                    print("\nCapital data:")
                    for key, value in data["capital"].items():
                        print(f"  {key}: {value}")
            except Exception as e:
                print(f"Error parsing JSON: {str(e)}")
                print(f"Raw response:")
                print(response.text)
        else:
            print(f"Error Response:")
            print(response.text)
    except Exception as e:
        print(f"Error: {str(e)}")
        
    # Try the token refresh endpoint
    print("\nTesting token refresh...")
    refresh_url = "https://userapi.webull.com/api/passport/refreshToken"
    refresh_data = {
        "refreshToken": token_data["refresh_token"],
        "deviceId": token_data["device_id"]
    }
    
    # Update headers for refresh request
    if "api_headers" in token_data:
        refresh_headers = {k: v for k, v in headers.items() if k in [
            "accept", "accept-language", "app", "app-group", "appid", 
            "device-type", "did", "hl", "lzone", "origin", "os", 
            "osv", "platform", "referer", "user-agent", "ver"
        ]}
    else:
        refresh_headers = headers
    
    try:
        refresh_response = requests.post(refresh_url, json=refresh_data, headers=refresh_headers)
        print(f"Refresh status code: {refresh_response.status_code}")
        print(f"Refresh response:")
        print(refresh_response.text[:500] + "..." if len(refresh_response.text) > 500 else refresh_response.text)
    except Exception as e:
        print(f"Refresh error: {str(e)}")

if __name__ == "__main__":
    main() 