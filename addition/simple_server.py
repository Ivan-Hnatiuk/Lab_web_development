from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Метод HTTP:", self.command)
        print("Отримано запит до:", self.path)
        print("Заголовки запиту:")
        print(self.headers)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(bytes("<h1>Простий HTTP-сервер на Python</h1>", "utf-8"))

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8000), SimpleHandler)
    print("Сервер запущено на http://localhost:8000")
    server.serve_forever()