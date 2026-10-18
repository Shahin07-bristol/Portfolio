import machine
import math
import time
import _thread
from mpu6050 import MPU6050

# --- 1. HARDWARE CONFIGURATION ---
AUDIO_PIN_NUM = 5  
audio_pin = machine.PWM(machine.Pin(AUDIO_PIN_NUM))

# Stable SoftI2C on your specific pins
i2c = machine.SoftI2C(sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)
sensor = MPU6050(i2c)

# --- 2. MULTI-THREADING BACKGROUND VARIABLE CONTROLS ---
# These variables communicate across Core 0 and Core 1
audio_queue = ""       # Stores the filename that needs to be played
audio_is_playing = False  # Tells Core 0 if the speaker is currently busy

# --- 3. HARDWARE AUDIO ENGINE ---
def play_wav(filename):
    """Streams an 8-bit, 11025Hz mono WAV file directly to the speaker"""
    try:
        audio_pin.freq(44100) 
        with open(filename, "rb") as f:
            f.seek(44) # Skip 44-byte WAV metadata header
            chunk_size = 256
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                for sample in data:
                    audio_pin.duty_u16(sample << 8)
                    time.sleep_us(62)
        audio_pin.duty_u16(0) # Cut power to speaker
    except:
        audio_pin.duty_u16(0)

# --- 4. CORE 1: BACKGROUND AUDIO WORKER LOOP ---
def audio_thread_worker():
    """This function runs exclusively on Core 1 to handle blocking audio task"""
    global audio_queue, audio_is_playing
    while True:
        if audio_queue != "":
            audio_is_playing = True
            current_file = audio_queue
            audio_queue = "" # Clear queue so it doesn't loop infinitely
            
            play_wav(current_file) # Runs heavy blocking playback loop here
            
            audio_is_playing = False
        time.sleep(0.05) # Tiny rest for Core 1 stability

# Fire up Core 1 right now before the main flight calculations begin
_thread.start_new_thread(audio_thread_worker, ())

# --- 5. CORE 0: MAIN FLIGHT CALCULATIONS & TELEMETRY STREAM ---
alpha = 0.1 
filtered_pitch = 0
filtered_roll = 0

while True:
    data = sensor.get_values()
    
    if data is not None:
        ax, ay, az = data["ax"], data["ay"], data["az"]
        
        try:
            # Calculate Pitch and Roll
            pitch = math.atan2(ay, math.sqrt(ax*ax + az*az)) * (180 / math.pi)
            roll = math.atan2(-ax, az) * (180 / math.pi)
            
            # Smooth the data with your filter
            filtered_pitch = (alpha * pitch) + ((1 - alpha) * filtered_pitch)
            filtered_roll = (alpha * roll) + ((1 - alpha) * filtered_roll)
            
            # --- ALARM CHECK FOR PYGAME OVERLAY ---
            alarm = 0
            if abs(filtered_roll) > 45.0 or filtered_pitch > 30.0 or filtered_pitch < -30.0:
                alarm = 1
            
            # ALWAYS PRINTING: This line never pauses or stops now!
            print(f"{filtered_pitch:.2f},{filtered_roll:.2f},{alarm}")
            
            # --- NON-BLOCKING AUDIO TRIGGERS ---
            # If the speaker isn't busy, hand the file to Core 1 and move on instantly
            if not audio_is_playing:
                if abs(filtered_roll) > 45.0:
                    audio_queue = "bank_angle.wav"
                elif filtered_pitch > 30.0:
                    audio_queue = "pull_up.wav"
                elif filtered_pitch < -30.0:
                    audio_queue = "stall.wav"
                    
        except ZeroDivisionError:
            pass
            
    time.sleep(0.05)