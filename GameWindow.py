import pygame
import random
import os

from paths import assets_dir, font_path, sound_path


class Game:
    def __init__(self, main_window=None, db=None, settings=None):
        self.main_window = main_window
        self.db = db
        self.settings = settings if isinstance(settings, dict) else {}  # ensure settings is a dictionary

        # Window size can be changed, but the "world" stays fixed for correct proportions
        self.window_size = tuple(self.settings.get("window_size", [700, 500]))
        self.W, self.H = self.window_size

        self.FPS = 60
        self.assetsdir = assets_dir()
        self.player_name = None

        # Fixed base resolution for keeping the proportions correct
        self.BASE_W = 700
        self.BASE_H = 500

        # Runtime fields (initialized in run)
        self.screen = None
        self.clock = None
        self.world = None
        self.s = None
        self.running = False
        self.played_gameover = False

        self.sounds = {}

        # Assets
        self.bg = None
        self.gameover_img = None
        self.doodle_left = None
        self.doodle_right = None
        self.plat_green = None
        self.plat_blue = None
        self.break_imgs = None
        self.coin_imgs = None
        self.heart_img = None
        self.blackhole_img = None
        self.spring_r_img = None
        self.spring_l_img = None
        self.tramp_img = None

        self.font = None
        self.font_big = None
        self.font_pause = None

        # Constants (initialized in _init_constants)
        self.PLAYER_W = 40
        self.PLAYER_H = 36
        self.PLAT_W = 78
        self.PLAT_H = 18
        self.SPRING_W = 78
        self.SPRING_H = 26
        self.COIN_W = 26
        self.COIN_H = 25
        self.HEART_W = 26
        self.HEART_H = 28
        self.BH_SIZE = 44
        self.BREAK_FRAME_TIME = 0.06

    def apply_settings(self, settings):  # apply settings while program runs
        if isinstance(settings, dict):
            self.settings = settings
        self.window_size = tuple(self.settings.get("window_size", [700, 500]))  # update window size from settings
        self.W, self.H = self.window_size
        self.apply_audio_settings()  # apply audio settings to music and sound effects

    def set_player(self, player_name):  # set current player name
        self.player_name = player_name

    def get_skin_sheet_path(self):  # determine skin sprite sheet path
        default_path = os.path.join(self.assetsdir, "doodle_sheet.png")  # default skin

        if not self.db or not self.player_name:
            return default_path

        try:
            p = self.db.get_player(self.player_name)
            skin_key = p[2] if p else "default"  # get skin key from database, default to "default" if player not found
            if skin_key == "default":
                return default_path

            candidate = os.path.join(self.assetsdir, f"{skin_key}_doodle_sheet.png")  # construct candidate path based on skin key
            if os.path.exists(candidate):
                return candidate
        except Exception:
            pass

        return default_path

    def apply_audio_settings(self):  # apply audio settings to music and sound effects
        try:
            if not pygame.mixer.get_init():  # initialize mixer if not already done
                return

            muted = bool(self.settings.get("muted", False))  # get muted state from settings
            music = float(self.settings.get("music_volume", 70)) / 100.0  # get music volume percentage from settings
            sfx = float(self.settings.get("sfx_volume", 70)) / 100.0  # get sfx volume percentage from settings

            if muted:
                pygame.mixer.music.set_volume(0.0)
                sfx = 0.0
            else:
                pygame.mixer.music.set_volume(max(0.0, min(1.0, music)))  # clamp music volume between 0.0 and 1.0

            # apply sfx volume to all loaded sound effects
            if hasattr(self, "sounds") and isinstance(self.sounds, dict):
                sfx = max(0.0, min(1.0, sfx))
                for sound in self.sounds.values():
                    if sound:
                        sound.set_volume(sfx)

        except Exception:
            pass

    def _init_pygame(self):
        pygame.init()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass

        sfx_volume = float(self.settings.get("sfx_volume", 70)) / 100.0

        def load_sound(filename, volume=0.7):
            try:
                p = sound_path(filename)
                if os.path.exists(p):
                    s = pygame.mixer.Sound(p)
                    s.set_volume(0.0 if bool(self.settings.get("muted", False)) else volume)
                    return s
            except Exception:
                return None
            return None

        self.sounds = {
            "jump": load_sound("jump.mp3", sfx_volume),
            "trampoline": load_sound("trampoline_platform.mp3", sfx_volume),
            "spring": load_sound("spring_platform.mp3", sfx_volume),
            "break": load_sound("breaking_platform.mp3", sfx_volume),
            "coin": load_sound("coin.mp3", sfx_volume),
            "blackhole": load_sound("blackhole.mp3", sfx_volume),
            "gameover": load_sound("gameover.mp3", sfx_volume),
        }
        self.apply_audio_settings()

    def play_sound(self, key):
        try:
            snd = self.sounds.get(key)
            if snd:
                snd.play()
        except Exception:
            pass

    def start_game_music(self):
        try:
            if not pygame.mixer.get_init():
                return
            p = sound_path("game_music.mp3")
            if not os.path.exists(p):
                return
            pygame.mixer.music.load(p)
            self.apply_audio_settings()  # apply current audio settings to music
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def stop_game_music(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def create_display(self):
        # Create resizable window and world surface
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
        pygame.display.set_caption("Doodle Jump Remake")
        self.clock = pygame.time.Clock()

        # Create fixed "world" surface
        self.world = pygame.Surface((self.BASE_W, self.BASE_H)).convert_alpha()

    def load_assets(self):
        # Load assets (scaled to base)
        def load_image(name, alpha=False):
            p = os.path.join(self.assetsdir, name)
            if not os.path.exists(p):
                raise FileNotFoundError(f"Missing asset file: {p}")
            img = pygame.image.load(p)
            return img.convert_alpha() if alpha else img.convert()

        self.bg = load_image("background.png", alpha=False)
        self.bg = pygame.transform.smoothscale(self.bg, (self.BASE_W, self.BASE_H))

        self.gameover_img = load_image("gameover.png", alpha=True)

        doodle_sheet = pygame.image.load(self.get_skin_sheet_path()).convert_alpha()

        platforms_sheet = load_image("platforms_sheet.png", alpha=True)
        breaking_sheet = load_image("breaking_platform_sheet.png", alpha=True)
        coin_sheet = load_image("coin_sheet.png", alpha=True)
        heart_img = load_image("heart_img.png", alpha=True)
        blackhole_img = load_image("blackhole.png", alpha=True)

        spring_r_img = load_image("right_spring_platform.png", alpha=True)
        spring_l_img = load_image("left_spring_platform.png", alpha=True)
        tramp_img = load_image("jump_platform.png", alpha=True)

        # Sprites
        self.doodle_left = pygame.transform.smoothscale(doodle_sheet.subsurface((0, 0, 348, 314)), (self.PLAYER_W, self.PLAYER_H))
        self.doodle_right = pygame.transform.smoothscale(doodle_sheet.subsurface((348, 0, 348, 314)), (self.PLAYER_W, self.PLAYER_H))

        self.plat_green = pygame.transform.smoothscale(platforms_sheet.subsurface((0, 0, 120, 30)), (self.PLAT_W, self.PLAT_H))
        self.plat_blue = pygame.transform.smoothscale(platforms_sheet.subsurface((120, 0, 120, 30)), (self.PLAT_W, self.PLAT_H))

        self.break_imgs = [pygame.transform.smoothscale(breaking_sheet.subsurface((i * 120, 0, 120, 30)), (self.PLAT_W, self.PLAT_H)) for i in range(4)]

        self.coin_imgs = [pygame.transform.smoothscale(coin_sheet.subsurface((i * 75, 0, 75, 71)), (self.COIN_W, self.COIN_H)) for i in range(10)]

        self.heart_img = pygame.transform.smoothscale(heart_img, (self.HEART_W, self.HEART_H))
        self.blackhole_img = pygame.transform.smoothscale(blackhole_img, (self.BH_SIZE, self.BH_SIZE))
        self.spring_r_img = pygame.transform.smoothscale(spring_r_img, (self.SPRING_W, self.SPRING_H))
        self.spring_l_img = pygame.transform.smoothscale(spring_l_img, (self.SPRING_W, self.SPRING_H))
        self.tramp_img = pygame.transform.smoothscale(tramp_img, (self.SPRING_W, self.SPRING_H))

        # Fonts
        self.font = pygame.font.Font(font_path("PatrickHand-Regular.ttf"), 26)
        self.font_big = pygame.font.Font(font_path("PatrickHand-Regular.ttf"), 40)
        self.font_pause = pygame.font.Font(font_path("PatrickHand-Regular.ttf"), 56)

    # Rect helpers
    def rect_player_world(self, x, y):
        return pygame.Rect(int(x), int(y), self.PLAYER_W, self.PLAYER_H)  # player rectangle in world coords

    def rect_plat_world(self, p):
        if p["type"] in ("spring_r", "spring_l", "tramp"):
            return pygame.Rect(int(p["x"]), int(p["y"]- 6), self.SPRING_W, self.SPRING_H - 6)  # smaller hitbox for springs
        return pygame.Rect(int(p["x"]), int(p["y"]), self.PLAT_W, self.PLAT_H)  # platform rectangle in world coords

    def rect_coin_world(self, c):
        return pygame.Rect(int(c["x"]), int(c["y"]), self.COIN_W, self.COIN_H)  # coin rectangle in world coords

    def rect_bh_world(self, b):
        return pygame.Rect(int(b["x"]), int(b["y"]), self.BH_SIZE, self.BH_SIZE)  # blackhole rectangle in world coords

    def spawn_platform(self, y, s, forced_type=None):
        if forced_type:
            ptype = forced_type
        else:
            h = -s["camera_y"]  # current height for dynamic difficulty adjustments

            # adjust platform type probabilities based on height to increase difficulty as player ascends
            if h < 1000:
                weights = [0.7, 0.15, 0.15, 0.0]
            elif h < 3000:
                weights = [0.6, 0.2, 0.15, 0.05]
            else:
                weights = [0.5, 0.25, 0.15, 0.10]

            # if player has hit multiple breaking platforms in a row or gone too long without a safe platform, increase chance of safe platforms to prevent "stuck" situations
            if s["break_streak"] >= 2 or s["since_safe"] >= 5:
                weights[1] = 0.0
                total = sum(weights)
                weights = [w / total for w in weights]

            base_type = random.choices(["normal", "break", "spring", "moving"], weights)[0]
            if base_type == "spring":
                ptype = random.choice(["spring_r", "spring_l", "tramp"])
            else:
                ptype = base_type

            if s.get("last_was_spring", False) and ptype in ("spring_r", "spring_l", "tramp"):
                ptype = "normal"

            s["last_was_spring"] = ptype in ("spring_r", "spring_l", "tramp")

        x = random.randint(0, self.BASE_W - self.PLAT_W)

        vx = random.choice([-120, 120]) if ptype == "moving" else 0

        if ptype == "break":
            s["break_streak"] += 1
            s["since_safe"] = 0
        else:
            s["break_streak"] = 0
            s["since_safe"] += 1

        return {
            "x": x,
            "y": y,
            "type": ptype,
            "vx": vx,
            "broken": False,
            "anim_frame": 0,
            "anim_timer": 0.0,
        }

    def reset_state(self):
        self.played_gameover = False  # reset gameover sound flag

        s = {}  # state dictionary
        s["x"] = float(self.BASE_W / 2 - self.PLAYER_W / 2)
        s["y"] = float(self.BASE_H - 140)
        s["vx"] = 0.0
        s["vy"] = 0.0
        s["facing_right"] = True
        s["gravity_base"] = 2050.0
        s["gravity_current"] = s["gravity_base"]
        s["move_speed_base"] = 450.0
        s["jump_speed"] = 920.0
        s["max_gap_jump"] = int((s["jump_speed"] ** 2) / (1.4 * s["gravity_base"]))
        s["max_gap_platform"] = max(55, min(s["max_gap_jump"], 110))
        s["camera_y"] = 0
        s["max_height"] = 0
        s["score"] = 0
        s["lives"] = 3
        s["coins_run"] = 0
        s["elapsed"] = 0
        s["invuln"] = 0
        s["respawn_lock"] = 0
        s["game_over"] = False
        s["saved"] = False
        s["paused"] = False
        s["coin_frame"] = 0
        s["coin_tick"] = 0
        s["platforms"] = []
        s["coins"] = []
        s["blackholes"] = []
        s["break_streak"] = 0
        s["since_safe"] = 0
        s["last_was_spring"] = False

        # Base platform
        s["platforms"].append(
            {
                "x": float(self.BASE_W / 2 - self.PLAT_W / 2),
                "y": float(self.BASE_H - 70),
                "type": "normal",
                "vx": 0.0,
                "broken": False,
                "anim_frame": 0,
                "anim_timer": 0.0,
            }
        )

        y = self.BASE_H - 120  # initial platform height
        for _ in range(18):
            gap = random.randint(50, min(78, s["max_gap_platform"]))  # gap between platforms
            s["platforms"].append(self.spawn_platform(y, s))  # spawn platform at given height
            y -= gap  # move up for next platform

        s["top_generated_y"] = min(p["y"] for p in s["platforms"])  # track highest generated platform

        # Initial coins and blackholes
        s["blackholes"].append({"x": float(random.randint(0, self.BASE_W - self.BH_SIZE)), "y": float(self.BASE_H - 320)})

        for _ in range(2):
            s["coins"].append(
                {
                    "x": float(random.randint(0, self.BASE_W - self.COIN_W)),
                    "y": float(self.BASE_H - random.randint(220, 420)),
                    "taken": False,
                }
            )

        return s

    def update_score(self):
        height = -self.s["camera_y"]
        if height > self.s["max_height"]:
            self.s["max_height"] = height
            self.s["score"] = int(self.s["max_height"])

    def choose_safe_platform(self):
        target = self.s["camera_y"] + self.BASE_H * 0.65  # target respawn height
        candidates = [p for p in self.s["platforms"] if not (p["type"] == "break" and p["broken"])]  # valid platforms
        return min(candidates, key=lambda pl: abs(pl["y"] - target))  # closest to target

    def lose_life_and_respawn(self):
        if self.s["respawn_lock"] > 0.0 or self.s["game_over"]:  # already respawning or game over
            return
        self.s["lives"] -= 1
        self.s["respawn_lock"] = 1.0
        self.s["invuln"] = 1.5

        if self.s["lives"] == 0:
            self.s["game_over"] = True
            self.s["paused"] = False
            return

        safe = self.choose_safe_platform()  # find safe platform
        self.s["x"] = float(safe["x"] + self.PLAT_W / 2 - self.PLAYER_W / 2)  # center on platform
        self.s["y"] = float(safe["y"] - self.PLAYER_H - 2)  # position above platform
        self.s["vx"] = 0.0  # reset horizontal velocity
        self.s["vy"] = 0.0  # reset vertical velocity

    def spawn_more(self):
        while self.s["top_generated_y"] > self.s["camera_y"] - 950: # spawn platforms until a certain distance above the camera to ensure smooth gameplay without sudden platform appearances
            g_cur = float(self.s.get("gravity_current", self.s["gravity_base"])) # current gravity for dynamic difficulty adjustments
            max_gap_now = int((self.s["jump_speed"] ** 2) / (2.0 * g_cur) * 0.85)  # calculate max gap based on current gravity for dynamic difficulty
            gap_cap = max(55, min(self.s["max_gap_platform"], max_gap_now))  # cap gap to ensure it's always possible to jump
            gap = random.randint(50, gap_cap)
            new_y = self.s["top_generated_y"] - gap

            forced = None
            if self.s["since_safe"] >= 5: # if it's been too long since a safe platform, force the next one to be safe to prevent "stuck" situations
                forced = random.choice(["normal", "moving"])
                self.s["since_safe"] = 0

            p = self.spawn_platform(new_y, self.s, forced_type=forced)  # spawn new platform with possible forced type for safety
            self.s["platforms"].append(p)
            self.s["top_generated_y"] = new_y
            if p["type"] == "break":
                buddy_gap = random.randint(45, 65)  # gap for buddy platform to provide an alternative to breaking platform
                buddy_y = self.s["top_generated_y"] - buddy_gap

                buddy = self.spawn_platform(buddy_y, self.s, forced_type="normal")  # spawn safe buddy platform near breaking platform to reduce "stuck" situations
                self.s["platforms"].append(buddy)
                self.s["top_generated_y"] = buddy_y

            if random.random() < 0.33:
                self.s["coins"].append(
                    {
                        "x": float(random.randint(0, self.BASE_W - self.COIN_W)),
                        "y": float(new_y - random.randint(90, 170)),
                        "taken": False,
                    }
                )

            if random.random() < 0.06:
                self.s["blackholes"].append(
                    {
                        "x": float(random.randint(0, self.BASE_W - self.BH_SIZE)),
                        "y": float(new_y - random.randint(140, 240)),
                    }
                )

    def save_run_if_needed(self): # save the run to the database if not already saved, ensuring it's only saved once and only if there's a valid score and player/database exists
        if not self.db or not self.player_name: # if no database or player name, skip saving
            return
        if self.s["saved"]:
            return

        self.s["saved"] = True

        if self.s["score"] == 0:
            return

        self.db.add_score(self.player_name, self.s["score"])
        if self.s["coins_run"] > 0:
            self.db.add_coins(self.player_name, self.s["coins_run"])

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                self.W, self.H = self.screen.get_size()
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif e.key == pygame.K_p:
                    if not self.s["game_over"]:
                        self.s["paused"] = not self.s["paused"]
                elif e.key == pygame.K_SPACE:
                    if self.s["game_over"]:
                        self.s = self.reset_state()

    def update(self, dt):
        if self.s["game_over"] and not self.played_gameover: # play gameover sound once when game over state is first reached
            self.play_sound("gameover")
            self.played_gameover = True

        # Update
        if self.s["paused"] and not self.s["game_over"]:  # game is paused
            self.s["coin_tick"] += 1
            if self.s["coin_tick"] % 4 == 0:
                self.s["coin_frame"] = (self.s["coin_frame"] + 1) % len(self.coin_imgs)
            return

        keys = pygame.key.get_pressed()

        if self.s["respawn_lock"] > 0.0:  # handle respawn lock timer
            self.s["respawn_lock"] = max(0.0, self.s["respawn_lock"] - dt)
        if self.s["invuln"] > 0.0: # handle invulnerability timer after respawning
            self.s["invuln"] = max(0.0, self.s["invuln"] - dt)

        self.s["coin_tick"] += 1
        if self.s["coin_tick"] % 4 == 0: # animate coins every 4 ticks for a smooth animation speed without it being too fast, giving a nice visual effect while keeping the gameplay clear and not distracting
            self.s["coin_frame"] = (self.s["coin_frame"] + 1) % len(self.coin_imgs)

        if not self.s["game_over"]:
            self.s["elapsed"] += dt # track elapsed time for dynamic difficulty adjustments, allowing the game to gradually become more challenging as the player survives longer
            speed_mult = 1.0 + min(0.9, self.s["elapsed"] / 60.0) # gradually increase speed multiplier over time

            gravity = self.s["gravity_base"] * (1.0 + 0.25 * (speed_mult - 1.0)) # increase gravity based on speed multiplier for dynamic difficulty, making the game more challenging as time goes on
            self.s["gravity_current"] = gravity
            move_speed = self.s["move_speed_base"] * speed_mult
            moving_mult = speed_mult

            self.s["vx"] = 0.0
            if keys[pygame.K_LEFT]:
                self.s["vx"] = -move_speed
                self.s["facing_right"] = False
            if keys[pygame.K_RIGHT]:
                self.s["vx"] = move_speed
                self.s["facing_right"] = True

            self.s["x"] += self.s["vx"] * dt
            if self.s["x"] > self.BASE_W:
                self.s["x"] = -self.PLAYER_W
            elif self.s["x"] < -self.PLAYER_W:
                self.s["x"] = self.BASE_W

            for p in self.s["platforms"]:
                if p["type"] == "moving": # only update position of moving platforms to reduce unnecessary calculations for static platforms
                    p["x"] += (p["vx"] * moving_mult) * dt
                    if p["x"] <= 0:
                        p["x"] = 0
                        p["vx"] *= -1
                    if p["x"] >= self.BASE_W - self.PLAT_W:
                        p["x"] = self.BASE_W - self.PLAT_W
                        p["vx"] *= -1

                if p["type"] == "break" and p["broken"]:
                    p["anim_timer"] += dt
                    while p["anim_timer"] >= self.BREAK_FRAME_TIME and p["anim_frame"] < 4:
                        p["anim_timer"] -= self.BREAK_FRAME_TIME
                        p["anim_frame"] += 1
                    if p["anim_frame"] >= 4:
                        p["y"] = self.s["camera_y"] + self.BASE_H + 9999

            prev_y = self.s["y"]
            self.s["vy"] += gravity * dt
            self.s["y"] += self.s["vy"] * dt

            threshold = self.BASE_H * 0.35
            if (self.s["y"] - self.s["camera_y"]) < threshold:
                self.s["camera_y"] = self.s["y"] - threshold

            self.update_score()

            if self.s["vy"] > 0:
                pos = self.rect_player_world(self.s["x"], self.s["y"])
                prev_bottom = prev_y + self.PLAYER_H # calculate previous bottom position of player for more accurate collision detection, especially when falling fast, to prevent "sinking" into platforms or missing collisions

                for p in self.s["platforms"]:
                    if p["type"] == "break" and p["broken"]: # skip broken platforms for collision since they should no longer be solid, preventing unfair deaths or "sinking" into them after they've visually broken
                        continue

                    r = self.rect_plat_world(p)
                    if pos.colliderect(r) and prev_bottom <= r.top + 10: # check if player is landing on platform (with a small tolerance for better gameplay feel)
                        self.s["y"] = float(r.top - self.PLAYER_H) # snap player to platform surface for consistent jumping behavior, preventing "sinking" into platforms or inconsistent jumps

                        if p["type"] == "break":
                            p["broken"] = True
                            p["anim_frame"] = 0
                            p["anim_timer"] = 0.0
                            self.s["vy"] = max(self.s["vy"], 320.0)
                            self.play_sound("break")
                        else:
                            if p["type"] in ("spring_r", "spring_l"):
                                self.s["vy"] = -self.s["jump_speed"] * 1.45
                                self.play_sound("spring")
                            elif p["type"] == "tramp":
                                self.s["vy"] = -self.s["jump_speed"] * 1.80
                                self.play_sound("trampoline")
                            else:
                                self.s["vy"] = -self.s["jump_speed"]
                                self.play_sound("jump")
                        break

            if self.s["invuln"] == 0.0: # only check for blackhole collisions if not currently invulnerable to prevent unfair deaths immediately after respawning
                pos = self.rect_player_world(self.s["x"], self.s["y"])
                for b in self.s["blackholes"]:
                    bh = self.rect_bh_world(b)
                    if bh.collidepoint(pos.centerx, pos.centery):
                        self.play_sound("blackhole")
                        self.lose_life_and_respawn()
                        break

            pos = self.rect_player_world(self.s["x"], self.s["y"])
            for c in self.s["coins"]:
                if c["taken"]:
                    continue
                if pos.colliderect(self.rect_coin_world(c)):
                    c["taken"] = True
                    self.s["coins_run"] += 1
                    self.play_sound("coin")

            self.spawn_more()

            self.s["platforms"] = [p for p in self.s["platforms"] if p["y"] < self.s["camera_y"] + self.BASE_H] # remove platforms that are below the camera 
            self.s["blackholes"] = [b for b in self.s["blackholes"] if b["y"] < self.s["camera_y"] + self.BASE_H] # remove blackholes that are below the camera
            self.s["coins"] = [c for c in self.s["coins"] if (not c["taken"]) and c["y"] < self.s["camera_y"] + self.BASE_H] # remove coins that are taken or below the camera

            if (self.s["y"] - self.s["camera_y"]) > self.BASE_H + 5:
                self.lose_life_and_respawn()
        else:
            self.save_run_if_needed()

    def draw(self):
        # Draw everything into world
        self.world.blit(self.bg, (0, 0))

        for p in self.s["platforms"]:
            dy = int(p["y"] - self.s["camera_y"]) # calculate platform's y position relative to camera for culling and correct drawing position
            if -80 <= dy <= self.BASE_H + 80:
                x = int(p["x"])
                t = p["type"]
                if t == "normal":
                    self.world.blit(self.plat_green, (x, dy))
                elif t == "moving":
                    self.world.blit(self.plat_blue, (x, dy))
                elif t == "break":
                    f = min(p["anim_frame"], 3)
                    self.world.blit(self.break_imgs[f], (x, dy))
                elif t == "spring_r":
                    self.world.blit(self.spring_r_img, (x, dy - 6))
                elif t == "spring_l":
                    self.world.blit(self.spring_l_img, (x, dy - 6))
                elif t == "tramp":
                    self.world.blit(self.tramp_img, (x, dy - 6))

        for b in self.s["blackholes"]:
            dy = int(b["y"] - self.s["camera_y"])
            if -120 <= dy <= self.BASE_H + 120:
                self.world.blit(self.blackhole_img, (int(b["x"]), dy))

        coin_img = self.coin_imgs[self.s["coin_frame"]]
        for c in self.s["coins"]:
            dy = int(c["y"] - self.s["camera_y"])
            if -120 <= dy <= self.BASE_H + 120:
                self.world.blit(coin_img, (int(c["x"]), dy))

        px = int(self.s["x"])
        py = int(self.s["y"] - self.s["camera_y"])
        self.world.blit(self.doodle_right if self.s["facing_right"] else self.doodle_left, (px, py))

        for i in range(self.s["lives"]):
            self.world.blit(self.heart_img, (8 + i * (22 + 6), 8))

        self.world.blit(self.font.render(f"Score: {self.s['score']}", True, (0, 0, 0)), (10, 36))
        self.world.blit(self.font.render(f"Coins: {self.s['coins_run']}", True, (0, 0, 0)), (10, 56))

        if self.s["paused"] and not self.s["game_over"]:
            overlay = pygame.Surface((self.BASE_W, self.BASE_H), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 160))
            self.world.blit(overlay, (0, 0))

            t1 = self.font_pause.render("PAUSED", True, (0, 0, 0)) # put "PAUSED" text in a larger font for better visibility and emphasis when the game is paused
            t2 = self.font.render("Press P to resume, ESC to return to menu", True, (0, 0, 0)) # add instructions for resuming and exiting to menu when paused
            self.world.blit(t1, (self.BASE_W // 2 - t1.get_width() // 2, self.BASE_H // 2 - 80))
            self.world.blit(t2, (self.BASE_W // 2 - t2.get_width() // 2, self.BASE_H // 2 + 10))

        if self.s["game_over"]:
            gx = self.BASE_W // 2 - self.gameover_img.get_width() // 2 # center game over image horizontally for better visual
            gy = self.BASE_H // 2 - self.gameover_img.get_height() // 2 # center game over image vertically for better visual
            self.world.blit(self.gameover_img, (gx, gy))
            self.world.blit(self.font_big.render("SPACE = Restart, ESC = Menu", True, (0, 0, 0)), (self.BASE_W // 2 - 220, gy + self.gameover_img.get_height() + 10),)

    def present(self):
        # Present stretched world to screen
        win_w, win_h = self.screen.get_size()
        scaled_world = pygame.transform.smoothscale(self.world, (win_w, win_h))
        self.screen.blit(scaled_world, (0, 0))
        pygame.display.flip()

    def run(self):  # main game loop
        self._init_pygame() # initialize pygame modules
        try:
            self._init_audio() # initialize audio and load sound effects with current settings applied
            self.start_game_music() # start background music with current audio settings applied

            self.create_display() # create game window and world surface
            self.load_assets() # load images and fonts, scaling them to the base resolution for consistent appearance regardless of window size

            self.s = self.reset_state() # initialize game state variables to their starting values for a new run
            self.running = True

            while self.running:
                dt = self.clock.tick(self.FPS) / 1000.0  # delta time in seconds

                self.handle_events()
                if not self.running:
                    break

                self.update(dt) # update game state based on player input, physics, collisions, and dynamic difficulty adjustments
                self.draw() # render the current game state to the world surface
                self.present() # scale and present the world surface to the actual game window

        finally:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass
            pygame.quit()