import machine
import time
from mpu6050 import MPU6050
from bmp280 import BMP280
from gy271 import GY271  # 1. Import the new compass driver

print("====================================================")
print("     PICO FLIGHT CONTROLLER: MICROPYTHON BOOT       ")
print("====================================================")

# Initialize Busses
i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17), freq=400000)
i2c1 = machine.I2C(1, sda=machine.Pin(14), scl=machine.Pin(15), freq=100000)
gps_uart = machine.UART(1, baudrate=9600, tx=machine.Pin(4), rx=machine.Pin(5))

# Instantiate sensor driver classes
imu = MPU6050(i2c0)
baro = BMP280(i2c1)
compass = GY271(i2c1) # 2. Link the compass to the shared I2C1 bus

print("\nHardware test loop running. Press CTRL+C to stop.\n")
time.sleep(1)

while True:
    imu_data = imu.get_values()
    temp_check = baro.get_altitude()
    mag_data = compass.get_heading() # 3. Fetch magnetic heading data
    
    # Process GPS stream safely
    gps_raw = ""
    if gps_uart.any():
        raw_bytes = gps_uart.read(64)
        if raw_bytes:
            try:
                gps_raw = raw_bytes.decode('utf-8').strip().replace('\n', ' ')
            except UnicodeError:
                gps_raw = "".join(chr(b) for b in raw_bytes if 32 <= b < 127)

    # 4. Print everything out simultaneously to the console
    if imu_data:
        print(f"IMU Accel: X:{imu_data['ax']:.2f} Y:{imu_data['ay']:.2f} Z:{imu_data['az']:.2f} | Mag: X:{mag_data['mx']} Y:{mag_data['my']} | Baro: {temp_check}°C | GPS Stream: {gps_raw[:20]}")
    else:
        print("Error reading IMU!")

    time.sleep(0.1)