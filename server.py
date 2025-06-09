from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import os

def run_server():
    server_address = ('', 8081)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("Сервер запущено на порту 8081")
    print("Відкрийте http://localhost:8081 у вашому браузері")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 