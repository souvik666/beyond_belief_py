"""
Automation service for posting news content to Facebook every 10 minutes
"""

import os
import time
import random
import schedule
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

from .news_service import NewsFetcher
from .content_generator import ContentGenerator
from .facebook_service import FacebookService
from .twitter_service import TwitterAPI
from .logging_service import AutomationLogger

load_dotenv()

class NewsAutomationService:
    def __init__(self):
        self.news_fetcher = NewsFetcher()
        self.content_generator = ContentGenerator()
        self.facebook_service = FacebookService()
        self.logger = AutomationLogger()
        
        # Initialize Twitter service (optional)
        self.twitter_enabled = os.getenv('ENABLE_TWITTER', 'true').lower() == 'true'
        
        if self.twitter_enabled:
            try:
                self.twitter_service = TwitterAPI()
                print("✅ Twitter service initialized")
            except Exception as e:
                print(f"⚠️ Twitter service not available: {e}")
                self.twitter_service = None
        else:
            print("ℹ️ Twitter posting disabled via ENABLE_TWITTER=false")
            self.twitter_service = None
        
        # User preferences (will be set during setup)
        self.preferences = None
        
        # Statistics
        self.stats = {
            'total_posts': 0,
            'successful_posts': 0,
            'failed_posts': 0,
            'start_time': datetime.now()
        }
        
        # Log initialization
        self.logger.log_step("AUTOMATION_SERVICE_INIT", {
            'start_time': self.stats['start_time'].isoformat(),
            'db_folder_created': True
        })
    
    def setup_preferences(self):
        """Setup user preferences for news fetching"""
        if not self.preferences:
            print("🎯 Setting up news preferences...")
            self.preferences = self.news_fetcher.choose_preferences()
        return self.preferences

    def ensure_articles_available(self) -> List[Dict[str, Any]]:
        """Ensure we have articles available - prioritize unposted articles first"""
        self.logger.log_step("ENSURE_ARTICLES_START")
        
        # First, always check for unposted articles in cache
        unposted_articles = self.news_fetcher.get_cached_articles()
        
        if unposted_articles:
            self.logger.log_step("UNPOSTED_ARTICLES_FOUND", {
                "unposted_count": len(unposted_articles),
                "action": "using_existing_unposted_articles"
            })
            print(f"📦 Found {len(unposted_articles)} unposted articles in cache - using them first")
            return unposted_articles
        
        # Only fetch new articles if no unposted articles exist
        self.logger.log_step("NO_UNPOSTED_ARTICLES", {"action": "fetching_new_articles"})
        print("🔄 No unposted articles found, fetching new articles...")
        
        # Setup preferences if not done
        if not self.preferences:
            self.logger.log_step("SETUP_PREFERENCES_START")
            self.setup_preferences()
            self.logger.log_step("SETUP_PREFERENCES_COMPLETE", {
                "topics": self.preferences.get('topics', []),
                "queries_count": len(self.preferences.get('queries', []))
            })
        
        # Fetch bulk news with logging
        new_articles = self.news_fetcher.fetch_bulk_news(self.preferences, total_articles=300, logger=self.logger)
        
        self.logger.log_step("ENSURE_ARTICLES_COMPLETE", {
            "new_articles_fetched": len(new_articles),
            "strategy": "fetched_new_after_cache_empty"
        })
        
        return new_articles
    
    def select_article_for_posting(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best article for posting based on various criteria"""
        if not articles:
            return None
        
        # Scoring criteria
        scored_articles = []
        
        for article in articles:
            score = 0
            title = article.get('title', '') or ''
            description = article.get('description', '') or ''
            title_lower = title.lower()
            description_lower = description.lower()
            
            # Prefer articles with images
            if article.get('image_url'):
                score += 10
            
            # Prefer recent articles
            pub_date = article.get('pubDate')
            if pub_date:
                try:
                    # Simple recency boost (this is a basic implementation)
                    score += 5
                except:
                    pass
            
            # Prefer articles with good descriptions
            if description and len(description) > 50:
                score += 5
            
            # Boost certain categories
            categories = article.get('category', []) or []
            if any(cat.lower() in ['politics', 'business', 'technology'] for cat in categories if cat):
                score += 8
            
            # Avoid certain keywords that might be sensitive
            sensitive_keywords = ['death', 'accident', 'murder', 'rape', 'suicide']
            if any(keyword in title_lower for keyword in sensitive_keywords):
                score -= 20
            
            scored_articles.append((article, score))
        
        # Sort by score and return the best one
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        
        if scored_articles:
            selected_article = scored_articles[0][0]
            print(f"📋 Selected article: {selected_article.get('title', '')[:50]}...")
            return selected_article
        
        return None
    
    def create_and_post_content(self):
        """Main function to create and post content using cached articles"""
        self.logger.log_step("CREATE_AND_POST_START", {
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            print(f"\n🚀 Starting content creation and posting at {datetime.now()}")
            
            # Ensure we have articles available
            available_articles = self.ensure_articles_available()
            
            if not available_articles:
                self.logger.log_step("NO_ARTICLES_AVAILABLE", {}, "error")
                print("❌ No articles available for posting")
                return
            
            # Select an article
            self.logger.log_step("ARTICLE_SELECTION_START", {
                'available_articles': len(available_articles)
            })
            
            article = self.select_article_for_posting(available_articles)
            
            if not article:
                self.logger.log_step("NO_SUITABLE_ARTICLE", {}, "error")
                print("❌ No suitable article found for posting")
                return
            
            self.logger.log_step("ARTICLE_SELECTED", {
                'title': article.get('title', '')[:100],
                'query_used': article.get('query_used', ''),
                'has_image': bool(article.get('image_url') or article.get('urlToImage')),
                'countries_searched': article.get('countries_searched', '')
            })
            
            # Generate content based on enabled platforms
            if self.twitter_enabled and self.twitter_service:
                print("🤖 Generating dual platform content with Meta AI...")
                self.logger.log_step("AI_CONTENT_GENERATION_START", {
                    'article_title': article.get('title', '')[:100]
                })
                dual_content = self.content_generator.generate_dual_platform_content(article)
            else:
                print("🤖 Generating Facebook content with Meta AI...")
                self.logger.log_step("AI_CONTENT_GENERATION_START", {
                    'article_title': article.get('title', '')[:100]
                })
                facebook_content = self.content_generator.generate_content_from_news(article, "facebook")
                dual_content = {'facebook': facebook_content, 'twitter': ''}
            
            if not dual_content or not dual_content.get('facebook'):
                self.logger.log_content_generation(article, "", False)
                print("❌ Failed to generate content")
                return
            
            facebook_content = dual_content['facebook']
            twitter_content = dual_content.get('twitter', '')
            
            self.logger.log_content_generation(article, facebook_content, True)
            
            # Get image URL from article
            image_url = article.get('image_url') or article.get('urlToImage')
            
            # Post to Facebook
            self.logger.log_step("FACEBOOK_POST_START", {
                'content_length': len(facebook_content),
                'has_image': bool(image_url),
                'image_url': image_url[:100] if image_url else None
            })
            
            print("📤 Posting to Facebook...")
            facebook_response = self.facebook_service.smart_post(
                facebook_content, 
                image_url, 
                article.get('title', ''), 
                article.get('description', '')
            )
            
            # Post to Twitter if available (optional - skip if fails)
            twitter_success = False
            if self.twitter_service and twitter_content:
                try:
                    print("🐦 Attempting to post to Twitter...")
                    self.logger.log_step("TWITTER_POST_START", {
                        'content_length': len(twitter_content),
                        'has_image': bool(image_url)
                    })
                    
                    twitter_success = self.twitter_service.post_tweet(twitter_content, image_url)
                    
                    if twitter_success:
                        print("✅ Successfully posted to Twitter!")
                    else:
                        print("⚠️ Twitter post failed - skipping and continuing with Facebook only")
                        
                except Exception as e:
                    print(f"⚠️ Twitter posting error: {e} - skipping Twitter and continuing")
                    twitter_success = False
            elif not self.twitter_service:
                print("ℹ️ Twitter service not available - posting to Facebook only")
            else:
                print("ℹ️ No Twitter content generated - posting to Facebook only")
            
            # Log the successful posts
            self.logger.log_post(article, facebook_content, facebook_response, True)
            
            response = facebook_response  # Keep for compatibility
            
            # Mark article as posted in cache
            self.news_fetcher.mark_as_posted(article)
            
            # Update statistics
            self.stats['total_posts'] += 1
            self.stats['successful_posts'] += 1
            
            print(f"✅ Successfully posted! Post ID: {response.get('id', 'Unknown')}")
            print(f"📊 Stats: {self.stats['successful_posts']}/{self.stats['total_posts']} successful posts")
            
            # Show cache stats
            cache_stats = self.news_fetcher.get_cache_stats()
            print(f"📦 Cache: {cache_stats.get('unposted', 0)} unposted, {cache_stats.get('posted', 0)} posted")
            
            self.logger.log_step("CREATE_AND_POST_SUCCESS", {
                'post_id': response.get('id', ''),
                'total_posts': self.stats['total_posts'],
                'successful_posts': self.stats['successful_posts']
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error in create_and_post_content: {error_msg}")
            
            self.logger.log_error("CREATE_AND_POST_ERROR", error_msg, {
                'total_posts': self.stats['total_posts'],
                'failed_posts': self.stats['failed_posts']
            })
            
            self.stats['total_posts'] += 1
            self.stats['failed_posts'] += 1
    
    def _should_refresh_cache(self) -> bool:
        """Check if article cache should be refreshed"""
        if not self.last_fetch_time:
            return True
        
        # Refresh cache every 30 minutes
        return datetime.now() - self.last_fetch_time > timedelta(minutes=30)
    
    def get_page_info(self):
        """Get and display Facebook page information"""
        try:
            page_info = self.facebook_service.get_page_info()
            print(f"📄 Page: {page_info.get('name', 'Unknown')}")
            print(f"👥 Followers: {page_info.get('fan_count', 'Unknown')}")
        except Exception as e:
            print(f"❌ Could not get page info: {e}")
    
    def print_stats(self):
        """Print current statistics including cache stats"""
        runtime = datetime.now() - self.stats['start_time']
        cache_stats = self.news_fetcher.get_cache_stats()
        
        print(f"\n📊 Automation Statistics:")
        print(f"   Runtime: {runtime}")
        print(f"   Total posts attempted: {self.stats['total_posts']}")
        print(f"   Successful posts: {self.stats['successful_posts']}")
        print(f"   Failed posts: {self.stats['failed_posts']}")
        print(f"   Success rate: {(self.stats['successful_posts']/max(1, self.stats['total_posts'])*100):.1f}%")
        
        print(f"\n📦 Cache Statistics:")
        print(f"   Total articles in cache: {cache_stats.get('total', 0)}")
        print(f"   Unposted articles: {cache_stats.get('unposted', 0)}")
        print(f"   Posted articles: {cache_stats.get('posted', 0)}")
        print(f"   Total posted (all time): {cache_stats.get('total_posted', 0)}")
    
    def reset_cache(self):
        """Reset the cache and posted articles"""
        print("🗑️ Resetting cache...")
        self.news_fetcher.reset_cache()
        self.preferences = None
        print("✅ Cache reset complete")
    
    def setup_and_cache_articles(self):
        """Setup preferences and cache articles without starting automation"""
        print("🎯 Setting up preferences and caching articles...")
        self.setup_preferences()
        self.news_fetcher.fetch_bulk_news(self.preferences, total_articles=300)
        self.print_stats()
    
    def start_automation(self, interval_minutes: int = 10):
        """Start the automation with custom scheduling"""
        print("🤖 Starting Facebook News Automation Service")
        print(f"⏰ Posting every {interval_minutes} minutes")
        
        # Get initial page info
        self.get_page_info()
        
        # Schedule the job with custom interval
        schedule.every(interval_minutes).minutes.do(self.create_and_post_content)
        
        # Also schedule stats printing every hour
        schedule.every().hour.do(self.print_stats)
        
        # Run the first post immediately
        print("🚀 Running first post...")
        self.create_and_post_content()
        
        print(f"⏰ Scheduler started. Posting every {interval_minutes} minutes. Press Ctrl+C to stop.")
        
        # Keep the scheduler running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 Automation stopped by user")
            self.print_stats()
    
    def choose_schedule_and_start(self):
        """Interactive schedule selection and start automation"""
        print("\n🕐 Choose posting frequency:")
        print("1. Fast (every 5 minutes)")
        print("2. Mid (every 15 minutes)")
        print("3. Slow (every 30 minutes)")
        print("4. Custom interval")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                interval = 5
                print("🚀 Selected: Fast posting (every 5 minutes)")
            elif choice == "2":
                interval = 15
                print("🚀 Selected: Mid posting (every 15 minutes)")
            elif choice == "3":
                interval = 30
                print("🚀 Selected: Slow posting (every 30 minutes)")
            elif choice == "4":
                while True:
                    try:
                        interval = int(input("Enter custom interval in minutes (1-1440): "))
                        if 1 <= interval <= 1440:  # Max 24 hours
                            print(f"🚀 Selected: Custom posting (every {interval} minutes)")
                            break
                        else:
                            print("❌ Please enter a value between 1 and 1440 minutes")
                    except ValueError:
                        print("❌ Please enter a valid number")
            else:
                print("❌ Invalid choice. Using default (10 minutes)")
                interval = 10
            
            self.start_automation(interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Setup cancelled by user")
        except Exception as e:
            print(f"❌ Error in schedule selection: {e}")
            print("Using default interval (10 minutes)")
            self.start_automation(10)
    
    def run_single_post(self):
        """Run a single post for testing"""
        print("🧪 Running single test post...")
        self.get_page_info()
        self.create_and_post_content()
        self.print_stats()

class CronAutomationService:
    """Alternative service using system cron instead of Python scheduling"""
    
    def __init__(self):
        self.automation = NewsAutomationService()
    
    def setup_cron_job(self):
        """Set up a cron job for the automation"""
        try:
            from crontab import CronTab
            
            # Get current user's crontab
            cron = CronTab(user=True)
            
            # Remove existing jobs for this script
            cron.remove_all(comment='facebook_news_automation')
            
            # Create new job to run every 10 minutes
            job = cron.new(command=f'cd {os.getcwd()} && python -c "from services.automation_service import NewsAutomationService; NewsAutomationService().create_and_post_content()"')
            job.minute.every(10)
            job.set_comment('facebook_news_automation')
            
            # Write the crontab
            cron.write()
            
            print("✅ Cron job set up successfully!")
            print("📅 Will run every 10 minutes")
            print("🔍 Check with: crontab -l")
            
        except ImportError:
            print("❌ python-crontab not available. Using Python scheduler instead.")
            return False
        except Exception as e:
            print(f"❌ Error setting up cron job: {e}")
            return False
        
        return True
    
    def remove_cron_job(self):
        """Remove the cron job"""
        try:
            from crontab import CronTab
            
            cron = CronTab(user=True)
            cron.remove_all(comment='facebook_news_automation')
            cron.write()
            
            print("✅ Cron job removed successfully!")
            
        except Exception as e:
            print(f"❌ Error removing cron job: {e}")
