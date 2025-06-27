# sos_gui_client.py
import pygame
import sys
import requests
import time

# --- Konfigurasi Awal ---
pygame.init()
BASE_URL = "http://localhost:8000"
WIDTH, HEIGHT = 500, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SOS Game")
clock = pygame.time.Clock()

# --- Warna ---
C_WHITE = (255, 255, 255)
C_BLACK = (30, 30, 30)
C_GRAY = (200, 200, 200)
C_LIGHT_GRAY = (230, 230, 230)
C_BLUE = (59, 130, 246)   # Warna untuk 'S'
C_GREEN = (34, 197, 94)
C_RED = (239, 68, 68)     # Warna untuk 'O'
C_ORANGE = (249, 115, 22)
C_BG = (241, 245, 249)

# --- Font ---
try:
    F_TITLE = pygame.font.Font(None, 70)
    F_BUTTON = pygame.font.Font(None, 30)
    F_INPUT = pygame.font.Font(None, 28)
    F_INFO = pygame.font.Font(None, 22)
    F_SOS = pygame.font.Font(None, 100)
    F_GAMEOVER = pygame.font.Font(None, 80)
    F_TITLE.set_bold(True)
    F_BUTTON.set_bold(True)
    F_SOS.set_bold(True)
    F_GAMEOVER.set_bold(True)
except Exception:
    F_TITLE = pygame.font.SysFont("arial", 70, bold=True)
    F_BUTTON = pygame.font.SysFont("arial", 30, bold=True)
    F_INPUT = pygame.font.SysFont("arial", 28)
    F_INFO = pygame.font.SysFont("arial", 22)
    F_SOS = pygame.font.SysFont("arial", 100, bold=True)
    F_GAMEOVER = pygame.font.SysFont("arial", 80, bold=True)


# --- State Aplikasi ---
class AppState:
    def __init__(self):
        self.reset_to_home()

    def reset_to_home(self):
        self.current_screen = "home"
        self.room_id = ""
        self.player_name = ""
        self.player_id = None
        self.form_input_room = ""
        self.form_input_name = ""
        self.active_input = "room"
        self.form_type = "create"
        self.error_message = ""
        self.game_state = {}
        self.selected_char = "S"
        self.last_fetch_time = 0
        self.winner_status = ""

app = AppState()

# --- Fungsi Helper & API ---
def parse_status(text):
    """
    Mengurai teks status dari server menjadi dictionary.
    FUNGSI INI TELAH DIPERBAIKI.
    """
    state = {}
    for line in text.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            
            # Penanganan umum untuk semua key
            if val == 'null':
                state[key] = None
                continue
            
            state[key] = val

            # Penanganan khusus untuk 'sos_lines' untuk memastikan tipenya adalah list
            if key == 'sos_lines':
                if not val:  # Jika val adalah string kosong ''
                    state[key] = [] # Ubah menjadi list kosong
                else:
                    lines = []
                    try:
                        # Parsing string koordinat menjadi list of tuples
                        for part in val.split(';'):
                            coords = [int(n) for n in part.split(',')]
                            lines.append(((coords[0], coords[1]), (coords[2], coords[3])))
                        state[key] = lines
                    except (ValueError, IndexError):
                        # Jika format string salah, default ke list kosong agar tidak crash
                        state[key] = []
    return state

def fetch_game_state():
    if not app.room_id or time.time() - app.last_fetch_time < 1:
        return
    try:
        app.last_fetch_time = time.time()
        r = requests.get(f"{BASE_URL}/status?room_id={app.room_id}", timeout=2)
        if r.status_code == 200:
            app.game_state = parse_status(r.text)
            if app.game_state.get('player_count') == '2' and app.current_screen == 'waiting':
                app.current_screen = 'game_board'
            if app.game_state.get('winner') and app.current_screen == 'game_board':
                winner_name = app.game_state['winner']
                if winner_name == 'SERI':
                    app.winner_status = 'SERI'
                elif winner_name == app.player_name:
                    app.winner_status = 'MENANG'
                else:
                    app.winner_status = 'KALAH'
                app.current_screen = 'game_over'
        else:
            app.error_message = r.text
    except requests.RequestException:
        app.error_message = "Server tidak merespon."

def api_call(endpoint, params):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=5)
        if r.status_code == 200:
            app.error_message = ""
            return True, r.text
        else:
            app.error_message = r.text
            return False, r.text
    except requests.RequestException as e:
        app.error_message = "Gagal terhubung ke server."
        return False, str(e)

# --- Fungsi Render ---
def draw_text(text, font, color, center):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    screen.blit(surf, rect)

def draw_button(rect, text, bg_color, text_color, border_radius=12):
    pygame.draw.rect(screen, bg_color, rect, border_radius=border_radius)
    draw_text(text, F_BUTTON, text_color, rect.center)

def draw_home_screen():
    draw_text("Game SOS", F_TITLE, C_BLACK, (WIDTH / 2, HEIGHT / 3))
    btn_create = pygame.Rect(WIDTH/2 - 150, HEIGHT/2, 300, 60)
    btn_join = pygame.Rect(WIDTH/2 - 150, HEIGHT/2 + 80, 300, 60)
    draw_button(btn_create, "BUAT ROOM", C_BLUE, C_WHITE)
    draw_button(btn_join, "GABUNG ROOM", C_GREEN, C_WHITE)
    return {"create": btn_create, "join": btn_join}

def draw_input_form():
    form_title = "Buat Room Baru" if app.form_type == 'create' else "Gabung ke Room"
    draw_text(form_title, F_BUTTON, C_BLACK, (WIDTH/2, 150))
    
    input_room_rect = pygame.Rect(WIDTH/2-200, 220, 400, 50)
    pygame.draw.rect(screen, C_WHITE, input_room_rect, border_radius=8)
    pygame.draw.rect(screen, C_BLUE if app.active_input == "room" else C_GRAY, input_room_rect, 2, border_radius=8)
    draw_text("ID Room", F_INFO, C_GRAY, (WIDTH/2-150, 200))
    draw_text(app.form_input_room, F_INPUT, C_BLACK, (input_room_rect.centerx, input_room_rect.centery))

    input_name_rect = pygame.Rect(WIDTH/2-200, 320, 400, 50)
    pygame.draw.rect(screen, C_WHITE, input_name_rect, border_radius=8)
    pygame.draw.rect(screen, C_BLUE if app.active_input == "name" else C_GRAY, input_name_rect, 2, border_radius=8)
    draw_text("Nama Anda", F_INFO, C_GRAY, (WIDTH/2-150, 300))
    draw_text(app.form_input_name, F_INPUT, C_BLACK, (input_name_rect.centerx, input_name_rect.centery))

    btn_ok = pygame.Rect(WIDTH/2 - 160, 420, 150, 50)
    btn_cancel = pygame.Rect(WIDTH/2 + 10, 420, 150, 50)
    draw_button(btn_ok, "OK", C_GREEN, C_WHITE)
    draw_button(btn_cancel, "BATAL", C_RED, C_WHITE)
    
    if app.error_message:
        draw_text(app.error_message, F_INFO, C_RED, (WIDTH/2, 500))

    return {"room": input_room_rect, "name": input_name_rect, "ok": btn_ok, "cancel": btn_cancel}

def draw_waiting_screen():
    draw_text("Menunggu Lawan...", F_TITLE, C_ORANGE, (WIDTH/2, HEIGHT/3))
    draw_text(f"Room ID: {app.room_id}", F_BUTTON, C_BLACK, (WIDTH/2, HEIGHT/2))
    
def draw_game_board():
    p1_name = app.game_state.get('p1_name', 'Player 1')
    p2_name = app.game_state.get('p2_name', 'Player 2')
    p1_score = app.game_state.get('p1_score', '0')
    p2_score = app.game_state.get('p2_score', '0')
    turn_id = app.game_state.get('turn_id')

    draw_text(f"{p1_name}: {p1_score}", F_BUTTON, C_BLUE if app.player_id == app.game_state.get('p1_id') else C_BLACK, (WIDTH * 0.25, 50))
    draw_text(f"{p2_name}: {p2_score}", F_BUTTON, C_BLUE if app.player_id == app.game_state.get('p2_id') else C_BLACK, (WIDTH * 0.75, 50))
    
    if turn_id == app.player_id:
        draw_text("Giliran Anda!", F_INFO, C_GREEN, (WIDTH/2, 90))
    else:
        draw_text("Menunggu Lawan...", F_INFO, C_ORANGE, (WIDTH/2, 90))

    board_size = 450
    cell_size = board_size // 3
    offset_x, offset_y = (WIDTH - board_size) // 2, 120
    board_rects = []
    
    board_str = app.game_state.get('board', '.'*9).replace(',', '')
    if len(board_str) < 9: board_str = '.' * 9
    
    for r in range(3):
        row_rects = []
        for c in range(3):
            rect = pygame.Rect(offset_x + c * cell_size, offset_y + r * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, C_LIGHT_GRAY, rect)
            pygame.draw.rect(screen, C_GRAY, rect, 2)
            row_rects.append(rect)
            
            letter = board_str[r*3 + c]
            if letter != '.':
                color = C_BLUE if letter == 'S' else C_RED
                draw_text(letter, F_SOS, color, rect.center)
        board_rects.append(row_rects)

    # Kode ini sekarang aman dan tidak akan crash
    sos_lines = app.game_state.get('sos_lines', [])
    for start_pos, end_pos in sos_lines:
        r1, c1 = start_pos
        r2, c2 = end_pos
        start_x = offset_x + c1 * cell_size + cell_size / 2
        start_y = offset_y + r1 * cell_size + cell_size / 2
        end_x = offset_x + c2 * cell_size + cell_size / 2
        end_y = offset_y + r2 * cell_size + cell_size / 2
        pygame.draw.line(screen, C_BLACK, (start_x, start_y), (end_x, end_y), 5)

    btn_s = pygame.Rect(WIDTH/2 - 100, HEIGHT - 80, 80, 50)
    btn_o = pygame.Rect(WIDTH/2 + 20, HEIGHT - 80, 80, 50)
    pygame.draw.rect(screen, C_WHITE, btn_s, border_radius=8)
    pygame.draw.rect(screen, C_BLUE, btn_s, 3 if app.selected_char == 'S' else 1, border_radius=8)
    draw_text("S", F_BUTTON, C_BLUE, btn_s.center)
    pygame.draw.rect(screen, C_WHITE, btn_o, border_radius=8)
    pygame.draw.rect(screen, C_RED, btn_o, 3 if app.selected_char == 'O' else 1, border_radius=8)
    draw_text("O", F_BUTTON, C_RED, btn_o.center)
    
    return {"board": board_rects, "s_btn": btn_s, "o_btn": btn_o}

def draw_game_over_screen():
    color = C_GREEN if app.winner_status == 'MENANG' else C_RED if app.winner_status == 'KALAH' else C_ORANGE
    draw_text(app.winner_status, F_GAMEOVER, color, (WIDTH/2, HEIGHT/3))
    
    btn_play_again = pygame.Rect(WIDTH/2 - 150, HEIGHT/2, 300, 60)
    draw_button(btn_play_again, "MAIN LAGI", C_BLUE, C_WHITE)
    return {"play_again": btn_play_again}

# --- Game Loop Utama ---
while True:
    screen.fill(C_BG)
    
    mouse_pos = pygame.mouse.get_pos()
    events = pygame.event.get()

    # Logika event dipisahkan dari logika menggambar utama
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if app.current_screen == "home":
            if event.type == pygame.MOUSEBUTTONDOWN:
                ui = draw_home_screen()
                if ui["create"].collidepoint(mouse_pos):
                    app.current_screen = "input_form"; app.form_type = "create"; app.error_message = ""
                elif ui["join"].collidepoint(mouse_pos):
                    app.current_screen = "input_form"; app.form_type = "join"; app.error_message = ""

        elif app.current_screen == "input_form":
            ui = draw_input_form()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ui["room"].collidepoint(mouse_pos): app.active_input = "room"
                elif ui["name"].collidepoint(mouse_pos): app.active_input = "name"
                elif ui["cancel"].collidepoint(mouse_pos): app.reset_to_home()
                elif ui["ok"].collidepoint(mouse_pos):
                    app.room_id = app.form_input_room.strip()
                    app.player_name = app.form_input_name.strip()
                    if not app.room_id or not app.player_name:
                        app.error_message = "ID Room dan Nama tidak boleh kosong."
                    else:
                        endpoint = "create_room" if app.form_type == "create" else "join_room"
                        params = {"room_id": app.room_id, "player_name": app.player_name}
                        success, text = api_call(endpoint, params)
                        if success:
                            app.player_id = parse_status(text).get('player_id')
                            app.current_screen = 'waiting'
            if event.type == pygame.KEYDOWN:
                active_str = "form_input_room" if app.active_input == "room" else "form_input_name"
                current_text = getattr(app, active_str)
                if event.key == pygame.K_BACKSPACE: setattr(app, active_str, current_text[:-1])
                elif len(current_text) < 20: setattr(app, active_str, current_text + event.unicode)
                    
        elif app.current_screen == 'game_board':
            if event.type == pygame.MOUSEBUTTONDOWN:
                ui = draw_game_board() # Dipanggil di sini hanya untuk mendapatkan rect
                if ui['s_btn'].collidepoint(mouse_pos): app.selected_char = 'S'
                elif ui['o_btn'].collidepoint(mouse_pos): app.selected_char = 'O'
                else:
                    for r, row_rects in enumerate(ui['board']):
                        for c, rect in enumerate(row_rects):
                            if rect.collidepoint(mouse_pos):
                                params = {"room_id": app.room_id, "player_id": app.player_id, "row": r, "col": c, "char": app.selected_char}
                                api_call("move", params)
                                fetch_game_state() # Paksa update setelah bergerak
                                
        elif app.current_screen == 'game_over':
            if event.type == pygame.MOUSEBUTTONDOWN:
                ui = draw_game_over_screen()
                if ui['play_again'].collidepoint(mouse_pos):
                    api_call("reset_game", {"room_id": app.room_id}) 
                    app.reset_to_home() 

    # --- Menggambar tampilan utama berdasarkan state (setelah semua event diproses) ---
    if app.current_screen == "home":
        draw_home_screen()
    elif app.current_screen == "input_form":
        draw_input_form()
    elif app.current_screen == "waiting":
        fetch_game_state()
        draw_waiting_screen()
    elif app.current_screen == "game_board":
        fetch_game_state()
        draw_game_board()
    elif app.current_screen == "game_over":
        draw_game_over_screen()

    pygame.display.flip()
    clock.tick(30)