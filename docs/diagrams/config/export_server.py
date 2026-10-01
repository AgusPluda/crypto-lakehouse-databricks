import http.server, os, sys
OUT = sys.argv[1]
class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        name = os.path.basename(self.path)
        data = self.rfile.read(int(self.headers["Content-Length"]))
        open(os.path.join(OUT, name), "wb").write(data)
        self.send_response(200); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in (("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Headers", "*"), ("Access-Control-Allow-Methods", "*")):
            self.send_header(k, v)
        self.end_headers()
http.server.test(HandlerClass=H, port=8765)
