"""
TTVClips - A tool for downloading and processing Twitch clips
Author: github.com/r-yeates
"""
import os
import sys
import datetime
import asyncio
import json
from typing import List, Dict, Any, Optional


from modules.auth.access_token import TwitchAuthenticator
from modules.data.get_clips import ClipFetcher
from modules.data.download_clips import ClipDownloader
from modules.upload.yt_upload import yt_upload, get_youtube_cookies
from modules.upload.tiktok_upload import tiktok_upload
from modules.utils.logger import print_header, print_error, print_success
from modules.config.config_validator import ConfigValidator
from modules.processing.subtitle_generator import SubtitleGenerator
from modules.processing.ffmpeg_processor import FFmpegProcessor

class TTVClips:
    def __init__(self):
        """Initialize TTVClips with configuration"""
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(script_dir, 'config', 'config.json')
        self.secrets_path = os.path.join(script_dir, 'config', 'secrets.json')
        
        # Validate configuration
        validator = ConfigValidator(self.config_path)
        if not validator.validate():
            raise RuntimeError("Configuration validation failed")
            
        self.config = self._load_config()
        self.secrets = self._load_secrets()
        self._setup_constants()
        self.authenticator = TwitchAuthenticator(self.CLIENT_ID, self.CLIENT_SECRET)
        self.ffmpeg_processor = FFmpegProcessor(self.config)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        config_path = self.config_path
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}") 
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config
    
    def _load_secrets(self) -> Dict[str, str]:
        """Load secrets from secrets.json"""
        if not os.path.exists(self.secrets_path):
            raise FileNotFoundError(f"Secrets file not found: {self.secrets_path}. Please create it with your CLIENT_ID and CLIENT_SECRET.") 
            
        with open(self.secrets_path, 'r', encoding='utf-8') as f:
            secrets = json.load(f)
        
        # Validate required secrets
        required_secrets = ['CLIENT_ID', 'CLIENT_SECRET']
        for secret in required_secrets:
            if secret not in secrets:
                raise ValueError(f"Missing required secret: {secret}")
                
        return secrets
    
    def _setup_constants(self):
        """Setup constants from config"""
        try:
            # Load credentials from secrets
            self.CLIENT_ID = self.secrets['CLIENT_ID']
            self.CLIENT_SECRET = self.secrets['CLIENT_SECRET']
            
            # Main settings
            default_config = self.config['default']
            self.CLIPS_AMOUNT = default_config['CLIPS_AMOUNT']
            self.PERIOD = default_config['PERIOD']
            self.GAME_ID = default_config['GAME_ID']
            self.UPLOAD_TO_YOUTUBE = default_config['UPLOAD_TO_YOUTUBE']
            self.UPLOAD_TO_TIKTOK = default_config['UPLOAD_TO_TIKTOK']
            self.CLIPS_LANGUAGE = default_config.get('CLIPS_LANGUAGE', 'en')
            
            # Clip processing settings
            clip_processing = self.config.get('clip_processing', {})
            self.BATCH_PROCESSING = clip_processing.get('BATCH_PROCESSING', True)

            # Blacklisted channels
            blacklist_config = self.config.get('blacklist', {})
            self.BLACKLISTED_CHANNELS = blacklist_config.get('CHANNELS', [])
            
            # Subtitle settings
            subtitles_config = self.config.get('subtitles', {})
            self.ENABLE_SUBTITLES = subtitles_config.get('ENABLE_SUBTITLES', False)
            self.WHISPER_MODEL_SIZE = subtitles_config.get('WHISPER_MODEL_SIZE', 'base')
            self.SUBTITLE_LANGUAGE = subtitles_config.get('SUBTITLE_LANGUAGE', 'en')
            self.BURN_SUBTITLES = subtitles_config.get('BURN_SUBTITLES', False)
            self.SUBTITLE_FONT_SIZE = subtitles_config.get('SUBTITLE_FONT_SIZE', 20)
            self.SUBTITLE_COLOR = subtitles_config.get('SUBTITLE_COLOR', 'white')
            self.SUBTITLE_OUTLINE_COLOR = subtitles_config.get('SUBTITLE_OUTLINE_COLOR', 'black')
            self.FONT_FILE = subtitles_config.get('FONT_FILE', 'C:/Windows/Fonts/arialbd.ttf')
            self.SUBTITLE_POSITION_Y = subtitles_config.get('SUBTITLE_POSITION_Y', 100)
            self.SUBTITLE_ALIGNMENT = subtitles_config.get('SUBTITLE_ALIGNMENT', 2)
            
            # Video processing settings
            video_config = self.config.get('video', {})
            self.BACKGROUND_TYPE = video_config.get('BACKGROUND_TYPE', 'blurred')  # blurred, gradient, solid
            self.ENABLE_CROP = video_config.get('ENABLE_CROP', False)
            self.CROP_PERCENTAGE = video_config.get('CROP_PERCENTAGE', 10)
            self.CROP_FROM_SIDES = video_config.get('CROP_FROM_SIDES', True)
            
        except KeyError as e:
            raise KeyError(f"Missing required config value: {e}")

    async def initialize(self):
        """Initialize Twitch API components"""
        token, twitch = await self.authenticator.authenticate()
        if not token or not twitch:
            raise RuntimeError("Failed to authenticate with Twitch")
            
        self.clip_fetcher = ClipFetcher(self.CLIENT_ID, twitch)
        self.clip_downloader = ClipDownloader()
        
    async def get_clips(self) -> List[Dict[str, Any]]:
        """Get clips from Twitch API"""
        return await self.clip_fetcher.get_clips(
            game_id=self.GAME_ID,
            clips_amount=self.CLIPS_AMOUNT,
            period=self.PERIOD,
            blacklisted_channels=self.BLACKLISTED_CHANNELS,
            language=self.CLIPS_LANGUAGE
        )
    
    def process_clips(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process clips in optimized batch workflow: Download → Render → Upload"""
        today = datetime.date.today().strftime('%Y-%m-%d')
        subfolder = os.path.join(today)
        clips_dir = os.path.join('clips', subfolder)
        os.makedirs(clips_dir, exist_ok=True)
        
        # Phase 1: Check what needs processing and download clips
        print_header("Phase 1: Downloading clips...")
        clips_to_process = []
        already_rendered = []
        successful_downloads = 0
        target_clips = self.CLIPS_AMOUNT
        
        for clip in clips:
            # Stop if we have enough clips
            if successful_downloads >= target_clips:
                break
                
            try:
                # Generate expected filename to match ClipDownloader logic
                # ClipDownloader uses: {broadcaster_name}_{clip_id}.mp4
                expected_filename = f"{clip['broadcaster_name']}_{clip['id']}.mp4"
                expected_file_path = os.path.join(clips_dir, expected_filename)
                
                base, ext = os.path.splitext(expected_file_path)
                rendered_path = f"{base}_rendered{ext}"
                
                # If already rendered, skip entirely (no download, no subtitle generation)
                if os.path.exists(rendered_path):
                    print_success(f"Already rendered: {clip['title'][:50]}")
                    already_rendered.append({
                        'clip': clip,
                        'file_path': rendered_path
                    })
                    successful_downloads += 1
                    continue
                
                # Only download and process if not already rendered
                print_header(f"Downloading: {clip['title'][:50]}...")
                file_path = self.clip_downloader.download(clip, subfolder)
                if file_path:
                    clips_to_process.append({
                        'clip': clip,
                        'raw_file_path': file_path,
                        'expected_rendered_path': rendered_path
                    })
                    print_success(f"Downloaded: {os.path.basename(file_path)}")
                    successful_downloads += 1
                else:
                    print_error(f"Failed to download: {clip['title'][:50]} - Trying next clip...")
                    continue  # Skip to next clip instead of counting as failure
                    
            except Exception as e:
                print_error(f"Error processing clip {clip.get('id', 'unknown')}: {str(e)} - Trying next clip...")
                continue  # Skip to next clip instead of stopping
        
        print_success(f"Successfully downloaded/found {successful_downloads} clips")
        
        # Phase 2: Generate subtitles for all downloaded clips
        if self.ENABLE_SUBTITLES and clips_to_process:
            print_header("Phase 2: Generating subtitles...")
            self._generate_subtitles_batch(clips_to_process)
        
        # Phase 3: Render all clips
        print_header("Phase 3: Rendering clips...")
        successfully_rendered = []
        
        for clip_data in clips_to_process:
            try:
                clip = clip_data['clip']
                file_path = clip_data['raw_file_path']
                subtitle_data = clip_data.get('subtitle_data')
                
                print_header(f"Rendering: {clip['title'][:50]}...")
                processed_path = self._render_clip(file_path, clip, subtitle_data)
                
                if processed_path:
                    successfully_rendered.append({
                        'clip': clip,
                        'file_path': processed_path
                    })
                else:
                    print_error(f"Failed to render: {clip['title'][:50]}")
                    
            except Exception as e:
                print_error(f"Error rendering clip {clip.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Combine already rendered + newly rendered clips
        all_processed = already_rendered + successfully_rendered
        
        print_success(f"Processing complete: {len(already_rendered)} already rendered, {len(successfully_rendered)} newly rendered")
        return all_processed
    
    def _generate_subtitles_batch(self, clips_to_process: List[Dict[str, Any]]):
        """Generate subtitles for all clips in batch"""
        subtitle_generator = SubtitleGenerator(model_size=self.WHISPER_MODEL_SIZE, config=self.config)
        print_header(f"Using Whisper model: {self.WHISPER_MODEL_SIZE}, Language: {self.SUBTITLE_LANGUAGE}")
        
        for clip_data in clips_to_process:
            try:
                clip = clip_data['clip']
                file_path = clip_data['raw_file_path']
                
                print_header(f"Generating subtitles: {clip.get('title', 'clip')[:50]}...")
                
                import tempfile
                # Get audio suffix from config
                paths_config = self.config.get('paths', {})
                audio_suffix = paths_config.get('TEMP_AUDIO_SUFFIX', '_audio.wav')
                temp_audio = os.path.join(tempfile.gettempdir(), f"{clip.get('id', 'temp')}{audio_suffix}")
                
                # Extract audio using FFmpeg
                if self.ffmpeg_processor.extract_audio_ffmpeg(file_path, temp_audio):
                    subtitle_data = subtitle_generator.transcribe_audio(temp_audio, self.SUBTITLE_LANGUAGE)
                    clip_data['subtitle_data'] = subtitle_data
                else:
                    print_error("FFmpeg audio extraction failed, trying fallback...")
                    subtitle_generator.extract_audio(file_path, temp_audio)
                    subtitle_data = subtitle_generator.transcribe_audio(temp_audio, self.SUBTITLE_LANGUAGE)
                    clip_data['subtitle_data'] = subtitle_data
                
                # Clean up temp audio file
                try:
                    if os.path.exists(temp_audio):
                        os.remove(temp_audio)
                except:
                    pass
                    
            except Exception as e:
                print_error(f"Subtitle generation failed for {clip.get('title', 'clip')[:50]}: {e}")
                clip_data['subtitle_data'] = None
    
    def _render_clip(self, input_path: str, clip: Dict[str, Any], subtitle_data: List[Dict] = None) -> Optional[str]:
        """Render a clip using FFmpeg for maximum speed"""
        try:
            return self.ffmpeg_processor.process_clip(
                input_path=input_path,
                clip=clip,
                subtitle_data=subtitle_data,
                enable_subtitles=self.ENABLE_SUBTITLES,
                burn_subtitles=self.BURN_SUBTITLES,
                background_type=self.BACKGROUND_TYPE,
                font_file=self.FONT_FILE,
                enable_crop=self.ENABLE_CROP,
                crop_percentage=self.CROP_PERCENTAGE,
                crop_from_sides=self.CROP_FROM_SIDES,
                subtitle_position_y=self.SUBTITLE_POSITION_Y,
                subtitle_alignment=self.SUBTITLE_ALIGNMENT
            )
        except Exception as e:
            print_error(f"Error rendering clip with FFmpeg: {str(e)}")
            return None
    
    

    async def upload_clips(self, processed_clips: List[Dict[str, Any]]):
        """Upload processed clips to configured platforms with 30-minute scheduling intervals"""
        if not processed_clips:
            print_error("No clips to upload")
            return

        today = datetime.date.today().strftime('%Y-%m-%d')
        subfolder = os.path.join('clips', today)

        # Calculate upload schedule using config values
        upload_config = self.config.get('upload_scheduling', {})
        initial_delay = upload_config.get('INITIAL_DELAY_MINUTES', 30)
        interval_minutes = upload_config.get('INTERVAL_MINUTES', 30)
        
        base_time = datetime.datetime.now() + datetime.timedelta(minutes=initial_delay)

        for i, processed in enumerate(processed_clips):
            clip = processed['clip']
            file_path = processed['file_path']
            
            # Schedule each upload with configured interval
            scheduled_time = base_time + datetime.timedelta(minutes=interval_minutes * i)
            
            if self.UPLOAD_TO_YOUTUBE:
                try:
                    print_header(f"Scheduling YouTube upload for {scheduled_time.strftime('%H:%M')}: {clip['title']}")
                    success = await yt_upload(
                        file_name=clip['title'],
                        broadcaster_name=clip['broadcaster_name'],
                        id=clip['id'],
                        subfolder=subfolder,
                        schedule=scheduled_time
                    )
                    if success:
                        print_success(f"Successfully scheduled YouTube upload: {clip['title']}")
                    else:
                        print_error(f"Failed to schedule YouTube upload: {clip['title']}")
                except Exception as e:
                    print_error(f"Error scheduling YouTube upload: {str(e)}")

            if self.UPLOAD_TO_TIKTOK:
                try:
                    print_header(f"Uploading to TikTok: {clip['title']}")
                    success = await tiktok_upload(
                        file_name=clip['title'],
                        broadcaster_name=clip['broadcaster_name'],
                        clip_id=clip['id'],
                        subfolder=subfolder
                    )
                    if success:
                        print_success(f"Successfully uploaded to TikTok: {clip['title']}")
                    else:
                        print_error(f"Failed to upload to TikTok: {clip['title']}")
                except Exception as e:
                    print_error(f"Error uploading to TikTok: {str(e)}")

    async def run(self):
        """Main execution flow"""
        try:
            # Initialize components
            await self.initialize()
            
            # Get clips
            print_header("Fetching clips...")
            clips = await self.get_clips()
            
            if not clips:
                print_error("No clips found")
                return
                
            print_success(f"Found {len(clips)} clips")
            
            # Process clips
            print_header("Processing clips...")
            processed_clips = self.process_clips(clips)
            
            if not processed_clips:
                print_error("No clips were processed successfully")
                return
                
            print_success(f"Successfully processed {len(processed_clips)} clips")
            
            # Upload clips if enabled
            if self.UPLOAD_TO_YOUTUBE or self.UPLOAD_TO_TIKTOK:
                await self.upload_clips(processed_clips)
            
        except Exception as e:
            print_error(f"An error occurred: {str(e)}")
            raise
        finally:
            # Cleanup async resources
            await self._cleanup()
    
    async def _cleanup(self):
        """Cleanup async resources"""
        try:
            # Close any aiohttp sessions if they exist
            if hasattr(self, 'clip_fetcher') and hasattr(self.clip_fetcher, 'session'):
                if not self.clip_fetcher.session.closed:
                    await self.clip_fetcher.session.close()
            
            # Give a moment for cleanup to complete
            await asyncio.sleep(0.1)
        except Exception as e:
            # Don't let cleanup errors crash the app
            pass

def print_banner():
    """Print the application banner"""
    print("\033[1;92m" + r"""
┌─────────────────────────────────────────────┐
│                                             │
│   _____________    __  _________            │
│  /_  __/_  __/ |  / / / ____/ (_)___  _____ │
│   / /   / /  | | / / / /   / / / __ \/ ___/ │
│  / /   / /   | |/ / / /___/ / / /_/ (__  )  │
│ /_/   /_/    |___/  \____/_/_/ .___/____/   │
│                             /_/             │
│                                             │
│             github.com/r-yeates             │
└─────────────────────────────────────────────┘
""" + "\033[0m")

async def main():
    """Main entry point"""
    print_banner()
    app = None
    
    try:
        # Initialize YouTube cookies if needed
        await get_youtube_cookies()
        
        # Create and run TTVClips
        app = TTVClips()
        await app.run()
        
    except KeyboardInterrupt:
        print_header("\nGracefully shutting down...")
    except asyncio.CancelledError:
        print_header("\nOperation cancelled, shutting down...")
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)
    finally:
        # Ensure cleanup happens
        if app:
            try:
                await app._cleanup()
            except:
                pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C at the top level
        print("\nProgram interrupted by user.")
        sys.exit(0)