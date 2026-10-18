from machine import Pin, PWM
import time

# --- PIN CONFIGURATION ---
servo = PWM(Pin(28))
servo.freq(50)

# Ultrasonic Sensor
trig = Pin(19, Pin.OUT)  
echo = Pin(14, Pin.IN)

# Active Buzzer Module
buzzer = Pin(18, Pin.OUT)

# --- VARIABLES ---
last_beep_time = time.ticks_ms()

# --- FUNCTIONS ---
def set_angle(angle):
    """Moves the servo to a specific angle (0-180 degrees)"""
    ns = 500000 + int((angle / 180) * 2000000)
    servo.duty_ns(ns)

def get_distance():
    """Measures distance in centimeters using the ultrasonic sensor"""
    trig.low()
    time.sleep_us(2)
    
    # Send 10-microsecond trigger pulse
    trig.high()
    time.sleep_us(10)
    trig.low()
    
    # Measure duration of the Echo pulse
    signaloff = time.ticks_us()
    while echo.value() == 0:
        signaloff = time.ticks_us()
        
    signalon = time.ticks_us()
    while echo.value() == 1:
        signalon = time.ticks_us()
        
    timepassed = signalon - signaloff
    distance = (timepassed * 0.0343) / 2
    return distance

def handle_buzzer(dist):
    """Calculates beep speed based on distance without freezing the servo"""
    global last_beep_time
    current_time = time.ticks_ms()
    
    # If nothing is within 50cm, keep the buzzer quiet
    if dist > 50 or dist < 2:
        buzzer.low()
        return

    # Map distance (2cm to 50cm) to a beep delay interval (50ms to 800ms)
    # Closer object = smaller delay = faster beeping!
    beep_interval = int(50 + ((dist - 2) / 48) * 750)
    
    # Non-blocking timer check
    if time.ticks_diff(current_time, last_beep_time) > beep_interval:
        buzzer.high()
        time.sleep_ms(15)  # Quick, sharp audio chirp
        buzzer.low()
        last_beep_time = current_time

# --- MAIN LOOP ---
print("Scanning started... Output format: [Angle, Distance(cm)]")

try:
    while True:
        # Forward Sweep: 0 to 180 degrees
        for angle in range(0, 181, 2):
            set_angle(angle)
            time.sleep_ms(35)     # Steady tracking step delay
            dist = get_distance()
            handle_buzzer(dist)
            print(f"{angle},{dist:.1f}")
            
        # Backward Sweep: 180 to 0 degrees
        for angle in range(180, -1, -2):
            set_angle(angle)
            time.sleep_ms(35)
            dist = get_distance()
            handle_buzzer(dist)
            print(f"{angle},{dist:.1f}")

except KeyboardInterrupt:
    # Safe shutdown routine when Ctrl+C is pressed
    servo.deinit()
    buzzer.low()
    print("\nRadar system safely powered down.")