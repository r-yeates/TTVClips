import json
from typing import Dict, List, Optional, Any
import os
from datetime import datetime, timedelta
from modules.logger import print_error, print_header, print_success

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors"""
    pass

class ConfigValidator:
    REQUIRED_SECTIONS = ['default', 'blacklist']
    REQUIRED_DEFAULT_KEYS = [
        'CLIENT_ID',
        'CLIENT_SECRET',
        'CLIPS_AMOUNT',
        'PERIOD',
        'GAME_ID',
        'BROADCASTER_ID',
        'UPLOAD_TO_YOUTUBE',
        'UPLOAD_TO_TIKTOK'
    ]

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Validate the configuration file.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            if not os.path.exists(self.config_path):
                raise ConfigValidationError(f"Configuration file not found: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Check required sections
            for section in self.REQUIRED_SECTIONS:
                if section not in self.config:
                    self.errors.append(f"Missing required section: {section}")

            # Check required keys in default section
            default_section = self.config.get('default', {})
            for key in self.REQUIRED_DEFAULT_KEYS:
                if key not in default_section:
                    self.errors.append(f"Missing required key in default section: {key}")

            # Validate specific values
            self._validate_numeric('CLIPS_AMOUNT', min_value=1, max_value=100)
            self._validate_numeric('PERIOD', min_value=1, max_value=365)
            self._validate_numeric('GAME_ID', min_value=1)
            self._validate_numeric('BROADCASTER_ID', min_value=1)
            self._validate_boolean('UPLOAD_TO_YOUTUBE')
            self._validate_boolean('UPLOAD_TO_TIKTOK')

            # Validate dependent configurations
            self._validate_upload_configs()

            if self.errors:
                print_error("Configuration validation failed:")
                for error in self.errors:
                    print_error(f"- {error}")
                return False

            if self.warnings:
                print_header("Configuration warnings:")
                for warning in self.warnings:
                    print_header(f"- {warning}")

            print_success("Configuration validation successful")
            return True

        except Exception as e:
            print_error(f"Error validating configuration: {e}")
            return False

    def _validate_numeric(self, key: str, min_value: Optional[int] = None, max_value: Optional[int] = None):
        """Validate numeric configuration values"""
        try:
            default_section = self.config.get('default', {})
            value = default_section.get(key)
            
            if not isinstance(value, int):
                self.errors.append(f"{key} must be a valid number")
                return
                
            if min_value is not None and value < min_value:
                self.errors.append(f"{key} must be at least {min_value}")
            if max_value is not None and value > max_value:
                self.errors.append(f"{key} must be at most {max_value}")
        except Exception:
            self.errors.append(f"{key} must be a valid number")

    def _validate_boolean(self, key: str):
        """Validate boolean configuration values"""
        try:
            default_section = self.config.get('default', {})
            value = default_section.get(key)
            
            if not isinstance(value, bool):
                self.errors.append(f"{key} must be a boolean value (true/false)")
        except Exception:
            self.errors.append(f"{key} must be a boolean value (true/false)")

    def _validate_upload_configs(self):
        """Validate upload-related configurations"""
        default_section = self.config.get('default', {})
        upload_to_youtube = default_section.get('UPLOAD_TO_YOUTUBE', False)
        upload_to_tiktok = default_section.get('UPLOAD_TO_TIKTOK', False)

        if upload_to_youtube:
            youtube_cookies = os.path.join(os.path.dirname(self.config_path), 'yt_cookies.txt')
            if not os.path.exists(youtube_cookies):
                self.warnings.append("YouTube uploads enabled but cookies file not found")

        if upload_to_tiktok:
            tiktok_cookies = os.path.join(os.path.dirname(os.path.dirname(self.config_path)), 
                                        'modules', 'config', 'cookies.txt')
            if not os.path.exists(tiktok_cookies):
                self.warnings.append("TikTok uploads enabled but cookies file not found")
