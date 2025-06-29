import os.path
from glob import glob
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from sos_game import SOSGame

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript'
        }
        # Menyimpan instance game yang aktif, diindeks oleh room_id
        self.games = {}

    def response(self, kode=404, message='Not Found', body=b'', headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append(f"HTTP/1.1 {kode} {message}\r\n")
        resp.append(f"Date: {tanggal}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append(f"Content-Length: {len(body)}\r\n")
        
        for kk in headers:
            resp.append(f"{kk}: {headers[kk]}\r\n")
        resp.append("\r\n")

        response_headers = "".join(resp)
        
        if not isinstance(body, bytes):
            body = str(body).encode('utf-8')
            
        return response_headers.encode('utf-8') + body

    def proses(self, data):
        requests = data.split("\r\n")
        if not requests or not requests[0]:
            return self.response(400, 'Bad Request', b'Invalid HTTP Request')

        baris = requests[0]
        all_headers = [n for n in requests[1:] if n != '']
        j = baris.split(" ")

        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address, all_headers)
            if method == 'POST':
                # Anda bisa implementasikan logika POST jika dibutuhkan di masa depan
                return self.http_post(object_address, all_headers)
            else:
                return self.response(405, 'Method Not Allowed', b'Method Not Allowed')
        except IndexError:
            return self.response(400, 'Bad Request', b'Invalid request line')

    def http_get(self, object_address, headers):
        # Parse URL untuk mendapatkan path dan parameter
        parsed_url = urlparse(object_address)
        path = parsed_url.path
        params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}

        # --- ROUTING UNTUK GAME SOS ---
        if path == '/create_room':
            room_id = params.get("room_id")
            player_name = params.get("player_name")
            board_size = int(params.get("board_size", 3))

            if not room_id or not player_name:
                return self.response(400, "Bad Request", b"Room ID dan Nama Player harus diisi.")
            if room_id in self.games:
                return self.response(400, "Bad Request", f"Room '{room_id}' sudah ada.".encode())
            
            try:
                game = SOSGame(board_size=board_size)
            except ValueError as e:
                return self.response(400, "Bad Request", str(e).encode())

            pid = game.add_player(player_name)
            self.games[room_id] = game
            body = f"success:true\nplayer_id:{pid}\nmessage:Room Dibuat"
            return self.response(200, "OK", body.encode())

        if path == '/join_room':
            room_id = params.get("room_id")
            player_name = params.get("player_name")
            if not room_id or not player_name:
                return self.response(400, "Bad Request", b"Room ID dan Nama Player harus diisi.")
            if room_id not in self.games:
                return self.response(404, "Not Found", f"Room '{room_id}' tidak ditemukan.".encode())
            
            game = self.games[room_id]
            if len(game.players) >= 2:
                return self.response(400, "Bad Request", b"Room sudah penuh.")

            pid = game.add_player(player_name)
            if pid is None:
                return self.response(400, "Bad Request", b"Nama pemain sudah digunakan.")

            body = f"success:true\nplayer_id:{pid}\nmessage:Berhasil Bergabung"
            return self.response(200, "OK", body.encode())

        if path == '/status':
            room_id = params.get("room_id")
            if room_id not in self.games:
                return self.response(404, "Not Found", b"Room tidak ditemukan.")
            game = self.games[room_id]
            return self.response(200, "OK", game.get_status().encode())

        if path == '/move':
            room_id = params.get("room_id")
            pid = params.get("player_id")
            try:
                row, col = int(params.get("row", -1)), int(params.get("col", -1))
                char = params.get("char", "").upper()
            except (ValueError, TypeError):
                 return self.response(400, "Bad Request", b"Parameter tidak valid.")
            
            if room_id not in self.games:
                return self.response(404, "Not Found", b"Room tidak ditemukan.")

            game = self.games[room_id]
            msg = game.make_move(pid, row, col, char)
            if msg == "OK":
                return self.response(200, "OK", game.get_status().encode())
            else:
                return self.response(400, "Bad Request", msg.encode())
        
        if path == '/reset_game':
            room_id = params.get("room_id")
            if room_id not in self.games:
                return self.response(404, "Not Found", b"Room tidak ditemukan.")
            self.games[room_id].reset()
            return self.response(200, "OK", b"Game direset.")

        # --- FALLBACK KE FUNGSI SERVER FILE DARI PROGJAR5 ---
        if path == '/':
            path = '/index.html' 

        file_path = path.strip('/')
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            try:
                with open(file_path, 'rb') as fp:
                    isi = fp.read()
                
                fext = os.path.splitext(file_path)[1].lower()
                content_type = self.types.get(fext, 'application/octet-stream')
                headers = {'Content-type': content_type}
                return self.response(200, 'OK', isi, headers)
            except Exception as e:
                return self.response(500, 'Internal Server Error', str(e).encode())
        else:
            return self.response(404, 'Not Found', b'File or API route not found')


    def http_post(self, object_address, headers):
        return self.response(501, 'Not Implemented', b'POST method not implemented yet.')