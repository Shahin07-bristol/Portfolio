# 📡 MicroPython Ultrasonic Radar & Real-Time Visualizer

An end-to-end embedded radar detection and tracking system built with **MicroPython** and **Pygame**. 

The hardware uses a servo motor to perform a continuous 180° sweep while an ultrasonic distance sensor scans for obstacles. An active buzzer provides dynamic audio alerts that beep faster as objects approach. Sensor measurements are streamed live over USB Serial to a Python Pygame application on a PC, rendering a radar visual interface with color-coded threat zones and motion trails.

---

## 🚀 Key Features

* **180° Radar Scanning**: Smooth forward and reverse sweep (0°–180°) powered by PWM servo control.
* **Real-Time Distance Sensing**: Precise proximity detection up to 50 cm using ultrasonic echo timing.
* **Dynamic Audio Chirp**: Non-blocking buzzer alert with variable beep intervals based on target proximity.
* **Interactive Desktop GUI**:
  * **Radar Sweep & Fading Overlay**: Real-time sweep needle with dynamic trail decay.
  * **Visual Proximity Zones**:
    * 🔴 **Red**: Danger Zone ($\le 15\text{ cm}$)
    * 🟡 **Yellow**: Caution Zone ($\le 35\text{ cm}$)
    * 🟢 **Green**: Safe / Clear Area
  * **On-Screen Heads-Up Display (HUD)**: Live target bearing angle and measured range readout.

---

## 🧰 Hardware & Circuit Setup

### Pinout Table

| Component | Pin / Port Connection | Notes |
| :--- | :--- | :--- |
| **Microcontroller** | Raspberry Pi Pico | Running MicroPython |
| **Servo Motor (PWM)** | Pin 28 (GP28) | 50Hz PWM Signal |
| **Ultrasonic Sensor (Trig)** | Pin 19 (GP19) | Output Trigger Pulse |
| **Ultrasonic Sensor (Echo)** | Pin 14 (GP14) | Input Echo Signal |
| **Active Buzzer Module** | Pin 18 (GP18) | Proximity Alert Output |

> **Schematic Diagram**: The full circuit schematic file (`Schematic Radar.fzz`) is included in the repository and can be opened using [Fritzing](https://fritzing.org/).

---

## 📂 Repository Structure

```text
.
├── Radar.py             # MicroPython firmware running on the Pico / microcontroller
├── radar_display.py     # Desktop Pygame GUI visualizer reading serial data
├── Schematic Radar.fzz  # Fritzing circuit schematic & layout file
└── README.md            # Project documentation
```

---

## ⚙️ Installation & Usage Guide

### 1. Flash the Firmware (Microcontroller)
1. Install [MicroPython](https://micropython.org/) on your microcontroller (e.g., Raspberry Pi Pico).
2. Connect your hardware components according to the pinout table above.
3. Open `Radar.py` in **Thonny IDE** and save/run it on the board.
4. Close Thonny or stop its execution so the COM port is released for the Pygame app.

### 2. Launch the Desktop Visualizer (PC)
1. Install the necessary Python dependencies:
   ```bash
   pip install pygame pyserial
   ```
2. Open `radar_display.py` and set your device's COM port:
   ```python
   PICO_PORT = 'COM4'  # Replace 'COM4' with your actual port (e.g., '/dev/ttyACM0' on Linux)
   ```
3. Run the visualizer application:
   ```bash
   python radar_display.py
   ```

---

## 📜 Serial Data Protocol

The microcontroller streams angle and distance readings across USB Serial at `115200` baud in the following CSV format:

```text
[Angle],[Distance_cm]
Example: 90,24.5
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).