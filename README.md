# TouchButton Library for CircuitPython

**TouchButton** is a robust, async-friendly CircuitPython class/library that turns any `touchio.TouchIn` pin into a smart button supporting:

- ✅ Single Click  
- ✅ Double Click  
- ✅ Long Press  

It adds baseline calibration, noise smoothing (EMA filter), and easy async integration, making raw capacitive inputs truly usable in real-world projects.

## ⭐️ Features

- 🔧 Automatic baseline calibration (with auto-tuning if touch locks)  
- 📉 Exponential Moving Average (EMA) filtering for stable detection  
- 🎚️ Adjustable touch threshold  
- ✨ Gesture detection: single click, double click, long press  
- 🚫 Option to disable double-click for instant single-click behavior  
- 🔄 Fully async design for use with `asyncio`

## ⚡️ Dependencies

- ✅ CircuitPython 8 or newer **recommended**  
- 📦 Libraries required:
  - `asyncio`
  - `adafruit_ticks`

📥 [Download from CircuitPython.org](https://circuitpython.org/libraries)

## 📦 How to Install

Choose one of the following:

### 🗂 Source code version  
Copy `touch_button.py` to your `CIRCUITPY/lib/` folder.

### ⚡️ Compiled version  
Copy `touch_button.mpy` to your `lib/` folder — optimized to be smaller and faster.

## 🧩 Quick Example

```python
import board
import asyncio
from touch_button import TouchButton

TOUCH_PIN = board.IO5

button = TouchButton(TOUCH_PIN)
button.set_touch_threshold(300)
button.set_long_press_timeout(1.0)
button.set_double_click_delay(0.4)
button.disable_double_click_detection()
button.set_debug(False)

def on_click():
    print("Single Click detected!")

def on_double_click():
    print("Double Click detected!")

def on_long_press():
    print("Long Press detected!!")

button.register_callback("clk", on_click)
button.register_callback("dclk", on_double_click)
button.register_callback("lpr", on_long_press)

async def my_main():
    while True:
        print("My custom code is running...")
        await asyncio.sleep(10)

async def main():
    print("Calibrating touch button...")
    await button.calibrate()
    print("Calibration done. Starting tasks...")
    
    await asyncio.gather(
        button.monitor_button(),
        my_main()
    )

asyncio.run(main())
```

## 🛠️ Tuning Options

| Method                           | Description |
|----------------------------------|-------------|
| `set_touch_threshold(value)`     | Adjust sensitivity for your sensor |
| `set_double_click_delay(seconds)`| Set double-click window (e.g. 0.4 = 400ms) |
| `set_long_press_timeout(seconds)`| Define how long a press is considered "long" |
| `disable_double_click_detection()`| Instantly detect single touches |
| `set_debug(True)`                | Log raw/smoothed data for fine-tuning |

## 💡 Why Use TouchButton?

- ✅ Native touch support in CircuitPython is raw and noisy  
- 🔍 TouchButton adds filtering, calibration, and gesture detection in one easy class  
- 🧠 Designed for capacitive pads, conductive paint, foil sensors, and more  

