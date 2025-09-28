"""
Facebook News Automation - Interactive Main Entry Point
Automatically posts news content to Facebook with interactive menu system
"""

import sys
import os
from services.automation_service import NewsAutomationService, CronAutomationService

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header"""
    print("=" * 70)
    print("🚀 BEYOND BELIEF - Facebook News Automation System")
    print("=" * 70)
    print("🤖 AI-Powered Content Generation with Gemini Fallback")
    print("📰 News + Reddit Content | 🔄 Auto-Posting | 📊 Analytics")
    print("=" * 70)

def print_menu():
    """Print the main menu options"""
    print("\n📋 MAIN MENU - Choose an option:")
    print("=" * 50)
    print("1️⃣  🚀 Start Automation (Mixed Mode)")
    print("2️⃣  📰 Start News-Only Mode")
    print("3️⃣  👻 Start Reddit-Only Mode")
    print("4️⃣  ⏰ Schedule Automation")
    print("5️⃣  🧪 Run Test Post")
    print("6️⃣  💾 Setup & Cache Content")
    print("7️⃣  📊 View Statistics")
    print("8️⃣  🗑️  Reset Cache")
    print("9️⃣  ⚙️  Cron Job Management")
    print("🔟  ℹ️  System Information")
    print("0️⃣  ❌ Exit")
    print("=" * 50)

def get_interval_choice():
    """Get interval choice from user"""
    print("\n⏰ Choose posting interval:")
    print("1. Fast (5 minutes)")
    print("2. Normal (10 minutes)")
    print("3. Medium (15 minutes)")
    print("4. Slow (30 minutes)")
    print("5. Custom interval")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice == "1":
                return 5
            elif choice == "2":
                return 10
            elif choice == "3":
                return 15
            elif choice == "4":
                return 30
            elif choice == "5":
                while True:
                    try:
                        custom = int(input("Enter custom interval in minutes (1-1440): "))
                        if 1 <= custom <= 1440:
                            return custom
                        else:
                            print("❌ Please enter a value between 1 and 1440 minutes")
                    except ValueError:
                        print("❌ Please enter a valid number")
            else:
                print("❌ Please enter a valid choice (1-5)")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)

def cron_management_menu():
    """Handle cron job management submenu"""
    cron_service = CronAutomationService()
    
    while True:
        print("\n⚙️ CRON JOB MANAGEMENT")
        print("=" * 30)
        print("1. Setup Cron Job")
        print("2. Remove Cron Job")
        print("3. Check Cron Status")
        print("4. Back to Main Menu")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                print("\n🔧 Setting up cron job...")
                if cron_service.setup_cron_job():
                    print("✅ Cron job setup successful!")
                else:
                    print("❌ Cron job setup failed. Falling back to Python scheduler...")
                    automation = NewsAutomationService()
                    automation.choose_schedule_and_start()
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                print("\n🗑️ Removing cron job...")
                cron_service.remove_cron_job()
                print("✅ Cron job removed!")
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                print("\n📋 Checking cron status...")
                # Add cron status check here if needed
                print("ℹ️ Check your system's cron jobs with: crontab -l")
                input("\nPress Enter to continue...")
                
            elif choice == "4":
                break
                
            else:
                print("❌ Please enter a valid choice (1-4)")
                
        except KeyboardInterrupt:
            print("\n\n👋 Returning to main menu...")
            break

def main():
    """Main interactive function"""
    try:
        while True:
            clear_screen()
            print_header()
            print_menu()
            
            try:
                choice = input("\n🎯 Enter your choice (0-10): ").strip()
                
                if choice == "0":
                    print("\n👋 Thank you for using Beyond Belief!")
                    print("🚀 Stay curious, stay automated!")
                    sys.exit(0)
                
                elif choice == "1":
                    # Start Mixed Mode Automation
                    print("\n🚀 Starting Mixed Mode Automation...")
                    print("📰 This mode alternates between news and Reddit content")
                    interval = get_interval_choice()
                    
                    automation = NewsAutomationService()
                    print(f"\n🎯 Starting automation with {interval} minute interval...")
                    automation.start_automation(interval)
                
                elif choice == "2":
                    # Start News-Only Mode
                    print("\n📰 Starting News-Only Mode...")
                    print("🎯 This mode will only post traditional news articles")
                    interval = get_interval_choice()
                    
                    automation = NewsAutomationService()
                    automation.set_content_mode('news_only')
                    print(f"\n🎯 Starting news-only automation with {interval} minute interval...")
                    automation.start_automation(interval)
                
                elif choice == "3":
                    # Start Reddit-Only Mode
                    print("\n👻 Starting Reddit-Only Mode...")
                    print("🎯 This mode will only post paranormal content from Reddit")
                    interval = get_interval_choice()
                    
                    automation = NewsAutomationService()
                    automation.set_content_mode('reddit_only')
                    print(f"\n🎯 Starting Reddit-only automation with {interval} minute interval...")
                    automation.start_automation(interval)
                
                elif choice == "4":
                    # Schedule Automation
                    print("\n⏰ Interactive Schedule Selection...")
                    automation = NewsAutomationService()
                    automation.choose_schedule_and_start()
                
                elif choice == "5":
                    # Run Test Post
                    print("\n🧪 Running test post...")
                    automation = NewsAutomationService()
                    automation.run_single_post()
                    input("\nPress Enter to continue...")
                
                elif choice == "6":
                    # Setup & Cache Content
                    print("\n💾 Setting up preferences and caching content...")
                    automation = NewsAutomationService()
                    automation.setup_and_cache_articles()
                    input("\nPress Enter to continue...")
                
                elif choice == "7":
                    # View Statistics
                    print("\n📊 Displaying statistics...")
                    automation = NewsAutomationService()
                    automation.print_stats()
                    input("\nPress Enter to continue...")
                
                elif choice == "8":
                    # Reset Cache
                    print("\n🗑️ Resetting cache files...")
                    confirm = input("Are you sure you want to reset all cache? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        automation = NewsAutomationService()
                        automation.reset_cache()
                        print("✅ Cache reset complete!")
                    else:
                        print("❌ Cache reset cancelled")
                    input("\nPress Enter to continue...")
                
                elif choice == "9":
                    # Cron Job Management
                    cron_management_menu()
                
                elif choice == "10":
                    # System Information
                    print("\n ℹ️ SYSTEM INFORMATION")
                    print("=" * 50)
                    automation = NewsAutomationService()
                    automation.get_page_info()
                    
                    print("\n🚀 Available Features:")
                    print("=" * 30)
                    print("• 🤖 AI Content Generation (Meta AI + Gemini Fallback)")
                    print("• 📰 Multi-source content (News + Reddit)")
                    print("• 🔄 Automatic posting with smart intervals")
                    print("• 📊 Built-in analytics and statistics")
                    print("• 💾 Smart caching system (300 articles per batch)")
                    print("• 🎯 Multiple content modes (Mixed/News/Reddit)")
                    print("• ⏰ Flexible scheduling options")
                    print("• 🛡️ Content safety filters")
                    print("• 📱 Cross-platform support (Facebook + Twitter)")
                    
                    print("\n📊 Content Sources:")
                    print("=" * 25)
                    print("• 📰 News: 60+ categories, multiple countries")
                    print("• 👻 Reddit: 60+ paranormal subreddits")
                    print("• 🎥 Video content support")
                    print("• 🖼️ Image posting capabilities")
                    
                    print("\n🔧 Technical Features:")
                    print("=" * 25)
                    print("• 🤖 Gemini AI fallback when Meta AI fails")
                    print("• 🚫 Smart content rejection detection")
                    print("• 🧹 Automatic content cleaning")
                    print("• ⏱️ Rate limiting and delays")
                    print("• 🔄 Robust error handling")
                    print("• 📝 Comprehensive logging")
                    
                    input("\nPress Enter to continue...")
                
                else:
                    print("❌ Invalid choice! Please enter a number between 0-10")
                    input("Press Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                input("Press Enter to continue...")
                
    except KeyboardInterrupt:
        print("\n\n👋 Thank you for using Beyond Belief!")
        sys.exit(0)

if __name__ == "__main__":
    # Check if running in Docker mode (legacy support)
    if len(sys.argv) > 1 and sys.argv[1] == 'docker':
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
        
        # Start automation with default interval
        interval = 10
        print(f"🚀 Starting automation with {interval} minute interval...")
        automation.start_automation(interval)
    else:
        # Interactive mode
        main()
