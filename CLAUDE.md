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
1. **Search Operators**: Support for AND, OR, NOT, and complex search queries
2. **Search Modes**: 5 search modes - Normal, AND, OR, NOT, Custom
3. **Search & Filter**: Search articles by keyword, filter paid articles only (price > 0)
4. **Dynamic UI**: Input forms change based on selected search mode
5. **Query Preview**: Real-time display of actual API query
6. **Sorting**: Sort by like_count (DESC), then publish_at (DESC)
7. **Output**: CSV format with URL column and clickable links in UI

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
│   ├── note_paid_articles_collection_spec_v2.md
│   ├── streamlit_implementation_plan.md
│   └── streamlit_implementation_plan_v2.md
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
2. Process search operators at API level (AND, OR, NOT)
3. Sort by `like_count` DESC, then `publish_at` DESC
4. Build article URLs and add clickable links
5. Truncate descriptions to 100 characters, remove HTML/newlines

### Compliance Notes
- This tool uses unofficial APIs - structure may change without notice
- Respect rate limits and robots.txt restrictions
- For personal research use only - do not redistribute collected data
- Implement graceful degradation for API changes

## Search Operators

### Supported Operators
- `AND` (case-insensitive): All conditions must be satisfied
- `OR` (case-insensitive): Any condition must be satisfied
- `NOT` (case-insensitive): Exclude specific conditions
- `()` (parentheses): Control operator precedence

### Search Mode Examples
```python
# Normal search
query = "エッセイ"

# AND search
query = "エッセイ AND 旅行"

# OR search
query = "エッセイ OR 日記 OR 随筆"

# NOT search
query = "エッセイ NOT ビジネス NOT 稼ぐ"

# Custom search
query = "(エッセイ OR 日記) AND 旅行 NOT ビジネス"
```

## Configuration Constants
```python
COMMON_EXCLUDE_WORDS = "稼ぐ,副業,収益,ビジネス,マネタイズ,集客"
RATE_LIMIT_MIN = 800  # ms
RATE_LIMIT_MAX = 1200  # ms
MAX_PAGES = 20
ITEMS_PER_PAGE = 20
MAX_RETRIES = 3
```

## Testing Checklist
- [ ] All search modes (Normal/AND/OR/NOT/Custom) working correctly
- [ ] Search query preview displays correct API query
- [ ] CSV output contains only paid articles (price > 0)
- [ ] CSV output includes URL column
- [ ] Clickable links work in UI table
- [ ] Articles sorted by likes (descending)
- [ ] Rate limiting working (800-1200ms delays)
- [ ] Error handling and retries working
- [ ] Search operator validation and error messages
- [ ] Dynamic UI changes based on search mode selection