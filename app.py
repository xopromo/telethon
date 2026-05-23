from flask import Flask, send_from_directory, request, Response
import json
import urllib.request
import urllib.error
import os

app = Flask(__name__, static_folder='docs', static_url_path='')

_CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
}


@app.after_request
def add_cors(resp):
    for k, v in _CORS.items():
        resp.headers[k] = v
    return resp


@app.route('/')
def index():
    return send_from_directory('docs', 'index.html')


@app.route('/api/create-issue', methods=['POST', 'OPTIONS'])
def create_issue():
    if request.method == 'OPTIONS':
        return Response('', 200)

    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()

    if not url or 'instagram.com' not in url:
        return Response(json.dumps({'error': 'Invalid Instagram URL'}), 400,
                        content_type='application/json')

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        return Response(json.dumps({'error': 'GITHUB_TOKEN not configured'}), 500,
                        content_type='application/json')

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
        with urllib.request.urlopen(req) as r:
            issue = json.loads(r.read())
        return Response(json.dumps({
            'success': True,
            'issue_url': issue['html_url'],
            'issue_number': issue['number'],
        }), 201, content_type='application/json')
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        return Response(json.dumps({'error': f'GitHub API {e.code}: {err}'}), 500,
                        content_type='application/json')


@app.route('/<path:path>')
def serve(path):
    return send_from_directory('docs', path)
