# run_server.py
import socket
from http_server import HttpServer

server = HttpServer()

# Konfigurasi alamat dan port
HOST, PORT = 'localhost', 8000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(5)

print(f"Server berjalan di http://{HOST}:{PORT}")

try:
    while True:
        conn, addr = sock.accept()
        print(f"Koneksi dari {addr}")
        data = conn.recv(1024).decode()
        if data:
            response = server.proses(data)
            conn.sendall(response)
        conn.close()
except KeyboardInterrupt:
    print("\nServer dimatikan")
finally:
    sock.close()
