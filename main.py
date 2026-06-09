from machine import Pin, PWM
import uasyncio as asyncio
from motor import Motor
from distance_sensor import DistanceSensor
from robot import Robot
from maze import Maze
from pico_sender import connect_to_wifi, send_maze_to_server
import math

motor_right  = Motor(fwd_pin=6, rev_pin=7, encoder_pin=11)
motor_left = Motor(fwd_pin=8, rev_pin=9, encoder_pin=10)
sensorR = DistanceSensor(3,0,11)
sensorF = DistanceSensor(5,2,11)
sensorL = DistanceSensor(4,1,11)

robot = Robot(motor_right, motor_left, sensorR, sensorL, sensorF)
maze = Maze(40)


async def update_maze_loop():
    while True:
        L = sensorL.get_distance_cm()
        F = sensorF.get_distance_cm()
        R = sensorR.get_distance_cm()
        print(f"L: {L:.1f} cm | F: {F:.1f} cm | R: {R:.1f} cm")
        maze.update_maze(maze.first, 0, L, F, R)
        send_maze_to_server(maze)  # Send updated maze to server
        await asyncio.sleep_ms(500)  # aktualizuj co 0.5 sekundy
async def odometry_loop():
    while True:
        robot.update_odometry()
        await asyncio.sleep_ms(100)
        # print(f"Odometry: x={robot.x:.2f} cm, y={robot.y:.2f} cm, theta={math.degrees(robot.theta):.1f}°")

direction = 0
posX = 0
posY = 0
async def main():
    # Connect to WiFi
    # wlan = connect_to_wifi('ABCD', '12345678')  # Replace with your WiFi credentials
    # print("Connected to WiFi")
    asyncio.create_task(sensorL.auto_update())
    asyncio.create_task(sensorR.auto_update())
    asyncio.create_task(sensorF.auto_update())
    await asyncio.sleep_ms(5000 )  # Allow sensors to start updating
    maze.update_maze(maze.first, direction, robot.sensorL.get_distance_cm(), robot.sensorF.get_distance_cm(), robot.sensorR.get_distance_cm())
    print("Initial sensor readings:")
    # await asyncio.sleep_ms(2000)
    # await robot.drive(5)
    # await robot.rotate_by_90("R")
    await robot.drive_centered_towards_wall_V3(15,30)
    await asyncio.sleep_ms(500)
    await robot.rotate_by_90("R")
    await asyncio.sleep_ms(500)
    await robot.drive_centered_towards_wall_V3(15,30)
    await asyncio.sleep_ms(500)
    await robot.rotate_by_90("R")
    await asyncio.sleep_ms(500)
    await robot.drive_centered_towards_wall_V3(15,30)
    await asyncio.sleep_ms(500)
    await robot.rotate_by_90("R")
    await asyncio.sleep_ms(500)
    await robot.drive_centered_towards_wall_V3(15,30)
    await asyncio.sleep_ms(500)
    await robot.rotate_by_90("R")
    await asyncio.sleep_ms(500)
    await robot.drive_centered_towards_wall_V3(45,30)

    # i = 0
    # while i<4:
    #     await robot.drive_centered_towards_wall_V3(20,40)
    #     await asyncio.sleep_ms(500)
    #     await robot.rotate_by_90("R")
    #     await asyncio.sleep_ms(500)
    #     i += 1


    robot.motorL.motor_fwd.duty_u16(0)
    robot.motorR.motor_fwd.duty_u16(0)
    robot.motorL.motor_rev.duty_u16(0)
    robot.motorR.motor_rev.duty_u16(0)
asyncio.run(main())
