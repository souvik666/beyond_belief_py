# 🚀 Deployment Guide - Facebook News Automation

## 📋 Pre-Deployment Checklist

### ✅ **What to Include in GitHub Repository:**
- ✅ All Python source code (`main.py`, `services/`)
- ✅ Configuration files (`pyproject.toml`, `poetry.lock`)
- ✅ Documentation (`README.md`, `FACEBOOK_TOKEN_GUIDE.md`)
- ✅ Docker setup (`Dockerfile`)
- ✅ Environment template (`.env.template`)
- ✅ Git configuration (`.gitignore`)

### ❌ **What NOT to Include in GitHub Repository:**
- ❌ `.env` file (contains sensitive API keys)
- ❌ `run_facebook_automation.sh` (contains hardcoded credentials)
- ❌ `update_token.sh` (may contain sensitive data)
- ❌ `db/` folder (contains cached data and logs)
- ❌ Any backup files (`*.backup`)

## 🔒 **Security Audit Results:**

### **Sensitive Information Found:**
1. **`.env` file** - Contains all API keys and credentials
2. **`run_facebook_automation.sh`** - Has hardcoded environment variables
3. **`update_token.sh`** - May contain token information

### **Security Measures Applied:**
- ✅ Updated `.gitignore` to exclude all sensitive files
- ✅ Created `.env.template` for safe sharing
- ✅ Created GitHub-based setup script without credentials
- ✅ Added validation to prevent accidental commits

## 📱 **Termux Android Deployment:**

### **Step 1: Prepare the GitHub-based Script**
1. Copy `termux_github_setup.sh` to your phone
2. Edit the script and update these values:
   ```bash
   GITHUB_REPO="YOUR_USERNAME/YOUR_REPO_NAME"
   NEWS_DATA_API="your_actual_api_key"
   META_PAGE_TOKEN="your_actual_token"
   # ... etc
   ```

### **Step 2: Deploy on Termux**
```bash
# Install Termux from F-Droid or Play Store
# Update packages
pkg update && pkg upgrade

# Make script executable
chmod +x termux_github_setup.sh

# Run the setup (downloads from GitHub)
./termux_github_setup.sh
```

### **Step 3: Verify Installation**
```bash
# Test the system
./termux_github_setup.sh test

# Start automation
./termux_github_setup.sh start
```

## 🐳 **Docker Testing:**

### **Build and Test:**
```bash
# Build Docker image
docker build -t facebook-news-automation .

# Create environment file
cp .env.template .env
# Edit .env with your actual values

# Test the system
docker run -it --rm -v $(pwd)/.env:/app/.env facebook-news-automation python main.py test

# Run automation (for testing)
docker run -it --rm -v $(pwd)/.env:/app/.env facebook-news-automation python main.py start --interval 5
```

## 📂 **Repository Structure for GitHub:**

```
your-repo/
├── .gitignore                    # Excludes sensitive files
├── .env.template                 # Safe environment template
├── Dockerfile                    # For testing
├── README.md                     # Project documentation
├── FACEBOOK_TOKEN_GUIDE.md       # Token setup guide
├── DEPLOYMENT_GUIDE.md           # This file
├── main.py                       # Main application
├── pyproject.toml               # Dependencies
├── poetry.lock                  # Locked dependencies
└── services/                    # All service modules
    ├── automation_service.py
    ├── content_generator.py
    ├── facebook_service.py
    ├── logging_service.py
    └── news_service.py
```

## 🔧 **GitHub Repository Setup:**

### **1. Initialize Repository:**
```bash
git init
git add .
git commit -m "Initial commit - Facebook News Automation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### **2. Verify No Sensitive Data:**
```bash
# Check what's being committed
git status
git diff --cached

# Ensure these files are NOT in the repo:
# - .env
# - run_facebook_automation.sh
# - update_token.sh
# - db/ folder
```

## 📱 **Termux User Instructions:**

### **For End Users (Copy this to your phone):**

1. **Download the setup script** from your repository
2. **Edit the script** with your credentials:
   ```bash
   nano termux_github_setup.sh
   # Update GITHUB_REPO and all API keys
   ```
3. **Run the setup:**
   ```bash
   chmod +x termux_github_setup.sh
   ./termux_github_setup.sh
   ```

## 🔄 **Update Process:**

### **For Code Updates:**
```bash
# On your development machine
git add .
git commit -m "Update: description of changes"
git push origin main

# On Termux
./termux_github_setup.sh update
```

## ⚠️ **Important Security Notes:**

### **Before Publishing to GitHub:**
1. ✅ **Remove all sensitive files** from the repository
2. ✅ **Double-check .gitignore** is working correctly
3. ✅ **Test with a fresh clone** to ensure no secrets are included
4. ✅ **Use environment templates** instead of real credentials

### **For Users:**
1. 🔒 **Never share your configured script** with credentials
2. 🔒 **Keep your API keys private**
3. 🔒 **Use long-lasting Facebook tokens** (see FACEBOOK_TOKEN_GUIDE.md)
4. 🔒 **Regularly rotate your credentials**

## 🧪 **Testing Checklist:**

### **Before Deployment:**
- [ ] Docker build succeeds
- [ ] No sensitive data in repository
- [ ] .gitignore excludes all sensitive files
- [ ] Environment template is complete
- [ ] Documentation is up to date

### **After Deployment:**
- [ ] Fresh clone works without errors
- [ ] Termux script downloads and runs correctly
- [ ] All dependencies install properly
- [ ] Test post works
- [ ] Automation runs successfully

## 🎯 **Production Deployment:**

### **Recommended Workflow:**
1. **Development** → Test locally with Docker
2. **Staging** → Test on Termux with GitHub script
3. **Production** → Deploy to final Termux device

### **Monitoring:**
- Check logs in `db/logs/` folder
- Monitor Facebook page for posts
- Watch for token expiration errors
- Verify news cache is updating

## 📞 **Support:**

### **Common Issues:**
1. **Token expired** → Use FACEBOOK_TOKEN_GUIDE.md
2. **Dependencies fail** → Check Python/Poetry installation
3. **GitHub clone fails** → Verify repository URL and access
4. **Posts not appearing** → Check Facebook permissions

**Your system is now ready for secure deployment! 🚀**
