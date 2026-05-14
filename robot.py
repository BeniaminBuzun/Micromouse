import time
import math
import uasyncio as asyncio
from machine import Pin, PWM
from stats import MOTOR_SPEED, PULSES_PER_REV

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
        beta = 5000 # coefficient -- correction based on error value change	 (for smoothness)
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

