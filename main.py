from machine import Pin, PWM
import uasyncio as asyncio
from motor import Motor
from distance_sensor import DistanceSensor
from robot import Robot
from maze import Maze

<<<<<<< HEAD
        
=======
 
>>>>>>> c26f4a09af471f8035a9ec658a239a261ea219bb
motor_right  = Motor(fwd_pin=6, rev_pin=7, encoder_pin=11)
motor_left = Motor(fwd_pin=8, rev_pin=9, encoder_pin=10)
sensorR = DistanceSensor(3,0,11)
sensorF = DistanceSensor(5,2,11)
sensorL = DistanceSensor(4,1,11)

robot = Robot(motor_right, motor_left, sensorL, sensorF, sensorR)
maze = Maze(20)


async def update_maze_loop():
    while True:
        L = sensorL.get_distance_cm()
        F = sensorF.get_distance_cm()
        R = sensorR.get_distance_cm()
        print(f"L: {L:.1f} cm | F: {F:.1f} cm | R: {R:.1f} cm")
        maze.update_maze(maze.first, 0, L, F, R)
        await asyncio.sleep_ms(500)  # aktualizuj co 0.5 sekundy

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
    print("Updating maze...")
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
