from flask import Flask, request, jsonify, render_template_string
import json

app = Flask(__name__)

maze_data = {"cells": []}

@app.route('/maze', methods=['POST'])
def receive_maze():
    global maze_data
    try:
        maze_data = request.get_json()
        print("Received maze data with", len(maze_data.get('cells', [])), "cells")
        return jsonify({"status": "received", "cells_count": len(maze_data.get('cells', []))})
    except Exception as e:
        print("Error receiving maze data:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Micromouse Maze Display</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        #mazeContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 20px;
        }
        canvas {
            border: 2px solid #333;
            background-color: white;
            margin-bottom: 20px;
        }
        #status {
            font-size: 18px;
            color: #666;
            text-align: center;
        }
        #controls {
            margin-top: 20px;
            text-align: center;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin: 0 10px;
            cursor: pointer;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>Micromouse Maze Display</h1>
    <div id="mazeContainer">
        <canvas id="mazeCanvas" width="800" height="600"></canvas>
        <div id="status">Waiting for maze data...</div>
        <div id="controls">
            <button onclick="loadMaze()">Refresh Maze</button>
            <button onclick="clearMaze()">Clear Maze</button>
        </div>
    </div>

    <script>
        let lastUpdateTime = 0;

        async function loadMaze() {
            try {
                const response = await fetch('/maze_data');
                const data = await response.json();
                drawMaze(data);
                updateStatus(data);
                lastUpdateTime = Date.now();
            } catch (error) {
                console.error('Error loading maze:', error);
                document.getElementById('status').textContent = 'Error loading maze data';
            }
        }

        function updateStatus(data) {
            const cells = data.cells || [];
            const status = document.getElementById('status');
            status.textContent = `Maze loaded: ${cells.length} cells explored. Last update: ${new Date().toLocaleTimeString()}`;
        }

function drawMaze(data) {
    const canvas = document.getElementById('mazeCanvas');
    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!data || !data.cells || data.cells.length === 0) {
        ctx.fillStyle = '#666';
        ctx.font = '24px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No maze data available', canvas.width / 2, canvas.height / 2);
        return;
    }

    const cells = data.cells;
    const cellSize = 30; // pixels per cell

    // Find bounds
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    cells.forEach(cell => {
        minX = Math.min(minX, cell.x);
        maxX = Math.max(maxX, cell.x);
        minY = Math.min(minY, cell.y);
        maxY = Math.max(maxY, cell.y);
    });

    const offsetX = -minX;
    const offsetY = -minY;
    const gridWidth = maxX - minX + 1;
    const gridHeight = maxY - minY + 1;

    // Resize canvas if needed
    const requiredWidth = gridWidth * cellSize;
    const requiredHeight = gridHeight * cellSize;
    if (requiredWidth > canvas.width || requiredHeight > canvas.height) {
        canvas.width = Math.max(requiredWidth, 800);
        canvas.height = Math.max(requiredHeight, 600);
    }

    // Draw grid background
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let i = 0; i <= gridWidth; i++) {
        const x = i * cellSize;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, gridHeight * cellSize);
        ctx.stroke();
    }
    for (let i = 0; i <= gridHeight; i++) {
        const y = i * cellSize;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(gridWidth * cellSize, y);
        ctx.stroke();
    }

    // Draw walls with both X and Y flipped, wall assignments adjusted
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 3;

    cells.forEach(cell => {
        // Flip X: rightmost cell becomes leftmost
        const x = (gridWidth - 1 - (cell.x + offsetX)) * cellSize;
        // Flip Y: topmost cell becomes bottommost (already handled)
        const y = (gridHeight - 1 - (cell.y + offsetY)) * cellSize;

        // North wall – top edge
        if (cell.has_wall_north) {
            ctx.beginPath();
            ctx.moveTo(x, y);               // top-left
            ctx.lineTo(x + cellSize, y);    // top-right
            ctx.stroke();
        }
        // South wall – bottom edge
        if (cell.has_wall_south) {
            ctx.beginPath();
            ctx.moveTo(x, y + cellSize);    // bottom-left
            ctx.lineTo(x + cellSize, y + cellSize); // bottom-right
            ctx.stroke();
        }
        // East wall – after X flip, robot's East becomes left side of the cell
        if (cell.has_wall_west) {
            ctx.beginPath();
            ctx.moveTo(x, y);               // left-top
            ctx.lineTo(x, y + cellSize);    // left-bottom
            ctx.stroke();
        }
        // West wall – after X flip, robot's West becomes right side of the cell
        if (cell.has_wall_east) {
            ctx.beginPath();
            ctx.moveTo(x + cellSize, y);    // right-top
            ctx.lineTo(x + cellSize, y + cellSize); // right-bottom
            ctx.stroke();
        }
    });

    // Draw cell coordinates (also flipped)
    ctx.fillStyle = '#0066cc';
    ctx.font = '10px Arial';
    ctx.textAlign = 'center';
    cells.forEach(cell => {
        const centerX = (gridWidth - 1 - (cell.x + offsetX)) * cellSize + cellSize / 2;
        const centerY = (gridHeight - 1 - (cell.y + offsetY)) * cellSize + cellSize / 2;
        ctx.fillText(`${cell.x},${cell.y}`, centerX, centerY + 3);
    });
}
        function clearMaze() {
            const canvas = document.getElementById('mazeCanvas');
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            document.getElementById('status').textContent = 'Maze cleared';
        }

        // Load maze on page load
        loadMaze();

        // Auto-refresh every 3 seconds
        setInterval(() => {
            if (Date.now() - lastUpdateTime > 3000) {
                loadMaze();
            }
        }, 3000);
    </script>
</body>
</html>
""")

@app.route('/maze_data')
def get_maze_data():
    return jsonify(maze_data)

@app.route('/clear', methods=['POST'])
def clear_maze():
    global maze_data
    maze_data = {"cells": []}
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    print("Starting Micromouse Maze Server...")
    print("Open http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=True)