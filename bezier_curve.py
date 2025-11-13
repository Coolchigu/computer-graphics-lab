from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
import math

WIN_W, WIN_H = 1000, 700
control_points = []    # list of (x,y)
dragging_index = None
show_polygon = True

POINT_RADIUS = 6.0
CURVE_RESOLUTION = 400  # number of samples along t (increase for smoother curve)

def to_opengl_y(y):
    return WIN_H - y

def distance_sq(a, b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2

def bezier_point(ctrl_pts, t):
    """Compute a point on Bezier curve at parameter t using de Casteljau (iterative)."""
    # Make a local copy of points as floats
    pts = [(float(x), float(y)) for (x,y) in ctrl_pts]
    n = len(pts)
    if n == 0:
        return None
    # de Casteljau iterative reduction
    for r in range(1, n):
        for i in range(n - r):
            x = (1 - t) * pts[i][0] + t * pts[i+1][0]
            y = (1 - t) * pts[i][1] + t * pts[i+1][1]
            pts[i] = (x, y)
    return pts[0]

def draw_circle(x, y, radius):
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    steps = 20
    for i in range(steps+1):
        theta = 2.0 * math.pi * i / steps
        glVertex2f(x + math.cos(theta) * radius, y + math.sin(theta) * radius)
    glEnd()

def display_text(x, y, text):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Draw control polygon
    if show_polygon and len(control_points) >= 2:
        glLineWidth(1.5)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_LINE_STRIP)
        for (x,y) in control_points:
            glVertex2f(x, y)
        glEnd()

    # Draw Bezier curve if at least 2 points
    if len(control_points) >= 2:
        glLineWidth(3.0)
        glColor3f(0.2, 1.0, 0.2)  # green curve
        glBegin(GL_LINE_STRIP)
        for i in range(CURVE_RESOLUTION + 1):
            t = i / CURVE_RESOLUTION
            p = bezier_point(control_points, t)
            if p is not None:
                glVertex2f(p[0], p[1])
        glEnd()

    # Draw control points
    for idx, (x,y) in enumerate(control_points):
        # point fill
        if idx == dragging_index:
            glColor3f(1.0, 0.8, 0.2)  # highlighted
        else:
            glColor3f(1.0, 0.2, 0.2)
        draw_circle(x, y, POINT_RADIUS)
        # outline
        glLineWidth(1.0)
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_LINE_LOOP)
        steps = 20
        for i in range(steps):
            theta = 2.0 * math.pi * i / steps
            glVertex2f(x + math.cos(theta) * POINT_RADIUS, y + math.sin(theta) * POINT_RADIUS)
        glEnd()

    # Instructions
    glColor3f(0.9, 0.9, 0.8)
    display_text(10, WIN_H - 20, "Left-click: add/mouse-drag point | Right-click: remove nearest point | 's' toggle control polygon | 'c' clear | 'q' quit")

    glutSwapBuffers()

def reshape(w, h):
    global WIN_W, WIN_H
    WIN_W, WIN_H = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w, 0, h, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def find_nearest_point(x, y, max_dist=20.0):
    """Return index of nearest control point to (x,y) or None"""
    best = None
    best_d2 = max_dist * max_dist
    for i, p in enumerate(control_points):
        d2 = distance_sq(p, (x,y))
        if d2 < best_d2:
            best_d2 = d2
            best = i
    return best

def mouse(button, state, x, y):
    global dragging_index
    gl_y = to_opengl_y(y)
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        idx = find_nearest_point(x, gl_y)
        if idx is not None:
            # start dragging existing point
            dragging_index = idx
        else:
            # add new control point
            control_points.append((x, gl_y))
        glutPostRedisplay()
    elif button == GLUT_LEFT_BUTTON and state == GLUT_UP:
        dragging_index = None
        glutPostRedisplay()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        # remove nearest point
        idx = find_nearest_point(x, gl_y)
        if idx is not None:
            control_points.pop(idx)
            print(f"Removed control point {idx}")
        glutPostRedisplay()

def motion(x, y):
    global dragging_index
    if dragging_index is not None:
        gl_y = to_opengl_y(y)
        control_points[dragging_index] = (x, gl_y)
        glutPostRedisplay()

def keyboard(key, x, y):
    ch = key.decode('utf-8') if isinstance(key, bytes) else key
    global show_polygon
    if ch in ('c', 'r', 'C', 'R'):
        control_points.clear()
        print("Cleared control points.")
        glutPostRedisplay()
    elif ch in ('s', 'S'):
        show_polygon = not show_polygon
        glutPostRedisplay()
    elif ch == 'q' or ch == '\x1b':
        print("Exiting.")
        sys.exit(0)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Bezier Curve Demo - de Casteljau (PyOpenGL + GLUT)")
    glClearColor(0.08, 0.08, 0.1, 1.0)
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutKeyboardFunc(keyboard)
    print("Bezier Curve Demo ready. Left-click to add points. Drag to move. Right-click to remove. 'c' clear, 's' toggle polygon, 'q' quit.")
    glutMainLoop()

if __name__ == "__main__":
    main()
