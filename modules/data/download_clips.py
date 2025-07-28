"""
Module for downloading Twitch clips using Streamlink
"""
import os
import subprocess
import sys
import shutil
from typing import Dict, Any, Optional
import pkg_resources

from modules.utils.logger import print_header, print_error, print_success

class ClipDownloader:
    def __init__(self, base_folder: str = 'clips'):
        """Initialize ClipDownloader
        
        Args:
            base_folder: Base folder to store downloaded clips
        """
        self.base_folder = base_folder
        self._ensure_streamlink_installed()
        
    def _ensure_streamlink_installed(self) -> None:
        """Ensure streamlink is installed and available"""
        try:
            # Check if streamlink is installed
            pkg_resources.get_distribution('streamlink')
        except pkg_resources.DistributionNotFound:
            print_header("Streamlink not found, installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlink>=6.11.0"])
            print_success("Streamlink installed successfully")
            
        # Find streamlink executable
        self.streamlink_path = self._get_streamlink_path()
        if not self.streamlink_path:
            raise RuntimeError("Could not find streamlink executable")
            
    def _get_streamlink_path(self) -> Optional[str]:
        """Get the path to the streamlink executable"""
        # Try Scripts directory first (pip install location)
        scripts_path = os.path.join(os.path.dirname(sys.executable), "Scripts")
        streamlink_exe = "streamlink.exe" if sys.platform == "win32" else "streamlink"
        local_path = os.path.join(scripts_path, streamlink_exe)
        
        if os.path.exists(local_path):
            return local_path
            
        # Try PATH
        path_streamlink = shutil.which(streamlink_exe)
        if path_streamlink:
            return path_streamlink
            
        return None
        
    def download(self, clip: Dict[str, Any], subfolder: str) -> Optional[str]:
        """Download a clip using Streamlink
        
        Args:
            clip: Clip data from Twitch API
            subfolder: Subfolder name to store the clip in (usually today's date)
            
        Returns:
            str: Path to downloaded file if successful, None otherwise
        """
        try:
            # Setup paths
            folder_path = os.path.join(self.base_folder, subfolder)
            os.makedirs(folder_path, exist_ok=True)
            
            file_path = os.path.join(folder_path, f"{clip['broadcaster_name']}_{clip['id']}.mp4")
            
            # Skip if already downloaded
            if os.path.exists(file_path):
                print_header(f"Clip already exists: {os.path.basename(file_path)}")
                return file_path

            # Get clip URL
            clip_url = clip.get('url')
            if not clip_url:
                print_error("No clip URL found in clip data")
                return None
            
            # Download using Streamlink
            result = self._run_streamlink(clip_url, file_path)
            
            if result and os.path.exists(file_path):
                return file_path
            
            print_error(f"Failed to download clip: {clip_url}")
            return None
            
        except Exception as e:
            print_error(f"Error downloading clip: {str(e)}")
            return None

    def _run_streamlink(self, url: str, output_file: str) -> bool:
        """Run Streamlink to download a clip
        
        Args:
            url: URL of the clip to download
            output_file: Path to save the downloaded file
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            cmd = [
                self.streamlink_path,
                '--stream-timeout', '30',  # Add timeout to prevent hanging
                '--twitch-disable-hosting',  # Disable hosted streams
                '--twitch-disable-ads',  # Skip ads
                url,
                'best',
                '-o', output_file
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode == 0:
                return True
                
            error_msg = process.stderr.strip()
            if "error: No plugin can handle URL" in error_msg:
                print_error("Invalid clip URL or clip no longer available")
            elif "error: 404 Client Error" in error_msg:
                print_error("Clip not found (404)")
            else:
                print_error(f"Error running streamlink: {error_msg}")
            return False
            
        except subprocess.TimeoutExpired:
            print_error("Download timed out after 5 minutes")
            return False
        except Exception as e:
            print_error(f"Error running streamlink: {str(e)}")
            return False