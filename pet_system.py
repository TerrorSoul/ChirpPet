import os
import sys
import math
from PIL import Image, ImageSequence
from PyQt6.QtGui import QImage, QPixmap, QColor, QTransform, QPainter
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QSoundEffect

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class SpriteLoader:
    def __init__(self, path, cols, rows):
        self.path = resource_path(path)
        self.cols = cols
        self.rows = rows
        self.sprites = []
        self.sprite_width = 0
        self.sprite_height = 0
        self.load_sprites()

    def load_sprites(self):
        if not os.path.exists(self.path):
            print(f"Error: Sprite sheet not found at {self.path}")
            return

        img = Image.open(self.path).convert("RGBA")
        sheet_width, sheet_height = img.size
        
        self.sprite_width = sheet_width / self.cols
        self.sprite_height = sheet_height / self.rows

        print(f"Sheet: {sheet_width}x{sheet_height}, Sprite: {self.sprite_width}x{self.sprite_height}")

        fixed_target_width = int(self.sprite_width * 0.5)
        fixed_target_height = int(self.sprite_height * 0.5)
        
        if fixed_target_width % 2 != 0:
            fixed_target_width -= 1
        if fixed_target_height % 2 != 0:
            fixed_target_height -= 1

        for row in range(self.rows):
            for col in range(self.cols):
                left = int(col * self.sprite_width)
                top = int(row * self.sprite_height)
                right = int((col + 1) * self.sprite_width)
                bottom = int((row + 1) * self.sprite_height)
                
                sprite_img = img.crop((left, top, right, bottom))
                
                data = sprite_img.tobytes("raw", "RGBA")
                qim = QImage(data, sprite_img.width, sprite_img.height, QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qim)
                
                pixmap = pixmap.scaled(fixed_target_width, fixed_target_height, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                self.sprites.append(pixmap)

class PetState:
    IDLE = 0
    LOOK_SEQUENCE = 1
    SPEAK = 2
    MOVE_RIGHT = 3
    MOVE_LEFT = 4
    SLEEP = 5
    FLAP = 6
    PUFF = 7
    FLAP_HARD = 8
    INQUISITIVE = 9
    IDLE_WINK = 10
    CORNER_POP = 11
    SPIN = 12
    JUMP = 13
    SHAKE = 14
    MOONWALK_RIGHT = 15
    MOONWALK_LEFT = 16
    ZOOMIES = 17
    GHOST = 18
    CHASE = 19
    DISCO = 20
    PULSE = 21
    CEILING_WALK_LEFT = 22
    CEILING_WALK_RIGHT = 23
    SPAWN = 24
    DRAG = 25
    PRE_CHASE = 26

class PetMood:
    HAPPY = 0
    SLEEPY = 1
    HYPER = 2
    GRUMPY = 3

class PetSystem:
    def __init__(self, sprite_path='assets/defaultspritesheet.png', style_name='Default'):
        self.load_style(sprite_path, style_name)
        
        self.current_state = PetState.SPAWN
        self.current_frame_index = 0
        self.frame_timer = 0
        self.bob_timer = 0 
        self.x = 100
        self.y = 100
        self.direction = 1 
        self.rotation = 0 
        self.offset_x = 0
        self.offset_y = 0
        
        self.name = "ChirPet"
        self.speech_text = ""
        self.speech_timer = 0
        self.next_speech_time = 5000 
        
        self.sounds = ["chirp", "peep", "tik", "mew", "kwee", "pip", "bip", "bop", "mrrp", "yip"]
        
        self.mood = PetMood.HAPPY
        self.mood_timer = 0
        self.mood_duration = 30000 
        
        self.hunger = 0 
        self.energy = 100 
        self.hunger_timer = 0
        self.energy_timer = 0

    def load_style(self, sprite_path, style_name='Default'):
        self.loader = SpriteLoader(sprite_path, 10, 10)
        self.chirp_sounds = []
        self.has_chirped = False
        
        self.animations = {
            PetState.IDLE: {'frames': [10], 'loop': True, 'interval': 1000}, 
            PetState.IDLE_WINK: {'frames': range(0, 10), 'loop': False, 'next': PetState.IDLE, 'interval': 150},
            PetState.LOOK_SEQUENCE: {'frames': range(10, 20), 'loop': False, 'next': PetState.IDLE, 'interval': 200},
            PetState.SPEAK: {'frames': range(20, 30), 'loop': False, 'next': PetState.IDLE, 'interval': 150},
            PetState.MOVE_RIGHT: {'frames': range(30, 40), 'loop': True, 'interval': 100},
            PetState.MOVE_LEFT: {'frames': range(40, 50), 'loop': True, 'interval': 100},
            PetState.SLEEP: {'frames': range(50, 60), 'loop': True, 'interval': 300},
            PetState.FLAP: {'frames': range(60, 70), 'loop': False, 'next': PetState.IDLE, 'interval': 100},
            PetState.PUFF: {'frames': list(range(70, 80)) + list(range(78, 69, -1)) + [10], 'loop': False, 'next': PetState.IDLE, 'interval': 150},
            PetState.FLAP_HARD: {'frames': range(80, 90), 'loop': False, 'next': PetState.IDLE, 'interval': 100},
            PetState.INQUISITIVE: {'frames': range(90, 99), 'loop': False, 'next': PetState.IDLE, 'interval': 200},
            PetState.SPIN: {'frames': [10], 'loop': False, 'next': PetState.IDLE, 'interval': 50}, 
            PetState.JUMP: {'frames': [10], 'loop': False, 'next': PetState.IDLE, 'interval': 50},
            PetState.SHAKE: {'frames': [10], 'loop': False, 'next': PetState.IDLE, 'interval': 50},
            PetState.MOONWALK_RIGHT: {'frames': range(40, 50), 'loop': True, 'interval': 100}, 
            PetState.MOONWALK_LEFT: {'frames': range(30, 40), 'loop': True, 'interval': 100}, 
            PetState.ZOOMIES: {'frames': range(30, 40), 'loop': True, 'interval': 50}, 
            PetState.GHOST: {'frames': [10], 'loop': True, 'interval': 1000}, 
            PetState.CHASE: {'frames': range(30, 40), 'loop': True, 'interval': 80}, 
            PetState.DISCO: {'frames': [10], 'loop': True, 'interval': 100}, 
            PetState.SPAWN: {'frames': [10], 'loop': True, 'interval': 100}, 
            PetState.DRAG: {'frames': range(60, 70), 'loop': True, 'interval': 100}, 
            PetState.PRE_CHASE: {'frames': range(90, 99), 'loop': False, 'next': PetState.CHASE, 'interval': 200},
        }
        
        if style_name == 'Melvin':
            self.animations[PetState.FLAP_HARD] = {'frames': [10], 'loop': False, 'next': PetState.IDLE, 'interval': 100}
            self.animations[PetState.INQUISITIVE] = {'frames': [10], 'loop': False, 'next': PetState.IDLE, 'interval': 200}
            self.animations[PetState.PRE_CHASE] = {'frames': [10], 'loop': False, 'next': PetState.CHASE, 'interval': 200}
        
        self.idle_counter = 0

    def update(self, dt_ms, mouse_pos=None, window_pos=None):
        anim = self.animations[self.current_state]
        self.frame_timer += dt_ms
        self.bob_timer += dt_ms
        
        self.offset_x = 0
        self.offset_y = 0
        self.rotation = 0
        
        if self.current_state == PetState.SPAWN:
            if self.bob_timer > 1000:
                self.set_state(PetState.IDLE)

        elif self.current_state == PetState.SPIN:
            progress = self.frame_timer / 1000.0
            if progress >= 1.0:
                self.set_state(PetState.IDLE)
            else:
                self.rotation = progress * 360
                return 

        elif self.current_state == PetState.JUMP:
            progress = self.frame_timer / 500.0
            if progress >= 1.0:
                self.set_state(PetState.IDLE)
            else:
                jump_height = 50
                self.offset_y = -int(math.sin(progress * math.pi) * jump_height)
                return

        elif self.current_state == PetState.SHAKE:
            progress = self.frame_timer / 500.0
            if progress >= 1.0:
                self.set_state(PetState.IDLE)
            else:
                shake_amount = 5
                self.offset_x = int(math.sin(progress * 10 * math.pi) * shake_amount)
                return
        
        elif self.current_state == PetState.ZOOMIES:
            if self.frame_timer % 500 < dt_ms:
                import random
                if random.random() < 0.3:
                    self.direction *= -1
                    if self.direction == 1:
                        self.animations[PetState.ZOOMIES]['frames'] = range(30, 40)
                    else:
                        self.animations[PetState.ZOOMIES]['frames'] = range(40, 50)
            
            if self.bob_timer > 3000: 
                 self.set_state(PetState.IDLE)

        elif self.current_state == PetState.SLEEP:
            if self.bob_timer > 20000:
                self.set_state(PetState.IDLE)

            if self.current_frame_index >= 2 and not self.has_chirped:
                self.has_chirped = True
        
        if self.speech_timer > 0:
            self.speech_timer -= dt_ms
            if self.speech_timer <= 0:
                self.speech_text = ""

        self.next_speech_time -= dt_ms
        if self.next_speech_time <= 0:
            self.say_random_thing()
            import random
            self.next_speech_time = random.randint(30000, 90000)

        # Mood updates
        self.mood_timer += dt_ms
        if self.mood_timer > self.mood_duration:
            self.change_mood_randomly()

        self.hunger_timer += dt_ms
        if self.hunger_timer > 5000:
            self.hunger = min(100, self.hunger + 1)
            self.hunger_timer = 0
            
        self.energy_timer += dt_ms
        if self.energy_timer > 5000:
            if self.current_state == PetState.SLEEP:
                self.energy = min(100, self.energy + 5)
            elif self.current_state in [PetState.ZOOMIES, PetState.CHASE, PetState.MOVE_RIGHT, PetState.MOVE_LEFT]:
                self.energy = max(0, self.energy - 2)
            else:
                self.energy = max(0, self.energy - 0.5)
            self.energy_timer = 0

        # Needs affecting Mood
        if self.hunger > 80:
            if self.mood != PetMood.GRUMPY and self.mood != PetMood.SLEEPY:
                self.mood = PetMood.GRUMPY
                self.speech_text = "Grrr..."
                self.speech_timer = 2000
        elif self.energy < 20:
             if self.mood != PetMood.SLEEPY:
                 self.mood = PetMood.SLEEPY
                 self.speech_text = "Zzz..."
                 self.speech_timer = 2000

        if self.frame_timer >= anim['interval']:
            self.frame_timer = 0
            self.current_frame_index += 1
            
            frames = anim['frames']
            if self.current_frame_index >= len(frames):
                if anim['loop']:
                    self.current_frame_index = 0
                    
                    if self.current_state == PetState.IDLE and mouse_pos and window_pos:
                        dx = mouse_pos.x() - window_pos.x()
                        dy = mouse_pos.y() - window_pos.y()
                        dist = (dx*dx + dy*dy)**0.5
                        
                        if dist < 400: 
                            if dx > 0:
                                self.direction = 1
                            else:
                                self.direction = -1
                                
                            if dist < 200:
                                import random
                                if random.random() < 0.5: 
                                    if random.random() < 0.5:
                                        self.set_state(PetState.JUMP)
                                    else:
                                        self.set_state(PetState.SHAKE)
                                    return

                    if self.current_state == PetState.IDLE:
                        import random
                        if random.random() < 0.3: 
                            r = random.random()
                            
                    if self.current_state == PetState.IDLE:
                        import random
                        if random.random() < 0.3: 
                            r = random.random()
                            
                            if mouse_pos and window_pos:
                                dx = mouse_pos.x() - window_pos.x()
                                dy = mouse_pos.y() - window_pos.y()
                                dist = (dx*dx + dy*dy)**0.5
                                
                                if dist < 300:
                                    if self.mood == PetMood.GRUMPY:
                                        if random.random() < 0.7:
                                            if dx > 0: self.set_state(PetState.MOVE_LEFT)
                                            else: self.set_state(PetState.MOVE_RIGHT)
                                            return
                                    elif self.mood in [PetMood.HAPPY, PetMood.HYPER]:
                                        if random.random() < 0.7:
                                            self.set_state(PetState.PRE_CHASE)
                                            return

                            # Probabilities based on mood
                            prob_move = 0.40
                            prob_look = 0.50
                            prob_speak = 0.60
                            prob_inquisitive = 0.70
                            prob_sleep = 0.75
                            prob_spin = 0.80
                            prob_jump = 0.85
                            prob_shake = 0.92
                            prob_moonwalk = 0.94
                            
                            if self.mood == PetMood.SLEEPY:
                                prob_sleep = 0.40
                                prob_move = 0.50
                                prob_look = 0.60
                                prob_speak = 0.65
                                prob_inquisitive = 0.70
                                prob_spin = 0.75
                                prob_jump = 0.80
                                prob_shake = 0.90
                                prob_moonwalk = 0.95
                            elif self.mood == PetMood.HYPER:
                                prob_move = 0.20
                                prob_spin = 0.30
                                prob_jump = 0.45
                                prob_zoomies = 0.60
                                prob_moonwalk = 0.70
                                prob_shake = 0.80
                                prob_look = 0.85
                                prob_speak = 0.90
                                prob_inquisitive = 0.95
                                prob_sleep = 1.0 # No sleep
                            elif self.mood == PetMood.GRUMPY:
                                prob_shake = 0.30
                                prob_look = 0.50
                                prob_move = 0.60
                                prob_speak = 0.70
                                prob_inquisitive = 0.80
                                prob_sleep = 0.90
                                prob_spin = 0.95
                                prob_jump = 0.98
                                prob_moonwalk = 1.0
                            
                            if self.mood == PetMood.HYPER:
                                if r < prob_move:
                                    if random.random() < 0.5: self.set_state(PetState.MOVE_RIGHT)
                                    else: self.set_state(PetState.MOVE_LEFT)
                                elif r < prob_spin: self.set_state(PetState.SPIN)
                                elif r < prob_jump: self.set_state(PetState.JUMP)
                                elif r < prob_zoomies: self.set_state(PetState.ZOOMIES)
                                elif r < prob_moonwalk:
                                    if random.random() < 0.5: self.set_state(PetState.MOONWALK_RIGHT)
                                    else: self.set_state(PetState.MOONWALK_LEFT)
                                elif r < prob_shake: self.set_state(PetState.SHAKE)
                                elif r < prob_look: self.set_state(PetState.LOOK_SEQUENCE)
                                elif r < prob_speak: self.set_state(PetState.SPEAK)
                                elif r < prob_inquisitive: self.set_state(PetState.INQUISITIVE)
                                else: self.set_state(PetState.IDLE)
                            else:
                                if r < prob_move: 
                                    if random.random() < 0.5:
                                        self.set_state(PetState.MOVE_RIGHT)
                                    else:
                                        self.set_state(PetState.MOVE_LEFT)
                                elif r < prob_look:
                                    self.set_state(PetState.LOOK_SEQUENCE)
                                elif r < prob_speak:
                                    self.set_state(PetState.SPEAK)
                                elif r < prob_inquisitive:
                                    self.set_state(PetState.INQUISITIVE)
                                elif r < prob_sleep:
                                    self.set_state(PetState.SLEEP)
                                elif r < prob_spin:
                                    self.set_state(PetState.SPIN)
                                elif r < prob_jump:
                                    self.set_state(PetState.JUMP)
                                elif r < prob_shake:
                                    self.set_state(PetState.SHAKE)
                                elif r < prob_moonwalk: 
                                    if random.random() < 0.5:
                                        self.set_state(PetState.MOONWALK_RIGHT)
                                    else:
                                        self.set_state(PetState.MOONWALK_LEFT)
                                else: 
                                    self.set_state(PetState.ZOOMIES)
                            
                    elif self.current_state in [PetState.MOVE_RIGHT, PetState.MOVE_LEFT, PetState.MOONWALK_RIGHT, PetState.MOONWALK_LEFT]:
                         import random
                         if random.random() < 0.20: 
                             self.set_state(PetState.IDLE)

                else:
                    if 'next' in anim:
                        self.set_state(anim['next'])
                    else:
                        self.current_frame_index = len(frames) - 1

    def set_state(self, new_state):
        if self.current_state != new_state:
            self.current_state = new_state
            self.current_frame_index = 0
            self.frame_timer = 0
            self.has_chirped = False
            
            self.offset_x = 0
            self.offset_y = 0
            self.rotation = 0 
            
            if new_state == PetState.MOVE_LEFT:
                self.direction = -1
            elif new_state == PetState.MOVE_RIGHT:
                self.direction = 1

    def say_name(self):
        self.speech_text = f"I am {self.name}!"
        self.speech_timer = 3000
        self.set_state(PetState.SPEAK)

    def change_mood_randomly(self):
        import random
        weights = [0.4, 0.2, 0.2, 0.2] # Happy, Sleepy, Hyper, Grumpy
        self.mood = random.choices([PetMood.HAPPY, PetMood.SLEEPY, PetMood.HYPER, PetMood.GRUMPY], weights=weights)[0]
        self.mood_timer = 0
        self.mood_duration = random.randint(20000, 60000)
        
        if self.mood == PetMood.SLEEPY:
            self.set_state(PetState.SLEEP)
        elif self.mood == PetMood.HYPER:
            self.set_state(PetState.ZOOMIES)
        elif self.mood == PetMood.GRUMPY:
            self.set_state(PetState.SHAKE)
            
    def handle_interaction(self, interaction_type):
        if interaction_type == 'click':
            if self.current_state == PetState.SLEEP:
                self.mood = PetMood.GRUMPY
                self.set_state(PetState.SHAKE)
                self.speech_text = "Mrrp!"
                self.speech_timer = 1000
            else:
                if self.mood == PetMood.GRUMPY:
                    if self.hunger > 80:
                         self.speech_text = "Chirp chirp!" # Chirpo is hungry!
                         self.speech_timer = 1000
                         self.set_state(PetState.SHAKE)
                    else:
                        self.mood = PetMood.HAPPY
                        self.set_state(PetState.JUMP)
                elif self.mood == PetMood.HAPPY:
                    import random
                    if random.random() < 0.3:
                        self.mood = PetMood.HYPER
                        self.set_state(PetState.SPIN)
                    else:
                        self.set_state(PetState.JUMP)
                self.mood_timer = 0

    def feed(self):
        self.hunger = 0
        self.mood = PetMood.HAPPY
        self.speech_text = "Mmm!"
        self.speech_timer = 2000
        self.set_state(PetState.JUMP)
        self.energy = min(100, self.energy + 20)

    def say_random_thing(self):
        import random
        
        num_words = random.randint(1, 4)
        sentence_words = []
        
        for _ in range(num_words):
            if random.random() < 0.2: # 20% chance to say name
                sentence_words.append(self.name)
            else:
                sentence_words.append(random.choice(self.sounds))
                
        sentence = " ".join(sentence_words)
        
        sentence = sentence.capitalize()
        
        punctuation = random.choice(["!", ".", "?", "!!"])
        sentence += punctuation
        
        self.speech_text = sentence
        self.speech_timer = 3000
        self.set_state(PetState.SPEAK)

    def get_render_data(self):
        anim = self.animations[self.current_state]
        frames = list(anim['frames']) 
        
        if self.current_frame_index < len(frames):
            global_index = frames[self.current_frame_index]
            pixmap = self.loader.sprites[global_index]
            
            offset_x = self.offset_x
            offset_y = self.offset_y
            
            scale_x = 1.0
            scale_y = 1.0
            rotation = self.rotation
            color_tint = None
            
            if self.current_state in [PetState.IDLE, PetState.IDLE_WINK]:

                cycle = (self.bob_timer % 3000) / 3000.0
                scale_y = 1.0 + 0.03 * math.sin(cycle * 2 * math.pi)
                
            if 60 <= global_index <= 69:
                offset_y += 20
                
            if self.current_state == PetState.DRAG:
                rotation = 10 * math.sin(self.bob_timer / 200.0)
                
            if self.current_state == PetState.SPAWN:
                progress = min(1.0, self.bob_timer / 1000.0)
                scale = 0.1 + 0.9 * progress
                scale_x = scale
                scale_y = scale
                
            return (pixmap, offset_x, offset_y, scale_x, scale_y, rotation, color_tint)
            
        return None
