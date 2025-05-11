from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer, Property
from PySide6.QtGui import QPainter, QColor

class LoadingOverlay(QWidget):
    """
    A semi-transparent overlay with a spinner and message
    that can be shown over any widget during loading operations
    """
    
    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.spinner = SpinnerWidget(self)
        layout.addWidget(self.spinner, 0, Qt.AlignCenter)
        
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
            background-color: transparent;
        """)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.8)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.hide()
    
    def set_message(self, message):
        """Update the loading message"""
        self.message_label.setText(message)
    
    def showEvent(self, event):
        """When shown, resize to parent and start spinner"""
        if self.parentWidget():
            self.resize(self.parentWidget().size())
        self.spinner.start()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """When hidden, stop the spinner"""
        self.spinner.stop()
        super().hideEvent(event)
    
    def paintEvent(self, event):
        """Paint the semi-transparent background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 150)) 
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        super().paintEvent(event)


class SpinnerWidget(QWidget):
    """
    A simple animated spinner widget
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._speed = 80  
    
    def _get_angle(self):
        return self._angle
    
    def _set_angle(self, angle):
        self._angle = angle
        self.update()
    
    angle = Property(int, _get_angle, _set_angle)
    
    def start(self):
        """Start the spinner animation"""
        self._timer.start(self._speed)
    
    def stop(self):
        """Stop the spinner animation"""
        self._timer.stop()
    
    def _rotate(self):
        """Rotate the spinner"""
        self._set_angle((self._angle + 30) % 360)
    
    def paintEvent(self, event):
        """Draw the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        
        for i in range(8):
            opacity = (i + 1) / 8.0
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, int(opacity * 255)))
            
            painter.save()
            painter.rotate(i * 45)
            painter.drawRoundedRect(-5, -20, 10, 15, 5, 5)
            painter.restore()