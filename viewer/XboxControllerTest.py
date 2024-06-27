import pygame
import cv2
import numpy as np

# Initialize Pygame for controller support
pygame.init()
pygame.joystick.init()
controller = pygame.joystick.Joystick(0)
controller.init()

# Window settings
window_width = 800
window_height = 600
cube_size = 50

# Initial position of the cube
cube_x = window_width // 2
cube_y = window_height // 2

# Movement increment
move_increment = 5

# Create the window
window = np.zeros((window_height, window_width, 3), dtype=np.uint8)
window.fill(128)  # Grey background

def draw_cube(window, x, y, size):
    cv2.rectangle(window, (x, y), (x + size, y + size), (255, 0, 0), -1)

def main():
    global cube_x, cube_y

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                axis = event.axis
                value = event.value
                if axis == 0:  # Left stick horizontal
                    cube_x += int(value * move_increment)
                elif axis == 1:  # Left stick vertical
                    cube_y += int(value * move_increment)
            elif event.type == pygame.QUIT:
                running = False

        # Clear the window
        window.fill(128)  # Grey background

        # Draw the cube
        draw_cube(window, cube_x, cube_y, cube_size)

        # Display the window
        cv2.imshow('Xbox Control Test', window)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
            running = False

    pygame.quit()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
