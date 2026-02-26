import sys
import time
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QFont

# --- YOUR CALIBRATION CLASS ---
class Calibration:
    def __init__(self, screen_width, screen_height, dwell_time=1.5):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.dwell_time = dwell_time
        self.steps = ["TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT", "CENTER"]
        
        # We add a small margin (50px) so dots aren't cut off by screen edges
        margin = 50
        self.screen_points = {
            "TOP_LEFT": (margin, margin),
            "TOP_RIGHT": (screen_width - margin, margin),
            "BOTTOM_LEFT": (margin, screen_height - margin),
            "BOTTOM_RIGHT": (screen_width - margin, screen_height - margin),
            "CENTER": (screen_width // 2, screen_height // 2),
        }
        self.gaze_samples = {step: [] for step in self.steps}
        self.current_step = 0
        self.start_time = None
        self.completed = False
        self.coeff_x = None
        self.coeff_y = None

    def record(self, gaze_offset):
        if self.completed: return False
        if self.start_time is None: self.start_time = time.time()

        if time.time() - self.start_time < self.dwell_time:
            return False

        step = self.steps[self.current_step]
        self.gaze_samples[step].append(gaze_offset)
        self.current_step += 1
        self.start_time = None

        if self.current_step >= len(self.steps):
            self.completed = True
            self.compute_mapping()
        return True

    def compute_mapping(self):
        gaze_x, gaze_y, screen_x, screen_y = [], [], [], []
        for step in self.steps:
            gx, gy = np.mean(self.gaze_samples[step], axis=0)
            sx, sy = self.screen_points[step]
            gaze_x.append(gx); gaze_y.append(gy)
            screen_x.append(sx); screen_y.append(sy)
        
        # Filter warnings for testing
        import warnings
        warnings.simplefilter('ignore', np.RankWarning)
        
        self.coeff_x = np.polyfit(gaze_x, screen_x, 1)
        self.coeff_y = np.polyfit(gaze_y, screen_y, 1)

# --- THE VISUAL GUI ---
class CalibrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Set window to full screen and transparent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

        # Get screen size for your class
        screen_geo = self.screen().geometry()
        self.calib = Calibration(screen_geo.width(), screen_geo.height())

        # Timer to check for "Gaze" (Mouse for now)
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_logic)
        self.timer.start(50)

    def process_logic(self):
        if not self.calib.completed:
            # Use Mouse position as proxy for Gaze
            from PyQt6.QtGui import QCursor
            pos = QCursor.pos()
            # Pass (x, y) to your record function
            if self.calib.record((pos.x(), pos.y())):
                self.update() # Redraw when moving to next dot
        else:
            print(f"X-Coeff: {self.calib.coeff_x}")
            print(f"Y-Coeff: {self.calib.coeff_y}")
            self.timer.stop()
            time.sleep(1)
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw a semi-transparent dark background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))

        if not self.calib.completed:
            step = self.calib.steps[self.calib.current_step]
            target_x, target_y = self.calib.screen_points[step]

            # Draw the Target Dot
            painter.setBrush(QColor(0, 242, 254)) # Cyan
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(target_x), int(target_y)), 20, 20)

            # Center white dot
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(QPoint(int(target_x), int(target_y)), 6, 6)

            # Instructions
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"DWELL ON THE {step.replace('_', ' ')} DOT")
        else:
            painter.setPen(QColor(0, 255, 127))
            painter.setFont(QFont("Arial", 32, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "CALIBRATION COMPLETE ✅")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalibrationWindow()
    window.show()
    sys.exit(app.exec())