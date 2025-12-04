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

        datas = img.getdata()
        new_data = []
        for item in datas:
            if item[1] > 100 and item[1] > item[0] + 40 and item[1] > item[2] + 40:
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append(item)
        
        img.putdata(new_data)

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

class PetSystem:
    def __init__(self, sprite_path='assets/defaultspritesheet.png'):
        self.load_style(sprite_path)
        
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

    def load_style(self, sprite_path):
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
        }
        
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
                            
                            if r < 0.40: 
                                if random.random() < 0.5:
                                    self.set_state(PetState.MOVE_RIGHT)
                                else:
                                    self.set_state(PetState.MOVE_LEFT)
                            elif r < 0.50:
                                self.set_state(PetState.LOOK_SEQUENCE)
                            elif r < 0.60:
                                self.set_state(PetState.SPEAK)
                            elif r < 0.70:
                                self.set_state(PetState.INQUISITIVE)
                            elif r < 0.75:
                                self.set_state(PetState.SLEEP)
                            elif r < 0.80:
                                self.set_state(PetState.SPIN)
                            elif r < 0.85:
                                self.set_state(PetState.JUMP)
                            elif r < 0.92:
                                self.set_state(PetState.SHAKE)
                            elif r < 0.94: 
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
