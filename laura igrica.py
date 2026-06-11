import pygame
import random
import sys
import json
import os

# Inicijalizacija
pygame.init()

# Konstante
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
LEADERBOARD_FILE = "leaderboard.json"

# Boje
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
LIGHT_BROWN = (205, 133, 63)
GRAY = (128, 128, 128)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
DARK_GREEN = (0, 100, 0)
ORANGE = (255, 140, 0)
LIGHT_GRAY = (200, 200, 200)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

# Ekran
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Udari Krticu!")
clock = pygame.time.Clock()

# Fontovi
font_large = pygame.font.Font(None, 74)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)
font_tiny = pygame.font.Font(None, 28)


def load_leaderboard():
    """Učitava leaderboard iz fajla."""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_leaderboard(leaderboard):
    """Čuva leaderboard u fajl."""
    try:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def add_score_to_leaderboard(name, score):
    """Dodaje rezultat u leaderboard i sortira ga."""
    leaderboard = load_leaderboard()
    leaderboard.append({"name": name, "score": score})
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    leaderboard = leaderboard[:10]  # Čuvaj samo top 10
    save_leaderboard(leaderboard)
    return leaderboard


class Hole:
    """Klasa koja predstavlja rupu iz koje izlazi krtica ili bomba."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 100
        self.height = 50
        self.has_mole = False
        self.has_bomb = False
        self.mole_timer = 0
        self.mole_duration = 2.0

    def draw(self, surface):
        # Crtanje rupe (elipsa)
        pygame.draw.ellipse(surface, DARK_BROWN,
                            (self.x - self.width // 2, self.y - self.height // 2,
                             self.width, self.height))
        pygame.draw.ellipse(surface, BLACK,
                            (self.x - self.width // 2 + 5, self.y - self.height // 2 + 5,
                             self.width - 10, self.height - 10))

        # Ako ima krticu, nacrtaj je
        if self.has_mole:
            self.draw_mole(surface)
        elif self.has_bomb:
            self.draw_bomb(surface)

    def draw_mole(self, surface):
        # Telo krtice
        mole_y = self.y - 40
        pygame.draw.ellipse(surface, BROWN,
                            (self.x - 35, mole_y - 30, 70, 60))

        # Glava
        pygame.draw.circle(surface, BROWN, (self.x, mole_y - 20), 30)

        # Nos
        pygame.draw.circle(surface, (255, 182, 193), (self.x, mole_y - 10), 10)

        # Oči
        pygame.draw.circle(surface, WHITE, (self.x - 12, mole_y - 28), 8)
        pygame.draw.circle(surface, WHITE, (self.x + 12, mole_y - 28), 8)
        pygame.draw.circle(surface, BLACK, (self.x - 12, mole_y - 28), 4)
        pygame.draw.circle(surface, BLACK, (self.x + 12, mole_y - 28), 4)

        # Brkovi
        for offset in [-1, 1]:
            pygame.draw.line(surface, BLACK,
                             (self.x + offset * 15, mole_y - 10),
                             (self.x + offset * 40, mole_y - 15), 2)
            pygame.draw.line(surface, BLACK,
                             (self.x + offset * 15, mole_y - 8),
                             (self.x + offset * 40, mole_y - 5), 2)

    def draw_bomb(self, surface):
        """Crta bombu."""
        bomb_y = self.y - 50

        # Telo bombe (crni krug)
        pygame.draw.circle(surface, BLACK, (self.x, bomb_y), 28)
        pygame.draw.circle(surface, (40, 40, 40), (self.x - 8, bomb_y - 8), 8)

        # Fitilj
        pygame.draw.line(surface, DARK_BROWN, (self.x, bomb_y - 28), (self.x + 10, bomb_y - 45), 4)

        # Iskra na fitilju
        spark_offset = random.randint(-3, 3)
        pygame.draw.circle(surface, ORANGE, (self.x + 10 + spark_offset, bomb_y - 48), 6)
        pygame.draw.circle(surface, YELLOW, (self.x + 10 + spark_offset, bomb_y - 48), 3)

        # Crveni znak opasnosti
        pygame.draw.circle(surface, RED, (self.x, bomb_y + 5), 10)
        skull_text = font_small.render("!", True, WHITE)
        surface.blit(skull_text, (self.x - 4, bomb_y - 3))

    def get_mole_rect(self):
        """Vraća pravougaonik za detekciju klika na krticu."""
        if self.has_mole:
            mole_y = self.y - 40
            return pygame.Rect(self.x - 35, mole_y - 50, 70, 80)
        return None

    def get_bomb_rect(self):
        """Vraća pravougaonik za detekciju klika na bombu."""
        if self.has_bomb:
            bomb_y = self.y - 50
            return pygame.Rect(self.x - 28, bomb_y - 28, 56, 56)
        return None

    def update(self, dt):
        """Ažurira tajmer krtice/bombe."""
        if self.has_mole or self.has_bomb:
            self.mole_timer -= dt
            if self.mole_timer <= 0:
                self.has_mole = False
                self.has_bomb = False
                return False
        return True

    def spawn_mole(self, duration):
        """Pojavi krticu na ovoj rupi."""
        self.has_mole = True
        self.has_bomb = False
        self.mole_timer = duration
        self.mole_duration = duration

    def spawn_bomb(self, duration):
        """Pojavi bombu na ovoj rupi."""
        self.has_bomb = True
        self.has_mole = False
        self.mole_timer = duration

    def hit_mole(self):
        """Proveri da li je krtica pogođena."""
        if self.has_mole:
            self.has_mole = False
            return True
        return False

    def hit_bomb(self):
        """Proveri da li je bomba pogođena."""
        if self.has_bomb:
            self.has_bomb = False
            return True
        return False

    def is_empty(self):
        """Proveri da li je rupa prazna."""
        return not self.has_mole and not self.has_bomb


class Button:
    """Klasa za dugmad u igri."""

    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color

        # Senka
        shadow_rect = self.rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(surface, GRAY, shadow_rect, border_radius=15)

        # Dugme
        pygame.draw.rect(surface, color, self.rect, border_radius=15)
        pygame.draw.rect(surface, BLACK, self.rect, 3, border_radius=15)

        # Tekst
        text_surface = font_medium.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class TextInput:
    """Klasa za unos teksta."""

    def __init__(self, x, y, width, height, max_length=12):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = ""
        self.max_length = max_length
        self.active = True
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True  # Signal da je unos završen
            elif len(self.text) < self.max_length:
                if event.unicode.isprintable() and event.unicode != '':
                    self.text += event.unicode
        return False

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

    def draw(self, surface):
        # Pozadina
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=10)
        pygame.draw.rect(surface, YELLOW if self.active else GRAY, self.rect, 3, border_radius=10)

        # Tekst
        display_text = self.text
        if self.cursor_visible and self.active:
            display_text += "|"

        text_surface = font_medium.render(display_text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def get_text(self):
        return self.text.strip() if self.text.strip() else "Igrač"


class PauseButton:
    """Dugme za pauzu u gornjem desnom uglu."""

    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH - 70, 70, 50, 50)
        self.is_hovered = False

    def draw(self, surface):
        color = (80, 80, 80) if self.is_hovered else (60, 60, 60)

        # Pozadina
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)

        # Simbol pauze (dve vertikalne linije)
        bar_width = 8
        bar_height = 24
        gap = 6
        center_x = self.rect.centerx
        center_y = self.rect.centery

        pygame.draw.rect(surface, WHITE,
                         (center_x - gap - bar_width, center_y - bar_height // 2, bar_width, bar_height))
        pygame.draw.rect(surface, WHITE,
                         (center_x + gap, center_y - bar_height // 2, bar_width, bar_height))

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Game:
    """Glavna klasa igre."""

    def __init__(self):
        self.state = "START"  # START, PLAYING, PAUSED, GAME_OVER
        self.score = 0
        self.time_left = 60
        self.total_time = 60
        self.player_name = ""

        # Unos imena
        self.name_input = TextInput(SCREEN_WIDTH // 2, 360, 300, 50)

        # Kreiranje rupa (3x3 mreža)
        self.holes = []
        start_x = 200
        start_y = 250
        spacing_x = 200
        spacing_y = 120

        for row in range(3):
            for col in range(3):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                self.holes.append(Hole(x, y))

        # Tajmer za pojavljivanje krtica
        self.spawn_timer = 0
        self.spawn_interval = 1.0

        # Tajmer za bombe
        self.bomb_spawn_timer = 0
        self.bomb_spawn_interval = 1.0

        # Dugmad
        self.start_button = Button(SCREEN_WIDTH // 2, 440, 200, 60, "START", GREEN, DARK_GREEN)
        self.restart_button = Button(SCREEN_WIDTH // 2, 540, 200, 50, "PONOVO", GREEN, DARK_GREEN)

        # Dugmad za pauzu
        self.pause_button = PauseButton()
        self.continue_button = Button(SCREEN_WIDTH // 2, 320, 220, 55, "NASTAVI", GREEN, DARK_GREEN)
        self.pause_restart_button = Button(SCREEN_WIDTH // 2, 400, 220, 55, "RESTART", RED, (180, 0, 0))

        # Efekat udarca
        self.hit_effects = []

        # Leaderboard
        self.leaderboard = load_leaderboard()

    def reset(self):
        """Resetuje igru na početno stanje."""
        self.score = 0
        self.time_left = 60
        self.spawn_timer = 0
        self.spawn_interval = 1.0
        self.bomb_spawn_timer = 0
        self.bomb_spawn_interval = 1.0

        for hole in self.holes:
            hole.has_mole = False
            hole.has_bomb = False

        self.hit_effects = []

    def get_mole_duration(self):
        """Računa koliko dugo krtica ostaje vidljiva na osnovu preostalog vremena."""
        progress = 1 - (self.time_left / self.total_time)
        duration = 2.0 - (progress * 1.5)
        return max(0.5, duration)

    def get_spawn_interval(self):
        """Računa interval pojavljivanja krtica."""
        progress = 1 - (self.time_left / self.total_time)
        interval = 1.0 - (progress * 0.5)
        return max(0.3, interval)

    def spawn_mole(self):
        """Pojavi krticu na nasumičnoj praznoj rupi."""
        empty_holes = [h for h in self.holes if h.is_empty()]
        if empty_holes:
            hole = random.choice(empty_holes)
            hole.spawn_mole(self.get_mole_duration())

    def spawn_bomb(self):
        """Pojavi bombu na nasumičnoj praznoj rupi."""
        empty_holes = [h for h in self.holes if h.is_empty()]
        if empty_holes:
            hole = random.choice(empty_holes)
            hole.spawn_bomb(self.get_mole_duration())

    def add_hit_effect(self, x, y, text, color):
        """Dodaje vizuelni efekat."""
        self.hit_effects.append({
            'x': x,
            'y': y,
            'timer': 0.5,
            'text': text,
            'color': color
        })

    def update(self, dt):
        """Ažurira stanje igre."""
        if self.state == "START":
            self.name_input.update(dt)
            return

        if self.state != "PLAYING":
            return

        # Ažuriraj tajmer
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.state = "GAME_OVER"
            # Sačuvaj rezultat u leaderboard
            self.leaderboard = add_score_to_leaderboard(self.player_name, self.score)
            return

        # Ažuriraj tajmer za pojavljivanje krtica
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_mole()
            self.spawn_interval = self.get_spawn_interval()
            self.spawn_timer = self.spawn_interval

        # Ažuriraj tajmer za bombe (ređe)
        self.bomb_spawn_timer -= dt
        if self.bomb_spawn_timer <= 0:
            if random.random() < 0.3:
                self.spawn_bomb()
            self.bomb_spawn_timer = self.bomb_spawn_interval + random.uniform(0, 2)

        # Ažuriraj sve rupe
        for hole in self.holes:
            hole.update(dt)

        # Ažuriraj efekte
        for effect in self.hit_effects[:]:
            effect['timer'] -= dt
            effect['y'] -= 50 * dt
            if effect['timer'] <= 0:
                self.hit_effects.remove(effect)

    def handle_event(self, event):
        """Obrađuje događaje."""
        if self.state == "START":
            if self.name_input.handle_event(event):
                # Enter pritisnut - započni igru
                self.player_name = self.name_input.get_text()
                self.state = "PLAYING"
                self.reset()

    def handle_click(self, pos):
        """Obrađuje klik miša."""
        if self.state == "START":
            if self.start_button.is_clicked(pos):
                self.player_name = self.name_input.get_text()
                self.state = "PLAYING"
                self.reset()

        elif self.state == "PLAYING":
            # Proveri da li je kliknuto dugme za pauzu
            if self.pause_button.is_clicked(pos):
                self.state = "PAUSED"
                return

            # Proveri klikove na rupe
            for hole in self.holes:
                # Prvo proveri bombu
                bomb_rect = hole.get_bomb_rect()
                if bomb_rect and bomb_rect.collidepoint(pos):
                    if hole.hit_bomb():
                        self.score -= 200
                        self.add_hit_effect(hole.x, hole.y - 60, "-200", RED)
                    break

                # Zatim proveri krticu
                mole_rect = hole.get_mole_rect()
                if mole_rect and mole_rect.collidepoint(pos):
                    if hole.hit_mole():
                        self.score += 100
                        self.add_hit_effect(hole.x, hole.y - 60, "+100", YELLOW)
                    break

        elif self.state == "PAUSED":
            if self.continue_button.is_clicked(pos):
                self.state = "PLAYING"
            elif self.pause_restart_button.is_clicked(pos):
                self.state = "PLAYING"
                self.reset()

        elif self.state == "GAME_OVER":
            if self.restart_button.is_clicked(pos):
                self.state = "START"
                self.name_input.text = self.player_name  # Zadrži ime
                self.reset()

    def draw_background(self):
        """Crta pozadinu."""
        # Nebo
        screen.fill((135, 206, 235))

        # Trava
        pygame.draw.rect(screen, GREEN, (0, 180, SCREEN_WIDTH, SCREEN_HEIGHT - 180))

        # Dekorativna trava
        random.seed(42)
        for i in range(0, SCREEN_WIDTH, 20):
            height = random.randint(10, 25)
            pygame.draw.line(screen, DARK_GREEN, (i, 180), (i - 5, 180 - height), 2)
            pygame.draw.line(screen, DARK_GREEN, (i, 180), (i + 5, 180 - height), 2)
        random.seed()

    def draw_ui(self):
        """Crta korisnički interfejs."""
        # Panel za rezultat i vreme
        pygame.draw.rect(screen, (50, 50, 50), (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.rect(screen, YELLOW, (0, 55, SCREEN_WIDTH, 5))

        # Ime igrača
        name_text = font_small.render(f"Igrač: {self.player_name}", True, LIGHT_GRAY)
        screen.blit(name_text, (20, 2))

        # Rezultat
        score_color = RED if self.score < 0 else WHITE
        score_text = font_medium.render(f"Poeni: {self.score}", True, score_color)
        screen.blit(score_text, (20, 25))

        # Vreme
        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        time_color = RED if self.time_left < 30 else WHITE
        time_text = font_medium.render(f"Vreme: {minutes:02d}:{seconds:02d}", True, time_color)
        screen.blit(time_text, (SCREEN_WIDTH - 220, 10))

        # Dugme za pauzu
        self.pause_button.draw(screen)

    def draw_start_screen(self):
        """Crta početni ekran."""
        self.draw_background()

        # Naslov
        title = font_large.render("UDARI KRTICU!", True, DARK_BROWN)
        title_shadow = font_large.render("UDARI KRTICU!", True, BLACK)
        screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 63))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        # Instrukcije
        instructions = [
            "Klikni na krtice da skupiš poene!",
            "PAZI na bombe! Bomba = -200 poena!"
        ]

        for i, text in enumerate(instructions):
            color = RED if "bombe" in text else BLACK
            inst_text = font_small.render(text, True, color)
            screen.blit(inst_text, (SCREEN_WIDTH // 2 - inst_text.get_width() // 2, 200 + i * 35))

        # Polje za unos imena
        name_label = font_small.render("Unesi svoje ime:", True, BLACK)
        screen.blit(name_label, (SCREEN_WIDTH // 2 - name_label.get_width() // 2, 300))

        self.name_input.draw(screen)

        # Dugme
        self.start_button.draw(screen)

        # Krtica za dekoraciju
        demo_hole = Hole(SCREEN_WIDTH // 2 - 100, 540)
        demo_hole.has_mole = True
        demo_hole.draw(screen)

        # Bomba za dekoraciju
        demo_bomb = Hole(SCREEN_WIDTH // 2 + 100, 540)
        demo_bomb.has_bomb = True
        demo_bomb.draw(screen)

    def draw_leaderboard(self, x, y):
        """Crta leaderboard na određenoj poziciji."""
        # Naslov
        title = font_small.render(" TOP 5 ", True, GOLD)
        screen.blit(title, (x - title.get_width() // 2, y))

        # Lista rezultata
        top_5 = self.leaderboard[:5]
        medal_colors = [GOLD, SILVER, BRONZE, WHITE, WHITE]

        for i, entry in enumerate(top_5):
            color = medal_colors[i]
            rank_text = f"{i + 1}."
            name = entry["name"][:10]  # Skrati ime ako je predugo
            score = entry["score"]

            # Oznaka mesta
            rank_surface = font_tiny.render(rank_text, True, color)
            screen.blit(rank_surface, (x - 80, y + 35 + i * 28))

            # Ime
            name_surface = font_tiny.render(name, True, WHITE)
            screen.blit(name_surface, (x - 50, y + 35 + i * 28))

            # Rezultat
            score_color = RED if score < 0 else color
            score_surface = font_tiny.render(str(score), True, score_color)
            screen.blit(score_surface, (x + 60, y + 35 + i * 28))

        if not top_5:
            empty_text = font_tiny.render("Nema rezultata", True, GRAY)
            screen.blit(empty_text, (x - empty_text.get_width() // 2, y + 40))

    def draw_pause_screen(self):
        """Crta ekran pauze."""
        # Zatamnjena pozadina
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        screen.blit(overlay, (0, 0))

        # Panel
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, 180, 360, 300)
        pygame.draw.rect(screen, (50, 50, 50), panel_rect, border_radius=20)
        pygame.draw.rect(screen, YELLOW, panel_rect, 4, border_radius=20)

        # Naslov
        pause_text = font_large.render("PAUZA", True, WHITE)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 210))

        # Dugmad
        self.continue_button.draw(screen)
        self.pause_restart_button.draw(screen)

    def draw_game_over_screen(self):
        """Crta ekran kraja igre sa leaderboard-om."""
        # Zatamnjena pozadina
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))

        # Glavni panel
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 350, 50, 700, 500)
        pygame.draw.rect(screen, (40, 40, 40), panel_rect, border_radius=20)
        pygame.draw.rect(screen, YELLOW, panel_rect, 4, border_radius=20)

        # Naslov
        game_over_text = font_large.render("KRAJ IGRE!", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 70))

        # Rezultat igrača - leva strana
        player_panel = pygame.Rect(SCREEN_WIDTH // 2 - 320, 150, 300, 250)
        pygame.draw.rect(screen, (60, 60, 60), player_panel, border_radius=15)

        player_label = font_small.render("Tvoj rezultat", True, LIGHT_GRAY)
        screen.blit(player_label, (player_panel.centerx - player_label.get_width() // 2, 170))

        name_text = font_medium.render(self.player_name, True, WHITE)
        screen.blit(name_text, (player_panel.centerx - name_text.get_width() // 2, 210))

        score_color = RED if self.score < 0 else GOLD
        score_text = font_large.render(str(self.score), True, score_color)
        screen.blit(score_text, (player_panel.centerx - score_text.get_width() // 2, 260))

        # Proveri poziciju na leaderboard-u
        position = None
        for i, entry in enumerate(self.leaderboard):
            if entry["name"] == self.player_name and entry["score"] == self.score:
                position = i + 1
                break

        if position:
            pos_text = font_small.render(f"Pozicija: #{position}", True, GOLD if position <= 3 else WHITE)
            screen.blit(pos_text, (player_panel.centerx - pos_text.get_width() // 2, 330))

        # Leaderboard - desna strana
        lb_panel = pygame.Rect(SCREEN_WIDTH // 2 + 20, 150, 300, 250)
        pygame.draw.rect(screen, (60, 60, 60), lb_panel, border_radius=15)

        self.draw_leaderboard(lb_panel.centerx, 160)

        # Dugme za restart
        self.restart_button.draw(screen)

    def draw(self):
        """Glavna funkcija za crtanje."""
        if self.state == "START":
            self.draw_start_screen()

        elif self.state == "PLAYING":
            self.draw_background()
            self.draw_ui()

            # Crtaj rupe
            for hole in self.holes:
                hole.draw(screen)

            # Crtaj efekte
            for effect in self.hit_effects:
                alpha = int(255 * (effect['timer'] / 0.5))
                effect_text = font_medium.render(effect['text'], True, effect['color'])
                effect_text.set_alpha(alpha)
                screen.blit(effect_text,
                            (effect['x'] - effect_text.get_width() // 2, effect['y']))

        elif self.state == "PAUSED":
            self.draw_background()
            self.draw_ui()
            for hole in self.holes:
                hole.draw(screen)
            self.draw_pause_screen()

        elif self.state == "GAME_OVER":
            self.draw_background()
            for hole in self.holes:
                hole.draw(screen)
            self.draw_game_over_screen()


def main():
    """Glavna funkcija."""
    game = Game()

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    game.handle_click(event.pos)

            elif event.type == pygame.MOUSEMOTION:
                if game.state == "START":
                    game.start_button.check_hover(event.pos)
                elif game.state == "PLAYING":
                    game.pause_button.check_hover(event.pos)
                elif game.state == "PAUSED":
                    game.continue_button.check_hover(event.pos)
                    game.pause_restart_button.check_hover(event.pos)
                elif game.state == "GAME_OVER":
                    game.restart_button.check_hover(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == "PLAYING":
                        game.state = "PAUSED"
                    elif game.state == "PAUSED":
                        game.state = "PLAYING"

            # Prosledi događaj za unos teksta
            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
