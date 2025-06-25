# sos_gui_client.py
import pygame
import sys
import requests

pygame.init()

WIDTH, HEIGHT = 300, 350
ROWS, COLS = 3, 3
CELL_SIZE = WIDTH // COLS

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game SOS - Multiplayer")

FONT = pygame.font.SysFont("arial", 40)
INFO_FONT = pygame.font.SysFont("arial", 24)

BASE_URL = "http://localhost:8000"

# Variabel pemain
game_id = input("Masukkan Game ID (kosong = buat baru): ")
player_id = ""
player_letter = ""

# Join game
if not game_id:
    r = requests.get(BASE_URL + "/join")
else:
    r = requests.get(f"{BASE_URL}/join_game?game_id={game_id}")

# Ambil semua info dari respons
for line in r.text.strip().split('\n'):
    if "Game ID" in line:
        game_id = line.split(": ")[1]
    if "Player ID" in line:
        player_id = line.split(": ")[1]
    if "Letter" in line:
        player_letter = line.split(": ")[1]

print(f"Game ID: {game_id}, Player ID: {player_id}, Letter: {player_letter}")

def get_board():
    r = requests.get(f"{BASE_URL}/board?game_id={game_id}")
    return r.text.strip().split('\n')

def send_move(row, col):
    r = requests.get(f"{BASE_URL}/move?game_id={game_id}&player={player_id}&row={row}&col={col}&char={player_letter}")
    return r.text.strip()

def get_status():
    r = requests.get(f"{BASE_URL}/status?game_id={game_id}")
    return r.text.strip()

def draw_grid(board, status):
    screen.fill((255, 255, 255))

    for row in range(ROWS):
        for col in range(COLS):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)

            letter = board[row][col]
            if letter != ".":
                text = FONT.render(letter, True, (0, 0, 255))
                screen.blit(text, (col * CELL_SIZE + 20, row * CELL_SIZE + 10))

    color = (0, 128, 0) if "Pemenang" not in status else (255, 0, 0)
    status_text = INFO_FONT.render(status, True, color)
    screen.blit(status_text, (10, HEIGHT - 40))

    pygame.display.flip()

# Loop game
game_over = False
while True:
    board = get_board()
    board_matrix = [row.split(" | ") for row in board]
    status = get_status()
    draw_grid(board_matrix, status)

    if "Pemenang" in status:
        game_over = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            x, y = pygame.mouse.get_pos()
            col = x // CELL_SIZE
            row = y // CELL_SIZE
            result = send_move(row, col)
            print(result)
