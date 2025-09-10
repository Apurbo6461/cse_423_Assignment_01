
from OpenGL.GL import *  
from OpenGL.GLUT import *  
from OpenGL.GLU import *  
import random  
import time  
import sys 

score = 0  # Tracks player score
game_over = False  # Indicates if the game is over
paused = False  # Indicates if the game is paused
diamond_speed = 1.0  # Speed of falling diamond
last_time = time.time()  # Stores time of last frame for smooth animation


diamond_x = 0  # X position of diamond
diamond_y = 0  # Y position of diamond
diamond_size = 20  # Size of the diamond
diamond_color = (1.0, 1.0, 1.0)  # Initial color (white)
diamond_falling = False  # Is diamond currently falling?

catcher_x = 0  # X position of catcher
catcher_y = -180  # Y position of catcher
catcher_width = 60  # Width of the catcher
catcher_height = 20  # Height of the catcher
catcher_color = (1.0, 1.0, 1.0)  # Color of the catcher (changes to red on game over)

screen_width = 800  # Screen width
screen_height = 600  # Screen height

# Midpoint Line Drawing  
def find_zone(x1, y1, x2, y2):
    """Determine zone (0-7) based on line slope and direction."""
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) >= abs(dy):
        if dx >= 0 and dy >= 0:
            return 0
        elif dx <= 0 and dy >= 0:
            return 3
        elif dx >= 0 and dy <= 0:
            return 4
        else:
            return 7
    else:
        if dx >= 0 and dy >= 0:
            return 1
        elif dx <= 0 and dy >= 0:
            return 2
        elif dx >= 0 and dy <= 0:
            return 5
        else:
            return 6

def convert_to_zone0(x, y, original_zone):
    """Convert coordinates from given zone to zone 0 for standard midpoint drawing."""
    if original_zone == 0:
        return x, y
    elif original_zone == 1:
        return y, x
    elif original_zone == 2:
        return y, -x
    elif original_zone == 3:
        return -x, y
    elif original_zone == 4:
        return x, -y
    elif original_zone == 5:
        return -y, x
    elif original_zone == 6:
        return -y, -x
    elif original_zone == 7:
        return -x, -y

def convert_from_zone0(x, y, target_zone):
    """Convert coordinates from zone 0 back to original zone after drawing."""
    if target_zone == 0:
        return x, y
    elif target_zone == 1:
        return y, x
    elif target_zone == 2:
        return -y, x
    elif target_zone == 3:
        return -x, y
    elif target_zone == 4:
        return x, -y
    elif target_zone == 5:
        return y, -x
    elif target_zone == 6:
        return -y, -x
    elif target_zone == 7:
        return -x, -y

def draw_line_midpoint(x1, y1, x2, y2):
    """Draw a line between two points using midpoint line drawing algorithm with zone handling."""
    zone = find_zone(x1, y1, x2, y2)  # Determine zone
    x1_z0, y1_z0 = convert_to_zone0(x1, y1, zone)  # Convert both points to zone 0
    x2_z0, y2_z0 = convert_to_zone0(x2, y2, zone)

    dx = x2_z0 - x1_z0
    dy = y2_z0 - y1_z0
    d = 2 * dy - dx  # Initial decision variable
    east = 2 * dy  # Increment when moving east
    North_east = 2 * (dy - dx)  # Increment when moving northeast

    x = x1_z0
    y = y1_z0
    points = []  # Store points to be drawn

    while x <= x2_z0:
        x_orig, y_orig = convert_from_zone0(x, y, zone)  # Convert back from zone 0
        points.append((x_orig, y_orig))
        if d > 0:
            d += North_east
            y += 1
        else:
            d += east
        x += 1
    return points

# Drawing Functions 
def draw_pixel(x, y):
    """Draw a single pixel on the screen at (x, y)."""
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def draw_line(x1, y1, x2, y2):
    """Draw a line using midpoint algorithm between two points."""
    points = draw_line_midpoint(x1, y1, x2, y2)
    for x, y in points:
        draw_pixel(x, y)

def draw_diamond(x, y, size):
    """Draw a diamond (rotated square) centered at (x, y)."""
    glColor3f(*diamond_color)
    half_size = size // 2
    draw_line(x, y + half_size, x + half_size, y)
    draw_line(x + half_size, y, x, y - half_size)
    draw_line(x, y - half_size, x - half_size, y)
    draw_line(x - half_size, y, x, y + half_size)

def draw_catcher(x, y, width, height):
    """Draw the player-controlled catcher at given position and size."""
    glColor3f(*catcher_color)
    half_width = width // 2
    draw_line(x - half_width, y, x + half_width, y)
    draw_line(x - half_width, y, x - half_width + 10, y + 10)
    draw_line(x + half_width, y, x + half_width - 10, y + 10)
    draw_line(x - half_width + 10, y + 10, x + half_width - 10, y + 10)

def draw_buttons():
    """Draw restart, play/pause, and exit buttons."""
    glColor3f(0.0, 1.0, 1.0)
    draw_line(-350, 270, -330, 260)
    draw_line(-350, 270, -330, 280)
    draw_line(-330, 260, -330, 280)

    glColor3f(1.0, 0.8, 0.0)
    if paused:
        draw_line(-10, 260, -10, 280)
        draw_line(-10, 260, 10, 270)
        draw_line(-10, 280, 10, 270)
    else:
        draw_line(-15, 260, -15, 280)
        draw_line(5, 260, 5, 280)

    glColor3f(1.0, 0.0, 0.0)
    draw_line(330, 260, 350, 280)
    draw_line(330, 280, 350, 260)

def check_collision():
    diamond_left = diamond_x - diamond_size // 2
    diamond_right = diamond_x + diamond_size // 2
    diamond_top = diamond_y + diamond_size // 2
    diamond_bottom = diamond_y - diamond_size // 2
    
    catcher_left = catcher_x - catcher_width // 2
    catcher_right = catcher_x + catcher_width // 2
    catcher_top = catcher_y + catcher_height
    catcher_bottom = catcher_y
    
    return (diamond_right > catcher_left and 
            diamond_left < catcher_right and 
            diamond_bottom < catcher_top and 
            diamond_top > catcher_bottom)

def update_diamond():
    global diamond_y, score, game_over, diamond_speed, catcher_color
    
    if not diamond_falling or paused or game_over:
        return
    
    current_time = time.time()
    delta_time = current_time - last_time
    diamond_y -= diamond_speed * delta_time * 100
    
    if diamond_y < -screen_height // 2 + diamond_size // 2:
        game_over = True
        catcher_color = (1.0, 0.0, 0.0)
        print(f"Game Over! Score: {score}")
    
    if check_collision():
        score += 1
        print(f"Score: {score}")
        diamond_speed += 0.2
        spawn_diamond()

def spawn_diamond():
    global diamond_x, diamond_y, diamond_color, diamond_falling
    diamond_x = random.randint(-screen_width//2 + diamond_size, screen_width//2 - diamond_size)
    diamond_y = screen_height // 2 - diamond_size
    diamond_color = (random.random(), random.random(), random.random())
    while sum(diamond_color) < 1.5:  # Ensure brightness
        diamond_color = (random.random(), random.random(), random.random())
    diamond_falling = True

def display():
    global last_time
    glClear(GL_COLOR_BUFFER_BIT)
    update_diamond()
    last_time = time.time()
    
    if diamond_falling:
        draw_diamond(diamond_x, diamond_y, diamond_size)
    draw_catcher(catcher_x, catcher_y, catcher_width, catcher_height)
    draw_buttons()
    glutSwapBuffers()

def keyboard_special(key, x, y):
    global catcher_x
    if game_over or paused:
        return
    if key == GLUT_KEY_LEFT:
        catcher_x = max(-screen_width//2 + catcher_width//2, catcher_x - 10)
    elif key == GLUT_KEY_RIGHT:
        catcher_x = min(screen_width//2 - catcher_width//2, catcher_x + 10)
    glutPostRedisplay()

def mouse(button, state, x, y):
    global game_over, paused, score, diamond_speed, catcher_color
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        screen_x = x - screen_width//2
        screen_y = screen_height//2 - y
        
        # Restart button
        if -370 <= screen_x <= -310 and 260 <= screen_y <= 280:
            game_over = False
            paused = False
            score = 0
            diamond_speed = 1.0
            catcher_color = (1.0, 1.0, 1.0)
            spawn_diamond()
            print("Starting over!")
        
        # Play/Pause button
        elif -20 <= screen_x <= 20 and 260 <= screen_y <= 280:
            paused = not paused
        
        # Exit button
        elif 310 <= screen_x <= 370 and 260 <= screen_y <= 280:
            print(f"Goodbye! Final score: {score}")
            glutLeaveMainLoop()
    glutPostRedisplay()

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    gluOrtho2D(-screen_width/2, screen_width/2, -screen_height/2, screen_height/2)
    spawn_diamond()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(screen_width, screen_height)
    glutCreateWindow(b"Catch the Diamonds!")
    glutDisplayFunc(display)
    glutIdleFunc(display)
    glutSpecialFunc(keyboard_special)
    glutMouseFunc(mouse)
    init()
    glutMainLoop()

if __name__ == "__main__":
    main()