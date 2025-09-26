#!/bin/bash

# Facebook News Automation - Termux GitHub Setup Script
# This script downloads the code from GitHub and sets up the environment

echo "🚀 Facebook News Automation - GitHub Setup"
echo "📱 Running on Termux Android"
echo "🔗 Downloading from GitHub..."
echo "=" * 50

# Configuration - UPDATE THESE WITH YOUR VALUES
GITHUB_REPO="souvik666/beyond_belief_py"  
PROJECT_DIR="facebook-news-automation"

# Environment variables - UPDATE THESE WITH YOUR ACTUAL VALUES
export NEWS_DATA_API="YOUR_NEWS_DATA_API_KEY_HERE"
export META_PAGE_TOKEN="YOUR_FACEBOOK_PAGE_TOKEN_HERE"
export META_ACCOUNT_ID="YOUR_FACEBOOK_ACCOUNT_ID_HERE"
export META_PAGE_ID="YOUR_FACEBOOK_PAGE_ID_HERE"
export FACEBOOK_EMAIL="YOUR_FACEBOOK_EMAIL_HERE"
export FACEBOOK_PASSWORD="YOUR_FACEBOOK_PASSWORD_HERE"
export FACEBOOK_PASSWORD="YOUR_FACEBOOK_PASSWORD_HERE"
export REDDIT_CLIENT_ID="YOUR_REDDIT_CLIENT_ID"
export REDDIT_CLIENT_SECRET="YOUR_REDDIT_CLIENT_SECRET"
# Twitter Control (set to false to disable Twitter posting)
export ENABLE_TWITTER="false"


echo "✅ Environment variables configured"

# Function to check system requirements
check_system_requirements() {
    echo "🔍 Checking system requirements..."
    
    # Check if running on Android/Termux
    if [[ ! "$PREFIX" =~ termux ]]; then
        echo "⚠️ Warning: This script is designed for Termux on Android"
        echo "🔧 You may need to modify package installation commands for your system"
    else
        echo "✅ Running on Termux Android"
    fi
    
    # Check available storage space
    echo "💾 Checking storage space..."
    local available_space=$(df -h "$HOME" | awk 'NR==2 {print $4}' | sed 's/[^0-9.]//g')
    local available_mb=$(echo "$available_space * 1024" | bc 2>/dev/null || echo "1000")
    
    if (( $(echo "$available_mb < 500" | bc -l 2>/dev/null || echo "0") )); then
        echo "⚠️ Warning: Low storage space detected (${available_space}MB available)"
        echo "🔧 Recommended: At least 500MB free space for installation"
        read -p "Continue anyway? (y/N): " continue_install
        if [[ ! "$continue_install" =~ ^[Yy]$ ]]; then
            echo "❌ Installation cancelled due to low storage"
            exit 1
        fi
    else
        echo "✅ Sufficient storage space available"
    fi
    
    # Check memory
    echo "🧠 Checking memory..."
    if command -v free &> /dev/null; then
        local total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2}')
        if [ "$total_mem" -lt 1024 ]; then
            echo "⚠️ Warning: Low memory detected (${total_mem}MB total)"
            echo "🔧 Some operations may be slower on low-memory devices"
        else
            echo "✅ Sufficient memory available (${total_mem}MB)"
        fi
    else
        echo "ℹ️ Memory check not available on this system"
    fi
    
    # Check architecture
    echo "🏗️ System architecture: $(uname -m)"
    echo "🐧 System: $(uname -s)"
    
    echo "✅ System requirements check complete"
}

# Function to setup error logging
setup_error_logging() {
    local log_dir="$HOME/.termux-setup-logs"
    local log_file="$log_dir/setup-$(date +%Y%m%d-%H%M%S).log"
    
    mkdir -p "$log_dir"
    
    # Redirect all output to log file as well
    exec > >(tee -a "$log_file")
    exec 2> >(tee -a "$log_file" >&2)
    
    echo "📝 Logging setup to: $log_file"
}

# Function to update Termux packages
update_termux() {
    echo "🔄 Updating Termux packages..."
    
    # Update package lists
    pkg update -y
    
    # Upgrade existing packages
    pkg upgrade -y
    
    echo "✅ Termux packages updated"
}

# Function to install essential dependencies
install_essential_deps() {
    echo "📦 Installing essential dependencies..."
    
    # Essential packages for the project
    local essential_packages=(
        "python"
        "python-pip" 
        "git"
        "curl"
        "wget"
        "openssh"
        "openssl"
        "libffi"
        "libjpeg-turbo"
        "zlib"
        "freetype"
        "libpng"
        "pkg-config"
        "build-essential"
        "clang"
        "make"
        "cmake"
        "rust"
    )
    
    echo "📋 Installing packages: ${essential_packages[*]}"
    
    for package in "${essential_packages[@]}"; do
        echo "📦 Installing $package..."
        if pkg install "$package" -y; then
            echo "✅ $package installed successfully"
        else
            echo "⚠️ Warning: Failed to install $package, continuing..."
        fi
    done
    
    echo "✅ Essential dependencies installation complete"
}

# Function to fix Python version issues
fix_python_version() {
    echo "🔧 Fixing Python version compatibility issues..."
    
    # Check current Python version
    local python_version=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    echo "🐍 Current Python version: $python_version"
    
    # Handle Python 3.12+ compatibility issues
    if [[ "$python_version" > "3.11" ]]; then
        echo "⚠️ Python 3.12+ detected - applying compatibility fixes..."
        
        # Set environment variables for compatibility
        export SETUPTOOLS_USE_DISTUTILS=stdlib
        export PIP_BREAK_SYSTEM_PACKAGES=1
        
        # Install compatible versions
        echo "📦 Installing Python 3.12+ compatible packages..."
        python -m pip install --upgrade pip setuptools wheel --break-system-packages
        
        # Install specific compatible versions
        python -m pip install "poetry>=1.6.0" --break-system-packages
        python -m pip install "cryptography>=41.0.0" --break-system-packages
        
    else
        echo "✅ Python version compatible, proceeding normally..."
    fi
}

# Function to setup Python environment
setup_python_environment() {
    echo "🐍 Setting up Python environment..."
    
    # Fix Python version issues first
    fix_python_version
    
    # Upgrade pip with compatibility flags
    echo "📦 Upgrading pip..."
    if python -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
        python -m pip install --upgrade pip --break-system-packages
    else
        python -m pip install --upgrade pip
    fi
    
    # Install essential Python packages with version compatibility
    echo "📦 Installing essential Python packages..."
    local python_packages=(
        "wheel"
        "setuptools>=68.0.0"
        "poetry>=1.6.0"
        "requests"
        "pillow"
        "cryptography>=41.0.0"
        "cffi"
        "pycparser"
    )
    
    for package in "${python_packages[@]}"; do
        echo "📦 Installing Python package: $package"
        
        # Use appropriate pip flags based on Python version
        if python -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
            if python -m pip install "$package" --break-system-packages; then
                echo "✅ $package installed successfully"
            else
                echo "⚠️ Warning: Failed to install $package, trying alternative..."
                # Try without version constraints
                local base_package=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
                python -m pip install "$base_package" --break-system-packages || echo "⚠️ $base_package installation failed"
            fi
        else
            if python -m pip install "$package"; then
                echo "✅ $package installed successfully"
            else
                echo "⚠️ Warning: Failed to install $package, continuing..."
            fi
        fi
    done
    
    echo "✅ Python environment setup complete"
}

# Function to check if required packages are installed
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    local missing_deps=()
    
    # Check essential commands
    local required_commands=("python" "pip" "git" "curl")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "❌ $cmd not found"
            missing_deps+=("$cmd")
        else
            echo "✅ $cmd found"
        fi
    done
    
    # If any dependencies are missing, install them
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "🔧 Missing dependencies detected: ${missing_deps[*]}"
        echo "📦 Installing missing dependencies..."
        
        update_termux
        install_essential_deps
        setup_python_environment
        
        # Re-check after installation
        echo "🔍 Re-checking dependencies..."
        for cmd in "${required_commands[@]}"; do
            if ! command -v "$cmd" &> /dev/null; then
                echo "❌ Critical: $cmd still not found after installation"
                echo "🆘 Please manually install $cmd and try again"
                exit 1
            else
                echo "✅ $cmd now available"
            fi
        done
    else
        echo "✅ All essential dependencies found"
    fi
    
    # Check Python version
    python_version=$(python --version 2>&1)
    echo "🐍 Python version: $python_version"
    
    # Check pip version
    pip_version=$(pip --version 2>&1)
    echo "📦 Pip version: $pip_version"
    
    # Check git version
    git_version=$(git --version 2>&1)
    echo "🔗 Git version: $git_version"
}

# Function to check internet connectivity
check_internet() {
    echo "🌐 Checking internet connectivity..."
    
    local test_urls=("google.com" "github.com" "8.8.8.8")
    
    for url in "${test_urls[@]}"; do
        if ping -c 1 "$url" &> /dev/null; then
            echo "✅ Internet connection verified ($url)"
            return 0
        fi
    done
    
    echo "❌ No internet connection detected"
    echo "🔧 Please check your internet connection and try again"
    exit 1
}

# Function to retry command with exponential backoff
retry_command() {
    local max_attempts=3
    local delay=1
    local attempt=1
    local command="$@"
    
    while [ $attempt -le $max_attempts ]; do
        echo "🔄 Attempt $attempt/$max_attempts: $command"
        
        if eval "$command"; then
            echo "✅ Command succeeded on attempt $attempt"
            return 0
        else
            echo "❌ Command failed on attempt $attempt"
            
            if [ $attempt -lt $max_attempts ]; then
                echo "⏳ Waiting ${delay}s before retry..."
                sleep $delay
                delay=$((delay * 2))  # Exponential backoff
            fi
            
            attempt=$((attempt + 1))
        fi
    done
    
    echo "❌ Command failed after $max_attempts attempts"
    return 1
}

# Function to download project from GitHub
download_project() {
    echo "📥 Downloading project from GitHub..."
    
    # Check internet connectivity first
    check_internet
    
    # Remove existing directory if it exists
    if [ -d "$PROJECT_DIR" ]; then
        echo "🗑️ Removing existing project directory..."
        rm -rf "$PROJECT_DIR"
    fi
    
    # Clone the repository with retry mechanism
    echo "🔗 Cloning repository: $GITHUB_REPO"
    
    if retry_command "git clone https://github.com/$GITHUB_REPO.git $PROJECT_DIR"; then
        echo "✅ Successfully downloaded project"
        cd "$PROJECT_DIR" || {
            echo "❌ Failed to enter project directory"
            exit 1
        }
    else
        echo "❌ Failed to download project from GitHub after multiple attempts"
        echo "🔧 Please check:"
        echo "   - Repository URL is correct: $GITHUB_REPO"
        echo "   - Repository is public or you have access"
        echo "   - Internet connection is stable"
        echo "   - GitHub is accessible"
        exit 1
    fi
}

# Function to install Python dependencies
install_python_deps() {
    echo "📦 Installing Python dependencies..."
    
    # Check if poetry is installed and install with compatibility
    if ! command -v poetry &> /dev/null; then
        echo "📦 Installing Poetry..."
        if python -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
            python -m pip install poetry --break-system-packages
        else
            python -m pip install poetry
        fi
    fi
    
    # Configure Poetry for Python 3.12+ compatibility
    echo "🔧 Configuring Poetry..."
    poetry config virtualenvs.create false
    poetry config installer.max-workers 1
    
    # Handle Python 3.12+ specific issues
    if python -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
        echo "🔧 Applying Python 3.12+ compatibility fixes for Poetry..."
        export PIP_BREAK_SYSTEM_PACKAGES=1
        export SETUPTOOLS_USE_DISTUTILS=stdlib
        
        # Install dependencies with compatibility flags
        echo "📦 Installing project dependencies (Python 3.12+ mode)..."
        poetry install --no-dev || {
            echo "⚠️ Poetry install failed, trying alternative method..."
            
            # Fallback: Install dependencies manually
            echo "📦 Installing dependencies manually..."
            python -m pip install requests pillow python-dotenv schedule meta-ai-api --break-system-packages
            
            # Create a minimal pyproject.toml if needed
            if [ ! -f "pyproject.toml" ]; then
                echo "📝 Creating minimal pyproject.toml..."
                cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "facebook-news-automation"
version = "1.0.0"
description = "Facebook News Automation"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.31.0"
pillow = "^10.0.0"
python-dotenv = "^1.0.0"
schedule = "^1.2.0"
meta-ai-api = "^0.1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF
            fi
        }
    else
        # Standard Poetry installation for older Python versions
        echo "📦 Installing project dependencies..."
        poetry install
    fi
    
    echo "✅ Dependencies installed"
}

# Function to create environment file
create_env_file() {
    echo "📝 Creating environment file..."
    
    cat > .env << EOF
NEWS_DATA_API=$NEWS_DATA_API
META_PAGE_TOKEN=$META_PAGE_TOKEN
META_ACCOUNT_ID=$META_ACCOUNT_ID
META_PAGE_ID=$META_PAGE_ID
FACEBOOK_EMAIL=$FACEBOOK_EMAIL
FACEBOOK_PASSWORD=$FACEBOOK_PASSWORD
ENABLE_TWITTER=$ENABLE_TWITTER
REDDIT_CLIENT_ID=$REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET=$REDDIT_CLIENT_SECRET
EOF
    
    echo "✅ Environment file created"
}

# Function to setup directories
setup_directories() {
    echo "📁 Setting up directories..."
    
    # Create db directory structure if it doesn't exist
    mkdir -p db/posts
    mkdir -p db/logs
    mkdir -p db/cache
    mkdir -p db/errors
    
    echo "✅ Directories created"
}

# Function to show menu
show_menu() {
    echo ""
    echo "🎯 Facebook News Automation Menu"
    echo "================================"
    echo "1. Start automation (default 10 min)"
    echo "2. Start with custom interval"
    echo "3. Run single test post"
    echo "4. Cache articles only"
    echo "5. Show statistics"
    echo "6. Reset cache"
    echo "7. Show page info"
    echo "8. Update from GitHub"
    echo "9. Exit"
    echo ""
}

# Function to run automation
run_automation() {
    local interval=${1:-10}
    echo "🚀 Starting automation with ${interval} minute interval..."
    echo "📱 Running on Termux Android"
    echo "🛑 Press Ctrl+C to stop"
    echo ""
    
    # Run the automation in non-interactive mode
    poetry run python main.py docker --interval $interval
}

# Function to run test post
run_test() {
    echo "🧪 Running single test post..."
    poetry run python main.py test
}

# Function to cache articles
cache_articles() {
    echo "📦 Caching articles..."
    poetry run python main.py cache
}

# Function to show stats
show_stats() {
    echo "📊 Showing statistics..."
    poetry run python main.py stats
}

# Function to reset cache
reset_cache() {
    echo "🗑️ Resetting cache..."
    poetry run python main.py reset-cache
}

# Function to show page info
show_page_info() {
    echo "📄 Showing page information..."
    poetry run python main.py info
}

# Function to update from GitHub
update_from_github() {
    echo "🔄 Updating from GitHub..."
    git pull origin main
    poetry install
    echo "✅ Update complete"
}

# Function to validate configuration
validate_config() {
    echo "🔍 Validating configuration..."
    
    # Check if environment variables are set
    if [[ "$NEWS_DATA_API" == "YOUR_NEWS_DATA_API_KEY_HERE" ]]; then
        echo "❌ Please update NEWS_DATA_API in the script"
        return 1
    fi
    
    if [[ "$META_PAGE_TOKEN" == "YOUR_FACEBOOK_PAGE_TOKEN_HERE" ]]; then
        echo "❌ Please update META_PAGE_TOKEN in the script"
        return 1
    fi
    
    if [[ "$FACEBOOK_EMAIL" == "YOUR_FACEBOOK_EMAIL_HERE" ]]; then
        echo "❌ Please update FACEBOOK_EMAIL in the script"
        return 1
    fi
    
    echo "✅ Configuration looks good"
    return 0
}

# Main execution
main() {
    # Setup error logging first
    setup_error_logging
    
    # Check system requirements
    check_system_requirements
    
    # Validate configuration first
    if ! validate_config; then
        echo ""
        echo "🔧 Please edit this script and update the configuration section:"
        echo "   - NEWS_DATA_API"
        echo "   - META_PAGE_TOKEN"
        echo "   - META_ACCOUNT_ID"
        echo "   - META_PAGE_ID"
        echo "   - FACEBOOK_EMAIL"
        echo "   - FACEBOOK_PASSWORD"
        echo "   - GITHUB_REPO"
        echo ""
        exit 1
    fi
    
    # Setup with robust error handling
    echo "🔧 Starting robust installation process..."
    
    if ! check_dependencies; then
        echo "❌ Dependency check failed"
        exit 1
    fi
    
    if ! download_project; then
        echo "❌ Project download failed"
        exit 1
    fi
    
    if ! install_python_deps; then
        echo "❌ Python dependencies installation failed"
        exit 1
    fi
    
    if ! create_env_file; then
        echo "❌ Environment file creation failed"
        exit 1
    fi
    
    if ! setup_directories; then
        echo "❌ Directory setup failed"
        exit 1
    fi
    
    echo "🎉 Installation completed successfully!"
    echo "📱 Your Facebook News Automation is ready to use!"
    
    # If arguments provided, run directly
    if [ $# -gt 0 ]; then
        case $1 in
            "start")
                interval=${2:-10}
                run_automation $interval
                ;;
            "test")
                run_test
                ;;
            "cache")
                cache_articles
                ;;
            "stats")
                show_stats
                ;;
            "reset")
                reset_cache
                ;;
            "info")
                show_page_info
                ;;
            "update")
                update_from_github
                ;;
            *)
                echo "❌ Unknown command: $1"
                echo "Usage: $0 [start|test|cache|stats|reset|info|update] [interval]"
                exit 1
                ;;
        esac
        return
    fi
    
    # Interactive menu
    while true; do
        show_menu
        read -p "Enter your choice (1-9): " choice
        
        case $choice in
            1)
                run_automation 10
                ;;
            2)
                read -p "Enter interval in minutes (1-1440): " custom_interval
                if [[ $custom_interval =~ ^[0-9]+$ ]] && [ $custom_interval -ge 1 ] && [ $custom_interval -le 1440 ]; then
                    run_automation $custom_interval
                else
                    echo "❌ Invalid interval. Please enter a number between 1 and 1440."
                fi
                ;;
            3)
                run_test
                ;;
            4)
                cache_articles
                ;;
            5)
                show_stats
                ;;
            6)
                reset_cache
                ;;
            7)
                show_page_info
                ;;
            8)
                update_from_github
                ;;
            9)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid choice. Please enter 1-9."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n🛑 Setup stopped by user"; exit 0' INT

# Show instructions if no arguments
if [ $# -eq 0 ]; then
    echo ""
    echo "📋 BEFORE RUNNING:"
    echo "1. Edit this script and update the configuration section"
    echo "2. Set your GitHub repository URL"
    echo "3. Add your API keys and credentials"
    echo ""
    echo "🚀 USAGE:"
    echo "   $0                    # Interactive menu"
    echo "   $0 start             # Start with 10 min interval"
    echo "   $0 start 5           # Start with 5 min interval"
    echo "   $0 test              # Run single test"
    echo ""
fi

# Run main function
main "$@"
