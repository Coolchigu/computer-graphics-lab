import pygame
from pygame.locals import *
from OpenGL.GL import *
import numpy as np


# Function to compute B-spline curve using De Boor's algorithm
def bspline(control_points, degree=3, num_points=200):
    n = len(control_points) - 1
    if n < degree:
        return np.array([])  # Not enough points for the curve

    k = degree
    m = n + k + 1

    # Uniform knot vector
    knots = np.array([0] * (k + 1) + list(range(1, m - 2 * k)) + [m - 2 * k] * (k + 1), dtype=float)
    knots = knots / max(knots)

    def de_boor(k, x, t, c):
        n = len(c) - 1
        # Find knot span
        for i in range(n + k + 1):
            if t[i] <= x < t[i + 1]:
                break
        else:
            i = n
        d = [c[j + i - k] for j in range(0, k + 1)]
        for r in range(1, k + 1):
            for j in range(k, r - 1, -1):
                alpha = (x - t[j + i - k]) / (t[j + 1 + i - r] - t[j + i - k])
                d[j] = (1.0 - alpha) * np.array(d[j - 1]) + alpha * np.array(d[j])
        return d[k]

    u = np.linspace(0, 1, num_points)
    curve = np.array([de_boor(k, x, knots, control_points) for x in u])
    return curve


def draw_text(x, y, text, color=(1, 1, 1)):
    """Draw simple text using OpenGL raster functions."""
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter = getattr(pygame, 'GLUT_BITMAP_HELVETICA_18', None)
        if glutBitmapCharacter:
            glutBitmapCharacter(ch)
        else:
            # Fallback: render using pygame.font
            font = pygame.font.SysFont("Arial", 18)
            surface = font.render(text, True, (255, 255, 255))
            data = pygame.image.tostring(surface, "RGBA", True)
            glDrawPixels(surface.get_width(), surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)
            break


def main():
    # Initialize Pygame and OpenGL
    pygame.init()
    display = (900, 700)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Interactive B-Spline Curve (No GLUT)")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)

    control_points = []
    degree = 3  # Cubic B-spline

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click → Add control point
                    x, y = event.pos
                    control_points.append([x, display[1] - y, 0])  # Flip y-axis for OpenGL coords

            elif event.type == KEYDOWN:
                if event.key == K_c:
                    control_points.clear()  # Clear control points
                elif event.key == K_ESCAPE:
                    running = False

        # Draw
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # Draw control polygon
        glColor3f(1, 0, 0)
        glBegin(GL_LINE_STRIP)
        for p in control_points:
            glVertex3fv(p)
        glEnd()

        # Draw control points
        glPointSize(6)
        glColor3f(1, 1, 0)
        glBegin(GL_POINTS)
        for p in control_points:
            glVertex3fv(p)
        glEnd()

        # Draw B-Spline curve if enough points
        if len(control_points) > degree:
            curve_points = bspline(np.array(control_points), degree=degree)
            glColor3f(0, 1, 0)
            glBegin(GL_LINE_STRIP)
            for p in curve_points:
                glVertex3fv(p)
            glEnd()

        # Display instructions
        font = pygame.font.SysFont("Consolas", 18)
        instructions = [
            "Left Click: Add control point",
            "C: Clear points",
            "ESC: Exit",
        ]
        for i, text in enumerate(instructions):
            text_surface = font.render(text, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            glWindowPos2d(10, display[1] - 25 - i * 25)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        pygame.display.flip()
        pygame.time.wait(15)

    pygame.quit()


if __name__ == "__main__":
    main()
