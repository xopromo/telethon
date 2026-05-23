from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import os


class handler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
        except Exception:
            self._json(400, {'error': 'Invalid JSON'})
            return

        url = data.get('url', '').strip()
        if not url or 'instagram.com' not in url:
            self._json(400, {'error': 'Invalid Instagram URL'})
            return

        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            self._json(500, {'error': 'GITHUB_TOKEN not configured'})
            return

        reel_id = url.rstrip('/').split('/')[-1] or 'reel'

        payload = json.dumps({
            'title': f'Download Reel: {reel_id}',
            'body': f'**Instagram URL:**\n{url}\n\n_Processed by GitHub Actions workflow._',
            'labels': ['reel-download'],
        }).encode()

        req = urllib.request.Request(
            'https://api.github.com/repos/xopromo/telethon/issues',
            data=payload,
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'Content-Type': 'application/json',
            },
        )

        try:
            with urllib.request.urlopen(req) as resp:
                issue = json.loads(resp.read())
            self._json(201, {
                'success': True,
                'issue_url': issue['html_url'],
                'issue_number': issue['number'],
            })
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            self._json(500, {'error': f'GitHub API {e.code}: {err}'})
