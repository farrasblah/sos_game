# http_server.py
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import uuid
from sos_game import SOSGame

class HttpServer:
    def __init__(self):
        self.games = {}          # Menyimpan game ID → game object
        self.player_letters = {} # Menyimpan game ID → {player_id: letter}

    def response(self, kode=200, message='OK', body='', headers=None):
        if headers is None:
            headers = {}
        if isinstance(body, str):
            body = body.encode()
        headers_text = f"""HTTP/1.0 {kode} {message}\r
Date: {datetime.now().ctime()}\r
Content-Length: {len(body)}\r
Content-Type: text/plain\r
\r
""".encode()
        return headers_text + body

    def parse_path(self, path):
        parsed = urlparse(path)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        return parsed.path, params

    def proses(self, data):
        baris_pertama = data.split("\r\n")[0]
        method, path, _ = baris_pertama.split(" ")
        if method != "GET":
            return self.response(405, "Method Not Allowed", "Gunakan GET")
        return self.route(path)

    def route(self, path):
        path_only, params = self.parse_path(path)

        # BUAT GAME BARU
        if path_only == "/join":
            game_id = str(uuid.uuid4())
            game = SOSGame()
            pid = game.add_player()
            if pid is None:
                return self.response(400, "Bad Request", "Gagal tambah player")
            self.games[game_id] = game
            self.player_letters[game_id] = {pid: "S"}
            return self.response(200, "OK", f"Game ID: {game_id}\nPlayer ID: {pid}\nLetter: S")

        # JOIN KE GAME YANG SUDAH ADA
        if path_only == "/join_game":
            gid = params.get("game_id")
            if gid in self.games:
                game = self.games[gid]
                pid = game.add_player()
                if pid:
                    huruf = "O"
                    self.player_letters[gid][pid] = huruf
                    return self.response(200, "OK", f"Game ID: {gid}\nPlayer ID: {pid}\nLetter: {huruf}")
                else:
                    return self.response(400, "Bad Request", "Game full")
            return self.response(404, "Not Found", "Game not found")

        # MEMAINKAN LANGKAH
        if path_only == "/move":
            gid = params.get("game_id")
            pid = params.get("player")
            row = int(params.get("row", -1))
            col = int(params.get("col", -1))
            char = params.get("char", "").upper()
            if gid in self.games:
                # Cek apakah player pakai huruf yang sesuai
                expected_char = self.player_letters.get(gid, {}).get(pid, "")
                if char != expected_char:
                    return self.response(400, "Bad Request", f"Kamu hanya bisa pakai huruf '{expected_char}'")
                msg = self.games[gid].make_move(pid, row, col, char)
                return self.response(200, "OK", msg)
            return self.response(404, "Not Found", "Game not found")

        # LIHAT BOARD
        if path_only == "/board":
            gid = params.get("game_id")
            if gid in self.games:
                return self.response(200, "OK", self.games[gid].board_string())
            return self.response(404, "Not Found", "Game not found")

        # CEK STATUS PEMENANG
        if path_only == "/status":
            gid = params.get("game_id")
            if gid in self.games:
                winner = self.games[gid].winner
                if winner:
                    return self.response(200, "OK", f"Pemenang: {winner}")
                return self.response(200, "OK", "Belum selesai")
            return self.response(404, "Not Found", "Game not found")

        # DEFAULT
        return self.response(404, "Not Found", "Unknown route")


# Untuk pengujian manual
if __name__ == "__main__":
    server = HttpServer()
    print(server.proses("GET /join HTTP/1.0\r\n\r\n").decode())
