import urequests
import json
import network
import time

def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to WiFi:', wlan.ifconfig())
    return wlan

def send_maze_to_server(maze, server_ip='10.200.109.165', port=5000):
    cells_data = []
    for cell in maze.maze:
        cell_data = {
            "x": cell.pos[0],
            "y": cell.pos[1],
            "has_wall_north": cell.north is None,
            "has_wall_south": cell.south is None,
            "has_wall_east": cell.east is None,
            "has_wall_west": cell.west is None
        }
        cells_data.append(cell_data)
    
    data = {"cells": cells_data}
    url = f"http://{server_ip}:{port}/maze"
    headers = {'Content-Type': 'application/json'}
    try:
        response = urequests.post(url, data=json.dumps(data), headers=headers)
        print("Maze sent:", response.text)
        response.close()
    except Exception as e:
        print("Error sending maze:", e)