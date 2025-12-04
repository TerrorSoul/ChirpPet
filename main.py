import sys
import os
import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QAction, QCursor, QColor, QIcon
from pet_system import PetSystem, PetState

LOGGING_ENABLED = False

def log_startup(msg):
    if LOGGING_ENABLED:
        with open("startup_log.txt", "a") as f:
            f.write(f"{datetime.datetime.now()}: {msg}\n")

def exception_hook(exctype, value, traceback_obj):
    import traceback
    traceback_text = "".join(traceback.format_exception(exctype, value, traceback_obj))
    log_startup(f"CRASH (Uncaught): {value}")
    log_startup(traceback_text)
    with open("crash_log.txt", "w") as f:
        f.write(f"CRASH DATE: {datetime.datetime.now()}\n")
        f.write(traceback_text)
    sys.exit(1)

sys.excepthook = exception_hook

log_startup("Starting main.py...")
print("Starting main.py...")

class PetWindow(QMainWindow):
    def __init__(self):
        log_startup("Initializing PetWindow")
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool 
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        log_startup("Initializing PetSystem...")
        self.pet = PetSystem('assets/defaultspritesheet.png')
        log_startup("PetSystem Initialized")
        
        self.resize(200, 200)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16) 
        
        self.old_pos = None
        self.is_dragging = False
        self.click_start_pos = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        style_menu = menu.addMenu("Style")

        def set_style(style_name):
            if style_name == "Default":
                self.pet.load_style('assets/defaultspritesheet.png')
            elif style_name == "Christmas":
                self.pet.load_style('assets/christmasspritesheet.png')
            elif style_name == "Sombrero":
                self.pet.load_style('assets/sombrerospritesheet.png')
            self.update()

        action_style_default = QAction("Default", self)
        action_style_default.triggered.connect(lambda checked: set_style("Default"))
        style_menu.addAction(action_style_default)

        action_style_xmas = QAction("Christmas", self)
        action_style_xmas.triggered.connect(lambda checked: set_style("Christmas"))
        style_menu.addAction(action_style_xmas)

        action_style_sombrero = QAction("Sombrero", self)
        action_style_sombrero.triggered.connect(lambda checked: set_style("Sombrero"))
        style_menu.addAction(action_style_sombrero)

        menu.addSeparator()
        
        close_action = QAction("Close Pet", self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)
        
        menu.exec(event.globalPos())

    def game_loop(self):
        if self.old_pos:
            return

        mouse_pos = QCursor.pos()
        window_pos = self.pos()
        
        self.pet.update(16, mouse_pos, window_pos)
        
        if self.is_dragging:
            return

        if self.pet.current_state in [PetState.MOVE_RIGHT, PetState.MOVE_LEFT, PetState.MOONWALK_RIGHT, PetState.MOONWALK_LEFT, PetState.ZOOMIES, PetState.CHASE]:
            current_screen = QApplication.screenAt(self.pos())
            if not current_screen:
                current_screen = QApplication.primaryScreen()
            screen_geo = current_screen.availableGeometry()
            
            speed = 3
            if self.pet.current_state == PetState.ZOOMIES:
                speed = 10
            elif self.pet.current_state == PetState.CHASE:
                speed = 6
            
            move_x = 0
            move_y = 0
            
            if self.pet.current_state == PetState.CHASE:
                window_center_x = self.x() + self.width() // 2
                dx = mouse_pos.x() - window_center_x
                
                if abs(dx) < 20:
                    move_x = 0
                elif dx > 0:
                    move_x = speed
                    self.pet.direction = 1
                elif dx < 0:
                    move_x = -speed
                    self.pet.direction = -1
            elif self.pet.current_state == PetState.MOONWALK_RIGHT:
                move_x = speed
                self.pet.direction = -1 
            elif self.pet.current_state == PetState.MOONWALK_LEFT:
                move_x = -speed
                self.pet.direction = 1 
            else:
                move_x = self.pet.direction * speed
            
            new_x = self.x() + move_x
            target_y = self.y()
            
            if new_x < screen_geo.left():
                if move_x < 0: 
                    new_x = screen_geo.left()
                    if self.pet.current_state == PetState.ZOOMIES:
                        self.pet.direction = 1 
                        pass 
                    elif self.pet.current_state in [PetState.MOVE_RIGHT, PetState.MOVE_LEFT]:
                        self.pet.set_state(PetState.MOVE_RIGHT)
                    elif self.pet.current_state in [PetState.MOONWALK_RIGHT, PetState.MOONWALK_LEFT, PetState.CHASE]:
                        self.pet.set_state(PetState.IDLE)
                    
            elif new_x + self.width() > screen_geo.right():
                if move_x > 0: 
                    new_x = screen_geo.right() - self.width()
                    if self.pet.current_state == PetState.ZOOMIES:
                        self.pet.direction = -1 
                        pass
                    elif self.pet.current_state in [PetState.MOVE_RIGHT, PetState.MOVE_LEFT]:
                        self.pet.set_state(PetState.MOVE_LEFT)
                    elif self.pet.current_state in [PetState.MOONWALK_RIGHT, PetState.MOONWALK_LEFT, PetState.CHASE]:
                        self.pet.set_state(PetState.IDLE)
            
            self.move(new_x, target_y)
            
        self.setWindowOpacity(1.0)
            
        if self.pet.current_state == PetState.CORNER_POP:
            if not hasattr(self, 'pop_stage'):
                self.pop_stage = 'INIT'
                self.pop_timer = 0
                self.saved_pos = self.pos()
            self.pet.rotation = 0
            if hasattr(self, 'saved_pos'):
                self.move(self.saved_pos)
                del self.saved_pos
            del self.pop_stage

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        render_data = self.pet.get_render_data()
        
        if render_data:
            pixmap, offset_x, offset_y, scale_x, scale_y, rotation, color_tint = render_data
            
            base_x = 44
            base_y = 104
            
            draw_x = base_x + offset_x
            draw_y = base_y + offset_y
            
            if not hasattr(self, 'initial_pos_set'):
                current_screen = QApplication.screenAt(QCursor.pos()) 
                if not current_screen:
                    current_screen = QApplication.primaryScreen()
                screen_geo = current_screen.availableGeometry()
                target_y = screen_geo.bottom() - 200
                self.move(screen_geo.right() - 300, target_y)
                self.initial_pos_set = True

            painter.save()
            
            anchor_x = 56
            anchor_y = 96
            
            if self.pet.current_state in [PetState.SPIN, PetState.DRAG]:
                anchor_x = 56
                anchor_y = 48
            
            painter.translate(draw_x + anchor_x, draw_y + anchor_y)
            
            front_facing_states = [
                PetState.IDLE, PetState.IDLE_WINK, 
                PetState.SPEAK, PetState.SLEEP, 
                PetState.SPAWN, PetState.LOOK_SEQUENCE,
                PetState.FLAP, PetState.PUFF,
                PetState.FLAP_HARD, PetState.INQUISITIVE,
                PetState.SPIN, PetState.JUMP,
                PetState.SHAKE, PetState.GHOST,
                PetState.DRAG,
                PetState.MOVE_LEFT, PetState.MOONWALK_RIGHT
            ]
            if self.pet.direction == -1 and self.pet.current_state not in front_facing_states:
                painter.scale(-1, 1)
            
            if rotation != 0:
                painter.rotate(rotation)
                
            if scale_x != 1.0 or scale_y != 1.0:
                painter.scale(scale_x, scale_y)
                
            painter.drawPixmap(-anchor_x, -anchor_y, pixmap)
            
            if color_tint:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
                if isinstance(color_tint, float): 
                    color = QColor.fromHslF(color_tint, 1.0, 0.5)
                    color.setAlpha(100) 
                    painter.fillRect(int(draw_x), int(draw_y), pixmap.width(), pixmap.height(), color)
                elif isinstance(color_tint, QColor): 
                    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
                    color_tint.setAlpha(200) 
                    painter.fillRect(int(draw_x), int(draw_y), pixmap.width(), pixmap.height(), color_tint)
                
            painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            self.click_start_pos = event.globalPosition().toPoint()
            self.is_dragging = False

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
            if self.is_dragging:
                pass
            self.is_dragging = False

    def mouseMoveEvent(self, event):
        if self.old_pos:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.old_pos
            
            if not self.is_dragging:
                dist = (current_pos - self.click_start_pos).manhattanLength()
                if dist > 5: 
                    self.is_dragging = True
            
            if self.is_dragging:
                self.move(self.x() + delta.x(), self.y() + delta.y())
                
            self.old_pos = current_pos

    def closeEvent(self, event):
        log_startup("Closing PetWindow...")
        self.timer.stop()
        event.accept()
        QApplication.instance().quit()

if __name__ == "__main__":
    try:
        log_startup("Entering main block")
        app = QApplication(sys.argv)
        app.setApplicationName("ChirPet")
        log_startup("QApplication created")
        window = PetWindow()
        window.setWindowTitle("ChirPet")
        log_startup("Window created, showing...")
        window.show()
        log_startup("Window shown, executing app...")
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        log_startup(f"CRASH: {e}")
        log_startup(traceback.format_exc())
        with open("crash_log.txt", "w") as f:
            f.write(traceback.format_exc())
        print("CRASHED! See crash_log.txt")
        traceback.print_exc()
