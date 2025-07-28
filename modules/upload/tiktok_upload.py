import os
import asyncio
from typing import Optional
from datetime import datetime
from tiktok_uploader.upload import upload_video
from modules.utils.logger import print_header, print_error, print_success


async def tiktok_upload(
    file_name: str,
    broadcaster_name: str,
    clip_id: str,
    subfolder: str,
    schedule: Optional[datetime] = None
) -> bool:
    """
    Upload a video to TikTok

    Args:
        file_name: Title for the video
        broadcaster_name: Name of the Twitch broadcaster
        creator_id: Unique identifier for the clip
        subfolder: Directory containing the video
        schedule: Optional datetime for scheduled upload (not currently supported by TikTok API)

    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        video_path = os.path.join(os.getcwd(), subfolder, f"{broadcaster_name}_{clip_id}_rendered.mp4")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        description = f"{file_name} #Twitch #TwitchClips #TwitchFails #TwitchMoments #TwitchStreamer #Streamer #fyp"
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(project_root, 'config')
        os.makedirs(config_dir, exist_ok=True)
        cookies_path = os.path.join(config_dir, 'tt_cookies.txt')

        # TikTok upload is synchronous, run in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: upload_video(
                filename=video_path,
                description=description[:2200],  # TikTok description limit
                cookies=cookies_path,
                headless=False,
                browser='firefox'
            )
        )

        print_success(f"Successfully uploaded {file_name} to TikTok")
        return True

    except Exception as e:
        print_error(f"TikTok upload error: {e}")
        if "cookie" in str(e).lower() or "auth" in str(e).lower():
            print_error("TikTok authentication failed. Please update your cookies file.")
        return False
