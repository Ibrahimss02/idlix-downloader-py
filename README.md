# IDLIX Video Downloader

Fast Python CLI for downloading videos from IDLIX streaming platform.

## Features

- ⚡ Fast Python-based CLI
- 🔓 Bypasses Cloudflare protection
- 📊 Interactive quality selection
- 🎯 Automatic quality matching
- 📁 N_m3u8DL-CLI integration
- 💾 Clean output naming

## Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Make executable
chmod +x idlix.py
```

Or use the installation script:
```bash
./install.sh
```

## Requirements

- Python 3.8+
- curl-cffi (Cloudflare bypass)
- beautifulsoup4 (HTML parsing)
- pycryptodome (AES decryption)
- m3u8 (Playlist parsing)
- lxml (XML parser)
- **N_m3u8DL-CLI** (for downloading - optional)

### Installing N_m3u8DL-CLI

Download from: https://github.com/nilaoda/N_m3u8DL-CLI

Or use ffmpeg as alternative:
```bash
ffmpeg -i "STREAM_URL" -c copy output.mp4
```

## Usage

### Interactive Mode (Recommended)

```bash
# Full interactive experience
./idlix.py -u "https://tv10.idlixku.com/movie/example/"

# You'll see:
# ============================================================
# 📊 Available Quality Options
# ============================================================
#   [0]   1280x720  (  0.7 Mbps)
#   [1]  1920x1080  (  1.7 Mbps)
# ============================================================
# 
# 🎯 Select quality [0-1] (default: 0):
```

### Automatic Quality Selection

```bash
# Specify quality directly
./idlix.py -u "URL" -q 1080p
./idlix.py -u "URL" -q 720p
./idlix.py -u "URL" -q 0    # Select by index
```

### Advanced Options

```bash
# Custom output directory
./idlix.py -u "URL" -o ~/Downloads

# Use direct embed URL (skip extraction)
./idlix.py -e "https://jeniusplay.com/player/index.php?data=xxx"

# Show stream URL without downloading
./idlix.py -u "URL" --no-download

# Extract embed URL only
./idlix.py -u "URL" --extract-only

# Custom base URL
./idlix.py -u "URL" -b "https://tv10.idlixku.com/"
```

## Quality Formats

Quality can be specified as:
- **Resolution**: `1080p`, `720p`, `480p`
- **Exact**: `1920x1080`, `1280x720`
- **Index**: `0`, `1`, `2` (0 is highest quality)

## Examples

```bash
# Interactive download
./idlix.py -u "https://tv10.idlixku.com/movie/harry-potter-2009/"

# Auto-select 1080p, save to Downloads
./idlix.py -u "URL" -q 1080p -o ~/Downloads

# Just show stream URL (no download)
./idlix.py -u "URL" --no-download

# Extract embed URL for later use
./idlix.py -u "URL" --extract-only

# Use extracted embed URL directly
./idlix.py -e "https://jeniusplay.com/player/index.php?data=xxx" -q 720p
```

## How It Works

1. 🔍 Fetches IDLIX page using Chrome-like requests (curl-cffi)
2. 📋 Extracts video ID from HTML metadata
3. �� Requests encrypted embed URL from API
4. 🔓 Decrypts embed URL using AES
5. 📊 Fetches M3U8 playlist from JeniusPlay
6. 🎯 Shows interactive quality selector
7. ⬇️ Downloads with N_m3u8DL-CLI (or shows URL)

## Interactive Quality Selection

The tool provides a beautiful interactive interface:

```
============================================================
📊 Available Quality Options
============================================================
  [0]   1280x720  (  0.7 Mbps)
  [1]  1920x1080  (  1.7 Mbps)
============================================================

🎯 Select quality [0-1] (default: 0): 1
✅ Selected: 1920x1080 (1.7 Mbps)

⬇️  Starting download...
📁 Output: ./Harry Potter and the Half-Blood Prince (2009).mp4
🚀 Running N_m3u8DL-CLI...
```

## N_m3u8DL-CLI Integration

The tool automatically:
- ✅ Finds N_m3u8DL-CLI in PATH
- ✅ Uses optimal settings (16 threads)
- ✅ Cleans up temporary files
- ✅ Shows progress during download
- ✅ Provides manual download command if tool not found

If N_m3u8DL-CLI is not installed, the tool shows the stream URL and manual download commands.

## Troubleshooting

### N_m3u8DL-CLI not found
```bash
# Download N_m3u8DL-CLI from:
https://github.com/nilaoda/N_m3u8DL-CLI

# Or use ffmpeg:
ffmpeg -i "STREAM_URL" -c copy output.mp4
```

### Cloudflare Error
curl-cffi handles Cloudflare automatically. If you get errors:
- Update curl-cffi: `pip3 install --upgrade curl-cffi`
- Try a different Chrome version in the code

### M3U8 URL Expired
M3U8 URLs expire after ~30 minutes. Re-extract if expired:
```bash
./idlix.py -u "URL" --extract-only  # Get fresh embed URL
./idlix.py -e "NEW_EMBED_URL"       # Use new embed URL
```

## Performance

- Extraction: ~3-5 seconds
- M3U8 fetch: ~1-2 seconds
- Success rate: ~95%
- Download speed: Limited by your connection and N_m3u8DL-CLI

## License

Apache License

## Notes

- Cloudflare bypass uses curl-cffi's Chrome emulation
- M3U8 URLs are temporary (valid ~30 minutes)
- Download requires N_m3u8DL-CLI or ffmpeg
- Interactive mode works in all terminals
