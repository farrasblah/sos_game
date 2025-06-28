#sos_game.py
import uuid

class SOSGame:
    def __init__(self, board_size=3):
        """Inisialisasi state game."""
        if board_size not in [3, 5, 9]:
            raise ValueError("Board size must be 3, 5, or 9.")
        self.board_size = board_size 
        self.players = []  
        self.reset()

    def reset(self):
        """Mereset game ke kondisi awal, tapi mempertahankan pemain."""
        self.board = [['' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.scores = {p['id']: 0 for p in self.players}
        self.turn = 0
        self.winner = None
        self.game_over_reason = ""
        self.sos_lines = []

    def add_player(self, player_name):
        """Menambahkan pemain baru dengan nama."""
        if len(self.players) >= 2:
            return None
        if any(p['name'] == player_name for p in self.players):
            return None
        player_id = str(uuid.uuid4())
        player_data = {'id': player_id, 'name': player_name}
        self.players.append(player_data)
        self.scores[player_id] = 0
        return player_id

    def is_board_full(self):
        """Mengecek apakah papan sudah terisi penuh."""
        return all(self.board[r][c] != '' for r in range(self.board_size) for c in range(self.board_size))

    def current_player_id(self):
        """Mendapatkan ID pemain yang sedang giliran."""
        if len(self.players) < 2:
            return None
        return self.players[self.turn % 2]['id']

    def make_move(self, player_id, row, col, char):
        """Memproses langkah pemain."""
        if self.winner:
            return f"Game sudah selesai. Pemenang: {self.winner}"
        if len(self.players) < 2:
            return "Menunggu pemain lain untuk bergabung."
        if player_id != self.current_player_id():
            return "Bukan giliranmu!"
        
        if not(0 <= row < self.board_size and 0 <= col < self.board_size and 
                self.board[row][col] == '' and char in ['S', 'O']):
            return "Langkah tidak valid."

        self.board[row][col] = char
        new_sos_lines = self.check_for_sos(row, col)
        
        if new_sos_lines:
            self.scores[player_id] += len(new_sos_lines)
            for line in new_sos_lines:
                if line not in self.sos_lines:
                    self.sos_lines.append(line)
        else:
            self.turn += 1

        if self.is_board_full():
            p1 = self.players[0]
            p2 = self.players[1]
            if self.scores[p1['id']] > self.scores[p2['id']]:
                self.winner = p1['name']
            elif self.scores[p2['id']] > self.scores[p1['id']]:
                self.winner = p2['name']
            else:
                self.winner = "SERI"
            self.game_over_reason = "Papan Penuh"
        
        return "OK"

    def check_for_sos(self, r, c):
        """
        Mengecek terbentuknya pola S-O-S di sekitar sel (r, c).
        Mengembalikan daftar berisi koordinat garis dari S ke S.
        """
        lines = []
        char = self.board[r][c]
        
        if char == 'O':
            for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                if self.get_char(r - dr, c - dc) == 'S' and self.get_char(r + dr, c + dc) == 'S':
                    p1 = (r - dr, c - dc)
                    p2 = (r + dr, c + dc)
                    lines.append(tuple(sorted((p1, p2))))

        elif char == 'S':
            for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]:
                 if self.get_char(r + dr, c + dc) == 'O' and self.get_char(r + 2*dr, c + 2*dc) == 'S':
                     p1 = (r, c)
                     p2 = (r + 2*dr, c + 2*dc)
                     lines.append(tuple(sorted((p1, p2))))
        return lines

    def get_char(self, r, c):
        """Helper untuk mendapatkan karakter di papan dengan aman."""
        if 0 <= r < self.board_size and 0 <= c < self.board_size:
            return self.board[r][c]
        return ''

    def get_status(self):
        """Mengembalikan status lengkap game dalam format string."""
        status_lines = []
        status_lines.append(f"player_count:{len(self.players)}")
        status_lines.append(f"board_size:{self.board_size}")
        
        p1_id = self.players[0]['id'] if len(self.players) > 0 else "null"
        p1_name = self.players[0]['name'] if len(self.players) > 0 else "N/A"
        p2_id = self.players[1]['id'] if len(self.players) > 1 else "null"
        p2_name = self.players[1]['name'] if len(self.players) > 1 else "Menunggu..."
        
        status_lines.append(f"p1_id:{p1_id}")
        status_lines.append(f"p1_name:{p1_name}")
        status_lines.append(f"p1_score:{self.scores.get(p1_id, 0)}")
        
        status_lines.append(f"p2_id:{p2_id}")
        status_lines.append(f"p2_name:{p2_name}")
        status_lines.append(f"p2_score:{self.scores.get(p2_id, 0)}")

        status_lines.append(f"turn_id:{self.current_player_id() or 'null'}")
        status_lines.append(f"winner:{self.winner or 'null'}")
        
        board_flat = ",".join(["".join(cell or '.' for cell in row) for row in self.board])
        status_lines.append(f"board:{board_flat}")

        lines_str = ";".join([f"{r1},{c1},{r2},{c2}" for (r1, c1), (r2, c2) in self.sos_lines])
        status_lines.append(f"sos_lines:{lines_str}")
        
        return "\n".join(status_lines)