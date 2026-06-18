import time
import uasyncio as asyncio
from machine import Pin, PWM


class DistanceSensor:
    def __init__(self, trigger_pin, echo_pin, samples=13):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trigger.low()
        self.samples = samples
        self._readings = [0.0] * samples # create a buffer of length `samples`
        self._last_valid = -1.0
        
    def _raw_distance_cm(self):
        """Single raw measurement."""
        self.trigger.low()
        time.sleep_us(2)
        self.trigger.high()
        time.sleep_us(10)
        self.trigger.low()
 
        timeout = time.ticks_us()
        while self.echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), timeout) > 30000:
                return -1
            start = time.ticks_us()
 
        while self.echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), start) > 30000:
                return -1
            end = time.ticks_us()
 
        duration = time.ticks_diff(end, start)
        return duration * 0.0343 / 2
 
    async def auto_update(self): # we trigger this method once
        while True:
            distance = self._raw_distance_cm() # get distance in cm
            if distance > 0: # if distance is valid
                self._readings.pop(0) # remove the last reading
                self._readings.append(distance) # add a new reading
                self._last_valid = distance
            await asyncio.sleep_ms(20) # sleep (async!)
    
    def get_distance_cm(self):
        valid_values = [d for d in self._readings if d > 0]
        if valid_values:
            return sorted(valid_values)[len(valid_values) // 2]
        return self._last_valid