import os
import asyncio
import browser_cookie3
from datetime import datetime, timedelta
from modules.utils.logger import print_header, print_error, print_success
from youtube_up import AllowCommentsEnum, Metadata, PrivacyEnum, YTUploaderSession

async def yt_check_cookies() -> bool:
    """Check if YouTube cookies are valid."""
    try:
        return YTUploaderSession.has_valid_cookies()
    except Exception as e:
        print_error(f"Error checking YouTube cookies: {e}")
        return False

async def get_youtube_cookies():
    """Get YouTube cookies from Firefox browser and save them to a file."""
    try:
        print_header("Getting new cookies file from Firefox...")
        cookies = browser_cookie3.firefox(domain_name='.youtube.com')
        
        os.makedirs("config", exist_ok=True)
        cookie_path = "config/yt_cookies.txt"
        
        with open(cookie_path, "w") as file:
            file.write("# Netscape HTTP Cookie File\n")
            file.write("# This is a generated file! Do not edit.\n\n")
            
            for cookie in cookies:
                file.write(
                    f"{cookie.domain}\t"
                    f"{'TRUE' if cookie.domain.startswith('.') else 'FALSE'}\t"
                    f"{cookie.path}\t"
                    f"{'TRUE' if cookie.secure else 'FALSE'}\t"
                    f"{int(cookie.expires) if cookie.expires else 0}\t"
                    f"{cookie.name}\t"
                    f"{cookie.value}\n"
                )
        
        print_success("YouTube cookies have been saved successfully.")
        return True
    except Exception as e:
        print_error(f"Error getting YouTube cookies: {e}")
        return False

async def yt_upload(file_name: str, broadcaster_name: str, id: str, subfolder: str, schedule: datetime = None) -> bool:
    """
    Upload a video to YouTube.
    
    Args:
        file_name: Title for the video
        broadcaster_name: Name of the Twitch broadcaster
        id: Unique identifier for the clip
        subfolder: Directory containing the video
        schedule: Optional datetime for scheduled upload
    
    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        description = f"""{file_name} 
        twitch.tv/{broadcaster_name}"""

        print_header(f"Uploading {file_name} to YouTube...")
        
        video_path = os.path.join(os.getcwd(), subfolder, f"{broadcaster_name}_{id}_rendered.mp4")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        uploader = YTUploaderSession.from_cookies_txt('config/yt_cookies.txt')
        metadata = Metadata(
            title=file_name[:100],  # YouTube title limit is 100 characters
            description=description,
            privacy=PrivacyEnum.PUBLIC,
            tags=["Twitch", "Clips", "TopClips", "Gaming", broadcaster_name][:500],  # YouTube tag limit
            made_for_kids=False,
            allow_comments_mode=AllowCommentsEnum.HOLD_ALL,
            scheduled_upload=schedule
        )

        # Upload is synchronous, run in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: uploader.upload(video_path, metadata)
        )
        
        print_success(f"Successfully uploaded {file_name} to YouTube")
        return True
        
    except Exception as e:
        print_error(f"YouTube upload error: {e}")
        if "cookie" in str(e).lower():
            print_header("Attempting to refresh cookies...")
            if await get_youtube_cookies():
                print_header("Retrying upload with new cookies...")
                return await yt_upload(file_name, broadcaster_name, id, subfolder, schedule)
        return False
