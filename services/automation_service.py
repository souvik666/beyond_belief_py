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
from .reddit_cache_manager import RedditCacheManager

load_dotenv()

class NewsAutomationService:
    def __init__(self):
        self.news_fetcher = NewsFetcher()
        self.content_generator = ContentGenerator()
        self.facebook_service = FacebookService()
        self.logger = AutomationLogger()
        
        # Initialize Reddit cache manager
        self.reddit_cache = RedditCacheManager()
        
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
        
        # Content mode: 'mixed', 'reddit_only', 'news_only'
        self.content_mode = 'mixed'
        
        # Alternating posting state (True = News, False = Reddit) - only used in mixed mode
        self.post_news_next = True
        
        # Statistics
        self.stats = {
            'total_posts': 0,
            'successful_posts': 0,
            'failed_posts': 0,
            'news_posts': 0,
            'reddit_posts': 0,
            'start_time': datetime.now()
        }
        
        # Log initialization
        self.logger.log_step("AUTOMATION_SERVICE_INIT", {
            'start_time': self.stats['start_time'].isoformat(),
            'db_folder_created': True
        })
    
    def set_content_mode(self, mode: str):
        """Set the content mode for the automation service"""
        valid_modes = ['mixed', 'reddit_only', 'news_only']
        if mode not in valid_modes:
            raise ValueError(f"Invalid content mode: {mode}. Must be one of {valid_modes}")
        
        self.content_mode = mode
        print(f"📊 Content mode set to: {mode.upper()}")
        
        if mode == 'reddit_only':
            print("👻 Will only post paranormal content from Reddit subreddits")
        elif mode == 'news_only':
            print("📰 Will only post traditional news articles")
        else:
            print("🔄 Will alternate between news and Reddit content")

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
        """Main function to create and post content - respects content mode settings"""
        # Track execution start time
        execution_start_time = datetime.now()
        
        # Determine post type based on content mode
        if self.content_mode == 'reddit_only':
            post_type = 'reddit'
        elif self.content_mode == 'news_only':
            post_type = 'news'
        else:  # mixed mode
            post_type = 'news' if self.post_news_next else 'reddit'
        
        self.logger.log_step("CREATE_AND_POST_START", {
            'timestamp': execution_start_time.isoformat(),
            'content_mode': self.content_mode,
            'post_type': post_type
        })
        
        try:
            print(f"\n🚀 Starting content creation and posting at {execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Content Mode: {self.content_mode.upper()}")
            
            # Post content based on determined type
            if post_type == 'news':
                print("📰 Posting NEWS content this round")
                success = self._post_news_content()
                if success:
                    self.stats['news_posts'] += 1
            else:  # reddit
                print("👻 Posting REDDIT content this round")
                success = self._post_reddit_content()
                if success:
                    self.stats['reddit_posts'] += 1
            
            if success:
                # Only toggle in mixed mode
                if self.content_mode == 'mixed':
                    self.post_news_next = not self.post_news_next
                    next_type = "NEWS" if self.post_news_next else "REDDIT"
                    print(f"🔄 Next post will be: {next_type}")
                else:
                    # In single-mode, always post the same type
                    mode_type = "NEWS" if self.content_mode == 'news_only' else "REDDIT"
                    print(f"🔄 Next post will be: {mode_type} (same mode)")
                
                self.stats['total_posts'] += 1
                self.stats['successful_posts'] += 1
                
                print(f"📊 Stats: {self.stats['successful_posts']}/{self.stats['total_posts']} successful posts")
                print(f"📊 News: {self.stats['news_posts']} | Reddit: {self.stats['reddit_posts']}")
                
                # Show next execution time if running in scheduled mode
                if schedule.jobs:
                    next_run = schedule.next_run()
                    if next_run:
                        print(f"🕐 Next execution will start at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                self.stats['total_posts'] += 1
                self.stats['failed_posts'] += 1
                print("❌ Post failed - will retry same type next time")
                
                # Show next execution time even on failure
                if schedule.jobs:
                    next_run = schedule.next_run()
                    if next_run:
                        print(f"🕐 Next execution will start at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error in create_and_post_content: {error_msg}")
            
            self.logger.log_error("CREATE_AND_POST_ERROR", error_msg, {
                'total_posts': self.stats['total_posts'],
                'failed_posts': self.stats['failed_posts'],
                'content_mode': self.content_mode
            })
            
            self.stats['total_posts'] += 1
            self.stats['failed_posts'] += 1
        
        finally:
            # Calculate and display execution time
            execution_end_time = datetime.now()
            execution_duration = execution_end_time - execution_start_time
            
            # Convert to human-readable format
            total_seconds = int(execution_duration.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            
            if minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"
            
            print(f"⏱️ Execution completed in: {duration_str}")
            print(f"🏁 Finished at: {execution_end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def _post_news_content(self) -> bool:
        """Post news content to Facebook"""
        try:
            # Ensure we have articles available
            available_articles = self.ensure_articles_available()
            
            if not available_articles:
                print("❌ No news articles available for posting")
                return False
            
            # Select an article
            article = self.select_article_for_posting(available_articles)
            
            if not article:
                print("❌ No suitable news article found for posting")
                return False
            
            print(f"📋 Selected news article: {article.get('title', '')[:50]}...")
            
            # Generate content
            facebook_content = self.content_generator.generate_content_from_news(article, "facebook")
            
            if facebook_content is None:
                print("🚫 Content rejected by LLM due to guidelines - skipping this article")
                return False
            elif not facebook_content:
                print("❌ Failed to generate news content")
                return False
            
            # Get image URL from article
            image_url = article.get('image_url') or article.get('urlToImage')
            
            # Post to Facebook
            print("📤 Posting news to Facebook...")
            facebook_response = self.facebook_service.smart_post(
                facebook_content, 
                image_url, 
                article.get('title', ''), 
                article.get('description', '')
            )
            
            if facebook_response and facebook_response.get('id'):
                # Mark article as posted in cache
                self.news_fetcher.mark_as_posted(article)
                
                print(f"✅ Successfully posted news! Post ID: {facebook_response.get('id')}")
                return True
            else:
                print("❌ Failed to post news to Facebook")
                return False
                
        except Exception as e:
            print(f"❌ Error posting news content: {e}")
            return False

    def _post_reddit_content(self) -> bool:
        """Post Reddit content to Facebook"""
        try:
            # Check for unposted Reddit posts in cache
            unposted_reddit = self.reddit_cache.get_unposted_reddit_posts(limit=10)
            
            if not unposted_reddit:
                print("📦 No Reddit posts in cache, fetching new ones with fresh content strategy...")
                # Fetch and cache new Reddit posts with enhanced freshness
                new_reddit_posts = self.content_generator.fetch_and_cache_reddit_posts(
                    limit=50, 
                    ensure_fresh=True  # Enable fresh content strategy
                )
                
                if new_reddit_posts:
                    # Cache the new posts with enhanced duplicate detection
                    cached_count = self.reddit_cache.cache_reddit_posts(new_reddit_posts)
                    print(f"💾 Successfully cached {cached_count} new Reddit posts")
                    unposted_reddit = self.reddit_cache.get_unposted_reddit_posts(limit=10)
                else:
                    print("⚠️ No new Reddit posts fetched - all may be duplicates")
                
                if not unposted_reddit:
                    print("❌ No Reddit posts available for posting after fetching")
                    return False
            
            # Select the best Reddit post
            reddit_post = self.reddit_cache.select_best_reddit_post()
            
            if not reddit_post:
                print("❌ No suitable Reddit post found for posting")
                return False
            
            print(f"📋 Selected Reddit post: {reddit_post.get('title', '')[:50]}...")
            
            # Generate content from Reddit post
            facebook_content = self.content_generator.generate_content_from_reddit(reddit_post, "facebook")
            
            if facebook_content is None:
                print("🚫 Reddit content rejected by LLM due to guidelines - skipping this post")
                return False
            elif not facebook_content:
                print("❌ Failed to generate Reddit content")
                return False
            
            # Get media URL from Reddit post (could be video or image)
            media_url = reddit_post.get('image_url')
            preview_images = reddit_post.get('preview_images', [])
            
            # Post to Facebook with proper video/image detection
            print("📤 Posting Reddit content to Facebook...")
            facebook_response = self.facebook_service.smart_post(
                facebook_content, 
                media_url, 
                reddit_post.get('title', ''), 
                reddit_post.get('selftext', '')[:200] if reddit_post.get('selftext') else '',
                preview_images
            )
            
            if facebook_response and facebook_response.get('id'):
                # Mark Reddit post as posted
                self.reddit_cache.mark_reddit_post_as_posted(reddit_post, facebook_response.get('id'))
                
                print(f"✅ Successfully posted Reddit content! Post ID: {facebook_response.get('id')}")
                return True
            else:
                print("❌ Failed to post Reddit content to Facebook")
                return False
                
        except Exception as e:
            print(f"❌ Error posting Reddit content: {e}")
            return False
    
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
        reddit_stats = self.reddit_cache.get_reddit_cache_stats()
        
        print(f"\n📊 Automation Statistics:")
        print(f"   Runtime: {runtime}")
        print(f"   Total posts attempted: {self.stats['total_posts']}")
        print(f"   Successful posts: {self.stats['successful_posts']}")
        print(f"   Failed posts: {self.stats['failed_posts']}")
        print(f"   Success rate: {(self.stats['successful_posts']/max(1, self.stats['total_posts'])*100):.1f}%")
        print(f"   📰 News posts: {self.stats['news_posts']}")
        print(f"   👻 Reddit posts: {self.stats['reddit_posts']}")
        
        print(f"\n📦 News Cache Statistics:")
        print(f"   Total articles in cache: {cache_stats.get('total', 0)}")
        print(f"   Unposted articles: {cache_stats.get('unposted', 0)}")
        print(f"   Posted articles: {cache_stats.get('posted', 0)}")
        print(f"   Total posted (all time): {cache_stats.get('total_posted', 0)}")
        
        print(f"\n👻 Reddit Cache Statistics:")
        print(f"   Total Reddit posts in cache: {reddit_stats.get('total_cached', 0)}")
        print(f"   Unposted Reddit posts: {reddit_stats.get('unposted', 0)}")
        print(f"   Posted Reddit posts: {reddit_stats.get('posted_from_cache', 0)}")
        print(f"   Total Reddit posted (all time): {reddit_stats.get('total_posted_ever', 0)}")
    
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
        
        # Calculate and display next execution time
        next_execution = datetime.now() + timedelta(minutes=interval_minutes)
        print(f"⏰ Scheduler started. Posting every {interval_minutes} minutes.")
        print(f"🕐 Next execution will start at: {next_execution.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Press Ctrl+C to stop.")
        
        # Keep the scheduler running
        try:
            while True:
                schedule.run_pending()
                
                # Show next execution time every cycle
                if schedule.jobs:
                    next_run = schedule.next_run()
                    if next_run:
                        print(f"🕐 Next execution scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
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
