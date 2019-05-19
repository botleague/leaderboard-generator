import http.server
import socketserver
from leaderboard_generator.config import c

PORT = 8888
DIRECTORY = "web"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=c.site_dir, **kwargs)


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print('serving http://0.0.0.0:%r' % PORT)
    httpd.serve_forever()
