"""
Module for handling Twitch API authentication using twitchAPI package
"""
import os
import asyncio
from typing import Optional, Tuple

from twitchAPI.twitch import Twitch
from modules.utils.logger import print_header, print_error, print_success

class TwitchAuthenticator:
    def __init__(self, client_id: str, client_secret: str):
        """Initialize TwitchAuthenticator
        
        Args:
            client_id: Twitch Client ID
            client_secret: Twitch Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.twitch: Optional[Twitch] = None
        
    async def authenticate(self) -> Tuple[Optional[str], Optional[Twitch]]:
        """Authenticate with Twitch API
        
        Returns:
            Tuple containing:
            - Access token string if successful, None if failed
            - Authenticated Twitch instance if successful, None if failed
        """
        try:
            print_header("Authenticating with Twitch...")
            self.twitch = await Twitch(self.client_id, self.client_secret)
            token = self.twitch.get_app_token()
            print_success("Successfully authenticated with Twitch!")
            return token, self.twitch
            
        except Exception as e:
            print_error(f"Failed to authenticate with Twitch: {str(e)}")
            return None, None

def get_token(client_id: str, client_secret: str) -> Optional[str]:
    """Get a valid Twitch access token
    
    This is a synchronous wrapper around the async authenticate method
    to maintain compatibility with existing code.
    
    Args:
        client_id: Twitch Client ID
        client_secret: Twitch Client Secret
        
    Returns:
        Access token string if successful, None if failed
    """
    authenticator = TwitchAuthenticator(client_id, client_secret)
    
    try:
        # Run async authenticate in an event loop
        token, twitch = asyncio.run(authenticator.authenticate())
        if token and twitch:
            # We got a valid token and Twitch instance
            return token
            
    except Exception as e:
        print_error(f"Error during authentication: {str(e)}")
        
    return None