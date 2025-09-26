# 📱 Termux Android Setup Guide

## 🚀 Quick Start - One Command Magic!

Just run this script and everything happens automatically:

```bash
./run_facebook_automation.sh
```

## 📋 What the Script Does Automatically:

1. ✅ **Sets all environment variables** (no need for .env file)
2. ✅ **Installs Python, pip, git** if not present
3. ✅ **Installs Poetry** for dependency management
4. ✅ **Installs all Python dependencies**
5. ✅ **Creates database folders**
6. ✅ **Starts automation with 10-minute default interval**

## 🎯 Usage Options:

### Interactive Menu (Default)
```bash
./run_facebook_automation.sh
```
Shows a menu with options:
1. Start automation (default 10 min)
2. Start with custom interval
3. Run single test post
4. Cache articles only
5. Show statistics
6. Reset cache
7. Show page info
8. Exit

### Direct Commands
```bash
# Start with default 10 minutes
./run_facebook_automation.sh start

# Start with custom interval (e.g., 5 minutes)
./run_facebook_automation.sh start 5

# Run single test post
./run_facebook_automation.sh test

# Cache articles only
./run_facebook_automation.sh cache

# Show statistics
./run_facebook_automation.sh stats

# Reset cache
./run_facebook_automation.sh reset

# Show page info
./run_facebook_automation.sh info
```

## 📱 Termux Installation:

1. **Install Termux** from F-Droid or Google Play Store
2. **Update packages**:
   ```bash
   pkg update && pkg upgrade
   ```
3. **Clone/copy your project** to Termux
4. **Run the magic script**:
   ```bash
   ./run_facebook_automation.sh
   ```

## 🔧 What's Included in the Script:

### Environment Variables (Pre-configured):
- ✅ NEWS_DATA_API
- ✅ META_PAGE_TOKEN  
- ✅ META_ACCOUNT_ID
- ✅ META_PAGE_ID
- ✅ FACEBOOK_EMAIL
- ✅ FACEBOOK_PASSWORD

### Features:
- ✅ **Country-based news queries** (India, Japan, Pakistan, Bangladesh)
- ✅ **AI content generation** with critical analysis
- ✅ **Meta AI image generation** when news has no images
- ✅ **Smart caching system** (processes unposted articles first)
- ✅ **Comprehensive logging** in db/ folder
- ✅ **Structured Facebook posts** with emojis and formatting

## 🛑 Stopping the Automation:

Press `Ctrl+C` to stop the automation gracefully.

## 📊 Monitoring:

The script shows:
- Real-time posting status
- Cache statistics
- Success/failure rates
- Database folder contents

## 🔄 Background Running:

To run in background on Termux:
```bash
nohup ./run_facebook_automation.sh start &
```

To check if it's running:
```bash
ps aux | grep python
```

## 🆘 Troubleshooting:

1. **Permission denied**: Run `chmod +x run_facebook_automation.sh`
2. **Python not found**: Script will auto-install it
3. **Dependencies missing**: Script will auto-install them
4. **Network issues**: Check your internet connection

## 📁 File Structure After Setup:

```
beyond_belief_py/
├── run_facebook_automation.sh    # Magic script
├── main.py                       # Main application
├── services/                     # All services
├── db/                          # Database (auto-created)
│   ├── posts/                   # Posted articles
│   ├── logs/                    # Session logs
│   ├── cache/                   # News cache
│   └── errors/                  # Error logs
└── TERMUX_SETUP.md             # This guide
```

## 🎉 That's It!

Just run `./run_facebook_automation.sh` and watch the magic happen! 🚀
