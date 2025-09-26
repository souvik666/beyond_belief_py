"""
Facebook News Automation - Main Entry Point
Automatically posts news content to Facebook every 10 minutes
"""

import sys
import argparse
from services.automation_service import NewsAutomationService, CronAutomationService

def main():
    parser = argparse.ArgumentParser(description='Facebook News Automation Service')
    parser.add_argument('command', choices=['start', 'schedule', 'test', 'setup-cron', 'remove-cron', 'info', 'cache', 'reset-cache', 'stats', 'docker', 'reddit-only', 'news-only'], 
                       help='Command to execute')
    parser.add_argument('--interval', type=int, help='Custom interval in minutes for start command')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        # Start the continuous automation with optional custom interval
        automation = NewsAutomationService()
        if args.interval:
            automation.start_automation(args.interval)
        else:
            automation.start_automation()  # Default 10 minutes
    
    elif args.command == 'schedule':
        # Interactive schedule selection
        automation = NewsAutomationService()
        automation.choose_schedule_and_start()
    
    elif args.command == 'test':
        # Run a single test post
        automation = NewsAutomationService()
        automation.run_single_post()
    
    elif args.command == 'cache':
        # Setup preferences and cache articles
        automation = NewsAutomationService()
        automation.setup_and_cache_articles()
    
    elif args.command == 'reset-cache':
        # Reset cache files
        automation = NewsAutomationService()
        automation.reset_cache()
    
    elif args.command == 'stats':
        # Show statistics
        automation = NewsAutomationService()
        automation.print_stats()
    
    elif args.command == 'setup-cron':
        # Set up system cron job
        cron_service = CronAutomationService()
        if not cron_service.setup_cron_job():
            print("Falling back to Python scheduler...")
            automation = NewsAutomationService()
            automation.choose_schedule_and_start()
    
    elif args.command == 'remove-cron':
        # Remove system cron job
        cron_service = CronAutomationService()
        cron_service.remove_cron_job()
    
    elif args.command == 'docker':
        # Docker mode - non-interactive automation with auto-setup
        print("🐳 Docker Mode - Non-interactive automation")
        print("🤖 Auto-configuring preferences...")
        
        automation = NewsAutomationService()
        
        # Auto-setup preferences without user input
        automation.preferences = {
            'topics': ['general', 'technology', 'business', 'politics'],
            'countries': ['in', 'jp', 'pk', 'bd'],  # India, Japan, Pakistan, Bangladesh
            'queries': [
                'technology news',
                'business updates', 
                'political developments',
                'congress party',
                'bangladesh news',
                'pakistan news',
                'strange news',
                'paranormal events'
            ]
        }
        
        print("✅ Auto-configured preferences:")
        print(f"   Topics: {automation.preferences['topics']}")
        print(f"   Countries: {automation.preferences['countries']}")
        print(f"   Queries: {len(automation.preferences['queries'])} search terms")
        
        # Start automation with custom interval or default
        interval = args.interval if args.interval else 10
        print(f"🚀 Starting automation with {interval} minute interval...")
        automation.start_automation(interval)
    
    elif args.command == 'reddit-only':
        # Reddit-only automation mode
        print("👻 Reddit-Only Mode - Paranormal Content from Reddit")
        print("🎯 This mode will only post content from Reddit paranormal subreddits")
        
        automation = NewsAutomationService()
        automation.set_content_mode('reddit_only')
        
        # Start automation with custom interval or default
        interval = args.interval if args.interval else 10
        print(f"🚀 Starting Reddit-only automation with {interval} minute interval...")
        automation.start_automation(interval)
    
    elif args.command == 'news-only':
        # News-only automation mode
        print("📰 News-Only Mode - Traditional News Content")
        print("🎯 This mode will only post news articles (no Reddit content)")
        
        automation = NewsAutomationService()
        automation.set_content_mode('news_only')
        
        # Start automation with custom interval or default
        interval = args.interval if args.interval else 10
        print(f"🚀 Starting News-only automation with {interval} minute interval...")
        automation.start_automation(interval)
    
    elif args.command == 'info':
        # Show page information
        automation = NewsAutomationService()
        automation.get_page_info()
        print("\n🚀 Available Commands:")
        print("=" * 60)
        print("  python main.py schedule              - Interactive schedule selection")
        print("  python main.py start                 - Start mixed mode (10 min)")
        print("  python main.py start --interval 5    - Start mixed mode with custom interval")
        print("  python main.py reddit-only           - Start Reddit-only mode (10 min)")
        print("  python main.py reddit-only --interval 5 - Reddit-only with custom interval")
        print("  python main.py news-only             - Start News-only mode (10 min)")
        print("  python main.py news-only --interval 5   - News-only with custom interval")
        print("  python main.py test                  - Run a single test post")
        print("  python main.py cache                 - Setup preferences & cache articles")
        print("  python main.py stats                 - Show statistics")
        print("  python main.py reset-cache           - Reset cache files")
        print("  python main.py setup-cron            - Set up system cron job")
        print("  python main.py remove-cron           - Remove system cron job")
        print("  python main.py info                  - Show this information")
        print("\n📊 Content Modes:")
        print("  Mixed Mode (default): Alternates between news and Reddit content")
        print("  Reddit-Only Mode: Posts only paranormal content from Reddit")
        print("  News-Only Mode: Posts only traditional news articles")
        print("\n⏰ Schedule Options:")
        print("  Fast: 5 minutes   | Mid: 15 minutes   | Slow: 30 minutes")
        print("\n📰 Features:")
        print("  • Video and image posting support")
        print("  • 60+ paranormal subreddits for Reddit content")
        print("  • AI-generated content and images")
        print("  • Smart caching system (300 articles per batch)")
        print("  • Automatic fallback systems for robust posting")

if __name__ == "__main__":
    main()
