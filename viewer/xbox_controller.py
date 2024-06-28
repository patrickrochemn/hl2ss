import asyncio
import websockets
import pygame
import time

# Initialize Pygame and Xbox controller
pygame.init()
pygame.joystick.init()

# Check if a joystick is connected
if pygame.joystick.get_count() == 0:
    print("No joystick connected.")
    exit()

# Initialize the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Joystick name: {joystick.get_name()}")

# Initial position and rotation of the cube
cube_position = [0, 0, 0]
cube_rotation = [0, 0, 0]  # Pitch, Yaw, Roll rotation

# List to store connected clients
clients = []

async def send_message(client, message):
    try:
        await client.send(message)
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection to client closed: {client.remote_address}")

async def process_joystick():
    global cube_position, cube_rotation
    while True:
        # Process Pygame events
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # A button
                    cube_position[1] += 0.2  # Move cube up
                elif event.button == 1:  # B button
                    cube_position[1] -= 0.2  # Move cube down
                elif event.button == 4:  # Left bumper
                    cube_rotation[1] -= 5  # Rotate left (yaw)
                elif event.button == 5:  # Right bumper
                    cube_rotation[1] += 5  # Rotate right (yaw)

            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:  # Left stick horizontal
                    cube_position[0] += event.value * 0.2
                elif event.axis == 1:  # Left stick vertical
                    cube_position[2] += event.value * 0.2
                elif event.axis == 3:  # Right stick horizontal
                    cube_rotation[2] += event.value * 5  # Roll
                elif event.axis == 4:  # Right stick vertical
                    cube_rotation[0] -= event.value * 5  # Pitch

        # Send position and rotation to all connected clients
        message = f"{cube_position[0]},{cube_position[1]},{cube_position[2]},{cube_rotation[0]},{cube_rotation[1]},{cube_rotation[2]}"
        print(f"Sending message: {message}")
        await asyncio.gather(*[send_message(client, message) for client in clients])
        
        # Sleep for a short duration to prevent high CPU usage
        await asyncio.sleep(0.1)

async def handle_client(websocket, path):
    print(f"New client connected: {websocket.remote_address}")
    clients.append(websocket)
    try:
        async for message in websocket:
            pass
    finally:
        print(f"Client disconnected: {websocket.remote_address}")
        clients.remove(websocket)

async def main():
    start_server = websockets.serve(handle_client, "localhost", 8765)
    print("WebSocket server started at ws://localhost:8765")
    await asyncio.gather(
        start_server,
        process_joystick()
    )

if __name__ == "__main__":
    asyncio.run(main())
