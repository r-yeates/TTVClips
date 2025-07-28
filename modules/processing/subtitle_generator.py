"""
Subtitle generation module using faster-whisper for Twitch clip processing
Optimized for Intel N100 CPU and 16GB RAM
"""
import os
import subprocess
import tempfile
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from modules.utils.logger import print_header, print_error, print_success

class SubtitleGenerator:
    """
    Handles audio extraction, transcription, and subtitle generation for video clips
    """
    
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8", config: dict = None):
        """
        Initialize the subtitle generator
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Device to run on ("cpu" or "cuda")
            compute_type: Quantization type ("int8", "int16", "float16", "float32")
            config: Configuration dictionary for subtitle styling
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.config = config or {}
        self.model = None
        
        if WhisperModel is None:
            raise ImportError("faster-whisper not installed. Run: pip install faster-whisper")
    
    def _initialize_model(self):
        """Lazy load the Whisper model to save memory"""
        if self.model is None:
            print_header(f"Loading Whisper model: {self.model_size}")
            try:
                # Get CPU threads from config
                audio_config = self.config.get('audio_processing', {}) if self.config else {}
                cpu_threads = audio_config.get('WHISPER_CPU_THREADS', 4)
                
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=cpu_threads  # Configurable CPU threads
                )
                print_success("Whisper model loaded successfully")
            except Exception as e:
                print_error(f"Failed to load Whisper model: {e}")
                raise
    
    def extract_audio(self, video_path: str, audio_path: str = None) -> str:
        """
        Extract audio from video using ffmpeg
        
        Args:
            video_path: Path to input video file
            audio_path: Path for output audio file (optional)
            
        Returns:
            str: Path to extracted audio file
        """
        if audio_path is None:
            # Create temporary audio file
            temp_dir = tempfile.gettempdir()
            video_name = Path(video_path).stem
            audio_path = os.path.join(temp_dir, f"{video_name}_audio.wav")
        
        print_header(f"Extracting audio from {Path(video_path).name}")
        
        # Get audio processing config
        audio_config = self.config.get('audio_processing', {}) if self.config else {}
        sample_rate = audio_config.get('SAMPLE_RATE', '16000')
        audio_codec = audio_config.get('AUDIO_CODEC', 'pcm_s16le')
        channels = audio_config.get('CHANNELS', '1')
        
        # Extract audio with configurable settings (optimal for Whisper)
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', audio_codec,  # Configurable audio codec
            '-ar', sample_rate,  # Configurable sample rate
            '-ac', channels,  # Configurable channels
            '-y',  # Overwrite output
            audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print_success(f"Audio extracted to {audio_path}")
            return audio_path
        except subprocess.CalledProcessError as e:
            print_error(f"Audio extraction failed: {e.stderr}")
            raise
    
    def transcribe_audio(self, audio_path: str, language: str = None) -> List[Dict]:
        """
        Transcribe audio using faster-whisper
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr') or None for auto-detect
            
        Returns:
            List[Dict]: Transcription segments with timestamps
        """
        self._initialize_model()
        
        try:
            # Transcribe with word-level timestamps for better subtitle timing
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)  # Merge short pauses
            )
            
            transcription = []
            for segment in segments:
                segment_dict = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip(),
                    'words': []
                }
                
                # Add word-level timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        segment_dict['words'].append({
                            'start': word.start,
                            'end': word.end,
                            'word': word.word
                        })
                
                transcription.append(segment_dict)
            
            print_success(f"Transcription completed. Language: {info.language}, {len(transcription)} segments")
            return transcription
            
        except Exception as e:
            print_error(f"Transcription failed: {e}")
            raise
    
    def generate_srt(self, transcription: List[Dict], srt_path: str, max_chars_per_line: int = 40) -> str:
        """
        Generate SRT subtitle file from transcription with intelligent word-based timing
        
        Args:
            transcription: List of transcription segments
            srt_path: Output path for SRT file
            max_chars_per_line: Maximum characters per subtitle line
            
        Returns:
            str: Path to generated SRT file
        """
        print_header(f"Generating SRT subtitles: {Path(srt_path).name}")
        
        def format_timestamp(seconds: float) -> str:
            """Convert seconds to SRT timestamp format"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        def group_words_by_timing(words: List[Dict], max_chars: int, max_gap: float = 0.5) -> List[Dict]:
            """Group words into subtitle chunks based on timing and character limits"""
            if not words:
                return []
            
            groups = []
            current_group = {'words': [], 'text': '', 'start': None, 'end': None}
            
            for word in words:
                word_text = word['word'].strip()
                if not word_text:
                    continue
                
                # Calculate if adding this word would exceed character limit
                potential_text = current_group['text'] + (' ' if current_group['text'] else '') + word_text
                
                # Check for timing gap (pause between words)
                has_timing_gap = (current_group['end'] is not None and 
                                word['start'] - current_group['end'] > max_gap)
                
                # Start new group if: too long, or there's a significant pause
                if (len(potential_text) > max_chars and current_group['words']) or has_timing_gap:
                    if current_group['words']:
                        groups.append(current_group)
                    current_group = {'words': [], 'text': '', 'start': None, 'end': None}
                
                # Add word to current group
                current_group['words'].append(word)
                current_group['text'] = current_group['text'] + (' ' if current_group['text'] else '') + word_text
                current_group['start'] = word['start'] if current_group['start'] is None else current_group['start']
                current_group['end'] = word['end']
            
            # Add final group
            if current_group['words']:
                groups.append(current_group)
            
            return groups
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                
                for segment in transcription:
                    if not segment['text'].strip():
                        continue
                    
                    # Use word-level timing if available
                    if segment.get('words') and len(segment['words']) > 0:
                        # Group words intelligently based on timing and character limits
                        word_groups = group_words_by_timing(segment['words'], max_chars_per_line)
                        
                        for group in word_groups:
                            f.write(f"{subtitle_index}\n")
                            f.write(f"{format_timestamp(group['start'])} --> {format_timestamp(group['end'])}\n")
                            f.write(f"{group['text']}\n\n")
                            subtitle_index += 1
                    else:
                        # Fallback to segment-level timing (old method)
                        def split_text(text: str, max_chars: int) -> List[str]:
                            """Split text into lines respecting word boundaries"""
                            words = text.split()
                            lines = []
                            current_line = []
                            current_length = 0
                            
                            for word in words:
                                word_length = len(word) + (1 if current_line else 0)
                                
                                if current_length + word_length <= max_chars:
                                    current_line.append(word)
                                    current_length += word_length
                                else:
                                    if current_line:
                                        lines.append(' '.join(current_line))
                                    current_line = [word]
                                    current_length = len(word)
                            
                            if current_line:
                                lines.append(' '.join(current_line))
                            
                            return lines
                        
                        text_lines = split_text(segment['text'], max_chars_per_line)
                        
                        if len(text_lines) == 1:
                            f.write(f"{subtitle_index}\n")
                            f.write(f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n")
                            f.write(f"{text_lines[0]}\n\n")
                            subtitle_index += 1
                        else:
                            duration = segment['end'] - segment['start']
                            time_per_line = duration / len(text_lines)
                            
                            for i, line in enumerate(text_lines):
                                start_time = segment['start'] + (i * time_per_line)
                                end_time = segment['start'] + ((i + 1) * time_per_line)
                                
                                f.write(f"{subtitle_index}\n")
                                f.write(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n")
                                f.write(f"{line}\n\n")
                                subtitle_index += 1
            
            print_success(f"SRT file generated: {srt_path}")
            return srt_path
            
        except Exception as e:
            print_error(f"SRT generation failed: {e}")
            raise
    
    def burn_subtitles(self, video_path: str, srt_path: str, output_path: str, 
                      font_size: int = 24, font_color: str = "white", 
                      outline_color: str = "black", outline_width: int = 2,
                      font_file: str = None) -> str:
        """
        Burn subtitles into video using ffmpeg
        
        Args:
            video_path: Input video path
            srt_path: SRT subtitle file path
            output_path: Output video path
            font_size: Subtitle font size
            font_color: Subtitle text color
            outline_color: Subtitle outline color
            outline_width: Subtitle outline width
            font_file: Path to font file (optional)
            
        Returns:
            str: Path to output video with burned subtitles
        """
        print_header(f"Burning subtitles into video: {Path(output_path).name}")
        
        # Escape file paths for ffmpeg
        srt_path_escaped = srt_path.replace('\\', '\\\\').replace(':', '\\:')
        
        # Build subtitle filter with optional font file
        if font_file and os.path.exists(font_file):
            font_file_escaped = font_file.replace('\\', '\\\\').replace(':', '\\:')
            subtitle_filter = f'subtitles={srt_path_escaped}:force_style=\'FontName={Path(font_file).stem},FontFile={font_file_escaped},FontSize={font_size},PrimaryColour=&H{self._color_to_bgr(font_color)},OutlineColour=&H{self._color_to_bgr(outline_color)},Outline={outline_width},Alignment=2\''
        else:
            subtitle_filter = f'subtitles={srt_path_escaped}:force_style=\'FontSize={font_size},PrimaryColour=&H{self._color_to_bgr(font_color)},OutlineColour=&H{self._color_to_bgr(outline_color)},Outline={outline_width},Alignment=2\''
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print_success(f"Subtitles burned successfully: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print_error(f"Subtitle burning failed: {e.stderr}")
            raise
    
    def _color_to_bgr(self, color: str) -> str:
        """Convert color name to BGR hex for ffmpeg"""
        color_map = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': '0000FF',
            'green': '00FF00',
            'blue': 'FF0000',
            'yellow': '00FFFF',
            'cyan': 'FFFF00',
            'magenta': 'FF00FF'
        }
        return color_map.get(color.lower(), 'FFFFFF')
    
    def process_video_subtitles(self, video_path: str, output_dir: str = None, 
                              language: str = None, burn_subs: bool = False) -> Dict[str, str]:
        """
        Complete subtitle processing pipeline for a video
        
        Args:
            video_path: Input video path
            output_dir: Output directory (default: same as video)
            language: Language for transcription
            burn_subs: Whether to burn subtitles into video
            
        Returns:
            Dict containing paths to generated files
        """
        if output_dir is None:
            output_dir = Path(video_path).parent
        
        video_name = Path(video_path).stem
        
        # File paths
        audio_path = os.path.join(tempfile.gettempdir(), f"{video_name}_temp_audio.wav")
        srt_path = os.path.join(output_dir, f"{video_name}_subtitles.srt")
        
        results = {
            'video_path': video_path,
            'srt_path': srt_path,
            'audio_path': audio_path
        }
        
        try:
            # Extract audio
            self.extract_audio(video_path, audio_path)
            
            # Transcribe
            transcription = self.transcribe_audio(audio_path, language)
            
            # Generate SRT
            self.generate_srt(transcription, srt_path)
            
            # Optionally burn subtitles
            if burn_subs:
                subtitled_video_path = os.path.join(output_dir, f"{video_name}_with_subtitles.mp4")
                self.burn_subtitles(video_path, srt_path, subtitled_video_path)
                results['subtitled_video_path'] = subtitled_video_path
            
            return results
            
        except Exception as e:
            print_error(f"Subtitle processing failed: {e}")
            raise
        finally:
            # Cleanup temporary audio file
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model is not None:
            # faster-whisper doesn't need explicit cleanup
            self.model = None
