from machine import Pin, PWM
import time
import uasyncio as asyncio
import math
PULSES_PER_REV = 40  # adjust to your encoder resolution
MOTOR_SPEED = 30
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
        
class DistanceSensor:
    def __init__(self, trigger_pin, echo_pin, samples=10):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trigger.low()
        self.samples = samples
        self._readings = [0] * samples # create a buer of length `samples`
        
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
        return (duration * 0.0343) / 2
 
    async def auto_update(self): # we trigger this method once
        while True:
            distance = self._raw_distance_cm() # get distance in cm
            if distance > 0: # if distance is valid
                self._readings.pop(0) # remove the last reading
                self._readings.append(distance) # add a new reading
            await asyncio.sleep_ms(20) # sleep (async!)
    
    def get_distance_cm(self):
        return sorted(self._readings)[self.samples//2] # get the median from `_readings` buffer


class Robot:
    def __init__(self,motorR,motorL,sensorR,sensorL,sensorF):
        self.motorR = motorR
        self.motorL = motorL
        self.sensorR = sensorR
        self.sensorL = sensorL
        self.sensorF = sensorF

    async def rotate_by_90(self,direction):
        amount = 203
        if direction == "L":
            await asyncio.gather(
                self.motorL.rotate_degrees(amount,speed=MOTOR_SPEED),
                self.motorR.rotate_degrees(amount,direction = 0,speed=MOTOR_SPEED)
            )
        if direction == "R":
            await asyncio.gather(
                self.motorL.rotate_degrees(amount,direction = 0,speed=MOTOR_SPEED),
                self.motorR.rotate_degrees(amount,speed=MOTOR_SPEED)
            )
    async def drive(self,distance,direction="F"):
        amount = distance*3600/72

        if direction == "F":
            await asyncio.gather(
                self.motorL.rotate_degrees(amount,speed=MOTOR_SPEED),
                self.motorR.rotate_degrees(amount,speed=MOTOR_SPEED)
            )
        if direction == "R":
            print(direction)
            await asyncio.gather(
                self.motorL.rotate_degrees(amount,direction = 0,speed=MOTOR_SPEED),
                self.motorR.rotate_degrees(amount,direction = 0,speed=MOTOR_SPEED)
            )

    async def rotate_by_angle(self,angle,direction):
        amount = angle*2.26
        if direction == "L":
            await asyncio.gather(
                self.motorL.rotate_degrees(amount,speed=MOTOR_SPEED),
                self.motorR.rotate_degrees(amount,direction = 0,speed=MOTOR_SPEED)
            )
        if direction == "R":
            await asyncio.gather(
                self.motorL.rotate_degrees(amount,direction = 0,speed=MOTOR_SPEED),
                self.motorR.rotate_degrees(amount,speed=MOTOR_SPEED)
            )
    async def rotate_by_angle_single(self,angle,direction):
        amount = angle*2.26
        if direction == "R":
            await asyncio.gather(
                self.motorL.rotate_degrees(amount,speed=MOTOR_SPEED),
            )
        if direction == "L":
            await asyncio.gather(
                self.motorR.rotate_degrees(amount,speed=MOTOR_SPEED)
            )

    async def correct_angle_by_walls_distance(self,expected_distance):
        distanceL = self.sensorL.distance_cm()
        time.sleep(0.1)
        distanceR = self.sensorR.distance_cm()
        distance_between_walls = distanceL+distanceR+6
        sin = distance_between_walls/expected_distance
#         print(distanceL,distanceR)
        if sin>1:
            sin = sin-1
        angle = math.degrees(math.asin(sin))
        print(angle)
        asyncio.run(self.rotate_by_angle_single(angle,"R"))
        
    async def correct_angle_by_movmeant(self):
        distance1 = self.sensorL.distance_cm()
        asyncio.run(self.drive(5))
        distance2 = self.sensorL.distance_cm()
        
        diff = distance1-distance2
        angle = math.atan(diff/10)*180/math.pi

        print("Distance1: "+str(distance1) +" Distance2: "+str(distance2) + " Difference: " + str(diff))
        print("Tangent: " +str(diff/10))

        print(f"Angle: {angle}")
        if angle>0:
            asyncio.run(self.rotate_by_angle(angle,"R"))
        else:
            asyncio.run(self.rotate_by_angle(abs(angle),"L"))
        
    async def drive_centered(self, distance):
        degrees_needed = (distance * 3600 / 72)
        pulses_needed = (degrees_needed / 360.0) * PULSES_PER_REV
        
        self.motorL.count = 0
        self.motorR.count = 0
        
        duty = int((MOTOR_SPEED / 100.0) * 65535)
        alpha = 1000 # coefficient -- correction based on error value
        beta = 5000 # coefficient -- correction based on error value change (for smoothness)
        # COEFFICIENTS ARE TO BE ADJUSTED, FEEL FREE TO CHANGE THEIR VALUES
        
        d_error = 0
        prev_error = 0
        
        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)
        
        while (self.motorL.count + self.motorR.count) / 2 < pulses_needed:
            l_distance = self.sensorL.get_distance_cm()
            r_distance = self.sensorR.get_distance_cm()
            
            if l_distance < 10 and r_distance < 10: # if there are both walls nearby
                error = l_distance - r_distance # calculate error (diff between left and right) -- if < 0, we add power to the left motor, otherwise to the right motor
                d_error = error - prev_error
                prev_error = error
                
                correction = int(alpha * error + beta * d_error) # calculate the correction strength
                
                # apply the correction to motors
                self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty - correction)))
                self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty + correction)))
                
            else: # if left or right sensor reads a value above 10cm (we can add individual cases to track specific walls, 
                  # but i think we are lowkey entering the area of solving the maze. it depends how we want to deal with it)
                # drive straight forward on both motors
                self.motorL.motor_fwd.duty_u16(duty)
                self.motorR.motor_fwd.duty_u16(duty)
            
            await asyncio.sleep_ms(10)
        self.motorL.motor_fwd.duty_u16(65535)
        self.motorR.motor_fwd.duty_u16(65535)
        self.motorL.motor_rev.duty_u16(65535)
        self.motorR.motor_rev.duty_u16(65535)
        await asyncio.sleep_ms(50)


class Cell:
    def __init__(self,posX,posY):
#         connections to other cells
        self.pos = (posX,posY)
        self.north = None
        self.south = None
        self.west = None
        self.east = None
        
    def __print__(self):
        return self.north+self.south+self.west+self.east



class Labirynth:
    def __init__(self,cell_size):
        self.cell_size = cell_size
        self.labirynth = set()
        self.first = Cell()
        self.labirynth.add(self.first)
# north = 0
# east = 1
# south = 2
# west = 3

#sensors:
#front = 0
#left = -1
#right = 1
    def calculate_direction(self,current_cell,facing_direction,sensor_direction):
        direction = (facing_direction + sensor_direction )%4
        if direction == 0:
            return current_cell.north
        if direction == 1:
            return current_cell.east
        if direction == 2:
            return current_cell.south
        if direction == 3:
            return current_cell.west
        
    def update_labirynth(self,current_cell,facing_direction,sensor_L,sensor_F,sensor_R):
            print(sensor_F)
            cell_R = current_cell
            for i in range(math.floor(sensor_F/self.cell_size)):
                new_cell = Cell()
                connection = self.calculate_direction(current_cell,facing_direction,0)
                connection = new_cell
                connection2 = self.calculate_direction(new_cell,facing_direction+2,0)
                connection2 = cell_R
                cell_R = new_cell

#             for i in range(math.floor(sensor_R/self.cell_size)):
#                 print("B")
#             for i in range(math.floor(sensor_L/self.cell_size)):
#                 print("C")
            print(current_cell)
        
motor_right  = Motor(fwd_pin=6, rev_pin=7, encoder_pin=11)
motor_left = Motor(fwd_pin=8, rev_pin=9, encoder_pin=10)
sensorR = DistanceSensor(3,0,11)
sensorF = DistanceSensor(5,2,11)
sensorL = DistanceSensor(4,1,11)

robot = Robot(motor_right, motor_left, sensorL, sensorF, sensorR)
maze = Labirynth(20)
async def main():
    asyncio.create_task(sensorL.auto_update())
    asyncio.create_task(sensorR.auto_update())
    asyncio.create_task(sensorF.auto_update())
    
#     await robot.drive_centered(distance=25)
    await asyncio.sleep_ms(1000)

    L = sensorL.get_distance_cm()
    F = sensorF.get_distance_cm()
    R = sensorR.get_distance_cm()
    print(L,R,F)
    maze.update_labirynth(maze.first,0,L,F,R)
#     while True:
#         L = sensorL.get_distance_cm()
#         F = sensorF.get_distance_cm()
#         R = sensorR.get_distance_cm()
#         
#         print(f"L: {L:.1f} cm | F: {F:.1f} cm | R: {R:.1f} cm")
#         
#         await asyncio.sleep_ms(100)

asyncio.run(main())