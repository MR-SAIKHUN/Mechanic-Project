import pygame
import sys
import random
import math
import logging
from datetime import datetime

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (200, 200, 0)
PURPLE = (128, 0, 128)
GRAY = (200, 200, 200)

# Set up logging
logging.basicConfig(
    filename=f'simulation_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Set up the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("RESULTANT OF MOMENT AND ROTATION (MOVED PIVOT)")


clock = pygame.time.Clock()

class Background:
    def __init__(self):
        self.surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.surface.fill(WHITE)
        self.draw_grid()
        self.draw_scale()

    def draw_grid(self):
        # Draw vertical lines
        for x in range(0, WINDOW_WIDTH, 50):
            pygame.draw.line(self.surface, GRAY, (x, 0), (x, WINDOW_HEIGHT), 1)
        # Draw horizontal lines
        for y in range(0, WINDOW_HEIGHT, 50):
            pygame.draw.line(self.surface, GRAY, (0, y), (WINDOW_WIDTH, y), 1)

    def draw_scale(self):
        # Draw scale markers
        font = pygame.font.Font(None, 20)
        # X-axis scale
        for x in range(0, WINDOW_WIDTH, 100):
            text = font.render(str(x), True, BLACK)
            self.surface.blit(text, (x, WINDOW_HEIGHT - 20))
        # Y-axis scale
        for y in range(0, WINDOW_HEIGHT, 100):
            text = font.render(str(y), True, BLACK)
            self.surface.blit(text, (5, y))

    def draw(self, surface):
        surface.blit(self.surface, (0, 0))

class CompositeObject(pygame.sprite.Sprite):
    def __init__(self, shape_type="default"):
        super().__init__()
        # Random size between 10% and 30% of window size
        size_percentage = random.uniform(0.1, 0.3)
        self.width = int(WINDOW_WIDTH * size_percentage)
        self.height = int(WINDOW_HEIGHT * size_percentage)
        
        # Create composite shape based on shape type
        self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.shape_type = shape_type
        
        if shape_type == "default":
            # Rectangle with triangle on top
            pygame.draw.rect(self.original_image, BLUE, (0, self.height//2, self.width, self.height//2))
            pygame.draw.polygon(self.original_image, BLUE, [
                (0, self.height//2),
                (self.width//2, 0),
                (self.width, self.height//2)
            ])
        elif shape_type == "circle":
            # Circle
            pygame.draw.circle(self.original_image, BLUE, (self.width//2, self.height//2), min(self.width, self.height)//2)
        elif shape_type == "square":
            # Square
            pygame.draw.rect(self.original_image, BLUE, (0, 0, self.width, self.height))
        elif shape_type == "triangle":
            # Triangle
            pygame.draw.polygon(self.original_image, BLUE, [
                (0, self.height),
                (self.width//2, 0),
                (self.width, self.height)
            ])
        
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
        
        # Initialize forces and moments
        self.initial_forces = []
        self.manual_force = None
        self.resultant_force = [0, 0]
        self.resultant_moment = 0
        self.velocity = [0, 0]
        
        # Random initial pivot point within object
        self.pivot_point = (
            random.randint(self.rect.left, self.rect.right),
            random.randint(self.rect.top, self.rect.bottom)
        )
        
        # Random initial rotation
        self.angle = random.randint(0, 360)
        self.rotate(self.angle)
        
        # Generate initial forces
        num_forces = random.randint(4, 6)
        for _ in range(num_forces):
            force = {
                'magnitude': random.uniform(300, 1000),
                'direction': random.uniform(0, 2 * math.pi),
                'position': (
                    random.randint(self.rect.left, self.rect.right),
                    random.randint(self.rect.top, self.rect.bottom)
                )
            }
            self.initial_forces.append(force)
            self.calculate_resultant_force()
        
        # Generate initial moment
        self.initial_moment = random.uniform(1500, 2500)
        self.current_moment = self.initial_moment
        self.moment_direction = random.choice([-1, 1])
        
        # Store initial state for undo
        self.initial_state = {
            'position': self.rect.center,
            'angle': self.angle,
            'pivot_point': self.pivot_point,
            'velocity': [0, 0],
            'resultant_force': self.resultant_force.copy(),
            'current_moment': self.current_moment
        }
        
        logging.info(f"Object created with shape type: {shape_type}, {num_forces} initial forces and moment of {self.initial_moment}")

    def rotate(self, angle):
        self.angle += angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pivot_point)

    def calculate_resultant_force(self):
        self.resultant_force = [0, 0]
        for force in self.initial_forces:
            # Ensure force magnitude is within range
            magnitude = max(300, min(1000, force['magnitude']))
            fx = magnitude * math.cos(force['direction'])
            fy = magnitude * math.sin(force['direction'])
            self.resultant_force[0] += fx
            self.resultant_force[1] += fy

    def apply_manual_force(self, force):
        # Validate force magnitude
        magnitude = math.sqrt(force[0]**2 + force[1]**2)
        if magnitude < 300:
            # Scale up to minimum
            scale = 300 / magnitude
            force = [force[0] * scale, force[1] * scale]
        elif magnitude > 1000:
            # Scale down to maximum
            scale = 1000 / magnitude
            force = [force[0] * scale, force[1] * scale]
        
        self.manual_force = force
        self.calculate_resultant_force()
        logging.info(f"Manual force applied: {force}")

    def update(self):
        # Update position based on resultant force
        self.velocity[0] += self.resultant_force[0] * 0.01
        self.velocity[1] += self.resultant_force[1] * 0.01
        
        # Calculate new position
        new_x = self.rect.x + self.velocity[0]
        new_y = self.rect.y + self.velocity[1]
        
        # Boundary constraints
        # Left boundary
        if new_x < 0:
            new_x = 0
            self.velocity[0] = -self.velocity[0] * 0.8  # Bounce with energy loss
        # Right boundary
        if new_x + self.rect.width > WINDOW_WIDTH:
            new_x = WINDOW_WIDTH - self.rect.width
            self.velocity[0] = -self.velocity[0] * 0.8
        # Top boundary
        if new_y < 0:
            new_y = 0
            self.velocity[1] = -self.velocity[1] * 0.8
        # Bottom boundary
        if new_y + self.rect.height > WINDOW_HEIGHT:
            new_y = WINDOW_HEIGHT - self.rect.height
            self.velocity[1] = -self.velocity[1] * 0.8
        
        # Apply the constrained position
        self.rect.x = new_x
        self.rect.y = new_y
        self.pivot_point = (self.rect.centerx, self.rect.centery)
        
        # Update rotation based on moment
        self.rotate(self.current_moment * self.moment_direction * 0.01)
        
        # Add friction to slow down movement
        self.velocity[0] *= 0.99
        self.velocity[1] *= 0.99

    def undo(self):
        # Reset to initial state
        self.rect.center = self.initial_state['position']
        self.angle = self.initial_state['angle']
        self.pivot_point = self.initial_state['pivot_point']
        self.velocity = self.initial_state['velocity'].copy()
        self.resultant_force = self.initial_state['resultant_force'].copy()
        self.current_moment = self.initial_state['current_moment']
        self.manual_force = None
        
        # Update visual representation
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pivot_point)
        
        logging.info("Object state reset to initial state")

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, 36)
        self.is_hovered = False

    def draw(self, surface):
        color = (min(self.color[0] + 50, 255), min(self.color[1] + 50, 255), min(self.color[2] + 50, 255)) if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class StatusWindow:
    def __init__(self, x, y, width, height, title):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.font = pygame.font.Font(None, 24)
        self.value = 0
        self.color = GREEN
        self.direction = 0  # For moment direction display

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # Draw title
        title_surface = self.font.render(self.title, True, BLACK)
        surface.blit(title_surface, (self.rect.x + 5, self.rect.y + 5))
        
        # Draw value with appropriate color
        value_surface = self.font.render(f"{self.value:.2f}", True, self.color)
        surface.blit(value_surface, (self.rect.x + 5, self.rect.y + 30))
        
        # Draw direction for moment window
        if "Moment" in self.title:
            direction_text = "Clockwise" if self.direction > 0 else "Counter-clockwise"
            direction_surface = self.font.render(direction_text, True, BLACK)
            surface.blit(direction_surface, (self.rect.x + 5, self.rect.y + 55))

class Notification:
    def __init__(self, message, color, duration=2, position="top"):
        self.message = message
        self.color = color
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 24)
        self.is_active = True
        self.alpha = 255
        self.fade_speed = 2
        self.padding = 10
        self.bottom_padding = 70  # Align with buttons at WINDOW_HEIGHT - 70
        self.position = position  # "top" or "bottom"

    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        if elapsed > (self.duration - 0.5) * 1000:
            self.alpha = max(0, self.alpha - self.fade_speed)
        
        if elapsed > self.duration * 1000:
            self.is_active = False

    def draw(self, surface):
        if self.is_active:
            text_surface = self.font.render(self.message, True, self.color)
            text_surface.set_alpha(self.alpha)
            text_rect = text_surface.get_rect()
            
            # Position text based on notification type
            if self.position == "top":
                text_rect.topright = (WINDOW_WIDTH - self.padding, self.padding)
            else:  # bottom
                text_rect.bottomright = (WINDOW_WIDTH - self.padding, WINDOW_HEIGHT - self.bottom_padding)
            
            surface.blit(text_surface, text_rect)

# Create game objects
background = Background()
object = CompositeObject()
all_sprites = pygame.sprite.Group(object)

# Create buttons
buttons = {
    'start': Button(20, WINDOW_HEIGHT - 70, 100, 40, "Start", GREEN),
    'stop': Button(130, WINDOW_HEIGHT - 70, 100, 40, "Stop", RED),
    'undo': Button(240, WINDOW_HEIGHT - 70, 100, 40, "Undo", BLUE),
    'reset': Button(350, WINDOW_HEIGHT - 70, 100, 40, "Reset", YELLOW),
    'shape': Button(460, WINDOW_HEIGHT - 70, 100, 40, "Shape", PURPLE)
}

# Create status windows
status_windows = {
    'force': StatusWindow(10, 10, 200, 60, "Applied Force"),
    'moment': StatusWindow(220, 10, 200, 80, "Resultant Moment")
}

# Game state
simulation_running = False
adjustment_mode = False
manual_force = None
notifications = []
last_force_warning = 0
last_moment_warning = 0
current_shape = "default"
shape_types = ["default", "circle", "square", "triangle"]
shape_index = 0

# Game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        
        # Handle button clicks
        for button_name, button in buttons.items():
            if button.handle_event(event):
                if button_name == 'start':
                    simulation_running = True
                    notifications.append(Notification("Simulation Started", GREEN, position="top"))
                    logging.info("Simulation started")
                elif button_name == 'stop':
                    simulation_running = False
                    notifications.append(Notification("Simulation Stopped", RED, position="top"))
                    logging.info("Simulation stopped")
                elif button_name == 'undo':
                    object.undo()
                    notifications.append(Notification("Manual Adjustments Undone", BLUE, position="top"))
                    logging.info("Manual adjustments undone")
                elif button_name == 'reset':
                    object = CompositeObject(current_shape)
                    all_sprites = pygame.sprite.Group(object)
                    simulation_running = False
                    adjustment_mode = False
                    manual_force = None
                    notifications.append(Notification("Simulation Reset", YELLOW, position="top"))
                    logging.info("Simulation reset")
                elif button_name == 'shape':
                    shape_index = (shape_index + 1) % len(shape_types)
                    current_shape = shape_types[shape_index]
                    object = CompositeObject(current_shape)
                    all_sprites = pygame.sprite.Group(object)
                    notifications.append(Notification(f"Shape Changed to {current_shape}", PURPLE, position="top"))
                    logging.info(f"Shape changed to: {current_shape}")

    # Update
    if simulation_running:
        object.update()
        
        # Update status windows
        total_force = math.sqrt(sum(f**2 for f in object.resultant_force))
        status_windows['force'].value = total_force
        status_windows['moment'].value = object.current_moment
        status_windows['moment'].direction = object.moment_direction
        
        # Update colors and check for warnings
        current_time = pygame.time.get_ticks()
        
        # Force warnings
        if total_force > 1000 and current_time - last_force_warning > 2000:
            notifications.append(Notification("Warning: Force Exceeding 1000N!", RED, position="bottom"))
            last_force_warning = current_time
            logging.warning(f"Force warning: {total_force:.2f}N")
        
        # Moment warnings
        if object.current_moment > 2500 and current_time - last_moment_warning > 2000:
            notifications.append(Notification("Warning: Moment Exceeding 2500N∙Unit!", RED, position="top"))
            last_moment_warning = current_time
            logging.warning(f"Moment warning: {object.current_moment:.2f}N∙Unit")
        
        # Update colors based on values
        if total_force <= 300:
            status_windows['force'].color = GREEN
        elif total_force <= 1000:
            status_windows['force'].color = YELLOW
        else:
            status_windows['force'].color = RED
            
        if object.current_moment <= 1000:
            status_windows['moment'].color = GREEN
        elif object.current_moment <= 2500:
            status_windows['moment'].color = YELLOW
        else:
            status_windows['moment'].color = RED

    # Update notifications
    notifications = [n for n in notifications if n.is_active]
    for notification in notifications:
        notification.update()

    # Draw
    screen.fill(WHITE)
    background.draw(screen)  # Draw background first
    all_sprites.draw(screen)
    
    # Draw buttons
    for button in buttons.values():
        button.draw(screen)
    
    # Draw status windows
    for window in status_windows.values():
        window.draw(screen)
    
    # Draw notifications
    for notification in notifications:
        notification.draw(screen)
    
    pygame.display.flip()
    clock.tick(FPS)

# Log final state
logging.info("Simulation ended")
pygame.quit()
sys.exit() 