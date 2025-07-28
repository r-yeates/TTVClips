"""
Module for fetching clips from Twitch API using TwitchAPI package
"""
from typing import List, Dict, Any
import datetime
from twitchAPI.twitch import Twitch
from modules.utils.logger import print_header, print_error, print_success

class ClipFetcher:
    def __init__(self, client_id: str, twitch: Twitch):
        """
        Initialize the ClipFetcher
        
        Args:
            client_id: Twitch Client ID
            twitch: Authenticated Twitch instance
        """
        self.client_id = client_id
        self.twitch = twitch

    async def get_clips(
        self,
        game_id: int,
        clips_amount: int,
        period: int,
        blacklisted_channels: List[str],
        language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """
        Get clips from Twitch API
        
        Args:
            game_id: Twitch game ID to fetch clips for
            clips_amount: Number of clips to fetch
            period: Number of days to look back for clips
            blacklisted_channels: List of channel names to exclude
            language: Language filter for clips (default: 'en')
            
        Returns:
            List of clip data dictionaries
        """
        print_header(f"Getting {clips_amount} clips from Twitch")
        print_header(f"Search parameters: Game ID: {game_id}, Period: {period} days, Language: {language}")
        print_header(f"Blacklisted channels: {len(blacklisted_channels)} channels")

        try:
            # Calculate date range
            started_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=period)
            print_header(f"Searching clips from {started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC onwards")
            
            # Get clips using TwitchAPI - request much more to account for filtering
            clips = []
            request_amount = max(clips_amount * 10, 100)  # Request at least 100 clips
            print_header(f"Requesting {request_amount} clips from Twitch API...")
            
            async for clip in self.twitch.get_clips(
                game_id=str(game_id),
                first=request_amount,
                started_at=started_at
            ):
                clips.append(clip)
                if len(clips) >= request_amount:
                    break
                    
            print_header(f"Received {len(clips)} raw clips from API")
            
            if not clips:
                print_error("No clips found from API")
                return []

            # Filter and process clips with detailed logging
            filtered_clips = self._filter_clips(
                clips=clips,
                language=language,
                blacklisted_channels=blacklisted_channels,
                limit=clips_amount * 2  # Get 2x the target amount for backup clips
            )

            print_success(f"Successfully fetched {len(filtered_clips)} clips after filtering")
            return filtered_clips

        except Exception as e:
            print_error(f"Failed to fetch clips: {str(e)}")
            return []

    def _filter_clips(
        self,
        clips: List[Any],
        language: str,
        blacklisted_channels: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Filter clips based on language and blacklisted channels"""
        filtered = []
        skipped_language = 0
        skipped_blacklisted = 0
        skipped_missing_data = 0
        
        print_header(f"Filtering {len(clips)} clips...")
        
        for clip in clips:
            try:
                # Get clip language
                clip_language = getattr(clip, 'language', '').lower()
                
                # Skip non-matching language (but be more flexible)
                if language.lower() != 'any' and clip_language and clip_language != language.lower():
                    skipped_language += 1
                    continue
                    
                # Skip blacklisted channels
                broadcaster_name = getattr(clip, 'broadcaster_name', '').lower()
                if broadcaster_name in map(str.lower, blacklisted_channels):
                    skipped_blacklisted += 1
                    continue
                
                # Convert Clip object to dictionary with needed fields
                clip_data = {
                    'id': getattr(clip, 'id', None),
                    'url': getattr(clip, 'url', None),
                    'title': getattr(clip, 'title', ''),
                    'broadcaster_name': getattr(clip, 'broadcaster_name', ''),
                    'language': getattr(clip, 'language', ''),
                    'view_count': getattr(clip, 'view_count', 0),
                    'created_at': getattr(clip, 'created_at', None),
                    'thumbnail_url': getattr(clip, 'thumbnail_url', '')
                }
                
                # Skip if missing required fields
                if not all([clip_data['id'], clip_data['url'], clip_data['broadcaster_name']]):
                    skipped_missing_data += 1
                    continue
                
                filtered.append(clip_data)
                
                # Stop if we have enough clips
                if len(filtered) >= limit:
                    break
                    
            except Exception as e:
                print_error(f"Error processing clip: {str(e)}")
                continue
        
        # Print filtering summary
        print_header(f"Filtering summary:")
        print_header(f"  - Total clips processed: {len(clips)}")
        print_header(f"  - Skipped for language ({language}): {skipped_language}")
        print_header(f"  - Skipped for blacklisted channels: {skipped_blacklisted}")
        print_header(f"  - Skipped for missing data: {skipped_missing_data}")
        print_header(f"  - Final clips returned: {len(filtered)}")
                
        return filtered