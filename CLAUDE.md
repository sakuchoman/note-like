# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web scraping tool for collecting paid articles from note.com, sorted by "likes" (スキ数). The tool is designed for personal research use with rate limiting and respectful scraping practices.

## Key Specifications

### API Endpoint
- Base URL: `https://note.com/api/v3/searches`
- Query parameters: `context=note&q={keyword}&size={size}&start={start}`
- Response structure: `data.notes.contents` (array of articles)

### Core Features
1. **Search & Filter**: Search articles by keyword, filter paid articles only (price > 0)
2. **Exclusion**: Exclude articles containing specific words in title/description
3. **Sorting**: Sort by like_count (DESC), then publish_at (DESC)
4. **Output**: CSV format with columns: likes, price, title, url, author_urlname, publish_at, description_short

## Development Commands

### Streamlit Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py

# Access at http://localhost:8501
```

### Deployment to Streamlit Cloud
1. Push code to GitHub
2. Connect repository at https://streamlit.io
3. Deploy with one click
4. Share the generated URL

## Project Structure
```
note-like/
├── app.py                        # Main Streamlit application
├── requirements.txt              # Python dependencies
├── .gitignore                   # Git ignore file
├── README.md                    # Project documentation
├── document/                    # Project specifications
│   ├── note_paid_articles_collection_spec.md
│   └── streamlit_implementation_plan.md
└── .streamlit/                  # Streamlit configuration (optional)
    └── config.toml
```

## Implementation Guidelines

### Rate Limiting
- **CRITICAL**: Wait 800-1200ms between requests (with jitter)
- Maximum 3 retries with exponential backoff for 429/403/5xx errors
- Default limit: 200 articles (20 per page × 10 pages)

### Error Handling
- 400: Stop execution, prompt user to check parameters
- 403/429: Exponential backoff retry, save partial results if failed
- 404: Skip and continue
- 5xx: Retry with backoff, save partial results if failed

### Data Processing
1. Filter articles where `price > 0`
2. Exclude articles containing any exclude_words (case-insensitive)
3. Sort by `like_count` DESC, then `publish_at` DESC
4. Truncate descriptions to 100 characters, remove HTML/newlines

### Compliance Notes
- This tool uses unofficial APIs - structure may change without notice
- Respect rate limits and robots.txt restrictions
- For personal research use only - do not redistribute collected data
- Implement graceful degradation for API changes

## Configuration (config/app.yaml)
```yaml
query: "エッセイ"
exclude_words: ["稼", "副業", "アフィ", "収益", "ビジネス"]
size: 20
pages: 10
min_likes: 0
price_max: null
date_from: null
date_to: null
sleep_ms_min: 800
sleep_ms_max: 1200
retries: 3
backoff_base_ms: 800
output_dir: "outputs"
cache_enabled: true
cache_dir: "cache"
log_dir: "logs"
```

## Testing Checklist
- [ ] CSV output contains only paid articles (price > 0)
- [ ] Excluded words filter working correctly
- [ ] Articles sorted by likes (descending)
- [ ] Rate limiting working (800-1200ms delays)
- [ ] Error handling and retries working
- [ ] Cache functionality (if enabled)