import os
from dotenv import load_dotenv
from services.reddit_service import RedditService

# Load environment variables
load_dotenv()

def test_reddit_service():
    """
    Test the Reddit service with environment variables
    """
    print("Testing Reddit Service...")
    print("=" * 50)
    
    try:
        # Initialize Reddit service using environment variables
        reddit_service = RedditService()
        
        print("✅ Reddit service initialized successfully!")
        print(f"Client ID: {reddit_service.client_id[:10]}...")
        print(f"User Agent: {reddit_service.user_agent}")
        
        # Test getting paranormal trending topics
        print("\n🔍 Fetching paranormal trending topics...")
        trending = reddit_service.get_paranormal_trending(limit=5)
        
        for sub, posts in trending.items():
            print(f"\n📍 Top posts in r/{sub}:")
            if posts:
                for i, post in enumerate(posts[:3], 1):  # Show only top 3
                    print(f"  {i}. {post['title'][:80]}...")
                    print(f"     Score: {post['score']} | Comments: {post['num_comments']}")
                    print(f"     URL: {post['url']}")
            else:
                print("  No posts found or subreddit may be private/restricted")
        
        # Test search functionality
        print(f"\n🔎 Searching for 'ghost' posts...")
        search_results = reddit_service.search_posts("ghost", subreddit_name="paranormal", limit=3)
        
        if search_results:
            print(f"Found {len(search_results)} posts:")
            for i, post in enumerate(search_results, 1):
                print(f"  {i}. {post['title'][:80]}...")
                print(f"     Score: {post['score']} | r/{post['subreddit']}")
        else:
            print("No search results found")
        
        # Test getting hot posts
        print(f"\n🔥 Getting hot posts from r/paranormal...")
        hot_posts = reddit_service.get_hot_posts("paranormal", limit=3)
        
        if hot_posts:
            for i, post in enumerate(hot_posts, 1):
                print(f"  {i}. {post['title'][:80]}...")
                print(f"     Score: {post['score']} | Comments: {post['num_comments']}")
        else:
            print("No hot posts found")
        
        # Test subreddit info
        print(f"\n📊 Getting subreddit info for r/paranormal...")
        subreddit_info = reddit_service.get_subreddit_info("paranormal")
        
        if subreddit_info:
            print(f"  Name: {subreddit_info.get('name', 'N/A')}")
            print(f"  Title: {subreddit_info.get('title', 'N/A')}")
            print(f"  Subscribers: {subreddit_info.get('subscribers', 'N/A'):,}")
            print(f"  Description: {subreddit_info.get('public_description', 'N/A')[:100]}...")
        
        print("\n✅ All tests completed successfully!")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Make sure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are set in your .env file")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your Reddit API credentials and internet connection")

def test_environment_variables():
    """
    Test that environment variables are properly loaded
    """
    print("\n🔧 Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET']
    optional_vars = ['REDDIT_USERNAME', 'REDDIT_PASSWORD', 'REDDIT_USER_AGENT']
    
    print("Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value[:10]}...")
        else:
            print(f"  ❌ {var}: Not set")
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value[:10]}...")
        else:
            print(f"  ⚠️  {var}: Not set (using default)")

if __name__ == "__main__":
    # Test environment variables first
    test_environment_variables()
    
    # Test Reddit service
    test_reddit_service()
