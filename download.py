#!/usr/bin/env python3
"""
🎬 Instagram Video Downloader — Simple One-Click Download

Usage: python download.py
Then just paste Instagram URL and it downloads!
"""

import subprocess
import sys

def main():
    print("\n" + "="*50)
    print("🎬 Instagram Video Downloader")
    print("="*50)

    url = input("\n🔗 Вставь Instagram ссылку:\n> ").strip()

    if not url:
        print("❌ Ссылка пуста!")
        sys.exit(1)

    if "instagram.com" not in url:
        print("❌ Это не Instagram ссылка!")
        sys.exit(1)

    print("\n⏳ Загружаю видео...\n")

    result = subprocess.run(
        [sys.executable, "instagram_agent.py", url],
        cwd=sys.path[0] if sys.path[0] else "."
    )

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
