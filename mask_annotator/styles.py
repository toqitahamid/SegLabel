"""
UI styling and screen scaling utilities for the Methane Mask Annotator.
"""

from PyQt5.QtWidgets import QApplication


# Global scale factor - will be set in main()
UI_SCALE = 1.0


def get_ui_scale_factor() -> float:
    """
    Calculate UI scale factor based on screen resolution.
    Returns a scale factor where 1.0 = optimized for 1080p (21" monitor).
    Larger screens (1440p, 4K) get values > 1.0.
    """
    try:
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                geometry = screen.availableGeometry()
                height = geometry.height()
                # Base reference: 1080p height
                # Scale factor ranges from 0.7 (small screens) to 1.5 (4K)
                if height <= 768:
                    return 0.6
                elif height <= 900:
                    return 0.7
                elif height <= 1080:
                    return 0.85
                elif height <= 1200:
                    return 0.95
                elif height <= 1440:
                    return 1.1
                elif height <= 1600:
                    return 1.2
                else:  # 4K and above
                    return 1.4
    except Exception:
        pass
    return 0.85  # Default for 1080p


def generate_scaled_stylesheet(scale: float = 1.0) -> str:
    """
    Generate stylesheet with scaled font sizes and dimensions.
    Scale of 1.0 = 32" monitor sizes (original).
    Scale of 0.7 = 21" monitor sizes.
    """
    # Helper to scale integers
    def s(val):
        return max(1, int(val * scale))

    return f"""
/* === MAIN WINDOW === */
QMainWindow {{
    background-color: #0a0e14;
}}

QWidget {{
    background-color: #0a0e14;
    color: #c5cdd9;
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: {s(14)}px;
}}

/* === FRAMES & PANELS === */
QFrame {{
    background-color: #121820;
    border: 1px solid #1e2832;
    border-radius: {s(3)}px;
}}

QFrame#folderFrame {{
    background-color: #0d1117;
    border: 1px solid #21262d;
    padding: {s(4)}px;
}}

QFrame#navFrame {{
    background-color: #161b22;
    border: 1px solid #30363d;
    border-left: 2px solid #58a6ff;
}}

/* === GROUP BOXES === */
QGroupBox {{
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: {s(6)}px;
    margin-top: {s(14)}px;
    padding: {s(10)}px;
    padding-top: {s(22)}px;
    font-weight: bold;
    font-size: {s(13)}px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {s(8)}px;
    padding: {s(3)}px {s(8)}px;
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: {s(3)}px;
    color: #58a6ff;
    font-size: {s(12)}px;
    letter-spacing: 1px;
}}

QGroupBox#syringeGroup {{
    border-left: 2px solid #3b82f6;
}}

QGroupBox#syringeGroup::title {{
    color: #60a5fa;
    background-color: rgba(59, 130, 246, 0.15);
}}

QGroupBox#gasGroup {{
    border-left: 2px solid #f59e0b;
}}

QGroupBox#gasGroup::title {{
    color: #fbbf24;
    background-color: rgba(245, 158, 11, 0.15);
}}

QGroupBox#actionsGroup {{
    border-left: 2px solid #10b981;
}}

QGroupBox#actionsGroup::title {{
    color: #34d399;
    background-color: rgba(16, 185, 129, 0.15);
}}

QGroupBox#settingsGroup {{
    border-left: 2px solid #8b5cf6;
}}

QGroupBox#settingsGroup::title {{
    color: #a78bfa;
    background-color: rgba(139, 92, 246, 0.15);
}}

/* === BUTTONS === */
QPushButton {{
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: {s(4)}px;
    padding: {s(8)}px {s(14)}px;
    color: #c9d1d9;
    font-weight: 500;
    font-size: {s(13)}px;
    min-height: {s(28)}px;
}}

QPushButton:hover {{
    background-color: #30363d;
    border-color: #58a6ff;
}}

QPushButton:pressed {{
    background-color: #0d1117;
}}

QPushButton:disabled {{
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}}

QPushButton#primaryBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #238636, stop:1 #2ea043);
    border: 1px solid #2ea043;
    color: white;
    font-weight: bold;
    font-size: {s(14)}px;
}}

QPushButton#primaryBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2ea043, stop:1 #3fb950);
    border-color: #3fb950;
}}

QPushButton#dangerBtn {{
    background-color: #da3633;
    border-color: #f85149;
    color: white;
}}

QPushButton#dangerBtn:hover {{
    background-color: #f85149;
}}

QPushButton#syringeBtn {{
    background-color: #21262d;
    border: 1px solid #3b82f6;
    color: #60a5fa;
}}

QPushButton#syringeBtn:hover {{
    background-color: rgba(59, 130, 246, 0.2);
    border-color: #60a5fa;
}}

QPushButton#syringeBtn:checked {{
    background-color: #3b82f6;
    color: white;
    font-weight: bold;
}}

QPushButton#navBtn {{
    background-color: #21262d;
    border: 1px solid #30363d;
    padding: {s(10)}px {s(18)}px;
    font-size: {s(15)}px;
    font-weight: bold;
    min-height: {s(32)}px;
}}

QPushButton#navBtn:hover {{
    background-color: #30363d;
    border-color: #58a6ff;
}}

/* === RADIO BUTTONS === */
QRadioButton {{
    spacing: {s(8)}px;
    padding: {s(6)}px {s(4)}px;
    font-size: {s(13)}px;
}}

QRadioButton::indicator {{
    width: {s(14)}px;
    height: {s(14)}px;
    border-radius: {s(7)}px;
    border: 2px solid #484f58;
    background-color: #0d1117;
}}

QRadioButton::indicator:hover {{
    border-color: #58a6ff;
}}

QRadioButton::indicator:checked {{
    border-color: #f59e0b;
    background-color: #f59e0b;
}}

QRadioButton:checked {{
    color: #fbbf24;
    font-weight: bold;
}}

/* === CHECKBOXES === */
QCheckBox {{
    spacing: {s(8)}px;
    padding: {s(6)}px;
    font-size: {s(13)}px;
}}

QCheckBox::indicator {{
    width: {s(14)}px;
    height: {s(14)}px;
    border-radius: {s(3)}px;
    border: 2px solid #484f58;
    background-color: #0d1117;
}}

QCheckBox::indicator:hover {{
    border-color: #58a6ff;
}}

QCheckBox::indicator:checked {{
    border-color: #58a6ff;
    background-color: #58a6ff;
}}

/* === SLIDERS === */
QSlider::groove:horizontal {{
    height: {s(6)}px;
    background: #21262d;
    border-radius: {s(3)}px;
}}

QSlider::handle:horizontal {{
    width: {s(14)}px;
    height: {s(14)}px;
    margin: {s(-4)}px 0;
    background: #58a6ff;
    border-radius: {s(7)}px;
}}

QSlider::handle:horizontal:hover {{
    background: #79c0ff;
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1f6feb, stop:1 #58a6ff);
    border-radius: {s(2)}px;
}}

/* === COMBOBOX === */
QComboBox {{
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: {s(3)}px;
    padding: {s(6)}px {s(10)}px;
    min-width: {s(100)}px;
    font-size: {s(13)}px;
    color: #c9d1d9;
}}

QComboBox:hover {{
    border-color: #58a6ff;
}}

QComboBox::drop-down {{
    border: none;
    padding-right: {s(4)}px;
}}

QComboBox::down-arrow {{
    width: {s(8)}px;
    height: {s(8)}px;
}}

QComboBox QAbstractItemView {{
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
}}

/* === LABELS === */
QLabel {{
    color: #8b949e;
    background: transparent;
    border: none;
}}

QLabel#titleLabel {{
    font-size: {s(20)}px;
    font-weight: bold;
    color: #58a6ff;
    letter-spacing: 1px;
}}

QLabel#pathLabel {{
    color: #7ee787;
    font-family: 'Consolas', monospace;
    font-size: {s(12)}px;
    padding: {s(4)}px {s(6)}px;
    background-color: rgba(46, 160, 67, 0.1);
    border-radius: {s(2)}px;
}}

QLabel#statusGood {{
    color: #3fb950;
    font-weight: bold;
}}

QLabel#statusWarning {{
    color: #d29922;
    font-weight: bold;
}}

QLabel#statusBad {{
    color: #f85149;
    font-weight: bold;
}}

QLabel#imageNameLabel {{
    font-size: {s(15)}px;
    font-weight: bold;
    color: #c9d1d9;
    padding: {s(4)}px {s(8)}px;
    background-color: #21262d;
    border-radius: {s(3)}px;
}}

QLabel#counterLabel {{
    font-size: {s(14)}px;
    color: #8b949e;
    font-family: 'Consolas', monospace;
}}

QLabel#statsLabel {{
    font-size: {s(12)}px;
    color: #8b949e;
    padding: {s(4)}px {s(6)}px;
    background-color: #161b22;
    border-radius: {s(3)}px;
}}

QLabel#coordLabel {{
    font-family: 'Consolas', monospace;
    font-size: {s(12)}px;
    color: #58a6ff;
}}

/* === STATUS BAR === */
QStatusBar {{
    background-color: #161b22;
    border-top: 1px solid #21262d;
    color: #8b949e;
    font-size: {s(12)}px;
    min-height: {s(24)}px;
}}

QStatusBar QLabel {{
    padding: {s(5)}px {s(10)}px;
    margin: 0 {s(4)}px;
    font-size: {s(12)}px;
}}

/* === SCROLL AREA === */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: #0d1117;
    width: {s(8)}px;
    border-radius: {s(4)}px;
}}

QScrollBar::handle:vertical {{
    background-color: #30363d;
    border-radius: {s(4)}px;
    min-height: {s(20)}px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #484f58;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* === SPLITTER === */
QSplitter::handle {{
    background-color: #21262d;
    width: {s(5)}px;
}}

QSplitter::handle:hover {{
    background-color: #58a6ff;
}}
"""
