import pygame
import websocket
import json
import time

# Initialize Pygame and the Xbox controller
pygame.init()
pygame.joystick.init()

# Get the number of joysticks (use pygame.JOYSTICK*)
num_joysticks = pygame.joystick.get_count()

if num_joysticks == 0:
    print("Error: No Xbox controller found!")
    quit()

# Get the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

# WebSocket connection
ws = websocket.WebSocket()
ws.connect("ws://localhost:8765")

try:
    while True:
        pygame.event.pump()

        # Get joystick input
        move_horizontal = joystick.get_axis(0)
        move_vertical = joystick.get_axis(1)
        move_up = joystick.get_button(0)  # A button
        move_down = joystick.get_button(1)  # B button
        pitch = joystick.get_axis(4) if joystick.get_button(2) else -joystick.get_axis(4)  # Right joystick vertical
        yaw = joystick.get_axis(3)  # Right joystick horizontal
        roll = (joystick.get_button(4) - joystick.get_button(5))  # LB and RB

        # Send data to Unity
        data = [move_horizontal, move_vertical, move_up, move_down, pitch, yaw, roll]
        ws.send(','.join(map(str, data)))

        time.sleep(0.01)

except KeyboardInterrupt:
    pass
finally:
    ws.close()
    pygame.quit()
