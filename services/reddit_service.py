import praw
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from constants import reddit_subs

# Load environment variables
load_dotenv()

class RedditService:
    """
    Service to interact with Reddit API:
    - CRUD posts
    - Get trending topics
    """
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None, username: str = None, password: str = None):
        """
        Initializes Reddit API client.
        For read-only operations, username/password can be None.
        If credentials are not provided, they will be loaded from environment variables.
        """
        # Use provided credentials or load from environment
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'beyond_belief_app/1.0')
        self.username = username or os.getenv('REDDIT_USERNAME')
        self.password = password or os.getenv('REDDIT_PASSWORD')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit client_id and client_secret are required. Set them in .env file or pass as parameters.")
        
        if self.username and self.password:
            # Full authenticated client
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent=self.user_agent
            )
        else:
            # Read-only client
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )

    # ---------------------------
    # CRUD Methods
    # ---------------------------

    def create_post(self, subreddit: str, title: str, selftext: str = "", url: str = None) -> str:
        """
        Create a post in a subreddit. Either selftext or URL must be provided.
        Requires authenticated client (username/password).
        """
        if not self.username or not self.password:
            raise ValueError("Authentication required for creating posts. Set REDDIT_USERNAME and REDDIT_PASSWORD in .env")
        
        sub = self.reddit.subreddit(subreddit)
        if url:
            submission = sub.submit(title, url=url)
        else:
            submission = sub.submit(title, selftext=selftext)
        return submission.id

    def read_post(self, post_id: str) -> Dict:
        """
        Read a post by ID.
        """
        submission = self.reddit.submission(id=post_id)
        return {
            "id": submission.id,
            "title": submission.title,
            "author": str(submission.author),
            "subreddit": str(submission.subreddit),
            "score": submission.score,
            "url": submission.url,
            "selftext": submission.selftext,
            "created_utc": submission.created_utc,
            "num_comments": submission.num_comments
        }

    def update_post(self, post_id: str, new_selftext: str) -> bool:
        """
        Update the text of a self post (only possible if you are the author).
        Requires authenticated client.
        """
        if not self.username or not self.password:
            raise ValueError("Authentication required for updating posts. Set REDDIT_USERNAME and REDDIT_PASSWORD in .env")
        
        submission = self.reddit.submission(id=post_id)
        submission.edit(new_selftext)
        return True

    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post (only possible if you are the author).
        Requires authenticated client.
        """
        if not self.username or not self.password:
            raise ValueError("Authentication required for deleting posts. Set REDDIT_USERNAME and REDDIT_PASSWORD in .env")
        
        submission = self.reddit.submission(id=post_id)
        submission.delete()
        return True

    # ---------------------------
    # Fetch Trending Topics
    # ---------------------------

    def get_top_posts(self, subreddit_name: str, limit: int = 10, time_filter: str = "day") -> List[Dict]:
        """
        Get top posts from a subreddit.
        time_filter can be: hour, day, week, month, year, all
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        try:
            for submission in subreddit.top(time_filter=time_filter, limit=limit):
                # Extract image information
                image_data = self._extract_image_data(submission)
                
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "score": submission.score,
                    "url": submission.url,
                    "author": str(submission.author),
                    "subreddit": str(submission.subreddit),
                    "created_utc": submission.created_utc,
                    "num_comments": submission.num_comments,
                    "selftext": submission.selftext[:200] + "..." if len(submission.selftext) > 200 else submission.selftext,
                    # Image data
                    "image_url": image_data.get("image_url"),
                    "thumbnail": image_data.get("thumbnail"),
                    "has_image": image_data.get("has_image", False),
                    "post_hint": getattr(submission, 'post_hint', None),
                    "preview_images": image_data.get("preview_images", [])
                })
        except Exception as e:
            print(f"Error fetching posts from r/{subreddit_name}: {e}")
            
        return posts

    def get_hot_posts(self, subreddit_name: str, limit: int = 10) -> List[Dict]:
        """
        Get hot posts from a subreddit.
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        try:
            for submission in subreddit.hot(limit=limit):
                # Extract image information
                image_data = self._extract_image_data(submission)
                
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "score": submission.score,
                    "url": submission.url,
                    "author": str(submission.author),
                    "subreddit": str(submission.subreddit),
                    "created_utc": submission.created_utc,
                    "num_comments": submission.num_comments,
                    "selftext": submission.selftext[:200] + "..." if len(submission.selftext) > 200 else submission.selftext,
                    # Image data
                    "image_url": image_data.get("image_url"),
                    "thumbnail": image_data.get("thumbnail"),
                    "has_image": image_data.get("has_image", False),
                    "post_hint": getattr(submission, 'post_hint', None),
                    "preview_images": image_data.get("preview_images", [])
                })
        except Exception as e:
            print(f"Error fetching hot posts from r/{subreddit_name}: {e}")
            
        return posts

    def get_paranormal_trending(self, subs: List[str] = None, limit: int = 10, time_filter: str = "day", ensure_fresh: bool = True, logger=None, cache_manager=None) -> Dict[str, List[Dict]]:
        """
        Get top posts from a list of paranormal subs with enhanced freshness strategies.
        Returns dictionary keyed by subreddit name.
        Enhanced with video-rich paranormal subreddits and dynamic content fetching.
        Now includes progressive caching to prevent data loss.
        """
        import time
        import random
        from datetime import datetime, timedelta
        
        if subs is None:
            # Enhanced list with more video-rich paranormal subreddits
            subs = reddit_subs

        print(f"🔍 Fetching fresh content from {len(subs)} subreddits...")
        print(f"📊 Strategy: {'Fresh content prioritized' if ensure_fresh else 'Standard fetching'}")
        print(f"💾 Progressive caching: {'ENABLED' if cache_manager else 'DISABLED'}")
        
        # Log the start of Reddit content fetching
        if logger:
            logger.log_step("REDDIT_CONTENT_FETCH_START", {
                'total_subreddits': len(subs),
                'limit_per_sub': limit,
                'time_filter': time_filter,
                'ensure_fresh': ensure_fresh,
                'progressive_caching': cache_manager is not None,
                'strategy': 'Fresh content prioritized' if ensure_fresh else 'Standard fetching'
            })
        
        # Dynamic time filters for freshness
        time_filters = ["hour", "day", "week"] if ensure_fresh else [time_filter]
        
        # Randomize subreddit order for variety
        if ensure_fresh:
            subs = random.sample(subs, len(subs))
            print(f"🔀 Randomized subreddit order for variety")

        trending = {}
        total_posts_fetched = 0
        successful_subs = 0
        failed_subs = 0
        subreddit_stats = []
        cached_posts_count = 0
        
        for i, sub in enumerate(subs):
            sub_start_time = datetime.now()
            try:
                print(f"📡 Fetching from r/{sub} ({i+1}/{len(subs)})...")
                
                # Use dynamic time filter for freshness
                current_time_filter = random.choice(time_filters) if ensure_fresh else time_filter
                
                # Fetch posts with current time filter
                posts = self.get_top_posts(subreddit_name=sub, limit=limit, time_filter=current_time_filter)
                
                # If no posts with current filter and ensure_fresh is True, try other filters
                if not posts and ensure_fresh and current_time_filter != "week":
                    print(f"   ⚠️ No posts with '{current_time_filter}' filter, trying 'week'...")
                    posts = self.get_top_posts(subreddit_name=sub, limit=limit, time_filter="week")
                
                # If still no posts, try hot posts as fallback
                if not posts and ensure_fresh:
                    print(f"   ⚠️ No top posts found, trying hot posts...")
                    posts = self.get_hot_posts(subreddit_name=sub, limit=limit)
                
                trending[sub] = posts
                posts_count = len(posts)
                total_posts_fetched += posts_count
                
                # PROGRESSIVE CACHING: Cache posts immediately after fetching from each subreddit
                if cache_manager and posts:
                    try:
                        # Add metadata to posts before caching
                        for post in posts:
                            post['source'] = 'reddit'
                            post['source_subreddit'] = sub
                            post['content_type'] = 'reddit_post'
                            post['fetch_strategy'] = 'fresh' if ensure_fresh else 'standard'
                            post['fetch_timestamp'] = datetime.now().isoformat()
                        
                        # Cache posts from this subreddit immediately
                        cached_count = cache_manager.cache_reddit_posts(posts)
                        cached_posts_count += cached_count
                        print(f"   💾 Cached {cached_count} posts from r/{sub} immediately")
                        
                        if logger:
                            logger.log_step("PROGRESSIVE_CACHE_SAVE", {
                                'subreddit': sub,
                                'posts_cached': cached_count,
                                'total_cached_so_far': cached_posts_count,
                                'subreddit_index': i + 1
                            })
                    except Exception as cache_error:
                        print(f"   ⚠️ Failed to cache posts from r/{sub}: {cache_error}")
                        if logger:
                            logger.log_step("PROGRESSIVE_CACHE_ERROR", {
                                'subreddit': sub,
                                'error': str(cache_error)
                            }, "warning")
                
                # Calculate fetch time for this subreddit
                sub_fetch_time = (datetime.now() - sub_start_time).total_seconds()
                
                # Track subreddit statistics
                sub_stats = {
                    'subreddit': sub,
                    'posts_fetched': posts_count,
                    'time_filter_used': current_time_filter,
                    'fetch_time_seconds': round(sub_fetch_time, 2),
                    'success': True
                }
                subreddit_stats.append(sub_stats)
                
                if posts_count > 0:
                    successful_subs += 1
                    print(f"   ✅ Fetched {posts_count} posts (filter: {current_time_filter}) in {sub_fetch_time:.1f}s")
                    
                    # Log detailed content count for this subreddit
                    if logger:
                        logger.log_step("SUBREDDIT_CONTENT_FETCHED", {
                            'subreddit': sub,
                            'posts_count': posts_count,
                            'time_filter': current_time_filter,
                            'fetch_time_seconds': sub_fetch_time,
                            'posts_with_images': sum(1 for post in posts if post.get('has_image')),
                            'posts_with_videos': sum(1 for post in posts if post.get('post_hint') == 'hosted:video'),
                            'average_score': round(sum(post.get('score', 0) for post in posts) / max(1, posts_count), 1),
                            'subreddit_index': i + 1,
                            'total_subreddits': len(subs)
                        })
                else:
                    print(f"   ⚠️ No posts fetched from r/{sub} (filter: {current_time_filter})")
                    if logger:
                        logger.log_step("SUBREDDIT_NO_CONTENT", {
                            'subreddit': sub,
                            'time_filter': current_time_filter,
                            'fetch_time_seconds': sub_fetch_time
                        }, "warning")
                
                # Add 3-second delay between requests to prevent rate limiting
                if i < len(subs) - 1:  # Don't delay after the last request
                    next_request_time = datetime.now() + timedelta(seconds=3)
                    print(f"   ⏳ Waiting 3 seconds before next request...")
                    print(f"   🕐 Next request at: {next_request_time.strftime('%H:%M:%S')}")
                    time.sleep(3)
                    
            except Exception as e:
                failed_subs += 1
                sub_fetch_time = (datetime.now() - sub_start_time).total_seconds()
                
                print(f"   ❌ Error fetching from r/{sub}: {e}")
                
                # Track failed subreddit statistics
                sub_stats = {
                    'subreddit': sub,
                    'posts_fetched': 0,
                    'time_filter_used': current_time_filter if 'current_time_filter' in locals() else time_filter,
                    'fetch_time_seconds': round(sub_fetch_time, 2),
                    'success': False,
                    'error': str(e)
                }
                subreddit_stats.append(sub_stats)
                
                # Log the error for this subreddit
                if logger:
                    logger.log_step("SUBREDDIT_FETCH_ERROR", {
                        'subreddit': sub,
                        'error': str(e),
                        'fetch_time_seconds': sub_fetch_time
                    }, "error")
                
                # Continue with other subreddits even if one fails
                trending[sub] = []
                continue
        
        # Calculate comprehensive statistics
        total_fetch_time = sum(stat['fetch_time_seconds'] for stat in subreddit_stats)
        posts_with_content = sum(1 for stat in subreddit_stats if stat['posts_fetched'] > 0)
        
        print(f"\n📈 FETCHING SUMMARY:")
        print(f"   📡 Subreddits processed: {len(subs)}")
        print(f"   ✅ Successful subreddits: {successful_subs}")
        print(f"   ❌ Failed subreddits: {failed_subs}")
        print(f"   📥 Total posts fetched: {total_posts_fetched}")
        print(f"   💾 Total posts cached: {cached_posts_count}")
        print(f"   📊 Average posts per subreddit: {total_posts_fetched/len(subs):.1f}")
        print(f"   📊 Average posts per successful subreddit: {total_posts_fetched/max(1, successful_subs):.1f}")
        print(f"   🎯 Time filters used: {time_filters}")
        print(f"   ⏱️ Total fetch time: {total_fetch_time:.1f} seconds")
        
        # Log comprehensive summary
        if logger:
            # Sort subreddits by posts fetched for better insights
            top_performing_subs = sorted([s for s in subreddit_stats if s['success']], 
                                       key=lambda x: x['posts_fetched'], reverse=True)[:10]
            
            logger.log_step("REDDIT_CONTENT_FETCH_COMPLETE", {
                'total_subreddits_processed': len(subs),
                'successful_subreddits': successful_subs,
                'failed_subreddits': failed_subs,
                'total_posts_fetched': total_posts_fetched,
                'total_posts_cached': cached_posts_count,
                'average_posts_per_subreddit': round(total_posts_fetched/len(subs), 2),
                'average_posts_per_successful_sub': round(total_posts_fetched/max(1, successful_subs), 2),
                'total_fetch_time_seconds': round(total_fetch_time, 2),
                'average_fetch_time_per_sub': round(total_fetch_time/len(subs), 2),
                'time_filters_used': time_filters,
                'top_performing_subreddits': top_performing_subs[:5],  # Top 5 for logging
                'subreddits_with_no_content': [s['subreddit'] for s in subreddit_stats if s['posts_fetched'] == 0],
                'content_distribution': {
                    'subs_with_1_5_posts': sum(1 for s in subreddit_stats if 1 <= s['posts_fetched'] <= 5),
                    'subs_with_6_10_posts': sum(1 for s in subreddit_stats if 6 <= s['posts_fetched'] <= 10),
                    'subs_with_more_than_10_posts': sum(1 for s in subreddit_stats if s['posts_fetched'] > 10)
                },
                'progressive_caching_enabled': cache_manager is not None
            })
            
            # Log detailed per-subreddit breakdown for analysis
            logger.log_step("SUBREDDIT_DETAILED_BREAKDOWN", {
                'subreddit_stats': subreddit_stats
            })
        
        return trending

    def search_posts(self, query: str, subreddit_name: str = None, limit: int = 10, sort: str = "relevance") -> List[Dict]:
        """
        Search for posts containing specific keywords.
        If subreddit_name is None, searches all of Reddit.
        sort can be: relevance, hot, top, new, comments
        """
        posts = []
        
        try:
            if subreddit_name:
                subreddit = self.reddit.subreddit(subreddit_name)
                search_results = subreddit.search(query, sort=sort, limit=limit)
            else:
                search_results = self.reddit.subreddit("all").search(query, sort=sort, limit=limit)
            
            for submission in search_results:
                # Extract image information
                image_data = self._extract_image_data(submission)
                
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "score": submission.score,
                    "url": submission.url,
                    "author": str(submission.author),
                    "subreddit": str(submission.subreddit),
                    "created_utc": submission.created_utc,
                    "num_comments": submission.num_comments,
                    "selftext": submission.selftext[:200] + "..." if len(submission.selftext) > 200 else submission.selftext,
                    # Image data
                    "image_url": image_data.get("image_url"),
                    "thumbnail": image_data.get("thumbnail"),
                    "has_image": image_data.get("has_image", False),
                    "post_hint": getattr(submission, 'post_hint', None),
                    "preview_images": image_data.get("preview_images", [])
                })
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            
        return posts

    def get_subreddit_info(self, subreddit_name: str) -> Dict:
        """
        Get information about a subreddit.
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            return {
                "name": subreddit.display_name,
                "title": subreddit.title,
                "description": subreddit.description,
                "subscribers": subreddit.subscribers,
                "created_utc": subreddit.created_utc,
                "over18": subreddit.over18,
                "public_description": subreddit.public_description
            }
        except Exception as e:
            print(f"Error getting info for r/{subreddit_name}: {e}")
            return {}

    def _extract_image_data(self, submission) -> Dict:
        """
        Extract image data from a Reddit submission based on the structure you provided
        """
        image_data = {
            "image_url": None,
            "thumbnail": None,
            "has_image": False,
            "preview_images": []
        }
        
        try:
            # Check if it's an image post
            post_hint = getattr(submission, 'post_hint', None)
            
            # Get main image URL
            if hasattr(submission, 'url_overridden_by_dest'):
                image_data["image_url"] = submission.url_overridden_by_dest
            elif submission.url and any(submission.url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                image_data["image_url"] = submission.url
            elif post_hint == 'image':
                image_data["image_url"] = submission.url
            
            # Get thumbnail
            if hasattr(submission, 'thumbnail') and submission.thumbnail not in ['self', 'default', 'nsfw', 'spoiler']:
                image_data["thumbnail"] = submission.thumbnail
            
            # Get preview images with different resolutions
            if hasattr(submission, 'preview') and submission.preview:
                try:
                    preview_data = submission.preview
                    if 'images' in preview_data and preview_data['images']:
                        first_image = preview_data['images'][0]
                        
                        # Add source image
                        if 'source' in first_image:
                            source = first_image['source']
                            image_data["preview_images"].append({
                                "url": source.get('url', '').replace('&amp;', '&'),
                                "width": source.get('width'),
                                "height": source.get('height'),
                                "type": "source"
                            })
                        
                        # Add different resolution images
                        if 'resolutions' in first_image:
                            for resolution in first_image['resolutions']:
                                image_data["preview_images"].append({
                                    "url": resolution.get('url', '').replace('&amp;', '&'),
                                    "width": resolution.get('width'),
                                    "height": resolution.get('height'),
                                    "type": "resolution"
                                })
                except Exception as e:
                    print(f"Error extracting preview images: {e}")
            
            # Determine if post has image
            image_data["has_image"] = bool(
                image_data["image_url"] or 
                image_data["thumbnail"] or 
                image_data["preview_images"] or
                post_hint == 'image'
            )
            
            # If no main image URL but we have preview images, use the largest one
            if not image_data["image_url"] and image_data["preview_images"]:
                # Find the largest image
                largest_image = max(image_data["preview_images"], 
                                  key=lambda x: (x.get('width', 0) * x.get('height', 0)))
                image_data["image_url"] = largest_image["url"]
            
        except Exception as e:
            print(f"Error extracting image data: {e}")
        
        return image_data
