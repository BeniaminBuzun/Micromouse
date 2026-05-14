import time
import uasyncio as asyncio
from machine import Pin, PWM
from stats import PULSES_PER_REV

class Motor:
    def __init__(self, fwd_pin, rev_pin, encoder_pin):
        self.motor_fwd = PWM(Pin(fwd_pin))
        self.motor_rev = PWM(Pin(rev_pin))
        self.motor_fwd.freq(1000)
        self.motor_rev.freq(1000)
 
        self.count = 0
        self.encoder = Pin(encoder_pin, Pin.IN, Pin.PULL_DOWN)
        self.encoder.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._encoder_isr)
#         self.encoder.irq(trigger=Pin.IRQ_RISING, handler=self._encoder_isr)

    def _encoder_isr(self, pin):
        self.count += 1

    async def rotate_degrees(self, degrees, speed=50, direction=1, timeout_ms=10000):
        pulses_needed = (degrees / 360.0) * PULSES_PER_REV
        self.count = 0
        self.running = True

        duty = int((speed / 100.0) * 65535)

        # Start motor
        if direction == 1:
            self.motor_rev.duty_u16(0)
            self.motor_fwd.duty_u16(duty)
        else:
            self.motor_fwd.duty_u16(0)
            self.motor_rev.duty_u16(duty)

        start = time.ticks_ms()

        while self.count < pulses_needed:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                print("Timeout")
                break
            await asyncio.sleep_ms(10)  # yield less often

        # Brake
        self.motor_fwd.duty_u16(65535)
        self.motor_rev.duty_u16(65535)
        await asyncio.sleep_ms(10)  

        self.running = False

        actual_degrees = (self.count / PULSES_PER_REV) * 360
        print(f"Target: {degrees}°, Actual: {actual_degrees}° ({self.count} pulses)")
        
