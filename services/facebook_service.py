"""
Facebook service for posting text and images to Facebook pages
"""

import os
import requests
import time
from typing import Dict, Any
from meta_ai_api import MetaAI
from dotenv import load_dotenv

load_dotenv()

class FacebookService:
    def __init__(self):
        self.page_token = os.getenv('META_PAGE_TOKEN')
        self.page_id = os.getenv('META_PAGE_ID')
        self.fb_email = os.getenv('FACEBOOK_EMAIL')
        self.fb_password = os.getenv('FACEBOOK_PASSWORD')
        
        if not self.page_token or not self.page_id:
            raise ValueError("META_PAGE_TOKEN or META_PAGE_ID is missing in environment variables")
        
        if not self.fb_email or not self.fb_password:
            raise ValueError("FACEBOOK_EMAIL or FACEBOOK_PASSWORD is missing in environment variables")
        
        self.base_url = "https://graph.facebook.com/v18.0"
        
        # Initialize Meta AI for image generation
        try:
            self.ai = MetaAI(fb_email=self.fb_email, fb_password=self.fb_password)
            print("✅ Meta AI initialized for image generation")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize Meta AI: {e}")
            self.ai = None
    
    def post_text(self, message: str) -> Dict[str, Any]:
        """Post a text message to the Facebook page"""
        url = f"{self.base_url}/{self.page_id}/feed"
        
        # Limit message length to Facebook's limits (around 1000 characters for safety)
        if len(message) > 1000:
            print(f"⚠️ Message too long ({len(message)} chars), truncating to 1000 chars")
            message = message[:997] + "..."
        
        params = {
            'message': message,
            'access_token': self.page_token
        }
        
        try:
            response = requests.post(url, params=params)
            
            # Check for specific Facebook API errors
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Unknown error')
                    
                    if 'access token' in error_message.lower() or 'session has expired' in error_message.lower():
                        print(f"❌ Facebook Access Token Error: {error_message}")
                        print("🔧 Please update your META_PAGE_TOKEN in the environment variables")
                        raise ValueError(f"Facebook access token expired: {error_message}")
                    else:
                        print(f"❌ Facebook API Error: {error_message}")
                        raise ValueError(f"Facebook API error: {error_message}")
                except:
                    print("❌ Failed to parse Facebook error response")
                    raise ValueError("Facebook API returned 400 Bad Request")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error posting text to Facebook: {e}")
            raise
    
    def post_image(self, image_path: str, message: str = "") -> Dict[str, Any]:
        """Post an image with optional message to the Facebook page"""
        url = f"{self.base_url}/{self.page_id}/photos"
        
        try:
            # Verify image file exists and is readable
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Check file size (Facebook limit is 4MB for photos)
            file_size = os.path.getsize(image_path)
            if file_size > 4 * 1024 * 1024:  # 4MB
                print(f"⚠️ Image file too large ({file_size} bytes), trying text-only post")
                return self.post_text(message)
            
            with open(image_path, 'rb') as image_file:
                files = {
                    'source': image_file
                }
                
                data = {
                    'message': message,
                    'access_token': self.page_token
                }
                
                print(f"📤 Posting image to Facebook (size: {file_size} bytes)")
                response = requests.post(url, files=files, data=data, timeout=30)
                
                # Check for specific Facebook API errors
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', 'Unknown error')
                        print(f"❌ Facebook API Error: {error_message}")
                        
                        # If image posting fails, try text-only post
                        print("🔄 Falling back to text-only post...")
                        return self.post_text(message)
                    except:
                        print("❌ Failed to parse Facebook error response")
                        print("🔄 Falling back to text-only post...")
                        return self.post_text(message)
                
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error posting image to Facebook: {e}")
            print("🔄 Falling back to text-only post...")
            return self.post_text(message)
        except Exception as e:
            print(f"❌ Unexpected error posting image: {e}")
            print("🔄 Falling back to text-only post...")
            return self.post_text(message)
    
    def upload_video(self, video_path: str) -> str:
        """Upload a video and return the video ID for use in posts"""
        url = f"{self.base_url}/{self.page_id}/videos"
        
        try:
            # Verify video file exists and is readable
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Check file size (Facebook limit is 1GB for videos, but we'll use 100MB for safety)
            file_size = os.path.getsize(video_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                print(f"⚠️ Video file too large ({file_size} bytes)")
                return None
            
            # Check if file is actually a video by reading first few bytes
            with open(video_path, 'rb') as f:
                header = f.read(12)
                
            # Basic video format validation
            is_valid_video = False
            if header.startswith(b'\x00\x00\x00') and b'ftyp' in header:  # MP4
                is_valid_video = True
            elif header.startswith(b'RIFF') and b'AVI' in header:  # AVI
                is_valid_video = True
            elif header.startswith(b'\x1a\x45\xdf\xa3'):  # WebM/MKV
                is_valid_video = True
            
            if not is_valid_video:
                print(f"⚠️ File doesn't appear to be a valid video format")
                return None
            
            with open(video_path, 'rb') as video_file:
                files = {
                    'source': ('video.mp4', video_file, 'video/mp4')
                }
                
                data = {
                    'published': 'false',  # Don't publish immediately, just upload
                    'access_token': self.page_token
                }
                
                print(f"📹 Uploading video to Facebook (size: {file_size} bytes)")
                response = requests.post(url, files=files, data=data, timeout=120)
                
                response.raise_for_status()
                result = response.json()
                
                video_id = result.get('id')
                if video_id:
                    print(f"✅ Video uploaded successfully! Video ID: {video_id}")
                    return video_id
                else:
                    print("❌ No video ID returned from upload")
                    return None
                
        except Exception as e:
            print(f"❌ Error uploading video: {e}")
            return None

    def post_video(self, video_path: str, message: str = "") -> Dict[str, Any]:
        """Post a video with message as a regular post (upload video first, then attach to post)"""
        try:
            # First try the simple approach - upload and publish directly with message
            url = f"{self.base_url}/{self.page_id}/videos"
            
            # Verify video file exists and is readable
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Check file size
            file_size = os.path.getsize(video_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                print(f"⚠️ Video file too large ({file_size} bytes), trying as image...")
                return self.post_image(video_path, message)
            
            # Check if file is actually a video
            with open(video_path, 'rb') as f:
                header = f.read(12)
                
            is_valid_video = False
            if header.startswith(b'\x00\x00\x00') and b'ftyp' in header:  # MP4
                is_valid_video = True
            elif header.startswith(b'RIFF') and b'AVI' in header:  # AVI
                is_valid_video = True
            elif header.startswith(b'\x1a\x45\xdf\xa3'):  # WebM/MKV
                is_valid_video = True
            
            if not is_valid_video:
                print(f"⚠️ File doesn't appear to be a valid video format, trying as image...")
                return self.post_image(video_path, message)
            
            with open(video_path, 'rb') as video_file:
                files = {
                    'source': ('video.mp4', video_file, 'video/mp4')
                }
                
                data = {
                    'description': message,  # Use description for video posts
                    'published': 'true',     # Publish immediately as a post
                    'access_token': self.page_token
                }
                
                print(f"📹 Posting video to Facebook as post (size: {file_size} bytes)")
                response = requests.post(url, files=files, data=data, timeout=120)
                
                # Check for specific Facebook API errors
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', 'Unknown error')
                        print(f"❌ Facebook API Error: {error_message}")
                        
                        # If video posting fails, try as image instead
                        print("🔄 Video posting failed, trying as image...")
                        return self.post_image(video_path, message)
                    except:
                        print("❌ Failed to parse Facebook error response")
                        print("🔄 Falling back to image post...")
                        return self.post_image(video_path, message)
                
                response.raise_for_status()
                result = response.json()
                
                # Log successful video post
                if result.get('id'):
                    print(f"✅ Video posted successfully as video post! Video ID: {result.get('id')}")
                
                return result
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error posting video to Facebook: {e}")
            print("🔄 Falling back to image post...")
            return self.post_image(video_path, message)
        except Exception as e:
            print(f"❌ Unexpected error posting video: {e}")
            print("🔄 Falling back to image post...")
            return self.post_image(video_path, message)
    
    def is_video_url(self, url: str) -> bool:
        """Check if URL points to a video file"""
        if not url:
            return False
        
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
        video_domains = ['v.redd.it', 'gfycat.com', 'imgur.com/a/', 'streamable.com']
        
        url_lower = url.lower()
        
        # Check file extensions
        if any(url_lower.endswith(ext) for ext in video_extensions):
            return True
        
        # Check video domains
        if any(domain in url_lower for domain in video_domains):
            return True
        
        return False
    
    def resolve_reddit_video_url(self, reddit_url: str) -> str:
        """Aggressively resolve Reddit video URL - SKIP HLS, prioritize direct MP4s"""
        try:
            if 'v.redd.it' not in reddit_url:
                return reddit_url
            
            print(f"🔍 Aggressively resolving Reddit video URL - PRIORITIZING DIRECT MP4s...")
            
            # Try to get the Reddit post data to find the fallback URL
            if '/DASH_' not in reddit_url and not reddit_url.endswith('.mp4'):
                # PRIORITIZE DIRECT MP4 URLs FIRST (skip problematic HLS)
                video_formats = [
                    # Fallback URLs (often have audio and work better)
                    'DASH_720.mp4?source=fallback',
                    'DASH_480.mp4?source=fallback', 
                    'DASH_360.mp4?source=fallback',
                    'DASH_240.mp4?source=fallback',
                    
                    # Direct MP4 URLs (most reliable)
                    'DASH_720.mp4',
                    'DASH_480.mp4',
                    'DASH_360.mp4', 
                    'DASH_240.mp4',
                    'DASH_96.mp4',
                    
                    # Alternative formats
                    'DASH_1080.mp4',
                    'DASH_720_v2.mp4',
                    'DASH_480_v2.mp4',
                    
                    # Try without DASH prefix
                    '720.mp4',
                    '480.mp4',
                    '360.mp4',
                    '240.mp4',
                    
                    # Try with different extensions
                    'video.mp4',
                    'video.webm',
                    'video.mov',
                    
                    # Audio streams (we can try these too)
                    'DASH_audio.mp4',
                    'audio.mp4',
                    
                    # HLS playlists LAST (problematic with yt-dlp)
                    'HLSPlaylist.m3u8',
                ]
                
                for format_name in video_formats:
                    test_url = f"{reddit_url.rstrip('/')}/{format_name}"
                    print(f"🔍 Trying format: {format_name}")
                    
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept': 'video/*,application/vnd.apple.mpegurl,*/*',
                            'Referer': 'https://www.reddit.com/',
                        }
                        
                        response = requests.head(test_url, headers=headers, timeout=10)
                        content_type = response.headers.get('content-type', '').lower()
                        content_length = response.headers.get('content-length', '0')
                        
                        # PRIORITIZE DIRECT VIDEO CONTENT OVER HLS
                        if any(vid_type in content_type for vid_type in ['video/', 'mp4', 'webm', 'mov']):
                            print(f"✅ Found DIRECT video URL: {test_url}")
                            print(f"   Content-Type: {content_type}")
                            print(f"   Content-Length: {content_length}")
                            return test_url
                        
                        # Only accept HLS if we have substantial content and no direct video found
                        elif 'mpegurl' in content_type and int(content_length) > 1000:
                            print(f"⚠️ Found HLS playlist (will try but may fail): {test_url}")
                            print(f"   Content-Type: {content_type}")
                            print(f"   Content-Length: {content_length}")
                            # Continue looking for direct MP4s, but save this as backup
                            hls_backup = test_url
                            continue
                            
                    except Exception as e:
                        print(f"⚠️ Failed to test {format_name}: {e}")
                        continue
                
                # If we found an HLS backup but no direct video, return it
                if 'hls_backup' in locals():
                    print(f"🔄 No direct MP4 found, using HLS backup: {hls_backup}")
                    return hls_backup
            
            # If direct resolution fails, return original URL anyway - let download_video handle it
            print(f"⚠️ Could not resolve Reddit video URL, but returning original to try anyway")
            return reddit_url
            
        except Exception as e:
            print(f"❌ Error resolving Reddit video URL: {e}")
            return reddit_url

    def combine_video_audio_with_ffmpeg(self, reddit_url: str) -> str:
        """Download video and audio separately, then combine with ffmpeg"""
        try:
            import subprocess
            
            print(f"🎵 ENHANCED audio combination - trying multiple audio detection methods...")
            
            # Try to find both video and audio URLs
            video_url = None
            audio_url = None
            
            # Test different video qualities and audio formats
            video_formats = ['DASH_720.mp4', 'DASH_480.mp4', 'DASH_360.mp4', 'DASH_240.mp4', 'DASH_96.mp4']
            audio_formats = ['DASH_audio.mp4', 'audio.mp4', 'DASH_AUDIO_128.mp4', 'DASH_AUDIO_64.mp4']
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'video/*,audio/*,*/*',
                'Referer': 'https://www.reddit.com/',
            }
            
            # Find video stream
            print(f"🔍 Searching for video streams...")
            for video_format in video_formats:
                test_url = f"{reddit_url.rstrip('/')}/{video_format}"
                try:
                    print(f"   Testing: {video_format}")
                    response = requests.head(test_url, headers=headers, timeout=10)
                    content_type = response.headers.get('content-type', '').lower()
                    content_length = response.headers.get('content-length', '0')
                    
                    if response.status_code == 200 and ('video/' in content_type or 'mp4' in content_type):
                        video_url = test_url
                        print(f"✅ Found video stream: {video_format} ({content_length} bytes)")
                        break
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    continue
            
            # Find audio stream - try multiple methods
            print(f"🔍 Searching for audio streams...")
            for audio_format in audio_formats:
                test_url = f"{reddit_url.rstrip('/')}/{audio_format}"
                try:
                    print(f"   Testing: {audio_format}")
                    response = requests.head(test_url, headers=headers, timeout=10)
                    content_type = response.headers.get('content-type', '').lower()
                    content_length = response.headers.get('content-length', '0')
                    
                    if response.status_code == 200 and int(content_length) > 1000:  # Must have substantial content
                        audio_url = test_url
                        print(f"✅ Found audio stream: {audio_format} ({content_length} bytes)")
                        break
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    continue
            
            if not video_url:
                print("❌ No video stream found")
                return None
            
            if not audio_url:
                print("⚠️ No audio stream found - this video may not have audio")
                # Still try to download video-only
                timestamp = int(time.time())
                print(f"📹 Downloading video-only stream...")
                video_response = requests.get(video_url, headers=headers, timeout=30, stream=True)
                video_response.raise_for_status()
                
                video_filename = f"reddit_video_only_{timestamp}.mp4"
                with open(video_filename, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(video_filename)
                print(f"📹 Downloaded video-only: {video_filename} ({file_size} bytes)")
                return video_filename
            
            timestamp = int(time.time())
            
            # Download video
            print(f"📹 Downloading video stream from: {video_url}")
            video_response = requests.get(video_url, headers=headers, timeout=30, stream=True)
            video_response.raise_for_status()
            
            video_filename = f"reddit_video_temp_{timestamp}.mp4"
            with open(video_filename, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            video_size = os.path.getsize(video_filename)
            print(f"✅ Video downloaded: {video_size} bytes")
            
            # Download audio
            print(f"🎵 Downloading audio stream from: {audio_url}")
            audio_response = requests.get(audio_url, headers=headers, timeout=30, stream=True)
            audio_response.raise_for_status()
            
            audio_filename = f"reddit_audio_temp_{timestamp}.mp4"
            with open(audio_filename, 'wb') as f:
                for chunk in audio_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            audio_size = os.path.getsize(audio_filename)
            print(f"✅ Audio downloaded: {audio_size} bytes")
            
            # Combine with ffmpeg
            output_filename = f"reddit_video_with_audio_{timestamp}.mp4"
            print(f"🔧 Combining video and audio with ffmpeg...")
            
            # Enhanced ffmpeg command with better audio handling
            ffmpeg_cmd = [
                'ffmpeg', '-y',  # -y to overwrite output file
                '-i', video_filename,  # Input video
                '-i', audio_filename,  # Input audio
                '-c:v', 'copy',  # Copy video stream (no re-encoding)
                '-c:a', 'aac',   # Re-encode audio to AAC (Facebook compatible)
                '-b:a', '128k',  # Set audio bitrate
                '-ar', '44100',  # Set audio sample rate
                '-ac', '2',      # Set audio channels to stereo
                '-shortest',     # End when shortest stream ends
                '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
                output_filename
            ]
            
            print(f"🔧 Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
            
            try:
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
                
                print(f"🔧 ffmpeg stdout: {result.stdout}")
                if result.stderr:
                    print(f"🔧 ffmpeg stderr: {result.stderr}")
                
                if result.returncode == 0:
                    # Clean up temporary files
                    try:
                        os.unlink(video_filename)
                        os.unlink(audio_filename)
                    except:
                        pass
                    
                    if os.path.exists(output_filename):
                        file_size = os.path.getsize(output_filename)
                        print(f"🎵 SUCCESS! Combined video with audio: {output_filename} ({file_size} bytes)")
                        
                        # Verify the output has audio
                        verify_cmd = ['ffprobe', '-v', 'quiet', '-show_streams', '-select_streams', 'a', output_filename]
                        try:
                            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
                            if verify_result.returncode == 0 and verify_result.stdout.strip():
                                print(f"✅ Audio stream verified in output file")
                            else:
                                print(f"⚠️ No audio stream detected in output file")
                        except:
                            print(f"⚠️ Could not verify audio stream")
                        
                        return output_filename
                    else:
                        print("❌ ffmpeg output file not found")
                        return None
                else:
                    print(f"❌ ffmpeg failed with return code: {result.returncode}")
                    print(f"❌ ffmpeg error: {result.stderr}")
                    # Clean up and return video-only
                    try:
                        os.unlink(audio_filename)
                    except:
                        pass
                    print("🔄 Returning video-only file...")
                    return video_filename
                    
            except subprocess.TimeoutExpired:
                print("❌ ffmpeg timeout")
                return video_filename
            except FileNotFoundError:
                print("⚠️ ffmpeg not found, returning video-only")
                try:
                    os.unlink(audio_filename)
                except:
                    pass
                return video_filename
                
        except Exception as e:
            print(f"❌ Error in video/audio combination: {e}")
            return None

    def download_video_with_yt_dlp(self, video_url: str) -> str:
        """Download video with audio using yt-dlp (for HLS playlists and complex formats)"""
        try:
            import yt_dlp
            
            print(f"🎵 Using yt-dlp to download video with audio...")
            
            # Create filename
            timestamp = int(time.time())
            output_template = f"reddit_video_audio_{timestamp}.%(ext)s"
            
            # More flexible yt-dlp options for Reddit videos
            ydl_opts = {
                'format': 'best/worst',  # Try best first, fallback to worst if needed
                'outtmpl': output_template,
                'quiet': True,  # Reduce noise
                'no_warnings': True,
                'extractaudio': False,  # Keep video
                'merge_output_format': 'mp4',  # Ensure output is mp4
                'writesubtitles': False,
                'writeautomaticsub': False,
                'ignoreerrors': True,  # Continue on errors
                'no_check_certificate': True,  # Skip SSL verification
                'prefer_ffmpeg': True,  # Use ffmpeg for processing
            }
            
            # Try multiple format strategies
            format_strategies = [
                'best[ext=mp4]/best[ext=webm]/best',  # Prefer mp4, then webm, then any
                'worst[ext=mp4]/worst[ext=webm]/worst',  # Try lower quality if best fails
                'best',  # Just get the best available
                'worst',  # Last resort - get anything
            ]
            
            for i, format_selector in enumerate(format_strategies):
                try:
                    print(f"🔄 yt-dlp attempt {i+1}/4 with format: {format_selector}")
                    
                    ydl_opts['format'] = format_selector
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Extract info first to check if video exists
                        info = ydl.extract_info(video_url, download=False)
                        if not info:
                            print(f"⚠️ No video info found for attempt {i+1}")
                            continue
                            
                        print(f"📹 Video found: {info.get('title', 'Unknown')[:50]}...")
                        
                        # Download the video
                        ydl.download([video_url])
                        
                        # Find the downloaded file
                        expected_filename = f"reddit_video_audio_{timestamp}.mp4"
                        if os.path.exists(expected_filename):
                            file_size = os.path.getsize(expected_filename)
                            print(f"🎵 SUCCESS! Downloaded video with audio: {expected_filename} ({file_size} bytes)")
                            return expected_filename
                        else:
                            # Look for any file with our timestamp
                            for file in os.listdir('.'):
                                if f"reddit_video_audio_{timestamp}" in file:
                                    file_size = os.path.getsize(file)
                                    print(f"🎵 SUCCESS! Downloaded video with audio: {file} ({file_size} bytes)")
                                    return file
                            
                            print(f"❌ Downloaded file not found for attempt {i+1}")
                            continue
                        
                except yt_dlp.DownloadError as e:
                    print(f"⚠️ yt-dlp attempt {i+1} failed: {e}")
                    continue
                except Exception as e:
                    print(f"⚠️ yt-dlp attempt {i+1} error: {e}")
                    continue
            
            print("❌ All yt-dlp attempts failed")
            return None
                    
        except ImportError:
            print("⚠️ yt-dlp not available, falling back to original method")
            return None
        except Exception as e:
            print(f"❌ Error with yt-dlp download: {e}")
            return None

    def download_video(self, video_url: str) -> str:
        """Download a video from URL and save locally - with ffmpeg audio combination for Reddit"""
        try:
            # For Reddit videos, try ffmpeg combination first to get audio
            if 'v.redd.it' in video_url:
                print(f"🎵 Reddit video detected - trying ffmpeg audio combination...")
                
                # Extract base URL for ffmpeg combination
                base_url = video_url.split('/DASH_')[0] if '/DASH_' in video_url else video_url.rstrip('/')
                
                # Try ffmpeg combination first
                combined_video = self.combine_video_audio_with_ffmpeg(base_url)
                if combined_video:
                    print(f"🎵 SUCCESS! Got Reddit video with audio using ffmpeg")
                    return combined_video
                
                print(f"⚠️ ffmpeg combination failed, trying standard resolution...")
                
                # Fallback to standard resolution
                resolved_url = self.resolve_reddit_video_url(video_url)
                if resolved_url != video_url:
                    video_url = resolved_url
                else:
                    print(f"⚠️ Could not resolve Reddit video URL, skipping video download")
                    return None
            
            # Check if it's an HLS playlist - use yt-dlp for these
            if 'HLSPlaylist.m3u8' in video_url or '.m3u8' in video_url:
                print(f"🎵 HLS playlist detected, using yt-dlp for audio support...")
                return self.download_video_with_yt_dlp(video_url)
            
            # For regular video URLs, use standard download
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            print(f"📹 Downloading video from: {video_url[:50]}...")
            response = requests.get(video_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            
            # Handle HLS playlists (contains audio but needs special processing)
            if 'application/x-mpegurl' in content_type or 'application/vnd.apple.mpegurl' in content_type:
                print(f"🎵 Found HLS playlist with audio, using yt-dlp...")
                return self.download_video_with_yt_dlp(video_url)
            
            # Check for valid video content types
            if not any(vid_type in content_type for vid_type in ['video/', 'mp4', 'webm', 'mov', 'avi']):
                print(f"⚠️ Invalid video content type: {content_type}")
                return None
            
            # Check content length
            content_length = int(response.headers.get('content-length', 0))
            if content_length > 100 * 1024 * 1024:  # 100MB limit
                print(f"⚠️ Video too large: {content_length} bytes")
                return None
            
            # Determine file extension from content type or URL
            if 'mp4' in content_type or video_url.lower().endswith('.mp4'):
                ext = '.mp4'
            elif 'webm' in content_type or video_url.lower().endswith('.webm'):
                ext = '.webm'
            elif 'mov' in content_type or video_url.lower().endswith('.mov'):
                ext = '.mov'
            elif 'avi' in content_type or video_url.lower().endswith('.avi'):
                ext = '.avi'
            else:
                ext = '.mp4'  # Default
            
            # Create filename
            timestamp = int(time.time())
            filename = f"reddit_video_{timestamp}{ext}"
            
            # Save video
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filename)
            print(f"📹 Downloaded video: {filename} ({file_size} bytes)")
            return filename
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error downloading video: {e}")
            return None
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            return None
    
    def download_image(self, image_url: str) -> str:
        """Download an image from URL and save locally"""
        try:
            # Skip Reddit gallery URLs - they don't contain direct images
            if 'reddit.com/gallery/' in image_url:
                print(f"⚠️ Reddit gallery URL detected, skipping: {image_url[:50]}...")
                return None
            
            # Skip other non-direct image URLs
            skip_patterns = [
                'reddit.com/r/',
                'reddit.com/user/',
                'reddit.com/comments/'
            ]
            
            # Skip redd.it URLs that don't have image extensions
            if 'redd.it' in image_url and not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                print(f"⚠️ Non-direct redd.it URL detected, skipping: {image_url[:50]}...")
                return None
            
            # Skip other non-direct URLs
            if any(skip_pattern in image_url for skip_pattern in skip_patterns):
                print(f"⚠️ Non-direct image URL detected, skipping: {image_url[:50]}...")
                return None
            
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            print(f"📥 Downloading image from: {image_url[:50]}...")
            response = requests.get(image_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'jpg', 'png', 'gif', 'webp']):
                print(f"⚠️ Invalid content type: {content_type}")
                return None
            
            # Check content length
            content_length = len(response.content)
            if content_length == 0:
                print("⚠️ Empty image content")
                return None
            
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                print(f"⚠️ Image too large: {content_length} bytes")
                return None
            
            # Determine file extension from content type or URL
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'webp' in content_type:
                ext = '.webp'
            elif image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                ext = '.' + image_url.split('.')[-1].lower()
            else:
                ext = '.jpg'  # Default
            
            # Create filename
            timestamp = int(time.time())
            filename = f"reddit_image_{timestamp}{ext}"
            
            # Save image
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"📥 Downloaded image: {filename} ({content_length} bytes)")
            return filename
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error downloading image: {e}")
            return None
        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            return None
    
    def generate_image_with_ai(self, title: str, description: str = "") -> str:
        """Generate an image using Meta AI based on news content"""
        if not self.ai:
            print("❌ Meta AI not available for image generation")
            return None
        
        try:
            # Create a descriptive prompt for image generation
            prompt = f"Generate a professional news image related to: {title}"
            
            # Add context if description is available
            if description:
                prompt += f". Context: {description[:100]}..."
            
            # Add style instructions
            prompt += ". Make it suitable for social media news post, professional and eye-catching."
            
            print(f"🎨 Generating AI image for: {title[:50]}...")
            
            # Generate image using Meta AI
            response = self.ai.prompt(message=prompt)
            
            # Check if response contains image data
            if isinstance(response, dict) and 'media' in response:
                # Handle image response
                media_data = response['media']
                if media_data and len(media_data) > 0:
                    image_url = media_data[0].get('url')
                    if image_url:
                        # Download the generated image
                        return self.download_image(image_url)
            
            # If no image in response, try to extract image URL from text response
            response_text = response.get('message', '') if isinstance(response, dict) else str(response)
            
            # Look for image URLs in the response
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, response_text)
            
            for url in urls:
                if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    print(f"🎨 Found generated image URL: {url[:50]}...")
                    return self.download_image(url)
            
            print("⚠️ No image generated by Meta AI")
            return None
            
        except Exception as e:
            print(f"❌ Error generating image with Meta AI: {e}")
            return None
    
    def smart_post(self, message: str, media_url: str = None, article_title: str = "", article_description: str = "", preview_images: list = None) -> Dict[str, Any]:
        """AGGRESSIVELY get videos/images - prioritize actual media over fallbacks"""
        try:
            media_path = None
            is_video = False
            
            print(f"🎯 AGGRESSIVE MEDIA EXTRACTION MODE - Videos and images MUST be posted!")
            
            # STEP 1: Try main media URL aggressively
            if media_url:
                if self.is_video_url(media_url):
                    print(f"📹 VIDEO DETECTED - MUST GET THIS VIDEO!")
                    print(f"🔍 Trying multiple methods to get video from: {media_url[:50]}...")
                    
                    # Try multiple times with different approaches
                    for attempt in range(3):
                        print(f"🔄 Video download attempt {attempt + 1}/3")
                        media_path = self.download_video(media_url)
                        if media_path:
                            is_video = True
                            print(f"✅ SUCCESS! Got video on attempt {attempt + 1}")
                            break
                        else:
                            print(f"⚠️ Video attempt {attempt + 1} failed, trying again...")
                            time.sleep(1)  # Brief pause between attempts
                    
                    # If video still failed, try preview images as video fallback
                    if not media_path and preview_images:
                        print(f"🎬 Video failed after 3 attempts, trying preview images as backup...")
                        for i, preview in enumerate(preview_images):
                            preview_url = preview.get('url')
                            if preview_url:
                                print(f"📥 Trying preview image {i+1}: {preview_url[:50]}...")
                                media_path = self.download_image(preview_url)
                                if media_path:
                                    is_video = False
                                    print(f"✅ Got preview image {i+1} as video fallback")
                                    break
                
                else:
                    print(f"📷 IMAGE DETECTED - MUST GET THIS IMAGE!")
                    
                    # Handle Reddit gallery URLs - go straight to preview images
                    if 'reddit.com/gallery/' in media_url:
                        print(f"🖼️ Reddit gallery detected - going straight to preview images!")
                        print(f"🔍 Debug: preview_images available: {len(preview_images) if preview_images else 0}")
                        
                        if preview_images:
                            print(f"📷 AGGRESSIVELY trying ALL {len(preview_images)} preview images...")
                            for i, preview in enumerate(preview_images):
                                preview_url = preview.get('url')
                                print(f"🔍 Preview {i+1}: {preview_url[:50] if preview_url else 'No URL'}")
                                
                                if preview_url:
                                    # Try multiple times for each preview image
                                    for attempt in range(2):
                                        print(f"📥 Trying preview image {i+1}/{len(preview_images)} (attempt {attempt+1}/2)")
                                        media_path = self.download_image(preview_url)
                                        if media_path:
                                            print(f"✅ SUCCESS! Got preview image {i+1} on attempt {attempt+1}")
                                            break
                                        time.sleep(0.5)
                                    
                                    if media_path:
                                        break
                        else:
                            print(f"❌ No preview images available for gallery URL!")
                    
                    else:
                        # Try main image URL aggressively
                        print(f"🔍 Trying multiple methods to get image from: {media_url[:50]}...")
                        for attempt in range(3):
                            print(f"🔄 Image download attempt {attempt + 1}/3")
                            media_path = self.download_image(media_url)
                            if media_path:
                                print(f"✅ SUCCESS! Got image on attempt {attempt + 1}")
                                break
                            else:
                                print(f"⚠️ Image attempt {attempt + 1} failed, trying again...")
                                time.sleep(1)
                        
                        # If main image failed, try preview images
                        if not media_path and preview_images:
                            print(f"📷 Main image failed, trying ALL preview images...")
                            for i, preview in enumerate(preview_images):
                                preview_url = preview.get('url')
                                if preview_url:
                                    print(f"📥 Trying preview image {i+1}/{len(preview_images)}: {preview_url[:50]}...")
                                    media_path = self.download_image(preview_url)
                                    if media_path:
                                        print(f"✅ Got preview image {i+1}")
                                        break
                    
                    is_video = False
            
            # STEP 2: If no main URL, try ALL preview images aggressively
            if not media_path and preview_images:
                print(f"🖼️ No main media URL, AGGRESSIVELY trying ALL {len(preview_images)} preview images...")
                for i, preview in enumerate(preview_images):
                    preview_url = preview.get('url')
                    if preview_url:
                        print(f"📥 Trying preview image {i+1}/{len(preview_images)}: {preview_url[:50]}...")
                        media_path = self.download_image(preview_url)
                        if media_path:
                            is_video = False
                            print(f"✅ Got preview image {i+1}")
                            break
            
            # STEP 3: Only if we absolutely cannot get any media, try AI generation
            if not media_path and (article_title or article_description):
                print("🎨 LAST RESORT: No media found anywhere, generating AI image...")
                media_path = self.generate_image_with_ai(article_title, article_description)
                is_video = False
            
            # STEP 4: Post the media we got (prioritize actual media over text-only)
            if media_path:
                if is_video:
                    print("📹 POSTING VIDEO TO FACEBOOK!")
                    response = self.post_video(media_path, message)
                else:
                    print("📤 POSTING IMAGE TO FACEBOOK!")
                    response = self.post_image(media_path, message)
                
                # Clean up the media file
                try:
                    os.unlink(media_path)
                    media_type = "video" if is_video else "image"
                    print(f"🗑️ Cleaned up temporary {media_type}")
                except OSError:
                    pass
            else:
                # Only fallback to text if we absolutely couldn't get any media
                print("📤 FALLBACK: No media available anywhere, posting text-only...")
                response = self.post_text(message)
            
            print("✅ Successfully posted to Facebook!")
            return response
            
        except Exception as e:
            print(f"❌ Error in smart_post: {e}")
            raise
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get information about the Facebook page"""
        url = f"{self.base_url}/{self.page_id}"
        params = {
            'fields': 'name,followers_count,fan_count',
            'access_token': self.page_token
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting page info: {e}")
            raise
