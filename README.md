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

button = TouchButton(board.A1)
button.set_touch_threshold(300)
button.set_double_click_delay(0.4)
button.disable_double_click_detection()

def on_click():
    print("Click detected!")

button.register_callback("clk", on_click)

async def main():
    await button.calibrate()
    await button.monitor_button()

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

