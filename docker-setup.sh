#!/bin/bash

# Facebook News Automation - Docker Setup Script
echo "🐳 Facebook News Automation - Docker Setup"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "📋 Installation guide: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "📋 Installation guide: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    
    if [ -f ".env.docker" ]; then
        cp .env.docker .env
        echo "✅ .env file created from .env.docker template"
    elif [ -f ".env.template" ]; then
        cp .env.template .env
        echo "✅ .env file created from .env.template"
    else
        echo "❌ No environment template found. Creating basic .env file..."
        cat > .env << 'EOF'
# Facebook News Automation Environment Variables
# Fill in your actual values

# News Data API
NEWS_DATA_API=your_news_api_key_here

# Facebook API
META_PAGE_TOKEN=your_facebook_page_token_here
META_ACCOUNT_ID=your_facebook_account_id_here
META_PAGE_ID=your_facebook_page_id_here
FACEBOOK_EMAIL=your_facebook_email_here
FACEBOOK_PASSWORD=your_facebook_password_here

# Twitter API (optional)
X_API_KEY=your_twitter_api_key_here
X_API_SECRET=your_twitter_api_secret_here
X_ACCESS_TOKEN=your_twitter_access_token_here
X_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# Settings
ENABLE_TWITTER=true
POSTING_INTERVAL=10
TZ=UTC
EOF
        echo "✅ Basic .env file created"
    fi
    
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file and add your API credentials:"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
else
    echo "✅ .env file already exists"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/db data/logs data/cache
echo "✅ Data directories created"

# Check if credentials are filled
echo "🔍 Checking environment variables..."
source .env

missing_vars=()

if [[ "$NEWS_DATA_API" == "your_news_api_key_here" || -z "$NEWS_DATA_API" ]]; then
    missing_vars+=("NEWS_DATA_API")
fi

if [[ "$META_PAGE_TOKEN" == "your_facebook_page_token_here" || -z "$META_PAGE_TOKEN" ]]; then
    missing_vars+=("META_PAGE_TOKEN")
fi

if [[ "$FACEBOOK_EMAIL" == "your_facebook_email_here" || -z "$FACEBOOK_EMAIL" ]]; then
    missing_vars+=("FACEBOOK_EMAIL")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please edit .env file and add the missing values:"
    echo "   nano .env"
    exit 1
fi

echo "✅ Required environment variables are set"

# Show menu
echo ""
echo "🎯 What would you like to do?"
echo "1. Build and start automation"
echo "2. Start automation (if already built)"
echo "3. View logs"
echo "4. Stop automation"
echo "5. Run test post"
echo "6. Start with monitoring (Portainer)"
echo "7. Clean up everything"
echo "8. Exit"
echo ""

read -p "Enter your choice (1-8): " choice

case $choice in
    1)
        echo "🔨 Building and starting automation..."
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ Automation started!"
        echo "📊 View logs: docker-compose logs -f facebook-news-automation"
        ;;
    2)
        echo "🚀 Starting automation..."
        docker-compose up -d
        echo "✅ Automation started!"
        echo "📊 View logs: docker-compose logs -f facebook-news-automation"
        ;;
    3)
        echo "📊 Showing logs..."
        docker-compose logs -f facebook-news-automation
        ;;
    4)
        echo "🛑 Stopping automation..."
        docker-compose down
        echo "✅ Automation stopped!"
        ;;
    5)
        echo "🧪 Running test post..."
        docker-compose exec facebook-news-automation python main.py test
        ;;
    6)
        echo "🔨 Starting with monitoring..."
        docker-compose --profile monitoring up -d
        echo "✅ Automation and monitoring started!"
        echo "🌐 Portainer: http://localhost:9000"
        echo "📊 View logs: docker-compose logs -f facebook-news-automation"
        ;;
    7)
        echo "🗑️ Cleaning up everything..."
        docker-compose down -v
        docker system prune -a -f
        echo "✅ Cleanup complete!"
        ;;
    8)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Useful commands:"
echo "   docker-compose logs -f                    # View logs"
echo "   docker-compose ps                         # Check status"
echo "   docker-compose restart                    # Restart"
echo "   docker-compose down                       # Stop"
echo "   docker-compose exec facebook-news-automation bash  # Access container"
echo ""
