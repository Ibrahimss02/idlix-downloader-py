#!/usr/bin/env python3
"""
IDLIX M3U8 Downloader v1.0.0
Pure Python implementation with curl-cffi for Cloudflare bypass
Multi-threaded segment downloading with caching and resume support
"""

import os
import re
import sys
import json
import random
import argparse
import subprocess
import threading
import time
import signal
import atexit
import hashlib
import requests
from queue import Queue
from urllib.parse import urlparse, unquote
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
import m3u8
import pyperclip
from vtt_to_srt.vtt_to_srt import ConvertFile
from crypto_helper import CryptoJsAes, dec


# Get bundled FFmpeg path
def get_ffmpeg_path():
    """Get path to bundled FFmpeg executable"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        bundle_dir = sys._MEIPASS
        ffmpeg_path = os.path.join(bundle_dir, 'ffmpeg')
        if os.name == 'nt':  # Windows
            ffmpeg_path += '.exe'
    else:
        # Running as script
        ffmpeg_path = 'ffmpeg'
    return ffmpeg_path


# Global cleanup handler - only for incomplete downloads
cleanup_dirs = []
keep_cache = True  # Global flag to preserve cache

def cleanup_temp_dirs():
    """Clean up temporary directories on exit (only if incomplete)"""
    if not keep_cache:
        import shutil
        for temp_dir in cleanup_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    print(f"\n✓ Cleaned up: {temp_dir}")
                except:
                    pass

# Register cleanup handler
atexit.register(cleanup_temp_dirs)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully - keep cache for resume"""
    print("\n\n✗ Download cancelled by user")
    print("✓ Cache preserved - you can resume this download later")
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)


class IDLIXDownloader:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = cffi_requests.Session(
            impersonate=random.choice(["chrome124", "chrome119", "chrome104"]),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            verify=False  # Disable SSL verification to avoid certificate issues
        )
        
    def extract_embed_url(self, page_url):
        """Extract embed URL from IDLIX page"""
        try:
            print(f"✓ Fetching video data...")
            
            response = self.session.get(page_url)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch page (status {response.status_code})")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract video ID
            meta_counter = soup.find('meta', {'id': 'dooplay-ajax-counter'})
            if not meta_counter:
                raise Exception("Could not find video ID in page")

            video_id = meta_counter.get('data-postid')

            # Extract video title
            meta_name = soup.find('meta', {'itemprop': 'name'})
            video_title = unquote(meta_name.get('content')) if meta_name else "Unknown"
            
            print(f"✓ Video: {video_title}")

            # Get encrypted embed URL
            print(f"✓ Decrypting embed URL...")
            ajax_response = self.session.post(
                url=self.base_url + "/wp-admin/admin-ajax.php",
                data={
                    "action": "doo_player_ajax",
                    "post": video_id,
                    "nume": "1",
                    "type": "movie",
                }
            )

            if ajax_response.status_code != 200:
                raise Exception(f"AJAX request failed (status {ajax_response.status_code})")

            ajax_data = ajax_response.json()
            if not ajax_data.get('embed_url'):
                raise Exception("No embed_url in response")

            # Decrypt embed URL
            embed_url = CryptoJsAes.decrypt(
                ajax_data.get('embed_url'),
                dec(
                    ajax_data.get('key'),
                    json.loads(ajax_data.get('embed_url')).get('m')
                )
            )

            return embed_url, video_title

        except Exception as e:
            raise Exception(f"Failed to extract embed URL: {e}")
    
    def get_m3u8_info(self, embed_url):
        """Fetch M3U8 playlist info from embed URL"""
        print(f"✓ Extracting M3U8 variants...")
        
        # Extract data parameter
        if '/video/' in urlparse(embed_url).path:
            data_param = urlparse(embed_url).path.split('/')[2]
        elif '?data=' in embed_url:
            data_param = urlparse(embed_url).query.split('=')[1]
        else:
            raise Exception(f"Cannot extract data parameter from URL: {embed_url}")

        try:
            response = self.session.post(
                url='https://jeniusplay.com/player/index.php',
                params={"data": data_param, "do": "getVideo"},
                headers={
                    "Host": "jeniusplay.com",
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                },
                data={"hash": data_param, "r": self.base_url}
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get video info (status {response.status_code})")

            video_data = response.json()
            if not video_data.get('securedLink'):
                raise Exception("No securedLink in response")

            m3u8_url = video_data.get('securedLink')

            # Parse M3U8 playlist - fetch with session to avoid SSL errors
            m3u8_response = self.session.get(m3u8_url)
            if m3u8_response.status_code != 200:
                raise Exception(f"Failed to fetch M3U8 (status {m3u8_response.status_code})")
            playlist = m3u8.loads(m3u8_response.text, uri=m3u8_url)

            variants = []
            if playlist.playlists:
                for p in playlist.playlists:
                    # Extract resolution from stream info
                    resolution = p.stream_info.resolution if p.stream_info.resolution else None
                    bandwidth = p.stream_info.bandwidth if p.stream_info.bandwidth else 0

                    # Build full URL for the variant
                    # Follow reference: keep URI as-is and prepend jeniusplay.com if needed
                    if p.uri.startswith('http'):
                        stream_url = p.uri
                    elif p.uri.startswith('/'):
                        # Absolute path - prepend domain only
                        stream_url = 'https://jeniusplay.com' + p.uri
                    else:
                        # Relative path - use base URL
                        base = m3u8_url.rsplit('/', 1)[0]
                        stream_url = f"{base}/{p.uri}"

                    # Calculate quality label
                    if resolution:
                        width, height = resolution
                        quality = f"{height}p"
                        mbps = round(bandwidth / 1_000_000, 1)
                        label = f"{width}x{height} ({quality}) - {mbps} Mbps"
                    else:
                        quality = f"{round(bandwidth / 1_000_000, 1)}M"
                        label = f"{quality}"

                    variants.append({
                        'quality': quality,
                        'label': label,
                        'url': stream_url,
                        'bandwidth': bandwidth,
                        'resolution': resolution
                    })
            else:
                # Single quality
                variants.append({
                    'quality': 'default',
                    'label': 'Default quality',
                    'url': m3u8_url,
                    'bandwidth': 0,
                    'resolution': None
                })

            # Sort by bandwidth (highest first)
            variants.sort(key=lambda x: x['bandwidth'], reverse=True)

            return variants

        except Exception as e:
            raise Exception(f"Failed to get M3U8 info: {e}")
    
    def get_subtitle(self, embed_url, video_name, download=True):
        """Fetch subtitle from jeniusplay.com player API
        
        Args:
            embed_url: Embed URL from IDLIX  
            video_name: Video name for file naming
            download: If True, download and convert to SRT; if False, return URL only
            
        Returns:
            dict: {'status': bool, 'subtitle': str (path or URL), 'message': str}
        """
        try:
            # Extract data parameter from embed URL
            if '/video/' in urlparse(embed_url).path:
                data_param = urlparse(embed_url).path.split('/')[2]
            elif '?data=' in embed_url:
                data_param = urlparse(embed_url).query.split('=')[1]
            else:
                data_param = embed_url
            
            # Use POST request to the API (same as get_m3u8_info but parse HTML response)
            response = self.session.post(
                url='https://jeniusplay.com/player/index.php',
                params={"data": data_param, "do": "getVideo"},
                headers={
                    "Host": "jeniusplay.com",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                },
                data={"hash": data_param, "r": self.base_url},
                impersonate="chrome"
            )
            
            if response.status_code != 200:
                return {
                    'status': False,
                    'message': f'Failed to fetch subtitle info (status {response.status_code})'
                }
            
            # The response might be HTML with JavaScript or JSON - check both
            # Try to find subtitle in the text response
            regex_subtitle = re.search(r'var playerjsSubtitle = "(.*?)";', response.text)
            
            if not regex_subtitle:
                return {
                    'status': False,
                    'message': 'Subtitle not found in response'
                }
            
            # Extract and clean subtitle URL
            subtitle_url = regex_subtitle.group(1)
            if "https://" in subtitle_url:
                subtitle_url = "https://" + subtitle_url.split("https://")[1]
            
            if download:
                # Sanitize filename
                safe_name = re.sub(r'[<>:"/\\|?*]', '', video_name).replace(' ', '_')
                vtt_path = f"{safe_name}.vtt"
                srt_path = f"{safe_name}.srt"
                
                # Download VTT file with SSL verification disabled
                subtitle_response = requests.get(subtitle_url, timeout=30, verify=False)
                if subtitle_response.status_code == 200:
                    with open(vtt_path, 'wb') as f:
                        f.write(subtitle_response.content)
                    
                    # Convert VTT to SRT
                    self.convert_vtt_to_srt(vtt_path)
                    
                    # Clean up VTT file
                    if os.path.exists(vtt_path):
                        os.remove(vtt_path)
                    
                    return {
                        'status': True,
                        'subtitle': srt_path,
                        'message': 'Subtitle downloaded and converted'
                    }
                else:
                    return {
                        'status': False,
                        'message': f'Failed to download subtitle (status {subtitle_response.status_code})'
                    }
            else:
                # Return URL only
                return {
                    'status': True,
                    'subtitle': subtitle_url,
                    'message': 'Subtitle URL retrieved'
                }
                
        except Exception as e:
            return {
                'status': False,
                'message': f'Error fetching subtitle: {str(e)}'
            }
    
    @staticmethod
    def convert_vtt_to_srt(vtt_file):
        """Convert VTT subtitle file to SRT format
        
        Args:
            vtt_file: Path to VTT file
        """
        try:
            convert_file = ConvertFile(vtt_file, "utf-8")
            convert_file.convert()
        except Exception as e:
            print(f"Warning: Subtitle conversion failed: {e}")
    
    def download_video(self, stream_url, output_path, threads=16, progress_callback=None):
        """Download video using multi-threaded segment downloading with caching
        
        Args:
            stream_url: M3U8 stream URL
            output_path: Output file path
            threads: Number of download threads
            progress_callback: Optional callback function(progress_dict) for progress updates
        """
        cache_dir = None
        temp_dir = None
        global keep_cache
        
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and output_dir != ".":
                os.makedirs(output_dir, exist_ok=True)

            if not progress_callback:
                print(f"\n✓ Preparing download...")
            
            # Parse M3U8 to get segments - use our session for proper headers
            m3u8_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "Referer": "https://jeniusplay.com/",
                "Origin": "https://jeniusplay.com"
            }
            
            # Load M3U8 playlist - fetch with session to avoid SSL errors
            m3u8_response = self.session.get(stream_url)
            if m3u8_response.status_code != 200:
                raise Exception(f"Failed to fetch M3U8 (status {m3u8_response.status_code})")
            playlist = m3u8.loads(m3u8_response.text, uri=stream_url)
            
            if not playlist.segments:
                raise Exception("No segments found in M3U8 playlist")
            
            segments = playlist.segments
            total_segments = len(segments)
            base_url = stream_url.rsplit('/', 1)[0]
            
            # Create cache directory based on content hash
            content_hash = hashlib.md5(stream_url.encode()).hexdigest()[:16]
            cache_base = os.path.expanduser("~/.cache/idlix-downloader")
            cache_dir = os.path.join(cache_base, content_hash)
            os.makedirs(cache_dir, exist_ok=True)
            
            # Check for cached segments
            cached_count = 0
            for idx in range(total_segments):
                segment_path = os.path.join(cache_dir, f"segment_{idx:05d}.ts")
                if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0:
                    cached_count += 1
            
            if cached_count > 0:
                if not progress_callback:
                    print(f"✓ Found {cached_count}/{total_segments} cached segments - resuming download")
            
            if not progress_callback:
                print(f"✓ Total segments: {total_segments}")
                print(f"✓ Downloading with {threads} threads...")
                print(f"✓ Cache: {cache_dir}")
                print(f"✓ Output: {output_path}\n")
            
            # Register cache dir (but won't delete if keep_cache is True)
            global cleanup_dirs
            cleanup_dirs.append(cache_dir)
            
            # Progress tracking
            progress = {
                'downloaded': cached_count,  # Start from cached count
                'failed': 0,
                'bytes_downloaded': 0,
                'lock': threading.Lock(),
                'start_time': time.time(),
                'cancelled': False,
                'errors': []
            }
            
            # Calculate initial bytes from cached segments
            for idx in range(total_segments):
                segment_path = os.path.join(cache_dir, f"segment_{idx:05d}.ts")
                if os.path.exists(segment_path):
                    progress['bytes_downloaded'] += os.path.getsize(segment_path)
            
            def download_segment(segment_info):
                """Download a single segment with caching"""
                idx, segment = segment_info
                
                # Check if download was cancelled
                if progress['cancelled']:
                    return False
                
                # Check if segment is already cached
                segment_path = os.path.join(cache_dir, f"segment_{idx:05d}.ts")
                if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0:
                    return True  # Already downloaded
                
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        # Build segment URL
                        if segment.uri.startswith('http'):
                            segment_url = segment.uri
                        else:
                            segment_url = f"{base_url}/{segment.uri}"
                        
                        # Download segment
                        response = cffi_requests.get(
                            segment_url,
                            impersonate=random.choice(["chrome124", "chrome119", "chrome104"]),
                            timeout=30,
                            verify=False  # Disable SSL verification
                        )
                        
                        if response.status_code == 200:
                            # Save segment to cache
                            with open(segment_path, 'wb') as f:
                                f.write(response.content)
                            
                            # Update progress
                            with progress['lock']:
                                progress['downloaded'] += 1
                                progress['bytes_downloaded'] += len(response.content)
                                downloaded = progress['downloaded']
                                bytes_dl = progress['bytes_downloaded']
                                elapsed = time.time() - progress['start_time']
                                percent = (downloaded / total_segments) * 100
                                speed = (downloaded - cached_count) / elapsed if elapsed > 0 else 0
                                remaining = total_segments - downloaded
                                eta = remaining / speed if speed > 0 else 0
                                
                                # Calculate download speed in MB/s
                                mb_downloaded = bytes_dl / (1024 * 1024)
                                dl_speed = (bytes_dl - progress.get('initial_bytes', 0)) / (1024 * 1024) / elapsed if elapsed > 0 else 0
                                
                                # Send progress update via callback if provided
                                if progress_callback:
                                    progress_callback({
                                        'status': 'downloading',
                                        'percent': percent,
                                        'downloaded_segments': downloaded,
                                        'total_segments': total_segments,
                                        'failed_segments': progress['failed'],
                                        'speed_mbps': dl_speed,
                                        'speed_segments': speed,
                                        'eta_seconds': int(eta),
                                        'bytes_downloaded': bytes_dl,
                                        'errors': progress['errors'].copy()
                                    })
                                else:
                                    # Progress bar for CLI
                                    bar_length = 40
                                    filled = int(bar_length * percent / 100)
                                    bar = '█' * filled + '░' * (bar_length - filled)
                                    
                                    print(f'\r[{bar}] {percent:.1f}% | {downloaded}/{total_segments} | {speed:.1f} seg/s | {dl_speed:.2f} MB/s | ETA: {int(eta)}s    ', end='', flush=True)
                            
                            return True
                        else:
                            if retry == max_retries - 1:
                                with progress['lock']:
                                    progress['failed'] += 1
                                    progress['errors'].append(f"Segment {idx}: HTTP {response.status_code}")
                                return False
                            time.sleep(1)  # Wait before retry
                            
                    except Exception as e:
                        if retry == max_retries - 1:
                            with progress['lock']:
                                progress['failed'] += 1
                                progress['errors'].append(f"Segment {idx}: {str(e)}")
                            return False
                        time.sleep(1)  # Wait before retry
                
                return False
            
            # Store initial bytes for speed calculation
            progress['initial_bytes'] = progress['bytes_downloaded']
            
            # Create queue and threads - only for segments not in cache
            queue = Queue()
            for idx, segment in enumerate(segments):
                segment_path = os.path.join(cache_dir, f"segment_{idx:05d}.ts")
                if not (os.path.exists(segment_path) and os.path.getsize(segment_path) > 0):
                    queue.put((idx, segment))
            
            if queue.qsize() == 0:
                if not progress_callback:
                    print("✓ All segments already cached!\n")
                else:
                    progress_callback({
                        'status': 'downloading',
                        'percent': 100.0,
                        'downloaded_segments': total_segments,
                        'total_segments': total_segments,
                        'failed_segments': 0,
                        'speed_mbps': 0.0,
                        'speed_segments': 0.0,
                        'eta_seconds': 0,
                        'bytes_downloaded': progress['bytes_downloaded'],
                        'errors': []
                    })
            else:
                def worker():
                    while not queue.empty() and not progress['cancelled']:
                        try:
                            segment_info = queue.get(timeout=1)
                            download_segment(segment_info)
                            queue.task_done()
                        except:
                            break
                
                # Start download threads
                thread_list = []
                for _ in range(threads):
                    t = threading.Thread(target=worker)
                    t.daemon = True
                    t.start()
                    thread_list.append(t)
                
                # Wait for all downloads to complete
                try:
                    queue.join()
                except KeyboardInterrupt:
                    progress['cancelled'] = True
                    print("\n\n✗ Download cancelled, cleaning up...")
                    raise
                
                for t in thread_list:
                    t.join()
                
                if not progress_callback:
                    print("\n")
            
            if progress['cancelled']:
                return False
            
            # Show error summary if any failed
            if progress['failed'] > 0:
                if progress_callback:
                    progress_callback({
                        'status': 'failed',
                        'percent': (progress['downloaded'] / total_segments) * 100,
                        'downloaded_segments': progress['downloaded'],
                        'total_segments': total_segments,
                        'failed_segments': progress['failed'],
                        'speed_mbps': 0.0,
                        'speed_segments': 0.0,
                        'eta_seconds': 0,
                        'bytes_downloaded': progress['bytes_downloaded'],
                        'errors': progress['errors']
                    })
                else:
                    print(f"\n✗ Failed to download {progress['failed']} segments")
                    print(f"\nError details (showing first 10):")
                    for error in progress['errors'][:10]:
                        print(f"  • {error}")
                    if len(progress['errors']) > 10:
                        print(f"  ... and {len(progress['errors']) - 10} more errors")
                    print(f"\n✓ Cache preserved - run again to retry failed segments")
                return False
            
            if progress['downloaded'] != total_segments:
                if not progress_callback:
                    print(f"\n✗ Download incomplete: {progress['downloaded']}/{total_segments} segments")
                    print(f"✓ Cache preserved - run again to resume")
                return False
            
            if progress_callback:
                progress_callback({
                    'status': 'merging',
                    'percent': 100.0,
                    'downloaded_segments': total_segments,
                    'total_segments': total_segments,
                    'failed_segments': 0,
                    'speed_mbps': 0.0,
                    'speed_segments': 0.0,
                    'eta_seconds': 0,
                    'bytes_downloaded': progress['bytes_downloaded'],
                    'errors': []
                })
            else:
                print(f"✓ All segments downloaded, merging...")
            
            # Merge segments using ffmpeg from cache
            concat_file = os.path.join(cache_dir, "concat.txt")
            with open(concat_file, 'w') as f:
                for idx in range(total_segments):
                    segment_path = os.path.join(cache_dir, f"segment_{idx:05d}.ts")
                    if os.path.exists(segment_path):
                        f.write(f"file '{segment_path}'\n")
            
            # Merge with ffmpeg (with progress)
            ffmpeg_path = get_ffmpeg_path()
            merge_cmd = [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel", "warning",
                "-stats",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-bsf:a", "aac_adtstoasc",
                "-y",
                output_path
            ]
            
            if not progress_callback:
                print(f"Merging {total_segments} segments...\n")
            result = subprocess.run(merge_cmd, text=True)
            
            if result.returncode == 0:
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    elapsed = time.time() - progress['start_time']
                    
                    # Calculate actual download time and bytes (excluding cached)
                    actual_bytes = progress['bytes_downloaded'] - progress['initial_bytes']
                    avg_speed = (actual_bytes / (1024 * 1024)) / elapsed if elapsed > 0 and actual_bytes > 0 else 0
                    
                    if progress_callback:
                        progress_callback({
                            'status': 'completed',
                            'percent': 100.0,
                            'downloaded_segments': total_segments,
                            'total_segments': total_segments,
                            'failed_segments': 0,
                            'speed_mbps': avg_speed,
                            'speed_segments': 0.0,
                            'eta_seconds': 0,
                            'bytes_downloaded': progress['bytes_downloaded'],
                            'file_size': int(file_size * 1024 * 1024),
                            'errors': []
                        })
                    else:
                        print(f"\n✓ Download completed: {output_path}")
                        print(f"✓ File size: {file_size:.2f} MB")
                        if avg_speed > 0:
                            print(f"✓ Average speed: {avg_speed:.2f} MB/s")
                        print(f"✓ Time elapsed: {int(elapsed)}s")
                    
                    # Cleanup cache after successful merge
                    import shutil
                    if cache_dir in cleanup_dirs:
                        cleanup_dirs.remove(cache_dir)
                    keep_cache = False  # Allow cleanup
                    shutil.rmtree(cache_dir, ignore_errors=True)
                    if not progress_callback:
                        print(f"✓ Cache cleaned")
                    
                    return True
                else:
                    if not progress_callback:
                        print(f"\n✗ Merge failed: File is empty or doesn't exist")
                    return False
            else:
                if not progress_callback:
                    print(f"\n✗ Merge failed (ffmpeg error code: {result.returncode})")
                return False

        except KeyboardInterrupt:
            # Keep cache for resume
            raise
        except Exception as e:
            if not progress_callback:
                print(f"\n✗ Download error: {e}")
            return False

# Helper functions for interactive mode

def extract_base_url(movie_url):
    """Extract base URL from movie URL"""
    parsed = urlparse(movie_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_movie_url():
    """Prompt user for movie URL"""
    print("\n" + "="*80)
    print("IDLIX M3U8 Downloader v1.0.0")
    print("="*80)
    
    url = input("\nMovie URL: ").strip()
    if not url:
        print("✗ URL is required")
        sys.exit(1)
    
    print(f"Movie URL: {url}\n")
    return url


def print_variants(variants):
    """Print available video quality variants"""
    print(f"\nAvailable variants:")
    for i, variant in enumerate(variants, 1):
        print(f"[{i}] {variant['label']}")


def select_variant(variants):
    """Interactive variant selection"""
    while True:
        try:
            choice = input(f"\nSelect variant [1-{len(variants)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(variants):
                return variants[idx]
            else:
                print(f"✗ Please enter a number between 1 and {len(variants)}")
        except ValueError:
            print(f"✗ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\n✗ Cancelled by user")
            sys.exit(0)


def get_output_filename(video_title):
    """Prompt for output directory and filename"""
    print(f"\nDownload directory [./ for current]: ", end="")
    output_dir = input().strip()
    if not output_dir:
        output_dir = "./"
    
    # Sanitize video title for filename
    safe_title = re.sub(r'[<>:"/\\|?*]', '', video_title)
    default_name = f"{safe_title}.mp4"
    
    print(f"Custom filename [{default_name}]: ", end="")
    custom_name = input().strip()
    
    filename = custom_name if custom_name else default_name
    if not filename.endswith('.mp4'):
        filename += '.mp4'
    
    return os.path.join(output_dir, filename)


def interactive_mode():
    """Interactive mode with menu"""
    try:
        # Get movie URL (base URL auto-detected)
        movie_url = get_movie_url()
        base_url = extract_base_url(movie_url)
        
        # Initialize downloader
        downloader = IDLIXDownloader(base_url)
        
        # Extract embed URL and video info
        embed_url, video_title = downloader.extract_embed_url(movie_url)
        
        # Get M3U8 variants
        variants = downloader.get_m3u8_info(embed_url)
        
        # Show available variants
        print_variants(variants)
        
        # Select variant
        selected = select_variant(variants)
        
        print(f"\n✓ M3U8 URL: {selected['url']}")
        
        # Check for subtitles
        print(f"\n✓ Checking for subtitles...")
        subtitle_info = downloader.get_subtitle(embed_url, video_title, download=False)
        if subtitle_info['status']:
            print(f"✓ Subtitles available")
        else:
            print(f"✗ Subtitles not available: {subtitle_info['message']}")
        
        # Action menu
        print(f"\nWhat would you like to do?")
        print(f"[1] Copy M3U8 URL to clipboard")
        print(f"[2] Download video")
        print(f"[3] Show JSON output")
        
        while True:
            try:
                choice = input(f"\nChoice [1-3]: ").strip()
                
                if choice == "1":
                    pyperclip.copy(selected['url'])
                    print(f"\n✓ M3U8 URL copied to clipboard!")
                    break
                
                elif choice == "2":
                    output_path = get_output_filename(video_title)
                    
                    # Download subtitle if available
                    subtitle_path = None
                    if subtitle_info['status']:
                        print(f"\n✓ Downloading subtitle...")
                        subtitle_dir = os.path.dirname(output_path) or "./"
                        safe_title = re.sub(r'[<>:"/\\|?*]', '', video_title).replace(' ', '_')
                        subtitle_output = os.path.join(subtitle_dir, f"{safe_title}.srt")
                        
                        subtitle_result = downloader.get_subtitle(embed_url, video_title, download=True)
                        if subtitle_result['status']:
                            # Move subtitle to output directory
                            if os.path.exists(subtitle_result['subtitle']):
                                if subtitle_result['subtitle'] != subtitle_output:
                                    os.makedirs(subtitle_dir, exist_ok=True)
                                    import shutil
                                    shutil.move(subtitle_result['subtitle'], subtitle_output)
                                else:
                                    subtitle_output = subtitle_result['subtitle']
                                subtitle_path = subtitle_output
                                print(f"✓ Subtitle saved: {subtitle_path}")
                        else:
                            print(f"✗ Subtitle download failed: {subtitle_result['message']}")
                    
                    # Download video
                    success = downloader.download_video(selected['url'], output_path, threads=16)
                    if success:
                        print(f"\n✓ Video saved successfully!")
                        if subtitle_path:
                            print(f"✓ Subtitle saved successfully!")
                    sys.exit(0 if success else 1)
                
                elif choice == "3":
                    output = {
                        'title': video_title,
                        'embed_url': embed_url,
                        'variants': variants
                    }
                    print(f"\n{json.dumps(output, indent=2)}")
                    break
                
                else:
                    print(f"✗ Invalid choice. Please enter 1, 2, or 3.")
            
            except KeyboardInterrupt:
                print("\n\n✗ Cancelled by user")
                sys.exit(0)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='IDLIX M3U8 Downloader with Resume Support')
    parser.add_argument('-u', '--url', help='Movie page URL')
    parser.add_argument('-b', '--base-url', help='Base IDLIX URL (auto-detected from movie URL if not provided)')
    parser.add_argument('-q', '--quality', help='Preferred quality (e.g., 1080p, 720p)')
    parser.add_argument('-o', '--output', help='Output directory', default='./')
    parser.add_argument('-n', '--name', help='Output filename')
    parser.add_argument('-t', '--threads', type=int, default=16, help='Number of download threads (default: 16)')
    parser.add_argument('--json', action='store_true', help='Output JSON with all variants')
    parser.add_argument('--auto', action='store_true', help='Auto-select highest quality')
    parser.add_argument('--no-subtitles', action='store_true', help='Skip subtitle download')
    parser.add_argument('--api-server', action='store_true', help='Run as API server for Electron integration')
    parser.add_argument('--port', type=int, default=0, help='API server port (0 = auto-assign, default: 0)')
    
    args = parser.parse_args()
    
    # API server mode
    if args.api_server:
        try:
            import uvicorn
            from backend.api_server import app
            
            # Find a free port if port is 0
            if args.port == 0:
                import socket
                sock = socket.socket()
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
                sock.close()
            else:
                port = args.port
            
            # Output port info for Electron to parse
            print(json.dumps({"status": "ready", "port": port}), flush=True)
            
            # Run uvicorn server
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=port,
                log_level="warning",
                access_log=False
            )
            return
        except ImportError as e:
            print(json.dumps({"status": "error", "message": f"API dependencies not installed: {e}"}), flush=True)
            sys.exit(1)
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}), flush=True)
            sys.exit(1)
    
    # If no URL provided, run interactive mode
    if not args.url:
        interactive_mode()
        return
    
    try:
        # Auto-detect base URL if not provided
        base_url = args.base_url or extract_base_url(args.url)
        
        downloader = IDLIXDownloader(base_url)
        
        # Extract embed URL and video info
        embed_url, video_title = downloader.extract_embed_url(args.url)
        
        # Get M3U8 variants
        variants = downloader.get_m3u8_info(embed_url)
        
        # JSON output mode
        if args.json:
            output = {
                'title': video_title,
                'embed_url': embed_url,
                'variants': variants
            }
            print(json.dumps(output, indent=2))
            return
        
        # Select quality
        selected = None
        if args.quality:
            # Find matching quality
            for v in variants:
                if args.quality.lower() in v['quality'].lower():
                    selected = v
                    break
            if not selected:
                print(f"✗ Quality '{args.quality}' not found. Available:")
                print_variants(variants)
                sys.exit(1)
        elif args.auto:
            # Select highest quality (first in sorted list)
            selected = variants[0]
        else:
            # Interactive selection
            print_variants(variants)
            selected = select_variant(variants)
        
        print(f"\n✓ Selected: {selected['label']}")
        print(f"✓ M3U8 URL: {selected['url']}")
        
        # Determine output path
        if args.name:
            filename = args.name if args.name.endswith('.mp4') else f"{args.name}.mp4"
        else:
            safe_title = re.sub(r'[<>:"/\\|?*]', '', video_title)
            filename = f"{safe_title}.mp4"
        
        output_path = os.path.join(args.output, filename)
        
        # Download subtitle if not disabled
        if not args.no_subtitles:
            print(f"\n✓ Checking for subtitles...")
            subtitle_result = downloader.get_subtitle(embed_url, video_title, download=True)
            if subtitle_result['status']:
                # Move subtitle to output directory
                subtitle_dir = os.path.dirname(output_path) or "./"
                safe_title = re.sub(r'[<>:"/\\|?*]', '', video_title).replace(' ', '_')
                subtitle_output = os.path.join(subtitle_dir, f"{safe_title}.srt")
                
                if os.path.exists(subtitle_result['subtitle']):
                    if subtitle_result['subtitle'] != subtitle_output:
                        os.makedirs(subtitle_dir, exist_ok=True)
                        import shutil
                        shutil.move(subtitle_result['subtitle'], subtitle_output)
                    else:
                        subtitle_output = subtitle_result['subtitle']
                    print(f"✓ Subtitle saved: {subtitle_output}")
            else:
                print(f"✗ Subtitles not available: {subtitle_result['message']}")
        
        # Download
        success = downloader.download_video(selected['url'], output_path, threads=args.threads)
        sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
