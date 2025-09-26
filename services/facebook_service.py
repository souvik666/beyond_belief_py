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
        """Resolve Reddit video URL to actual video file URL"""
        try:
            if 'v.redd.it' not in reddit_url:
                return reddit_url
            
            print(f"🔍 Resolving Reddit video URL...")
            
            # Try to construct direct video URL
            # Reddit video URLs often follow pattern: https://v.redd.it/VIDEO_ID/DASH_720.mp4
            if '/DASH_' not in reddit_url and not reddit_url.endswith('.mp4'):
                # Try common video qualities
                video_qualities = ['DASH_720.mp4', 'DASH_480.mp4', 'DASH_360.mp4', 'DASH_240.mp4']
                
                for quality in video_qualities:
                    test_url = f"{reddit_url.rstrip('/')}/{quality}"
                    print(f"🔍 Trying: {test_url}")
                    
                    try:
                        # Test if this URL returns video content
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept': 'video/*',
                        }
                        
                        response = requests.head(test_url, headers=headers, timeout=10)
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'video/' in content_type or 'mp4' in content_type:
                            print(f"✅ Found working video URL: {test_url}")
                            return test_url
                            
                    except Exception as e:
                        print(f"⚠️ Failed to test {quality}: {e}")
                        continue
            
            # If direct resolution fails, return original URL
            print(f"⚠️ Could not resolve Reddit video URL, returning original")
            return reddit_url
            
        except Exception as e:
            print(f"❌ Error resolving Reddit video URL: {e}")
            return reddit_url

    def download_video(self, video_url: str) -> str:
        """Download a video from URL and save locally"""
        try:
            # Resolve Reddit video URLs first
            if 'v.redd.it' in video_url:
                resolved_url = self.resolve_reddit_video_url(video_url)
                if resolved_url != video_url:
                    video_url = resolved_url
                else:
                    print(f"⚠️ Could not resolve Reddit video URL, skipping video download")
                    return None
            
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
        """Post content with video, image, AI-generated image, or text-only"""
        try:
            media_path = None
            is_video = False
            
            if media_url:
                # Check if it's a video or image
                if self.is_video_url(media_url):
                    print(f"📹 Detected video URL, downloading video...")
                    media_path = self.download_video(media_url)
                    is_video = True
                    
                    # If video download failed but we have preview images, use them instead
                    if not media_path and preview_images:
                        print(f"🎬 Video download failed, trying preview images...")
                        for preview in preview_images:
                            preview_url = preview.get('url')
                            if preview_url:
                                print(f"📥 Trying preview image: {preview_url[:50]}...")
                                media_path = self.download_image(preview_url)
                                if media_path:
                                    is_video = False  # Now it's an image
                                    print(f"✅ Using preview image instead of video")
                                    break
                else:
                    print(f"📥 Detected image URL, downloading image...")
                    media_path = self.download_image(media_url)
                    is_video = False
                
            if not media_path and (article_title or article_description):
                # Generate image using Meta AI if no media available
                print("🎨 No media available, generating AI image...")
                media_path = self.generate_image_with_ai(article_title, article_description)
                is_video = False
            
            if media_path:
                # Post with media (video, image, or AI-generated image)
                if is_video:
                    print("📹 Posting to Facebook with video...")
                    response = self.post_video(media_path, message)
                else:
                    print("📤 Posting to Facebook with image...")
                    response = self.post_image(media_path, message)
                
                # Clean up the media file
                try:
                    os.unlink(media_path)
                    media_type = "video" if is_video else "image"
                    print(f"🗑️ Cleaned up temporary {media_type}")
                except OSError:
                    pass
            else:
                # Fallback to text-only post
                print("📤 No media available, posting text-only to Facebook...")
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
