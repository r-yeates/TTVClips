#!/usr/bin/env python3
"""
FFmpeg-based video processor for ultra-fast rendering
Author: github.com/r-yeates
"""
import os
import subprocess
import tempfile
import json
from typing import List, Dict, Any, Optional, Tuple
from modules.utils.logger import print_header, print_error, print_success

class FFmpegProcessor:
    def __init__(self, config: dict = None):
        """Initialize FFmpeg processor with optional configuration"""
        self.ffmpeg_path = self._find_ffmpeg()
        self.temp_dir = tempfile.gettempdir()
        self.config = config or {}
        
    def _find_meme_font(self) -> str:
        """Find the best available font for meme-style text on Windows"""
        # Get font priorities from config
        fonts_config = self.config.get('fonts', {})
        font_priorities = fonts_config.get('FONT_PRIORITIES', [
            "C:/Windows/Fonts/ariblk.ttf",     # Arial Black (best for memes)
            "C:/Windows/Fonts/impact.ttf",     # Impact (classic meme font)
            "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
            "C:/Windows/Fonts/arial.ttf"       # Arial (fallback)
        ])
        
        for font_path in font_priorities:
            if os.path.exists(font_path):
                return font_path
        
        # If no fonts found, return the default from config
        return fonts_config.get('DEFAULT_FONT_PATH', "C:/Windows/Fonts/arialbd.ttf")
    
    def _create_meme_title_filter(self, text: str, video_width: int, video_height: int, line_index: int = 0, total_lines: int = 1) -> str:
        """Create FFmpeg drawtext filter for meme-style title text with proper margins"""
        title_config = self.config.get('title_style', {})
        
        # Get meme-style configuration with defaults
        font_size_multiplier = title_config.get('FONT_SIZE_MULTIPLIER', 0.09)
        border_width = title_config.get('BORDER_WIDTH', 5)
        text_color = title_config.get('TEXT_COLOR', 'white')
        border_color = title_config.get('BORDER_COLOR', 'black')
        add_shadow = title_config.get('ADD_SHADOW', True)
        shadow_offset = title_config.get('SHADOW_OFFSET', 2)
        
        # Calculate font size based on video height (9% of height for high visibility)
        font_size = int(video_height * font_size_multiplier)
        
        # Calculate horizontal margins (configurable, default 10% of video width on each side)
        margin_percent = title_config.get('MARGIN_PERCENT', 0.10)
        side_margin = int(video_width * margin_percent)
        
        # Get the best meme font
        font_file = self._find_meme_font()
        font_file_escaped = font_file.replace("\\", "/").replace(":", "\\:")
        
        # Escape text for FFmpeg: single quotes must be handled as '\''
        # See: https://ffmpeg.org/ffmpeg-filters.html#drawtext-1
        escaped_text = text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:").replace("%", "\\%")
        
        # Calculate Y position for multi-line titles
        if total_lines == 1:
            y_pos = 200  # Single line centered
        elif total_lines == 2:
            y_pos = 170 + (line_index * 70)  # Two lines: 170, 240
        else:
            # Three lines: 140, 200, 260
            y_pos = 140 + (line_index * 60)
        
        # Build the drawtext filter with meme-style formatting and safe margins
        filter_parts = [
            f"text='{escaped_text}'",
            f"fontfile='{font_file_escaped}'",
            f"fontsize={font_size}",
            f"fontcolor={text_color}",
            f"borderw={border_width}",
            f"bordercolor={border_color}",
            # Center horizontally with safe margins to prevent off-screen text
            # Use a fixed margin approach that's simpler than conditional logic
            f"x=(w-text_w)/2",
            f"y={y_pos}"
        ]
        
        # Add shadow if enabled
        if add_shadow:
            filter_parts.extend([
                f"shadowx={shadow_offset}",
                f"shadowy={shadow_offset}",
                "shadowcolor=black@0.5"
            ])
        
        return ":".join(filter_parts)
        
    def _create_watermark_filter(self, video_width: int, video_height: int) -> str:
        """Create FFmpeg drawtext filter for watermark"""
        watermark_config = self.config.get('watermark', {})
        
        # Return empty string if watermark is disabled
        if not watermark_config.get('ENABLE_WATERMARK', False):
            return ""
        
        # Get watermark configuration with defaults
        watermark_text = watermark_config.get('WATERMARK_TEXT', 'YourChannel')
        font_size = watermark_config.get('WATERMARK_FONT_SIZE', 24)
        color = watermark_config.get('WATERMARK_COLOR', 'white@0.7')
        margin_x = watermark_config.get('WATERMARK_MARGIN_X', 20)
        margin_y = watermark_config.get('WATERMARK_MARGIN_Y', 20)
        
        # Use the same font as the title for consistency, or default from config
        font_file = self.config.get('subtitles', {}).get('FONT_FILE') or self.config.get('fonts', {}).get('DEFAULT_FONT_PATH', 'C:/Windows/Fonts/arial.ttf')
        
        # Escape special characters for FFmpeg
        text_escaped = watermark_text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:").replace("%", "\\%")
        font_file_escaped = font_file.replace("\\", "/").replace(":", "\\:")
        
        # Build filter parts for bottom-left positioning
        filter_parts = [
            f"text='{text_escaped}'",
            f"fontfile='{font_file_escaped}'",
            f"fontsize={font_size}",
            f"fontcolor={color}",
            f"x={margin_x}",  # Distance from left edge
            f"y=h-text_h-{margin_y}"  # Distance from bottom edge
        ]
        
        return ":".join(filter_parts)
        
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        # Try common locations
        possible_paths = [
            "ffmpeg",  # System PATH
            "ffmpeg.exe",  # Windows
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            "/usr/bin/ffmpeg",  # Linux
            "/usr/local/bin/ffmpeg",  # macOS
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "-version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print_success(f"Found FFmpeg at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
                
        raise RuntimeError("FFmpeg not found! Please install FFmpeg and add it to your PATH")
    
    def get_video_info(self, input_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe"""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", input_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")
        except Exception as e:
            print_error(f"Error getting video info: {e}")
            return {}
    
    def create_subtitle_file(self, subtitle_data: List[Dict], output_path: str) -> bool:
        """Create SRT subtitle file for FFmpeg with TikTok-style timing"""
        try:
            if not subtitle_data:
                print_error("No subtitle data available")
                return False
            
            # First, collect all subtitle chunks with their timing
            subtitle_chunks = []
            
            for segment in subtitle_data:
                if not segment.get('text', '').strip():
                    continue
                
                # Use word-level timing if available for TikTok-style rapid subtitles
                if segment.get('words') and len(segment['words']) > 0:
                    words_data = segment['words']
                    
                    # Smart chunking to avoid orphaned words
                    chunks = self._create_smart_chunks(words_data)
                    
                    for chunk_words in chunks:
                        chunk_text = ' '.join([w['word'].strip() for w in chunk_words])
                        start_time = chunk_words[0]['start']
                        end_time = chunk_words[-1]['end']
                        
                        # Ensure minimum display time for readability
                        duration = end_time - start_time
                        if duration < 0.5:  # Minimum 0.5 seconds
                            end_time = start_time + 0.5
                        
                        # Make text uppercase for TikTok style
                        display_text = chunk_text.upper()
                        
                        subtitle_chunks.append({
                            'text': display_text,
                            'start': start_time,
                            'end': end_time
                        })
                        
                else:
                    # Fallback: split text into smart chunks for TikTok style
                    text = segment['text'].strip()
                    start_time = segment['start']
                    end_time = segment['end']
                    duration = end_time - start_time
                    
                    # Smart chunking for text without word-level timing
                    words = text.split()
                    chunks = self._create_smart_text_chunks(words)
                    
                    if chunks:
                        chunk_duration = duration / len(chunks)
                        chunk_duration = max(0.5, chunk_duration)  # Minimum 0.5s per chunk
                        
                        for k, chunk_words in enumerate(chunks):
                            chunk_start = start_time + (k * chunk_duration)
                            chunk_end = min(chunk_start + chunk_duration, end_time)
                            
                            chunk_text = ' '.join(chunk_words)
                            # Make text uppercase for TikTok style
                            display_text = chunk_text.upper()
                            
                            subtitle_chunks.append({
                                'text': display_text,
                                'start': chunk_start,
                                'end': chunk_end
                            })
            
            # Sort chunks by start time
            subtitle_chunks.sort(key=lambda x: x['start'])
            
            # Fix overlapping subtitles - ensure each subtitle ends before the next one starts
            for i in range(len(subtitle_chunks) - 1):
                current_chunk = subtitle_chunks[i]
                next_chunk = subtitle_chunks[i + 1]
                
                # If current subtitle overlaps with next one, cut it short
                if current_chunk['end'] > next_chunk['start']:
                    # Leave a small gap (0.1 seconds) between subtitles
                    gap = 0.1
                    current_chunk['end'] = max(current_chunk['start'] + 0.3, next_chunk['start'] - gap)
            
            # Write the non-overlapping subtitles to file
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(subtitle_chunks, 1):
                    start_srt = self._seconds_to_srt_time(chunk['start'])
                    end_srt = self._seconds_to_srt_time(chunk['end'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_srt} --> {end_srt}\n")
                    f.write(f"{chunk['text']}\n\n")
            return True
            
        except Exception as e:
            print_error(f"Error creating TikTok-style subtitle file: {e}")
            return False
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _create_smart_chunks(self, words_data: List[Dict]) -> List[List[Dict]]:
        """Create smart word chunks that avoid orphaned single words and respect character limits"""
        if not words_data:
            return []
        
        # Check if the entire phrase should be kept together
        all_words_text = ' '.join([w['word'].strip() for w in words_data])
        if len(words_data) > 3 and len(all_words_text) <= 20:
            return [words_data]
        
        chunks = []
        i = 0
        
        while i < len(words_data):
            current_chunk = [words_data[i]]
            current_text = words_data[i]['word'].strip()
            j = i + 1
            
            # Look ahead to see how many words are left
            remaining_words = len(words_data) - j
            
            # Add words to current chunk if they fit timing and character constraints
            while j < len(words_data) and len(current_chunk) < 4:  # Max 4 words
                # Check timing gap
                gap = words_data[j]['start'] - words_data[j-1]['end']
                if gap > 0.2:  # Break on pauses
                    break
                if words_data[j]['end'] - current_chunk[0]['start'] > 1.5:  # Max 1.5s per chunk
                    break
                
                # Check character limit
                test_text = current_text + ' ' + words_data[j]['word'].strip()
                if len(test_text) > 20:
                    break
                
                current_chunk.append(words_data[j])
                current_text = test_text
                j += 1
            
            # Smart orphan prevention
            remaining_after_chunk = len(words_data) - j
            
            # If we'd leave exactly 1 word orphaned, include it if it fits
            if remaining_after_chunk == 1 and len(current_chunk) < 4:
                test_text = current_text + ' ' + words_data[j]['word'].strip()
                if len(test_text) <= 20:
                    current_chunk.append(words_data[j])
                    j += 1
            # If we have 2 words left and current chunk has only 1 word, try to take one more
            elif remaining_after_chunk == 2 and len(current_chunk) == 1:
                test_text = current_text + ' ' + words_data[j]['word'].strip()
                if len(test_text) <= 20:
                    current_chunk.append(words_data[j])
                    j += 1
            
            if current_chunk:
                chunks.append(current_chunk)
            
            i = j
        
        return chunks
    
    def _create_smart_text_chunks(self, words: List[str]) -> List[List[str]]:
        """Create smart text chunks that avoid orphaned single words and respect character limits"""
        if not words:
            return []
        
        # Calculate total character count for the phrase
        total_text = ' '.join(words)
        total_chars = len(total_text)
        
        # If it's more than 3 words AND under 20 characters, keep it together
        if len(words) > 3 and total_chars <= 20:
            return [words]
        
        # If it's 3 words or less, keep together regardless of character count
        if len(words) <= 3:
            return [words]
        
        # For longer phrases, use smart chunking
        chunks = []
        i = 0
        
        while i < len(words):
            remaining = len(words) - i
            
            if remaining == 1:
                # Single word left - add to previous chunk if possible
                if chunks and len(' '.join(chunks[-1]) + ' ' + words[i]) <= 20:
                    chunks[-1].append(words[i])
                else:
                    chunks.append([words[i]])
                break
            elif remaining == 2:
                # Two words left - check if they fit in 20 chars
                two_word_text = ' '.join(words[i:i+2])
                if len(two_word_text) <= 20:
                    chunks.append(words[i:i+2])
                else:
                    # Split them if too long
                    chunks.append([words[i]])
                    chunks.append([words[i+1]])
                break
            elif remaining == 3:
                # Three words left - check if they fit in 20 chars
                three_word_text = ' '.join(words[i:i+3])
                if len(three_word_text) <= 20:
                    chunks.append(words[i:i+3])
                else:
                    # Try 2+1 split
                    two_word_text = ' '.join(words[i:i+2])
                    if len(two_word_text) <= 20:
                        chunks.append(words[i:i+2])
                        chunks.append([words[i+2]])
                    else:
                        # Split as 1+1+1
                        chunks.append([words[i]])
                        chunks.append([words[i+1]])
                        chunks.append([words[i+2]])
                break
            elif remaining == 4:
                # Four words - try to split evenly while respecting char limit
                four_word_text = ' '.join(words[i:i+4])
                if len(four_word_text) <= 20:
                    chunks.append(words[i:i+4])
                    break
                else:
                    # Try 2+2 split
                    first_two = ' '.join(words[i:i+2])
                    last_two = ' '.join(words[i+2:i+4])
                    if len(first_two) <= 20 and len(last_two) <= 20:
                        chunks.append(words[i:i+2])
                        chunks.append(words[i+2:i+4])
                    else:
                        # Fall back to smaller chunks
                        chunks.append([words[i]])
                        i += 1
                        continue
                break
            else:
                # More than 4 words - take what fits in 20 chars
                current_chunk = []
                current_text = ""
                
                for j in range(i, min(i + 4, len(words))):  # Max 4 words per chunk
                    test_text = current_text + (' ' if current_text else '') + words[j]
                    if len(test_text) <= 20:
                        current_chunk.append(words[j])
                        current_text = test_text
                    else:
                        break
                
                if not current_chunk:  # Single word is too long
                    current_chunk = [words[i]]
                
                chunks.append(current_chunk)
                i += len(current_chunk)
        
        return chunks
    
    def _clean_title_text(self, text: str) -> str:
        """Clean title text by removing emojis, special characters, and non-English text"""
        import re
        
        # Remove emojis and other Unicode symbols
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002500-\U00002BEF"  # chinese char
            "\U00002702-\U000027B0"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642" 
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+", 
            flags=re.UNICODE
        )
        
        # Remove emojis
        text = emoji_pattern.sub('', text)
        
        # Keep only ASCII letters, numbers, spaces, and basic punctuation
        text = re.sub(r'[^\w\s\-.,!?()\'"]', '', text)
        
        # Clean up multiple spaces and trim
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _split_title_text(self, text: str, font_size: int = None, video_width: int = 1080) -> List[str]:
        """Split title text into multiple lines based on font size and video width
        
        Args:
            text: The text to split
            font_size: Font size in pixels (if None, will estimate based on config)
            video_width: Video width in pixels for calculating line capacity
        """
        # Estimate font size if not provided
        if font_size is None:
            title_config = self.config.get('title_style', {})
            font_size_multiplier = title_config.get('FONT_SIZE_MULTIPLIER', 0.09)
            # Use config video height for calculation, default to 1920
            video_height = self.config.get('video', {}).get('VIDEO_HEIGHT', 1920)
            font_size = int(video_height * font_size_multiplier)
        
        # Get video width from config if not provided
        if video_width == 1080:  # Default value, replace with config
            video_width = self.config.get('video', {}).get('VIDEO_WIDTH', 1080)
        
        # Calculate approximate characters that fit per line
        # For meme fonts (Arial Black/Impact), characters are wider - about 80% of font size
        # For normal fonts, about 60% of font size
        title_config = self.config.get('title_style', {})
        use_meme_style = title_config.get('STYLE', 'normal') == 'meme'
        
        if use_meme_style:
            char_width = font_size * 0.8  # Meme fonts are wider
        else:
            char_width = font_size * 0.6  # Normal fonts
            
        # Leave 20% margin on each side (40% total)
        usable_width = video_width * 0.8
        max_chars_per_line = int(usable_width / char_width)
        
        # For meme style, be even more conservative to ensure no overflow
        if use_meme_style:
            max_chars_per_line = int(max_chars_per_line * 0.9)  # Reduced safety margin from 0.8 to 0.9
        
        # Ensure reasonable bounds (minimum 12, maximum 50)
        max_chars_per_line = max(12, min(50, max_chars_per_line))
        
        if len(text) <= max_chars_per_line:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # Check if adding this word would exceed the limit
            test_line = current_line + (" " if current_line else "") + word
            
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                # Start new line
                if current_line:
                    lines.append(current_line)
                current_line = word
                
                # If single word is too long, truncate it
                if len(current_line) > max_chars_per_line:
                    current_line = current_line[:max_chars_per_line-3] + "..."
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        # Limit to maximum 3 lines
        if len(lines) > 3:
            lines = lines[:2]
            lines.append(lines[1][:max_chars_per_line-3] + "...")
        
        return lines
    
    def process_clip(self, input_path: str, clip: Dict[str, Any], 
                    subtitle_data: List[Dict] = None, 
                    enable_subtitles: bool = False,
                    burn_subtitles: bool = False,
                    background_type: str = "blurred",
                    font_file: str = "C:/Windows/Fonts/arialbd.ttf",
                    enable_crop: bool = False,
                    crop_percentage: int = 10,
                    crop_from_sides: bool = True,
                    subtitle_position_y: int = 100,
                    subtitle_alignment: int = 2) -> Optional[str]:
        """Process video clip with FFmpeg (ultra-fast)
        
        Args:
            background_type: 'blurred', 'gradient', or 'solid'
            enable_crop: Whether to crop the video to make it larger
            crop_percentage: Percentage to crop from each side (e.g., 10 = 10% from each side)
            crop_from_sides: If True, crop from left/right sides. If False, crop from top/bottom
            subtitle_position_y: Distance from bottom of video for subtitles (pixels)
            subtitle_alignment: Subtitle alignment (1=left, 2=center, 3=right)
        """
        try:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_rendered{ext}"
            
            if os.path.exists(output_path):
                return output_path
            
            # Get video info
            video_info = self.get_video_info(input_path)
            if not video_info:
                raise RuntimeError("Could not get video information")
            
            # Build FFmpeg command for ultra-fast processing
            cmd = [
                self.ffmpeg_path,
                "-i", input_path,
                "-y",  # Overwrite output
            ]
            
            # Create filter complex for layout with background and text overlays
            filters = []
            
            # Get video config values
            video_config = self.config.get('video', {})
            video_width = video_config.get('VIDEO_WIDTH', 1080)
            video_height = video_config.get('VIDEO_HEIGHT', 1920)
            main_video_y = video_config.get('MAIN_VIDEO_Y_POSITION', 400)
            blur_sigma_1 = video_config.get('BLUR_SIGMA_1', 10)
            blur_sigma_2 = video_config.get('BLUR_SIGMA_2', 15)
            bg_brightness = video_config.get('BACKGROUND_BRIGHTNESS', -0.1)
            gradient_color = video_config.get('GRADIENT_COLOR', '0x1a1a2e')
            solid_color = video_config.get('SOLID_BACKGROUND_COLOR', '#1a1a2e')
            
            if background_type == "blurred":
                # Create high-quality blurred background (most popular for TikTok/Shorts)
                filters.append(f"[0:v]scale={video_width}:{video_height}:force_original_aspect_ratio=increase[bg_scaled]")
                filters.append(f"[bg_scaled]crop={video_width}:{video_height}[bg_cropped]") 
                # Higher quality blur (2-pass with different sigma values for better aesthetics)
                filters.append(f"[bg_cropped]gblur=sigma={blur_sigma_1}[temp_blur]")
                filters.append(f"[temp_blur]gblur=sigma={blur_sigma_2}[temp_blurred]")
                # Slightly darken the blurred background to make main video stand out better
                filters.append(f"[temp_blurred]eq=brightness={bg_brightness}[bg_blurred]")
                
                # Scale and optionally crop main video
                if enable_crop and crop_percentage > 0:
                    if crop_from_sides:
                        # Crop from left and right sides, then scale to make video larger
                        # Calculate crop amounts as percentage of original width
                        crop_left_right = f"(iw*{crop_percentage}/100)"
                        # Crop the sides first: crop=width:height:x:y
                        filters.append(f"[0:v]crop=iw-2*{crop_left_right}:ih:{crop_left_right}:0[main_cropped]")
                        # Now scale the cropped video to fit the target width (making it larger)
                        filters.append(f"[main_cropped]scale={video_width}:-1[main_scaled]")
                    else:
                        # Crop from top and bottom sides, then scale to make video larger
                        crop_top_bottom = f"(ih*{crop_percentage}/100)"
                        # Crop the top/bottom first
                        filters.append(f"[0:v]crop=iw:ih-2*{crop_top_bottom}:0:{crop_top_bottom}[main_cropped]")
                        # Scale the cropped video to fit target width 
                        filters.append(f"[main_cropped]scale={video_width}:-1[main_scaled]")
                else:
                    # Scale main video to fit width (preserves all content) but use more vertical space
                    # This ensures no cropping while maximizing size within our layout
                    filters.append(f"[0:v]scale={video_width}:-1[main_scaled]")
                
                # Position video more centered on the page
                filters.append(f"[bg_blurred][main_scaled]overlay=(W-w)/2:{main_video_y}[composed]")
                
            elif background_type == "gradient":
                # Create animated gradient background (modern look)
                filters.append(f"color=c={gradient_color}:s={video_width}x{video_height}:d=60[gradient_bg]")
                
                # Scale and optionally crop main video
                if enable_crop and crop_percentage > 0:
                    if crop_from_sides:
                        # Crop from left and right sides, then scale to make video larger
                        crop_left_right = f"(iw*{crop_percentage}/100)"
                        filters.append(f"[0:v]crop=iw-2*{crop_left_right}:ih:{crop_left_right}:0[main_cropped]")
                        filters.append(f"[main_cropped]scale={video_width}:-1[main_scaled]")
                    else:
                        # Crop from top and bottom sides, then scale to make video larger
                        crop_top_bottom = f"(ih*{crop_percentage}/100)"
                        filters.append(f"[0:v]crop=iw:ih-2*{crop_top_bottom}:0:{crop_top_bottom}[main_cropped]")
                        filters.append(f"[main_cropped]scale={video_width}:-1[main_scaled]")
                else:
                    # Scale main video to fit width - preserves all content including webcams
                    filters.append(f"[0:v]scale={video_width}:-1[main_scaled]")
                
                # Position video more centered on the page
                filters.append(f"[gradient_bg][main_scaled]overlay=(W-w)/2:{main_video_y}[composed]")
                
            else:  # solid background
                # Simple solid color background (fastest)
                # Scale and optionally crop main video
                if enable_crop and crop_percentage > 0:
                    if crop_from_sides:
                        # Crop from left and right sides, then scale to make video larger
                        crop_left_right = f"(iw*{crop_percentage}/100)"
                        filters.append(f"[0:v]crop=iw-2*{crop_left_right}:ih:{crop_left_right}:0[main_cropped]")
                        filters.append(f"[main_cropped]scale={video_width}:-1[main_scaled]")
                    else:
                        # Crop from top and bottom sides, then scale to make video larger
                        crop_top_bottom = f"(ih*{crop_percentage}/100)"
                        filters.append(f"[0:v]crop=iw:ih-2*{crop_top_bottom}:0:{crop_top_bottom}[main_cropped]")
                        filters.append(f"[main_cropped]scale={video_width}:-1[main_scaled]")
                    filters.append(f"[main_scaled]pad={video_width}:{video_height}:(ow-iw)/2:{main_video_y}:color={solid_color}[composed]")
                else:
                    # Scale main video to fit width - preserves all content
                    filters.append(f"[0:v]scale={video_width}:-1[main_scaled]")
                    filters.append(f"[main_scaled]pad={video_width}:{video_height}:(ow-iw)/2:{main_video_y}:color={solid_color}[composed]")
            
            # Get title text first
            title_text = self._clean_title_text(clip['title'])
            
            # Check if meme style is enabled
            title_config = self.config.get('title_style', {})
            use_meme_style = title_config.get('STYLE', 'normal') == 'meme'
            
            # Get video dimensions from ffprobe output (needed for both styles)
            video_width = None
            video_height = None
            
            # Extract dimensions from video streams
            if 'streams' in video_info:
                for stream in video_info['streams']:
                    if stream.get('codec_type') == 'video':
                        video_width = stream.get('width')
                        video_height = stream.get('height')
                        break
            
            # Fallback to default dimensions if not found
            if not video_width or not video_height:
                video_width = 1080
                video_height = 1920
                print_error(f"Could not get video dimensions, using defaults: {video_width}x{video_height}")
            
            # Calculate font size for line splitting
            if use_meme_style:
                font_size_multiplier = title_config.get('FONT_SIZE_MULTIPLIER', 0.09)
                font_size = int(video_height * font_size_multiplier)
            else:
                font_size = 60  # Default font size for normal style
            
            # Now split title text based on actual font size and video width
            title_lines = self._split_title_text(title_text, font_size=font_size, video_width=video_width)
            
            # Prepare font file path for FFmpeg (needed for both styles)
            font_file_escaped = font_file.replace("\\", "/").replace(":", "\\:")
            
            current_filter = "[composed]"
            for i, line in enumerate(title_lines):
                next_filter = f"[titled_{i}]" if i < len(title_lines) - 1 else "[titled]"
                
                if use_meme_style:
                    # Use meme-style formatting
                    meme_filter = self._create_meme_title_filter(line, video_width, video_height, i, len(title_lines))
                    filters.append(f"{current_filter}drawtext={meme_filter}{next_filter}")
                else:
                    # Use original formatting with safe margins
                    line_escaped = line.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:").replace("%", "\\%")
                    
                    # Calculate horizontal margins (configurable, default 10% of video width on each side)
                    margin_percent = title_config.get('MARGIN_PERCENT', 0.10)
                    side_margin = int(video_width * margin_percent)
                    
                    # Get title positioning config
                    title_pos_config = self.config.get('title_positioning', {})
                    default_font_size = title_pos_config.get('DEFAULT_FONT_SIZE', 60)
                    
                    # Calculate Y position for each line using config values
                    if len(title_lines) == 1:
                        y_pos = title_pos_config.get('SINGLE_LINE_Y', 200)
                    elif len(title_lines) == 2:
                        y_start = title_pos_config.get('TWO_LINE_Y_START', 170)
                        y_spacing = title_pos_config.get('TWO_LINE_Y_SPACING', 70)
                        y_pos = y_start + (i * y_spacing)
                    else:
                        # Three lines
                        y_start = title_pos_config.get('THREE_LINE_Y_START', 140)
                        y_spacing = title_pos_config.get('THREE_LINE_Y_SPACING', 60)
                        y_pos = y_start + (i * y_spacing)
                    
                    # Center text horizontally with safe margins
                    # Simple centering approach that works reliably
                    x_pos = "(w-text_w)/2"
                    filters.append(f"{current_filter}drawtext=text='{line_escaped}':fontfile='{font_file_escaped}':fontsize={default_font_size}:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2:x={x_pos}:y={y_pos}{next_filter}")
                
                current_filter = f"[titled_{i}]"
            
            # Add channel name - positioned below the video with safe margins
            channel_text = f"twitch.tv/{clip['broadcaster_name']}"
            # Escape special characters for FFmpeg drawtext filter
            channel_text = channel_text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:").replace("%", "\\%")
            
            # Center channel name horizontally 
            # Simple centering approach that works reliably
            channel_x_pos = "(w-text_w)/2"
            
            # Get channel name config
            title_pos_config = self.config.get('title_positioning', {})
            channel_y_offset = title_pos_config.get('CHANNEL_NAME_Y_OFFSET', 150)
            channel_font_size = title_pos_config.get('CHANNEL_NAME_FONT_SIZE', 36)
            
            filters.append(f"[titled]drawtext=text='{channel_text}':fontfile='{font_file_escaped}':fontsize={channel_font_size}:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2:x={channel_x_pos}:y=h-{channel_y_offset}[channel_added]")
            
            # Add watermark if enabled
            watermark_filter = self._create_watermark_filter(video_width, video_height)
            if watermark_filter:
                filters.append(f"[channel_added]drawtext={watermark_filter}[watermarked]")
                current_output = "[watermarked]"
            else:
                current_output = "[channel_added]"
            
            # Add subtitle overlay if enabled (TikTok-style, positioned below main video)
            if enable_subtitles and burn_subtitles and subtitle_data:
                subtitle_file = os.path.join(self.temp_dir, f"temp_subtitles_{os.getpid()}.srt")
                if self.create_subtitle_file(subtitle_data, subtitle_file):
                    # Escape the subtitle file path for Windows
                    subtitle_file_escaped = subtitle_file.replace("\\", "/").replace(":", "\\:")
                    
                    # High-quality TikTok-style subtitles with configurable positioning
                    # Use configurable MarginV (distance from bottom) and Alignment
                    filters.append(f"{current_output}subtitles='{subtitle_file_escaped}':force_style='FontName=Arial,FontSize=12,PrimaryColour=&Hffffff,OutlineColour=&HFB5689,Outline=2,BorderStyle=1,Alignment={subtitle_alignment},MarginV={subtitle_position_y},Bold=1'[final]")
                    final_output = "[final]"
                else:
                    final_output = current_output
            else:
                final_output = current_output
            
            # Combine all filters
            filter_complex = ";".join(filters)
            
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", final_output,
                "-map", "0:a",  # Copy audio
            ])
            
            # Get encoding settings from config
            encoding_config = self.config.get('encoding', {})
            video_codec = encoding_config.get('VIDEO_CODEC', 'libx264')
            preset = encoding_config.get('PRESET', 'medium')
            crf = encoding_config.get('CRF', '18')
            framerate = encoding_config.get('FRAMERATE', '30')
            profile = encoding_config.get('PROFILE', 'high')
            tune = encoding_config.get('TUNE', 'film')
            audio_codec = encoding_config.get('AUDIO_CODEC', 'aac')
            audio_bitrate = encoding_config.get('AUDIO_BITRATE', '192k')
            max_duration = encoding_config.get('MAX_DURATION_SECONDS', 59)
            timeout = encoding_config.get('PROCESSING_TIMEOUT', 300)
            
            # Add encoding settings
            cmd.extend([
                # High-quality encoding settings
                "-c:v", video_codec,
                "-preset", preset,  # Better quality, reasonable speed
                "-crf", str(crf),  # Higher quality (lower is better, 18-20 is "visually lossless")
                "-r", str(framerate),  # Higher framerate for smoother motion
                "-profile:v", profile,  # Use high profile for better quality
                "-tune", tune,  # Tune for general film content
                
                # Better audio settings
                "-c:a", audio_codec,
                "-b:a", audio_bitrate,  # Higher audio bitrate
                
                # Performance optimizations
                "-threads", "0",  # Use all CPU threads
                "-movflags", "+faststart",  # Fast streaming start
                
                # Trim to configured duration if needed
                "-t", str(max_duration),
                
                output_path
            ])
            
            # Run FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                # Clean up temp subtitle file
                if enable_subtitles and burn_subtitles and subtitle_data:
                    try:
                        if os.path.exists(subtitle_file):
                            os.remove(subtitle_file)
                    except:
                        pass
                
                # Remove original file
                try:
                    if os.path.exists(input_path):
                        os.remove(input_path)
                except Exception as e:
                    print_error(f"Warning: Could not remove original file: {e}")
                
                print_success(f"Rendering Completed: {clip['title']}")
                return output_path
            else:
                print_error(f"FFmpeg failed: {result.stderr}")
                return None
                
        except Exception as e:
            print_error(f"Error in FFmpeg processing: {e}")
            return None
    
    def extract_audio_ffmpeg(self, video_path: str, audio_path: str) -> bool:
        """Extract audio using FFmpeg (faster than MoviePy)"""
        try:
            # Get audio processing config
            audio_config = self.config.get('audio_processing', {})
            sample_rate = audio_config.get('SAMPLE_RATE', '16000')
            audio_codec = audio_config.get('AUDIO_CODEC', 'pcm_s16le')
            channels = audio_config.get('CHANNELS', '1')
            
            # Get encoding config for timeout
            encoding_config = self.config.get('encoding', {})
            timeout = encoding_config.get('AUDIO_EXTRACTION_TIMEOUT', 60)
            
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vn",  # No video
                "-acodec", audio_codec,  # WAV format for Whisper
                "-ar", sample_rate,  # Sample rate (Whisper optimal)
                "-ac", channels,  # Mono
                "-y",  # Overwrite
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0
            
        except Exception as e:
            print_error(f"FFmpeg audio extraction failed: {e}")
            return False
    
    def get_duration(self, video_path: str) -> float:
        """Get video duration using FFmpeg"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return 0.0
            
        except Exception as e:
            print_error(f"Error getting duration: {e}")
            return 0.0