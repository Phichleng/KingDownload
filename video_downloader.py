#!/usr/bin/env python3
"""
TikTok Video Downloader - Enhanced Version
Command-line tool with multiple service fallbacks
"""

import os
import sys
import re
import time
from pathlib import Path
import requests
import random
import json

class TikTokDownloader:
    def __init__(self, download_path="./tiktok_downloads"):
        """Initialize the TikTok downloader"""
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        
        self.user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        ]

    def extract_video_url(self, url):
        """Extract TikTok video using multiple services"""
        services = [
            ("TikMate", self._extract_with_tikmate),
            ("SnapTik", self._extract_with_snaptik),
            ("SSSTik", self._extract_with_ssstik),
        ]
        
        for service_name, extract_func in services:
            try:
                print(f"🔗 Trying {service_name}...")
                result = extract_func(url)
                if result and result.get('direct_url'):
                    print(f"✅ {service_name} extraction successful")
                    return result
            except Exception as e:
                print(f"❌ {service_name} failed: {str(e)}")
                continue
        
        raise Exception("All extraction services failed")

    def _extract_with_tikmate(self, url):
        """Extract using TikMate service"""
        session = requests.Session()
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://tikmate.cc',
            'Referer': 'https://tikmate.cc/',
        }
        
        domains = ['https://tikmate.cc', 'https://tikmate.online', 'https://tikmate.app']
        
        for domain in domains:
            try:
                data = {'url': url}
                response = session.post(f'{domain}/download', data=data, headers=headers, timeout=30)
                response.raise_for_status()
                
                download_url = None
                title = f"TikTok_Video_{self._extract_video_id(url)}"
                
                # Try JSON response
                try:
                    result = response.json()
                    if result.get('success'):
                        download_url = result.get('url')
                        title = result.get('title', title)
                except:
                    # Parse HTML response
                    download_match = re.search(r'href="([^"]*\.mp4[^"]*)"', response.text, re.IGNORECASE)
                    if not download_match:
                        patterns = [
                            r'href="([^"]*)"[^>]*>.*?Download.*?MP4',
                            r'href="([^"]*)"[^>]*>.*?Download.*?Without.*?Watermark',
                        ]
                        for pattern in patterns:
                            download_match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                            if download_match:
                                break
                    
                    if download_match:
                        download_url = download_match.group(1)
                        title_match = re.search(r'<title>([^<]+)</title>', response.text)
                        if title_match:
                            title = title_match.group(1)
                
                if not download_url:
                    continue
                
                # Fix URL formatting
                if download_url.startswith('//'):
                    download_url = 'https:' + download_url
                elif download_url.startswith('/'):
                    download_url = domain + download_url
                elif not download_url.startswith('http'):
                    download_url = 'https://' + download_url.lstrip('/')
                
                if download_url and download_url.startswith('http'):
                    return {
                        'direct_url': download_url,
                        'title': title,
                        'filename': f"TikTok_{self._clean_filename(title)}.mp4"
                    }
                    
            except Exception as e:
                print(f"❌ {domain} failed: {str(e)}")
                continue
        
        raise Exception("All TikMate domains failed")

    def _extract_with_snaptik(self, url):
        """Extract using SnapTik service"""
        try:
            session = requests.Session()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = session.get('https://snaptik.app/', headers=headers, timeout=30)
            response.raise_for_status()
            
            form_data = {'url': url}
            response = session.post('https://snaptik.app/abc', data=form_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            patterns = [
                r'href="([^"]+)"[^>]*>.*?Download MP4',
                r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*download[^"]*"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                if match:
                    download_url = match.group(1)
                    title_match = re.search(r'<title>([^<]+)</title>', response.text)
                    title = title_match.group(1) if title_match else f"TikTok_Video_{self._extract_video_id(url)}"
                    
                    return {
                        'direct_url': download_url,
                        'title': title,
                        'filename': f"TikTok_SnapTik_{self._clean_filename(title)}.mp4"
                    }
            
            raise Exception("Download link not found")
            
        except Exception as e:
            raise Exception(f"SnapTik failed: {str(e)}")

    def _extract_with_ssstik(self, url):
        """Extract using SSSTik service"""
        try:
            session = requests.Session()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = session.get('https://ssstik.io', headers=headers, timeout=30)
            response.raise_for_status()
            
            form_data = {'id': url, 'locale': 'en', 'tt': ''}
            response = session.post('https://ssstik.io/abc', data=form_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            patterns = [
                r'href="([^"]+)"[^>]*>.*?Download Without Watermark',
                r'href="([^"]+)"[^>]*>.*?Download MP4',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                if match:
                    download_url = match.group(1)
                    title_match = re.search(r'<p[^>]*class="[^"]*maintext[^"]*"[^>]*>([^<]+)</p>', response.text)
                    title = title_match.group(1) if title_match else f"TikTok_Video_{self._extract_video_id(url)}"
                    
                    return {
                        'direct_url': download_url,
                        'title': title,
                        'filename': f"TikTok_SSSTik_{self._clean_filename(title)}.mp4"
                    }
            
            raise Exception("Download link not found")
            
        except Exception as e:
            raise Exception(f"SSSTik failed: {str(e)}")

    def download_video(self, url, custom_filename=None):
        """Download TikTok video"""
        try:
            print(f"\n🎬 Starting TikTok download: {url}")
            
            # Extract video info
            video_info = self.extract_video_url(url)
            if not video_info or not video_info.get('direct_url'):
                raise Exception("No video URL found")
            
            # Use custom filename if provided
            if custom_filename:
                filename = f"{custom_filename}.mp4"
            else:
                filename = video_info['filename']
            
            filepath = self.download_path / filename
            
            print(f"📁 Downloading: {video_info['title']}")
            print(f"💾 Saving as: {filename}")
            
            # Download the video
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Referer': 'https://www.tiktok.com/',
            }
            
            response = requests.get(video_info['direct_url'], headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percentage = (downloaded / total_size) * 100
                            print(f"\r📊 Progress: {percentage:.1f}% ({self._format_bytes(downloaded)}/{self._format_bytes(total_size)})", end='', flush=True)
            
            print(f"\n✅ Download completed: {filepath}")
            return True
            
        except Exception as e:
            print(f"\n❌ Download failed: {str(e)}")
            return False

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
        clean_name = re.sub(r'[<>:"/\\|?*]', '', filename)
        clean_name = re.sub(r'[^\w\s-]', '', clean_name)
        clean_name = re.sub(r'[-\s]+', '-', clean_name).strip('-')
        return clean_name[:50] if clean_name else 'tiktok_video'

    def _format_bytes(self, bytes_val):
        """Format bytes for display"""
        if not bytes_val or bytes_val == 0:
            return '0 B'
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} TB"

    def batch_download(self, urls):
        """Download multiple TikTok videos"""
        if not urls:
            print("❌ No URLs provided")
            return False
        
        valid_urls = [url.strip() for url in urls if url.strip()]
        
        if not valid_urls:
            print("❌ No valid URLs found")
            return False
        
        total_urls = len(valid_urls)
        print(f"\n📦 Starting batch download: {total_urls} TikTok videos")
        
        success_count = 0
        
        for i, url in enumerate(valid_urls, 1):
            print(f"\n" + "="*50)
            print(f"📥 [{i}/{total_urls}] Processing: {url}")
            
            try:
                if self.download_video(url):
                    success_count += 1
                    print(f"✅ [{i}/{total_urls}] Successfully downloaded")
                else:
                    print(f"❌ [{i}/{total_urls}] Download failed")
            except Exception as e:
                print(f"❌ [{i}/{total_urls}] Error: {str(e)}")
            
            # Add delay between downloads
            if i < total_urls:
                print("⏳ Waiting 2 seconds before next download...")
                time.sleep(2)
        
        print(f"\n" + "="*50)
        print(f"🎉 Batch download completed!")
        print(f"📊 Results: {success_count}/{total_urls} videos downloaded successfully")
        
        return success_count > 0

def main():
    """Main function for command-line usage"""
    print("🎵 Enhanced TikTok Video Downloader - Command Line")
    print("🔧 Powered by Multiple Services (TikMate, SnapTik, SSSTik)")
    print("="*50)
    
    downloader = TikTokDownloader()
    
    while True:
        print("\n🎯 Options:")
        print("1. Download single TikTok video")
        print("2. Download multiple TikTok videos")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            url = input("Enter TikTok URL: ").strip()
            if url:
                custom_name = input("Custom filename (optional): ").strip() or None
                downloader.download_video(url, custom_name)
        
        elif choice == '2':
            print("Paste TikTok URLs (one per line). Press Enter twice when finished:")
            urls = []
            while True:
                line = input()
                if line.strip() == "":
                    if len(urls) > 0:
                        break
                    else:
                        continue
                urls.append(line.strip())
            
            if urls:
                downloader.batch_download(urls)
        
        elif choice == '3':
            print("👋 Thank you for using TikTok Downloader!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        import requests
        print("✅ requests library found")
    except ImportError:
        print("❌ Error: requests library not installed")
        print("💡 Please install it using: pip install requests")
        sys.exit(1)
    
    main()