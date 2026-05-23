from flask import Flask, send_from_directory, request, jsonify, make_response
import os
import requests as http_requests

app = Flask(__name__, static_folder='docs', static_url_path='')

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Accept',
}


@app.route('/')
def index():
    return send_from_directory('docs', 'index.html')


@app.route('/api/create-issue', methods=['POST', 'OPTIONS'])
def create_issue():
    resp = make_response()
    for k, v in CORS_HEADERS.items():
        resp.headers[k] = v

    if request.method == 'OPTIONS':
        resp.status_code = 200
        return resp

    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()

    if not url or 'instagram.com' not in url:
        resp.status_code = 400
        resp.set_data('{"error":"Invalid Instagram URL"}')
        resp.content_type = 'application/json'
        return resp

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        resp.status_code = 500
        resp.set_data('{"error":"GITHUB_TOKEN not configured"}')
        resp.content_type = 'application/json'
        return resp

    reel_id = url.rstrip('/').split('/')[-1] or 'reel'

    gh = http_requests.post(
        'https://api.github.com/repos/xopromo/telethon/issues',
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        },
        json={
            'title': f'Download Reel: {reel_id}',
            'body': f'**Instagram URL:**\n{url}\n\n_Processed by GitHub Actions workflow._',
            'labels': ['reel-download'],
        },
    )

    if not gh.ok:
        resp.status_code = 500
        resp.set_data(f'{{"error":"GitHub API {gh.status_code}"}}')
        resp.content_type = 'application/json'
        return resp

    issue = gh.json()
    resp.status_code = 201
    import json
    resp.set_data(json.dumps({
        'success': True,
        'issue_url': issue['html_url'],
        'issue_number': issue['number'],
    }))
    resp.content_type = 'application/json'
    return resp


@app.route('/<path:path>')
def serve(path):
    return send_from_directory('docs', path)


if __name__ == '__main__':
    app.run(debug=False)
