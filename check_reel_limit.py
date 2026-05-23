#!/usr/bin/env python3
"""
Rate limiter for Instagram reel downloads - 2 per day
"""

import json
from datetime import datetime
import sys

def check_and_update_limit():
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        with open("rate_limiter.json", "r") as f:
            limiter = json.load(f)
    except:
        limiter = {}

    # Initialize today if not exists
    if today not in limiter:
        limiter[today] = 0

    count = limiter[today]

    if count >= 2:
        print(f"❌ Лимит исчерпан! Скачиваний сегодня: {count}/2")
        print("Попробуй завтра 🌅")
        return False

    # Increment counter
    limiter[today] = count + 1

    # Save back
    with open("rate_limiter.json", "w") as f:
        json.dump(limiter, f, indent=2)

    remaining = 2 - limiter[today]
    print(f"✅ Скачивание разрешено! Осталось сегодня: {remaining}")
    return True

if __name__ == "__main__":
    if check_and_update_limit():
        sys.exit(0)
    else:
        sys.exit(1)
