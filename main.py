"""
Facebook News Automation - Main Entry Point
Automatically posts news content to Facebook every 10 minutes
"""

import sys
import argparse
from services.automation_service import NewsAutomationService, CronAutomationService

def main():
    parser = argparse.ArgumentParser(description='Facebook News Automation Service')
    parser.add_argument('command', choices=['start', 'schedule', 'test', 'setup-cron', 'remove-cron', 'info', 'cache', 'reset-cache', 'stats'], 
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
    
    elif args.command == 'info':
        # Show page information
        automation = NewsAutomationService()
        automation.get_page_info()
        print("\n🚀 Available Commands:")
        print("=" * 50)
        print("  python main.py schedule              - Interactive schedule selection")
        print("  python main.py start                 - Start with default (10 min)")
        print("  python main.py start --interval 5    - Start with custom interval")
        print("  python main.py test                  - Run a single test post")
        print("  python main.py cache                 - Setup preferences & cache articles")
        print("  python main.py stats                 - Show statistics")
        print("  python main.py reset-cache           - Reset cache files")
        print("  python main.py setup-cron            - Set up system cron job")
        print("  python main.py remove-cron           - Remove system cron job")
        print("  python main.py info                  - Show this information")
        print("\n⏰ Schedule Options:")
        print("  Fast: 5 minutes   | Mid: 15 minutes   | Slow: 30 minutes")
        print("\n📰 News Focus:")
        print("  Paranormal/Strange news with AI-generated content")
        print("  Automatic image downloading from news articles")
        print("  Smart caching system (300 articles per batch)")

if __name__ == "__main__":
    main()

