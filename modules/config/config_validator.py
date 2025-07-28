import json
from typing import Dict, List, Optional, Any
import os
from datetime import datetime, timedelta
from modules.utils.logger import print_error, print_header, print_success

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors"""
    pass

class ConfigValidator:
    REQUIRED_SECTIONS = ['default', 'blacklist']
    REQUIRED_DEFAULT_KEYS = [
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
            self._validate_watermark_config()
            self._validate_video_config()
            self._validate_encoding_config()
            self._validate_paths_config()

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

    def _validate_watermark_config(self):
        """Validate watermark configuration"""
        watermark_section = self.config.get('watermark', {})
        
        if not watermark_section:
            # Watermark section is optional
            return
            
        # Validate ENABLE_WATERMARK
        enable_watermark = watermark_section.get('ENABLE_WATERMARK')
        if enable_watermark is not None and not isinstance(enable_watermark, bool):
            self.errors.append("ENABLE_WATERMARK must be a boolean value (true/false)")
            
        # If watermark is enabled, validate other settings
        if enable_watermark:
            # Validate watermark text
            watermark_text = watermark_section.get('WATERMARK_TEXT', '')
            if not isinstance(watermark_text, str):
                self.errors.append("WATERMARK_TEXT must be a string")
            elif len(watermark_text.strip()) == 0:
                self.warnings.append("WATERMARK_TEXT is empty")
                
            # Validate font size
            font_size = watermark_section.get('WATERMARK_FONT_SIZE', 24)
            if not isinstance(font_size, int) or font_size < 8 or font_size > 100:
                self.errors.append("WATERMARK_FONT_SIZE must be an integer between 8 and 100")
                
            # Validate margins
            margin_x = watermark_section.get('WATERMARK_MARGIN_X', 20)
            margin_y = watermark_section.get('WATERMARK_MARGIN_Y', 20)
            
            if not isinstance(margin_x, int) or margin_x < 0 or margin_x > 200:
                self.errors.append("WATERMARK_MARGIN_X must be an integer between 0 and 200")
            if not isinstance(margin_y, int) or margin_y < 0 or margin_y > 200:
                self.errors.append("WATERMARK_MARGIN_Y must be an integer between 0 and 200")

    def _validate_video_config(self):
        """Validate video configuration"""
        video_section = self.config.get('video', {})
        
        # Validate video dimensions
        width = video_section.get('VIDEO_WIDTH', 1080)
        height = video_section.get('VIDEO_HEIGHT', 1920)
        
        if not isinstance(width, int) or width < 480 or width > 3840:
            self.errors.append("VIDEO_WIDTH must be an integer between 480 and 3840")
        if not isinstance(height, int) or height < 720 or height > 2160:
            self.errors.append("VIDEO_HEIGHT must be an integer between 720 and 2160")
            
        # Validate background type
        bg_type = video_section.get('BACKGROUND_TYPE', 'blurred')
        if bg_type not in ['blurred', 'gradient', 'solid']:
            self.errors.append("BACKGROUND_TYPE must be 'blurred', 'gradient', or 'solid'")

    def _validate_encoding_config(self):
        """Validate encoding configuration"""
        encoding_section = self.config.get('encoding', {})
        
        # Validate CRF
        crf = encoding_section.get('CRF')
        if crf is not None:
            try:
                crf_val = int(crf)
                if crf_val < 0 or crf_val > 51:
                    self.errors.append("CRF must be between 0 and 51")
            except (ValueError, TypeError):
                self.errors.append("CRF must be a valid integer")
                
        # Validate framerate
        framerate = encoding_section.get('FRAMERATE')
        if framerate is not None:
            try:
                fr_val = int(framerate)
                if fr_val < 15 or fr_val > 60:
                    self.errors.append("FRAMERATE must be between 15 and 60")
            except (ValueError, TypeError):
                self.errors.append("FRAMERATE must be a valid integer")
                
        # Validate max duration
        max_duration = encoding_section.get('MAX_DURATION_SECONDS', 59)
        if not isinstance(max_duration, int) or max_duration < 10 or max_duration > 600:
            self.errors.append("MAX_DURATION_SECONDS must be between 10 and 600")

    def _validate_paths_config(self):
        """Validate paths configuration"""
        paths_section = self.config.get('paths', {})
        
        # Check if essential files exist
        youtube_cookies = paths_section.get('YOUTUBE_COOKIES', 'config/yt_cookies.txt')
        if self.config.get('default', {}).get('UPLOAD_TO_YOUTUBE', False):
            full_path = os.path.join(os.path.dirname(self.config_path), '..', youtube_cookies)
            if not os.path.exists(full_path):
                self.warnings.append(f"YouTube cookies file not found: {youtube_cookies}")
