"""
Download Instagram Reel and analyze with Gemini
"""
import subprocess
import os
import sys
from pathlib import Path

def download_reel(url: str, output_dir: str = "downloaded_reels") -> str | None:
    """Download Instagram reel using yt-dlp"""
    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-f", "best",  # best quality
        "-o", output_template,
        url
    ]

    try:
        print(f"📥 Downloading: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            # Find the downloaded file
            files = list(Path(output_dir).glob("*"))
            if files:
                latest = max(files, key=os.path.getctime)
                print(f"✅ Downloaded: {latest}")
                return str(latest)
        else:
            print(f"❌ Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

async def analyze_with_gemini(video_path: str) -> str | None:
    """Analyze video with Gemini"""
    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY

        genai.configure(api_key=GEMINI_API_KEY)

        # Upload video file
        print(f"📤 Uploading to Gemini: {video_path}")
        video_file = genai.upload_file(video_path)

        # Analyze
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = """Analyze this Instagram reel and provide:
1. Main content/topic
2. Visual style (colors, transitions, effects)
3. Key message or hook
4. What makes it engaging
5. Suggested improvements

Keep it brief (3-4 sentences per section)."""

        response = model.generate_content([video_file, prompt])
        return response.text
    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")
        return None

async def main():
    if len(sys.argv) < 2:
        print("Usage: python download_instagram_reel.py <instagram_url>")
        print("Example: python download_instagram_reel.py https://www.instagram.com/reel/ABC123/")
        return

    url = sys.argv[1]

    # Download
    video_path = download_reel(url)
    if not video_path:
        return

    # Analyze
    print("\n🤖 Analyzing with Gemini...")
    analysis = await analyze_with_gemini(video_path)

    if analysis:
        print("\n" + "="*60)
        print("ANALYSIS:")
        print("="*60)
        print(analysis)

    print(f"\n💾 Video saved: {video_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
