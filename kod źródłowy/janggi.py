import copy
import os
import random
import sys

import pygame



# konfiguracja gry


BOARD_WIDTH = 600
HEIGHT = 700
SIDE_PANEL_WIDTH = 260
WIDTH = BOARD_WIDTH + SIDE_PANEL_WIDTH

ROWS = 10
COLS = 9
CELL_SIZE = BOARD_WIDTH // COLS

BOARD_COLOR = (218, 165, 32)
LINE_COLOR = (0, 0, 0)
SELECT_COLOR = (0, 255, 0)
MOVE_COLOR = (50, 150, 255)
CAPTURE_COLOR = (255, 50, 50)
CHECK_COLOR = (255, 0, 0)
PANEL_COLOR = (235, 200, 120)
BUTTON_COLOR = (180, 120, 20)

BLUE = "b"
RED = "r"

DIFFICULTY_DEPTH = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
}

DIFFICULTY_LABELS = {
    "easy": "Łatwy",
    "medium": "Średni",
    "hard": "Trudny",
}

PLAYER_TIME_LIMITS = {
    "easy": 15 * 60,
    "medium": 10 * 60,
    "hard": 5 * 60,
}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Janggi - Korean Chess")
font = pygame.font.SysFont("arial", 26)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_menu_background():
    path = os.path.join(BASE_DIR, "menu_background_final_updated.png")

    if not os.path.exists(path):
        return None

    image = pygame.image.load(path).convert()


    image_ratio = image.get_width() / image.get_height()
    window_ratio = WIDTH / HEIGHT

    if image_ratio > window_ratio:
        scaled_height = HEIGHT
        scaled_width = int(HEIGHT * image_ratio)
    else:
        scaled_width = WIDTH
        scaled_height = int(WIDTH / image_ratio)

    image = pygame.transform.smoothscale(
        image,
        (scaled_width, scaled_height),
    )

    x = (scaled_width - WIDTH) // 2
    y = (scaled_height - HEIGHT) // 2

    return image.subsurface((x, y, WIDTH, HEIGHT)).copy()


MENU_BACKGROUND = load_menu_background()


# Figury


def load_piece(name):
    image = pygame.image.load(os.path.join(BASE_DIR, name)).convert_alpha()
    return pygame.transform.smoothscale(image, (60, 60))


PIECES = {
    "r_cha": load_piece("red_cha.png"),
    "b_cha": load_piece("blue_cha.png"),
    "r_ma": load_piece("red_ma.png"),
    "b_ma": load_piece("blue_ma.png"),
    "r_pao": load_piece("red_pao.png"),
    "b_pao": load_piece("blue_pao.png"),
    "r_sang": load_piece("red_sang.png"),
    "b_sang": load_piece("blue_sang.png"),
    "r_sa": load_piece("red_sa.png"),
    "b_sa": load_piece("blue_sa.png"),
    "r_king": load_piece("red_king.png"),
    "b_king": load_piece("blue_king.png"),
    "r_jol": load_piece("red_jol.png"),
    "b_jol": load_piece("blue_jol.png"),
}

STARTING_POSITIONS = [
    ["r_cha", "r_sang", "r_ma", "r_sa", None, "r_sa", "r_ma", "r_sang", "r_cha"],
    [None, None, None, None, "r_king", None, None, None, None],
    [None, "r_pao", None, None, None, None, None, "r_pao", None],
    ["r_jol", None, "r_jol", None, "r_jol", None, "r_jol", None, "r_jol"],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
    ["b_jol", None, "b_jol", None, "b_jol", None, "b_jol", None, "b_jol"],
    [None, "b_pao", None, None, None, None, None, "b_pao", None],
    [None, None, None, None, "b_king", None, None, None, None],
    ["b_cha", "b_sang", "b_ma", "b_sa", None, "b_sa", "b_ma", "b_sang", "b_cha"],
]

PIECE_VALUES = {
    "king": 10000,
    "cha": 90,
    "pao": 55,
    "ma": 45,
    "sang": 35,
    "sa": 20,
    "jol": 15,
}

PIECE_POINTS = {
    "cha": 13,
    "pao": 7,
    "ma": 5,
    "sang": 3,
    "sa": 3,
    "jol": 2,
    "king": 0,
}

PIECE_NAMES = {
    "king": "Generał",
    "cha": "Rydwan",
    "pao": "Działo",
    "ma": "Koń",
    "sang": "Słoń",
    "sa": "Strażnik",
    "jol": "Żołnierz",
}



# stan gry


board = copy.deepcopy(STARTING_POSITIONS)
turn = BLUE
selected = None
winner = None

move_history = []
move_log = []
captured_by_blue = []
captured_by_red = []

ai_difficulty = "medium"

player_time_remaining = float(PLAYER_TIME_LIMITS[ai_difficulty])
game_end_reason = None
consecutive_passes = 0



# funkcje pomocnicze


def inside(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def color_of(piece):
    return piece[0] if piece else None


def type_of(piece):
    return piece[2:] if piece else None


def enemy(piece1, piece2):
    return piece1 and piece2 and color_of(piece1) != color_of(piece2)


def empty_or_enemy(piece, r, c):
    return inside(r, c) and (board[r][c] is None or enemy(piece, board[r][c]))


def opponent_of(color):
    return RED if color == BLUE else BLUE


def format_piece_name(piece):
    return PIECE_NAMES.get(type_of(piece), type_of(piece))



# Punktacja


def calculate_points(color):
    total = 0

    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]
            if piece and color_of(piece) == color:
                total += PIECE_POINTS.get(type_of(piece), 0)

    # W przyjętym wariancie czerwony otrzymuje 1,5 punktu kompensacji.
    if color == RED:
        total += 1.5

    return total



#  Pałac


def in_palace(color, r, c):
    if color == RED:
        return 0 <= r <= 2 and 3 <= c <= 5
    return 7 <= r <= 9 and 3 <= c <= 5


def palace_diagonal_allowed(r1, c1, r2, c2):
    diagonals = {
        (0, 3): [(1, 4)],
        (0, 5): [(1, 4)],
        (1, 4): [(0, 3), (0, 5), (2, 3), (2, 5)],
        (2, 3): [(1, 4)],
        (2, 5): [(1, 4)],

        (7, 3): [(8, 4)],
        (7, 5): [(8, 4)],
        (8, 4): [(7, 3), (7, 5), (9, 3), (9, 5)],
        (9, 3): [(8, 4)],
        (9, 5): [(8, 4)],
    }

    return (r2, c2) in diagonals.get((r1, c1), [])



# Generał i szach


def find_king(color):
    target = color + "_king"

    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == target:
                return r, c

    return None


def kings_facing():
    red_king = find_king(RED)
    blue_king = find_king(BLUE)

    if red_king is None or blue_king is None:
        return False

    rr, rc = red_king
    br, bc = blue_king

    if rc != bc:
        return False

    start = min(rr, br) + 1
    end = max(rr, br)

    for r in range(start, end):
        if board[r][rc] is not None:
            return False

    return True



# Generowanie ruchów figur


def get_king_moves(piece, r, c):
    moves = []
    color = color_of(piece)

    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1),
    ]

    for dr, dc in directions:
        nr, nc = r + dr, c + dc

        if not inside(nr, nc):
            continue

        if abs(dr) + abs(dc) == 2 and not palace_diagonal_allowed(r, c, nr, nc):
            continue

        if in_palace(color, nr, nc) and empty_or_enemy(piece, nr, nc):
            moves.append((nr, nc))

    return moves


def get_sa_moves(piece, r, c):
    return get_king_moves(piece, r, c)


def get_jol_moves(piece, r, c):
    moves = []
    color = color_of(piece)
    forward = 1 if color == RED else -1

    candidates = [
        (r + forward, c),
        (r, c - 1),
        (r, c + 1),
    ]

    for nr, nc in candidates:
        if empty_or_enemy(piece, nr, nc):
            moves.append((nr, nc))

    for dr, dc in [(forward, -1), (forward, 1)]:
        nr, nc = r + dr, c + dc

        if (
            inside(nr, nc)
            and palace_diagonal_allowed(r, c, nr, nc)
            and empty_or_enemy(piece, nr, nc)
        ):
            moves.append((nr, nc))

    return moves


def get_cha_moves(piece, r, c):
    moves = []

    # Ruch ortogonalny.
    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nr, nc = r + dr, c + dc

        while inside(nr, nc):
            if board[nr][nc] is None:
                moves.append((nr, nc))
            else:
                if enemy(piece, board[nr][nc]):
                    moves.append((nr, nc))
                break

            nr += dr
            nc += dc

    # Ruch po przekątnych pałacu.
    for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        cr, cc = r, c
        nr, nc = cr + dr, cc + dc

        while inside(nr, nc) and palace_diagonal_allowed(cr, cc, nr, nc):
            if board[nr][nc] is None:
                moves.append((nr, nc))
            else:
                if enemy(piece, board[nr][nc]):
                    moves.append((nr, nc))
                break

            cr, cc = nr, nc
            nr, nc = cr + dr, cc + dc

    return moves


def get_pao_moves(piece, r, c):
    moves = []


    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nr, nc = r + dr, c + dc
        jumped = False

        while inside(nr, nc):
            current = board[nr][nc]

            if not jumped:
                if current is not None:
                    if type_of(current) != "pao":
                        jumped = True
                    else:
                        break
            else:
                if current is None:
                    moves.append((nr, nc))
                else:
                    if enemy(piece, current) and type_of(current) != "pao":
                        moves.append((nr, nc))
                    break

            nr += dr
            nc += dc


    palace_diagonal_jumps = {
        (0, 3): ((1, 4), (2, 5)),
        (0, 5): ((1, 4), (2, 3)),
        (2, 3): ((1, 4), (0, 5)),
        (2, 5): ((1, 4), (0, 3)),
        (7, 3): ((8, 4), (9, 5)),
        (7, 5): ((8, 4), (9, 3)),
        (9, 3): ((8, 4), (7, 5)),
        (9, 5): ((8, 4), (7, 3)),
    }

    diagonal = palace_diagonal_jumps.get((r, c))
    if diagonal:
        (screen_r, screen_c), (target_r, target_c) = diagonal
        screen_piece = board[screen_r][screen_c]
        target_piece = board[target_r][target_c]

        if screen_piece is not None and type_of(screen_piece) != "pao":
            if target_piece is None:
                moves.append((target_r, target_c))
            elif enemy(piece, target_piece) and type_of(target_piece) != "pao":
                moves.append((target_r, target_c))

    return moves


def get_ma_moves(piece, r, c):
    moves = []

    patterns = [
        (-2, -1, -1, 0),
        (-2, 1, -1, 0),
        (2, -1, 1, 0),
        (2, 1, 1, 0),
        (-1, -2, 0, -1),
        (1, -2, 0, -1),
        (-1, 2, 0, 1),
        (1, 2, 0, 1),
    ]

    for dr, dc, block_dr, block_dc in patterns:
        block_r, block_c = r + block_dr, c + block_dc
        nr, nc = r + dr, c + dc

        if (
            inside(nr, nc)
            and inside(block_r, block_c)
            and board[block_r][block_c] is None
            and empty_or_enemy(piece, nr, nc)
        ):
            moves.append((nr, nc))

    return moves


def get_sang_moves(piece, r, c):
    moves = []

    patterns = [
        (-3, -2, -1, 0, -2, -1),
        (-3, 2, -1, 0, -2, 1),
        (3, -2, 1, 0, 2, -1),
        (3, 2, 1, 0, 2, 1),
        (-2, -3, 0, -1, -1, -2),
        (2, -3, 0, -1, 1, -2),
        (-2, 3, 0, 1, -1, 2),
        (2, 3, 0, 1, 1, 2),
    ]

    for dr, dc, br1, bc1, br2, bc2 in patterns:
        b1r, b1c = r + br1, c + bc1
        b2r, b2c = r + br2, c + bc2
        nr, nc = r + dr, c + dc

        if (
            inside(nr, nc)
            and inside(b1r, b1c)
            and inside(b2r, b2c)
            and board[b1r][b1c] is None
            and board[b2r][b2c] is None
            and empty_or_enemy(piece, nr, nc)
        ):
            moves.append((nr, nc))

    return moves


def get_raw_moves_for_piece(r, c):
    piece = board[r][c]

    if piece is None:
        return []

    kind = type_of(piece)

    move_generators = {
        "king": get_king_moves,
        "sa": get_sa_moves,
        "jol": get_jol_moves,
        "cha": get_cha_moves,
        "pao": get_pao_moves,
        "ma": get_ma_moves,
        "sang": get_sang_moves,
    }

    generator = move_generators.get(kind)
    return generator(piece, r, c) if generator else []




def square_attacked_by(color, target_r, target_c):
    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]

            if piece and color_of(piece) == color:
                if (target_r, target_c) in get_raw_moves_for_piece(r, c):
                    return True

    return False


def is_in_check(color):
    king_pos = find_king(color)

    if king_pos is None:
        return True

    king_r, king_c = king_pos
    opponent = opponent_of(color)

    if square_attacked_by(opponent, king_r, king_c):
        return True


    return False


def simulate_move(sr, sc, er, ec):
    moving_piece = board[sr][sc]
    captured_piece = board[er][ec]

    board[er][ec] = moving_piece
    board[sr][sc] = None

    return captured_piece


def undo_simulated_move(sr, sc, er, ec, captured_piece):
    moving_piece = board[er][ec]

    board[sr][sc] = moving_piece
    board[er][ec] = captured_piece


def get_legal_moves_for_piece(r, c):
    piece = board[r][c]

    if piece is None:
        return []

    color = color_of(piece)
    legal_moves = []
    bikjang_before_move = kings_facing()

    for er, ec in get_raw_moves_for_piece(r, c):
        target = board[er][ec]


        if target and type_of(target) == "king":
            continue

        captured = simulate_move(r, c, er, ec)

        legal = not is_in_check(color)


        if bikjang_before_move and kings_facing():
            legal = False

        if legal:
            legal_moves.append((er, ec))

        undo_simulated_move(r, c, er, ec, captured)

    return legal_moves


def get_all_legal_moves(color):
    moves = []

    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]

            if piece and color_of(piece) == color:
                for er, ec in get_legal_moves_for_piece(r, c):
                    moves.append((r, c, er, ec))

    return moves


def is_checkmate(color):
    return is_in_check(color) and not get_all_legal_moves(color)


def update_game_state_after_move():
    global winner, game_end_reason

    if is_checkmate(RED):
        winner = BLUE
        game_end_reason = "checkmate"
    elif is_checkmate(BLUE):
        winner = RED
        game_end_reason = "checkmate"



# Historia i wykonywanie ruchów


def save_position():
    move_history.append(
        (
            copy.deepcopy(board),
            turn,
            winner,
            copy.deepcopy(move_log),
            copy.deepcopy(captured_by_blue),
            copy.deepcopy(captured_by_red),
            player_time_remaining,
            game_end_reason,
            consecutive_passes,
        )
    )


def make_move(sr, sc, er, ec, save=True):
    global move_log, captured_by_blue, captured_by_red, consecutive_passes

    if save:
        save_position()

    consecutive_passes = 0

    moving_piece = board[sr][sc]
    captured_piece = board[er][ec]
    moving_color = color_of(moving_piece)

    if captured_piece:
        if moving_color == BLUE:
            captured_by_blue.append(captured_piece)
        else:
            captured_by_red.append(captured_piece)

    board[er][ec] = moving_piece
    board[sr][sc] = None

    side_name = "Gracz" if moving_color == BLUE else "Komputer"
    capture_text = (
        f" x {format_piece_name(captured_piece)}"
        if captured_piece
        else ""
    )

    move_log.append(
        f"{side_name}: {format_piece_name(moving_piece)} "
        f"({sr},{sc})->({er},{ec}){capture_text}"
    )

    update_game_state_after_move()


def undo_last_turn():
    global board, turn, selected, winner
    global move_log, captured_by_blue, captured_by_red
    global player_time_remaining, game_end_reason, consecutive_passes

    if not move_history:
        return

    (
        board,
        turn,
        winner,
        move_log,
        captured_by_blue,
        captured_by_red,
        player_time_remaining,
        game_end_reason,
        consecutive_passes,
    ) = move_history.pop()

    selected = None


def pass_turn(color, save=True):
    global turn, selected, winner, game_end_reason, consecutive_passes

    # Brak funkcji pas podczas szacha
    if winner is not None or is_in_check(color):
        return False

    if save:
        save_position()

    side_name = "Gracz" if color == BLUE else "Komputer"
    move_log.append(f"{side_name}: PAS")
    selected = None


    if kings_facing():
        winner = "draw"
        game_end_reason = "bikjang"
        return True

    consecutive_passes += 1


    if consecutive_passes >= 2:
        winner = "draw"
        game_end_reason = "double_pass"
        return True

    turn = opponent_of(color)
    return True


def resolve_game_on_time():
    global winner, game_end_reason

    blue_score = calculate_points(BLUE)
    red_score = calculate_points(RED)

    if blue_score > red_score:
        winner = BLUE
    elif red_score > blue_score:
        winner = RED
    else:
        winner = "draw"

    game_end_reason = "time"


def format_time(seconds):
    total_seconds = max(0, int(seconds + 0.999))
    minutes = total_seconds // 60
    secs = total_seconds % 60
    return f"{minutes:02d}:{secs:02d}"



# Sztuczna inteligencja


def evaluate_board():

    if is_checkmate(BLUE):
        return 1_000_000

    if is_checkmate(RED):
        return -1_000_000

    score = 0

    # Materiał.
    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]

            if piece is None:
                continue

            value = PIECE_VALUES.get(type_of(piece), 0)

            if color_of(piece) == RED:
                score += value
            else:
                score -= value


    if is_in_check(BLUE):
        score += 40

    if is_in_check(RED):
        score -= 40




    return score


def move_order_score(move):

    _, _, er, ec = move
    target = board[er][ec]

    if target is None:
        return 0

    return PIECE_VALUES.get(type_of(target), 0)


def ordered_moves(color):
    moves = get_all_legal_moves(color)
    return sorted(moves, key=move_order_score, reverse=True)


def minimax(depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate_board()

    color = RED if maximizing_player else BLUE
    moves = ordered_moves(color)

    if not moves:
        return evaluate_board()

    if maximizing_player:
        best_score = -float("inf")

        for sr, sc, er, ec in moves:
            captured = simulate_move(sr, sc, er, ec)

            score = minimax(
                depth - 1,
                alpha,
                beta,
                False,
            )

            undo_simulated_move(sr, sc, er, ec, captured)

            best_score = max(best_score, score)
            alpha = max(alpha, best_score)

            if beta <= alpha:
                break

        return best_score

    best_score = float("inf")

    for sr, sc, er, ec in moves:
        captured = simulate_move(sr, sc, er, ec)

        score = minimax(
            depth - 1,
            alpha,
            beta,
            True,
        )

        undo_simulated_move(sr, sc, er, ec, captured)

        best_score = min(best_score, score)
        beta = min(beta, best_score)

        if beta <= alpha:
            break

    return best_score


def choose_ai_move_easy(moves):

    scored_moves = []

    for move in moves:
        sr, sc, er, ec = move
        target = board[er][ec]

        score = random.randint(0, 25)

        if target:
            score += PIECE_VALUES.get(type_of(target), 0) * 5

        captured = simulate_move(sr, sc, er, ec)

        if is_in_check(BLUE):
            score += 30

        undo_simulated_move(sr, sc, er, ec, captured)
        scored_moves.append((score, move))

    scored_moves.sort(key=lambda item: item[0], reverse=True)


    top_count = min(4, len(scored_moves))
    return random.choice(scored_moves[:top_count])[1]


def choose_ai_move_minimax(moves, depth):
    best_score = -float("inf")
    best_moves = []


    moves = sorted(moves, key=move_order_score, reverse=True)

    for sr, sc, er, ec in moves:
        captured = simulate_move(sr, sc, er, ec)

        score = minimax(
            depth - 1,
            -float("inf"),
            float("inf"),
            False,
        )

        undo_simulated_move(sr, sc, er, ec, captured)

        if score > best_score:
            best_score = score
            best_moves = [(sr, sc, er, ec)]
        elif score == best_score:
            best_moves.append((sr, sc, er, ec))

    return random.choice(best_moves)


def ai_move():
    global turn, winner, game_end_reason

    moves = get_all_legal_moves(RED)


    if kings_facing():
        if not moves or evaluate_board() <= 0:
            pass_turn(RED, save=False)
            return

    if not moves:
        if is_in_check(RED):
            winner = BLUE
            game_end_reason = "checkmate"
        else:

            pass_turn(RED, save=False)
        return

    if ai_difficulty == "easy":
        chosen_move = choose_ai_move_easy(moves)
    else:
        depth = DIFFICULTY_DEPTH[ai_difficulty]
        chosen_move = choose_ai_move_minimax(moves, depth)

    sr, sc, er, ec = chosen_move
    make_move(sr, sc, er, ec, save=False)

    if winner is None:
        turn = BLUE



# Interfejs

def draw_board():
    screen.fill(BOARD_COLOR)

    for row in range(ROWS):
        for col in range(COLS):
            x = col * CELL_SIZE + CELL_SIZE // 2
            y = row * CELL_SIZE + CELL_SIZE // 2

            pygame.draw.circle(screen, LINE_COLOR, (x, y), 5)

            if col < COLS - 1:
                pygame.draw.line(
                    screen,
                    LINE_COLOR,
                    (x, y),
                    (x + CELL_SIZE, y),
                    1,
                )

            if row < ROWS - 1:
                pygame.draw.line(
                    screen,
                    LINE_COLOR,
                    (x, y),
                    (x, y + CELL_SIZE),
                    1,
                )

    pygame.draw.line(
        screen,
        LINE_COLOR,
        (3.5 * CELL_SIZE, 0.5 * CELL_SIZE),
        (5.5 * CELL_SIZE, 2.5 * CELL_SIZE),
        2,
    )
    pygame.draw.line(
        screen,
        LINE_COLOR,
        (5.5 * CELL_SIZE, 0.5 * CELL_SIZE),
        (3.5 * CELL_SIZE, 2.5 * CELL_SIZE),
        2,
    )

    pygame.draw.line(
        screen,
        LINE_COLOR,
        (3.5 * CELL_SIZE, 7.5 * CELL_SIZE),
        (5.5 * CELL_SIZE, 9.5 * CELL_SIZE),
        2,
    )
    pygame.draw.line(
        screen,
        LINE_COLOR,
        (5.5 * CELL_SIZE, 7.5 * CELL_SIZE),
        (3.5 * CELL_SIZE, 9.5 * CELL_SIZE),
        2,
    )


def draw_pieces():
    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]

            if piece:
                rect = PIECES[piece].get_rect(
                    center=(
                        col * CELL_SIZE + CELL_SIZE // 2,
                        row * CELL_SIZE + CELL_SIZE // 2,
                    )
                )
                screen.blit(PIECES[piece], rect)


def draw_highlights():
    if not selected:
        return

    r, c = selected

    pygame.draw.rect(
        screen,
        SELECT_COLOR,
        (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE),
        3,
    )

    for mr, mc in get_legal_moves_for_piece(r, c):
        center = (
            mc * CELL_SIZE + CELL_SIZE // 2,
            mr * CELL_SIZE + CELL_SIZE // 2,
        )

        if board[mr][mc] is None:
            pygame.draw.circle(screen, MOVE_COLOR, center, 12, 3)
        else:
            pygame.draw.circle(screen, CAPTURE_COLOR, center, 18, 4)
            pygame.draw.rect(
                screen,
                CAPTURE_COLOR,
                (
                    mc * CELL_SIZE + 6,
                    mr * CELL_SIZE + 6,
                    CELL_SIZE - 12,
                    CELL_SIZE - 12,
                ),
                3,
            )


def draw_check_marker():
    if winner:
        return

    ticks = pygame.time.get_ticks()
    visible = (ticks // 400) % 2 == 0

    if not visible:
        return

    for color in [RED, BLUE]:
        if is_in_check(color):
            king_pos = find_king(color)

            if king_pos:
                r, c = king_pos

                pygame.draw.rect(
                    screen,
                    CHECK_COLOR,
                    (
                        c * CELL_SIZE + 3,
                        r * CELL_SIZE + 3,
                        CELL_SIZE - 6,
                        CELL_SIZE - 6,
                    ),
                    5,
                )

                pygame.draw.circle(
                    screen,
                    CHECK_COLOR,
                    (
                        c * CELL_SIZE + CELL_SIZE // 2,
                        r * CELL_SIZE + CELL_SIZE // 2,
                    ),
                    31,
                    4,
                )


def draw_side_panel():
    panel_x = BOARD_WIDTH
    left = panel_x + 15

    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        (panel_x, 0, SIDE_PANEL_WIDTH, HEIGHT),
    )
    pygame.draw.line(
        screen,
        LINE_COLOR,
        (panel_x, 0),
        (panel_x, HEIGHT),
        3,
    )

    title_font = pygame.font.SysFont("arial", 24, bold=True)
    small_font = pygame.font.SysFont("arial", 17)
    history_font = pygame.font.SysFont("arial", 15)

    y = 18

    title = title_font.render("Punktacja", True, LINE_COLOR)
    screen.blit(title, (left, y))
    y += 30

    blue_score = calculate_points(BLUE)
    red_score = calculate_points(RED)

    screen.blit(
        small_font.render(f"Gracz: {blue_score} pkt", True, LINE_COLOR),
        (left, y),
    )
    screen.blit(
        small_font.render(f"Komputer: {red_score} pkt", True, LINE_COLOR),
        (left, y + 22),
    )
    y += 52

    screen.blit(
        small_font.render(
            f"Poziom AI: {DIFFICULTY_LABELS[ai_difficulty]}",
            True,
            LINE_COLOR,
        ),
        (left, y),
    )
    y += 28

    timer_color = (170, 0, 0) if player_time_remaining <= 60 else LINE_COLOR
    timer_font = pygame.font.SysFont("arial", 22, bold=True)
    screen.blit(
        timer_font.render(
            f"Czas gracza: {format_time(player_time_remaining)}",
            True,
            timer_color,
        ),
        (left, y),
    )
    y += 42

    title = title_font.render("Historia ruchów", True, LINE_COLOR)
    screen.blit(title, (left, y))
    y += 32


    history_line_height = 19
    max_history_lines = 9

    if move_log:
        for move in move_log[-max_history_lines:]:

            displayed = move
            max_width = SIDE_PANEL_WIDTH - 30
            while (
                history_font.size(displayed)[0] > max_width
                and len(displayed) > 4
            ):
                displayed = displayed[:-4].rstrip() + "..."

            image = history_font.render(displayed, True, LINE_COLOR)
            screen.blit(image, (left, y))
            y += history_line_height
    else:
        screen.blit(
            history_font.render("Brak ruchów", True, LINE_COLOR),
            (left, y),
        )
        y += history_line_height


    y = 405

    title = title_font.render("Zbite przez Gracza", True, LINE_COLOR)
    screen.blit(title, (left, y))
    y += 29

    def draw_captured_compact(captured, y_pos):
        if not captured:
            screen.blit(
                small_font.render("Brak", True, LINE_COLOR),
                (left, y_pos),
            )
            return y_pos + 21


        names = [format_piece_name(piece) for piece in captured]
        counts = {}
        order = []
        for name in names:
            if name not in counts:
                counts[name] = 0
                order.append(name)
            counts[name] += 1

        parts = [
            f"{name} x{counts[name]}" if counts[name] > 1 else name
            for name in order
        ]

        lines = []
        current = ""
        max_width = SIDE_PANEL_WIDTH - 30

        for part in parts:
            candidate = part if not current else current + ", " + part
            if small_font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = part
        if current:
            lines.append(current)


        if len(lines) > 2:
            lines = lines[:2]
            if small_font.size(lines[-1] + ", ...")[0] <= max_width:
                lines[-1] += ", ..."

        for line in lines:
            screen.blit(
                small_font.render(line, True, LINE_COLOR),
                (left, y_pos),
            )
            y_pos += 21

        return y_pos

    y = draw_captured_compact(captured_by_blue, y)
    y += 14

    title = title_font.render("Zbite przez Komputer", True, LINE_COLOR)
    screen.blit(title, (left, y))
    y += 29

    draw_captured_compact(captured_by_red, y)


    y = HEIGHT - 132

    title = title_font.render("Sterowanie", True, LINE_COLOR)
    screen.blit(title, (left, y))
    y += 31

    controls = [
        "R - restart gry",
        "U - cofnij turę",
        "P - pas",
        "Klik - wybór/ruch",
    ]

    for i, control_text in enumerate(controls):
        image = small_font.render(control_text, True, LINE_COLOR)
        screen.blit(image, (left, y + i * 23))


def draw_status():
    if winner:
        if game_end_reason == "time":
            blue_score = calculate_points(BLUE)
            red_score = calculate_points(RED)

            if winner == BLUE:
                text = (
                    f"KONIEC CZASU - wygrywa Gracz "
                    f"({blue_score} : {red_score})"
                )
            elif winner == RED:
                text = (
                    f"KONIEC CZASU - wygrywa Komputer "
                    f"({blue_score} : {red_score})"
                )
            else:
                text = (
                    f"KONIEC CZASU - remis "
                    f"({blue_score} : {red_score})"
                )
        elif game_end_reason == "bikjang":
            text = "REMIS - BIKJANG"
        elif game_end_reason == "double_pass":
            text = "REMIS - dwa kolejne pasy"
        else:
            if winner == BLUE:
                text = "MAT! Wygrał NIEBIESKI!"
            elif winner == RED:
                text = "MAT! Wygrał CZERWONY!"
            else:
                text = "REMIS!"
    elif kings_facing():
        text = (
            "BIKJANG! P - remis lub wykonaj ruch przerywający"
            if turn == BLUE
            else "BIKJANG - ruch komputera..."
        )
    elif is_in_check(turn):
        text = (
            "SZACH! Twoja tura"
            if turn == BLUE
            else "SZACH! Ruch komputera"
        )
    elif turn == BLUE and not get_all_legal_moves(BLUE):
        text = "Brak legalnych ruchów - naciśnij P, aby spasować"
    else:
        text = (
            "Twoja tura: NIEBIESKI"
            if turn == BLUE
            else "Ruch komputera..."
        )

    image = font.render(text, True, LINE_COLOR)
    screen.blit(image, (10, HEIGHT - 35))



def get_game_over_buttons():
    panel_height = 390
    panel_y = (HEIGHT - panel_height) // 2
    restart_button = pygame.Rect(WIDTH // 2 - 235, panel_y + 285, 220, 58)
    menu_button = pygame.Rect(WIDTH // 2 + 15, panel_y + 285, 220, 58)
    return restart_button, menu_button


def draw_game_over_screen():

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    panel_width = 560
    panel_height = 390
    panel_x = (WIDTH - panel_width) // 2
    panel_y = (HEIGHT - panel_height) // 2
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    pygame.draw.rect(screen, (235, 205, 145), panel_rect, border_radius=16)
    pygame.draw.rect(screen, (85, 55, 20), panel_rect, 4, border_radius=16)

    end_title_font = pygame.font.SysFont("arial", 42, bold=True)
    result_font = pygame.font.SysFont("arial", 27, bold=True)
    info_font = pygame.font.SysFont("arial", 21)

    if game_end_reason == "time":
        title_text = "KONIEC CZASU"
    elif game_end_reason == "checkmate":
        title_text = "MAT"
    elif game_end_reason == "bikjang":
        title_text = "BIKJANG"
    elif game_end_reason == "double_pass":
        title_text = "REMIS"
    else:
        title_text = "KONIEC GRY"

    if winner == BLUE:
        result_text = "ZWYCIĘSTWO GRACZA"
    elif winner == RED:
        result_text = "ZWYCIĘSTWO KOMPUTERA"
    else:
        result_text = "REMIS"

    title_img = end_title_font.render(title_text, True, (55, 35, 15))
    result_img = result_font.render(result_text, True, (75, 45, 15))

    screen.blit(title_img, title_img.get_rect(center=(WIDTH // 2, panel_y + 65)))
    screen.blit(result_img, result_img.get_rect(center=(WIDTH // 2, panel_y + 125)))

    if game_end_reason == "time":
        blue_score = calculate_points(BLUE)
        red_score = calculate_points(RED)
        reason_text = "Partia została rozstrzygnięta na podstawie punktów."
        score_text = f"Gracz: {blue_score} pkt     Komputer: {red_score} pkt"
    elif game_end_reason == "checkmate":
        reason_text = "Partia została zakończona matem."
        score_text = (
            f"Punkty końcowe: {calculate_points(BLUE)} : "
            f"{calculate_points(RED)}"
        )
    elif game_end_reason == "bikjang":
        reason_text = "Remis został przyjęty w pozycji bikjang."
        score_text = (
            f"Punkty końcowe: {calculate_points(BLUE)} : "
            f"{calculate_points(RED)}"
        )
    elif game_end_reason == "double_pass":
        reason_text = "Obie strony spasowały w kolejnych turach."
        score_text = (
            f"Punkty końcowe: {calculate_points(BLUE)} : "
            f"{calculate_points(RED)}"
        )
    else:
        reason_text = "Partia została zakończona."
        score_text = (
            f"Punkty końcowe: {calculate_points(BLUE)} : "
            f"{calculate_points(RED)}"
        )

    reason_img = info_font.render(reason_text, True, (65, 45, 30))
    score_img = info_font.render(score_text, True, (65, 45, 30))
    screen.blit(reason_img, reason_img.get_rect(center=(WIDTH // 2, panel_y + 180)))
    screen.blit(score_img, score_img.get_rect(center=(WIDTH // 2, panel_y + 215)))

    mouse_pos = pygame.mouse.get_pos()
    restart_button, menu_button = get_game_over_buttons()

    draw_button("ZAGRAJ PONOWNIE", restart_button, mouse_pos)
    draw_button("MENU GŁÓWNE", menu_button, mouse_pos)

    return restart_button, menu_button



# Menu/ reset gry


def restart_game():
    global board, turn, selected, winner
    global move_history, move_log
    global captured_by_blue, captured_by_red
    global player_time_remaining, game_end_reason, consecutive_passes

    board = copy.deepcopy(STARTING_POSITIONS)
    turn = BLUE
    selected = None
    winner = None
    move_history = []
    move_log = []
    captured_by_blue = []
    captured_by_red = []
    player_time_remaining = float(PLAYER_TIME_LIMITS[ai_difficulty])
    game_end_reason = None
    consecutive_passes = 0


def draw_button(text, rect, mouse_pos, selected_button=False):
    hovered = rect.collidepoint(mouse_pos)

    # Ciemne, półprzezroczyste przyciski nawiązujące do stylu grafiki.
    button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)

    if selected_button:
        fill_color = (120, 35, 25, 235)
        border_color = (225, 175, 80)
        text_color = (255, 241, 214)
        border_width = 3
    elif hovered:
        fill_color = (95, 55, 30, 235)
        border_color = (220, 175, 95)
        text_color = (255, 245, 220)
        border_width = 3
    else:
        fill_color = (20, 17, 14, 220)
        border_color = (150, 115, 65)
        text_color = (240, 225, 195)
        border_width = 2

    pygame.draw.rect(
        button_surface,
        fill_color,
        button_surface.get_rect(),
        border_radius=8,
    )
    pygame.draw.rect(
        button_surface,
        border_color,
        button_surface.get_rect(),
        border_width,
        border_radius=8,
    )

    screen.blit(button_surface, rect.topleft)

    button_font = pygame.font.SysFont("georgia", 21, bold=True)
    image = button_font.render(text, True, text_color)
    screen.blit(image, image.get_rect(center=rect.center))


def draw_menu_background(strength=145):
    if MENU_BACKGROUND is not None:
        screen.blit(MENU_BACKGROUND, (0, 0))
    else:

        screen.fill((90, 62, 35))


    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((10, 8, 6, strength))
    screen.blit(shade, (0, 0))


def draw_menu_card(rect, alpha=205):
    card = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(
        card,
        (15, 12, 10, alpha),
        card.get_rect(),
        border_radius=16,
    )
    pygame.draw.rect(
        card,
        (176, 132, 70, 235),
        card.get_rect(),
        2,
        border_radius=16,
    )
    pygame.draw.rect(
        card,
        (92, 65, 38, 200),
        card.get_rect().inflate(-12, -12),
        1,
        border_radius=12,
    )
    screen.blit(card, rect.topleft)


def rules_screen():
    title_font = pygame.font.SysFont("georgia", 34, bold=True)
    heading_font = pygame.font.SysFont("georgia", 20, bold=True)
    small_font = pygame.font.SysFont("arial", 17)

    back_button = pygame.Rect(WIDTH // 2 - 110, HEIGHT - 82, 220, 46)
    card_rect = pygame.Rect(85, 48, WIDTH - 170, HEIGHT - 96)

    rules = [
        ("Cel gry", [
            "Doprowadź do mata generała przeciwnika.",
            "Generał nie jest zbijany bezpośrednio.",
        ]),
        ("Sterowanie", [
            "Kliknij własną figurę, a następnie wybrane pole.",
            "Niebieskie znaczniki pokazują legalne ruchy.",
            "Czerwone znaczniki oznaczają możliwe bicia.",
            "U - cofnij ostatnią pełną turę, R - restart gry.",
            "P - pas (niedostępny podczas szacha).",
            "ESC - powrót do menu głównego.",
        ]),
        ("Rozgrywka", [
            "Gracz prowadzi figury niebieskie.",
            "Komputer prowadzi figury czerwone.",
            "Poziom trudności AI wybierany jest w menu.",
            "Bikjang pozwala stronie na ruchu przyjąć remis przez pas.",
            "Dwa kolejne pasy również kończą partię remisem.",
        ]),
    ]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        draw_menu_background(strength=175)
        draw_menu_card(card_rect, alpha=220)

        title = title_font.render("ZASADY GRY", True, (246, 228, 194))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 88)))

        pygame.draw.line(
            screen,
            (165, 45, 35),
            (WIDTH // 2 - 100, 113),
            (WIDTH // 2 + 100, 113),
            3,
        )

        y = 135

        for heading, lines in rules:
            heading_image = heading_font.render(
                heading,
                True,
                (222, 177, 99),
            )
            screen.blit(heading_image, (120, y))
            y += 31

            for line in lines:
                line_image = small_font.render(
                    "• " + line,
                    True,
                    (238, 226, 205),
                )
                screen.blit(line_image, (140, y))
                y += 26

            y += 12

        draw_button("POWRÓT", back_button, mouse_pos)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return



def draw_menu_hotspot(rect, mouse_pos, selected=False):

    if selected:
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((145, 45, 30, 55))
        screen.blit(overlay, rect.topleft)
        pygame.draw.rect(screen, (225, 178, 103), rect, 3, border_radius=5)
    elif rect.collidepoint(mouse_pos):
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((255, 225, 165, 25))
        screen.blit(overlay, rect.topleft)
        pygame.draw.rect(screen, (220, 175, 105), rect, 2, border_radius=5)


def author_screen():
    title_font = pygame.font.SysFont("georgia", 32, bold=True)
    text_font = pygame.font.SysFont("arial", 18)

    card = pygame.Rect(150, 135, 560, 390)
    back_button = pygame.Rect(310, 445, 240, 52)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        draw_menu_background(strength=150)
        draw_menu_card(card, alpha=225)

        title = title_font.render("O PROJEKCIE", True, (246, 228, 194))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 180)))

        lines = [
            "Janggi - Koreańskie szachy",
            "Aplikacja stworzona jako projekt pracy licencjackiej.",
            "Rozgrywka: gracz kontra przeciwnik komputerowy.",
            "Technologie: Python i Pygame.",
        ]

        y = 245
        for line in lines:
            image = text_font.render(line, True, (235, 220, 195))
            screen.blit(image, image.get_rect(center=(WIDTH // 2, y)))
            y += 38

        draw_button("POWRÓT", back_button, mouse_pos)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return



def pause_menu():

    title_font = pygame.font.SysFont("georgia", 38, bold=True)
    info_font = pygame.font.SysFont("arial", 18)

    panel_width = 500
    panel_height = 330
    panel_x = (WIDTH - panel_width) // 2
    panel_y = (HEIGHT - panel_height) // 2
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    resume_button = pygame.Rect(
        panel_x + 80,
        panel_y + 150,
        panel_width - 160,
        58,
    )
    menu_button = pygame.Rect(
        panel_x + 80,
        panel_y + 225,
        panel_width - 160,
        58,
    )

    while True:
        mouse_pos = pygame.mouse.get_pos()


        draw_board()
        draw_pieces()
        draw_highlights()
        draw_check_marker()
        draw_side_panel()
        draw_status()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            screen,
            (235, 205, 145),
            panel_rect,
            border_radius=16,
        )
        pygame.draw.rect(
            screen,
            (85, 55, 20),
            panel_rect,
            4,
            border_radius=16,
        )

        title = title_font.render("PAUZA", True, (55, 35, 15))
        screen.blit(
            title,
            title.get_rect(center=(WIDTH // 2, panel_y + 65)),
        )

        info = info_font.render(
            "Rozgrywka została wstrzymana.",
            True,
            (65, 45, 30),
        )
        screen.blit(
            info,
            info.get_rect(center=(WIDTH // 2, panel_y + 110)),
        )

        draw_button("WZNÓW GRĘ", resume_button, mouse_pos)
        draw_button("WYJDŹ DO MENU GŁÓWNEGO", menu_button, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"

            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_button.collidepoint(event.pos):
                    return "resume"

                if menu_button.collidepoint(event.pos):
                    return "menu"


def main_menu():
    global ai_difficulty


    start_button = pygame.Rect(280, 239, 301, 59)
    rules_button = pygame.Rect(288, 310, 285, 48)
    author_button = pygame.Rect(288, 362, 285, 50)
    quit_button = pygame.Rect(288, 416, 285, 50)

    difficulty_buttons = {
        "easy": pygame.Rect(646, 276, 208, 51),
        "medium": pygame.Rect(646, 334, 208, 51),
        "hard": pygame.Rect(646, 390, 208, 51),
    }

    while True:
        mouse_pos = pygame.mouse.get_pos()

        if MENU_BACKGROUND is not None:
            screen.blit(MENU_BACKGROUND, (0, 0))
        else:
            draw_menu_background(strength=0)


        for rect in (
            start_button,
            rules_button,
            author_button,
            quit_button,
        ):
            draw_menu_hotspot(rect, mouse_pos)

        for difficulty, rect in difficulty_buttons.items():
            draw_menu_hotspot(
                rect,
                mouse_pos,
                selected=(difficulty == ai_difficulty),
            )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                for difficulty, rect in difficulty_buttons.items():
                    if rect.collidepoint(event.pos):
                        ai_difficulty = difficulty

                if start_button.collidepoint(event.pos):
                    restart_game()
                    return

                if rules_button.collidepoint(event.pos):
                    rules_screen()

                if author_button.collidepoint(event.pos):
                    author_screen()

                if quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()



# Główna pętla


def main():
    global selected, turn
    global player_time_remaining

    clock = pygame.time.Clock()
    running = True
    ai_delay = 0

    while running:
        dt = clock.tick(60) / 1000.0


        if turn == BLUE and winner is None:
            player_time_remaining -= dt

            if player_time_remaining <= 0:
                player_time_remaining = 0
                resolve_game_on_time()

        if turn == RED and winner is None:
            ai_delay += 1

            if ai_delay > 25:
                ai_move()


                clock.tick(60)
                ai_delay = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    restart_game()

                if event.key == pygame.K_u:
                    undo_last_turn()

                if (
                    event.key == pygame.K_p
                    and turn == BLUE
                    and winner is None
                ):
                    pass_turn(BLUE)

                if event.key == pygame.K_ESCAPE and winner is None:
                    pause_action = pause_menu()


                    clock.tick(60)

                    if pause_action == "menu":
                        main_menu()
                        ai_delay = 0
                        clock.tick(60)

            if event.type == pygame.MOUSEBUTTONDOWN and winner is not None:
                restart_button, menu_button = get_game_over_buttons()

                if restart_button.collidepoint(event.pos):
                    restart_game()
                    ai_delay = 0
                    continue

                if menu_button.collidepoint(event.pos):
                    main_menu()
                    ai_delay = 0
                    continue

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and turn == BLUE
                and winner is None
            ):
                x, y = event.pos
                col = x // CELL_SIZE
                row = y // CELL_SIZE

                if not inside(row, col):
                    continue

                clicked_piece = board[row][col]

                if selected is None:
                    if clicked_piece and color_of(clicked_piece) == BLUE:
                        selected = (row, col)
                else:
                    sr, sc = selected
                    legal_moves = get_legal_moves_for_piece(sr, sc)

                    if (row, col) in legal_moves:
                        make_move(sr, sc, row, col)
                        selected = None

                        if winner is None:
                            turn = RED
                    else:
                        if clicked_piece and color_of(clicked_piece) == BLUE:
                            selected = (row, col)
                        else:
                            selected = None

        draw_board()
        draw_highlights()
        draw_check_marker()
        draw_pieces()
        draw_status()
        draw_side_panel()

        if winner is not None:
            draw_game_over_screen()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main_menu()
    main()


