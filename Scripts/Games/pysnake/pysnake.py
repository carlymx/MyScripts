# ==========================================
#  ███████╗███╗   ██╗ █████╗ ██╗  ██╗███████╗
#  ██╔════╝████╗  ██║██╔══██╗██║██║  ██╔════╝
#  ███████╗██╔██╗ ██║███████║████╗   ██████║
#  ╚════██║██║╚██╗██║██╔══██║██╔██╗  ██╔══╝
#  ███████║██║ ╚████║██║  ██║██║  ██║███████║
#  ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
# ------------------------------------------
#          S N A K E   -   P Y T H O N 3   
# ------------------------------------------
#  Un simple juego de la serpiente en Pygame
#  Creado por: [Tu Nombre o Alias]
#  Versión: 0.5
# ==========================================


import pygame
import random

# Inicializar Pygame
pygame.init()

# Configuración de la ventana
WINDOW_SIZE = 600
BLOCK_SIZE = 20
assert WINDOW_SIZE % BLOCK_SIZE == 0, "El tamaño de la ventana debe ser divisible por el tamaño del bloque"
window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Snake Simplificado")

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

class Snake:
    def __init__(self):
        self.body = [(10 * BLOCK_SIZE, 10 * BLOCK_SIZE)]
        self.direction = pygame.K_RIGHT
        self.next_direction = self.direction
        self.color = GREEN
    
    def move(self):
        head_x, head_y = self.body[0]
        
        if self.next_direction == pygame.K_UP:
            head_y -= BLOCK_SIZE
        elif self.next_direction == pygame.K_DOWN:
            head_y += BLOCK_SIZE
        elif self.next_direction == pygame.K_LEFT:
            head_x -= BLOCK_SIZE
        elif self.next_direction == pygame.K_RIGHT:
            head_x += BLOCK_SIZE
        
        self.body.insert(0, (head_x, head_y))
        if not self.has_eaten_food():
            self.body.pop()
        
    def has_eaten_food(self):
        global score  # Indicamos que usamos la variable global
        if self.body[0] in food_positions:
            food_positions[0] = create_food()  # Nueva comida aleatoria
            score += 10  # Incrementa la puntuación
            return True
        return False
    
    def draw(self):
        for segment in self.body:
            pygame.draw.rect(window, self.color, 
                            (segment[0], segment[1], BLOCK_SIZE - 2, BLOCK_SIZE - 2))
    
def create_food():
    while True:
        x = random.randint(0, WINDOW_SIZE // BLOCK_SIZE - 1) * BLOCK_SIZE
        y = random.randint(0, WINDOW_SIZE // BLOCK_SIZE - 1) * BLOCK_SIZE
        if (x, y) not in snake.body:  # Verifica que la comida no esté en la serpiente
            return (x, y)

def reset_game():
    global snake, food_positions, game_over, score
    snake = Snake()  # Reinicia la serpiente
    food_positions = [create_food()]  # Crea nueva comida
    game_over = False  # Restablece el estado del juego
    score = 0  # Reinicia la puntuación

# Crear instancia de Snake
snake = Snake()

# Posición inicial de la comida
food_positions = [create_food()]

# Reloj para controlar el FPS
clock = pygame.time.Clock()
FPS = 10

# Sistema de puntuación
score = 0
font = pygame.font.Font(None, 30)

running = True
game_over = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # Si se presiona ESC, salir del juego
                running = False
            elif game_over:
                reset_game()  # Reiniciar si se presiona cualquier otra tecla
            else:
                snake.next_direction = event.key
    
    if not game_over:
        # Mover la serpiente
        snake.move()
        
        # Verificar colisión con paredes o sí misma
        head_x, head_y = snake.body[0]
        if (head_x < 0 or head_x >= WINDOW_SIZE or 
            head_y < 0 or head_y >= WINDOW_SIZE):
            game_over = True
        
        for i in range(1, len(snake.body)):
            if snake.body[i] == snake.body[0]:
                game_over = True
    
    # Dibujar en la ventana
    window.fill(BLACK)
    
    # Mostrar puntuación
    score_text = font.render(f"Puntuación: {score}", True, WHITE)
    window.blit(score_text, (10, 10))
    
    # Dibujar comida
    for food in food_positions:
        pygame.draw.rect(window, RED, 
                        (food[0], food[1], BLOCK_SIZE - 2, BLOCK_SIZE - 2))
    
    if not game_over:
        snake.draw()
    else:
        # Mostrar mensaje de Game Over
        game_over_text = font.render("¡Game Over! Presiona cualquier tecla para reiniciar", True, RED)
        text_rect = game_over_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
        window.blit(game_over_text, text_rect)

        exit_text = font.render("Presiona ESC para salir", True, RED)
        exit_rect = exit_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 40))
        window.blit(exit_text, exit_rect)
        
    # Actualizar la ventana
    pygame.display.flip()
    
    # Controlar FPS
    clock.tick(FPS)
    
# Finalizar Pygame
pygame.quit()

