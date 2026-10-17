from machine import Pin, SPI, ADC
import time
import random
import max7219
import tm1637 # Ensure tm1637.py is saved on your Pico

# ================= DISPLAY SETUP =================
spi = SPI(1, baudrate=10000000, sck=Pin(14), mosi=Pin(11))
cs = Pin(13, Pin.OUT)
d = max7219.Matrix8x8(spi, cs, 4)
d.brightness(2)

# ================= HW-069 SCOREBOARD SETUP =================
tm = tm1637.TM1637(clk=Pin(2), dio=Pin(3))
tm.brightness(2)

# ================= CONTROLS & SOUND =================
btn = Pin(22, Pin.IN, Pin.PULL_UP) # Joystick click to STACK
buzzer = Pin(0, Pin.OUT)
buzzer.value(0)

# Grid size matching your vertical 8x32 matrix setup
W, H = 8, 32
board = [[0]*W for _ in range(H)]

# ================= ADJUSTED ARCADE SPEED TUNING =================
base_speed = 160   # Smooth starting speed for the first 8x8 matrix block
move_speed = base_speed

# ================= GAME VARIABLES =================
current_row = 31   # Starts at the very bottom row
block_width = 3    # Starts 3 blocks wide
block_x = 0        # Initial horizontal position
direction = 1      # 1 = Right, -1 = Left
score = 0          # Tracks successfully stacked rows

def play_sound(freq_type):
    if freq_type == "click":
        buzzer.value(1)
        time.sleep(0.02)
        buzzer.value(0)
    elif freq_type == "chop":
        for _ in range(3):
            buzzer.value(1)
            time.sleep(0.01)
            buzzer.value(0)
            time.sleep(0.01)
    elif freq_type == "gameover":
        for f in range(3):
            buzzer.value(1)
            time.sleep(0.15)
            buzzer.value(0)
            time.sleep(0.05)
    elif freq_type == "win":
        for _ in range(10):
            buzzer.value(1)
            time.sleep(0.03)
            buzzer.value(0)
            time.sleep(0.02)

def reset_game():
    global board, current_row, block_width, block_x, direction, score, move_speed
    board = [[0]*W for _ in range(H)]
    current_row = 31
    block_width = 3
    block_x = random.randint(0, W - block_width)
    direction = 1
    score = 0
    move_speed = base_speed
    tm.number(score)

def draw():
    d.fill(0)
    
    # 1. Draw already stacked blocks on the board
    for y in range(H):
        for x in range(W):
            if board[y][x]:
                d.pixel(y, x, 1)
                
    # 2. Draw the currently moving active row
    for i in range(block_width):
        target_x = block_x + i
        if 0 <= target_x < W:
            d.pixel(current_row, target_x, 1)
            
    d.show()

# Initialize scoreboard
tm.number(score)
last_move = time.ticks_ms()

# ================= MAIN GAME LOOP =================
while True:
    # 1. CHECK THE STACK BUTTON (Action Input)
    if btn.value() == 0:
        if current_row == 31:
            # First row is free! Lock all blocks completely
            for i in range(block_width):
                board[current_row][block_x + i] = 1
            play_sound("click")
            score += 1
            tm.number(score)
            current_row -= 1
        else:
            # Compare current row placement with the row directly underneath it
            survived_blocks = 0
            for i in range(block_width):
                target_x = block_x + i
                if board[current_row + 1][target_x] == 1:
                    board[current_row][target_x] = 1
                    survived_blocks += 1
            
            if survived_blocks == 0:
                # Total miss! Game over animation
                play_sound("gameover")
                for _ in range(3):
                    for i in range(block_width): d.pixel(current_row, block_x + i, 1); d.show()
                    time.sleep(0.15)
                    for i in range(block_width): d.pixel(current_row, block_x + i, 0); d.show()
                    time.sleep(0.15)
                reset_game()
                continue
                
            elif survived_blocks < block_width:
                # Part of the block was chopped off
                play_sound("chop")
                block_width = survived_blocks
            else:
                # Perfect stack alignment
                play_sound("click")
                
            score += 1
            tm.number(score)
            
            # Check for Ultimate Win Condition (Reached the top row)
            if current_row == 0:
                play_sound("win")
                for _ in range(5):
                    d.fill(1); d.show(); time.sleep(0.1)
                    d.fill(0); d.show(); time.sleep(0.1)
                reset_game()
                continue
                
            # Move up to the next level row
            current_row -= 1
            
            # --- MATRIX PANEL DETECTOR ---
            # Calculate which 8x8 panel you are currently climbing (0 to 3)
            # Panel 0 = Bottom (Rows 24-31), Panel 3 = Top (Rows 0-7)
            matrix_panel = 3 - (current_row // 8)
            
            # Speed updates ONLY when crossing to a brand new 8x8 matrix panel!
            # Each panel subtracts 40ms from the original 160ms delay.
            move_speed = max(40, base_speed - (matrix_panel * 40))
            


        # Reset active block properties for the next row level
        block_x = 0
        direction = 1
        time.sleep(0.25) # Debounce delay to prevent double-pressing accidental inputs

    # 2. RUN NON-BLOCKING MOVEMENT ENGINE
    if time.ticks_diff(time.ticks_ms(), last_move) > move_speed:
        next_x = block_x + direction
        if next_x < 0 or next_x > (W - block_width):
            direction *= -1
        block_x += direction
        last_move = time.ticks_ms()

    # 3. REFRESH LED MATRIX WINDOW
    draw()