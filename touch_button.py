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
    POLL_INTERVAL = 0.01
    TOUCH_CHECK_INTERVAL = 0.05
    CALIBRATION_SAMPLES = 5
    CALIBRATION_DELAY = 0.05

    def __init__(self, touch_pin: board.Pin):
        self.touch = touchio.TouchIn(touch_pin)
        self._smoothed = 0
        self._baseline = 0
        self._touch_threshold = 500
        self._ema_alpha = 0.3
        self._baseline_factor = 0.0005
        self._double_click_delay = 0.3
        self._long_press_timeout = 1.0
        self._long_hold_interval = 0.05
        self._baseline_reset_timeout = 10.0
        self._enable_double_click = True
        self._dbg = False
        self._callbacks = {
            "clk": None,
            "dclk": None,
            "lpr": None,
            "lprhld": None
        }

    async def calibrate(self):
        total = 0
        for _ in range(self.CALIBRATION_SAMPLES):
            total += self.touch.raw_value
            await asyncio.sleep(self.CALIBRATION_DELAY)
        self._baseline = total // self.CALIBRATION_SAMPLES
        if self._dbg:
            print(f"Calibrated baseline: {self._baseline}")

    def register_callback(self, event: str, cb: callable):
        if event not in self._callbacks:
            raise ValueError(f"Invalid event: {event}")
        self._callbacks[event] = cb

    def set_touch_threshold(self, threshold: int): self._touch_threshold = threshold
    def set_baseline_approximation_factor(self, factor: float): self._baseline_factor = factor
    def set_double_click_delay(self, delay: float): self._double_click_delay = delay
    def set_long_press_timeout(self, duration: float): self._long_press_timeout = duration
    def set_long_press_hold_interval(self, interval: float): self._long_hold_interval = interval
    def disable_double_click_detection(self): self._enable_double_click = False
    def enable_double_click_detection(self): self._enable_double_click = True
    def set_debug(self, dbg: bool): self._dbg = dbg

    def _is_touching(self):
        diff = self._smoothed - self._baseline
        touching = diff > self._touch_threshold
        if self._dbg:
            print(f"sraw:{self._smoothed} base:{self._baseline} diff:{diff} touching:{touching}")
        return touching

    async def _update_touch_values(self):
        touch_start = None
        while True:
            raw = self.touch.raw_value

            # Exponential moving average
            self._smoothed = raw if not self._smoothed else int(
                self._ema_alpha * raw + (1 - self._ema_alpha) * self._smoothed
            )

            # Baseline auto-reset if long touch held
            if self._is_touching():
                if touch_start is None:
                    touch_start = time.monotonic()
                elif (time.monotonic() - touch_start) > self._baseline_reset_timeout:
                    if self._dbg:
                        print("Resetting baseline due to long touch")
                    self._baseline = self._smoothed
                    touch_start = None
            else:
                touch_start = None

            # Adaptive baseline adjustment
            if self._baseline == 0:
                self._baseline = self._smoothed
            elif self._smoothed < self._baseline:
                self._baseline = self._smoothed
            else:
                self._baseline += int(self._baseline_factor * (self._smoothed - self._baseline))

            await asyncio.sleep(self.POLL_INTERVAL)

    async def _handle_touch(self):
        while True:
            await asyncio.sleep(self.TOUCH_CHECK_INTERVAL)

            if not self._is_touching():
                continue

            start = time.monotonic()
            long_fired = False

            while self._is_touching():
                elapsed = time.monotonic() - start

                if elapsed > self._long_press_timeout:
                    if not long_fired:
                        self._trigger("lpr")
                        long_fired = True

                    self._trigger("lprhld")
                    await asyncio.sleep(self._long_hold_interval)
                else:
                    await asyncio.sleep(self.POLL_INTERVAL)

            if not long_fired:
                await self._handle_click(start)

    async def _handle_click(self, start_time: float):
        clicks = 1

        if not self._enable_double_click:
            self._trigger("clk")
            return

        end_time = start_time + self._double_click_delay

        while time.monotonic() < end_time:
            if self._is_touching():
                clicks += 1
                while self._is_touching():
                    await asyncio.sleep(self.POLL_INTERVAL)
                break
            await asyncio.sleep(self.POLL_INTERVAL)

        if clicks == 1:
            self._trigger("clk")
        else:
            self._trigger("dclk")

    def _trigger(self, event: str):
        cb = self._callbacks.get(event)
        if cb:
            try:
                cb()
            except Exception as e:
                print(f"Callback error [{event}]: {e}")
        if self._dbg:
            print(f"Event: {event}")

    async def monitor_button(self):
        await asyncio.gather(
            self._update_touch_values(),
            self._handle_touch()
        )
