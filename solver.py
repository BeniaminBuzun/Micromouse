from cell import Cell

DIRECTIONS = [0, 1, 2, 3]
DIR_NAME = {0: "north", 1: "east", 2: "south", 3: "west"}

async def turn_to_direction(robot, current_facing, target_facing):
    diff = (target_facing - current_facing) % 4
    if diff == 1:
        await robot.rotate_by_90("R")
    elif diff == 2:
        await robot.rotate_by_90("R")
        await robot.rotate_by_90("R")
    elif diff == 3:
        await robot.rotate_by_90("L")
    return target_facing


def floodfill_values(maze, goal_cell):
    values = {goal_cell: 0}
    queue = [goal_cell]

    while queue:
        cell = queue.pop(0)
        current_value = values[cell]

        for d in DIRECTIONS:
            neighbor = getattr(cell, DIR_NAME[d])
            if neighbor and neighbor not in values:
                values[neighbor] = current_value + 1
                queue.append(neighbor)

    return values


def best_neighbor_direction(current_cell, values):
    best_dir = None
    best_value = None
    for d in DIRECTIONS:
        neighbor = getattr(current_cell, DIR_NAME[d])
        if neighbor and neighbor in values:
            if best_value is None or values[neighbor] < best_value:
                best_value = values[neighbor]
                best_dir = d
    return best_dir


def can_drive_forward(robot, min_clear=5):
    front_distance = robot.sensorF.get_distance_cm()
    if front_distance <= 0:
        return True
    return front_distance > min_clear


async def move_one_cell_forward(robot, current_cell, facing, maze, cell_length=14):
    await robot.drive_centered_one_cell(cell_length)
    next_cell = getattr(current_cell, DIR_NAME[facing])
    if next_cell is None:
        next_cell = maze.get_or_create_neighbor(current_cell, facing)
    return next_cell


async def solve_with_floodfill(robot, maze, goal_pos=(0, 0), start_pos=None, start_facing=0, cell_length=14, max_steps=50):
    if start_pos is None:
        current_cell = maze.first
    else:
        current_cell = maze.get_current_cell(start_pos[0], start_pos[1])
        if current_cell is None:
            current_cell = Cell(start_pos[0], start_pos[1])
            maze.maze[f"{start_pos[0]},{start_pos[1]}"] = current_cell
    facing = start_facing

    goal_cell = maze.get_current_cell(goal_pos[0], goal_pos[1])
    if goal_cell is None:
        goal_cell = Cell(goal_pos[0], goal_pos[1])
        maze.maze[f"{goal_pos[0]},{goal_pos[1]}"] = goal_cell

    steps = 0
    while current_cell.pos != goal_cell.pos and steps < max_steps:
        print(f"Floodfill step {steps}: current={current_cell.pos}, facing={facing}")

        maze.update_maze(
            current_cell,
            facing,
            robot.sensorL.get_distance_cm(),
            robot.sensorF.get_distance_cm(),
            robot.sensorR.get_distance_cm()
        )

        values = floodfill_values(maze, goal_cell)
        best_dir = best_neighbor_direction(current_cell, values)
        if best_dir is None:
            print("No known path to goal from current map.")
            if can_drive_forward(robot):
                print("Front is clear, exploring forward one cell.")
                current_cell = await move_one_cell_forward(robot, current_cell, facing, maze, cell_length)
                steps += 1
                continue
            print("Front blocked and no known path; stopping.")
            break

        facing = await turn_to_direction(robot, facing, best_dir)
        current_cell = await move_one_cell_forward(robot, current_cell, facing, maze, cell_length)
        steps += 1

    if current_cell.pos == goal_cell.pos:
        print(f"Reached goal cell {goal_cell.pos} in {steps} steps.")
    else:
        print(f"Stopped at {current_cell.pos} after {steps} steps.")

    return current_cell
