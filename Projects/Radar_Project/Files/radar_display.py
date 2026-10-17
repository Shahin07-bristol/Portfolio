import pygame
import serial
import math
import sys

PICO_PORT = 'COM4'
BAUD_RATE = 115200

# Initialize Pygame Display
pygame.init()
WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced Radar - Direction Corrected")
clock = pygame.time.Clock()

# Theme Colors (RGB)
BG_COLOR = (5, 8, 5)
GRID_COLOR = (0, 60, 0)
SWEEP_LINE_COLOR = (100, 255, 100)
TEXT_COLOR = (0, 200, 0)

# Radar geometry configuration
CENTER = (WIDTH // 2, HEIGHT - 40)
MAX_DISTANCE_CM = 50.0  
MAX_RADIUS = 400        

# Connect to the Pico Serial Port
try:
    ser = serial.Serial(PICO_PORT, BAUD_RATE, timeout=0.1)
    print(f"Successfully connected to Pico on {PICO_PORT}")
except Exception as e:
    print(f"Error: Could not connect to {PICO_PORT}. Did you close Thonny?")
    print(e)
    sys.exit()

# Tracking radar memory data for all 180 degrees
radar_sectors = {angle: {"distance": 999.0, "alpha": 0.0} for angle in range(0, 182, 2)}

current_angle = 0
current_dist = 0.0
font = pygame.font.SysFont("monospace", 16)

# --- MAIN APP LOOP ---
running = True
while running:
    screen.fill(BG_COLOR)
    
    # 1. Handle Window Exit Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Read live data streaming over USB from the Pico
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').strip()
            if ',' in line:
                parts = line.split(',')
                angle_read = int(parts[0])
                dist_read = float(parts[1])
                
                # Snap the raw angle to our closest 2-degree map slice
                sector_angle = (angle_read // 2) * 2
                if sector_angle in radar_sectors:
                    radar_sectors[sector_angle]["distance"] = dist_read
                    radar_sectors[sector_angle]["alpha"] = 255.0  # Reset to full brightness
                    
                current_angle = angle_read
                current_dist = dist_read
        except:
            pass 

    # 3. Create a Transparent Surface Canvas for the Fading Wedges
    fade_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # 4. Fade all existing sectors slightly every frame (The Trail Decay)
    DECAY_RATE = 2.5  
    for angle in radar_sectors:
        if radar_sectors[angle]["alpha"] > 0:
            radar_sectors[angle]["alpha"] -= DECAY_RATE
            if radar_sectors[angle]["alpha"] < 0:
                radar_sectors[angle]["alpha"] = 0.0

    # 5. Render the Swept Wedges onto the Transparency Canvas
    for angle, data in radar_sectors.items():
        alpha = int(data["alpha"])
        if alpha <= 0:
            continue
            
        dist = data["distance"]
        
        # DIRECTION CORRECTION: Removed '180 -' to invert the drawing direction
        rad1 = math.radians(angle)
        rad2 = math.radians(angle + 2)
        
        # Determine warning alert color profiles based on object proximity
        if dist <= 15.0:
            color = (200, 0, 0, alpha)  # Danger Red
        elif dist <= 35.0:
            color = (200, 150, 0, alpha)  # Warning Yellow
        else:
            color = (0, 120, 0, int(alpha * 0.25))  # Soft Sweeping Green

        # Generate drawing coordinate boundaries for the sector
        if dist <= MAX_DISTANCE_CM and dist >= 2.0:
            pixel_dist = (dist / MAX_DISTANCE_CM) * MAX_RADIUS
            p1 = (CENTER[0] + int(pixel_dist * math.cos(rad1)), CENTER[1] - int(pixel_dist * math.sin(rad1)))
            p2 = (CENTER[0] + int(pixel_dist * math.cos(rad2)), CENTER[1] - int(pixel_dist * math.sin(rad2)))
            pygame.draw.polygon(fade_overlay, color, [CENTER, p1, p2])
            
            # Faint background trail placeholder behind the object
            p1_out = (CENTER[0] + int(MAX_RADIUS * math.cos(rad1)), CENTER[1] - int(MAX_RADIUS * math.sin(rad1)))
            p2_out = (CENTER[0] + int(MAX_RADIUS * math.cos(rad2)), CENTER[1] - int(MAX_RADIUS * math.sin(rad2)))
            pygame.draw.polygon(fade_overlay, (0, 120, 0, int(alpha * 0.08)), [p1, p1_out, p2_out, p2])
        else:
            p1_out = (CENTER[0] + int(MAX_RADIUS * math.cos(rad1)), CENTER[1] - int(MAX_RADIUS * math.sin(rad1)))
            p2_out = (CENTER[0] + int(MAX_RADIUS * math.cos(rad2)), CENTER[1] - int(MAX_RADIUS * math.sin(rad2)))
            pygame.draw.polygon(fade_overlay, color, [CENTER, p1_out, p2_out])

    # Blit the compiled transparency overlay onto the primary screen
    screen.blit(fade_overlay, (0, 0))

    # 6. Draw Fixed Outer Target Grid Rings & Spoke Guidelines
    for r in [100, 200, 300, 400]:
        pygame.draw.circle(screen, GRID_COLOR, CENTER, r, 1)
    for a in [30, 60, 90, 120, 150]:
        rad = math.radians(a)
        end_x = CENTER[0] + int(MAX_RADIUS * math.cos(rad))
        end_y = CENTER[1] - int(MAX_RADIUS * math.sin(rad))
        pygame.draw.line(screen, GRID_COLOR, CENTER, (end_x, end_y), 1)
    pygame.draw.line(screen, GRID_COLOR, (CENTER[0] - MAX_RADIUS, CENTER[1]), (CENTER[0] + MAX_RADIUS, CENTER[1]), 2)

    # 7. Draw the Bright Main Active Sweep Needle Line
    # DIRECTION CORRECTION: Removed '180 -' here to match the new alignment
    sweep_rad = math.radians(current_angle)
    sweep_x = CENTER[0] + int(MAX_RADIUS * math.cos(sweep_rad))
    sweep_y = CENTER[1] - int(MAX_RADIUS * math.sin(sweep_rad))
    pygame.draw.line(screen, SWEEP_LINE_COLOR, CENTER, (sweep_x, sweep_y), 3)

    # 8. Draw Heads-Up Dashboard Display Text
    hud_angle = font.render(f"BEARING: {current_angle}°", True, TEXT_COLOR)
    hud_dist = font.render(f"RANGE: {current_dist:.1f} cm", True, TEXT_COLOR)
    screen.blit(hud_angle, (30, 20))
    screen.blit(hud_dist, (30, 45))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
ser.close()