import serial
import pygame
import sys
import math

# --- CONFIGURATION ---
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

# --- INITIALIZE PYGAME & FONTS ---
pygame.init()
pygame.font.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced Flight Deck Display")
clock = pygame.time.Clock()

font_large = pygame.font.SysFont("Arial", 36, bold=True)
font_small = pygame.font.SysFont("Arial", 16, bold=True)

# Colors
SKY_BLUE = (35, 136, 222)
GROUND_BROWN = (130, 70, 20)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)
BLACK = (15, 15, 15)
RED = (230, 30, 30)

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"Connected to Pico on {SERIAL_PORT}")
except Exception as e:
    print(f"Error connecting to port {SERIAL_PORT}. Ensure Thonny is STOPPED!")
    sys.exit()

pitch, roll, alarm = 0.0, 0.0, 0
flash_timer = 0

while True:
    flash_timer += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            ser.close()
            pygame.quit()
            sys.exit()

    # --- READ DATA ---
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').strip()
            p_str, r_str, a_str = line.split(',')
            pitch = float(p_str)
            roll = float(r_str)
            alarm = int(a_str)
        except:
            pass

    screen.fill(BLACK)

    # --- 1. DRAW THE ROTATING HORIZON BACKGROUND ---
    horizon_surf = pygame.Surface((WIDTH * 2, HEIGHT * 2))
    horizon_surf.fill(SKY_BLUE)
    
    # Draw Ground
    pygame.draw.rect(horizon_surf, GROUND_BROWN, (0, HEIGHT, WIDTH * 2, HEIGHT * 2))
    # Draw Main Horizon White Line
    pygame.draw.line(horizon_surf, WHITE, (0, HEIGHT), (WIDTH * 2, HEIGHT), 6)

    # Draw Pitch Ladder Ticks (Every 10 degrees)
    for deg in [-30, -20, -10, 10, 20, 30]:
        y_pos = HEIGHT - (deg * 5) 
        pygame.draw.line(horizon_surf, WHITE, (WIDTH - 40, y_pos), (WIDTH + 40, y_pos), 3)
        txt = font_small.render(str(abs(deg)), True, WHITE)
        horizon_surf.blit(txt, (WIDTH + 50, y_pos - 8))
        horizon_surf.blit(txt, (WIDTH - 70, y_pos - 8))

    # Apply Roll Rotation
    rotated_surf = pygame.transform.rotate(horizon_surf, -roll)
    
    # Apply Inverted Pitch Direction (-pitch)
    pitch_pixels = -pitch * 5 
    
    # Draw horizon onto main screen
    surf_rect = rotated_surf.get_rect(center=(WIDTH // 2, (HEIGHT // 2) + pitch_pixels))
    
    # --- 2. THE COCKPIT GAUGE MASK ---
    display_circle = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(display_circle, (255, 255, 255, 255), (WIDTH // 2, HEIGHT // 2), 220)
    
    horizon_container = pygame.Surface((WIDTH, HEIGHT))
    horizon_container.blit(rotated_surf, surf_rect)
    horizon_container.blit(display_circle, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    
    screen.blit(horizon_container, (0, 0))

    # --- 3. DRAW STATIC GAUGE BORDERS & ROLL DEGREE SCALE ---
    # Thick outer instrument ring bezel
    pygame.draw.circle(screen, (60, 60, 60), (WIDTH // 2, HEIGHT // 2), 222, 6)

    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # Standard aviation bank angle marks (0, 10, 20, 30, 45, 60 degrees)
    bank_angles = [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]
    
    for angle in bank_angles:
        # Convert angle to radians (subtract 90 to orient 0 degrees straight UP)
        rad = math.radians(angle - 90)
        
        # Make major markings (0, 30, 60) longer than intermediate ones
        tick_len = 16 if angle in [-60, -30, 0, 30, 60] else 9
        
        # Calculate inner and outer points for the tick lines
        x1 = center_x + (220 - tick_len) * math.cos(rad)
        y1 = center_y + (220 - tick_len) * math.sin(rad)
        x2 = center_x + 218 * math.cos(rad)
        y2 = center_y + 218 * math.sin(rad)
        
        pygame.draw.line(screen, WHITE, (x1, y1), (x2, y2), 3)

    # Draw the Dynamic Sky Pointer (The triangle indicating current bank angle)
    # It rotates smoothly based on the current roll value
    pointer_rad = math.radians(-roll - 90)
    
    # Tip of the triangle pointing outward toward the ticks
    p_tip_x = center_x + 205 * math.cos(pointer_rad)
    p_tip_y = center_y + 205 * math.sin(pointer_rad)
    
    # Left and right base corners of the triangle
    p_base1_x = center_x + 190 * math.cos(pointer_rad - 0.04)
    p_base1_y = center_y + 190 * math.sin(pointer_rad - 0.04)
    p_base2_x = center_x + 190 * math.cos(pointer_rad + 0.04)
    p_base2_y = center_y + 190 * math.sin(pointer_rad + 0.04)
    
    pygame.draw.polygon(screen, WHITE, [(p_tip_x, p_tip_y), (p_base1_x, p_base1_y), (p_base2_x, p_base2_y)])
    
    # --- 4. DRAW FIXED COCKPIT WINGS ---
    pygame.draw.line(screen, YELLOW, (WIDTH // 2 - 90, HEIGHT // 2), (WIDTH // 2 - 30, HEIGHT // 2), 6)
    pygame.draw.line(screen, YELLOW, (WIDTH // 2 - 30, HEIGHT // 2), (WIDTH // 2 - 30, HEIGHT // 2 + 15), 6)
    pygame.draw.line(screen, YELLOW, (WIDTH // 2 + 30, HEIGHT // 2), (WIDTH // 2 + 80, HEIGHT // 2), 6)
    pygame.draw.line(screen, YELLOW, (WIDTH // 2 + 30, HEIGHT // 2), (WIDTH // 2 + 30, HEIGHT // 2 + 15), 6)
    pygame.draw.circle(screen, BLACK, (WIDTH // 2, HEIGHT // 2), 7)
    pygame.draw.circle(screen, YELLOW, (WIDTH // 2, HEIGHT // 2), 4)

    # --- 5. DYNAMIC VISUAL ALARM HUD OVERLAY ---
    if alarm == 1:
        # Step-by-step logic to determine the exact hazard message
        if abs(roll) > 45.0:
            warning_msg = "BANK ANGLE! BANK ANGLE!"
        elif pitch > 30.0:
            warning_msg = "PULL UP! PULL UP!"
        elif pitch < -30.0:
            warning_msg = "PULL DOWN! PULL DOWN!"
        else:
            warning_msg = "OVERSPEED / UNSTABLE"

        # Blink every 15 frames
        if (flash_timer // 15) % 2 == 0:
            # Translucent alert banner at the top
            alarm_box = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
            alarm_box.fill((230, 30, 30, 200)) 
            screen.blit(alarm_box, (0, 40))
            
            # Render our custom contextual text
            warn_text = font_large.render(warning_msg, True, WHITE)
            text_rect = warn_text.get_rect(center=(WIDTH // 2, 70))
            screen.blit(warn_text, text_rect)

    # UI Status Readouts
    pitch_txt = font_small.render(f"PITCH: {-pitch:+.1f}°", True, WHITE)
    roll_txt = font_small.render(f"ROLL: {roll:+.1f}°", True, WHITE)
    screen.blit(pitch_txt, (30, 30))
    screen.blit(roll_txt, (WIDTH - 130, 30))

    pygame.display.flip()
    clock.tick(60)