import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Region codes for Cohen-Sutherland algorithm
INSIDE = 0  # 0000
LEFT = 1    # 0001
RIGHT = 2   # 0010
BOTTOM = 4  # 0100
TOP = 8     # 1000

class LineClipping:
    def __init__(self):
        self.clip_window = {'xmin': -0.5, 'ymin': -0.5, 'xmax': 0.5, 'ymax': 0.5}
        self.lines = []
        self.current_line = None
        self.dragging_corner = None
        self.mode = 'draw_line'  # 'draw_line' or 'resize_window'
        
    def compute_code(self, x, y):
        """Compute region code for a point(x,y)"""
        code = INSIDE
        if x < self.clip_window['xmin']:
            code |= LEFT
        elif x > self.clip_window['xmax']:
            code |= RIGHT
        if y < self.clip_window['ymin']:
            code |= BOTTOM
        elif y > self.clip_window['ymax']:
            code |= TOP
        return code
    
    def cohen_sutherland_clip(self, x1, y1, x2, y2):
        """Cohen-Sutherland line clipping algorithm"""
        code1 = self.compute_code(x1, y1)
        code2 = self.compute_code(x2, y2)
        accept = False
        
        while True:
            # Both endpoints inside
            if code1 == 0 and code2 == 0:
                accept = True
                break
            # Both endpoints in same outside region
            elif (code1 & code2) != 0:
                break
            else:
                # Line needs clipping
                x, y = 0.0, 0.0
                # Pick an outside point
                code_out = code1 if code1 != 0 else code2
                
                # Find intersection point
                if code_out & TOP:
                    x = x1 + (x2 - x1) * (self.clip_window['ymax'] - y1) / (y2 - y1)
                    y = self.clip_window['ymax']
                elif code_out & BOTTOM:
                    x = x1 + (x2 - x1) * (self.clip_window['ymin'] - y1) / (y2 - y1)
                    y = self.clip_window['ymin']
                elif code_out & RIGHT:
                    y = y1 + (y2 - y1) * (self.clip_window['xmax'] - x1) / (x2 - x1)
                    x = self.clip_window['xmax']
                elif code_out & LEFT:
                    y = y1 + (y2 - y1) * (self.clip_window['xmin'] - x1) / (x2 - x1)
                    x = self.clip_window['xmin']
                
                # Replace outside point with intersection point
                if code_out == code1:
                    x1, y1 = x, y
                    code1 = self.compute_code(x1, y1)
                else:
                    x2, y2 = x, y
                    code2 = self.compute_code(x2, y2)
        
        if accept:
            return (x1, y1, x2, y2, True)
        else:
            return (x1, y1, x2, y2, False)
    
    def draw_grid_and_window(self):
        """Draw the clipping window and extended grid lines"""
        xmin, xmax = self.clip_window['xmin'], self.clip_window['xmax']
        ymin, ymax = self.clip_window['ymin'], self.clip_window['ymax']
        
        # Draw extended grid lines (black, thin)
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(2)
        
        # Vertical lines
        glBegin(GL_LINES)
        # Left vertical line
        glVertex2f(xmin, -1.0)
        glVertex2f(xmin, 1.0)
        # Right vertical line
        glVertex2f(xmax, -1.0)
        glVertex2f(xmax, 1.0)
        glEnd()
        
        # Horizontal lines
        glBegin(GL_LINES)
        # Bottom horizontal line
        glVertex2f(-1.0, ymin)
        glVertex2f(1.0, ymin)
        # Top horizontal line
        glVertex2f(-1.0, ymax)
        glVertex2f(1.0, ymax)
        glEnd()
        
        # Draw clipping window (blue, thicker)
        glColor3f(0.0, 0.0, 1.0)
        glLineWidth(4)
        glBegin(GL_LINE_LOOP)
        glVertex2f(xmin, ymin)
        glVertex2f(xmax, ymin)
        glVertex2f(xmax, ymax)
        glVertex2f(xmin, ymax)
        glEnd()
        
        # Draw corner handles (yellow, only in resize mode)
        if self.mode == 'resize_window':
            glPointSize(10)
            glColor3f(1.0, 1.0, 0.0)
            glBegin(GL_POINTS)
            glVertex2f(xmin, ymin)
            glVertex2f(xmax, ymin)
            glVertex2f(xmax, ymax)
            glVertex2f(xmin, ymax)
            glEnd()
    
    def render(self):
        """Render all elements"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Draw grid and clipping window first
        self.draw_grid_and_window()
        
        # Draw all original lines (red, semi-transparent)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for line in self.lines:
            x1, y1, x2, y2 = line
            glColor4f(1.0, 0.0, 0.0, 0.6)
            glLineWidth(2)
            glBegin(GL_LINES)
            glVertex2f(x1, y1)
            glVertex2f(x2, y2)
            glEnd()
        
        # Draw clipped portions (green, thick)
        for line in self.lines:
            x1, y1, x2, y2 = line
            cx1, cy1, cx2, cy2, visible = self.cohen_sutherland_clip(x1, y1, x2, y2)
            if visible:
                glColor3f(0.0, 0.8, 0.0)
                glLineWidth(5)
                glBegin(GL_LINES)
                glVertex2f(cx1, cy1)
                glVertex2f(cx2, cy2)
                glEnd()
        
        # Draw current line being drawn (yellow preview)
        if self.current_line:
            x1, y1, x2, y2 = self.current_line
            glColor3f(1.0, 1.0, 0.0)
            glLineWidth(3)
            glBegin(GL_LINES)
            glVertex2f(x1, y1)
            glVertex2f(x2, y2)
            glEnd()
            
            # Show endpoints
            glPointSize(8)
            glBegin(GL_POINTS)
            glVertex2f(x1, y1)
            glVertex2f(x2, y2)
            glEnd()

def screen_to_world(x, y, width, height):
    """Convert screen coordinates to world coordinates"""
    world_x = (x / width) * 2 - 1
    world_y = 1 - (y / height) * 2
    return world_x, world_y

def world_to_screen(x, y, width, height):
    """Convert world coordinates to screen coordinates"""
    screen_x = int((x + 1) * width / 2)
    screen_y = int((1 - y) * height / 2)
    return screen_x, screen_y

def draw_region_codes(screen, clipper, display):
    """Draw region codes using Pygame on the display"""
    font = pygame.font.Font(None, 36)
    
    xmin, xmax = clipper.clip_window['xmin'], clipper.clip_window['xmax']
    ymin, ymax = clipper.clip_window['ymin'], clipper.clip_window['ymax']
    
    # Calculate center positions for each region (in world coordinates)
    x_left = (xmin - 1.0) / 2
    x_center = (xmin + xmax) / 2
    x_right = (xmax + 1.0) / 2
    
    y_top = (ymax + 1.0) / 2
    y_center = (ymin + ymax) / 2
    y_bottom = (ymin - 1.0) / 2
    
    # Region codes and their positions
    regions = [
        ("1001", x_left, y_top),      # Top-Left
        ("1000", x_center, y_top),    # Top
        ("1010", x_right, y_top),     # Top-Right
        ("0001", x_left, y_center),   # Left
        ("0000", x_center, y_center), # Center (Inside)
        ("0010", x_right, y_center),  # Right
        ("0101", x_left, y_bottom),   # Bottom-Left
        ("0100", x_center, y_bottom), # Bottom
        ("0110", x_right, y_bottom),  # Bottom-Right
    ]
    
    for code, wx, wy in regions:
        sx, sy = world_to_screen(wx, wy, display[0], display[1])
        text_surface = font.render(code, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(sx, sy))
        screen.blit(text_surface, text_rect)

def main():
    try:
        # Initialize Pygame
        pygame.init()
        display = (1000, 700)
        
        # Create window with OpenGL context
        screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Cohen-Sutherland Line Clipping Algorithm")
        
        # Setup OpenGL viewport and projection
        glViewport(0, 0, display[0], display[1])
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Set background color to white
        glClearColor(1.0, 1.0, 1.0, 1.0)
        
        # Enable antialiasing
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_POINT_SMOOTH)
        
        clipper = LineClipping()
        clock = pygame.time.Clock()
        running = True
        drawing = False
        start_pos = None
        
        # Create a surface for 2D overlay
        overlay = pygame.Surface(display, pygame.SRCALPHA)
        
        print("\n" + "="*60)
        print("COHEN-SUTHERLAND LINE CLIPPING ALGORITHM")
        print("="*60)
        print("\n📋 CONTROLS:")
        print("  ➤ Left Click & Drag   : Draw a line")
        print("  ➤ Right Click         : Toggle Draw/Resize mode")
        print("  ➤ C Key              : Clear all lines")
        print("  ➤ R Key              : Reset clipping window")
        print("  ➤ I Key              : Input line coordinates")
        print("  ➤ ESC Key            : Exit")
        print("\n📊 REGION CODES:")
        print("  • 0000 = Inside (center)")
        print("  • 0001 = Left,  0010 = Right")
        print("  • 0100 = Bottom, 1000 = Top")
        print("  • Other codes = Combinations (corners)")
        print("\n🎨 VISUAL GUIDE:")
        print("  • Yellow line: Preview (while drawing)")
        print("  • Red line: Original line")
        print("  • Green line: Clipped visible portion")
        print("  • Blue rectangle: Clipping window")
        print("  • Black lines: Extended grid")
        print("\n✨ Ready! Start drawing lines...\n")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    print("\n👋 Exiting program...")
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        print("\n👋 Exiting program...")
                    elif event.key == pygame.K_c:
                        clipper.lines = []
                        print("🗑️  All lines cleared")
                    elif event.key == pygame.K_r:
                        clipper.clip_window = {'xmin': -0.5, 'ymin': -0.5, 'xmax': 0.5, 'ymax': 0.5}
                        print("🔄 Clipping window reset to default")
                    elif event.key == pygame.K_i:
                        # Input line coordinates from console
                        print("\n" + "="*50)
                        print("INPUT LINE COORDINATES")
                        print("Enter coordinates in range [-1, 1]")
                        print("="*50)
                        try:
                            x1 = float(input("Enter x1: "))
                            y1 = float(input("Enter y1: "))
                            x2 = float(input("Enter x2: "))
                            y2 = float(input("Enter y2: "))
                            
                            line = (x1, y1, x2, y2)
                            clipper.lines.append(line)
                            
                            # Check if line is inside/outside
                            _, _, _, _, visible = clipper.cohen_sutherland_clip(*line)
                            if visible:
                                print(f"✅ Line ({x1:.2f},{y1:.2f}) to ({x2:.2f},{y2:.2f}): VISIBLE")
                            else:
                                print(f"❌ Line ({x1:.2f},{y1:.2f}) to ({x2:.2f},{y2:.2f}): COMPLETELY OUTSIDE")
                        except ValueError:
                            print("❌ Invalid input! Please enter numbers.")
                        print("="*50 + "\n")
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mx, my = pygame.mouse.get_pos()
                        world_x, world_y = screen_to_world(mx, my, display[0], display[1])
                        
                        if clipper.mode == 'draw_line':
                            drawing = True
                            start_pos = (world_x, world_y)
                        elif clipper.mode == 'resize_window':
                            # Check if clicking on a corner
                            threshold = 0.05
                            corners = [
                                ('xmin', 'ymin'), ('xmax', 'ymin'),
                                ('xmax', 'ymax'), ('xmin', 'ymax')
                            ]
                            for cx, cy in corners:
                                dist = ((clipper.clip_window[cx] - world_x)**2 + 
                                       (clipper.clip_window[cy] - world_y)**2)**0.5
                                if dist < threshold:
                                    clipper.dragging_corner = (cx, cy)
                                    print("📌 Dragging corner...")
                                    break
                    
                    elif event.button == 3:  # Right click
                        if clipper.mode == 'draw_line':
                            clipper.mode = 'resize_window'
                            print("🔧 Mode: RESIZE WINDOW (drag yellow corner handles)")
                        else:
                            clipper.mode = 'draw_line'
                            print("✏️  Mode: DRAW LINE")
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if drawing and start_pos:
                            mx, my = pygame.mouse.get_pos()
                            world_x, world_y = screen_to_world(mx, my, display[0], display[1])
                            line = (start_pos[0], start_pos[1], world_x, world_y)
                            clipper.lines.append(line)
                            
                            # Check if line is inside/outside
                            _, _, _, _, visible = clipper.cohen_sutherland_clip(*line)
                            if visible:
                                print(f"✅ Line added: VISIBLE (inside or intersecting)")
                            else:
                                print(f"❌ Line added: COMPLETELY OUTSIDE")
                            
                            drawing = False
                            start_pos = None
                            clipper.current_line = None
                        
                        clipper.dragging_corner = None
                
                elif event.type == pygame.MOUSEMOTION:
                    mx, my = pygame.mouse.get_pos()
                    world_x, world_y = screen_to_world(mx, my, display[0], display[1])
                    
                    if drawing and start_pos:
                        clipper.current_line = (start_pos[0], start_pos[1], world_x, world_y)
                    
                    if clipper.dragging_corner:
                        cx, cy = clipper.dragging_corner
                        clipper.clip_window[cx] = world_x
                        clipper.clip_window[cy] = world_y
            
            # Render OpenGL scene
            clipper.render()
            
            # Read pixels from OpenGL buffer
            glReadBuffer(GL_BACK)
            pixels = glReadPixels(0, 0, display[0], display[1], GL_RGB, GL_UNSIGNED_BYTE)
            gl_surface = pygame.image.fromstring(pixels, display, "RGB")
            gl_surface = pygame.transform.flip(gl_surface, False, True)
            
            # Create a new screen surface and draw everything
            screen = pygame.display.get_surface()
            screen.blit(gl_surface, (0, 0))
            
            # Draw region codes on top using Pygame
            draw_region_codes(screen, clipper, display)
            
            # Update display
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        print("✅ Program closed successfully\n")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Make sure you have installed: pip install pygame PyOpenGL")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()