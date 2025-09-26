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

    def upload_image(self, image_url: str) -> str:
        """Upload image from URL to Twitter, returns media_id with network error handling"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"📥 Downloading image from: {image_url} (attempt {attempt + 1}/{max_retries})")
                
                # Download image with retry logic
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                
                # Check content type and size
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"❌ Invalid content type: {content_type}")
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

    def post_tweet(self, text: str, image_url: str = None) -> bool:
        """Post a tweet with optional image with retry logic for rate limits"""
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
