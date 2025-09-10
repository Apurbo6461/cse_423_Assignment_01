#task-01

import random  # Used for generating random positions for raindrops
from OpenGL.GL import *      # Core OpenGL functions
from OpenGL.GLUT import *    # OpenGL Utility Toolkit for windowing, events
from OpenGL.GLU import *     # OpenGL Utility Library (for 2D/3D projection)

# ---------- Global Variables ----------
width, height = 800, 600  # Window dimensions
raindrops = []            # List to store raindrop coordinates
num_drops = 300           # Total number of raindrops
rain_dx = 0.0             # Horizontal drift of raindrops
bg_color = [0.0, 0.0, 0.0]  # Background color (starts in night mode)

# ---------- Initialize Raindrops ----------
def init_rain():
    global raindrops
    # Generate random (x, y) positions for each raindrop
    raindrops = [(random.randint(0, width), random.randint(0, height)) for _ in range(num_drops)]

# ---------- Update Raindrop Positions ----------
def update_rain():
    global raindrops
    new_drops = []
    for x, y in raindrops:
        y -= 5          # Move drop downward
        x += rain_dx    # Drift left/right
        # If drop moves out of screen, reset it to the top
        if y < 0 or x < 0 or x > width:
            x = random.randint(0, width)
            y = height
        new_drops.append((x, y))  # Add updated position to new list
    raindrops[:] = new_drops      # Replace old drops with updated ones
    glutPostRedisplay()           # Request screen redraw

# ---------- Draw the Rain Using Lines ----------
def draw_rain():
    glColor3f(0.3, 0.6, 1.0)  # Light blue color
    glLineWidth(1.5)
    glBegin(GL_LINES)
    for x, y in raindrops:
        glVertex2f(x, y)                       # Start of rain line
        glVertex2f(x + rain_dx * 3, y - 10)    # End of rain line (slanted if dx ≠ 0)
    glEnd()

# ---------- Setup Viewport and Projection ----------
def iterate():
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, width, 0.0, height)  # Set orthographic 2D projection
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

# ---------- Draw the House (using triangles/points/lines) ----------
def draw_house():
    # Walls: two triangles forming a rectangle
    glColor3f(1.0, 0.95, 0.9)
    glBegin(GL_TRIANGLES)
    glVertex2f(250, 150)
    glVertex2f(550, 150)
    glVertex2f(550, 300)
    glVertex2f(550, 300)
    glVertex2f(250, 300)
    glVertex2f(250, 150)
    glEnd()

    # Door: two triangles forming a rectangle
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_TRIANGLES)
    glVertex2f(370, 150)
    glVertex2f(430, 150)
    glVertex2f(430, 230)
    glVertex2f(430, 230)
    glVertex2f(370, 230)
    glVertex2f(370, 150)
    glEnd()

    # Door lock as a point
    glColor3f(0.0, 0.0, 0.0)
    glPointSize(6)
    glBegin(GL_POINTS)
    glVertex2f(425, 190)
    glEnd()

    # Windows (left & right)
    for offset in [0, 160]:
        x1 = 280 + offset
        x2 = x1 + 40
        y1 = 230
        y2 = 270

        # Window rectangles using triangles
        glColor3f(0.1, 0.4, 0.9)
        glBegin(GL_TRIANGLES)
        glVertex2f(x1, y1)
        glVertex2f(x2, y1)
        glVertex2f(x2, y2)
        glVertex2f(x2, y2)
        glVertex2f(x1, y2)
        glVertex2f(x1, y1)
        glEnd()

        # Cross lines in window
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(x1 + 20, y1)        # Vertical line
        glVertex2f(x1 + 20, y2)
        glVertex2f(x1, (y1 + y2) / 2)  # Horizontal line
        glVertex2f(x2, (y1 + y2) / 2)
        glEnd()

# ---------- Roof ----------
def draw_roof():
    glColor3f(0.4, 0.0, 0.8)
    glBegin(GL_TRIANGLES)
    glVertex2f(230, 300)  # Left corner
    glVertex2f(570, 300)  # Right corner
    glVertex2f(400, 400)  # Peak
    glEnd()

#  Draw Background Trees 
def draw_trees():
    for i in range(15):
        x = 30 + i * 50
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_TRIANGLES)
        glVertex2f(x, 150)
        glVertex2f(x + 30, 150)
        glVertex2f(x + 15, 210)
        glEnd()

# ---------- Ground ----------
def draw_ground():
    glColor3f(0.5, 0.3, 0.0)
    glBegin(GL_TRIANGLES)
    glVertex2f(0, 0)
    glVertex2f(width, 0)
    glVertex2f(width, 150)
    glVertex2f(width, 150)
    glVertex2f(0, 150)
    glVertex2f(0, 0)
    glEnd()

# ---------- Main Render Function ----------
def show_screen():
    glClearColor(*bg_color, 1.0)  # Set background color
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear screen
    glLoadIdentity()
    iterate()

    # Draw scene elements
    draw_ground()
    draw_trees()
    draw_house()
    draw_roof()
    draw_rain()

    glutSwapBuffers()  # Double buffering

# ---------- Arrow Key Interaction ----------
def special_keys(key, x, y):
    global rain_dx
    if key == GLUT_KEY_LEFT:
        rain_dx -= 0.2  # Bend rain to the left
    elif key == GLUT_KEY_RIGHT:
        rain_dx += 0.2  # Bend rain to the right

# ---------- Keyboard Interaction ----------
def keyboard(key, x, y):
    global bg_color
    if key == b'n':  # Night to Day: increase background brightness
        for i in range(3):
            bg_color[i] = min(bg_color[i] + 0.05, 1.0)
    elif key == b'd':  # Day to Night: darken background
        for i in range(3):
            bg_color[i] = max(bg_color[i] - 0.05, 0.0)

# ---------- Main Function ----------
def main():
    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)  # Double buffering and RGBA color
    glutInitWindowSize(width, height)  # Set window size
    glutInitWindowPosition(100, 100)  # Set window position
    glutCreateWindow(b"Rainfall on House - Assignment Task 1")  # Create window
    glutDisplayFunc(show_screen)     # Register display callback
    glutIdleFunc(update_rain)        # Continuously update raindrops
    glutSpecialFunc(special_keys)    # Register special key handler (arrow keys)
    glutKeyboardFunc(keyboard)       # Register keyboard handler
    init_rain()                      # Initialize raindrops
    glutMainLoop()                   # Start event loop

main()  # Run the program


























# #task-02

# import random  # For generating random directions and colors
# from OpenGL.GL import *  # Core OpenGL functions
# from OpenGL.GLUT import *  # OpenGL Utility Toolkit for windowing and input
# from OpenGL.GLU import *  # OpenGL Utility Library for 2D/3D viewing
# import time  # To manage blinking timing

# # Global variables
# width, height = 800, 600  # Window dimensions
# points = []  # List to store point data: [x, y, dx, dy, r, g, b]
# blink = False  # Controls whether blinking is enabled
# freeze = False  # Pauses movement when True
# speed = 1.0  # Movement speed
# last_blink_time = time.time()  # Last time the blink status changed
# blink_on = True  # Whether the points are currently visible in blinking mode

# # Function to add a new point at (x, y)
# def add_point(x, y):
#     dir_x = random.choice([-1, 1])  # Random direction in X
#     dir_y = random.choice([-1, 1])  # Random direction in Y
#     color = [random.random(), random.random(), random.random()]  # Random RGB color
#     points.append([x, y, dir_x, dir_y] + color)  # Append point with position, direction, and color

# # Function to update point positions and handle bouncing/blinking
# def update_points():
#     global points, last_blink_time, blink_on
#     if freeze:
#         return  # Skip updates if frozen

#     for p in points:
#         p[0] += p[2] * speed  # Update x position
#         p[1] += p[3] * speed  # Update y position

#         # Reverse direction if hitting window boundaries
#         if p[0] <= 0 or p[0] >= width:
#             p[2] *= -1
#         if p[1] <= 0 or p[1] >= height:
#             p[3] *= -1

#     # Handle blinking logic if enabled
#     if blink:
#         current_time = time.time()
#         if current_time - last_blink_time > 0.5:  # Toggle visibility every 0.5s
#             blink_on = not blink_on
#             last_blink_time = current_time

#     glutPostRedisplay()  # Request to redraw the screen

# # Function to render the points
# def draw_points():
#     glPointSize(8)  # Set point size
#     glBegin(GL_POINTS)  # Begin drawing points
#     for p in points:
#         if blink and not blink_on:
#             glColor3f(0.0, 0.0, 0.0)  # Set color to background (black) when blinking off
#         else:
#             glColor3f(p[4], p[5], p[6])  # Set color to point's color
#         glVertex2f(p[0], p[1])  # Draw the point at (x, y)
#     glEnd()  # End drawing

# # Function to handle screen refresh
# def show_screen():
#     glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
#     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear screen
#     glLoadIdentity()  # Reset transformation
#     gluOrtho2D(0, width, 0, height)  # Set 2D orthographic projection
#     draw_points()  # Draw all points
#     glutSwapBuffers()  # Swap buffers for double buffering

# # Mouse input callback
# def mouse_click(button, state, x, y):
#     global blink
#     if freeze or state != GLUT_DOWN:
#         return  # Ignore clicks if frozen or not mouse down

#     y = height - y  # Flip y-axis to match OpenGL coordinates

#     if button == GLUT_RIGHT_BUTTON:
#         add_point(x, y)  # Right click adds a point
#     elif button == GLUT_LEFT_BUTTON:
#         blink = not blink  # Left click toggles blinking

# # Special keys (arrow keys) callback
# def special_keys(key, x, y):
#     global speed
#     if freeze:
#         return  # Do nothing if frozen
#     if key == GLUT_KEY_UP:
#         speed += 0.2  # Increase speed
#     elif key == GLUT_KEY_DOWN:
#         speed = max(0.2, speed - 0.2)  # Decrease speed, minimum 0.2

# # Keyboard input callback
# def keyboard(key, x, y):
#     global freeze
#     if key == b' ':  # Spacebar pressed
#         freeze = not freeze  # Toggle freeze mode

# # Main function to set up the OpenGL environment and enter main loop
# def main():
#     glutInit()  # Initialize GLUT
#     glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # Enable double buffering and RGB mode
#     glutInitWindowSize(width, height)  # Set window size
#     glutInitWindowPosition(100, 100)  # Set window position
#     glutCreateWindow(b"Moving Bouncing Points with Mouse & Keyboard Interaction")  # Create window with title

#     # Register callback functions
#     glutDisplayFunc(show_screen)  # Set display function
#     glutIdleFunc(update_points)  # Set idle (update) function
#     glutMouseFunc(mouse_click)  # Set mouse click function
#     glutKeyboardFunc(keyboard)  # Set keyboard function
#     glutSpecialFunc(special_keys)  # Set special keys function (arrow keys)

#     glutMainLoop()  # Enter the main event loop

# # Run the application
# main()
