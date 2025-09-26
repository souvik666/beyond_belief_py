# Facebook News Automation

<img width="1382" height="705" alt="Screenshot_20250926_142302" src="https://github.com/user-attachments/assets/bf491d10-e91b-472f-8640-cbf5c8e72766" />

## Features

- 🔄 **Automated News Fetching**: Fetches fresh news from multiple Indian states
- 🤖 **AI Content Generation**: Uses Meta AI to create unique, engaging social media posts
- 🎨 **Image Generation**: Creates custom images with news content
- 📱 **Facebook Integration**: Posts content with images to Facebook pages
- ⏰ **Scheduled Posting**: Runs every 10 minutes automatically
- 📊 **Statistics Tracking**: Monitors success rates and performance
- 🎯 **Smart Article Selection**: Chooses the best articles based on multiple criteria

## Setup

### 1. Install Dependencies

```bash
poetry install
```

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
# News API
NEWS_DATA_API=your_newsdata_api_key

# Facebook/Meta API
META_PAGE_TOKEN=your_facebook_page_access_token
META_PAGE_ID=your_facebook_page_id
META_ACCOUNT_ID=your_facebook_account_id
```

### 3. Get API Keys

#### NewsData.io API
1. Visit [NewsData.io](https://newsdata.io/)
2. Sign up for a free account
3. Get your API key from the dashboard

#### Facebook Page Access Token
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create an app and get a Page Access Token
3. Make sure the token has `pages_manage_posts` and `pages_read_engagement` permissions

## Usage

### Test the System
```bash
python main.py test
```

### Start Continuous Automation
```bash
python main.py start
```

### Set Up System Cron Job
```bash
python main.py setup-cron
```

### Remove Cron Job
```bash
python main.py remove-cron
```

### Get Page Information
```bash
python main.py info
```

## How It Works

1. **News Fetching**: The system fetches news from multiple Indian states using the NewsData.io API
2. **Content Generation**: Meta AI creates unique, engaging social media posts from news headlines
3. **Image Creation**: PIL generates custom images with the news content
4. **Smart Selection**: Articles are scored based on recency, quality, and engagement potential
5. **Facebook Posting**: Content is posted to Facebook with generated images
6. **Duplicate Prevention**: Tracks posted articles to avoid duplicates

## Configuration

### Supported States
- West Bengal
- Maharashtra
- Karnataka
- Tamil Nadu
- Gujarat
- Rajasthan
- Uttar Pradesh
- Delhi

### Content Templates
The system uses various templates to create diverse content:
- Compelling social media posts
- Thought-provoking captions
- Engaging Facebook updates
- Conversational news summaries

### Hashtag Categories
- General: #BreakingNews, #India, #News
- Politics: #Politics, #Government, #Policy
- Business: #Business, #Economy, #Finance
- Technology: #Technology, #Tech, #Innovation
- Sports: #Sports, #Cricket, #Football
- Entertainment: #Entertainment, #Bollywood

## File Structure

```
beyond_belief_py/
├── main.py                          # Main entry point
├── services/
│   ├── news_service.py             # News fetching from NewsData.io
│   ├── content_generator.py        # Meta AI content generation
│   ├── facebook_service.py         # Facebook posting and image generation
│   └── automation_service.py       # Main automation logic and scheduling
├── pyproject.toml                  # Dependencies
├── .env                           # Environment variables
└── README.md                      # This file
```

## Dependencies

- `meta-ai-api`: For AI content generation
- `requests`: For API calls
- `pillow`: For image generation
- `python-crontab`: For cron job management
- `schedule`: For Python-based scheduling
- `python-dotenv`: For environment variable management

## Error Handling

The system includes comprehensive error handling:
- API failures are logged and retried
- Fallback content generation when AI fails
- Graceful handling of Facebook API limits
- Automatic cleanup of temporary files

## Statistics

The system tracks:
- Total posts attempted
- Successful posts
- Failed posts
- Success rate
- Runtime statistics
- Cache status

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all environment variables are set correctly
2. **Facebook Permissions**: Make sure your page token has the required permissions
3. **Rate Limits**: The system includes delays to respect API rate limits
4. **Image Generation**: Requires system fonts; fallback to default if unavailable

### Logs

The system provides detailed logging with emojis for easy monitoring:
- 🔄 Fetching operations
- 🤖 AI generation
- 📤 Facebook posting
- ✅ Success messages
- ❌ Error messages

## License

This project is for educational and personal use. Make sure to comply with Facebook's and NewsData.io's terms of service.
