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
    
    def download_image(self, image_url: str) -> str:
        """Download an image from URL and save locally"""
        try:
            # Handle Reddit video URLs by trying to get preview image instead
            if 'v.redd.it' in image_url:
                print(f"⚠️ Reddit video URL detected, skipping: {image_url}")
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
    
    def smart_post(self, message: str, image_url: str = None, article_title: str = "", article_description: str = "") -> Dict[str, Any]:
        """Post content with news image, AI-generated image, or text-only"""
        try:
            image_path = None
            
            if image_url:
                # Try to download image from news article
                print(f"📥 Downloading image from news article...")
                image_path = self.download_image(image_url)
                
            if not image_path and (article_title or article_description):
                # Generate image using Meta AI if no news image available
                print("🎨 No news image available, generating AI image...")
                image_path = self.generate_image_with_ai(article_title, article_description)
            
            if image_path:
                # Post with image (either downloaded or AI-generated)
                print("📤 Posting to Facebook with image...")
                response = self.post_image(image_path, message)
                
                # Clean up the image
                try:
                    os.unlink(image_path)
                    print("🗑️ Cleaned up temporary image")
                except OSError:
                    pass
            else:
                # Fallback to text-only post
                print("📤 No image available, posting text-only to Facebook...")
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
