# Dockerfile for testing Facebook News Automation
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files (excluding sensitive data)
COPY pyproject.toml poetry.lock ./
COPY main.py ./
COPY services/ ./services/
COPY README.md ./
COPY FACEBOOK_TOKEN_GUIDE.md ./

# Install Python dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

# Create environment file template
RUN echo "# Environment Variables Template" > .env.template \
    && echo "NEWS_DATA_API=your_news_api_key_here" >> .env.template \
    && echo "META_PAGE_TOKEN=your_facebook_page_token_here" >> .env.template \
    && echo "META_ACCOUNT_ID=your_facebook_account_id_here" >> .env.template \
    && echo "META_PAGE_ID=your_facebook_page_id_here" >> .env.template \
    && echo "FACEBOOK_EMAIL=your_facebook_email_here" >> .env.template \
    && echo "FACEBOOK_PASSWORD=your_facebook_password_here" >> .env.template

# Create directories
RUN mkdir -p db/posts db/logs db/cache db/errors

# Expose port (if needed for web interface)
EXPOSE 8000

# Default command - Docker mode (non-interactive)
CMD ["python", "main.py", "docker"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Labels
LABEL maintainer="Facebook News Automation"
LABEL description="Docker container for testing Facebook News Automation system"
LABEL version="1.0"

# Instructions for running
# docker build -t facebook-news-automation .
# docker run -it --rm -v $(pwd)/.env:/app/.env facebook-news-automation python main.py test
