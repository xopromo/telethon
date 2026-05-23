#!/usr/bin/env python3
"""Instagram video downloader using yt-dlp"""

import subprocess
import json
import os
import os
from pathlib import Path
from typing import Optional, Dict, Any


class InstagramDownloader:
    """Download Instagram videos using yt-dlp"""

    def __init__(self, output_dir: str = "/tmp/instagram_downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract video metadata without downloading"""
        try:
            result = subprocess.run(
                ["yt-dlp", "-j", "--cookies-from-browser", "chrome", url],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Error getting info: {e}")
        return None

    def download(self, url: str, filename: Optional[str] = None) -> bool:
        """Download Instagram video. Returns True if successful"""
        try:
            output_template = f"{self.output_dir}/%(title)s.%(ext)s"
            if filename:
                output_template = f"{self.output_dir}/{filename}.%(ext)s"

            cookies_arg = setup_cookies()
            cookies_flag = cookies_arg.split()[0]
            cookies_value = cookies_arg.split()[1] if len(cookies_arg.split()) > 1 else "chrome"

            cmd = [
                "yt-dlp",
                cookies_flag,
                cookies_value,
                "-f", "best",
                "-o", output_template,
                url,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                print(f"✅ Downloaded: {url}")
                return True
            else:
                print(f"❌ Failed: {result.stderr[:200]}")
                return False

        except Exception as e:
            print(f"Error downloading: {e}")
            return False

    def download_reel(self, url: str) -> Optional[str]:
        """Download Instagram Reel and return file path"""
        if not self.download(url):
            return None

        files = list(self.output_dir.glob("*"))
        if files:
            return str(files[-1])
        return None


def setup_cookies():
    """Setup Instagram cookies from instagram_cookies.json if available"""
    cookies_file = "instagram_cookies.json"
    if os.path.exists(cookies_file):
        return f"--cookies {cookies_file}"
    return "--cookies-from-browser chrome"


# Quick test
if __name__ == "__main__":
    downloader = InstagramDownloader()

    # Test URL
    test_url = "https://www.instagram.com/p/DYpsm93IVGM/"

    print("Getting info...")
    info = downloader.get_info(test_url)
    if info:
        print(f"Title: {info.get('title')}")
        print(f"Duration: {info.get('duration')}s")
        print(f"Uploader: {info.get('uploader')}")

    print("\nAttempting download...")
    downloader.download(test_url, filename="test_video")
