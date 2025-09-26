import praw
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

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

    def get_paranormal_trending(self, subs: List[str] = None, limit: int = 10, time_filter: str = "day") -> Dict[str, List[Dict]]:
        """
        Get top posts from a list of paranormal subs.
        Returns dictionary keyed by subreddit name.
        """
        if subs is None:
            subs = ["paranormal", "HighStrangeness", "ghosts", "UFOs", "aliens", "cryptids", "truecreepy", "Glitch_in_the_Matrix", "nosleep", "LetsNotMeet"]

        trending = {}
        for sub in subs:
            print(f"Fetching posts from r/{sub}...")
            trending[sub] = self.get_top_posts(subreddit_name=sub, limit=limit, time_filter=time_filter)
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
