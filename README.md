# RSS Reader CLI

A local RSS/Atom feed reader with unread tracking.

## Features
- Add multiple feeds
- Fetch latest entries
- Marks new items automatically
- Pure Python (stdlib only)

## Usage
```bash
python rss.py add https://example.com/feed.xml "Example Blog"
python rss.py list
python rss.py update          # show latest 15
python rss.py update 30
```
