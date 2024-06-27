import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Define some colors
BLACK = (0, 0, 0)
WHITE = (1, 1, 1)
RED = (1, 0, 0)
GREEN = (0, 1, 0)
BLUE = (0, 0, 1)
YELLOW = (1, 1, 0)
CYAN = (0, 1, 1)
MAGENTA = (1, 0, 1)
GREY = (0.75, 0.75, 0.75)

# Define cube vertices and colors for each face
vertices = [
    (-1, -1, -1),
    (1, -1, -1),
    (1, 1, -1),
    (-1, 1, -1),
    (-1, -1, 1),
    (1, -1, 1),
    (1, 1, 1),
    (-1, 1, 1),
]

edges = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 4),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
)

surfaces = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (0, 3, 7, 4),
    (1, 5, 6, 2),
    (0, 4, 5, 1),
    (2, 3, 7, 6),
)

colors = [
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
]

def Cube():
    glBegin(GL_QUADS)
    for i, surface in enumerate(surfaces):
        glColor3fv(colors[i % len(colors)])
        for vertex in surface:
            glVertex3fv(vertices[vertex])
    glEnd()

    glBegin(GL_LINES)
    glColor3fv(WHITE)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

def draw_grid():
    glBegin(GL_LINES)
    glColor3fv(GREY)
    for x in range(-20, 21):
        glVertex3f(x, -1, -20)
        glVertex3f(x, -1, 20)
        glVertex3f(-20, -1, x)
        glVertex3f(20, -1, x)
    glEnd()

def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 10, -10, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])

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

# Set screen dimensions
width = 800
height = 600
screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Cube with Xbox Controller")

# Setup OpenGL
glEnable(GL_DEPTH_TEST)
gluPerspective(45, (width / height), 0.1, 50.0)
glTranslatef(0.0, 0.0, -20)
setup_lighting()
cube_position = [0, 0, 0]
cube_angles = [0, 0, 0]  # Initial angles for X, Y, Z rotation
rotation_speed = 0.05
movement_sensitivity = 0.1

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False

    # Get joystick input
    x_move = joystick.get_axis(0) * movement_sensitivity
    z_move = joystick.get_axis(1) * movement_sensitivity
    x_rotate = joystick.get_axis(2) * rotation_speed
    y_rotate = joystick.get_axis(3) * rotation_speed

    # Update cube position and rotation
    cube_position[0] += x_move
    cube_position[2] += z_move
    cube_angles[0] += x_rotate
    cube_angles[1] += y_rotate

    # Clear screen and draw the cube
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(cube_position[0], cube_position[1], cube_position[2])
    glRotatef(cube_angles[0], 1, 0, 0)
    glRotatef(cube_angles[1], 0, 1, 0)
    draw_grid()
    Cube()
    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()
