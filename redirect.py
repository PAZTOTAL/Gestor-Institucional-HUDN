from http.server import HTTPServer, BaseHTTPRequestHandler

TARGET = "http://172.20.100.173:8000"

class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(301)
        self.send_header("Location", TARGET + self.path)
        self.end_headers()

    def do_POST(self):
        self.send_response(301)
        self.send_header("Location", TARGET + self.path)
        self.end_headers()

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    print(f"Redirigiendo :8000 -> {TARGET}")
    HTTPServer(("0.0.0.0", 8080), RedirectHandler).serve_forever()
