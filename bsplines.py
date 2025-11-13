import glfw
from OpenGL.GL import *
import numpy as np

# ----------------- Helper: B-spline Basis Function -----------------
def bspline_basis(i, k, t, knot):
    """Recursive definition of B-spline basis function"""
    if k == 0:
        return 1.0 if knot[i] <= t < knot[i + 1] else 0.0
    else:
        left = 0.0
        right = 0.0
        if knot[i + k] - knot[i] != 0:
            left = ((t - knot[i]) / (knot[i + k] - knot[i])) * bspline_basis(i, k - 1, t, knot)
        if knot[i + k + 1] - knot[i + 1] != 0:
            right = ((knot[i + k + 1] - t) / (knot[i + k + 1] - knot[i + 1])) * bspline_basis(i + 1, k - 1, t, knot)
        return left + right

# ----------------- Generate B-spline Curve Points -----------------
def bspline_curve(control_points, degree=3, num_points=100):
    n = len(control_points) - 1
    k = degree
    m = n + k + 1  # number of knots
    # Uniform knot vector
    knot = np.linspace(0, 1, m + 1)
    
    t_values = np.linspace(knot[k], knot[n + 1], num_points)
    curve = []
    for t in t_values:
        x = y = 0
        for i in range(n + 1):
            coeff = bspline_basis(i, k, t, knot)
            x += coeff * control_points[i][0]
            y += coeff * control_points[i][1]
        curve.append((x, y))
    return curve

# ----------------- OpenGL Display -----------------
control_points = []
degree = 3  # Default cubic

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    
    # Draw control points
    glPointSize(8)
    glColor3f(1, 0, 0)
    glBegin(GL_POINTS)
    for p in control_points:
        glVertex2f(p[0], p[1])
    glEnd()

    # Draw control polygon
    if len(control_points) > 1:
        glColor3f(0.6, 0.6, 0.6)
        glBegin(GL_LINE_STRIP)
        for p in control_points:
            glVertex2f(p[0], p[1])
        glEnd()

    # Draw B-spline curve
    if len(control_points) > degree:
        curve = bspline_curve(control_points, degree)
        glColor3f(0, 1, 0)
        glBegin(GL_LINE_STRIP)
        for p in curve:
            glVertex2f(p[0], p[1])
        glEnd()

# ----------------- Input Handling -----------------
def mouse_button(window, button, action, mods):
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        x, y = glfw.get_cursor_pos(window)
        w, h = glfw.get_window_size(window)
        # Normalize to [-1, 1]
        x = (x / w) * 2 - 1
        y = -((y / h) * 2 - 1)
        control_points.append((x, y))

def key_callback(window, key, scancode, action, mods):
    global degree
    if action == glfw.PRESS:
        if key == glfw.KEY_C:
            control_points.clear()
        elif key in [glfw.KEY_1, glfw.KEY_2, glfw.KEY_3, glfw.KEY_4]:
            degree = int(chr(key))  # 1, 2, 3, 4
            print(f"Degree changed to {degree}")

# ----------------- Main -----------------
def main():
    if not glfw.init():
        return
    window = glfw.create_window(800, 600, "B-Spline Curve (Press 1–4 to change degree, C to clear)", None, None)
    glfw.make_context_current(window)
    glfw.set_mouse_button_callback(window, mouse_button)
    glfw.set_key_callback(window, key_callback)
    
    glClearColor(0, 0, 0, 1)
    
    while not glfw.window_should_close(window):
        display()
        glfw.swap_buffers(window)
        glfw.poll_events()
    
    glfw.terminate()

if __name__ == "__main__":
    main()
