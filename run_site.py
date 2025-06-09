from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import sys
import logging
from datetime import datetime

# Налаштування логування
logging.basicConfig(
    filename='site.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CustomHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        logging.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        try:
            super().do_GET()
        except Exception as e:
            logging.error(f"Error handling request: {e}")
            self.send_error(500, "Internal server error")

def run_server(port=8081):
    try:
        server_address = ('0.0.0.0', port)  # Використовуємо 0.0.0.0 для прийому зовнішніх підключень
        httpd = HTTPServer(server_address, CustomHandler)  # Використовуємо CustomHandler замість SimpleHTTPRequestHandler
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print(f"🌐 Сайт запущено на:")
        print(f"📱 Локальна адреса: http://localhost:{port}")
        print(f"🌍 Мережева адреса: http://{local_ip}:{port}")
        print(f"⏰ Час запуску: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📝 Логи зберігаються в файлі site.log")
        
        logging.info(f"Server started on port {port}")
        print(f"Сервер запущено на порту {port}")
        print(f"Відкрийте http://localhost:{port} у вашому браузері")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер зупинено користувачем")
        logging.info("Server stopped by user")
    except Exception as e:
        print(f"\n❌ Помилка запуску сервера: {e}")
        logging.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server() 