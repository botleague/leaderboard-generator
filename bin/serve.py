import http.server
import os
import socketserver
from leaderboard_generator.config import config

PORT = int(os.environ.get('PORT', None)) or 8888


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=config.site_dir, **kwargs)


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print('serving http://0.0.0.0:%r' % PORT)
    httpd.serve_forever()
