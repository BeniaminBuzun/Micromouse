from machine import Pin, PWM
import time
import uasyncio as asyncio
import math
from motor import Motor
from distance_sensor import DistanceSensor
from robot import Robot
from maze import Maze

PULSES_PER_REV = 40  # adjust to your encoder resolution
MOTOR_SPEED = 30
        
motor_right  = Motor(fwd_pin=6, rev_pin=7, encoder_pin=11)
motor_left = Motor(fwd_pin=8, rev_pin=9, encoder_pin=10)
sensorR = DistanceSensor(3,0,11)
sensorF = DistanceSensor(5,2,11)
sensorL = DistanceSensor(4,1,11)

robot = Robot(motor_right, motor_left, sensorL, sensorF, sensorR)
maze = Maze(20)

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
    maze.update_maze(maze.first,0,L,F,R)
#     while True:
#         L = sensorL.get_distance_cm()
#         F = sensorF.get_distance_cm()
#         R = sensorR.get_distance_cm()
#         
#         print(f"L: {L:.1f} cm | F: {F:.1f} cm | R: {R:.1f} cm")
#         
#         await asyncio.sleep_ms(100)

asyncio.run(main())