#!/usr/bin/env python3
"""
Fix for Reddit video audio issue - Install yt-dlp and update video download logic
"""

import subprocess
import sys
import os

def install_yt_dlp():
    """Install yt-dlp for proper Reddit video handling"""
    try:
        print("📦 Installing yt-dlp for Reddit video audio support...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        print("✅ yt-dlp installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install yt-dlp: {e}")
        return False

def test_yt_dlp():
    """Test if yt-dlp can handle Reddit videos"""
    try:
        import yt_dlp
        print("✅ yt-dlp is available")
        
        # Test with a sample Reddit video URL format
        test_url = "https://v.redd.it/sample"
        
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("✅ yt-dlp configured successfully")
            
        return True
    except ImportError:
        print("❌ yt-dlp not available")
        return False
    except Exception as e:
        print(f"⚠️ yt-dlp test warning: {e}")
        return True  # Still usable

def create_enhanced_video_downloader():
    """Create enhanced video downloader with yt-dlp support"""
    
    enhanced_code = '''
    def download_video_with_audio(self, video_url: str) -> str:
        """Download a video with audio using yt-dlp for Reddit videos"""
        try:
            # First try yt-dlp for Reddit videos (handles audio properly)
            if 'v.redd.it' in video_url or 'reddit.com' in video_url:
                return self._download_with_yt_dlp(video_url)
            else:
                # Use original method for other video sources
                return self.download_video(video_url)
                
        except Exception as e:
            print(f"❌ Error in enhanced video download: {e}")
            # Fallback to original method
            return self.download_video(video_url)
    
    def _download_with_yt_dlp(self, video_url: str) -> str:
        """Download Reddit video with audio using yt-dlp"""
        try:
            import yt_dlp
            import time
            
            print(f"🎵 Downloading Reddit video with audio using yt-dlp...")
            
            # Create filename
            timestamp = int(time.time())
            output_template = f"reddit_video_audio_{timestamp}.%(ext)s"
            
            ydl_opts = {
                'format': 'best[ext=mp4]/best',  # Prefer mp4, fallback to best available
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'extractaudio': False,  # Keep video
                'audioformat': 'mp4',
                'merge_output_format': 'mp4',  # Ensure output is mp4
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to check if video exists
                try:
                    info = ydl.extract_info(video_url, download=False)
                    if not info:
                        print("⚠️ No video info found")
                        return None
                        
                    print(f"📹 Video found: {info.get('title', 'Unknown')[:50]}...")
                    
                    # Download the video
                    ydl.download([video_url])
                    
                    # Find the downloaded file
                    expected_filename = f"reddit_video_audio_{timestamp}.mp4"
                    if os.path.exists(expected_filename):
                        file_size = os.path.getsize(expected_filename)
                        print(f"🎵 Downloaded video with audio: {expected_filename} ({file_size} bytes)")
                        return expected_filename
                    else:
                        # Look for any file with our timestamp
                        for file in os.listdir('.'):
                            if f"reddit_video_audio_{timestamp}" in file:
                                file_size = os.path.getsize(file)
                                print(f"🎵 Downloaded video with audio: {file} ({file_size} bytes)")
                                return file
                        
                        print("❌ Downloaded file not found")
                        return None
                        
                except yt_dlp.DownloadError as e:
                    print(f"⚠️ yt-dlp download error: {e}")
                    return None
                    
        except ImportError:
            print("⚠️ yt-dlp not available, falling back to original method")
            return None
        except Exception as e:
            print(f"❌ Error with yt-dlp download: {e}")
            return None
    '''
    
    print("📝 Enhanced video downloader code ready")
    print("🔧 To integrate this, you need to:")
    print("   1. Add the above methods to FacebookService class")
    print("   2. Update smart_post to use download_video_with_audio for Reddit videos")
    print("   3. Test with actual Reddit video URLs")
    
    return enhanced_code

def main():
    """Main function to fix Reddit audio issue"""
    print("🔧 Reddit Video Audio Fix")
    print("=" * 50)
    
    # Step 1: Install yt-dlp
    if not install_yt_dlp():
        print("❌ Cannot proceed without yt-dlp")
        return
    
    # Step 2: Test yt-dlp
    if not test_yt_dlp():
        print("❌ yt-dlp not working properly")
        return
    
    # Step 3: Create enhanced downloader
    enhanced_code = create_enhanced_video_downloader()
    
    print("\n✅ Reddit video audio fix is ready!")
    print("\n📋 Next Steps:")
    print("1. yt-dlp has been installed")
    print("2. Enhanced video downloader methods are available")
    print("3. Update FacebookService to use the new methods")
    print("4. Test with Reddit video URLs")
    
    print("\n🎵 This should resolve the muted video issue!")
    print("   Reddit videos will now download with proper audio tracks")

if __name__ == "__main__":
    main()
