# run_server.py
import socket
from concurrent.futures import ThreadPoolExecutor
from http_server import HttpServer

# Inisialisasi server logic
server_logic = HttpServer()

def handle_connection(connection):
    """Fungsi untuk menangani satu koneksi klien dalam satu thread."""
    try:
        connection.settimeout(5) 
        data = connection.recv(1024).decode('utf-8')
        if data:
            response = server_logic.proses(data)
            connection.sendall(response)
    except socket.timeout:
        print("Connection timed out.")
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        connection.close()

def run_server():
    HOST, PORT = 'localhost', 8000
    
    # Menggunakan ThreadPoolExecutor untuk menangani banyak klien secara bersamaan
    executor = ThreadPoolExecutor(max_workers=20)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(5)
        print(f"Server berjalan di http://{HOST}:{PORT}")
        print("Server siap menerima koneksi...")

        try:
            while True:
                conn, addr = sock.accept()
                # Setiap koneksi baru diserahkan ke thread dari pool untuk diproses
                executor.submit(handle_connection, conn)
        except KeyboardInterrupt:
            print("\nServer dimatikan.")
        finally:
            executor.shutdown(wait=True)

if __name__ == "__main__":
    run_server()