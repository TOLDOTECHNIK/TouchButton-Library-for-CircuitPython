# touch_button.py
# Created by TOLDO TECHNIK (https://github.com/toldotechnik)
# 2024-10-09 Init
# 2024-10-10 Better double click handling
# 2024-10-22 auto calibration of baseline, improved long press detection, touch threshold
# 2024-10-23 much stabler touch detection with EMA (Exponential Moving Average) filter, switch debugging on/off method
# 2024-10-24 refactor _handle_touch
# 2024-10-26 auto tune baseline when touch is locked
# 2025-07-05 option to disable double click detection -> faster single click enable_double_click_detection

import board
import touchio
import asyncio
import time

class TouchButton:
    def __init__(self, touch_pin: board.Pin):
        self.touch = touchio.TouchIn(touch_pin)
        self._smoothed_raw_value = 0
        self._ema_alpha = 0.1                       # Smoothing factor for EMA filter
        self._baseline = 0
        self._baseline_approx_factor = 0.0005
        self._touch_threshold = 500
        self._double_click_delay = 0.3
        self._long_set_long_press_timeout = 1.0
        self._long_touch_baseline_timeout = 10.0   # 10 seconds baseline auto tune timeout
        self._callbacks = {
            "clk": None,                            # Click
            "dclk": None,                           # Double click
            "lpr": None                             # Long press
        }
        self._enable_double_click = True
        self._dbg = False

    async def calibrate(self):
        values = []
        for _ in range(5):
            values.append(self.touch.raw_value)
            await asyncio.sleep(0.05)
        self._baseline = sum(values) / len(values)
    
    def register_callback(self, event_name: str, callback: callable):
        if event_name in self._callbacks:
            self._callbacks[event_name] = callback

    def set_touch_threshold(self, threshold: int):
        self._touch_threshold = threshold

    def set_baseline_approximation_factor(self, factor: float):
        self._baseline_approx_factor = factor

    def set_double_click_delay(self, delay):
        self._double_click_delay = delay

    def set_long_press_timeout(self, duration: float):
        self._long_set_long_press_timeout = duration

    def disable_double_click_detection(self):
        self._enable_double_click = False

    def enable_double_click_detection(self):
        self._enable_double_click = True

    def set_debug(self, dbg: bool):
        self._dbg = dbg

    async def _update_touch_values(self):
        touch_start_time = None
        while True:
            raw_value = self.touch.raw_value
            if self._smoothed_raw_value == 0:
                self._smoothed_raw_value = raw_value
            else:
                # Apply Exponential Moving Average (EMA) to smooth raw_value
                self._smoothed_raw_value = int(
                    self._ema_alpha * raw_value + (1 - self._ema_alpha) * self._smoothed_raw_value
                )

            # Detect when touch starts and track duration
            if self.is_touching():
                if touch_start_time is None:
                    touch_start_time = time.monotonic()  # Start tracking touch duration
                elif time.monotonic() - touch_start_time > self._long_touch_baseline_timeout:
                    # If touch has been held for more than 8 seconds, update the baseline
                    self._baseline = self._smoothed_raw_value
                    touch_start_time = None  # Reset the timer
            else:
                touch_start_time = None  # Reset the timer when touch is released

            # baseline adjustment with approximation
            if self._baseline == 0:
                self._baseline = int(self._smoothed_raw_value)
            elif self._smoothed_raw_value < self._baseline:
                self._baseline = self._smoothed_raw_value
            else:
                self._baseline = (
                    (1 - self._baseline_approx_factor) * self._baseline
                    + self._baseline_approx_factor * self._smoothed_raw_value
                )

            await asyncio.sleep(0.01)

    def is_touching(self):
        is_touching = self._smoothed_raw_value > self._baseline + self._touch_threshold
        if self._dbg:
            print(f"sraw: {self._smoothed_raw_value}\t baseln: {int(self._baseline)}\t thrshld: {self._touch_threshold}\t diff: {int(self._smoothed_raw_value - self._baseline)}\t tch: {is_touching}")
        return is_touching

    async def monitor_button(self):
        await asyncio.gather(self._update_touch_values(), self._handle_touch())

    async def _handle_touch(self):
        while True:
            await asyncio.sleep(0.05)
            if not self.is_touching():
                continue

            start_time = time.monotonic()
            click_count = 1

            # Handle long press detection
            while self.is_touching():
                elapsed_time = time.monotonic() - start_time
                if elapsed_time > self._long_set_long_press_timeout:
                    if (cb := self._callbacks.get("lpr")):
                        cb()

                    # Keep detecting until touch is released
                    while self.is_touching():
                        await asyncio.sleep(0.05)
                    break
                await asyncio.sleep(0.01)
            else:
                if not self._enable_double_click:
                    # Immediately fire single click without waiting
                    if (cb := self._callbacks.get("clk")):
                        cb()
                else:
                    # Handle single and double click detection
                    while time.monotonic() - start_time < self._double_click_delay:
                        if self.is_touching():
                            click_count += 1
                            await asyncio.sleep(self._double_click_delay)
                            break
                        await asyncio.sleep(0.01)

                    # Trigger appropriate callback based on click count
                    if (cb := self._callbacks.get("clk" if click_count == 1 else "dclk")):
                        cb()

