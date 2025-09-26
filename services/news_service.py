"""
Advanced news fetcher with caching and paranormal/strange news focus
"""

import os
import json
import requests
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class NewsFetcher:
    def __init__(self):
        self.api_key = os.getenv('NEWS_DATA_API')
        if not self.api_key:
            raise ValueError("NEWS_DATA_API not found in environment variables")
        
        # Create db folder structure
        from pathlib import Path
        self.db_folder = Path("db")
        self.db_folder.mkdir(exist_ok=True)
        (self.db_folder / "cache").mkdir(exist_ok=True)
        
        # Cache files in db folder
        self.cache_file = self.db_folder / "cache" / "news_cache.json"
        self.posted_file = self.db_folder / "cache" / "posted_articles.json"
        
        # All Indian states
        self.indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir"
        ]
        
        # Paranormal/Strange news queries
        self.strange_queries = [
            "strange", "mysterious", "paranormal", "unexplained", "bizarre",
            "supernatural", "ghost", "haunted", "miracle", "unusual",
            "weird", "extraordinary", "unbelievable", "shocking", "rare",
            "alien", "UFO", "psychic", "spiritual", "divine", "mystical"
        ]
        
        # News topics
        self.topics = [
            "general", "politics", "business", "technology", "sports",
            "entertainment", "health", "science", "environment", "crime",
            "education", "religion", "culture", "paranormal", "strange"
        ]
        
        # Countries for broader strange news
        self.countries = ["in", "jp", "pk", "bd", "us", "uk", "au"]

    def choose_preferences(self) -> Dict[str, Any]:
        """Interactive preference selection"""
        print("\n🎯 Configure News Preferences")
        print("=" * 40)
        
        # Topic selection
        print("\n📰 Select News Topics:")
        print("1. Paranormal/Strange (recommended)")
        print("2. General News")
        print("3. Politics")
        print("4. Technology")
        print("5. Entertainment")
        print("6. Random Mix")
        print("7. Custom Selection")
        
        topic_choice = input("\nEnter choice (1-7): ").strip()
        
        if topic_choice == "1":
            topics = ["paranormal", "strange"]
            queries = self.strange_queries
        elif topic_choice == "2":
            topics = ["general"]
            queries = ["news", "breaking", "latest"]
        elif topic_choice == "3":
            topics = ["politics"]
            queries = ["politics", "government", "election"]
        elif topic_choice == "4":
            topics = ["technology"]
            queries = ["technology", "tech", "innovation"]
        elif topic_choice == "5":
            topics = ["entertainment"]
            queries = ["entertainment", "bollywood", "celebrity"]
        elif topic_choice == "6":
            topics = random.sample(self.topics, 3)
            queries = random.sample(self.strange_queries + ["news", "breaking"], 5)
        else:
            print("Available topics:", ", ".join(self.topics))
            custom_topics = input("Enter topics (comma-separated): ").strip().split(',')
            topics = [t.strip() for t in custom_topics if t.strip()]
            queries = self.strange_queries if "paranormal" in topics else ["news"]
        
        print(f"\n✅ Selected topics: {', '.join(topics)}")
        print(f"🌍 Using country-based queries: India, Japan, Pakistan, Bangladesh")
        
        return {
            'topics': topics,
            'queries': queries
        }

    def fetch_bulk_news(self, preferences: Dict[str, Any], total_articles: int = 300, logger=None) -> List[Dict[str, Any]]:
        """Fetch bulk news articles using country-based queries"""
        if logger:
            logger.log_step("FETCH_BULK_NEWS_START", {
                'total_articles_requested': total_articles,
                'topics': preferences['topics'],
                'queries_count': len(preferences['queries'])
            })
        
        print(f"\n🔄 Fetching {total_articles} articles with country-based queries...")
        print(f"Topics: {', '.join(preferences['topics'])}")
        
        all_articles = []
        queries = preferences['queries']
        
        # Use fixed country list as specified
        countries = "in,jp,pk,bd"  # India, Japan, Pakistan, Bangladesh
        
        # Calculate articles per query
        articles_per_query = max(1, total_articles // len(queries))
        
        for query in queries:
            if len(all_articles) >= total_articles:
                break
                
            try:
                # Build URL exactly as specified: only q parameter changes
                url = f"https://newsdata.io/api/1/latest?apikey={self.api_key}&q={query}&country={countries}"
                
                print(f"🔍 Fetching: {query} from countries: {countries}")
                
                if logger:
                    logger.log_step("API_REQUEST_START", {
                        'url': url,
                        'query': query,
                        'countries': countries
                    })
                
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if logger:
                    logger.log_api_call(url, query, countries, response.status_code, len(data.get('results', [])))
                
                if data.get('status') == 'success':
                    articles = data.get('results', [])
                    
                    for article in articles:
                        if len(all_articles) >= total_articles:
                            break
                        
                        # Enhance article with metadata
                        article.update({
                            'posted': False,
                            'fetch_timestamp': datetime.now().isoformat(),
                            'query_used': query,
                            'countries_searched': countries,
                            'topics': preferences['topics']
                        })
                        
                        all_articles.append(article)
                    
                    print(f"  ✅ Got {len(articles)} articles")
                    
                    if logger:
                        logger.log_step("API_REQUEST_SUCCESS", {
                            'query': query,
                            'articles_received': len(articles),
                            'total_articles_so_far': len(all_articles)
                        })
                    
                    time.sleep(1)  # Rate limiting
                else:
                    error_msg = f"API returned status: {data.get('status')}"
                    print(f"  ❌ {error_msg}")
                    if logger:
                        logger.log_error("API_STATUS_ERROR", error_msg, {'query': query, 'response': data})
                
            except Exception as e:
                error_msg = f"Error fetching {query}: {e}"
                print(f"  ❌ {error_msg}")
                if logger:
                    logger.log_error("API_REQUEST_ERROR", str(e), {'query': query, 'url': url})
                continue
        
        # Remove duplicates and save to cache
        unique_articles = self._remove_duplicates(all_articles)
        final_articles = unique_articles[:total_articles]
        
        if logger:
            logger.log_cache_operation("SAVE", {
                'total_articles_fetched': len(all_articles),
                'unique_articles': len(unique_articles),
                'final_articles_cached': len(final_articles)
            })
        
        self._save_cache(final_articles)
        print(f"💾 Cached {len(final_articles)} unique articles")
        
        if logger:
            logger.log_step("FETCH_BULK_NEWS_COMPLETE", {
                'articles_cached': len(final_articles),
                'cache_file': str(self.cache_file)
            })
        
        return final_articles

    def get_cached_articles(self) -> List[Dict[str, Any]]:
        """Get articles from cache"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            
            # Filter unposted articles
            unposted = [a for a in articles if not a.get('posted', False)]
            print(f"📦 Found {len(unposted)} unposted articles in cache")
            return unposted
            
        except FileNotFoundError:
            print("📦 No cache file found")
            return []
        except Exception as e:
            print(f"❌ Error reading cache: {e}")
            return []

    def mark_as_posted(self, article: Dict[str, Any]):
        """Mark an article as posted"""
        try:
            # Update cache
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            
            # Find and update the article
            for cached_article in articles:
                if cached_article.get('title') == article.get('title'):
                    cached_article['posted'] = True
                    cached_article['posted_timestamp'] = datetime.now().isoformat()
                    break
            
            # Save updated cache
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            # Also save to posted articles log
            self._log_posted_article(article)
            
        except Exception as e:
            print(f"❌ Error marking article as posted: {e}")

    def _save_cache(self, articles: List[Dict[str, Any]]):
        """Save articles to cache file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving cache: {e}")

    def _log_posted_article(self, article: Dict[str, Any]):
        """Log posted article to separate file"""
        try:
            # Load existing posted articles
            try:
                with open(self.posted_file, 'r', encoding='utf-8') as f:
                    posted_articles = json.load(f)
            except FileNotFoundError:
                posted_articles = []
            
            # Add new posted article
            posted_articles.append({
                'title': article.get('title'),
                'posted_timestamp': datetime.now().isoformat(),
                'query_used': article.get('query_used'),
                'location': article.get('location')
            })
            
            # Save updated posted articles
            with open(self.posted_file, 'w', encoding='utf-8') as f:
                json.dump(posted_articles, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Error logging posted article: {e}")

    def reset_cache(self):
        """Reset cache files"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            if os.path.exists(self.posted_file):
                os.remove(self.posted_file)
            print("🗑️ Cache files reset successfully")
        except Exception as e:
            print(f"❌ Error resetting cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Cache stats
            cache_stats = {'total': 0, 'unposted': 0, 'posted': 0}
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                cache_stats['total'] = len(articles)
                cache_stats['unposted'] = len([a for a in articles if not a.get('posted', False)])
                cache_stats['posted'] = cache_stats['total'] - cache_stats['unposted']
            
            # Posted stats
            posted_stats = {'total_posted': 0}
            if os.path.exists(self.posted_file):
                with open(self.posted_file, 'r', encoding='utf-8') as f:
                    posted_articles = json.load(f)
                posted_stats['total_posted'] = len(posted_articles)
            
            return {**cache_stats, **posted_stats}
            
        except Exception as e:
            print(f"❌ Error getting cache stats: {e}")
            return {}

    def _remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            title = article.get('title', '').lower()
            # Use first 6 words for better uniqueness
            simple_title = ' '.join(title.split()[:6])
            
            if simple_title not in seen_titles and simple_title and len(simple_title) > 10:
                seen_titles.add(simple_title)
                unique_articles.append(article)
        
        return unique_articles

    def should_refresh_cache(self, min_articles: int = 5) -> bool:
        """Check if cache should be refreshed - only when truly needed"""
        unposted = self.get_cached_articles()
        should_refresh = len(unposted) < min_articles
        
        if should_refresh:
            print(f"🔄 Cache refresh needed: only {len(unposted)} unposted articles remaining")
        else:
            print(f"📦 Cache sufficient: {len(unposted)} unposted articles available")
            
        return should_refresh
