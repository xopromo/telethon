from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='docs', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('docs', 'index.html')

@app.route('/<path:path>')
def serve(path):
    if path.endswith('.html'):
        return send_from_directory('docs', path)
    return send_from_directory('docs', path)

if __name__ == '__main__':
    app.run(debug=False)
