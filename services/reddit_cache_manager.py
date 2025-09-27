"""
Reddit cache manager for storing and managing Reddit posts
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class RedditCacheManager:
    def __init__(self, cache_dir: str = "db/cache"):
        self.cache_dir = cache_dir
        self.reddit_cache_file = os.path.join(cache_dir, "reddit_cache.json")
        self.posted_reddit_file = os.path.join(cache_dir, "posted_reddit.json")
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize cache files if they don't exist
        self._init_cache_files()
    
    def _init_cache_files(self):
        """Initialize cache files if they don't exist"""
        if not os.path.exists(self.reddit_cache_file):
            self._save_json(self.reddit_cache_file, [])
        
        if not os.path.exists(self.posted_reddit_file):
            self._save_json(self.posted_reddit_file, [])
    
    def _load_json(self, file_path: str) -> Any:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_json(self, file_path: str, data: Any):
        """Save JSON data to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving to {file_path}: {e}")
    
    def _generate_post_id(self, reddit_post: Dict[str, Any]) -> str:
        """Generate a unique ID for a Reddit post - ALWAYS use Reddit's native ID"""
        # ALWAYS use Reddit's own ID - this is the primary unique identifier
        if 'id' in reddit_post and reddit_post['id']:
            return str(reddit_post['id'])
        
        # If no Reddit ID, this is likely invalid data - log and create fallback
        print(f"⚠️ WARNING: Reddit post missing native ID, creating fallback hash")
        print(f"   Title: {reddit_post.get('title', 'No title')[:50]}...")
        print(f"   Subreddit: {reddit_post.get('subreddit', 'Unknown')}")
        
        # Fallback: generate hash from title + subreddit + created_utc for uniqueness
        content = f"{reddit_post.get('title', '')}{reddit_post.get('subreddit', '')}{reddit_post.get('created_utc', '')}"
        fallback_id = hashlib.md5(content.encode()).hexdigest()[:12]
        print(f"   Generated fallback ID: {fallback_id}")
        return fallback_id
    
    def cache_reddit_posts(self, posts: List[Dict[str, Any]]) -> int:
        """Cache Reddit posts, avoiding duplicates with enhanced logging"""
        if not posts:
            print("⚠️ No posts provided to cache")
            return 0
        
        print(f"🔍 Processing {len(posts)} Reddit posts for caching...")
        
        # Load existing cache
        cached_posts = self._load_json(self.reddit_cache_file)
        posted_posts = self._load_json(self.posted_reddit_file)
        
        # Create sets of existing IDs for quick lookup
        cached_ids = {self._generate_post_id(post) for post in cached_posts}
        posted_ids = {post.get('post_id', '') for post in posted_posts}
        
        print(f"📊 Current cache status:")
        print(f"   - Already cached: {len(cached_ids)} posts")
        print(f"   - Already posted: {len(posted_ids)} posts")
        
        new_posts = []
        duplicate_count = 0
        already_posted_count = 0
        
        for post in posts:
            post_id = self._generate_post_id(post)
            title = post.get('title', 'No title')[:50]
            subreddit = post.get('subreddit', 'Unknown')
            
            # Check if already posted
            if post_id in posted_ids:
                already_posted_count += 1
                print(f"🚫 DUPLICATE (Already Posted): ID={post_id}")
                print(f"   Title: {title}...")
                print(f"   Subreddit: r/{subreddit}")
                print(f"   ⏭️ SKIPPING - Moving to next post")
                continue
            
            # Check if already cached
            if post_id in cached_ids:
                duplicate_count += 1
                print(f"🚫 DUPLICATE (Already Cached): ID={post_id}")
                print(f"   Title: {title}...")
                print(f"   Subreddit: r/{subreddit}")
                print(f"   ⏭️ SKIPPING - Moving to next post")
                continue
            
            # New post - add to cache
            post['cached_at'] = datetime.now().isoformat()
            post['post_id'] = post_id
            post['posted'] = False
            
            new_posts.append(post)
            cached_ids.add(post_id)
            
            print(f"✅ NEW POST CACHED: ID={post_id}")
            print(f"   Title: {title}...")
            print(f"   Subreddit: r/{subreddit}")
            print(f"   Score: {post.get('score', 0)} upvotes")
        
        # Summary logging
        print(f"\n📈 CACHING SUMMARY:")
        print(f"   📥 Total posts processed: {len(posts)}")
        print(f"   ✅ New posts cached: {len(new_posts)}")
        print(f"   🚫 Duplicates (already cached): {duplicate_count}")
        print(f"   🚫 Duplicates (already posted): {already_posted_count}")
        print(f"   📊 Duplicate rate: {((duplicate_count + already_posted_count) / len(posts) * 100):.1f}%")
        
        if new_posts:
            # Add new posts to cache
            cached_posts.extend(new_posts)
            
            # Sort by score (popularity) descending
            cached_posts.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Save updated cache
            self._save_json(self.reddit_cache_file, cached_posts)
            
            print(f"💾 Cache updated with {len(new_posts)} new Reddit posts")
        else:
            print("ℹ️ No new Reddit posts to cache - all were duplicates")
        
        return len(new_posts)
    
    def get_unposted_reddit_posts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get unposted Reddit posts from cache"""
        cached_posts = self._load_json(self.reddit_cache_file)
        posted_posts = self._load_json(self.posted_reddit_file)
        
        # Create set of posted IDs
        posted_ids = {post.get('post_id', '') for post in posted_posts}
        
        # Filter unposted posts
        unposted = [
            post for post in cached_posts 
            if not post.get('posted', False) and self._generate_post_id(post) not in posted_ids
        ]
        
        # Sort by score (popularity)
        unposted.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        if limit:
            unposted = unposted[:limit]
        
        return unposted
    
    def mark_reddit_post_as_posted(self, reddit_post: Dict[str, Any], facebook_post_id: str = None):
        """Mark a Reddit post as posted"""
        post_id = self._generate_post_id(reddit_post)
        
        # Load posted posts
        posted_posts = self._load_json(self.posted_reddit_file)
        
        # Add to posted list
        posted_entry = {
            'post_id': post_id,
            'reddit_title': reddit_post.get('title', ''),
            'subreddit': reddit_post.get('subreddit', ''),
            'reddit_score': reddit_post.get('score', 0),
            'posted_at': datetime.now().isoformat(),
            'facebook_post_id': facebook_post_id,
            'source': 'reddit'
        }
        
        posted_posts.append(posted_entry)
        self._save_json(self.posted_reddit_file, posted_posts)
        
        # Update cache to mark as posted
        cached_posts = self._load_json(self.reddit_cache_file)
        for post in cached_posts:
            if self._generate_post_id(post) == post_id:
                post['posted'] = True
                post['posted_at'] = datetime.now().isoformat()
                break
        
        self._save_json(self.reddit_cache_file, cached_posts)
        
        print(f"✅ Marked Reddit post as posted: {reddit_post.get('title', '')[:50]}...")
    
    def get_reddit_cache_stats(self) -> Dict[str, int]:
        """Get Reddit cache statistics"""
        cached_posts = self._load_json(self.reddit_cache_file)
        posted_posts = self._load_json(self.posted_reddit_file)
        
        unposted_count = len([
            post for post in cached_posts 
            if not post.get('posted', False)
        ])
        
        return {
            'total_cached': len(cached_posts),
            'unposted': unposted_count,
            'posted_from_cache': len(cached_posts) - unposted_count,
            'total_posted_ever': len(posted_posts)
        }
    
    def clean_old_reddit_posts(self, days_old: int = 7):
        """Remove old Reddit posts from cache"""
        cached_posts = self._load_json(self.reddit_cache_file)
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Filter out old posts
        fresh_posts = []
        removed_count = 0
        
        for post in cached_posts:
            cached_at = post.get('cached_at')
            if cached_at:
                try:
                    post_date = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
                    if post_date > cutoff_date:
                        fresh_posts.append(post)
                    else:
                        removed_count += 1
                except:
                    # Keep posts with invalid dates
                    fresh_posts.append(post)
            else:
                # Keep posts without cached_at date
                fresh_posts.append(post)
        
        if removed_count > 0:
            self._save_json(self.reddit_cache_file, fresh_posts)
            print(f"🧹 Cleaned {removed_count} old Reddit posts from cache")
        
        return removed_count
    
    def reset_reddit_cache(self):
        """Reset Reddit cache completely"""
        self._save_json(self.reddit_cache_file, [])
        self._save_json(self.posted_reddit_file, [])
        print("🗑️ Reddit cache reset complete")
    
    def get_top_reddit_posts_by_subreddit(self, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Get top unposted Reddit posts grouped by subreddit"""
        unposted = self.get_unposted_reddit_posts()
        
        # Group by subreddit
        by_subreddit = {}
        for post in unposted:
            subreddit = post.get('subreddit', 'unknown')
            if subreddit not in by_subreddit:
                by_subreddit[subreddit] = []
            by_subreddit[subreddit].append(post)
        
        # Limit posts per subreddit
        for subreddit in by_subreddit:
            by_subreddit[subreddit] = by_subreddit[subreddit][:limit]
        
        return by_subreddit
    
    def select_best_reddit_post(self) -> Optional[Dict[str, Any]]:
        """Select the best Reddit post for posting based on score and freshness"""
        unposted = self.get_unposted_reddit_posts(limit=20)  # Get top 20 candidates
        
        if not unposted:
            return None
        
        # Score posts based on multiple factors
        scored_posts = []
        
        for post in unposted:
            score = 0
            
            # Reddit score (upvotes)
            reddit_score = post.get('score', 0)
            score += min(reddit_score / 10, 50)  # Cap at 50 points
            
            # Prefer posts with text content
            if post.get('selftext') and len(post.get('selftext', '').strip()) > 50:
                score += 20
            
            # Prefer certain subreddits
            subreddit = post.get('subreddit', '').lower()
            if subreddit in ['paranormal', 'ghosts', 'highstrangeness']:
                score += 15
            elif subreddit in ['ufos', 'aliens', 'cryptids']:
                score += 10
            
            # Prefer posts with engaging titles
            title = post.get('title', '').lower()
            engaging_words = ['help', 'experience', 'happened', 'saw', 'heard', 'real', 'true']
            for word in engaging_words:
                if word in title:
                    score += 5
            
            scored_posts.append((post, score))
        
        # Sort by score and return the best one
        scored_posts.sort(key=lambda x: x[1], reverse=True)
        
        if scored_posts:
            best_post = scored_posts[0][0]
            print(f"📋 Selected Reddit post: {best_post.get('title', '')[:50]}... (Score: {scored_posts[0][1]:.1f})")
            return best_post
        
        return None
