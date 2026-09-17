#!/usr/bin/env python3
"""
Simple local RSS/Atom reader
- Add feeds
- Fetch & list latest entries
- Mark as read / unread tracking
- No external dependencies beyond stdlib + feedparser (optional)
"""

import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from email.utils import parsedate_to_datetime

DATA_FILE = Path(__file__).parent / "feeds.json"

def load():
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"feeds": [], "seen": []}

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_feed(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rss-reader-cli/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
        root = ET.fromstring(content)

        # RSS 2.0
        items = []
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = item.findtext("pubDate") or ""
                guid = (item.findtext("guid") or link or title).strip()
                items.append({"title": title, "link": link, "date": pub, "id": guid})
            return items

        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns) or root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href") if link_el is not None else ""
            updated = entry.findtext("{http://www.w3.org/2005/Atom}updated") or ""
            eid = (entry.findtext("{http://www.w3.org/2005/Atom}id") or link or title).strip()
            items.append({"title": title, "link": link, "date": updated, "id": eid})
        return items
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return []

def add_feed(url, name=None):
    data = load()
    if any(f["url"] == url for f in data["feeds"]):
        print("Feed already exists.")
        return
    data["feeds"].append({
        "url": url,
        "name": name or url,
        "added": datetime.now().isoformat(timespec="seconds")
    })
    save(data)
    print(f"✓ Added feed: {name or url}")

def list_feeds():
    data = load()
    if not data["feeds"]:
        print("No feeds. Add one with: python rss.py add <url>")
        return
    for i, f in enumerate(data["feeds"], 1):
        print(f"{i}. {f['name']}\n   {f['url']}")

def update(limit=15):
    data = load()
    if not data["feeds"]:
        print("No feeds configured.")
        return

    all_items = []
    for feed in data["feeds"]:
        print(f"Fetching {feed['name']}...")
        items = fetch_feed(feed["url"])
        for it in items:
            it["feed"] = feed["name"]
            all_items.append(it)

    # sort by date if possible, otherwise keep order
    print(f"\nLatest entries (showing up to {limit}):\n")
    shown = 0
    for it in all_items:
        if shown >= limit:
            break
        is_new = it["id"] not in data["seen"]
        marker = "NEW" if is_new else "   "
        print(f"[{marker}] {it['feed']}")
        print(f"       {it['title']}")
        print(f"       {it['link']}")
        if is_new:
            data["seen"].append(it["id"])
        shown += 1
        print()

    # keep seen list from growing forever
    data["seen"] = data["seen"][-2000:]
    save(data)

def main():
    if len(sys.argv) < 2:
        print("""RSS Reader CLI
==============
  add <url> [name]   Add a feed
  list               List feeds
  update [n]         Fetch and show latest n entries (default 15)
""")
        return

    cmd = sys.argv[1].lower()
    if cmd == "add" and len(sys.argv) >= 3:
        name = sys.argv[3] if len(sys.argv) > 3 else None
        add_feed(sys.argv[2], name)
    elif cmd == "list":
        list_feeds()
    elif cmd == "update":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        update(n)
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
