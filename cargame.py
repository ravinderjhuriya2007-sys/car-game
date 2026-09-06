"""
================================================================================
✦ TURBO HORIZON: HIGHWAY SPEED RACER ✦
A complete, high-speed 2D arcade car racing game in Python using Pygame and NumPy.
Zero external assets required: sprites, visual effects, and audio are 100% procedural!
================================================================================
Controls:
  - Steer:        LEFT / RIGHT Arrows or A / D
  - Accelerate:   UP Arrow or W
  - Brake:        DOWN Arrow or S
  - Nitro Boost:  SPACEBAR or SHIFT
  - Toggle Audio: M
  - Pause:        P or ESC
  - Restart:      R (after game over)
================================================================================
"""

import sys
import math
import random
import numpy as np
import pygame

# ------------------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# ------------------------------------------------------------------------------
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 800
FPS = 60

# Road Dimensions
ROAD_WIDTH = 480
ROAD_LEFT = (WINDOW_WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH
NUM_LANES = 4
LANE_WIDTH = ROAD_WIDTH // NUM_LANES
LANE_CENTERS = [ROAD_LEFT + int((i + 0.5) * LANE_WIDTH) for i in range(NUM_LANES)]

# Colors
COLOR_GRASS = (28, 80, 42)
COLOR_GRASS_DARK = (22, 66, 34)
COLOR_ROAD = (42, 44, 52)
COLOR_ROAD_SHOULDER = (120, 120, 125)
COLOR_STRIPE_WHITE = (245, 245, 250)
COLOR_STRIPE_YELLOW = (255, 205, 30)
COLOR_GUARDRAIL = (180, 185, 195)
COLOR_HUD_BG = (15, 18, 26, 210)
COLOR_CYAN = (0, 240, 255)
COLOR_GOLD = (255, 215, 0)
COLOR_ORANGE = (255, 130, 20)
COLOR_RED = (255, 45, 45)
COLOR_NEON_GREEN = (50, 255, 120)

SAMPLE_RATE = 44100


# ------------------------------------------------------------------------------
# PROCEDURAL AUDIO SYNTHESIZER (No external sound files required)
# ------------------------------------------------------------------------------
class SoundEngine:
    """Generates procedural sound effects in real-time using NumPy & Pygame."""
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self.engine_channel = None
        self.nitro_channel = None
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=1024)
                pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self._bake_procedural_sounds()
        except Exception as e:
            print(f"[SoundEngine] Audio init disabled: {e}")
            self.enabled = False

    def _bake_procedural_sounds(self):
        # 1. Tire Screech
        self.sounds["screech"] = self._synth_screech()
        # 2. Nitro Whoosh
        self.sounds["nitro"] = self._synth_nitro()
        # 3. Coin Chime
        self.sounds["coin"] = self._synth_coin()
        # 4. Fuel Pickup
        self.sounds["fuel"] = self._synth_fuel()
        # 5. Crash Explosion
        self.sounds["crash"] = self._synth_crash()
        # 6. Close Call Zing
        self.sounds["close_call"] = self._synth_close_call()
        # 7. Engine Rhythms
        self.sounds["engine_idle"] = self._synth_engine(freq=75.0, duration=1.2)
        self.sounds["engine_mid"] = self._synth_engine(freq=130.0, duration=1.2)
        self.sounds["engine_high"] = self._synth_engine(freq=210.0, duration=1.2)

    def _synth_to_sound(self, wave: np.ndarray) -> pygame.mixer.Sound:
        max_val = np.max(np.abs(wave))
        if max_val > 0:
            wave = (wave / max_val) * 0.7
        stereo = np.zeros((len(wave), 2), dtype=np.int16)
        samples_16 = (wave * 32767).astype(np.int16)
        stereo[:, 0] = samples_16
        stereo[:, 1] = samples_16
        return pygame.sndarray.make_sound(stereo)

    def _synth_engine(self, freq: float, duration: float = 1.0) -> pygame.mixer.Sound:
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        sig = 0.5 * np.sin(2 * np.pi * freq * t)
        sig += 0.3 * np.sin(2 * np.pi * (freq * 2) * t + 0.3)
        sig += 0.2 * np.sin(2 * np.pi * (freq * 3) * t + 0.7)
        sig += 0.15 * np.sin(2 * np.pi * (freq * 4) * t + 1.2)
        sig = np.tanh(sig * 1.5)
        return self._synth_to_sound(sig)

    def _synth_screech(self, duration: float = 0.45) -> pygame.mixer.Sound:
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, len(t))
        carrier = np.sin(2 * np.pi * 2200 * t + np.sin(2 * np.pi * 40 * t) * 3)
        wave = (noise * 0.35 + carrier * 0.65) * np.exp(-1.8 * t)
        return self._synth_to_sound(wave)

    def _synth_nitro(self, duration: float = 0.8) -> pygame.mixer.Sound:
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, len(t))
        sweep = np.sin(2 * np.pi * (400 + 1200 * (t / duration) ** 1.5) * t)
        wave = (noise * 0.6 + sweep * 0.4) * np.sin(np.pi * (t / duration))
        return self._synth_to_sound(wave)

    def _synth_coin(self) -> pygame.mixer.Sound:
        duration = 0.25
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        half = len(t) // 2
        wave = np.zeros_like(t)
        wave[:half] = np.sin(2 * np.pi * 987.77 * t[:half]) * np.exp(-8 * t[:half])
        wave[half:] = np.sin(2 * np.pi * 1318.51 * (t[half:] - t[half])) * np.exp(-6 * (t[half:] - t[half]))
        return self._synth_to_sound(wave)

    def _synth_fuel(self) -> pygame.mixer.Sound:
        duration = 0.3
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        wave = np.sin(2 * np.pi * (520 + 350 * t) * t) * np.exp(-5 * t)
        return self._synth_to_sound(wave)

    def _synth_close_call(self) -> pygame.mixer.Sound:
        duration = 0.35
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        wave = np.sin(2 * np.pi * (800 + 800 * (t / duration)) * t) * np.exp(-4 * t)
        return self._synth_to_sound(wave)

    def _synth_crash(self) -> pygame.mixer.Sound:
        duration = 1.2
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, len(t))
        boom = np.sin(2 * np.pi * 60 * np.exp(-3 * t) * t)
        wave = (noise * 0.6 + boom * 0.7) * np.exp(-2.2 * t)
        return self._synth_to_sound(wave)

    def play(self, sound_name: str, volume: float = 1.0):
        if not self.enabled or sound_name not in self.sounds:
            return
        ch = pygame.mixer.find_channel()
        if ch:
            ch.set_volume(volume)
            ch.play(self.sounds[sound_name])

    def update_engine_audio(self, speed_ratio: float, is_nitro: bool):
        if not self.enabled:
            return
        if self.engine_channel is None or not self.engine_channel.get_busy():
            self.engine_channel = pygame.mixer.Channel(0)
            target = "engine_high" if speed_ratio > 0.65 else ("engine_mid" if speed_ratio > 0.3 else "engine_idle")
            if target in self.sounds:
                vol = 0.25 + 0.35 * speed_ratio
                self.engine_channel.set_volume(vol)
                self.engine_channel.play(self.sounds[target], loops=-1)


# ------------------------------------------------------------------------------
# PARTICLE & VISUAL FX SYSTEMS
# ------------------------------------------------------------------------------
class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'radius', 'life', 'max_life', 'drag')

    def __init__(self, x: float, y: float, vx: float, vy: float, color, radius: float, life: float = 0.6, drag: float = 0.94):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.life = life
        self.max_life = life
        self.drag = drag

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt * 60.0
        self.y += self.vy * dt * 60.0
        self.vx *= self.drag
        self.vy *= self.drag
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        t = max(0.0, self.life / self.max_life)
        cur_r = max(1, int(self.radius * t))
        alpha = int(255 * t)
        
        surf = pygame.Surface((cur_r * 2 + 2, cur_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (cur_r + 1, cur_r + 1), cur_r)
        surface.blit(surf, (int(self.x - cur_r - 1), int(self.y - cur_r - 1)), special_flags=pygame.BLEND_ADD)


class Skidmark:
    """Tire skid tracks left on asphalt."""
    __slots__ = ('x1', 'y1', 'x2', 'y2', 'alpha', 'width')

    def __init__(self, x1, y1, x2, y2, width=4):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.alpha = 140
        self.width = width

    def update(self, scroll_dy: float) -> bool:
        self.y1 += scroll_dy
        self.y2 += scroll_dy
        self.alpha -= 0.8
        return self.alpha > 0 and self.y1 < WINDOW_HEIGHT + 100

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        surf = pygame.Surface((abs(self.x2 - self.x1) + 20, abs(self.y2 - self.y1) + 20), pygame.SRCALPHA)
        min_x = min(self.x1, self.x2) - 10
        min_y = min(self.y1, self.y2) - 10
        p1 = (self.x1 - min_x, self.y1 - min_y)
        p2 = (self.x2 - min_x, self.y2 - min_y)
        pygame.draw.line(surf, (20, 20, 24, int(self.alpha)), p1, p2, self.width)
        surface.blit(surf, (min_x, min_y))


class FloatingText:
    """Floating combo/bonus score banner."""
    def __init__(self, text: str, x: float, y: float, color=COLOR_GOLD):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 1.0
        self.max_life = 1.0

    def update(self, dt: float) -> bool:
        self.y -= dt * 45.0
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        alpha = int(255 * (self.life / self.max_life))
        txt_surf = font.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        surface.blit(txt_surf, (int(self.x - txt_surf.get_width() // 2), int(self.y)))


# ------------------------------------------------------------------------------
# PROCEDURAL CAR VECTOR RENDERING
# ------------------------------------------------------------------------------
def draw_detailed_car(surface: pygame.Surface, x: float, y: float, w: int, h: int,
                      body_color, car_type: str = "sports", tilt_angle: float = 0.0,
                      is_braking: bool = False, is_nitro: bool = False, draw_headlights: bool = True):
    """Draws a sports car, sedan, truck, or police cruiser with procedural vector shapes."""
    car_surf = pygame.Surface((w + 40, h + 60), pygame.SRCALPHA)
    cx = (w + 40) // 2
    cy = (h + 60) // 2
    
    # 1. Wheels
    tire_w, tire_h = 6, 16
    wheel_offsets = [
        (-w // 2 + 1, -h // 2 + 12),
        (w // 2 - tire_w - 1, -h // 2 + 12),
        (-w // 2 + 1, h // 2 - 20),
        (w // 2 - tire_w - 1, h // 2 - 20)
    ]
    for ox, oy in wheel_offsets:
        pygame.draw.rect(car_surf, (15, 15, 18), (cx + ox, cy + oy, tire_w, tire_h), border_radius=2)
        pygame.draw.rect(car_surf, (80, 85, 95), (cx + ox + 1, cy + oy + 3, tire_w - 2, tire_h - 6))

    # 2. Main Chassis
    body_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    pygame.draw.rect(car_surf, body_color, body_rect, border_radius=10)
    darker_shade = tuple(max(0, c - 45) for c in body_color[:3])
    pygame.draw.rect(car_surf, darker_shade, body_rect, width=2, border_radius=10)

    # 3. Model Detailing
    if car_type == "sports":
        stripe_col = (255, 255, 255) if body_color[0] < 200 else (30, 30, 35)
        pygame.draw.rect(car_surf, stripe_col, (cx - 4, cy - h // 2 + 4, 3, h - 14))
        pygame.draw.rect(car_surf, stripe_col, (cx + 1, cy - h // 2 + 4, 3, h - 14))
        front_glass = pygame.Rect(cx - w // 2 + 5, cy - h // 2 + 20, w - 10, 14)
        pygame.draw.rect(car_surf, (30, 45, 65), front_glass, border_radius=4)
        pygame.draw.line(car_surf, (130, 175, 215), (front_glass.left + 3, front_glass.bottom - 3), (front_glass.right - 8, front_glass.top + 3), 2)
        rear_glass = pygame.Rect(cx - w // 2 + 6, cy + 8, w - 12, 12)
        pygame.draw.rect(car_surf, (30, 45, 65), rear_glass, border_radius=3)
        pygame.draw.rect(car_surf, darker_shade, (cx - w // 2 + 2, cy + h // 2 - 6, w - 4, 5), border_radius=2)
        
    elif car_type == "truck":
        bed_rect = pygame.Rect(cx - w // 2 + 2, cy - 8, w - 4, h // 2 + 6)
        pygame.draw.rect(car_surf, (160, 165, 175), bed_rect, border_radius=4)
        pygame.draw.rect(car_surf, (80, 85, 95), bed_rect, width=2, border_radius=4)
        for bar_y in range(bed_rect.top + 10, bed_rect.bottom - 5, 16):
            pygame.draw.line(car_surf, (110, 115, 125), (bed_rect.left + 4, bar_y), (bed_rect.right - 4, bar_y), 2)
        cab_glass = pygame.Rect(cx - w // 2 + 4, cy - h // 2 + 8, w - 8, 12)
        pygame.draw.rect(car_surf, (35, 50, 70), cab_glass, border_radius=2)

    elif car_type == "police":
        roof_rect = pygame.Rect(cx - w // 2, cy - 10, w, 26)
        pygame.draw.rect(car_surf, (245, 245, 250), roof_rect)
        front_glass = pygame.Rect(cx - w // 2 + 4, cy - h // 2 + 18, w - 8, 12)
        pygame.draw.rect(car_surf, (25, 40, 60), front_glass, border_radius=3)
        strobe = (pygame.time.get_ticks() // 120) % 2
        bar_left = (255, 30, 30) if strobe == 0 else (30, 120, 255)
        bar_right = (30, 120, 255) if strobe == 0 else (255, 30, 30)
        pygame.draw.rect(car_surf, bar_left, (cx - 10, cy - 2, 8, 5), border_radius=1)
        pygame.draw.rect(car_surf, bar_right, (cx + 2, cy - 2, 8, 5), border_radius=1)

    else:  # Sedan
        front_glass = pygame.Rect(cx - w // 2 + 4, cy - h // 2 + 16, w - 8, 13)
        pygame.draw.rect(car_surf, (30, 45, 65), front_glass, border_radius=3)
        rear_glass = pygame.Rect(cx - w // 2 + 5, cy + 10, w - 10, 11)
        pygame.draw.rect(car_surf, (30, 45, 65), rear_glass, border_radius=2)

    # 4. Headlights & Taillights
    hl_color = (255, 255, 220)
    pygame.draw.circle(car_surf, hl_color, (cx - w // 2 + 6, cy - h // 2 + 3), 3)
    pygame.draw.circle(car_surf, hl_color, (cx + w // 2 - 6, cy - h // 2 + 3), 3)

    tail_col = (255, 30, 30) if is_braking else (180, 25, 25)
    tail_r = 4 if is_braking else 3
    pygame.draw.circle(car_surf, tail_col, (cx - w // 2 + 5, cy + h // 2 - 3), tail_r)
    pygame.draw.circle(car_surf, tail_col, (cx + w // 2 - 5, cy + h // 2 - 3), tail_r)

    # 5. Nitro Exhaust Flames
    if is_nitro:
        flame_len = random.randint(18, 34)
        for pipe_x in [cx - 8, cx + 8]:
            f_poly1 = [(pipe_x - 3, cy + h // 2), (pipe_x + 3, cy + h // 2), (pipe_x, cy + h // 2 + flame_len)]
            pygame.draw.polygon(car_surf, (0, 200, 255, 220), f_poly1)
            f_poly2 = [(pipe_x - 1, cy + h // 2), (pipe_x + 1, cy + h // 2), (pipe_x, cy + h // 2 + flame_len // 2)]
            pygame.draw.polygon(car_surf, (255, 255, 200, 255), f_poly2)

    # Draw Car with Tilt
    if abs(tilt_angle) > 0.01:
        rotated_surf = pygame.transform.rotate(car_surf, math.degrees(-tilt_angle))
        rx = int(x - rotated_surf.get_width() // 2)
        ry = int(y - rotated_surf.get_height() // 2)
        surface.blit(rotated_surf, (rx, ry))
    else:
        surface.blit(car_surf, (int(x - cx), int(y - cy)))

    # Headlight Beams
    if draw_headlights:
        cone_surf = pygame.Surface((ROAD_WIDTH, 260), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surf, (255, 255, 220, 28), [(120, 260), (140, 260), (190, 0), (90, 0)])
        pygame.draw.polygon(cone_surf, (255, 255, 220, 28), [(160, 260), (180, 260), (230, 0), (130, 0)])
        surface.blit(cone_surf, (int(x - 150), int(y - h // 2 - 250)), special_flags=pygame.BLEND_ADD)


# ------------------------------------------------------------------------------
# ENTITIES: PLAYER, TRAFFIC, COLLECTIBLES
# ------------------------------------------------------------------------------
class PlayerCar:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = 44
        self.height = 84
        
        self.speed = 0.0
        self.min_speed = 0.0
        self.cruise_speed = 130.0
        self.max_speed = 220.0
        self.nitro_max_speed = 310.0
        
        self.lateral_speed = 360.0
        self.tilt_angle = 0.0
        self.is_braking = False
        self.is_nitro = False
        
        self.nitro = 100.0
        self.max_nitro = 100.0
        self.fuel = 100.0
        self.max_fuel = 100.0
        
        self.is_crashed = False
        self.crash_rot = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.width // 2 + 4), int(self.y - self.height // 2 + 4),
                           self.width - 8, self.height - 8)

    def update(self, dt: float, keys, particles, skids, sound_engine: SoundEngine):
        if self.is_crashed:
            self.speed = max(0.0, self.speed - dt * 260.0)
            self.crash_rot += dt * 360.0
            return

        wants_accel = keys[pygame.K_UP] or keys[pygame.K_w]
        wants_brake = keys[pygame.K_DOWN] or keys[pygame.K_s]
        wants_nitro = (keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]) and self.nitro > 5.0

        on_grass = (self.x < ROAD_LEFT + 25) or (self.x > ROAD_RIGHT - 25)
        top_limit = self.nitro_max_speed if wants_nitro else self.max_speed
        if on_grass:
            top_limit = min(top_limit, 85.0)

        # Nitro
        if wants_nitro and wants_accel:
            self.is_nitro = True
            self.nitro = max(0.0, self.nitro - dt * 32.0)
            self.speed = min(top_limit, self.speed + dt * 140.0)
            particles.append(Particle(self.x - 8, self.y + self.height // 2, random.uniform(-1, 1), random.uniform(3, 7), (0, 220, 255), 5.0, 0.4))
            particles.append(Particle(self.x + 8, self.y + self.height // 2, random.uniform(-1, 1), random.uniform(3, 7), (0, 220, 255), 5.0, 0.4))
        else:
            self.is_nitro = False
            self.nitro = min(self.max_nitro, self.nitro + dt * 6.0)

        # Acceleration
        if wants_accel:
            accel_rate = 95.0 if self.speed < 120 else 60.0
            self.speed = min(top_limit, self.speed + dt * accel_rate)
        elif not wants_nitro:
            if self.speed > self.cruise_speed:
                self.speed = max(self.cruise_speed, self.speed - dt * 45.0)
            elif self.speed < self.cruise_speed:
                self.speed = min(self.cruise_speed, self.speed + dt * 35.0)

        # Braking
        self.is_braking = wants_brake
        if wants_brake:
            self.speed = max(self.min_speed, self.speed - dt * 220.0)
            if self.speed > 80.0:
                particles.append(Particle(self.x - 14, self.y + 24, random.uniform(-2, 2), random.uniform(1, 3), (200, 205, 215), 4.0, 0.35))
                particles.append(Particle(self.x + 14, self.y + 24, random.uniform(-2, 2), random.uniform(1, 3), (200, 205, 215), 4.0, 0.35))

        # Fuel burn
        fuel_burn = 1.2 if not self.is_nitro else 3.2
        self.fuel = max(0.0, self.fuel - dt * fuel_burn)
        if self.fuel <= 0.0:
            self.speed = max(0.0, self.speed - dt * 50.0)

        # Steering
        steer = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: steer -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: steer += 1.0

        prev_x = self.x
        if steer != 0.0:
            speed_factor = min(1.2, max(0.3, self.speed / 130.0))
            self.x += steer * self.lateral_speed * speed_factor * dt
            target_tilt = steer * 0.12
            self.tilt_angle += (target_tilt - self.tilt_angle) * min(1.0, 14.0 * dt)
            
            if self.speed > 160.0 and random.random() < 0.35:
                skids.append(Skidmark(prev_x - 14, self.y + 20, self.x - 14, self.y + 22))
                skids.append(Skidmark(prev_x + 14, self.y + 20, self.x + 14, self.y + 22))
                particles.append(Particle(self.x, self.y + 20, random.uniform(-2, 2), random.uniform(0, 2), (210, 215, 225), 3.5, 0.3))
        else:
            self.tilt_angle += (0.0 - self.tilt_angle) * min(1.0, 12.0 * dt)

        self.x = max(ROAD_LEFT - 30, min(ROAD_RIGHT + 30, self.x))
        sound_engine.update_engine_audio(self.speed / self.max_speed, self.is_nitro)


class TrafficCar:
    TYPES = [
        {"type": "sports", "w": 42, "h": 82, "color": (230, 40, 40), "speed_range": (140, 180)},
        {"type": "sports", "w": 42, "h": 82, "color": (255, 210, 20), "speed_range": (135, 175)},
        {"type": "sedan", "w": 44, "h": 84, "color": (35, 105, 215), "speed_range": (100, 130)},
        {"type": "sedan", "w": 44, "h": 84, "color": (40, 180, 110), "speed_range": (95, 125)},
        {"type": "sedan", "w": 44, "h": 84, "color": (160, 165, 175), "speed_range": (105, 130)},
        {"type": "truck", "w": 48, "h": 110, "color": (195, 95, 30), "speed_range": (75, 100)},
        {"type": "police", "w": 44, "h": 84, "color": (20, 20, 25), "speed_range": (145, 190)}
    ]

    def __init__(self, lane_idx: int, y: float):
        cfg = random.choice(self.TYPES)
        self.car_type = cfg["type"]
        self.width = cfg["w"]
        self.height = cfg["h"]
        self.color = cfg["color"]
        self.lane_idx = lane_idx
        self.x = float(LANE_CENTERS[lane_idx])
        self.target_x = self.x
        self.y = y
        self.speed = float(random.randint(*cfg["speed_range"]))
        self.close_call_checked = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.width // 2 + 3), int(self.y - self.height // 2 + 3),
                           self.width - 6, self.height - 6)

    def update(self, dt: float, player_speed: float):
        rel_speed = (self.speed - player_speed) * 4.2
        self.y -= rel_speed * dt
        if abs(self.x - self.target_x) > 1.0:
            self.x += (self.target_x - self.x) * min(1.0, 6.0 * dt)


class Collectible:
    def __init__(self, kind: str, x: float, y: float):
        self.kind = kind
        self.x = x
        self.y = y
        self.radius = 16
        self.anim_t = random.uniform(0, math.pi * 2)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    def update(self, dt: float, player_speed: float):
        self.anim_t += dt * 5.0
        self.y += player_speed * 4.2 * dt

    def draw(self, surface: pygame.Surface, font_small: pygame.font.Font):
        pulse = 0.85 + 0.15 * math.sin(self.anim_t)
        r = int(self.radius * pulse)
        px, py = int(self.x), int(self.y)

        if self.kind == "coin":
            spin_w = max(4, int(r * abs(math.cos(self.anim_t))))
            pygame.draw.ellipse(surface, COLOR_GOLD, (px - spin_w, py - r, spin_w * 2, r * 2))
            pygame.draw.ellipse(surface, (255, 245, 140), (px - spin_w + 2, py - r + 2, max(2, (spin_w - 2) * 2), (r - 2) * 2), 1)
        elif self.kind == "nitro":
            pygame.draw.rect(surface, COLOR_CYAN, (px - 8, py - 12, 16, 24), border_radius=4)
            pygame.draw.rect(surface, (255, 255, 255), (px - 4, py - 16, 8, 4), border_radius=1)
            txt = font_small.render("N2O", True, (0, 30, 45))
            surface.blit(txt, (px - txt.get_width() // 2, py - txt.get_height() // 2))
        elif self.kind == "fuel":
            pygame.draw.rect(surface, COLOR_RED, (px - 10, py - 12, 20, 24), border_radius=4)
            pygame.draw.rect(surface, (220, 220, 220), (px - 6, py - 16, 6, 5))
            txt = font_small.render("GAS", True, (255, 255, 255))
            surface.blit(txt, (px - txt.get_width() // 2, py - txt.get_height() // 2))


# ------------------------------------------------------------------------------
# HIGHWAY SCENERY & HUD
# ------------------------------------------------------------------------------
class HighwayEnvironment:
    def __init__(self):
        self.scroll_y = 0.0
        self.trees = [
            {"x": random.choice([random.randint(40, ROAD_LEFT - 50), random.randint(ROAD_RIGHT + 50, WINDOW_WIDTH - 40)]),
             "y": random.randint(0, WINDOW_HEIGHT),
             "r": random.randint(18, 32),
             "shade": random.choice([(34, 110, 55), (42, 128, 64), (28, 95, 46)])}
            for _ in range(24)
        ]

    def update(self, dt: float, player_speed: float):
        scroll_speed = player_speed * 4.2
        self.scroll_y = (self.scroll_y + scroll_speed * dt) % 80.0
        for t in self.trees:
            t["y"] += scroll_speed * dt
            if t["y"] > WINDOW_HEIGHT + 40:
                t["y"] = -40
                t["x"] = random.choice([random.randint(40, ROAD_LEFT - 50), random.randint(ROAD_RIGHT + 50, WINDOW_WIDTH - 40)])

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_GRASS)
        for y in range(-80, WINDOW_HEIGHT + 80, 80):
            sy = int((y + self.scroll_y) % (WINDOW_HEIGHT + 160) - 80)
            pygame.draw.rect(surface, COLOR_GRASS_DARK, (0, sy, ROAD_LEFT, 40))
            pygame.draw.rect(surface, COLOR_GRASS_DARK, (ROAD_RIGHT, sy, WINDOW_WIDTH - ROAD_RIGHT, 40))

        shoulder_w = 18
        pygame.draw.rect(surface, COLOR_ROAD_SHOULDER, (ROAD_LEFT - shoulder_w, 0, shoulder_w, WINDOW_HEIGHT))
        pygame.draw.rect(surface, COLOR_ROAD_SHOULDER, (ROAD_RIGHT, 0, shoulder_w, WINDOW_HEIGHT))

        block_h = 30
        for y in range(-60, WINDOW_HEIGHT + 60, block_h):
            sy = int((y + self.scroll_y) % (WINDOW_HEIGHT + 120) - 60)
            col = (240, 240, 245) if (y // block_h) % 2 == 0 else (215, 45, 45)
            pygame.draw.rect(surface, col, (ROAD_LEFT - shoulder_w, sy, shoulder_w, block_h))
            pygame.draw.rect(surface, col, (ROAD_RIGHT, sy, shoulder_w, block_h))

        pygame.draw.rect(surface, COLOR_ROAD, (ROAD_LEFT, 0, ROAD_WIDTH, WINDOW_HEIGHT))
        pygame.draw.line(surface, COLOR_STRIPE_YELLOW, (ROAD_LEFT + 4, 0), (ROAD_LEFT + 4, WINDOW_HEIGHT), 3)
        pygame.draw.line(surface, COLOR_STRIPE_YELLOW, (ROAD_RIGHT - 4, 0), (ROAD_RIGHT - 4, WINDOW_HEIGHT), 3)

        dash_h, dash_gap = 42, 38
        stripe_step = dash_h + dash_gap
        for lane_i in range(1, NUM_LANES):
            lx = ROAD_LEFT + lane_i * LANE_WIDTH
            for y in range(-stripe_step, WINDOW_HEIGHT + stripe_step, stripe_step):
                sy = int((y + self.scroll_y) % (WINDOW_HEIGHT + stripe_step * 2) - stripe_step)
                pygame.draw.line(surface, COLOR_STRIPE_WHITE, (lx, sy), (lx, sy + dash_h), 3)

        pygame.draw.line(surface, COLOR_GUARDRAIL, (ROAD_LEFT - shoulder_w, 0), (ROAD_LEFT - shoulder_w, WINDOW_HEIGHT), 4)
        pygame.draw.line(surface, COLOR_GUARDRAIL, (ROAD_RIGHT + shoulder_w, 0), (ROAD_RIGHT + shoulder_w, WINDOW_HEIGHT), 4)

        for t in self.trees:
            pygame.draw.circle(surface, (15, 45, 25), (t["x"] + 3, int(t["y"]) + 4), t["r"])
            pygame.draw.circle(surface, t["shade"], (t["x"], int(t["y"])), t["r"])
            pygame.draw.circle(surface, tuple(min(255, c + 25) for c in t["shade"]), (t["x"] - 3, int(t["y"]) - 4), t["r"] // 2)


class HUD:
    def __init__(self):
        pygame.font.init()
        self.font_huge = pygame.font.SysFont("Impact, Arial Black, sans-serif", 46)
        self.font_title = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 26, bold=True)
        self.font_med = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.font_digital = pygame.font.SysFont("Consolas, Courier, monospace", 28, bold=True)

    def draw(self, surface: pygame.Surface, player: PlayerCar, score: int, high_score: int,
             distance_m: float, combo: int, is_muted: bool):
        top_h = 60
        top_surf = pygame.Surface((WINDOW_WIDTH, top_h), pygame.SRCALPHA)
        pygame.draw.rect(top_surf, COLOR_HUD_BG, (0, 0, WINDOW_WIDTH, top_h))
        pygame.draw.line(top_surf, (0, 240, 255, 120), (0, top_h - 1), (WINDOW_WIDTH, top_h - 1), 2)
        surface.blit(top_surf, (0, 0))

        # Score & Distance
        surface.blit(self.font_small.render("SCORE", True, (160, 180, 205)), (30, 8))
        surface.blit(self.font_digital.render(f"{score:07d}", True, COLOR_CYAN), (30, 24))

        surface.blit(self.font_small.render("BEST", True, (160, 180, 205)), (190, 8))
        surface.blit(self.font_digital.render(f"{high_score:07d}", True, COLOR_GOLD), (190, 24))

        dist_km = distance_m / 1000.0
        surface.blit(self.font_small.render("DISTANCE", True, (160, 180, 205)), (WINDOW_WIDTH - 200, 8))
        surface.blit(self.font_digital.render(f"{dist_km:05.2f} KM", True, (255, 255, 255)), (WINDOW_WIDTH - 200, 24))

        # Speedometer & Gauges
        dash_w, dash_h = 230, 165
        dash_x, dash_y = WINDOW_WIDTH - dash_w - 20, WINDOW_HEIGHT - dash_h - 20

        dash_panel = pygame.Surface((dash_w, dash_h), pygame.SRCALPHA)
        pygame.draw.rect(dash_panel, COLOR_HUD_BG, (0, 0, dash_w, dash_h), border_radius=14)
        pygame.draw.rect(dash_panel, (0, 240, 255, 130), (0, 0, dash_w, dash_h), width=2, border_radius=14)
        surface.blit(dash_panel, (dash_x, dash_y))

        speed_int = int(player.speed)
        speed_color = COLOR_CYAN if not player.is_nitro else COLOR_ORANGE
        surface.blit(self.font_huge.render(f"{speed_int:03d}", True, speed_color), (dash_x + 22, dash_y + 12))
        surface.blit(self.font_small.render("KM/H", True, (170, 190, 210)), (dash_x + 130, dash_y + 36))

        arc_rect = pygame.Rect(dash_x + 155, dash_y + 15, 60, 60)
        speed_ratio = min(1.0, player.speed / player.nitro_max_speed)
        end_angle = -math.pi * 0.2 + speed_ratio * (math.pi * 1.4)
        pygame.draw.arc(surface, (50, 60, 75), arc_rect, -math.pi * 0.2, math.pi * 1.2, 5)
        if speed_ratio > 0.05:
            pygame.draw.arc(surface, speed_color, arc_rect, -math.pi * 0.2, end_angle, 5)

        # Nitro
        surface.blit(self.font_small.render("NITRO [SPACE]", True, (160, 220, 255)), (dash_x + 22, dash_y + 78))
        nitro_pct = max(0.0, min(1.0, player.nitro / player.max_nitro))
        bar_w, bar_h = 186, 10
        pygame.draw.rect(surface, (25, 30, 42), (dash_x + 22, dash_y + 96, bar_w, bar_h), border_radius=4)
        if nitro_pct > 0:
            pygame.draw.rect(surface, COLOR_CYAN, (dash_x + 22, dash_y + 96, int(bar_w * nitro_pct), bar_h), border_radius=4)

        # Fuel
        surface.blit(self.font_small.render("FUEL", True, (255, 170, 170)), (dash_x + 22, dash_y + 116))
        fuel_pct = max(0.0, min(1.0, player.fuel / player.max_fuel))
        fuel_col = COLOR_RED if fuel_pct < 0.25 else COLOR_NEON_GREEN
        pygame.draw.rect(surface, (25, 30, 42), (dash_x + 22, dash_y + 134, bar_w, bar_h), border_radius=4)
        if fuel_pct > 0:
            pygame.draw.rect(surface, fuel_col, (dash_x + 22, dash_y + 134, int(bar_w * fuel_pct), bar_h), border_radius=4)

        if fuel_pct < 0.2 and (pygame.time.get_ticks() // 300) % 2 == 0:
            warn_txt = self.font_med.render("⚠️ LOW FUEL!", True, COLOR_RED)
            surface.blit(warn_txt, (WINDOW_WIDTH // 2 - warn_txt.get_width() // 2, 75))

        if combo > 1:
            surface.blit(self.font_title.render(f"{combo}x COMBO!", True, COLOR_GOLD), (30, 75))

        if is_muted:
            mute_txt = self.font_small.render("[Muted - M]", True, (255, 120, 120))
            surface.blit(mute_txt, (WINDOW_WIDTH // 2 - mute_txt.get_width() // 2, 8))


# ------------------------------------------------------------------------------
# MASTER GAME CONTROLLER
# ------------------------------------------------------------------------------
class TurboHorizonGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("✦ TURBO HORIZON: HIGHWAY SPEED RACER ✦")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.sound = SoundEngine()
        self.env = HighwayEnvironment()
        self.hud = HUD()

        self.player = PlayerCar(LANE_CENTERS[1], WINDOW_HEIGHT - 160)
        self.traffic: list[TrafficCar] = []
        self.collectibles: list[Collectible] = []
        self.particles: list[Particle] = []
        self.skids: list[Skidmark] = []
        self.floating_texts: list[FloatingText] = []

        self.score = 0
        self.high_score = 0
        self.distance_m = 0.0
        self.coins_collected = 0
        self.close_calls = 0
        self.combo = 1
        self.combo_timer = 0.0

        self.traffic_timer = 0.0
        self.item_timer = 0.0

        self.is_paused = False
        self.is_game_over = False
        self.is_muted = False
        self.screen_shake = 0.0

    def reset_game(self):
        self.player = PlayerCar(LANE_CENTERS[1], WINDOW_HEIGHT - 160)
        self.traffic.clear()
        self.collectibles.clear()
        self.particles.clear()
        self.skids.clear()
        self.floating_texts.clear()
        self.score = 0
        self.distance_m = 0.0
        self.coins_collected = 0
        self.close_calls = 0
        self.combo = 1
        self.combo_timer = 0.0
        self.is_game_over = False
        self.screen_shake = 0.0

    def spawn_traffic(self):
        lane = random.randint(0, NUM_LANES - 1)
        too_close = any(abs(t.x - LANE_CENTERS[lane]) < 30 and t.y < 80 for t in self.traffic)
        if not too_close:
            self.traffic.append(TrafficCar(lane, y=-120))

    def spawn_collectible(self):
        lane = random.randint(0, NUM_LANES - 1)
        lx = LANE_CENTERS[lane]
        rand_val = random.random()
        if rand_val < 0.55:
            for i in range(3):
                self.collectibles.append(Collectible("coin", lx, -80 - i * 40))
        elif rand_val < 0.80:
            self.collectibles.append(Collectible("nitro", lx, -80))
        else:
            self.collectibles.append(Collectible("fuel", lx, -80))

    def handle_collisions(self):
        p_rect = self.player.rect

        for car in self.traffic:
            c_rect = car.rect
            if p_rect.colliderect(c_rect) and not self.player.is_crashed:
                self.player.is_crashed = True
                self.is_game_over = True
                self.screen_shake = 22.0
                self.sound.play("crash")
                for _ in range(50):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(2, 9)
                    self.particles.append(Particle(
                        self.player.x, self.player.y,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        random.choice([(255, 200, 30), (255, 60, 20), (180, 185, 195)]),
                        random.uniform(3, 7), life=random.uniform(0.6, 1.4)
                    ))
                break

            if not car.close_call_checked and not self.player.is_crashed:
                if abs(self.player.x - car.x) < (self.player.width + car.width) * 0.75:
                    if abs(self.player.y - car.y) < 70 and self.player.speed > 130:
                        car.close_call_checked = True
                        self.close_calls += 1
                        self.combo += 1
                        self.combo_timer = 2.5
                        bonus = 250 * self.combo
                        self.score += bonus
                        self.floating_texts.append(FloatingText(f"CLOSE CALL! +{bonus}", self.player.x, self.player.y - 40, COLOR_GOLD))
                        self.sound.play("close_call")

        for item in self.collectibles[:]:
            if p_rect.colliderect(item.rect) and not self.player.is_crashed:
                self.collectibles.remove(item)
                if item.kind == "coin":
                    self.coins_collected += 1
                    pts = 100 * self.combo
                    self.score += pts
                    self.floating_texts.append(FloatingText(f"+{pts}", item.x, item.y, COLOR_GOLD))
                    self.sound.play("coin")
                elif item.kind == "nitro":
                    self.player.nitro = min(self.player.max_nitro, self.player.nitro + 50.0)
                    self.floating_texts.append(FloatingText("+NITRO", item.x, item.y, COLOR_CYAN))
                    self.sound.play("fuel")
                elif item.kind == "fuel":
                    self.player.fuel = min(self.player.max_fuel, self.player.fuel + 45.0)
                    self.floating_texts.append(FloatingText("+FUEL", item.x, item.y, COLOR_NEON_GREEN))
                    self.sound.play("fuel")

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(0.05, dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_m:
                        self.is_muted = not self.is_muted
                        if self.is_muted:
                            pygame.mixer.pause()
                        else:
                            pygame.mixer.unpause()
                    elif event.key == pygame.K_r and self.is_game_over:
                        self.reset_game()

            if self.is_paused:
                self._draw_pause()
                pygame.display.flip()
                continue

            keys = pygame.key.get_pressed()

            if not self.is_game_over:
                dist_delta = (self.player.speed * (1000.0 / 3600.0)) * dt
                self.distance_m += dist_delta
                speed_score_mult = 1.0 if not self.player.is_nitro else 2.5
                self.score += int(self.player.speed * 0.15 * speed_score_mult)
                if self.score > self.high_score:
                    self.high_score = self.score

                if self.combo > 1:
                    self.combo_timer -= dt
                    if self.combo_timer <= 0:
                        self.combo = 1

                self.traffic_timer += dt
                spawn_interval = max(0.65, 1.8 - (self.player.speed / self.player.max_speed) * 0.8)
                if self.traffic_timer >= spawn_interval:
                    self.traffic_timer = 0.0
                    self.spawn_traffic()

                self.item_timer += dt
                if self.item_timer >= 3.2:
                    self.item_timer = 0.0
                    self.spawn_collectible()

            self.player.update(dt, keys, self.particles, self.skids, self.sound)
            self.env.update(dt, self.player.speed)

            for car in self.traffic:
                car.update(dt, self.player.speed)
            self.traffic = [c for c in self.traffic if -250 < c.y < WINDOW_HEIGHT + 250]

            for item in self.collectibles:
                item.update(dt, self.player.speed)
            self.collectibles = [it for it in self.collectibles if it.y < WINDOW_HEIGHT + 50]

            self.particles = [p for p in self.particles if p.update(dt)]
            scroll_dy = self.player.speed * 4.2 * dt
            self.skids = [s for s in self.skids if s.update(scroll_dy)]
            self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

            if not self.player.is_crashed:
                self.handle_collisions()

            if self.screen_shake > 0:
                self.screen_shake = max(0.0, self.screen_shake - dt * 30.0)

            shake_x = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            shake_y = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            
            render_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.env.draw(render_surf)

            for skid in self.skids:
                skid.draw(render_surf)

            for item in self.collectibles:
                item.draw(render_surf, self.hud.font_small)

            for car in self.traffic:
                draw_detailed_car(render_surf, car.x, car.y, car.width, car.height, car.color,
                                  car_type=car.car_type, tilt_angle=0.0, draw_headlights=False)

            draw_detailed_car(
                render_surf, self.player.x, self.player.y,
                self.player.width, self.player.height,
                body_color=(235, 30, 45),
                car_type="sports",
                tilt_angle=self.player.tilt_angle if not self.player.is_crashed else self.player.crash_rot,
                is_braking=self.player.is_braking,
                is_nitro=self.player.is_nitro,
                draw_headlights=True
            )

            for p in self.particles:
                p.draw(render_surf)

            for ft in self.floating_texts:
                ft.draw(render_surf, self.hud.font_med)

            self.screen.blit(render_surf, (int(shake_x), int(shake_y)))
            self.hud.draw(self.screen, self.player, self.score, self.high_score,
                          self.distance_m, self.combo, self.is_muted)

            if self.is_game_over:
                self._draw_game_over()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _draw_pause(self):
        dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dim.fill((10, 15, 25, 190))
        self.screen.blit(dim, (0, 0))

        txt_p = self.hud.font_huge.render("PAUSED", True, COLOR_CYAN)
        txt_sub = self.hud.font_med.render("Press [P] or [ESC] to Resume", True, (220, 230, 240))
        self.screen.blit(txt_p, (WINDOW_WIDTH // 2 - txt_p.get_width() // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(txt_sub, (WINDOW_WIDTH // 2 - txt_sub.get_width() // 2, WINDOW_HEIGHT // 2 + 15))

    def _draw_game_over(self):
        dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 8, 10, 210))
        self.screen.blit(dim, (0, 0))

        pw, ph = 460, 360
        px = (WINDOW_WIDTH - pw) // 2
        py = (WINDOW_HEIGHT - ph) // 2
        
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 24, 34, 240), (0, 0, pw, ph), border_radius=16)
        pygame.draw.rect(panel, (255, 45, 45, 180), (0, 0, pw, ph), width=2, border_radius=16)
        self.screen.blit(panel, (px, py))

        txt_crashed = self.hud.font_huge.render("CRASHED!", True, COLOR_RED)
        self.screen.blit(txt_crashed, (WINDOW_WIDTH // 2 - txt_crashed.get_width() // 2, py + 22))

        lines = [
            f"Final Score:      {self.score:,}",
            f"High Score:       {self.high_score:,}",
            f"Distance Driven:  {self.distance_m / 1000.0:.2f} km",
            f"Close Calls:      {self.close_calls}",
            f"Coins Collected:  {self.coins_collected}"
        ]
        
        cur_y = py + 95
        for line in lines:
            surf_l = self.hud.font_med.render(line, True, (230, 235, 245))
            self.screen.blit(surf_l, (px + 45, cur_y))
            cur_y += 32

        txt_restart = self.hud.font_title.render("Press [R] to Race Again", True, COLOR_CYAN)
        self.screen.blit(txt_restart, (WINDOW_WIDTH // 2 - txt_restart.get_width() // 2, py + ph - 55))


if __name__ == "__main__":
    game = TurboHorizonGame()
    game.run()