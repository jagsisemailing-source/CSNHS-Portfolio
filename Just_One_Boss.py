import sys
import pygame as pg
import random as r
import os
import math
from PIL import Image

pg.init()

w = 1500
h = 900
screen = pg.display.set_mode((w, h))
pg.display.set_caption("Just One Boss")

script_folder = os.path.dirname(__file__)
background_img = pg.image.load(os.path.join(script_folder, '10k.png')).convert()
background_img = pg.transform.scale(background_img, (w, h))

player_img = os.path.join(script_folder, 'player.png')

center_x = w // 2

clock = pg.time.Clock()
fps = 60
game_state = "START"
big_font = pg.font.SysFont("Arial", 100)

# transitions stuff
going_to_start = False
going_to_ui = False
transition_val = 0
transition_spd = 0.02
menu_y = 0
expansion_val = 0

def show_opening():
    """
    Displays the opening transition animation with a black box expanding from the center.
    """
    current_w = int(w * transition_val)
    black_box = pg.Rect(center_x - current_w // 2, 0, current_w, h)
    screen.blit(background_img, (0, 0))
    pg.draw.rect(screen, (0, 0, 0), black_box)
    show_menu()

def show_menu():
    """
    Renders the main menu title text in the center of the screen.
    """
    title = big_font.render("JUST ONE B<O>SS", True, (255, 255, 255))
    title_pos = title.get_rect(center=(center_x, 80 + menu_y))
    screen.blit(title, title_pos)

def draw_ui_transition():
    """
    Creates a vertical-to-horizontal expanding white rectangle transition effect.
    """
    global expansion_val
    ui_w = w - 500
    ui_h = 400
    ui_x = (w - ui_w) // 2
    ui_y = h - ui_h - 100
    cx = w // 2
    cy = ui_y // 2 + 400

    screen.fill((0, 0, 0))
    if expansion_val <= 25:
        pg.draw.rect(screen, (255, 255, 255), (cx, cy - ((ui_y // 25) * expansion_val) // 2, 1,
                                     (ui_h // 25) * expansion_val), 10)
    elif expansion_val <= 50:
        p = expansion_val - 25
        pg.draw.rect(screen, (255, 255, 255), (cx - ((ui_x // 25) * p * 2), ui_y, 1 + (ui_w // 25) * p, ui_h), 10)

def draw_ui_box():
    """
    Draws the main UI border rectangle at the bottom of the screen.
    """
    ui_w = w - 500
    ui_h = 400
    ui_x = (w - ui_w) // 2
    ui_y = h - ui_h - 100
    pg.draw.rect(screen, (255, 255, 255), ((w-ui_w) // 2, h - 500, w - 500, 400), 10)

def draw_health_bar(where, boss_obj):
    """
    Renders the boss health bar at the top center of the screen.
    """
    bar_w = 300
    bar_h = 25
    bar_x = w // 2 - bar_w // 2
    bar_y = 50
    phase_now = boss_obj.current_phase
    hp = boss_obj.hp_dict.get(phase_now, 0)
    pg.draw.rect(where, (150, 150, 150), (bar_x, bar_y, bar_w, bar_h))
    if hp > 0:
        pg.draw.rect(where, (0, 255, 0), (bar_x, bar_y, bar_w * (hp / 3), bar_h))
    pg.draw.rect(where, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2)

class Boss:
    def __init__(self, g1, g2, g3, g4, m1, m2, m3, m4, x=750, y=150):
        """
        Initializes the boss with animations, music, and combat parameters.
        """
        self.x = x
        self.y = y
        self.current_phase = 0
        self.fra = 0
        self.frame_spd = 0.15
        self.vol = 1
        self.hp_dict = {1: 3, 2: 3, 3: 3, 4: 3}
        self.music_chans = {}
        self.animations = {1: self.load(g1), 2: self.load(g2), 3: self.load(g3), 4: self.load(g4)}
        self.music_files = {1: pg.mixer.Sound(m1), 2: pg.mixer.Sound(m2), 3: pg.mixer.Sound(m3), 4: pg.mixer.Sound(m4)}
        for snd in self.music_files.values():
            snd.set_volume(self.vol / 10)
    
    def load(self, gif_file):
        """
        Loads and converts GIF frames into Pygame surfaces for animation.
        """
        if gif_file is None:
            return None
        frames = []
        img = Image.open(gif_file)
        for frame_num in range(img.n_frames):
            img.seek(frame_num)
            f = img.convert("RGBA")
            d = f.tobytes()
            pg_frame = pg.image.fromstring(d, f.size, "RGBA").convert_alpha()
            frames.append(pg_frame)
        return frames if frames else None
    
    def next(self):
        """
        Advances the boss to the next combat phase and plays phase-specific music.
        """
        if self.current_phase > 1:
            self.music_chans[self.current_phase].stop()
        self.current_phase = self.current_phase + 1 if self.current_phase < 4 else 1
        self.frame = 0
        snd = self.music_files[self.current_phase]
        ch = snd.play(-1)
        self.music_chans[self.current_phase] = ch
        ch.set_volume(self.vol / 10)
    
    def draw_me(self, where):
        """
        Renders the current boss animation frame, scaled and centered in the play area.
        """
        frames = self.animations.get(self.current_phase)
        if not frames:
            return
        if self.current_phase == 'special' and getattr(self, 'hold_last', False):
            frm = frames[-1]
        else:
            self.fra += self.frame_spd
            if self.fra >= len(frames):
                self.fra = 0
            frm = frames[int(self.fra)]
        scale_up = 6
        new_w = frm.get_width() * scale_up
        new_h = frm.get_height() * scale_up
        frm = pg.transform.scale(frm, (new_w, new_h))
        x_pos = w // 2 - new_w // 2
        border_h = 400
        rect_y = h - border_h - 100
        y_pos = (0 + rect_y) // 2 - new_h // 2
        where.blit(frm, (x_pos, y_pos))
    
    def custom_anim(self, gif_path, hold_last=True):
        """
        Plays a special animation sequence, interrupting current music and visuals.
        """
        for ch in self.music_chans.values():
            if ch.get_busy():
                ch.stop()
        
        self.animations['special'] = self.load(gif_path)
        self.current_phase = 'special'
        self.frame_num = 0
        self.hold_last = hold_last
    
    def mute_toggle(self):
        """
        Toggles audio mute state for all boss music tracks.
        """
        if getattr(self, "is_muted", False):
            for snd in self.music_files.values():
                snd.set_volume(self.vol / 10)
            self.is_muted = False
        else:
            for snd in self.music_files.values():
                snd.set_volume(0)
            self.is_muted = True
    
    def vol_up(self):
        """
        Increases the volume level for all boss music by one increment.
        """
        if getattr(self, "is_muted", False):
            return
        self.vol = min(self.vol + 1, 10)
        for snd in self.music_files.values():
            snd.set_volume(self.vol / 10)
    
    def vol_down(self):
        """
        Decreases the volume level for all boss music by one increment.
        """
        if getattr(self, "is_muted", False):
            return
        self.vol = max(self.vol - 1, 0)
        for snd in self.music_files.values():
            snd.set_volume(self.vol / 10)

class PlayerChar:
    def __init__(self, img_file, start_x=0, start_y=0, spd=450):
        """
        Initializes the player character with sprite, hitbox, and movement properties.
        """
        self.sprite = pg.image.load(img_file).convert_alpha()
        self.sprite = pg.transform.scale(self.sprite, (50, 50))
        self.rect = self.sprite.get_rect(topleft=(start_x, start_y))
        
        hit_w = 20
        hit_h = 20
        self.hit_off_x = (self.rect.width - hit_w) // 2
        self.hit_off_y = (self.rect.height - hit_h) // 2
        self.hitbox = pg.Rect(
            self.rect.x + self.hit_off_x,
            self.rect.y + self.hit_off_y,
            hit_w,
            hit_h
        )
        
        self.move_spd = spd
        self.x = float(start_x)
        self.y = float(start_y)
        self.lives = 10
        self.invincible = 0.0
        self.hit_flash = 0.0
        self.up = False
        self.down = False
        self.right = False
        self.left = False
    
    def move(self, dt, bounds):
        """
        Updates player position based on input, delta time, and screen boundaries.
        """
        dx, dy = 0, 0
        if self.up: dy -= 1
        if self.down: dy += 1
        if self.right: dx += 1
        if self.left: dx -= 1
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
        
        self.x += dx * self.move_spd * dt
        self.y += dy * self.move_spd * dt
        
        self.rect.topleft = (round(self.x), round(self.y))
        self.rect.clamp_ip(bounds)
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        
        self.hitbox.center = self.rect.center
        
        if self.invincible > 0: self.invincible -= dt
        if self.hit_flash > 0: self.hit_flash -= dt
    
    def hit(self):
        """
        Registers a hit on the player, reducing lives and activating invincibility.
        """
        if self.invincible <= 0 and self.lives > 0:
            self.lives -= 1
            self.invincible = 2.0
            self.hit_flash = 0.5
    
    def show_lives(self, where):
        """
        Displays the player's remaining lives as green circles with hit effects.
        """
        rad = 15
        gap = 10
        for i in range(10):
            x_pos = 20 + i * (rad * 2 + gap)
            y_pos = 20
            if i < self.lives:
                col = (0, 255, 0)
            else:
                col = (150, 150, 150)
            if self.hit_flash > 0 and i == self.lives:
                col = (255, 255, 255)
                shake_x = r.randint(-3, 3)
                shake_y = r.randint(-3, 3)
                pg.draw.circle(where, col, (x_pos + shake_x, y_pos + shake_y), rad)
                pg.draw.circle(where, (0, 0, 0), (x_pos + shake_x, y_pos + shake_y), rad, 2)
            else:
                pg.draw.circle(where, col, (x_pos, y_pos), rad)
                pg.draw.circle(where, (0, 0, 0), (x_pos, y_pos), rad, 2)

class BaseAttack:
    def __init__(self, area):
        """
        Base class for all boss attacks with common activation properties.
        """
        self.area = area
        self.active = False
    
    def start(self):
        """
        Activates the attack sequence.
        """
        self.active = True
    
    def update(self, dt, plr):
        """
        Updates attack logic over time and checks for player collisions.
        """
        pass
    
    def draw(self, where, plr):
        """
        Renders attack visuals to the specified surface.
        """
        pass
    
    def done(self):
        """
        Returns True when the attack sequence has completed.
        """
        return not self.active

class GreenBallAttack(BaseAttack):
    def __init__(self, area, boss_ref):
        """
        Creates a green ball attack that players can collect to damage the boss.
        """
        super().__init__(area)
        self.boss_ref = boss_ref
        self.size = 20
        self.pos = (0, 0)
        self.got = False
    
    def start(self):
        """
        Activates the green ball at a random position within the play area.
        """
        super().start()
        self.got = False
        self.pos = (
            r.randint(self.area.left + self.size, self.area.right - self.size),
            r.randint(self.area.top + self.size, self.area.bottom - self.size)
        )
    
    def update(self, dt, plr):
        """
        Checks for player collision with the green ball and applies boss damage.
        """
        if not self.active:
            return
        dx = self.pos[0] - plr.hitbox.centerx
        dy = self.pos[1] - plr.hitbox.centery
        dist = math.hypot(dx, dy)
        if dist <= self.size + plr.hitbox.width // 2:
            self.got = True
            self.active = False
            phase_now = self.boss_ref.current_phase
            if self.boss_ref.hp_dict[phase_now] > 0:
                self.boss_ref.hp_dict[phase_now] -= 1
    
    def draw(self, where, plr):
        """
        Renders the green ball as a filled circle with a white border.
        """
        if self.active:
            pg.draw.circle(where, (0, 255, 0), (int(self.pos[0]), int(self.pos[1])), self.size)
            pg.draw.circle(where, (255, 255, 255), (int(self.pos[0]), int(self.pos[1])), self.size, 2)

class BoomCircle:
    def __init__(self, x, y, max_r=60, flash=0.12, purple_t=0.2, warn_spd=160):
        """
        Individual expanding circle for the BoomAttack with visual progression states.
        """
        self.x = x
        self.y = y
        self.radius = 10
        self.max_r = max_r
        self.purple_r = 0
        self.flash_t = 0.0
        self.flash_spd = flash
        self.flash_on = True
        self.state = "warning"
        self.timer = 0.0
        self.purple_time = purple_t
        self.warn_spd = warn_spd
    
    def update(self, dt):
        """
        Progresses the circle through warning, charge, and active damage states.
        """
        if self.state == "warning":
            self.flash_t += dt
            if self.flash_t >= self.flash_spd:
                self.flash_t = 0.0
                self.flash_on = not self.flash_on
            self.radius += self.warn_spd * dt
            if self.radius >= self.max_r:
                self.radius = self.max_r
                self.state = "purple_wait"
                self.timer = 0.0
        elif self.state == "purple_wait":
            self.timer += dt
            if self.timer >= 0.2:
                self.state = "purple_grow"
                self.timer = 0.0
        elif self.state == "purple_grow":
            self.timer += dt
            prog = min(self.timer / self.purple_time, 1.0)
            self.purple_r = int(self.max_r * prog)
            if self.purple_r >= self.max_r:
                self.state = "active"
                self.timer = 0.0
    
    def draw(self, where):
        """
        Renders the circle with different colors based on its current state.
        """
        if self.state == "warning":
            col = (200, 200, 200) if self.flash_on else (255, 255, 255)
            pg.draw.circle(where, col, (self.x, self.y), int(self.radius))
        elif self.state == "purple_wait":
            pg.draw.circle(where, (200, 200, 200), (self.x, self.y), self.max_r)
        elif self.state == "purple_grow":
            pg.draw.circle(where, (200, 200, 200), (self.x, self.y), self.max_r)
            pg.draw.circle(where, (128, 0, 128), (self.x, self.y), self.purple_r)
            pg.draw.circle(where, (255, 255, 255), (self.x, self.y), self.purple_r, 2)
        elif self.state == "active":
            pg.draw.circle(where, (128, 0, 128), (self.x, self.y), self.max_r)
            pg.draw.circle(where, (255, 255, 255), (self.x, self.y), self.max_r, 2)
    
    def is_ready(self):
        """
        Returns True when the circle is in its active damage state.
        """
        return self.state == "active"

class BoomAttack(BaseAttack):
    def __init__(self, area, radius=60, telegraph=0.8, active_t=1.0, num=2, diff=1):
        """
        Creates multiple expanding circles that damage players in their active state.
        """
        super().__init__(area)
        self.rad = radius
        self.telegraph_t = telegraph
        self.active_t = active_t
        self.num_circles = num * diff
        self.diff = diff
        self.circles = []
        self.timer = 0.0
        self.phase = "idle"
    
    def start(self):
        """
        Initializes multiple BoomCircles at random positions within the play area.
        """
        super().start()
        self.timer = 0.0
        self.phase = "telegraph"
        self.circles = [
            BoomCircle(
                r.randint(self.area.left + self.rad, self.area.right - self.rad),
                r.randint(self.area.top + self.rad, self.area.bottom - self.rad),
                max_r=self.rad
            )
            for _ in range(self.num_circles)
        ]
    
    def update(self, dt, plr):
        """
        Updates all circles and checks for player collisions during active states.
        """
        if not self.active:
            return
        if self.phase == "telegraph":
            all_ready = True
            for c in self.circles:
                c.update(dt)
                if c.state != "active":
                    all_ready = False
                else:
                    rect = pg.Rect(c.x - c.max_r, c.y - c.max_r,
                                   c.max_r * 2, c.max_r * 2)
                    if plr.hitbox.colliderect(rect):
                        plr.hit()
            if all_ready:
                self.phase = "active"
                self.timer = 0.0
        elif self.phase == "active":
            self.timer += dt
            for c in self.circles:
                if c.is_ready():
                    rect = pg.Rect(c.x - c.max_r, c.y - c.max_r,
                                   c.max_r * 2, c.max_r * 2)
                    if plr.hitbox.colliderect(rect):
                        plr.hit()
            if self.timer >= self.active_t:
                self.phase = "done"
                self.active = False
    
    def draw(self, where, plr):
        """
        Renders all BoomCircles in their current visual state.
        """
        if not self.active:
            return
        for c in self.circles:
            c.draw(where)

class LaserAttack(BaseAttack):
    def __init__(self, area, boss_ref, duration=5.0, diff=2):
        """
        EYELASER ATTACK - Created with the help of AI, this attack fires multiple
        laser beams that track the player's position. We had the laser beam tracking player position part down.
        We asked Ai to help smoothly indiacate the beam chargin and the laser beam shrinking over time.
        """
        super().__init__(area)
        self.boss_ref = boss_ref
        self.duration = duration
        self.diff = diff
        self.timer = 0.0
        self.lasers = []
        
        self.charge_max = 20
        self.charge_t = 0.5
        self.beam_spd = 1500
        self.beam_w = 28
        self.beam_shrink = 20.0
        self.beam_life = 1.5
    
    def start(self):
        """
        Activates the eyelaser attack sequence, resetting timers and laser list.
        """
        super().start()
        self.timer = 0.0
        self.lasers = []
    
    def make_laser(self, plr):
        """
        Creates a new laser that targets the player's current position from a random edge.
        """
        margin_x = 40
        margin_y = 30
        start_x = r.randint(self.area.left + margin_x, self.area.right - margin_x)
        start_y = r.randint(self.area.top + margin_y, self.area.bottom - margin_y)
        target_x, target_y = plr.hitbox.center
        
        self.lasers.append({
            "start": (start_x, start_y),
            "target": (target_x, target_y),
            "state": "charge",
            "timer": 0.0,
            "charge_r": 0,
            "length": 0.0,
            "width": self.beam_w
        })
    
    def update(self, dt, plr):
        """
        Updates all active lasers through charge, firing, and dissipation phases.
        """
        if not self.active:
            return
        
        self.timer += dt
        
        if len(self.lasers) < self.diff and self.timer <= self.duration:
            self.make_laser(plr)
        
        for laser in list(self.lasers):
            if laser["state"] == "charge":
                laser["timer"] += dt
                prog = min(laser["timer"] / self.charge_t, 1.0)
                laser["charge_r"] = int(self.charge_max * prog)
                if laser["timer"] >= self.charge_t:
                    dx = laser["target"][0] - laser["start"][0]
                    dy = laser["target"][1] - laser["start"][1]
                    laser["angle"] = math.atan2(dy, dx)
                    laser["state"] = "beam"
                    laser["timer"] = 0.0
                    laser["length"] = 0.0
            
            elif laser["state"] == "beam":
                laser["length"] += self.beam_spd * dt
                laser["width"] = max(0, laser["width"] - self.beam_shrink * dt)
                
                start = laser["start"]
                end = (
                    start[0] + math.cos(laser["angle"]) * laser["length"],
                    start[1] + math.sin(laser["angle"]) * laser["length"]
                )
                if self.hit_check(start, end, plr.hitbox, laser["width"]):
                    plr.hit()
                
                max_len = max(self.area.width, self.area.height)
                if laser["length"] >= max_len or laser["width"] <= 0:
                    laser["state"] = "done"
            
            if laser["state"] == "done":
                self.lasers.remove(laser)
        
        if self.timer >= self.duration and not self.lasers:
            self.active = False
    
    def draw(self, where, plr):
        """
        Renders laser charge circles and active beams with polygon-based visuals.
        """
        for laser in self.lasers:
            cx, cy = laser["start"]
            if laser["state"] == "charge":
                pg.draw.circle(where, (255, 255, 255), (int(cx), int(cy)), laser["charge_r"] + 2, 2)
                pg.draw.circle(where, (128, 0, 128), (int(cx), int(cy)), laser["charge_r"])
            elif laser["state"] == "beam":
                end_x = cx + math.cos(laser["angle"]) * laser["length"]
                end_y = cy + math.sin(laser["angle"]) * laser["length"]
                perp = laser["angle"] + math.pi / 2
                off_x = math.cos(perp) * laser["width"]
                off_y = math.sin(perp) * laser["width"]
                pts = [
                    (cx - off_x, cy - off_y),
                    (cx + off_x, cy + off_y),
                    (end_x + off_x, end_y + off_y),
                    (end_x - off_x, end_y - off_y)
                ]
                pg.draw.polygon(where, (128, 0, 128), pts)
                pg.draw.polygon(where, (255, 255, 255), pts, 2)
    
    def hit_check(self, start, end, rect, w):
        """
        Checks if a laser beam collides with the player's hitbox using expanded collision detection.
        """
        bigger = rect.inflate(w * 2, w * 2)
        return bigger.clipline(start, end)

class DarkAttack(BaseAttack):
    def __init__(self, area, duration=6.0, dark_r=200, orb_count=8, orb_r=20, diff=1):
        """
        DARKNESS ATTACK - Created with the help of AI, this attack creates a
        darkening effect with purple orbs that bounce around the screen. We had the base darkness effect but we weren't able to implement the orbs properly.
        We asked Ai to help us implement the orbs, and we implemented the difficulty progression system.
        """
        super().__init__(area)
        self.dur = duration
        self.dark_r = dark_r
        self.orb_num = orb_count * diff
        self.orb_r = orb_r
        self.timer = 0.0
        self.orbs = []
    
    def start(self):
        """
        Activates the darkness attack with randomly positioned bouncing orbs.
        """
        super().start()
        self.timer = 0.0
        self.orbs = [
            {"x": r.randint(self.area.left + self.orb_r, self.area.right - self.orb_r),
             "y": r.randint(self.area.top + self.orb_r, self.area.bottom - self.orb_r),
             "vx": r.uniform(-200, 200),
             "vy": r.uniform(-200, 200)}
            for _ in range(self.orb_num)
        ]
    
    def update(self, dt, plr):
        """
        Updates orb positions, checks for player collisions, and manages attack duration.
        """
        if not self.active:
            return
        self.timer += dt
        if self.timer >= self.dur:
            self.active = False
        for orb in self.orbs:
            orb["x"] += orb["vx"] * dt
            orb["y"] += orb["vy"] * dt
            if orb["x"] - self.orb_r < self.area.left or orb["x"] + self.orb_r > self.area.right:
                orb["vx"] *= -1
            if orb["y"] - self.orb_r < self.area.top or orb["y"] + self.orb_r > self.area.bottom:
                orb["vy"] *= -1
            if math.hypot(orb["x"] - plr.hitbox.centerx, orb["y"] - plr.hitbox.centery) <= self.orb_r + 25:
                plr.hit()
    
    def draw(self, where, plr):
        """
        Renders the darkness effect with gradient visibility and bouncing purple orbs.
        """
        if not self.active:
            return
        dark = pg.Surface((w, h), pg.SRCALPHA)
        dark.fill((0, 0, 0, 180))
        where.blit(dark, (0, 0))
        player_center = plr.hitbox.center
        light = pg.Surface((w, h), pg.SRCALPHA)
        layers = 8
        for i in range(layers):
            alpha = int(180 * (1 - i / layers))
            rad = int(self.dark_r * (i + 1) / layers)
            pg.draw.circle(light, (200, 200, 200, alpha), player_center, rad)
        where.blit(light, (0, 0))
        for orb in self.orbs:
            dx = orb["x"] - player_center[0]
            dy = orb["y"] - player_center[1]
            if math.hypot(dx, dy) <= self.dark_r:
                pg.draw.circle(where, (128, 0, 128), (int(orb["x"]), int(orb["y"])), self.orb_r)
                pg.draw.circle(where, (255, 255, 255), (int(orb["x"]), int(orb["y"])), self.orb_r, 2)

class AttackHandler:
    def __init__(self, boss_ref, play_area):
        """
        Manages the sequencing and execution of all boss attacks during phases.
        """
        self.boss_ref = boss_ref
        self.play_area = play_area
        self.base_atks = [
            BoomAttack(play_area),
            LaserAttack(play_area, boss_ref),
            DarkAttack(play_area)
        ]
        self.active_list = []
        self.current_idx = 0
        self.current_atk = None
        self.cycle_done = False
        self.green_ball = GreenBallAttack(play_area, boss_ref)
    
    def start_phase(self, phase_num):
        """
        Configures attack sequences for a specific boss phase with difficulty scaling.
        """
        atks_to_use = min(phase_num, len(self.base_atks))
        self.active_list = []
        dur_mult = 2.5 if phase_num == 4 else 1.0
        for i in range(atks_to_use):
            base = self.base_atks[i]
            diff_val = phase_num - i
            if isinstance(base, BoomAttack):
                atk = BoomAttack(self.play_area,
                                 diff=diff_val,
                                 active_t=base.active_t * dur_mult,
                                 telegraph=base.telegraph_t * dur_mult)
            elif isinstance(base, LaserAttack):
                atk = LaserAttack(self.play_area,
                                  self.boss_ref,
                                  diff=diff_val,
                                  duration=base.duration * dur_mult)
            elif isinstance(base, DarkAttack):
                atk = DarkAttack(self.play_area,
                                 diff=diff_val,
                                 duration=base.dur * dur_mult)
            self.active_list.append(atk)
        self.current_idx = 0
        if self.active_list:
            self.current_atk = self.active_list[self.current_idx]
            self.current_atk.start()
        self.green_ball.active = False
    
    def update_all(self, dt, plr):
        """
        Updates all active attacks and manages the attack cycle progression.
        """
        if self.current_atk:
            self.current_atk.update(dt, plr)
            if self.current_atk.done():
                self.current_idx += 1
                if self.current_idx >= len(self.active_list):
                    self.green_ball.start()
                    self.current_atk = None
                    self.cycle_done = True
                else:
                    self.current_atk = self.active_list[self.current_idx]
                    self.current_atk.start()
        if self.green_ball.active:
            self.green_ball.update(dt, plr)
        else:
            if self.cycle_done:
                self.cycle_done = False
                self.current_idx = 0
                if self.active_list:
                    self.current_atk = self.active_list[self.current_idx]
                    self.current_atk.start()
    
    def draw_all(self, where, plr):
        """
        Renders all currently active attacks to the specified surface.
        """
        if self.current_atk:
            self.current_atk.draw(where, plr)
        if self.green_ball.active:
            self.green_ball.draw(where, plr)

def game_loop():
    """
    Main game loop that manages game states, player input, and battle progression.
    """
    global game_state, transition_val, menu_y, going_to_start, going_to_ui, expansion_val
    
    player_start_x = w // 2 - 25
    player_start_y = h // 2 - 25
    player_img_file = os.path.join(script_folder, '9k.png')
    player = PlayerChar(player_img_file)
    
    border_w = w - 500
    border_h = 400
    border_x = (w - border_w) // 2
    border_y = h - border_h - 100
    game_area = pg.Rect(border_x, border_y, border_w, border_h)
    
    boss = Boss(
        os.path.join(script_folder, 'phase1.gif'),
        os.path.join(script_folder, 'phase2.gif'),
        os.path.join(script_folder, 'phase3.gif'),
        os.path.join(script_folder, 'phase4.gif'),
        os.path.join(script_folder, 'phase1.ogg'),
        os.path.join(script_folder, 'phase2.ogg'),
        os.path.join(script_folder, 'phase3.ogg'),
        os.path.join(script_folder, 'phase4.ogg')
    )
    
    atk_handler = AttackHandler(boss, game_area)
    player.x = float(game_area.centerx - player.hitbox.width // 2)
    
    screen.blit(background_img, (0, 0))
    
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_UP: player.up = True
                if e.key == pg.K_DOWN: player.down = True
                if e.key == pg.K_LEFT: player.left = True
                if e.key == pg.K_RIGHT: player.right = True
                if e.key == pg.K_m: boss.mute_toggle()
                if e.key == pg.K_b: boss.vol_up()
                if e.key == pg.K_n: boss.vol_down()
            if e.type == pg.KEYUP:
                if e.key == pg.K_UP: player.up = False
                if e.key == pg.K_DOWN: player.down = False
                if e.key == pg.K_LEFT: player.left = False
                if e.key == pg.K_RIGHT: player.right = False
        
        if game_state == 'START':
            show_menu()
            if pg.key.get_pressed()[pg.K_DOWN]:
                going_to_start = True
        
        player.move(dt, game_area)
        
        if going_to_start and not going_to_ui:
            transition_val += transition_spd
            if transition_val <= 0.2: menu_y += 6
            elif transition_val <= 0.3: menu_y += 2
            elif transition_val <= 0.5: menu_y -= 2
            elif transition_val <= 1: menu_y -= 10
            show_opening()
            if transition_val >= 1.0:
                going_to_ui = True
                going_to_start = False
                screen.fill((0, 0, 0))
                transition_val = 0
        
        elif going_to_ui:
            transition_val += transition_spd
            if transition_val <= 1: expansion_val += 1
            draw_ui_transition()
            if transition_val >= 1.0:
                going_to_ui = False
                screen.fill((0, 0, 0))
                transition_val = 0
                game_state = 'BATTLE'
                boss.next()
                atk_handler.start_phase(boss.current_phase)
        
        if game_state == 'BATTLE':
            if player.lives <= 0: game_state = 'LOSE'
            screen.fill((0, 0, 0))
            draw_ui_box()
            atk_handler.update_all(dt, player)
            atk_handler.draw_all(screen, player)
            screen.blit(player.sprite, player.rect)
            player.show_lives(screen)
            boss.draw_me(screen)
            draw_health_bar(screen, boss)
            phase_now = boss.current_phase
            if boss.hp_dict[phase_now] <= 0:
                if phase_now < 4:
                    boss.next()
                    atk_handler.start_phase(boss.current_phase)
                else:
                    game_state = 'WIN'
        
        if game_state == 'WIN':
            screen.fill((0, 0, 0))
            if not hasattr(boss, 'win_done'):
                end_gif = os.path.join(script_folder, 'end.gif')
                boss.custom_anim(end_gif, hold_last=False)
                boss.win_done = True
            boss.draw_me(screen)
            for ch in boss.music_chans.values():
                if ch.get_busy(): ch.stop()
            win_text = big_font.render("YOU WIN!", True, (255, 255, 0))
            win_rect = win_text.get_rect(center=(w // 2, h // 2 + 250))
            screen.blit(win_text, win_rect)
        elif game_state == 'LOSE':
            screen.fill((0, 0, 0))
            for ch in boss.music_chans.values():
                if ch.get_busy(): ch.stop()
            lose_text = big_font.render("YOU LOSE!", True, (255, 0, 0))
            lose_rect = lose_text.get_rect(center=(w // 2, h // 2))
            screen.blit(lose_text, lose_rect)
        
        pg.display.flip()
    
    pg.quit()

game_loop()