#!/usr/bin/env python3
"""
Test script for extracting token data from Webull
This script tests the extract_token_from_webull method in WebullAuth class
"""

import os
import sys
import logging
import argparse
from webull_auth import WebullAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("test_token_extract")

def setup_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(description='Test token extraction from Webull')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser

def main():
    """Main function to test token extraction"""
    # Parse command line arguments
    parser = setup_parser()
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("webull_auth").setLevel(logging.DEBUG)
    
    # Create WebullAuth instance
    auth = WebullAuth()
    
    # Print current token info
    logger.info("Current token information:")
    if auth.token_data:
        logger.info(f"Access Token: {auth.token_data.get('access_token', 'Not found')[:10]}... (truncated)")
        logger.info(f"Refresh Token: {auth.token_data.get('refresh_token', 'Not found')[:10]}... (truncated)")
        logger.info(f"Expiry: {auth.token_data.get('expiry', 'Not found')}")
        logger.info(f"Last Updated: {auth.token_data.get('last_updated', 'Not found')}")
        
        # Check if token is valid
        is_valid = auth.is_token_valid()
        logger.info(f"Token valid: {is_valid}")
    else:
        logger.warning("No token data found")
    
    # Test token extraction
    logger.info("\nAttempting to extract token from Webull...")
    result = auth.extract_token_from_webull()
    
    if result:
        logger.info("Successfully extracted token from Webull")
        logger.info("Updated token information:")
        logger.info(f"Access Token: {auth.token_data.get('access_token', 'Not found')[:10]}... (truncated)")
        logger.info(f"Refresh Token: {auth.token_data.get('refresh_token', 'Not found')[:10]}... (truncated)")
        logger.info(f"Expiry: {auth.token_data.get('expiry', 'Not found')}")
        logger.info(f"Last Updated: {auth.token_data.get('last_updated', 'Not found')}")
        
        # Check if token is valid after extraction
        is_valid = auth.is_token_valid()
        logger.info(f"Token valid after extraction: {is_valid}")
    else:
        logger.error("Failed to extract token from Webull")
    
    # Test fallback to refresh token
    if not result and auth.token_data and auth.token_data.get('refresh_token'):
        logger.info("\nAttempting to refresh token using refresh_auth_token...")
        refresh_result = auth.refresh_auth_token()
        
        if refresh_result:
            logger.info("Successfully refreshed token")
            logger.info("Updated token information after refresh:")
            logger.info(f"Access Token: {auth.token_data.get('access_token', 'Not found')[:10]}... (truncated)")
            logger.info(f"Refresh Token: {auth.token_data.get('refresh_token', 'Not found')[:10]}... (truncated)")
            logger.info(f"Expiry: {auth.token_data.get('expiry', 'Not found')}")
            logger.info(f"Last Updated: {auth.token_data.get('last_updated', 'Not found')}")
            
            # Check if token is valid after refresh
            is_valid = auth.is_token_valid()
            logger.info(f"Token valid after refresh: {is_valid}")
        else:
            logger.error("Failed to refresh token")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 