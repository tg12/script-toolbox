# BLACK HOLE - A fun arcade-style game!
#
# Click to place black holes and suck in all the planets.
# You have a limited number of black holes and time.
# Black holes last a few seconds and show a countdown.
# Planets bounce around - plan your shots!
# Can you clear the galaxy? Good luck!
#
# Disclaimer: This game is for entertainment and educational purposes only.
# No real planets were harmed in the making of this code.
#

"""Copyright (C) 2025 James Sawyer
All rights reserved.

This script and the associated files are private
and confidential property. Unauthorized copying of
this file, via any medium, and the divulgence of any
contained information without express written consent
is strictly prohibited.

This script is intended for personal use only and should
not be distributed or used in any commercial or public
setting unless otherwise authorized by the copyright holder.
By using this script, you agree to abide by these terms.

DISCLAIMER: This script is provided 'as is' without warranty
of any kind, either express or implied, including, but not
limited to, the implied warranties of merchantability,
fitness for a particular purpose, or non-infringement. In no
event shall the authors or copyright holders be liable for
any claim, damages, or other liability, whether in an action
of contract, tort or otherwise, arising from, out of, or in
connection with the script or the use or other dealings in
the script.
"""

# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0621, W1203, C0103, C0301, W1201, W0511, E0401, E1101, E0606
# C0116: Missing function or method docstring
# W0621: Redefining name %r from outer scope (line %s)
# W1203: Use % formatting in logging functions and pass the % parameters as arguments
# C0103: Constant name "%s" doesn't conform to UPPER_CASE naming style
# C0301: Line too long (%s/%s)
# W1201: Specify string format arguments as logging function parameters
# W0511: TODOs
# E1101: Module 'holidays' has no 'US' member (no-member) ... it does, so ignore this
# E0606: possibly-used-before-assignment, ignore this
# UP018: native-literals (UP018)

import math
import random
import sys
import time

import numpy as np
import pygame

# --- CONFIG ---
WIDTH, HEIGHT = 1280, 720
FPS = 90

PLANET_RADIUS = 24
BLACKHOLE_RADIUS_RANGE = (90, 120)  # min, max
BLACKHOLE_LIFETIME_RANGE = (2.0, 3.5)  # seconds
PLANET_COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (127, 255, 0),
    (128, 0, 255),
]
FONT_NAME = "freesansbold.ttf"

# --- DIFFICULTY SETTINGS ---
DIFFICULTY_LEVELS = {
    "Easy": {"planets": 10, "holes": 4, "speed": 2.5, "timer": 40},
    "Medium": {"planets": 16, "holes": 3, "speed": 3.5, "timer": 32},
    "Hard": {"planets": 22, "holes": 2, "speed": 4.5, "timer": 24},
}


# --- STARFIELD ---
def make_starfield(num=120):
    return [
        (random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3))
        for _ in range(num)
    ]


def draw_starfield(screen, stars):
    for x, y, r in stars:
        pygame.draw.circle(screen, (255, 255, 255), (x, y), r)


# --- CLASSES ---


class Planet:
    def __init__(self):
        # Use numpy for random positions and velocities
        self.x = np.random.randint(PLANET_RADIUS, WIDTH - PLANET_RADIUS)
        self.y = np.random.randint(PLANET_RADIUS + 70, HEIGHT - PLANET_RADIUS)
        angle = np.random.uniform(0, 2 * np.pi)
        speed = np.random.uniform(self.speed_min, self.speed_max)
        self.vx = np.cos(angle) * speed
        self.vy = np.sin(angle) * speed
        self.color = random.choice(PLANET_COLORS)
        self.alive = True
        self.sucked = False
        self.suck_target = None
        self.suck_progress = 0

    @classmethod
    def set_speed_range(cls, minv, maxv):
        cls.speed_min = minv
        cls.speed_max = maxv

    def move(self):
        if self.sucked and self.suck_target:
            dx = self.suck_target[0] - self.x
            dy = self.suck_target[1] - self.y
            dist = math.hypot(dx, dy)
            if dist < 5:
                self.alive = False
            else:
                angle = math.atan2(dy, dx)
                spiral = angle + 0.2
                self.x += math.cos(spiral) * max(dist * 0.18, 2)
                self.y += math.sin(spiral) * max(dist * 0.18, 2)
                self.suck_progress += 1
        else:
            self.x += self.vx
            self.y += self.vy
            # Bounce
            if self.x < PLANET_RADIUS or self.x > WIDTH - PLANET_RADIUS:
                self.vx *= -1
            if self.y < PLANET_RADIUS + 60 or self.y > HEIGHT - PLANET_RADIUS:
                self.vy *= -1

    def draw(self, screen):
        if self.alive:
            glow_color = tuple(min(255, c + 120) for c in self.color)
            pygame.draw.circle(
                screen, glow_color, (int(self.x), int(self.y)), PLANET_RADIUS + 7
            )
            pygame.draw.circle(
                screen,
                (220, 220, 220),
                (int(self.x), int(self.y)),
                PLANET_RADIUS + 2,
                2,
            )
            pygame.draw.circle(
                screen, self.color, (int(self.x), int(self.y)), PLANET_RADIUS
            )
            if self.sucked:
                shrink = max(0, PLANET_RADIUS - self.suck_progress // 3)
                if shrink > 0:
                    pygame.draw.circle(
                        screen, self.color, (int(self.x), int(self.y)), shrink
                    )


class BlackHole:
    def __init__(self, pos):
        self.x, self.y = pos
        self.radius = random.randint(*BLACKHOLE_RADIUS_RANGE)
        self.lifetime = random.uniform(*BLACKHOLE_LIFETIME_RANGE)
        self.created = time.time()
        self.active = True
        self.angle = np.random.uniform(0, 2 * np.pi)

    def update(self):
        if time.time() - self.created > self.lifetime:
            self.active = False
        self.angle += 0.09

    def draw(self, screen):
        t = (time.time() - self.created) / self.lifetime
        alpha = max(0, 255 - int(200 * t))
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        for i in range(6):
            a = self.angle + i * math.pi / 3
            r = int(self.radius * 0.85)
            x = int(self.radius + math.cos(a) * r * 0.7)
            y = int(self.radius + math.sin(a) * r * 0.7)
            pygame.draw.circle(
                s, (40, 40, 90, int(alpha * 0.25)), (x, y), int(self.radius * 0.35)
            )
        pygame.draw.circle(
            s, (10, 10, 10, alpha), (self.radius, self.radius), self.radius
        )
        pygame.draw.circle(
            s,
            (40, 40, 90, int(alpha * 0.4)),
            (self.radius, self.radius),
            int(self.radius * 0.75),
        )
        pygame.draw.circle(
            s,
            (120, 120, 255, int(alpha * 0.18)),
            (self.radius, self.radius),
            int(self.radius * 0.97),
            3,
        )
        screen.blit(s, (self.x - self.radius, self.y - self.radius))
        # Draw countdown seconds
        seconds_left = max(
            0, int(math.ceil(self.lifetime - (time.time() - self.created)))
        )
        if seconds_left > 0:
            font = pygame.font.Font(FONT_NAME, 32)
            txt = font.render(str(seconds_left), True, (255, 255, 180))
            txt_rect = txt.get_rect(center=(self.x, self.y))
            screen.blit(txt, txt_rect)


def draw_text(screen, text, size, x, y, color=(255, 255, 255), center=True):
    font = pygame.font.Font(FONT_NAME, size)
    txt_surf = font.render(text, True, color)
    rect = txt_surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(txt_surf, rect)


def countdown(screen, seconds, stars):
    for i in range(seconds, 0, -1):
        screen.fill((0, 0, 0))
        draw_starfield(screen, stars)
        draw_text(screen, f"{i}", 160, WIDTH // 2, HEIGHT // 2)
        pygame.display.flip()
        pygame.time.wait(800)
    screen.fill((0, 0, 0))
    draw_starfield(screen, stars)
    draw_text(screen, "GO!", 120, WIDTH // 2, HEIGHT // 2, (90, 255, 90))
    pygame.display.flip()
    pygame.time.wait(700)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Black Hole")
    clock = pygame.time.Clock()
    stars = make_starfield()
    best_score = 0

    # --- DIFFICULTY MENU ---
    selected = 0
    difficulties = list(DIFFICULTY_LEVELS.keys())
    running = True
    while running:
        screen.fill((12, 17, 37))
        draw_starfield(screen, stars)
        draw_text(screen, "BLACK HOLE", 72, WIDTH // 2, 70, (255, 255, 255))
        draw_text(screen, "Select Difficulty", 50, WIDTH // 2, 340, (180, 220, 255))
        for i, level in enumerate(difficulties):
            color = (140, 255, 180) if i == selected else (255, 255, 255)
            draw_text(screen, f"{level}", 42, WIDTH // 2, 420 + i * 70, color)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(difficulties)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(difficulties)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    running = False
        clock.tick(24)

    diff = difficulties[selected]
    params = DIFFICULTY_LEVELS[diff]
    Planet.set_speed_range(params["speed"] * 0.75, params["speed"] * 1.15)

    while True:
        # --- PREPARE GAME ---
        planets = [Planet() for _ in range(params["planets"])]
        blackholes = []
        blackholes_left = params["holes"]
        timer = params["timer"]
        start_time = time.time()
        sucked_count = 0

        # --- COUNTDOWN ---
        countdown(screen, 3, stars)

        # --- MAIN GAME LOOP ---
        game_over = False
        win = False

        while True:
            dt = clock.tick(FPS) / 1000.0
            elapsed = int(time.time() - start_time)
            time_left = max(0, timer - elapsed)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    if blackholes_left > 0:
                        mx, my = pygame.mouse.get_pos()
                        blackholes.append(BlackHole((mx, my)))
                        blackholes_left -= 1

            # Update black holes
            for bh in blackholes:
                bh.update()
            blackholes = [bh for bh in blackholes if bh.active]

            # Improved collision detection: use squared distance and sum of radii
            for p in planets:
                if not p.alive or p.sucked:
                    continue
                for bh in blackholes:
                    dx = bh.x - p.x
                    dy = bh.y - p.y
                    sum_r = bh.radius + PLANET_RADIUS
                    if dx * dx + dy * dy < sum_r * sum_r:
                        p.sucked = True
                        p.suck_target = (bh.x, bh.y)
                        break

            # Update planets
            for p in planets:
                if p.alive:
                    prev_alive = p.alive
                    p.move()
                    if prev_alive and not p.alive:
                        sucked_count += 1
            alive_planets = [p for p in planets if p.alive]

            # --- DRAW ---
            screen.fill((0, 0, 0))
            draw_starfield(screen, stars)
            draw_text(
                screen, f"Time: {time_left}", 32, 80, 30, (255, 255, 180), center=False
            )
            draw_text(
                screen,
                f"Black Holes: {blackholes_left}",
                32,
                WIDTH - 270,
                30,
                (180, 255, 255),
                center=False,
            )
            draw_text(
                screen,
                f"Planets Left: {len(alive_planets)}",
                32,
                WIDTH // 2 - 80,
                30,
                (255, 180, 255),
                center=False,
            )
            for bh in blackholes:
                bh.draw(screen)
            for p in planets:
                p.draw(screen)

            if game_over:
                # Freeze time and blackholes_left for bonus/score calculation at game over
                if not hasattr(main, "_final_bonus"):
                    # Only calculate once at game over
                    main._final_blackholes_left = blackholes_left
                    main._final_time_left = time_left
                    main._final_bonus = max(
                        0, main._final_blackholes_left * 3 + main._final_time_left
                    )
                    main._final_score = sucked_count + main._final_bonus
                bonus = main._final_bonus
                score = main._final_score
                if win:
                    draw_text(
                        screen,
                        "YOU WIN!",
                        88,
                        WIDTH // 2,
                        HEIGHT // 2 - 60,
                        (100, 255, 100),
                    )
                else:
                    draw_text(
                        screen,
                        "TIME'S UP!",
                        74,
                        WIDTH // 2,
                        HEIGHT // 2 - 60,
                        (255, 90, 90),
                    )
                draw_text(
                    screen,
                    f"Planets Sucked In: {sucked_count}",
                    52,
                    WIDTH // 2,
                    HEIGHT // 2 + 10,
                    (255, 255, 180),
                )
                draw_text(
                    screen,
                    f"Bonus: {bonus}",
                    40,
                    WIDTH // 2,
                    HEIGHT // 2 + 60,
                    (180, 255, 255),
                )
                draw_text(
                    screen,
                    f"Final Score: {score}",
                    54,
                    WIDTH // 2,
                    HEIGHT // 2 + 120,
                    (255, 255, 255),
                )
                if score > best_score:
                    best_score = score
                draw_text(
                    screen,
                    f"Best Score: {best_score}",
                    38,
                    WIDTH // 2,
                    HEIGHT // 2 + 180,
                    (255, 255, 180),
                )
                draw_text(
                    screen,
                    "Press R to Restart",
                    38,
                    WIDTH // 2,
                    HEIGHT // 2 + 240,
                    (180, 220, 255),
                )
            else:
                # Reset the final bonus/score cache if not game over
                if hasattr(main, "_final_bonus"):
                    del main._final_bonus
                    del main._final_score
                    del main._final_blackholes_left
                    del main._final_time_left
            pygame.display.flip()

            # --- WIN/LOSE LOGIC ---
            if not game_over:
                if not alive_planets:
                    win, game_over = True, True
                elif time_left == 0:
                    win, game_over = False, True
                # Instant game over if no black holes left and planets remain
                elif (
                    blackholes_left == 0
                    and len(alive_planets) > 0
                    and not any(bh.active for bh in blackholes)
                ):
                    win, game_over = False, True
            else:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_r]:
                    break  # Restart with same difficulty


if __name__ == "__main__":
    main()
