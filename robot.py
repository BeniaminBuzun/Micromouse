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
                    if correction > 0:
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
        # await asyncio.sleep_ms(50)

    async def drive_centered_one_cell(self, cell_length=14, alpha=400, beta=150, wall_presence_threshold=10, wall_keep_distance=3, front_stop_distance=3, front_presence_distance=10):
        """Drive one maze cell forward while centering between walls."""
        degrees_needed = (cell_length * 3600 / 72)
        pulses_needed = (degrees_needed / 360.0) * PULSES_PER_REV

        self.motorL.count = 0
        self.motorR.count = 0

        duty = int((MOTOR_SPEED / 100.0) * 65535)
        prev_error = 0

        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)

        last_l_distance = self.sensorL.get_distance_cm()
        last_r_distance = self.sensorR.get_distance_cm()
        front_stop_hits = 0
        last_progress = (self.motorL.count + self.motorR.count) / 2
        last_progress_time = time.ticks_ms()

        while (self.motorL.count + self.motorR.count) / 2 < pulses_needed:
            l_distance = self.sensorL.get_distance_cm()
            r_distance = self.sensorR.get_distance_cm()
            front_distance = self.sensorF.get_distance_cm()

            if front_distance > 0 and front_distance <= front_stop_distance:
                front_stop_hits += 1
                if front_stop_hits >= 3:
                    print("Front wall confirmed, stopping early")
                    break
                else:
                    print("Front reading low but not stable yet", front_distance)
            else:
                front_stop_hits = 0

            current_progress = (self.motorL.count + self.motorR.count) / 2
            if current_progress > last_progress:
                last_progress = current_progress
                last_progress_time = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), last_progress_time) > 400:
                print("No encoder progress detected, stopping to avoid stall")
                break

            left_wall = l_distance > 0 and l_distance < wall_presence_threshold
            right_wall = r_distance > 0 and r_distance < wall_presence_threshold

            if left_wall and right_wall:
                error = l_distance - r_distance
            elif left_wall:
                error = l_distance - wall_keep_distance
            elif right_wall:
                error = wall_keep_distance - r_distance
            else:
                error = 0

            d_error = error - prev_error
            prev_error = error
            correction = int(alpha * error + beta * d_error)
            max_correction = int(duty * 0.35)
            correction = min(max(correction, -max_correction), max_correction)
            if abs(error) < 0.5:
                correction = 0

            self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty + correction)))
            self.motorR.motor_fwd.duty_u16(min(65535, max(0, duty - correction)))

            await asyncio.sleep_ms(10)

        # optional front-wall confirmation when a wall is nearby
        front_distance = self.sensorF.get_distance_cm()
        if front_distance > 0 and front_distance < front_presence_distance and front_distance > front_stop_distance:
            print("Front wall ahead, confirming final position")
            start = time.ticks_ms()
            self.motorL.motor_fwd.duty_u16(duty // 2)
            self.motorR.motor_fwd.duty_u16(duty // 2)
            while True:
                front_distance = self.sensorF.get_distance_cm()
                if front_distance > 0 and front_distance <= front_stop_distance:
                    break
                if time.ticks_diff(time.ticks_ms(), start) > 400:
                    break
                await asyncio.sleep_ms(20)

        self.motorL.motor_fwd.duty_u16(0)
        self.motorR.motor_fwd.duty_u16(0)
        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)

    async def drive_centered_towards_wall_V2(self, distance_to_wall,wall_separation=20,margin=5):
        def map_range(x, old_min, old_max, new_min, new_max):
            # Prevent division by zero if the old range is a single point
            if old_max == old_min:
                return new_min
            
            # Apply the linear interpolation formula
            return new_min + ((x - old_min) * (new_max - new_min) / (old_max - old_min))
        angles = []
        duty = int((MOTOR_SPEED / 100.0) * 65535)

        self.motorL.count = 0
        self.motorR.count = 0
        alpha = -1000
        angle_range = 25
        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)
        self.motorL.motor_fwd.duty_u16(0)
        self.motorR.motor_fwd.duty_u16(0)
        last_distance_r = self.sensorR.get_distance_cm()
        last_distance_l = self.sensorL.get_distance_cm()
        while self.sensorF.get_distance_cm() > distance_to_wall:
            
            l_distance = self.sensorL.get_distance_cm()
            r_distance = self.sensorR.get_distance_cm()
            both_motor_count = (self.motorL.count + self.motorR.count) // 2
            driven_distance = both_motor_count * 0.18
            if driven_distance > 0 : # if there are both walls nearby
                angle = math.atan((last_distance_l-l_distance)/driven_distance)*180/math.pi # calculate angle to the wall based on difference between left and right distance and distance traveled since last correction
                angles.append(angle)
                angles = angles[-1:]
                angle = sum(angles)/len(angles)
                print("Angle to wall: " + str(angle))

                offset = min(max((wall_separation/2) - l_distance,-wall_separation/2),wall_separation/2)

                print("Error: " + str(offset))
                desired_angle = map_range(offset, -wall_separation/2, wall_separation/2, -angle_range, angle_range)
                print("Desired angle: " + str(desired_angle))
                angle_difference = desired_angle - angle
                print("Angle difference: " + str(angle_difference))
                applied_force = math.floor(angle_difference * alpha)
                print("Applied force: " + str(math.fabs(applied_force)))

                # if applied_force > 0:
                self.motorL.motor_fwd.duty_u16(min(65535, max(0, int(duty+(math.fabs(applied_force))))))
                self.motorR.motor_fwd.duty_u16(min(65535, max(0, int(duty-(math.fabs(applied_force))))))


                # else:
                #     self.motorL.motor_fwd.duty_u16(min(65535, max(0, duty)))
                #     self.motorR.motor_fwd.duty_u16(min(65535, max(0, int(duty-(math.fabs(applied_force))))))

            else:
                self.motorL.motor_fwd.duty_u16(duty)
                self.motorR.motor_fwd.duty_u16(duty)

            self.motorL.count = 0
            self.motorR.count = 0
            last_distance_l = l_distance
            last_distance_r = r_distance
            await asyncio.sleep_ms(100)
    async def drive_centered_towards_wall_V3(self, distance_to_wall,wall_separation=20,margin=5):
        ANGLE_CHECK_INTERVAL = 1
        duty = int((MOTOR_SPEED / 100.0) * 65535)
        angles = []

        self.motorL.counter = 0
        self.motorR.counter = 0
        alpha =300
        beta = 150
        offsetLimit = 8
        self.motorL.motor_rev.duty_u16(0)
        self.motorR.motor_rev.duty_u16(0)
        self.motorL.motor_fwd.duty_u16(0)
        self.motorR.motor_fwd.duty_u16(0)
        last_distance_r = self.sensorR.get_distance_cm()
        last_distance_l = self.sensorL.get_distance_cm()
        last_offset = 0
        i = 0
        while self.sensorF.get_distance_cm() > distance_to_wall:

        # calculate centering force 
            l_distance = self.sensorL.get_distance_cm()
            r_distance = self.sensorR.get_distance_cm()

            if l_distance > wall_separation*3/4 and r_distance > wall_separation*3/4:
                force1 = 0
                offset = 0
                print("NO WALLS NEARBY")
            elif l_distance > wall_separation*3/4:
                offset = -min(max((wall_separation/2)-3 - r_distance,-wall_separation/2-3),wall_separation/2+3)
                offset = min(max(offset,-offsetLimit),offsetLimit)
                force1 = alpha * offset


                print("LEFT WALL NEARBY")
            elif r_distance > wall_separation*3/4:
                offset = min(max((wall_separation/2)-3 - l_distance,-wall_separation/2-3),wall_separation/2+3)
                offset = min(max(offset,-offsetLimit),offsetLimit)

                force1 = alpha * offset
                print("RIGHT WALL NEARBY")
            else:
                offset = r_distance - l_distance 
                offset = min(max(offset,-offsetLimit),offsetLimit)
                force1 = alpha * offset
                print("BOTH WALLS NEARBY")

    # multiply force by 1.5 if offset is increasing, otherwise multiply by 0.7 to prevent overshooting
            if math.fabs(offset) > last_offset:
                force1 *= 1.5
            else:
                force1 *= 0.7
            last_offset = math.fabs(offset)
            force2 = 0

            both_motor_count = (self.motorL.counter + self.motorR.counter) // 2
            driven_distance = both_motor_count * 0.18
            print(driven_distance)
            if i%ANGLE_CHECK_INTERVAL == 0 and driven_distance > 0 and l_distance < wall_separation*3/4 and r_distance < wall_separation*3/4:
                # calculate angle to the wall based on difference between left and right distance and distance traveled since last correction
                
                angle_r = math.atan((last_distance_r-r_distance)/driven_distance)*180/math.pi 
                angle_l = -math.atan((last_distance_l-l_distance)/driven_distance)*180/math.pi
                if math.fabs(angle_r-angle_l) <30:
                    angle = min(max((math.fabs(angle_r)+math.fabs(angle_l))/2,-15),15)
                else:
                    print("Angle difference between left and right is too big, skipping angle correction")
                    angle = 0
                if r_distance - last_distance_r < 0 and l_distance - last_distance_l > 0:
                    force2 = -math.fabs(beta * angle)
                elif r_distance - last_distance_r > 0 and l_distance - last_distance_l < 0:
                    force2 = math.fabs(beta * angle)
                else:
                    force2 = 0
                # force2 = 0

                # if math.fabs(angle) > 10:
                # force2 = beta * angle   
                print("distance left: " + str(l_distance) + " distance right: " + str(r_distance))
                print("last distance left: " + str(last_distance_l) + " last distance right: " + str(last_distance_r))
                print("Angle to wall R: " + str(angle_r) + " Angle to wall L: " + str(angle_l))
                print("Chosen angle: " + str(angle))
                print("Force2 based on angle: " + str(force2))
                last_distance_l = l_distance
                last_distance_r = r_distance
                self.motorL.counter = 0
                self.motorR.counter = 0

            #     angle = math.atan((last_distance_r-r_distance)/driven_distance)*180/math.pi # calculate angle to the wall based on difference between left and right distance and distance traveled since last correction
            #     # print("Angle to wall: " + str(angle))
            #     # print("Offset: " + str(last_distance_r-r_distance))
            #     angle = min(max(angle,-25),25)
            #     if math.fabs(angle) > 5:
            #         force1 = 0
            #     angles.append(angle)
            #     angles = angles[-2:]
            #     angle = sum(angles)/len(angles)
            #     force2 = beta * angle
            #     # print("Average angle: " + str(angle))
            #     # print("___")

            applied_force = force1 +force2
            self.motorL.motor_fwd.duty_u16(min(65535, max(0, int(duty+(applied_force)))))
            self.motorR.motor_fwd.duty_u16(min(65535, max(0, int(duty-(applied_force)))))
            print("r_distance: " + str(r_distance) + " l_distance: " + str(l_distance) + " offset: " + str(offset))
            print("force1: " + str(force1) + " force2: " + str(force2) + " applied_force: " + str(applied_force))
            print("_____")
            await asyncio.sleep_ms(200)
            self.motorL.motor_rev.duty_u16(0)
            self.motorR.motor_rev.duty_u16(0)
            self.motorL.motor_fwd.duty_u16(0)
            self.motorR.motor_fwd.duty_u16(0)
            i+=1
            await asyncio.sleep_ms(50)

        print("Final front distance: " + str(self.sensorF.get_distance_cm()))