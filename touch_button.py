# touch_button.py
# Created by TOLDO TECHNIK (https://github.com/toldotechnik)
# 2024-10-09 Init
# 2024-10-10 Better double click handling
# 2024-10-22 auto calibration of baseline, improved long press detection, touch threshold
# 2024-10-23 much stabler touch detection with EMA (Exponential Moving Average) filter, switch debugging on/off method
# 2024-10-24 refactor _handle_touch
# 2024-10-26 auto tune baseline when touch is locked
# 2025-07-05 option to disable double click detection -> faster single click enable_double_click_detection
# 2025-10-21 code optimization, added lprhld (long press hold) with configurable interval, improved error handling and structure

import board
import touchio
import asyncio
import time

class TouchButton:
    # Timing constants
    POLL_INTERVAL = 0.01
    TOUCH_CHECK_INTERVAL = 0.05
    CALIBRATION_SAMPLES = 5
    CALIBRATION_DELAY = 0.05
    
    def __init__(self, touch_pin: board.Pin):
        self.touch = touchio.TouchIn(touch_pin)
        self._smoothed_raw_value = 0
        self._ema_alpha = 0.3
        self._baseline = 0
        self._baseline_approx_factor = 0.0005
        self._touch_threshold = 500
        self._double_click_delay = 0.3
        self._long_press_timeout = 1.0
        self._long_press_hold_interval = 0.05
        self._long_touch_baseline_timeout = 10.0
        self._callbacks = {
            "clk": None,
            "dclk": None,
            "lpr": None,
            "lprhld": None
        }
        self._enable_double_click = True
        self._dbg = False

    async def calibrate(self):
        values = []
        for _ in range(self.CALIBRATION_SAMPLES):
            values.append(self.touch.raw_value)
            await asyncio.sleep(self.CALIBRATION_DELAY)
        self._baseline = sum(values) / len(values)
        if self._dbg:
            print("Calibrated baseline: {}".format(int(self._baseline)))
    
    def register_callback(self, event_name: str, callback: callable):
        if event_name in self._callbacks:
            self._callbacks[event_name] = callback
        else:
            raise ValueError("Unknown event: {}. Valid: {}".format(event_name, list(self._callbacks.keys())))

    def set_touch_threshold(self, threshold: int):
        self._touch_threshold = threshold

    def set_baseline_approximation_factor(self, factor: float):
        self._baseline_approx_factor = factor

    def set_double_click_delay(self, delay: float):
        self._double_click_delay = delay

    def set_long_press_timeout(self, duration: float):
        self._long_press_timeout = duration
    
    def set_long_press_hold_interval(self, interval: float):
        self._long_press_hold_interval = interval

    def disable_double_click_detection(self):
        self._enable_double_click = False

    def enable_double_click_detection(self):
        self._enable_double_click = True

    def set_debug(self, dbg: bool):
        self._dbg = dbg

    def is_touching(self):
        is_touching = self._smoothed_raw_value > self._baseline + self._touch_threshold
        if self._dbg:
            print("sraw: {}\t baseline: {}\t threshold: {}\t diff: {}\t touching: {}".format(
                self._smoothed_raw_value,
                int(self._baseline),
                self._touch_threshold,
                int(self._smoothed_raw_value - self._baseline),
                is_touching
            ))
        return is_touching

    async def _update_touch_values(self):
        touch_start_time = None
        
        while True:
            raw_value = self.touch.raw_value
            
            if self._smoothed_raw_value == 0:
                self._smoothed_raw_value = raw_value
            else:
                self._smoothed_raw_value = int(
                    self._ema_alpha * raw_value + 
                    (1 - self._ema_alpha) * self._smoothed_raw_value
                )

            if self.is_touching():
                if touch_start_time is None:
                    touch_start_time = time.monotonic()
                elif time.monotonic() - touch_start_time > self._long_touch_baseline_timeout:
                    if self._dbg:
                        print("Auto-tuning baseline (touch held too long)")
                    self._baseline = self._smoothed_raw_value
                    touch_start_time = None
            else:
                touch_start_time = None

            if self._baseline == 0:
                self._baseline = int(self._smoothed_raw_value)
            elif self._smoothed_raw_value < self._baseline:
                self._baseline = self._smoothed_raw_value
            else:
                self._baseline = (
                    (1 - self._baseline_approx_factor) * self._baseline +
                    self._baseline_approx_factor * self._smoothed_raw_value
                )

            await asyncio.sleep(self.POLL_INTERVAL)

    async def _handle_touch(self):
        while True:
            await asyncio.sleep(self.TOUCH_CHECK_INTERVAL)
            
            if not self.is_touching():
                continue

            start_time = time.monotonic()
            long_press_fired = False

            while self.is_touching():
                elapsed_time = time.monotonic() - start_time
                
                if elapsed_time > self._long_press_timeout:
                    if not long_press_fired:
                        if self._dbg:
                            print("Event: Long Press")
                        self._safe_callback("lpr")
                        long_press_fired = True
                    
                    if self._dbg:
                        print("Event: Long Press Hold")
                    self._safe_callback("lprhld")
                    
                    await asyncio.sleep(self._long_press_hold_interval)
                else:
                    await asyncio.sleep(self.POLL_INTERVAL)
            
            if long_press_fired:
                continue

            await self._handle_clicks(start_time)

    async def _handle_clicks(self, start_time: float):
        click_count = 1
        
        if not self._enable_double_click:
            if self._dbg:
                print("Event: Click")
            self._safe_callback("clk")
            return
        
        while time.monotonic() - start_time < self._double_click_delay:
            if self.is_touching():
                click_count += 1
                while self.is_touching():
                    await asyncio.sleep(self.POLL_INTERVAL)
                break
            await asyncio.sleep(self.POLL_INTERVAL)
        
        if click_count == 1:
            if self._dbg:
                print("Event: Click")
            self._safe_callback("clk")
        else:
            if self._dbg:
                print("Event: Double Click")
            self._safe_callback("dclk")
    
    def _safe_callback(self, event_name: str):
        try:
            callback = self._callbacks.get(event_name)
            if callback:
                callback()
        except Exception as e:
            print("Error in {} callback: {}".format(event_name, e))

    async def monitor_button(self):
        await asyncio.gather(
            self._update_touch_values(),
            self._handle_touch()
        )