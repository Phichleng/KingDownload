"""
TikTok Video Downloader - Fixed Complete Version
Enhanced with multiple services and better error handling
"""

# EVENTLET MONKEY PATCHING MUST BE FIRST!
import eventlet
eventlet.monkey_patch()

# Now import other modules
import os
import sys
import json
import time
import uuid
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
import requests
import yt_dlp
from urllib.parse import unquote, urljoin
import random

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tiktok-fixed-downloader'
CORS(app, origins=["*"])
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

# Global variables
active_downloads = {}

class TikTokExtractor:
    """Enhanced TikTok extractor with multiple working services"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        ]

    def extract_tiktok_video(self, url):
        """Main TikTok extraction with enhanced services"""
        url = self._clean_tiktok_url(url)
        logger.info(f"Processing TikTok URL: {url}")
        
        # Try multiple services in order of reliability
        services = [
            ("TikMate", self._extract_with_tikmate),
            ("SnapTik", self._extract_with_snaptik),
            ("SSSTik", self._extract_with_ssstik),
            ("TikWM", self._extract_with_tikwm),
            ("TikFast", self._extract_with_tikfast),
        ]
        
        for service_name, extract_func in services:
            try:
                logger.info(f"Trying {service_name}...")
                result = extract_func(url)
                if result and result.get('direct_url'):
                    logger.info(f"✅ Success with {service_name}")
                    return result
            except Exception as e:
                logger.warning(f"❌ {service_name} failed: {str(e)}")
                continue
        
        # Final fallback to yt-dlp
        try:
            logger.info("Trying yt-dlp as final fallback...")
            result = self._extract_with_ytdlp(url)
            if result and result.get('direct_url'):
                logger.info("✅ Success with yt-dlp")
                return result
        except Exception as e:
            logger.warning(f"❌ yt-dlp failed: {str(e)}")
        
        raise Exception("All download methods failed. The TikTok video may be private, region-restricted, or temporarily unavailable.")

    def _extract_with_tikmate(self, url):
        """Extract using TikMate service"""
        try:
            session = requests.Session()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://tikmate.cc',
                'Referer': 'https://tikmate.cc/',
            }
            
            # Try multiple TikMate domains
            domains = [
                'https://tikmate.cc',
                'https://tikmate.online', 
                'https://tikmate.app'
            ]
            
            for domain in domains:
                try:
                    data = {'url': url}
                    response = session.post(f'{domain}/download', data=data, headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    # Try to find download link in response
                    download_url = None
                    title = f"TikTok_Video_{self._extract_video_id(url)}"
                    
                    # Check for JSON response
                    try:
                        result = response.json()
                        if result.get('success'):
                            download_url = result.get('url')
                            title = result.get('title', title)
                    except:
                        # Parse HTML response
                        patterns = [
                            r'href="([^"]*\.mp4[^"]*)"',
                            r'href="([^"]*)"[^>]*>.*?Download.*?MP4',
                            r'href="([^"]*)"[^>]*>.*?Download.*?Without.*?Watermark',
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, response.text, re.IGNORECASE)
                            if match:
                                download_url = match.group(1)
                                break
                    
                    if download_url:
                        # Fix URL formatting
                        if download_url.startswith('//'):
                            download_url = 'https:' + download_url
                        elif download_url.startswith('/'):
                            download_url = domain + download_url
                        
                        return {
                            'direct_url': download_url,
                            'title': title,
                            'filename': f"TikTok_TikMate_{self._clean_filename(title)}.mp4",
                            'filesize': None,
                            'duration': None,
                            'platform': 'tiktok',
                            'headers': {
                                'User-Agent': random.choice(self.user_agents),
                                'Referer': domain + '/',
                            },
                            'thumbnail': None,
                            'uploader': 'unknown',
                            'view_count': 0
                        }
                        
                except Exception as e:
                    logger.warning(f"TikMate domain {domain} failed: {str(e)}")
                    continue
            
            raise Exception("All TikMate domains failed")
            
        except Exception as e:
            raise Exception(f"TikMate extraction failed: {str(e)}")

    def _extract_with_snaptik(self, url):
        """Extract using SnapTik service"""
        try:
            session = requests.Session()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            # Use SnapTik
            response = session.get('https://snaptik.app/', headers=headers, timeout=30)
            response.raise_for_status()
            
            # Submit the URL
            form_data = {
                'url': url
            }
            
            response = session.post('https://snaptik.app/abc', data=form_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Look for download link
            patterns = [
                r'href="([^"]+)"[^>]*>.*?Download MP4',
                r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*download[^"]*"',
                r'download-link"[^>]*href="([^"]+)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                if match:
                    download_url = match.group(1)
                    
                    # Extract title
                    title_match = re.search(r'<title>([^<]+)</title>', response.text)
                    title = title_match.group(1) if title_match else f"TikTok_Video_{self._extract_video_id(url)}"
                    
                    return {
                        'direct_url': download_url,
                        'title': title,
                        'filename': f"TikTok_SnapTik_{self._clean_filename(title)}.mp4",
                        'filesize': None,
                        'duration': None,
                        'platform': 'tiktok',
                        'headers': {
                            'User-Agent': random.choice(self.user_agents),
                            'Referer': 'https://snaptik.app/',
                        },
                        'thumbnail': None,
                        'uploader': 'unknown',
                        'view_count': 0
                    }
            
            raise Exception("Download link not found")
            
        except Exception as e:
            raise Exception(f"SnapTik failed: {str(e)}")

    def _extract_with_ssstik(self, url):
        """Extract using SSSTik alternative method"""
        try:
            session = requests.Session()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            # Use alternative SSSTik domain
            response = session.get('https://ssstik.io', headers=headers, timeout=30)
            response.raise_for_status()
            
            # Look for the download form and submit directly
            form_data = {
                'id': url,
                'locale': 'en',
                'tt': ''  # Token might not be required
            }
            
            response = session.post('https://ssstik.io/abc', data=form_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Try to find download link with multiple patterns
            patterns = [
                r'href="([^"]+)"[^>]*>.*?Download Without Watermark',
                r'href="([^"]+)"[^>]*>.*?Download MP4',
                r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*download[^"]*"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                if match:
                    download_url = match.group(1)
                    
                    # Extract title
                    title_match = re.search(r'<p[^>]*class="[^"]*maintext[^"]*"[^>]*>([^<]+)</p>', response.text)
                    title = title_match.group(1) if title_match else f"TikTok_Video_{self._extract_video_id(url)}"
                    
                    return {
                        'direct_url': download_url,
                        'title': title,
                        'filename': f"TikTok_SSSTik_{self._clean_filename(title)}.mp4",
                        'filesize': None,
                        'duration': None,
                        'platform': 'tiktok',
                        'headers': {
                            'User-Agent': random.choice(self.user_agents),
                            'Referer': 'https://ssstik.io/',
                        },
                        'thumbnail': None,
                        'uploader': 'unknown',
                        'view_count': 0
                    }
            
            raise Exception("Download link not found")
            
        except Exception as e:
            raise Exception(f"SSSTik failed: {str(e)}")

    def _extract_with_tikwm(self, url):
        """Extract using TikWM API"""
        try:
            session = requests.Session()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'https://www.tikwm.com/',
            }
            
            data = {
                'url': url,
                'hd': 1
            }
            
            response = session.post('https://www.tikwm.com/api/', data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') != 0:
                raise Exception("API returned error")
            
            data = result.get('data', {})
            video_url = data.get('hdplay') or data.get('play')
            
            if not video_url:
                raise Exception("No video URL found")
            
            # Fix URL if it's relative
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            
            title = data.get('title', f'TikTok_Video_{self._extract_video_id(url)}')
            
            return {
                'direct_url': video_url,
                'title': title,
                'filename': f"TikTok_TikWM_{self._clean_filename(title)}.mp4",
                'filesize': None,
                'duration': data.get('duration'),
                'platform': 'tiktok',
                'headers': {
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://www.tiktok.com/',
                },
                'thumbnail': data.get('cover'),
                'uploader': data.get('author', {}).get('unique_id', 'unknown'),
                'view_count': data.get('play_count', 0)
            }
            
        except Exception as e:
            raise Exception(f"TikWM failed: {str(e)}")

    def _extract_with_tikfast(self, url):
        """Extract using TikFast API"""
        try:
            session = requests.Session()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'Origin': 'https://tikfast.org',
                'Referer': 'https://tikfast.org/',
            }
            
            data = {
                'url': url
            }
            
            response = session.post('https://tikfast.org/api/download', json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get('success'):
                raise Exception("API returned error")
            
            data = result.get('data', {})
            video_url = data.get('video_url')
            
            if not video_url:
                raise Exception("No video URL found")
            
            title = data.get('title', f'TikTok_Video_{self._extract_video_id(url)}')
            
            return {
                'direct_url': video_url,
                'title': title,
                'filename': f"TikTok_TikFast_{self._clean_filename(title)}.mp4",
                'filesize': None,
                'duration': None,
                'platform': 'tiktok',
                'headers': {
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://tikfast.org/',
                },
                'thumbnail': None,
                'uploader': 'unknown',
                'view_count': 0
            }
            
        except Exception as e:
            raise Exception(f"TikFast failed: {str(e)}")

    def _extract_with_ytdlp(self, url):
        """Extract using yt-dlp with proper TikTok configuration"""
        try:
            options = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best[height<=720]',
                'nocheckcertificate': True,
                'extract_flat': False,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.tiktok.com/',
                    'Origin': 'https://www.tiktok.com',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                },
                'extractor_args': {
                    'tiktok': {
                        'app_version': '26.2.0',
                        'manifest_app_version': '2022600040',
                    }
                },
            }
            
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise Exception("No video info extracted")
                
                # Get the best available video URL
                direct_url = info.get('url')
                if not direct_url and 'formats' in info:
                    # Try to find the best format
                    formats = info['formats']
                    video_formats = [f for f in formats if f.get('vcodec') != 'none']
                    if video_formats:
                        # Prefer formats with both video and audio
                        best_format = None
                        for fmt in video_formats:
                            if fmt.get('acodec') != 'none':
                                best_format = fmt
                                break
                        if not best_format and video_formats:
                            best_format = video_formats[0]
                        
                        if best_format:
                            direct_url = best_format['url']
                
                if not direct_url:
                    raise Exception("No playable video URL found")
                
                title = info.get('title', f'TikTok_Video_{self._extract_video_id(url)}')
                
                return {
                    'direct_url': direct_url,
                    'title': title,
                    'filename': f"TikTok_ytdlp_{self._clean_filename(title)}.mp4",
                    'filesize': info.get('filesize'),
                    'duration': info.get('duration'),
                    'platform': 'tiktok',
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                        'Referer': 'https://www.tiktok.com/',
                        'Origin': 'https://www.tiktok.com',
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Sec-Fetch-Dest': 'video',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'cross-site',
                    },
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count')
                }
                
        except Exception as e:
            raise Exception(f"yt-dlp failed: {str(e)}")

    def _clean_tiktok_url(self, url):
        """Clean and standardize TikTok URL"""
        # Remove tracking parameters
        url = re.sub(r'[?&].*$', '', url)
        
        # Handle short URLs
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
            try:
                session = requests.Session()
                headers = {'User-Agent': random.choice(self.user_agents)}
                response = session.head(url, headers=headers, allow_redirects=True, timeout=10)
                url = str(response.url)
            except:
                pass
        
        return url

    def _extract_video_id(self, url):
        """Extract TikTok video ID"""
        patterns = [
            r'tiktok\.com/.*?/video/(\d+)',
            r'tiktok\.com/@[^/]+/video/(\d+)',
            r'vm\.tiktok\.com/([a-zA-Z0-9]+)',
            r'vt\.tiktok\.com/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return str(int(time.time()))

    def _clean_filename(self, filename):
        """Clean filename for safe file operations"""
        if not filename:
            return 'tiktok_video'
        # Replace problematic characters
        clean_name = re.sub(r'[<>:"/\\|?*]', '', filename)
        clean_name = re.sub(r'[^\w\s-]', '', clean_name)
        clean_name = re.sub(r'[-\s]+', '-', clean_name).strip('-')
        return clean_name[:50] if clean_name else 'tiktok_video'

class TikTokVideoExtractor:
    """Main TikTok video extractor"""
    
    def __init__(self):
        self.tiktok_extractor = TikTokExtractor()
    
    def extract_direct_url(self, url):
        """Main extraction method"""
        platform = self.detect_platform(url)
        logger.info(f"Extracting from {platform}: {url}")
        
        if platform == 'tiktok':
            return self.tiktok_extractor.extract_tiktok_video(url)
        else:
            raise Exception("This tool only supports TikTok downloads. Please provide a TikTok URL.")
    
    def detect_platform(self, url):
        """Detect platform"""
        domain = url.lower()
        
        if any(x in domain for x in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
            return 'tiktok'
        else:
            return 'unsupported'

# Initialize extractor
extractor = TikTokVideoExtractor()

def perform_streaming(direct_url, video_info, download_id, filename):
    """Core streaming logic with improved error handling"""
    logger.info(f"Streaming from: {direct_url[:100]}...")
    
    headers = video_info.get('headers', {}).copy()
    
    # Enhanced headers for TikTok CDN
    headers.update({
        'Accept': '*/*',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive',
        'Referer': 'https://www.tiktok.com/',
        'Origin': 'https://www.tiktok.com',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    # Handle range requests
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header
    
    session = requests.Session()
    
    try:
        # Add retry logic for CDN issues
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = session.get(
                    direct_url,
                    headers=headers,
                    stream=True,
                    timeout=(10, 30),
                    allow_redirects=True,
                    verify=False
                )
                
                if response.status_code == 403:
                    if attempt < max_retries:
                        logger.warning(f"403 Forbidden, retrying... (attempt {attempt + 1})")
                        time.sleep(1)
                        continue
                    else:
                        raise Exception("Access forbidden after multiple attempts. The video may be protected or temporarily unavailable.")
                
                elif response.status_code == 404:
                    raise Exception("Video not found. It may have been deleted.")
                
                elif response.status_code >= 400:
                    raise Exception(f"HTTP {response.status_code}: {response.reason}")
                
                # If we get here, the request was successful
                break
                
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    logger.warning(f"Timeout, retrying... (attempt {attempt + 1})")
                    continue
                else:
                    raise Exception("Connection timeout after multiple attempts")
        
        total_size = int(response.headers.get('content-length', 0))
        active_downloads[download_id].update({
            'total_bytes': total_size,
            'status': 'streaming'
        })
        
        downloaded = 0
        chunk_size = 32768
        start_time = time.time()
        last_progress_time = start_time
        
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                downloaded += len(chunk)
                current_time = time.time()
                
                if current_time - last_progress_time >= 1.0 or downloaded >= total_size:
                    elapsed_time = current_time - start_time
                    speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                    percentage = (downloaded / total_size * 100) if total_size > 0 else 0
                    eta = (total_size - downloaded) / speed if speed > 0 and downloaded < total_size else 0
                    
                    progress_data = {
                        'id': download_id,
                        'status': 'streaming',
                        'downloaded_bytes': downloaded,
                        'total_bytes': total_size,
                        'speed': speed,
                        'percentage': round(percentage, 1),
                        'eta': eta
                    }
                    
                    active_downloads[download_id].update(progress_data)
                    socketio.emit('download_progress', progress_data)
                    last_progress_time = current_time
                
                yield chunk
            
            if time.time() - start_time > 300:  # 5 minute timeout
                logger.warning("Streaming timeout reached")
                break
        
        # Streaming completed successfully
        total_time = time.time() - start_time
        active_downloads[download_id].update({
            'status': 'completed',
            'total_time': total_time,
            'percentage': 100
        })
        
        socketio.emit('download_status', {
            'id': download_id,
            'status': 'completed',
            'percentage': 100,
            'total_time': total_time
        })
        
    except Exception as e:
        raise
    finally:
        session.close()

@app.route('/api/download/quick', methods=['POST'])
def quick_download():
    """Quick download endpoint for TikTok videos"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Processing quick download for: {url}")
        
        # Validate it's a TikTok URL
        platform = extractor.detect_platform(url)
        if platform != 'tiktok':
            return jsonify({'error': 'Only TikTok URLs are supported. Please provide a valid TikTok video URL.'}), 400
        
        try:
            video_info = extractor.extract_direct_url(url)
            logger.info(f"Successfully extracted: {video_info['title']}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"TikTok extraction failed: {error_msg}")
            
            # Provide user-friendly error messages
            if "private" in error_msg.lower():
                error_msg = "This TikTok video appears to be private or unavailable. Private videos cannot be downloaded."
            elif "region" in error_msg.lower():
                error_msg = "This TikTok video may be restricted in your region."
            elif "copyright" in error_msg.lower():
                error_msg = "This video cannot be downloaded due to copyright restrictions."
            else:
                error_msg = f"Failed to download TikTok video. Please try again later. Error: {error_msg}"
            
            return jsonify({'error': error_msg}), 400
        
        download_id = str(uuid.uuid4())
        
        active_downloads[download_id] = {
            'id': download_id,
            'url': url,
            'status': 'ready',
            'platform': 'tiktok',
            'title': video_info['title'],
            'filename': video_info['filename'],
            'filesize': video_info['filesize'],
            'created_at': datetime.now().isoformat(),
            'type': 'streaming'
        }
        
        return jsonify({
            'download_id': download_id,
            'stream_url': f'/api/stream/{download_id}',
            'filename': video_info['filename'],
            'filesize': video_info['filesize'],
            'title': video_info['title'],
            'platform': 'tiktok',
            'duration': video_info.get('duration'),
            'thumbnail': video_info.get('thumbnail'),
            'uploader': video_info.get('uploader'),
            'message': 'Video ready for download'
        })
        
    except Exception as e:
        logger.error(f"Quick download setup error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/stream/<download_id>')
def stream_video(download_id):
    """Streaming endpoint for TikTok videos"""
    if download_id not in active_downloads:
        return jsonify({'error': 'Download not found'}), 404
    
    download_info = active_downloads[download_id]
    url = download_info['url']
    
    logger.info(f"Starting stream for TikTok: {download_id}")
    
    def generate_stream():
        try:
            active_downloads[download_id]['status'] = 'streaming'
            socketio.emit('download_status', {
                'id': download_id,
                'status': 'streaming'
            })
            
            # Get fresh video info for streaming
            video_info = extractor.extract_direct_url(url)
            if not video_info or not video_info.get('direct_url'):
                raise Exception("No video URL available for streaming")
            
            yield from perform_streaming(
                video_info['direct_url'],
                video_info,
                download_id,
                video_info['filename']
            )
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            error_msg = f"Streaming failed: {str(e)}"
            
            if download_id in active_downloads:
                active_downloads[download_id].update({
                    'status': 'error',
                    'error': error_msg
                })
            
            socketio.emit('download_status', {
                'id': download_id,
                'status': 'error',
                'error': error_msg
            })
            
            # Return error as simple text to avoid encoding issues
            yield f"ERROR: {error_msg}".encode('utf-8')
    
    try:
        # Get initial video info
        initial_video_info = extractor.extract_direct_url(url)
        filename = initial_video_info['filename']
        filesize = initial_video_info.get('filesize')
        
        # Create response with proper encoding
        response = Response(
            stream_with_context(generate_stream()),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Range, Content-Range, Content-Length',
                'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges',
                'Accept-Ranges': 'bytes'
            }
        )
        
        if filesize and filesize > 0:
            response.headers['Content-Length'] = str(filesize)
        
        return response
        
    except Exception as e:
        logger.error(f"Stream setup failed: {str(e)}")
        return jsonify({'error': f'Stream setup failed: {str(e)}'}), 500

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get TikTok video information"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        platform = extractor.detect_platform(url)
        if platform != 'tiktok':
            return jsonify({'error': 'Only TikTok URLs are supported'}), 400
        
        try:
            video_info = extractor.extract_direct_url(url)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
        return jsonify({
            'title': video_info['title'],
            'filename': video_info['filename'],
            'filesize': video_info['filesize'],
            'duration': video_info.get('duration'),
            'platform': 'tiktok',
            'thumbnail': video_info.get('thumbnail'),
            'uploader': video_info.get('uploader'),
            'view_count': video_info.get('view_count'),
            'streaming_available': True
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/downloads', methods=['GET'])
def list_downloads():
    """Get list of downloads"""
    return jsonify({
        'active_downloads': list(active_downloads.values()),
        'total_active': len(active_downloads)
    })

@app.route('/api/downloads/clear', methods=['POST'])
def clear_downloads():
    """Clear completed downloads"""
    global active_downloads
    before_count = len(active_downloads)
    active_downloads = {
        k: v for k, v in active_downloads.items() 
        if v['status'] in ['queued', 'starting', 'streaming', 'ready']
    }
    cleared_count = before_count - len(active_downloads)
    socketio.emit('downloads_cleared')
    return jsonify({
        'message': 'Downloads cleared',
        'cleared_count': cleared_count,
        'remaining': len(active_downloads)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_downloads': len(active_downloads),
        'version': 'enhanced_tiktok_downloader',
        'services': ['TikMate', 'SnapTik', 'SSSTik', 'TikWM', 'TikFast', 'yt-dlp']
    })

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {
        'message': 'Connected to Enhanced TikTok Downloader',
        'active_downloads': len(active_downloads)
    })

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('get_downloads')
def handle_get_downloads():
    emit('downloads_update', {
        'downloads': list(active_downloads.values()),
        'total': len(active_downloads)
    })

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

def main():
    print("🎵 Enhanced TikTok Video Downloader Starting...")
    print("🔧 Services: TikMate, SnapTik, SSSTik, TikWM, TikFast, yt-dlp")
    print("="*60)
    print("READY FOR TIKTOK DOWNLOADS!")
    print("="*60)
    
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    print(f"🌐 Server: http://{host}:{port}")
    print("🚀 Using multiple extraction methods for better success rate...")
    
    # Production configuration
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            allow_unsafe_werkzeug=True,
            log_output=debug_mode
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {str(e)}")

if __name__ == '__main__':
    main()