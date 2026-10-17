from machine import Pin, SPI, ADC
import time
import random
import max7219
import tm1637

# ================= DISPLAY SETUP =================
spi = SPI(1, baudrate=10000000, sck=Pin(14), mosi=Pin(11))
cs = Pin(13, Pin.OUT)
d = max7219.Matrix8x8(spi, cs, 4)
d.brightness(2)

# ================= HW-069 SCOREBOARD SETUP =================
tm = tm1637.TM1637(clk=Pin(2), dio=Pin(3))
tm.brightness(2)
score = 0
tm.number(score)

# ================= HARDWARE SETUP =================
vrx = ADC(27) 
vry = ADC(26) 
btn = Pin(22, Pin.IN, Pin.PULL_UP)

buzzer = Pin(0, Pin.OUT)
buzzer.value(0)

W, H = 8, 32 # Game board setup (8 columns x 32 rows)
board = [[0]*W for _ in range(H)]

# ================= THE 7 CLASSIC SHAPES =================
SHAPES = [
    [(0,0), (1,0), (2,0), (3,0)],  # I
    [(0,0), (1,0), (0,1), (1,1)],  # O
    [(-1,0), (0,0), (1,0), (0,1)], # T
    [(0,0), (1,0), (2,0), (0,1)],  # L
    [(0,0), (1,0), (2,0), (2,1)],  # J
    [(0,1), (1,1), (1,0), (2,0)],  # S 
    [(0,0), (1,0), (1,1), (2,1)],  # Z
]

# ================= SOUND EFFECTS =================
def play_sound(duration, count=1, delay=0.05):
    for _ in range(count):
        buzzer.value(1)
        time.sleep(duration)
        buzzer.value(0)
        if count > 1:
            time.sleep(delay)

def new_piece():
    shape = random.choice(SHAPES)
    return {"x": 3, "y": 5, "shape": shape}

# Initialize game pieces
piece = new_piece()
next_piece = new_piece()
fall_speed = 400

def collide(px, py, shape):
    for x, y in shape:
        nx, ny = px + x, py + y
        if nx < 0 or nx >= W or ny >= H: return True
        if ny < 5: return True 
        if board[ny][nx]: return True
    return False

def lock():
    global piece, next_piece, fall_speed, board, score
    # Stamp current piece onto the play board
    for x, y in piece["shape"]:
        if piece["y"]+y >= 0:
            board[piece["y"]+y][piece["x"]+x] = 1
    
    # Scan active rows (5 to 31) for complete lines
    full_rows = [y for y in range(5, H) if sum(board[y]) == W]
    
    if full_rows:
        # ANIMATION: Blink full lines 2 times
        for _ in range(2):
            for y in full_rows: board[y] = [0]*W
            draw()
            time.sleep(0.12)
            for y in full_rows: board[y] = [1]*W
            draw()
            time.sleep(0.12)
            
        # Shift remaining rows down
        new_board = [row for row in board if sum(row) < W]
        while len(new_board) < H:
            new_board.insert(0, [0]*W)
        board = new_board
        
        play_sound(duration=0.08, count=2, delay=0.04)
        
        # Arcade Score System: More rows cleared at once = way more points!
        points_table = [0, 100, 300, 600, 1200]
        cleared_count = min(len(full_rows), 4)
        score += points_table[cleared_count]
        tm.number(score)  # Instantly update HW-069 screen
        
        # Speed progression (15ms faster per row)
        fall_speed = max(100, fall_speed - (15 * len(full_rows)))
        
    # Cycle the preview piece into the active game
    piece = next_piece
    next_piece = new_piece()
    
    # Game over detection
    if collide(piece["x"], piece["y"], piece["shape"]):
        play_sound(duration=0.8, count=1)
        for i in range(H): board[i] = [0]*W
        fall_speed = 400
        score = 0
        tm.number(score)  # Reset scoreboard
        piece = new_piece()
        next_piece = new_piece()
        play_sound(duration=0.06, count=3, delay=0.06)

def draw():
    d.fill(0)
    
    # 1. DYNAMICALLY CENTERED PREVIEW WINDOW
    shape_coords = next_piece["shape"]
    min_x = min(px for px, py in shape_coords)
    max_x = max(px for px, py in shape_coords)
    min_y = min(py for px, py in shape_coords)
    max_y = max(py for px, py in shape_coords)
    
    shape_w = max_x - min_x + 1
    shape_h = max_y - min_y + 1
    
    offset_x = (8 - shape_w) // 2
    offset_y = (4 - shape_h) // 2
    
    for px, py in shape_coords:
        d.pixel(offset_y + (py - min_y), offset_x + (px - min_x), 1)
        
    # 2. SEPARATOR DIVIDER LINE (Row 4)
    for x in range(W):
        d.pixel(4, x, 1)

    # 3. STATIC OCCUPIED BLOCKS (Rows 5-31)
    for y in range(5, H):
        for x in range(W):
            if board[y][x]: d.pixel(y, x, 1)

    # 4. ACTIVE FALLING PIECE
    for px, py in piece["shape"]:
        lx, ly = piece["x"] + px, piece["y"] + py
        if 5 <= ly < H and 0 <= lx < W: 
            d.pixel(ly, lx, 1)
            
    d.show()

# Play boot sound
play_sound(duration=0.06, count=3, delay=0.06)

current_intent = "CENTER"
last_fall = time.ticks_ms()

# ================= MAIN GAME LOOP =================
while True:
    vrx.read_u16()
    xval = vrx.read_u16()
    vry.read_u16()
    yval = vry.read_u16()
    
    # Smart Intent Latch
    if 40000 < xval < 56000 and 40000 < yval < 56000:
        current_intent = "CENTER"
    elif not (xval > 61000 and yval > 61000):
        if xval < 5000:    current_intent = "UP"
        elif xval > 56000: current_intent = "DOWN"
        elif yval < 5000:  current_intent = "LEFT"   
        elif yval > 56000: current_intent = "RIGHT"  

    # Execute Left/Right shift mechanics
    if current_intent == "LEFT":
        if not collide(piece["x"]-1, piece["y"], piece["shape"]):
            piece["x"] -= 1
            time.sleep(0.12)
    elif current_intent == "RIGHT":
        if not collide(piece["x"]+1, piece["y"], piece["shape"]):
            piece["x"] += 1
            time.sleep(0.12)

    # Rotational input trigger
    if btn.value() == 0:
        rotated = [(y, -x) for x, y in piece["shape"]]
        if not collide(piece["x"], piece["y"], rotated):
            piece["shape"] = rotated
        time.sleep(0.2)

    # Assign game drop speed based on down-press status
    current_speed = 40 if current_intent == "DOWN" else fall_speed

    # Gravity timing tick
    if time.ticks_diff(time.ticks_ms(), last_fall) > current_speed:
        if not collide(piece["x"], piece["y"]+1, piece["shape"]):
            piece["y"] += 1
        else:
            lock()
        last_fall = time.ticks_ms()

    draw()