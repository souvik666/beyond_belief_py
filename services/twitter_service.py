"""
Simple Twitter API module for posting tweets with images
"""

import os
import time
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

load_dotenv()

class TwitterAPI:
    def __init__(self):
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise EnvironmentError("Missing Twitter API credentials")
        
        self.auth = OAuth1(self.api_key, self.api_secret, self.access_token, self.access_token_secret)

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image URL"""
        if not url:
            return False
        
        # Check for common image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        url_lower = url.lower()
        
        # Check if URL ends with image extension
        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True
        
        # Check if URL contains image-related patterns
        image_patterns = ['image', 'img', 'photo', 'picture', 'pic']
        if any(pattern in url_lower for pattern in image_patterns):
            return True
        
        # Reject obvious non-image URLs
        non_image_patterns = ['.html', '.php', '.asp', '.jsp', '/news/', '/article/', '/story/']
        if any(pattern in url_lower for pattern in non_image_patterns):
            return False
        
        return True

    def upload_image(self, image_url: str) -> str:
        """Upload image from URL to Twitter, returns media_id with network error handling"""
        # First validate if this looks like an image URL
        if not self._is_valid_image_url(image_url):
            print(f"⚠️ URL doesn't look like an image: {image_url}")
            print("🔄 Skipping image upload - posting text-only tweet")
            return None
        
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"📥 Downloading image from: {image_url} (attempt {attempt + 1}/{max_retries})")
                
                # Download image with retry logic and proper headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                img_response = requests.get(image_url, timeout=30, headers=headers)
                img_response.raise_for_status()
                
                # Check content type and size
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"❌ Invalid content type: {content_type}")
                    print(f"🔍 Response content preview: {str(img_response.content[:100])}")
                    return None
                
                content_length = len(img_response.content)
                if content_length > 5 * 1024 * 1024:  # 5MB limit
                    print(f"❌ Image too large: {content_length / (1024*1024):.1f}MB")
                    return None
                
                print(f"✅ Image downloaded: {content_length / 1024:.1f}KB, type: {content_type}")
                
                # Upload to Twitter with retry logic
                upload_url = "https://upload.twitter.com/1.1/media/upload.json"
                files = {'media': ('image.jpg', img_response.content, content_type)}
                
                upload_response = requests.post(upload_url, auth=self.auth, files=files, timeout=30)
                
                if upload_response.status_code in (200, 201):
                    media_id = upload_response.json().get('media_id_string')
                    print(f"✅ Image uploaded successfully! Media ID: {media_id}")
                    return media_id
                else:
                    print(f"❌ Media upload failed: {upload_response.status_code} - {upload_response.text}")
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                        print(f"⏳ Retrying image upload in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return None
                
            except requests.exceptions.ConnectionError as e:
                print(f"⚠️ Network connection error during image upload: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s for connection issues
                    print(f"⏳ Retrying image upload in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Failed to upload image after all retry attempts due to network issues")
                    return None
                    
            except requests.exceptions.Timeout as e:
                print(f"⚠️ Timeout during image upload: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3  # 3s, 6s, 12s for timeouts
                    print(f"⏳ Retrying image upload in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Failed to upload image after all retry attempts due to timeouts")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Request error during image upload: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"⏳ Retrying image upload in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Failed to upload image after all retry attempts due to request errors")
                    return None
                    
            except Exception as e:
                print(f"❌ Unexpected error uploading image: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"⏳ Retrying image upload in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Failed to upload image after all retry attempts")
                    return None
        
        return None

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

    def download_media(self, media_url: str) -> tuple:
        """Download media from URL and return (filepath, is_video)"""
        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'video/*,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            print(f"📥 Downloading media from: {media_url[:50]}...")
            response = requests.get(media_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            content_length = int(response.headers.get('content-length', 0))
            
            # Determine if it's video or image
            is_video = False
            if any(vid_type in content_type for vid_type in ['video/', 'mp4', 'webm', 'mov', 'avi']):
                is_video = True
                print(f"📹 Detected video content: {content_type}")
            elif any(img_type in content_type for img_type in ['image/', 'jpeg', 'jpg', 'png', 'gif', 'webp']):
                is_video = False
                print(f"📷 Detected image content: {content_type}")
            else:
                print(f"⚠️ Unknown content type: {content_type}")
                return None, False
            
            # Check size limits (Twitter: 5MB for images, 512MB for videos)
            max_size = 512 * 1024 * 1024 if is_video else 5 * 1024 * 1024
            if content_length > max_size:
                print(f"⚠️ Media too large: {content_length / (1024*1024):.1f}MB (limit: {max_size / (1024*1024):.1f}MB)")
                return None, False
            
            # Determine file extension
            if is_video:
                if 'mp4' in content_type or media_url.lower().endswith('.mp4'):
                    ext = '.mp4'
                elif 'webm' in content_type or media_url.lower().endswith('.webm'):
                    ext = '.webm'
                elif 'mov' in content_type or media_url.lower().endswith('.mov'):
                    ext = '.mov'
                else:
                    ext = '.mp4'  # Default for videos
            else:
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # Default for images
            
            # Create filename
            timestamp = int(time.time())
            media_type = "video" if is_video else "image"
            filename = f"twitter_{media_type}_{timestamp}{ext}"
            
            # Download the media
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filename)
            print(f"✅ Downloaded {media_type}: {filename} ({file_size} bytes)")
            return filename, is_video
            
        except Exception as e:
            print(f"❌ Error downloading media: {e}")
            return None, False

    def upload_video(self, video_path: str) -> str:
        """Upload video to Twitter using chunked upload"""
        try:
            import os
            
            file_size = os.path.getsize(video_path)
            print(f"📹 Uploading video to Twitter: {video_path} ({file_size} bytes)")
            
            # Step 1: Initialize upload
            init_url = "https://upload.twitter.com/1.1/media/upload.json"
            init_data = {
                'command': 'INIT',
                'media_type': 'video/mp4',
                'total_bytes': file_size
            }
            
            init_response = requests.post(init_url, auth=self.auth, data=init_data, timeout=30)
            if init_response.status_code != 202:
                print(f"❌ Video upload init failed: {init_response.status_code} - {init_response.text}")
                return None
            
            media_id = init_response.json().get('media_id_string')
            print(f"✅ Video upload initialized, media_id: {media_id}")
            
            # Step 2: Upload chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            segment_id = 0
            
            with open(video_path, 'rb') as video_file:
                while True:
                    chunk = video_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    append_data = {
                        'command': 'APPEND',
                        'media_id': media_id,
                        'segment_index': segment_id
                    }
                    
                    files = {'media': chunk}
                    
                    append_response = requests.post(init_url, auth=self.auth, data=append_data, files=files, timeout=60)
                    if append_response.status_code != 204:
                        print(f"❌ Video chunk upload failed: {append_response.status_code}")
                        return None
                    
                    segment_id += 1
                    print(f"📤 Uploaded chunk {segment_id}")
            
            # Step 3: Finalize upload
            finalize_data = {
                'command': 'FINALIZE',
                'media_id': media_id
            }
            
            finalize_response = requests.post(init_url, auth=self.auth, data=finalize_data, timeout=30)
            if finalize_response.status_code not in (200, 201):
                print(f"❌ Video upload finalize failed: {finalize_response.status_code} - {finalize_response.text}")
                return None
            
            print(f"✅ Video uploaded successfully! Media ID: {media_id}")
            return media_id
            
        except Exception as e:
            print(f"❌ Error uploading video: {e}")
            return None

    def smart_post(self, text: str, media_url: str = None, preview_images: list = None) -> bool:
        """Smart posting with aggressive media handling like Facebook"""
        try:
            print(f"🎯 TWITTER SMART POST - Aggressive media extraction mode!")
            
            media_path = None
            is_video = False
            media_id = None
            
            # STEP 1: Try main media URL aggressively
            if media_url:
                if self.is_video_url(media_url):
                    print(f"📹 VIDEO DETECTED - MUST GET THIS VIDEO!")
                    print(f"🔍 Trying multiple methods to get video from: {media_url[:50]}...")
                    
                    # Try multiple times with different approaches
                    for attempt in range(3):
                        print(f"🔄 Video download attempt {attempt + 1}/3")
                        media_path, is_video = self.download_media(media_url)
                        if media_path and is_video:
                            print(f"✅ SUCCESS! Got video on attempt {attempt + 1}")
                            break
                        else:
                            print(f"⚠️ Video attempt {attempt + 1} failed, trying again...")
                            time.sleep(1)
                    
                    # If video still failed, try preview images as fallback
                    if not media_path and preview_images:
                        print(f"🎬 Video failed after 3 attempts, trying preview images as backup...")
                        for i, preview in enumerate(preview_images):
                            preview_url = preview.get('url')
                            if preview_url and self._is_valid_image_url(preview_url):
                                print(f"📥 Trying preview image {i+1}: {preview_url[:50]}...")
                                media_path, is_video = self.download_media(preview_url)
                                if media_path:
                                    is_video = False
                                    print(f"✅ Got preview image {i+1} as video fallback")
                                    break
                
                else:
                    print(f"📷 IMAGE DETECTED - MUST GET THIS IMAGE!")
                    print(f"🔍 Trying multiple methods to get image from: {media_url[:50]}...")
                    
                    # Try main image URL aggressively
                    for attempt in range(3):
                        print(f"🔄 Image download attempt {attempt + 1}/3")
                        media_path, is_video = self.download_media(media_url)
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
                            if preview_url and self._is_valid_image_url(preview_url):
                                print(f"📥 Trying preview image {i+1}/{len(preview_images)}: {preview_url[:50]}...")
                                media_path, is_video = self.download_media(preview_url)
                                if media_path:
                                    print(f"✅ Got preview image {i+1}")
                                    break
            
            # STEP 2: If no main URL, try ALL preview images aggressively
            if not media_path and preview_images:
                print(f"🖼️ No main media URL, AGGRESSIVELY trying ALL {len(preview_images)} preview images...")
                for i, preview in enumerate(preview_images):
                    preview_url = preview.get('url')
                    if preview_url and self._is_valid_image_url(preview_url):
                        print(f"📥 Trying preview image {i+1}/{len(preview_images)}: {preview_url[:50]}...")
                        media_path, is_video = self.download_media(preview_url)
                        if media_path:
                            print(f"✅ Got preview image {i+1}")
                            break
            
            # STEP 3: Upload media to Twitter if we got any
            if media_path:
                if is_video:
                    print("📹 UPLOADING VIDEO TO TWITTER!")
                    media_id = self.upload_video(media_path)
                else:
                    print("📤 UPLOADING IMAGE TO TWITTER!")
                    # Read the file and upload as image
                    with open(media_path, 'rb') as f:
                        img_content = f.read()
                    
                    # Upload to Twitter
                    upload_url = "https://upload.twitter.com/1.1/media/upload.json"
                    files = {'media': ('image.jpg', img_content, 'image/jpeg')}
                    
                    upload_response = requests.post(upload_url, auth=self.auth, files=files, timeout=30)
                    
                    if upload_response.status_code in (200, 201):
                        media_id = upload_response.json().get('media_id_string')
                        print(f"✅ Image uploaded successfully! Media ID: {media_id}")
                    else:
                        print(f"❌ Image upload failed: {upload_response.status_code} - {upload_response.text}")
                
                # Clean up the media file
                try:
                    os.unlink(media_path)
                    media_type = "video" if is_video else "image"
                    print(f"🗑️ Cleaned up temporary {media_type}")
                except OSError:
                    pass
            
            # STEP 4: Post the tweet
            payload = {"text": text}
            if media_id:
                payload["media"] = {"media_ids": [media_id]}
                print(f"🖼️ Media attached to tweet with media_id: {media_id}")
            
            # Post tweet using v2 API
            url = "https://api.twitter.com/2/tweets"
            headers = {'Content-Type': 'application/json'}
            
            print(f"🐦 Posting tweet...")
            response = requests.post(url, auth=self.auth, json=payload, headers=headers, timeout=30)
            
            if response.status_code in (200, 201):
                tweet_data = response.json()
                tweet_id = tweet_data.get('data', {}).get('id', 'unknown')
                if media_id:
                    media_type = "video" if is_video else "image"
                    print(f"✅ Tweet with {media_type} posted successfully! Tweet ID: {tweet_id}")
                else:
                    print(f"✅ Tweet posted successfully! Tweet ID: {tweet_id}")
                return True
            else:
                print(f"❌ Failed to post tweet: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error in smart_post: {e}")
            return False

    def post_tweet(self, text: str, image_url: str = None, preview_images: list = None) -> bool:
        """Post a tweet with optional media using smart posting"""
        # Use the new smart_post method for comprehensive media handling
        return self.smart_post(text, image_url, preview_images)

    def post_tweet_simple(self, text: str, image_url: str = None) -> bool:
        """Simple tweet posting (legacy method for backward compatibility)"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                payload = {"text": text}
                
                # Upload image if provided (only on first attempt)
                if image_url and attempt == 0:
                    print(f"🖼️ Attempting to upload image: {image_url}")
                    media_id = self.upload_image(image_url)
                    if media_id:
                        payload["media"] = {"media_ids": [media_id]}
                        print(f"🖼️ Image attached to tweet with media_id: {media_id}")
                        
                        # Add 2-second delay between image upload and posting
                        print("⏳ Waiting 2 seconds before posting tweet...")
                        time.sleep(2)
                    else:
                        print("⚠️ Failed to upload image, posting text-only tweet")
                
                # Post tweet using v2 API
                url = "https://api.twitter.com/2/tweets"
                headers = {
                    'Content-Type': 'application/json',
                }
                
                print(f"🐦 Posting tweet (attempt {attempt + 1}/{max_retries})...")
                response = requests.post(url, auth=self.auth, json=payload, headers=headers, timeout=30)
                
                if response.status_code in (200, 201):
                    tweet_data = response.json()
                    tweet_id = tweet_data.get('data', {}).get('id', 'unknown')
                    if 'media' in payload:
                        print(f"✅ Tweet with image posted successfully! Tweet ID: {tweet_id}")
                    else:
                        print(f"✅ Tweet posted successfully! Tweet ID: {tweet_id}")
                    return True
                    
                elif response.status_code == 429:
                    # Rate limit exceeded - don't wait, just fail fast
                    print("❌ Twitter rate limit hit (429) - skipping Twitter post to avoid delays")
                    return False
                        
                elif response.status_code in [500, 502, 503, 504]:
                    # Server errors - retry with shorter backoff
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    print(f"⚠️ Twitter server error {response.status_code}. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Server error persists: {response.status_code} - {response.text}")
                        return False
                        
                else:
                    # Other errors - don't retry
                    print(f"❌ Failed to post tweet: {response.status_code} - {response.text}")
                    return False
                
            except requests.exceptions.Timeout:
                wait_time = (2 ** attempt) * 3  # 3s, 6s, 12s
                print(f"⚠️ Request timeout. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Request timeout - all retry attempts failed")
                    return False
                    
            except requests.exceptions.ConnectionError as e:
                wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                print(f"⚠️ Network connection error: {e}")
                print(f"⏳ Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Network connection failed - all retry attempts failed")
                    return False
                    
            except Exception as e:
                print(f"❌ Unexpected error posting tweet: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"⏳ Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Unexpected error - all retry attempts failed")
                    return False
        
        return False
