#!/usr/bin/env python3
"""
Process download queue and download Instagram reels
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

def load_queue():
    """Load download queue"""
    try:
        with open("download_queue.json", "r") as f:
            return json.load(f)
    except:
        return {"queue": [], "processing": False}

def save_queue(queue):
    """Save queue back to file"""
    with open("download_queue.json", "w") as f:
        json.dump(queue, f, indent=2)

def process_queue():
    """Process all items in queue"""
    queue = load_queue()

    if not queue.get("queue"):
        print("✅ Queue is empty")
        return True

    print(f"📋 Processing {len(queue['queue'])} items in queue...")

    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)

    successful = 0
    failed = 0

    for i, item in enumerate(queue["queue"]):
        url = item.get("url", "")
        print(f"\n[{i+1}/{len(queue['queue'])}] Downloading: {url}")

        try:
            # Check rate limit
            if not check_limit():
                print("❌ Rate limit reached!")
                item["status"] = "rate_limited"
                failed += 1
                continue

            # Download video
            cmd = [
                "yt-dlp",
                "-o", str(downloads_dir / "%(title)s.%(ext)s"),
                url
            ]

            # Add cookies if available
            if os.path.exists("instagram_cookies.txt"):
                cmd.insert(2, "--cookies")
                cmd.insert(3, "instagram_cookies.txt")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✅ Downloaded successfully")
                item["status"] = "completed"
                successful += 1
            else:
                print(f"❌ Download failed: {result.stderr[:100]}")
                item["status"] = "failed"
                failed += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            item["status"] = "error"
            failed += 1

    # Clear processed items
    queue["queue"] = []
    queue["processing"] = False
    queue["last_update"] = datetime.now().isoformat()
    save_queue(queue)

    print(f"\n📊 Summary: {successful} successful, {failed} failed")
    return True

def check_limit():
    """Check rate limit (2 per day)"""
    try:
        with open("rate_limiter.json", "r") as f:
            limiter = json.load(f)
    except:
        limiter = {}

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    if today not in limiter:
        limiter[today] = 0

    if limiter[today] >= 2:
        return False

    limiter[today] += 1
    with open("rate_limiter.json", "w") as f:
        json.dump(limiter, f, indent=2)

    return True

if __name__ == "__main__":
    process_queue()
