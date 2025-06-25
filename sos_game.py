# sos_game.py
import uuid

class SOSGame:
    def __init__(self):
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.players = []
        self.turn = 0
        self.winner = None

    def add_player(self):
        if len(self.players) >= 2:
            return None
        player_id = str(uuid.uuid4())
        self.players.append(player_id)
        return player_id

    def current_player(self):
        return self.players[self.turn % 2]

    def is_valid_move(self, row, col, char):
        if char not in ['S', 'O']:
            return False
        if not (0 <= row < 3 and 0 <= col < 3):
            return False
        if self.board[row][col] != '':
            return False
        return True

    def make_move(self, player, row, col, char):
        if self.winner or len(self.players) < 2:
            return "Game belum bisa dimainkan."
        if player != self.current_player():
            return "Bukan giliranmu!"
        if not self.is_valid_move(row, col, char):
            return "Langkah tidak valid."

        self.board[row][col] = char
        if self.check_win(player):
            self.winner = player

        else:
            self.turn += 1
        return "OK"

    def check_win(self, player):
        for r in range(3):
            for c in range(3):
                if self.check_sos(r, c):
                    return True  # return True kalau menemukan pola SOS
        return False

    def check_sos(self, r, c):
        def get(r, c):
            if 0 <= r < 3 and 0 <= c < 3:
                return self.board[r][c]
            return ''
        directions = [(0,1), (1,0), (1,1), (1,-1)]
        for dr, dc in directions:
            if get(r, c) == 'S' and get(r+dr, c+dc) == 'O' and get(r+2*dr, c+2*dc) == 'S':
                print(f"SOS ditemukan di: ({r},{c}) → arah ({dr},{dc})")
                return True
        return False

    def board_string(self):
        return "\n".join([" | ".join(cell or '.' for cell in row) for row in self.board])
