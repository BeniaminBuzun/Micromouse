import time
import math
import uasyncio as asyncio
from machine import Pin, PWM
from stats import MOTOR_SPEED, PULSES_PER_REV
WHEEL_CIRCUMFERENCE = 7.2        # units per full wheel turn (e.g. cm)
WHEEL_BASE = 5                 # distance between wheels
import math

class Robot:
    def __init__(self,motorR,motorL,sensorR,sensorL,sensorF):
        self.motorR = motorR
        self.motorL = motorL
        self.sensorR = sensorR
        self.sensorL = sensorL
        self.sensorF = sensorF

        # distance travaled
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0             # heading in radians
        self.prev_left_count = 0
        self.prev_right_count = 0
        # distance per encoder pulse
        self.dist_per_pulse = WHEEL_CIRCUMFERENCE / PULSES_PER_REV

    def update_odometry(self):
        """Read encoder counts and update the robot's relative pose.
        Call this regularly (e.g. in your main loop) to track position."""
        # read current counts
        left = self.motorL.count
        right = self.motorR.count

        # distance travelled by each wheel since last update
        d_left  = (left - self.prev_left_count)  * self.dist_per_pulse
        d_right = (right - self.prev_right_count) * self.dist_per_pulse

        # store current counts for next call
        self.prev_left_count = left
        self.prev_right_count = right

        # differential drive kinematics
        d_center = (d_left + d_right) / 2.0          # distance the robot moved
        d_theta  = (d_right - d_left) / WHEEL_BASE/2  # change in heading

        # update global pose
        self.x += d_center * math.cos(self.theta)
        self.y += d_center * math.sin(self.theta)
        self.theta += d_theta

        # keep theta inside [-pi, pi]
        self.theta = (self.theta + math.pi) % (2 * math.pi) - math.pi
        print(f"Pose: x={self.x:.2f} cm, y={self.y:.2f} cm, theta={math.degrees(self.theta):.1f}°")
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
        
    async def drive_centered_towards_wall(self, distance_to_wall,wall_separation=20,margin=5):
        
        self.motorL.count = 0
        self.motorR.count = 0
        last_motor_count = 0
        duty = int((MOTOR_SPEED / 100.0) * 65535)
        alpha = 200 # coefficient -- correction based on error value
        beta = 2500 # coefficient -- correction based on error value change	 (for smoothness)
        # COEFFICIENTS ARE TO BE ADJUSTED, FEEL FREE TO CHANGE THEIR VALUES
        
        d_error = 0
        prev_error = 0
        
        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)
        
        while self.sensorF.get_distance_cm() > distance_to_wall:
            l_distance = self.sensorL.get_distance_cm()
            r_distance = self.sensorR.get_distance_cm()
            print(f"Front: {self.sensorF.get_distance_cm():.1f} cm | Left: {l_distance:.1f} cm | Right: {r_distance:.1f} cm")
            if l_distance < wall_separation and r_distance < wall_separation: # if there are both walls nearby
                motor_count = (self.motorL.count + self.motorR.count) // 2
                dist = motor_count - last_motor_count * 0.18 # distance traveled since last correction (0.18 is distance per pulse)




                error = l_distance - r_distance # calculate error (diff between left and right) -- if < 0, we add power to the left motor, otherwise to the right motor
                d_error = error - prev_error
                prev_error = error
                
                correction = int(alpha * error + beta * d_error) # calculate the correction strength
                
                # apply the correction to motors
                print("BOTH WALLS NEARBY")
                print(f"Error: {error} | dError: {d_error} | Correction: {correction}")
                print("L:duty: " + str(min(65535, max(0, duty - correction))) + " R:duty: " + str(min(65535, max(0, duty + correction))))
                if correction > 0:
                    self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty - correction)))
                    self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty)))
                else:
                    self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty)))
                    self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty+correction)))

                
            else: 
                if l_distance < wall_separation:
                    error = (wall_separation/2)-6 - l_distance 
                    d_error = error - prev_error
                    print(error)
                    prev_error = error
                    
                    correction = int(alpha * error + beta * d_error) # calculate the correction strength
                    
                    # apply the correction to motors
                    print("LEFT WALL NEARBY")
                    print(f"Error: {error} | dError: {d_error} | Correction: {correction}")

                    print("L:duty: " + str(min(65535, max(0, duty - correction))) + " R:duty: " + str(min(65535, max(0, duty + correction))))
                    if- correction > 0:
                        self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty - correction)))
                        self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty)))
                    else:
                        self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty)))
                        self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty+correction)))

                elif r_distance < wall_separation:
                    error = (wall_separation/2)-6 - r_distance
                    d_error = error - prev_error
                    prev_error = error
                    correction = int(alpha * error + beta * d_error) # calculate the correction strength
                    print("RIGHT WALL NEARBY")
                    print(f"Error: {error} | dError: {d_error} | Correction: {correction}")

                    print("L:duty: " + str(min(65535, max(0, duty - correction))) + " R:duty: " + str(min(65535, max(0, duty + correction))))
                    # apply the correction to motors
                    if correction > 0:
                        self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty - correction)))
                        self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty)))
                    else:
                        self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty)))
                        self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty+correction)))

                else:
                # if left or right sensor reads a value above 10cm (we can add individual cases to track specific walls, 
                  # but i think we are lowkey entering the area of solving the maze. it depends how we want to deal with it)
                # drive straight forward on both motors
                    print("NO WALLS NEARBY")
                    self.motorL.motor_fwd.duty_u16(duty)
                    self.motorR.motor_fwd.duty_u16(duty)
            
            last_motor_count = self.motorL.count + self.motorR.count //2
            await asyncio.sleep_ms(50)

        self.motorL.motor_fwd.duty_u16(0)
        self.motorR.motor_fwd.duty_u16(0)
        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)
        await asyncio.sleep_ms(50)

    async def drive_centered_towards_wall_V2(self, distance_to_wall,wall_separation=20,margin=5):
        angles = []
        duty = int((MOTOR_SPEED / 100.0) * 65535)

        self.motorL.count = 0
        self.motorR.count = 0
        last_motor_count = 0
        alpha = 30
        beta = 1
        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)
        self.motorL.motor_fwd.duty_u16(0)
        self.motorR.motor_fwd.duty_u16(0)
        last_distance_r = self.sensorR.get_distance_cm()
        last_distance_l = self.sensorL.get_distance_cm()
        while self.sensorF.get_distance_cm() > distance_to_wall:
            
            l_distance = self.sensorR.get_distance_cm()
            r_distance = self.sensorR.get_distance_cm()
            print(f"Front: {self.sensorF.get_distance_cm():.1f} cm | Left: {l_distance:.1f} cm | Right: {r_distance:.1f} cm")
            both_motor_count = (self.motorL.count + self.motorR.count) // 2
            driven_distance = both_motor_count * 0.18
            if driven_distance > 0 and l_distance < wall_separation: # if there are both walls nearby
                angle = math.atan((last_distance_l-l_distance)/driven_distance)*180/math.pi # calculate angle to the wall based on difference between left and right distance and distance traveled since last correction
                angles.append(angle)
                angles = angles[-5:]
                angle = sum(angles)/len(angles)
                print("avg angle: " + str(angle))
                print("Angle to wall: " + str(angle))

                print(f"Driven distance: {driven_distance:.2f} cm")
                print("duty: " + str(duty), "correction: " + str(math.floor(math.fabs(angle)*alpha)))
                error = wall_separation - r_distance
                print(error)
                desired_angle = (wall_separation / 2 / error * 90)-90
                print("Desired angle: " + str(desired_angle))
                angle = angle - desired_angle
                if angle > 0:
                    self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty-(math.floor(math.fabs(angle)*alpha)))))
                    self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty)))


                else:
                    self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty)))
                    self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty-(math.floor(math.fabs(angle)*alpha)))))

            else:
                self.motorL.motor_fwd.duty_u16(duty)
                self.motorR.motor_fwd.duty_u16(duty)

            self.motorL.count = 0
            self.motorR.count = 0
            last_distance_l = l_distance
            last_distance_r = r_distance
            await asyncio.sleep_ms(200)