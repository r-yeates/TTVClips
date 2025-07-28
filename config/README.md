# TTVClips Configuration Guide

Complete guide to all configuration options in `config.json`.

---

## Default Settings

Core Twitch API and processing settings.

- **`CLIENT_ID`** (string): Your Twitch application client ID
  - Required for Twitch API access
  - Get from: https://dev.twitch.tv/console/apps

- **`CLIENT_SECRET`** (string): Your Twitch application client secret
  - Required for Twitch API authentication
  - Keep this secure and private

- **`CLIPS_AMOUNT`** (integer): Number of clips to process
  - `1`: Process 1 clip (testing)
  - `5`: Process 5 clips (recommended)
  - `10`: Process 10 clips (batch processing)

- **`PERIOD`** (integer): Time period for clip selection (days)
  - `1`: Last 24 hours (trending clips)
  - `7`: Last week (popular clips)
  - `30`: Last month (all-time favorites)

- **`GAME_ID`** (integer): Twitch game/category ID
  - Find game IDs at: https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/
  - `509658`: Just Chatting
  - `32982`: Grand Theft Auto V

- **`BROADCASTER_ID`** (integer): Specific broadcaster ID (optional)
  - Leave empty to get clips from all broadcasters
  - Set to focus on specific streamer

- **`UPLOAD_TO_YOUTUBE`** (boolean): Enable YouTube uploads
  - `true`: Upload processed clips to YouTube
  - `false`: Skip YouTube upload

- **`UPLOAD_TO_TIKTOK`** (boolean): Enable TikTok uploads
  - `true`: Upload processed clips to TikTok
  - `false`: Skip TikTok upload

- **`CLIPS_LANGUAGE`** (string): Language filter for clips
  - `"en"`: English clips only
  - `"es"`: Spanish clips only
  - `""`: All languages

---

## Clip Processing

Batch processing and optimization settings.

- **`BATCH_PROCESSING`** (boolean): Process clips in batches
  - `true`: Process all clips at once (faster)
  - `false`: Process clips one by one (safer)

---

## Subtitles

AI-powered subtitle generation and styling.

- **`ENABLE_SUBTITLES`** (boolean): Enable subtitle generation
  - `true`: Generate subtitles using Whisper AI
  - `false`: No subtitles

- **`WHISPER_MODEL_SIZE`** (string): Whisper AI model size
  - `"tiny"`: Fastest, least accurate
  - `"base"`: Good balance
  - `"small"`: Better accuracy
  - `"medium"`: High accuracy (recommended)
  - `"large"`: Best accuracy, slowest

- **`SUBTITLE_LANGUAGE`** (string): Subtitle language
  - `"en"`: English
  - `"es"`: Spanish
  - `"fr"`: French

- **`BURN_SUBTITLES`** (boolean): Burn subtitles into video
  - `true`: Subtitles permanently embedded (TikTok style)
  - `false`: Separate subtitle file

- **`SUBTITLE_FONT_SIZE`** (integer): Subtitle text size
  - `24`: Small text
  - `32`: Medium text (recommended)
  - `48`: Large text

- **`SUBTITLE_COLOR`** (string): Subtitle text color
  - `"white"`: White text (most readable)
  - `"yellow"`: Yellow text
  - `"#FF0000"`: Custom hex color

- **`SUBTITLE_OUTLINE_COLOR`** (string): Subtitle outline color
  - `"black"`: Black outline (recommended)
  - `"#000000"`: Custom hex color

- **`FONT_FILE`** (string): Font file path for subtitles
  - Path to .ttf font file
  - Default: Arial Bold

- **`SUBTITLE_UPPERCASE`** (boolean): Convert subtitles to uppercase
  - `true`: ALL CAPS (TikTok style)
  - `false`: Normal case

- **`SUBTITLE_MAX_WORDS_PER_CHUNK`** (integer): Words per subtitle line
  - `3`: Short, punchy lines (recommended)
  - `5`: Longer lines
  - `8`: Full sentences

- **`SUBTITLE_MIN_DURATION`** (float): Minimum subtitle display time
  - `0.5`: Half second minimum
  - `1.0`: One second minimum

- **`SUBTITLE_POSITION_Y`** (integer): Distance from bottom of video (pixels)
  - `50`: Very close to bottom
  - `100`: Standard position (recommended)
  - `200`: Higher up on screen

- **`SUBTITLE_ALIGNMENT`** (integer): Horizontal alignment
  - `1`: Left-aligned subtitles
  - `2`: Center-aligned subtitles (recommended)
  - `3`: Right-aligned subtitles

---

## Title Style

Title text appearance and positioning.

- **`STYLE`** (string): Title styling mode
  - `"normal"`: Clean, simple text
  - `"meme"`: Bold meme-style text with borders

- **`FONT_SIZE_MULTIPLIER`** (float): Font size relative to video height
  - `0.05`: Small text (5% of video height)
  - `0.08`: Medium text
  - `0.12`: Large text

- **`BORDER_WIDTH`** (integer): Text border thickness (meme style)
  - `3`: Thin border
  - `5`: Medium border (recommended)
  - `8`: Thick border

- **`TEXT_COLOR`** (string): Title text color
  - `"white"`: White text (most readable)
  - `"yellow"`: Yellow text
  - `"#FF0000"`: Custom hex color

- **`BORDER_COLOR`** (string): Title border color
  - `"black"`: Black border (recommended)
  - `"#000000"`: Custom hex color

- **`ADD_SHADOW`** (boolean): Add text shadow
  - `true`: Add shadow for better readability
  - `false`: No shadow

- **`SHADOW_OFFSET`** (integer): Shadow distance in pixels
  - `2`: Subtle shadow
  - `4`: Prominent shadow

- **`SHADOW_COLOR`** (string): Shadow color with transparency
  - `"black@0.5"`: 50% transparent black
  - `"black@0.8"`: 80% transparent black

- **`MARGIN_PERCENT`** (float): Text margin from video edges
  - `0.08`: 8% margin (tight)
  - `0.10`: 10% margin (recommended)
  - `0.15`: 15% margin (spacious)

---

## Video Processing

Video layout, cropping, and background settings.

- **`BACKGROUND_TYPE`** (string): Background style
  - `"blurred"`: Blurred version of video (most popular)
  - `"gradient"`: Solid gradient background
  - `"solid"`: Solid color background

- **`VIDEO_WIDTH`** (integer): Output video width
  - `1080`: Standard mobile width
  - `720`: Lower quality, smaller file

- **`VIDEO_HEIGHT`** (integer): Output video height
  - `1920`: Standard mobile height (9:16 ratio)
  - `1280`: Shorter format

- **`MAIN_VIDEO_Y_POSITION`** (integer): Vertical position of main video
  - `300`: Higher on screen
  - `400`: Centered (recommended)
  - `500`: Lower on screen

- **`GRADIENT_COLOR`** (string): Gradient background color
  - `"0x1a1a2e"`: Dark blue
  - `"0x000000"`: Black
  - `"0x2c3e50"`: Dark gray

- **`SOLID_BACKGROUND_COLOR`** (string): Solid background color
  - `"#1a1a2e"`: Dark blue
  - `"#000000"`: Black
  - `"#ffffff"`: White

- **`BLUR_SIGMA_1`** (integer): First blur pass intensity
  - `5`: Light blur
  - `10`: Medium blur (recommended)
  - `15`: Heavy blur

- **`BLUR_SIGMA_2`** (integer): Second blur pass intensity
  - `10`: Light blur
  - `15`: Medium blur (recommended)
  - `20`: Heavy blur

- **`BACKGROUND_BRIGHTNESS`** (float): Background brightness adjustment
  - `-0.3`: Much darker
  - `-0.1`: Slightly darker (recommended)
  - `0.0`: No change

### Video Crop Settings

Make videos larger by cropping sides - perfect for mobile viewing.

- **`ENABLE_CROP`** (boolean): Enable or disable cropping feature
  - `true`: Enable cropping to make video larger
  - `false`: Keep original video size (default behavior)

- **`CROP_PERCENTAGE`** (integer): Percentage to crop from each side
  - `10`: Crop 10% from each side (recommended for mobile)
  - `15`: Crop 15% from each side (more aggressive)
  - `5`: Crop 5% from each side (subtle crop)

- **`CROP_FROM_SIDES`** (boolean): Direction of cropping
  - `true`: Crop from left and right sides (makes video taller, good for mobile)
  - `false`: Crop from top and bottom (makes video wider)

---

## Encoding

Video and audio encoding quality settings.

- **`VIDEO_CODEC`** (string): Video compression codec
  - `"libx264"`: H.264 (widely compatible)
  - `"libx265"`: H.265 (better compression, slower)

- **`PRESET`** (string): Encoding speed vs quality trade-off
  - `"ultrafast"`: Fastest encoding, larger files
  - `"fast"`: Quick encoding
  - `"medium"`: Balanced (recommended)
  - `"slow"`: Better quality, slower encoding
  - `"veryslow"`: Best quality, very slow

- **`CRF`** (string): Constant Rate Factor (quality)
  - `"15"`: Very high quality, large files
  - `"18"`: High quality (recommended)
  - `"23"`: Standard quality
  - `"28"`: Lower quality, smaller files

- **`FRAMERATE`** (string): Output video framerate
  - `"24"`: Cinematic
  - `"30"`: Standard (recommended)
  - `"60"`: High framerate (gaming)

- **`PROFILE`** (string): H.264 profile
  - `"baseline"`: Maximum compatibility
  - `"main"`: Good compatibility
  - `"high"`: Best quality (recommended)

- **`TUNE`** (string): Encoding optimization
  - `"film"`: Live action content (recommended)
  - `"animation"`: Animated content
  - `"grain"`: Preserve film grain

- **`AUDIO_CODEC`** (string): Audio compression codec
  - `"aac"`: Standard (recommended)
  - `"mp3"`: Legacy compatibility

- **`AUDIO_BITRATE`** (string): Audio quality
  - `"128k"`: Standard quality
  - `"192k"`: High quality (recommended)
  - `"256k"`: Very high quality

- **`MAX_DURATION_SECONDS`** (integer): Maximum clip length
  - `59`: TikTok/Shorts limit
  - `120`: Extended clips
  - `300`: Long form content

- **`PROCESSING_TIMEOUT`** (integer): Processing timeout (seconds)
  - `300`: 5 minutes (recommended)
  - `600`: 10 minutes for complex clips

- **`AUDIO_EXTRACTION_TIMEOUT`** (integer): Audio extraction timeout
  - `60`: 1 minute (recommended)
  - `120`: 2 minutes for long clips

---

## Fonts

Font selection and priorities.

- **`DEFAULT_FONT_PATH`** (string): Fallback font file
  - Path to default .ttf font file
  - Used when preferred fonts not found

- **`FONT_PRIORITIES`** (array): Font preference order
  - List of font file paths in priority order
  - First available font will be used
  - Example: `["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arial.ttf"]`

---

## Title Positioning

Precise control over title text placement.

- **`DEFAULT_FONT_SIZE`** (integer): Base font size for normal style
  - `48`: Small text
  - `60`: Medium text (recommended)
  - `72`: Large text

- **`SINGLE_LINE_Y`** (integer): Y position for single-line titles
  - `150`: Higher position
  - `200`: Centered (recommended)
  - `250`: Lower position

- **`TWO_LINE_Y_START`** (integer): Starting Y position for two-line titles
  - `150`: Higher start
  - `170`: Balanced (recommended)
  - `200`: Lower start

- **`TWO_LINE_Y_SPACING`** (integer): Spacing between two title lines
  - `60`: Tight spacing
  - `70`: Standard spacing (recommended)
  - `80`: Wide spacing

- **`THREE_LINE_Y_START`** (integer): Starting Y position for three-line titles
  - `120`: Higher start
  - `140`: Balanced (recommended)
  - `160`: Lower start

- **`THREE_LINE_Y_SPACING`** (integer): Spacing between three title lines
  - `50`: Tight spacing
  - `60`: Standard spacing (recommended)
  - `70`: Wide spacing

- **`CHANNEL_NAME_Y_OFFSET`** (integer): Channel name distance from bottom
  - `120`: Closer to bottom
  - `150`: Standard (recommended)
  - `200`: Further from bottom

- **`CHANNEL_NAME_FONT_SIZE`** (integer): Channel name text size
  - `28`: Small text
  - `36`: Medium text (recommended)
  - `48`: Large text

---

## Audio Processing

Audio extraction and processing settings.

- **`SAMPLE_RATE`** (string): Audio sample rate
  - `"16000"`: Whisper AI optimal (recommended)
  - `"44100"`: CD quality
  - `"48000"`: Professional quality

- **`AUDIO_CODEC`** (string): Audio extraction codec
  - `"pcm_s16le"`: Uncompressed (recommended for AI)
  - `"mp3"`: Compressed
  - `"aac"`: Modern compressed

- **`CHANNELS`** (string): Audio channel count
  - `"1"`: Mono (recommended for AI processing)
  - `"2"`: Stereo

- **`WHISPER_CPU_THREADS`** (integer): CPU threads for Whisper AI
  - `2`: Low CPU usage
  - `4`: Balanced (recommended)
  - `8`: High performance (if available)

---

## Paths

File system paths and naming conventions.

- **`LOG_FILE`** (string): Application log file location
  - Relative or absolute path
  - Default: `"config/app.log"`

- **`YOUTUBE_COOKIES`** (string): YouTube cookies file path
  - Required for YouTube uploads
  - Default: `"config/yt_cookies.txt"`

- **`TIKTOK_COOKIES`** (string): TikTok cookies file path
  - Required for TikTok uploads
  - Default: `"config/tt_cookies.txt"`

- **`CLIPS_FOLDER`** (string): Output clips directory
  - Where processed clips are saved
  - Default: `"clips"`

- **`TEMP_SUBTITLE_PREFIX`** (string): Temporary subtitle file prefix
  - Used for subtitle processing
  - Default: `"temp_subtitles_"`

- **`TEMP_AUDIO_SUFFIX`** (string): Temporary audio file suffix
  - Used for audio extraction
  - Default: `"_audio.wav"`

- **`RENDERED_SUFFIX`** (string): Processed video file suffix
  - Added to final rendered videos
  - Default: `"_rendered.mp4"`

---

## Upload Scheduling

Automated upload timing and intervals.

- **`INITIAL_DELAY_MINUTES`** (integer): Delay before first upload
  - `15`: Quick start
  - `30`: Standard delay (recommended)
  - `60`: Longer delay

- **`INTERVAL_MINUTES`** (integer): Time between uploads
  - `15`: Frequent uploads
  - `30`: Standard interval (recommended)
  - `60`: Spaced out uploads

---

## Watermark

Channel branding and watermark settings.

- **`ENABLE_WATERMARK`** (boolean): Show watermark on videos
  - `true`: Add watermark
  - `false`: No watermark

- **`WATERMARK_TEXT`** (string): Watermark text content
  - Your channel name or brand
  - Example: `"@YourChannel"`

- **`WATERMARK_FONT_SIZE`** (integer): Watermark text size
  - `18`: Small watermark
  - `24`: Medium watermark (recommended)
  - `32`: Large watermark

- **`WATERMARK_COLOR`** (string): Watermark color with transparency
  - `"white@0.7"`: 70% transparent white (recommended)
  - `"black@0.5"`: 50% transparent black
  - `"yellow@0.8"`: 80% transparent yellow

- **`WATERMARK_POSITION`** (string): Watermark placement
  - `"bottom_left"`: Bottom left corner
  - `"bottom_right"`: Bottom right corner
  - `"top_left"`: Top left corner
  - `"top_right"`: Top right corner

- **`WATERMARK_MARGIN_X`** (integer): Horizontal margin from edge
  - `10`: Close to edge
  - `20`: Standard margin (recommended)
  - `40`: Far from edge

- **`WATERMARK_MARGIN_Y`** (integer): Vertical margin from edge
  - `10`: Close to edge
  - `20`: Standard margin (recommended)
  - `40`: Far from edge

---

## Blacklist

Channel filtering and content curation.

- **`CHANNELS`** (array): Blacklisted channel names
  - List of broadcaster names to exclude
  - Helps curate content quality
  - Example: `["unwanted_channel1", "unwanted_channel2"]`

---

## Quick Setup Examples

### Mobile-First Configuration (Recommended)
```json
{
  "video": {
    "ENABLE_CROP": true,
    "CROP_PERCENTAGE": 10,
    "CROP_FROM_SIDES": true,
    "BACKGROUND_TYPE": "blurred"
  },
  "subtitles": {
    "ENABLE_SUBTITLES": true,
    "BURN_SUBTITLES": true,
    "WHISPER_MODEL_SIZE": "small"
  }
}
```

### High Quality Configuration
```json
{
  "encoding": {
    "PRESET": "slow",
    "CRF": "15",
    "AUDIO_BITRATE": "256k"
  },
  "subtitles": {
    "WHISPER_MODEL_SIZE": "medium"
  }
}
```

### Fast Processing Configuration
```json
{
  "encoding": {
    "PRESET": "fast",
    "CRF": "23"
  },
  "subtitles": {
    "WHISPER_MODEL_SIZE": "tiny"
  }
}
```
