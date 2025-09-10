from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15  # Added this line to fix the error
import math
import random
import time

# Global Game State
WINDOW_W, WINDOW_H = 1000, 800

# Grid config
GRID_HALF = 300     # grid spans from -GRID_HALF..+GRID_HALF on X and Z
GRID_STEP = 30      # spacing between lines

# Player
player_x, player_z = 0.0, 0.0
player_y = 0.0
player_angle = 0.0         # yaw in degrees (0 -> +Z)
player_speed = 3.0
player_alive = True

# Gun / bullets
bullets = []               # each bullet: dict(x,y,z, angle, speed)
bullet_speed = 8.0
bullet_size = 6.0
bullet_cooldown = 0.12     # seconds between shots
last_shot_time = 0.0
bullets_missed = 0

# Enemies
NUM_ENEMIES = 5
enemies = []               # each enemy: dict(x,z, phase, speed)
enemy_speed_base = 1.2
enemy_touch_dist = 18.0
enemy_respawn_margin = 40.0

# Score/Life
score = 0
life = 5
game_over = False
game_over_reason = ""

# Camera
camera_mode_first_person = False
cam_orbit_angle = 45.0     # for third-person orbit (degrees)
cam_radius = 700.0
cam_height = 300.0

# Cheat mode
cheat_enabled = False
cheat_auto_follow = False  # works only in first-person according to spec
cheat_spin_speed = 2.2     # deg per frame
cheat_fire_cone = 8.0      # degrees within which an enemy is considered "in line of sight"

# Time
prev_time = time.time()

# Utility
def clamp(v, a, b):
    return max(a, min(b, v))

def dist2(x1, z1, x2, z2):
    dx = x1 - x2
    dz = z1 - z2
    return dx*dx + dz*dz

def angle_to(x1, z1, x2, z2):
    ang = math.degrees(math.atan2((x2-x1), (z2-z1)))  # note swapped to align 0->+Z
    return ang

def wrap_angle(a):
    while a < -180: a += 360
    while a > 180: a -= 360
    return a

def now():
    return time.time()

# HUD Text (bitmap)
def draw_text_2d(x, y, text, font=None):
    if font is None:
        font = GLUT_BITMAP_9_BY_15  # This line (88) now correctly uses the imported constant

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glColor3f(1,1,1)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ... (rest of the code remains the same)

def draw_grid_and_bounds():
    # Floor grid (dynamic using loops)
    glDisable(GL_LIGHTING)
    glColor3f(0.25, 0.25, 0.25)
    glBegin(GL_LINES)
    for x in range(-GRID_HALF, GRID_HALF+1, GRID_STEP):
        glVertex3f(x, 0, -GRID_HALF)
        glVertex3f(x, 0,  GRID_HALF)
    for z in range(-GRID_HALF, GRID_HALF+1, GRID_STEP):
        glVertex3f(-GRID_HALF, 0, z)
        glVertex3f( GRID_HALF, 0, z)
    glEnd()

    # 4 vertical boundaries as cuboids (thin walls)
    glColor3f(0.5, 0.5, 0.8)
    wall_height = 60
    wall_thickness = 3
    # +Z wall
    draw_cuboid(-GRID_HALF, 0, GRID_HALF, 2*GRID_HALF, wall_height, wall_thickness)
    # -Z wall
    draw_cuboid(-GRID_HALF, 0, -GRID_HALF - wall_thickness, 2*GRID_HALF, wall_height, wall_thickness)
    # +X wall
    draw_cuboid(GRID_HALF, 0, -GRID_HALF, wall_thickness, wall_height, 2*GRID_HALF)
    # -X wall
    draw_cuboid(-GRID_HALF - wall_thickness, 0, -GRID_HALF, wall_thickness, wall_height, 2*GRID_HALF)
    glEnable(GL_LIGHTING)

def draw_cuboid(x, y, z, sx, sy, sz):
    glPushMatrix()
    glTranslatef(x + sx/2.0, y + sy/2.0, z + sz/2.0)
    glScalef(sx, sy, sz)
    glutSolidCube(1.0)
    glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    if game_over and not player_alive:
        glRotatef(90, 0, 0, 1)  # lie down
    # Torso
    glColor3f(0.2, 0.7, 0.2)
    draw_cuboid(-6, 0, -6, 12, 18, 12)
    # Head (sphere)
    glColor3f(0.9, 0.8, 0.7)
    glPushMatrix()
    glTranslatef(0, 22, 0)
    quad = gluNewQuadric()
    gluSphere(quad, 6, 16, 16)
    glPopMatrix()
    # Gun base (cylinder on right side)
    glPushMatrix()
    glRotatef(player_angle, 0, 1, 0)
    glTranslatef(0, 12, 8)  # move the gun forward
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.4, 0.4, 0.4)
    quad2 = gluNewQuadric()
    gluCylinder(quad2, 2.5, 2.5, 18, 16, 1)
    # Gun muzzle cube
    glPopMatrix()
    glPushMatrix()
    glRotatef(player_angle, 0, 1, 0)
    glTranslatef(0, 12, 26)
    glColor3f(0.2, 0.2, 0.2)
    glutSolidCube(4.0)
    glPopMatrix()
    glPopMatrix()

def draw_enemy(ex, ez, anim_scale):
    glPushMatrix()
    glTranslatef(ex, 0, ez)
    glScalef(anim_scale, anim_scale, anim_scale)
    # two spheres stacked
    glColor3f(0.8, 0.2, 0.2)
    q = gluNewQuadric()
    gluSphere(q, 8, 20, 20)              # bottom sphere
    glTranslatef(0, 10, 0)
    gluSphere(q, 5.5, 20, 20)            # top sphere
    glPopMatrix()

def draw_bullet(b):
    glPushMatrix()
    glTranslatef(b['x'], b['y'], b['z'])
    glutSolidCube(bullet_size)
    glPopMatrix()

# Spawning / Reset
def spawn_enemy():
    # Spawn around the perimeter
    side = random.choice([0,1,2,3])
    if side == 0:  # north (+Z)
        ex = random.uniform(-GRID_HALF+20, GRID_HALF-20)
        ez = GRID_HALF - enemy_respawn_margin
    elif side == 1: # south
        ex = random.uniform(-GRID_HALF+20, GRID_HALF-20)
        ez = -GRID_HALF + enemy_respawn_margin
    elif side == 2: # east (+X)
        ex = GRID_HALF - enemy_respawn_margin
        ez = random.uniform(-GRID_HALF+20, GRID_HALF-20)
    else:           # west (-X)
        ex = -GRID_HALF + enemy_respawn_margin
        ez = random.uniform(-GRID_HALF+20, GRID_HALF-20)
    return {'x': ex, 'z': ez, 'phase': random.uniform(0, math.tau), 'speed': enemy_speed_base * random.uniform(0.9,1.3)}

def reset_game():
    global player_x, player_z, player_y, player_angle, player_alive
    global bullets, bullets_missed, enemies, score, life, game_over, game_over_reason
    global cam_orbit_angle, cam_radius, cam_height, camera_mode_first_person
    global cheat_enabled, cheat_auto_follow, last_shot_time

    player_x, player_z = 0.0, 0.0
    player_y = 0.0
    player_angle = 0.0
    player_alive = True

    bullets = []
    bullets_missed = 0

    enemies = [spawn_enemy() for _ in range(NUM_ENEMIES)]

    score = 0
    life = 5
    game_over = False
    game_over_reason = ""

    cam_orbit_angle = 45.0
    cam_radius = 700.0
    cam_height = 300.0
    camera_mode_first_person = False

    cheat_enabled = False
    cheat_auto_follow = False
    last_shot_time = 0.0

# Input
keys_down = set()

def keyboardListener(key, x, y):
    global cheat_enabled, cheat_auto_follow, game_over, player_alive
    global player_angle, player_x, player_z, camera_mode_first_person
    global last_shot_time

    k = key.decode('utf-8').lower()
    if k == '\x1b':  # ESC
        glutLeaveMainLoop() if hasattr(GLUT, 'glutLeaveMainLoop') else exit(0)
        return

    if game_over:
        if k == 'r':
            reset_game()
        return

    if k == 'w':
        keys_down.add('w')
    elif k == 's':
        keys_down.add('s')
    elif k == 'a':
        keys_down.add('a')
    elif k == 'd':
        keys_down.add('d')
    elif k == 'c':
        cheat_enabled = not cheat_enabled
    elif k == 'v':
        if cheat_enabled:  # Only allow if cheat is active
            cheat_auto_follow = not cheat_auto_follow
            if cheat_auto_follow:
                camera_mode_first_person = True  # Force first-person
    elif k == 'r':
        reset_game()

def keyboardUp(key, x, y):
    k = key.decode('utf-8').lower()
    keys_down.discard(k)

def specialKeyListener(key, x, y):
    global cam_height, cam_orbit_angle
    if camera_mode_first_person:  # Disable arrow keys in first-person
        return
    if key == GLUT_KEY_UP:
        cam_height = clamp(cam_height + 10.0, 100.0, 500.0)
    elif key == GLUT_KEY_DOWN:
        cam_height = clamp(cam_height - 10.0, 100.0, 500.0)
    elif key == GLUT_KEY_LEFT:
        cam_orbit_angle -= 4.0
    elif key == GLUT_KEY_RIGHT:
        cam_orbit_angle += 4.0

def mouseListener(button, state, x, y):
    global camera_mode_first_person
    if state != GLUT_DOWN:
        return
    if button == GLUT_LEFT_BUTTON:
        fire_bullet()
    elif button == GLUT_RIGHT_BUTTON:
        camera_mode_first_person = not camera_mode_first_person

# Bullets
def fire_bullet():
    global last_shot_time
    t = now()
    if t - last_shot_time < bullet_cooldown:
        return
    last_shot_time = t

    # muzzle position
    mx = player_x + math.sin(math.radians(player_angle)) * 26
    mz = player_z + math.cos(math.radians(player_angle)) * 26
    my = 12.0
    bullets.append({'x': mx, 'y': my, 'z': mz, 'angle': player_angle, 'speed': bullet_speed})


# Update
def update_player(dt):
    global player_x, player_z, player_angle
    rot = 2.0
    if 'a' in keys_down:
        player_angle -= 2.0
    if 'd' in keys_down:
        player_angle += 2.0
    # movement along forward/back
    dx = math.sin(math.radians(player_angle))
    dz = math.cos(math.radians(player_angle))
    if 'w' in keys_down:
        player_x += dx * player_speed
        player_z += dz * player_speed
    if 's' in keys_down:
        player_x -= dx * player_speed
        player_z -= dz * player_speed
    # clamp to grid bounds
    player_x = clamp(player_x, -GRID_HALF+12, GRID_HALF-12)
    player_z = clamp(player_z, -GRID_HALF+12, GRID_HALF-12)

def update_bullets(dt):
    global bullets, bullets_missed, score
    new_bullets = []
    for b in bullets:
        dx = math.sin(math.radians(b['angle'])) * b['speed']
        dz = math.cos(math.radians(b['angle'])) * b['speed']
        b['x'] += dx
        b['z'] += dz
        # out of bounds -> miss
        if abs(b['x']) > GRID_HALF or abs(b['z']) > GRID_HALF:
            bullets_missed += 1
            continue
        # check collision with enemies
        hit = False
        for e in enemies:
            if math.sqrt(dist2(b['x'], b['z'], e['x'], e['z'])) < 12.0:
                # hit!
                hit = True
                e.clear()
                e.update(spawn_enemy())  # respawn
                score += 1
                break
        if not hit:
            new_bullets.append(b)
    bullets = new_bullets

def update_enemies(dt):
    global life, game_over, game_over_reason, player_alive
    for e in enemies:
        # move toward player
        ang = angle_to(e['x'], e['z'], player_x, player_z)
        dx = math.sin(math.radians(ang)) * e['speed']
        dz = math.cos(math.radians(ang)) * e['speed']
        e['x'] += dx
        e['z'] += dz
        # bounce anim phase
        e['phase'] += dt * 4.0
        # player collision
        if math.sqrt(dist2(e['x'], e['z'], player_x, player_z)) < enemy_touch_dist:
            # reduce life and respawn enemy
            life -= 1
            e.clear()
            e.update(spawn_enemy())
            if life <= 0:
                game_over = True
                game_over_reason = "Life reached zero"
                player_alive = False

def update_cheat(dt):
    global player_angle
    if not cheat_enabled:
        return
    # spin gun
    player_angle += cheat_spin_speed
    if player_angle >= 360.0:
        player_angle -= 360.0
    # auto-fire when any enemy is within cone
    for e in enemies:
        ang_to_enemy = angle_to(player_x, player_z, e['x'], e['z'])
        if abs(wrap_angle(ang_to_enemy - player_angle)) <= cheat_fire_cone:
            fire_bullet()
            break

def update_game_over():
    global game_over, game_over_reason, player_alive
    if bullets_missed >= 10 and not game_over:
        game_over = True
        game_over_reason = "Bullets missed reached 10"
        player_alive = False

def idle():
    global prev_time
    t = now()
    dt = t - prev_time
    prev_time = t

    if not game_over:
        update_player(dt)
        update_bullets(dt)
        update_enemies(dt)
        update_cheat(dt)
        update_game_over()

    glutPostRedisplay()

# Camera & Projection
def set_perspective():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = max(1.0, WINDOW_W / float(max(1, WINDOW_H)))
    gluPerspective(70.0, aspect, 1.0, 3000.0)
    glMatrixMode(GL_MODELVIEW)

def setup_camera():
    glLoadIdentity()
    if camera_mode_first_person:
        # camera at player's head, looking along player_angle
        eye_x = player_x
        eye_y = 30.0
        eye_z = player_z
        la_x = eye_x + math.sin(math.radians(player_angle)) * 50.0
        la_y = 25.0
        la_z = eye_z + math.cos(math.radians(player_angle)) * 50.0
        gluLookAt(eye_x, eye_y, eye_z, la_x, la_y, la_z, 0,1,0)
    else:
        # orbit camera around center
        cx = math.sin(math.radians(cam_orbit_angle)) * cam_radius
        cz = math.cos(math.radians(cam_orbit_angle)) * cam_radius
        gluLookAt(cx, cam_height, cz, 0, 0, 0, 0, 1, 0)

# Lighting
def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(400.0, 600.0, 400.0, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (GLfloat * 4)(0.2, 0.2, 0.2, 1.0))
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

# Display
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)

    set_perspective()
    setup_camera()
    setup_lighting()

    # draw world
    draw_grid_and_bounds()

    # enemies
    for e in enemies:
        anim = 1.0 + 0.15 * math.sin(e['phase'])
        draw_enemy(e['x'], e['z'], anim)

    # player & bullets
    draw_player()
    glColor3f(1,1,0)
    for b in bullets:
        draw_bullet(b)

    # HUD
    glDisable(GL_LIGHTING)
    draw_text_2d(15, WINDOW_H - 30, f"Score: {score}   Life: {life}   Missed: {bullets_missed}")
    mode_txt = "FP" if camera_mode_first_person else "TP"
    cheat_txt = "ON" if cheat_enabled else "OFF"
    draw_text_2d(15, WINDOW_H - 55, f"Camera: {mode_txt}   Cheat: {cheat_txt}   [W/S move, A/D rotate, Mouse: LMB shoot, RMB camera, C cheat, V follow, Arrows camera, R reset]")
    if game_over:
        draw_text_2d(WINDOW_W/2 - 110, WINDOW_H/2 + 10, "GAME OVER")
        draw_text_2d(WINDOW_W/2 - 220, WINDOW_H/2 - 20, f"{game_over_reason}. Press R to restart.")
    glEnable(GL_LIGHTING)

    glutSwapBuffers()

def reshape(w, h):
    global WINDOW_W, WINDOW_H
    WINDOW_W, WINDOW_H = max(1, w), max(1, h)
    glViewport(0, 0, WINDOW_W, WINDOW_H)

def init():
    glClearColor(0.05, 0.05, 0.07, 1.0)
    glEnable(GL_DEPTH_TEST)
    reset_game()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"Bullet Frenzy - CSE423 Lab 03")

    init()

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUp)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    # IMPORTANT: per assignment, do not use glutTimerFunc; we use idle for updates.
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()