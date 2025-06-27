# http_server.py
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from sos_game import SOSGame

class HttpServer:
    def __init__(self):
        self.games = {} 

    def response(self, kode=200, message='OK', body='', headers=None):
        """Membuat respons HTTP standar."""
        if headers is None: headers = {}
        body_bytes = body.encode('utf-8')
        headers_text = f"""HTTP/1.1 {kode} {message}\r
Date: {datetime.now().ctime()}\r
Content-Length: {len(body_bytes)}\r
Content-Type: text/plain; charset=utf-8\r
Connection: close\r
\r
""".encode('utf-8')
        return headers_text + body_bytes

    def parse_path(self, path):
        """Mengekstrak path dan parameter dari request."""
        parsed = urlparse(path)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        return parsed.path, params

    def proses(self, data):
        """Memproses seluruh request dari klien."""
        try:
            baris_pertama = data.split("\r\n")[0]
            method, path, _ = baris_pertama.split(" ")
            print("[SERVER] Menerima request:")
            print(baris_pertama)
        except ValueError:
            return self.response(400, "Bad Request", "Invalid HTTP request")
        
        if method != "GET":
            return self.response(405, "Method Not Allowed", "Gunakan GET")
        return self.route(path)

    def route(self, path):
        """Mengarahkan request ke fungsi yang sesuai."""
        print(f"[SERVER] Menangani request: {path}")
        path_only, params = self.parse_path(path)
        room_id = params.get("room_id")
        player_name = params.get("player_name")

        # Membuat room baru
        if path_only == "/create_room":
            if not room_id or not player_name:
                return self.response(400, "Bad Request", "Room ID dan Nama Player harus diisi.")
            if room_id in self.games:
                return self.response(400, "Bad Request", f"Room '{room_id}' sudah ada.")
            
            game = SOSGame(board_size=3)
            pid = game.add_player(player_name)
            self.games[room_id] = game
            return self.response(200, "OK", f"Room Dibuat\nplayer_id:{pid}")

        # Bergabung ke room yang ada
        if path_only == "/join_room":
            if not room_id or not player_name:
                return self.response(400, "Bad Request", "Room ID dan Nama Player harus diisi.")
            if room_id not in self.games:
                return self.response(404, "Not Found", f"Room '{room_id}' tidak ditemukan.")

            game = self.games[room_id]
            if len(game.players) >= 2:
                return self.response(400, "Bad Request", "Room sudah penuh.")

            pid = game.add_player(player_name)
            if pid is None:
                return self.response(400, "Bad Request", "Nama pemain sudah digunakan.")

            return self.response(200, "OK", f"Berhasil Bergabung\nplayer_id:{pid}")

        if room_id not in self.games:
            return self.response(404, "Not Found", "Room tidak ditemukan.")
        
        game = self.games[room_id]

        if path_only == "/status":
            return self.response(200, "OK", game.get_status())
            
        # Melakukan langkah
        if path_only == "/move":
            pid = params.get("player_id")
            row = int(params.get("row", -1))
            col = int(params.get("col", -1))
            char = params.get("char", "").upper()
            msg = game.make_move(pid, row, col, char)
            return self.response(200, "OK", msg)
            
        # Mereset game untuk main lagi
        if path_only == "/reset_game":
            game.reset()
            return self.response(200, "OK", "Game direset.")

        return self.response(404, "Not Found", "Route tidak dikenal.")