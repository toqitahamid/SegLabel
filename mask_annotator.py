"""
Methane Mask Annotator - PyQt5-based annotation tool for methane image analysis.

Features:
- Two mask types: Syringe (100) and Gas (255)
- Persistent syringe mask across images
- Multiple gas regions per image
- Folder-based workflow with session persistence
- Skip/Review functionality
- Undo/Redo support
- Keyboard shortcuts for efficient workflow

Author: Generated for Methane Ratio analysis
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Optional, Set, Tuple
from dataclasses import dataclass, field

import numpy as np
import cv2
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QCheckBox, QRadioButton,
    QButtonGroup, QGroupBox, QStatusBar, QComboBox, QSplitter,
    QFrame, QMessageBox, QSizePolicy, QSpacerItem, QScrollArea
)
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QBrush,
    QPolygon, QPainterPath, QCursor, QKeySequence, QFont, QPalette, QLinearGradient
)


# =============================================================================
# STYLE CONFIGURATION - Scientific Instrumentation Theme
# =============================================================================

STYLE_SHEET = """
/* === MAIN WINDOW === */
QMainWindow {
    background-color: #0a0e14;
}

QWidget {
    background-color: #0a0e14;
    color: #c5cdd9;
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: 18px;
}

/* === FRAMES & PANELS === */
QFrame {
    background-color: #121820;
    border: 1px solid #1e2832;
    border-radius: 4px;
}

QFrame#folderFrame {
    background-color: #0d1117;
    border: 1px solid #21262d;
    padding: 8px;
}

QFrame#navFrame {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #58a6ff;
}

/* === GROUP BOXES === */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 20px;
    padding: 18px;
    padding-top: 36px;
    font-weight: bold;
    font-size: 17px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 6px 14px;
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    color: #58a6ff;
    font-size: 16px;
    letter-spacing: 1px;
}

QGroupBox#syringeGroup {
    border-left: 3px solid #3b82f6;
}

QGroupBox#syringeGroup::title {
    color: #60a5fa;
    background-color: rgba(59, 130, 246, 0.15);
}

QGroupBox#gasGroup {
    border-left: 3px solid #f59e0b;
}

QGroupBox#gasGroup::title {
    color: #fbbf24;
    background-color: rgba(245, 158, 11, 0.15);
}

QGroupBox#actionsGroup {
    border-left: 3px solid #10b981;
}

QGroupBox#actionsGroup::title {
    color: #34d399;
    background-color: rgba(16, 185, 129, 0.15);
}

QGroupBox#settingsGroup {
    border-left: 3px solid #8b5cf6;
}

QGroupBox#settingsGroup::title {
    color: #a78bfa;
    background-color: rgba(139, 92, 246, 0.15);
}

/* === BUTTONS === */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 14px 22px;
    color: #c9d1d9;
    font-weight: 500;
    font-size: 17px;
    min-height: 44px;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #58a6ff;
}

QPushButton:pressed {
    background-color: #0d1117;
}

QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #238636, stop:1 #2ea043);
    border: 1px solid #2ea043;
    color: white;
    font-weight: bold;
    font-size: 18px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #2ea043, stop:1 #3fb950);
    border-color: #3fb950;
}

QPushButton#dangerBtn {
    background-color: #da3633;
    border-color: #f85149;
    color: white;
}

QPushButton#dangerBtn:hover {
    background-color: #f85149;
}

QPushButton#syringeBtn {
    background-color: rgba(59, 130, 246, 0.2);
    border: 1px solid #3b82f6;
    color: #60a5fa;
}

QPushButton#syringeBtn:hover {
    background-color: rgba(59, 130, 246, 0.3);
}

QPushButton#syringeBtn:checked {
    background-color: #3b82f6;
    color: white;
}

QPushButton#navBtn {
    background-color: #21262d;
    border: 1px solid #30363d;
    padding: 16px 28px;
    font-size: 20px;
    font-weight: bold;
    min-height: 50px;
}

QPushButton#navBtn:hover {
    background-color: #30363d;
    border-color: #58a6ff;
}

/* === RADIO BUTTONS === */
QRadioButton {
    spacing: 14px;
    padding: 10px 6px;
    font-size: 17px;
}

QRadioButton::indicator {
    width: 24px;
    height: 24px;
    border-radius: 12px;
    border: 2px solid #484f58;
    background-color: #0d1117;
}

QRadioButton::indicator:hover {
    border-color: #58a6ff;
}

QRadioButton::indicator:checked {
    border-color: #f59e0b;
    background-color: #f59e0b;
}

QRadioButton:checked {
    color: #fbbf24;
    font-weight: bold;
}

/* === CHECKBOXES === */
QCheckBox {
    spacing: 14px;
    padding: 10px;
    font-size: 16px;
}

QCheckBox::indicator {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    border: 2px solid #484f58;
    background-color: #0d1117;
}

QCheckBox::indicator:hover {
    border-color: #58a6ff;
}

QCheckBox::indicator:checked {
    border-color: #58a6ff;
    background-color: #58a6ff;
}

/* === SLIDERS === */
QSlider::groove:horizontal {
    height: 10px;
    background: #21262d;
    border-radius: 5px;
}

QSlider::handle:horizontal {
    width: 24px;
    height: 24px;
    margin: -7px 0;
    background: #58a6ff;
    border-radius: 12px;
}

QSlider::handle:horizontal:hover {
    background: #79c0ff;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1f6feb, stop:1 #58a6ff);
    border-radius: 3px;
}

/* === COMBOBOX === */
QComboBox {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 10px 16px;
    min-width: 160px;
    font-size: 16px;
    color: #c9d1d9;
}

QComboBox:hover {
    border-color: #58a6ff;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
}

/* === LABELS === */
QLabel {
    color: #8b949e;
    background: transparent;
    border: none;
}

QLabel#titleLabel {
    font-size: 28px;
    font-weight: bold;
    color: #58a6ff;
    letter-spacing: 2px;
}

QLabel#pathLabel {
    color: #7ee787;
    font-family: 'Consolas', monospace;
    font-size: 18px;
    padding: 6px 10px;
    background-color: rgba(46, 160, 67, 0.1);
    border-radius: 3px;
}

QLabel#statusGood {
    color: #3fb950;
    font-weight: bold;
}

QLabel#statusWarning {
    color: #d29922;
    font-weight: bold;
}

QLabel#statusBad {
    color: #f85149;
    font-weight: bold;
}

QLabel#imageNameLabel {
    font-size: 20px;
    font-weight: bold;
    color: #c9d1d9;
    padding: 6px 14px;
    background-color: #21262d;
    border-radius: 4px;
}

QLabel#counterLabel {
    font-size: 18px;
    color: #8b949e;
    font-family: 'Consolas', monospace;
}

QLabel#statsLabel {
    font-size: 16px;
    color: #8b949e;
    padding: 6px 10px;
    background-color: #161b22;
    border-radius: 4px;
}

QLabel#coordLabel {
    font-family: 'Consolas', monospace;
    font-size: 16px;
    color: #58a6ff;
}

/* === STATUS BAR === */
QStatusBar {
    background-color: #161b22;
    border-top: 1px solid #21262d;
    color: #8b949e;
    font-size: 16px;
    min-height: 36px;
}

QStatusBar QLabel {
    padding: 8px 16px;
    margin: 0 6px;
    font-size: 16px;
}

/* === SCROLL AREA === */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #0d1117;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #30363d;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* === SPLITTER === */
QSplitter::handle {
    background-color: #21262d;
}

QSplitter::handle:hover {
    background-color: #58a6ff;
}
"""


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Shape:
    """Represents a drawn shape (polygon, freehand path, or rectangle)."""
    shape_type: str  # 'polygon', 'freehand', 'rectangle'
    points: List[Tuple[int, int]]  # List of (x, y) coordinates
    
    def to_numpy(self) -> np.ndarray:
        """Convert points to numpy array for cv2.fillPoly."""
        return np.array(self.points, dtype=np.int32)


@dataclass
class SyringeVersion:
    """A syringe mask version that applies from a specific image index."""
    start_index: int  # Image index from which this syringe applies
    shapes: List[Shape] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "start_index": self.start_index,
            "shapes": [{"type": s.shape_type, "points": s.points} for s in self.shapes]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SyringeVersion':
        return cls(
            start_index=data.get("start_index", 0),
            shapes=[
                Shape(shape_type=s["type"], points=[tuple(p) for p in s["points"]])
                for s in data.get("shapes", [])
            ]
        )


@dataclass
class AnnotationSession:
    """Holds the current annotation session state."""
    images_folder: str = ""
    masks_folder: str = ""
    image_list: List[str] = field(default_factory=list)
    current_index: int = 0
    syringe_versions: List[SyringeVersion] = field(default_factory=list)  # Versioned syringe masks
    skipped_images: Set[str] = field(default_factory=set)
    review_images: Set[str] = field(default_factory=set)
    
    def get_syringe_for_index(self, index: int) -> List[Shape]:
        """Get the syringe shapes that apply to a given image index."""
        if not self.syringe_versions:
            return []
        
        # Find the version with the highest start_index that is <= index
        applicable_version = None
        for version in self.syringe_versions:
            if version.start_index <= index:
                if applicable_version is None or version.start_index > applicable_version.start_index:
                    applicable_version = version
        
        return applicable_version.shapes if applicable_version else []
    
    def add_syringe_version(self, start_index: int, shapes: List[Shape]):
        """Add a new syringe version starting from the given index."""
        # Remove any existing version at this exact index
        self.syringe_versions = [v for v in self.syringe_versions if v.start_index != start_index]
        # Add new version
        self.syringe_versions.append(SyringeVersion(start_index=start_index, shapes=shapes))
        # Sort by start_index
        self.syringe_versions.sort(key=lambda v: v.start_index)
    
    def clear_current_syringe(self, current_index: int):
        """Clear the syringe version that applies to the current index."""
        applicable = None
        for version in self.syringe_versions:
            if version.start_index <= current_index:
                if applicable is None or version.start_index > applicable.start_index:
                    applicable = version
        
        if applicable:
            self.syringe_versions.remove(applicable)
    
    def to_dict(self) -> dict:
        """Convert session to dictionary for JSON serialization."""
        return {
            "images_folder": self.images_folder,
            "masks_folder": self.masks_folder,
            "current_index": self.current_index,
            "syringe_versions": [v.to_dict() for v in self.syringe_versions],
            "skipped_images": list(self.skipped_images),
            "review_images": list(self.review_images)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnnotationSession':
        """Create session from dictionary."""
        session = cls()
        session.images_folder = data.get("images_folder", "")
        session.masks_folder = data.get("masks_folder", "")
        session.current_index = data.get("current_index", 0)
        
        # Handle both old format (syringe_shapes) and new format (syringe_versions)
        if "syringe_versions" in data:
            session.syringe_versions = [
                SyringeVersion.from_dict(v) for v in data.get("syringe_versions", [])
            ]
        elif "syringe_shapes" in data:
            # Migrate old format: treat old shapes as version starting at index 0
            old_shapes = [
                Shape(shape_type=s["type"], points=[tuple(p) for p in s["points"]])
                for s in data.get("syringe_shapes", [])
            ]
            if old_shapes:
                session.syringe_versions = [SyringeVersion(start_index=0, shapes=old_shapes)]
        
        session.skipped_images = set(data.get("skipped_images", []))
        session.review_images = set(data.get("review_images", []))
        return session


# =============================================================================
# UNDO/REDO SYSTEM
# =============================================================================

class UndoStack:
    """Simple undo/redo stack for shape operations."""
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.undo_stack: List[List[Shape]] = []
        self.redo_stack: List[List[Shape]] = []
    
    def push(self, shapes: List[Shape]):
        """Save current state before modification."""
        self.undo_stack.append([Shape(s.shape_type, list(s.points)) for s in shapes])
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
    
    def undo(self, current_shapes: List[Shape]) -> Optional[List[Shape]]:
        """Undo last action, return previous state."""
        if not self.undo_stack:
            return None
        self.redo_stack.append([Shape(s.shape_type, list(s.points)) for s in current_shapes])
        return self.undo_stack.pop()
    
    def redo(self, current_shapes: List[Shape]) -> Optional[List[Shape]]:
        """Redo last undone action."""
        if not self.redo_stack:
            return None
        self.undo_stack.append([Shape(s.shape_type, list(s.points)) for s in current_shapes])
        return self.redo_stack.pop()
    
    def clear(self):
        """Clear both stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()


# =============================================================================
# DRAWING CANVAS
# =============================================================================

class DrawingCanvas(QLabel):
    """Custom canvas widget for drawing masks on images."""
    
    # Signals
    shape_completed = pyqtSignal(Shape)
    mouse_moved = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #0d1117; border: 2px solid #21262d; border-radius: 4px;")
        
        # Image data
        self.original_image: Optional[np.ndarray] = None
        self.display_pixmap: Optional[QPixmap] = None
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        
        # Drawing state
        self.current_tool = "polygon"  # polygon, freehand, rectangle
        self.is_drawing_syringe = False
        self.current_points: List[Tuple[int, int]] = []
        self.is_drawing = False
        self.start_point: Optional[Tuple[int, int]] = None
        
        # Shapes
        self.syringe_shapes: List[Shape] = []
        self.gas_shapes: List[Shape] = []
        self.eraser_shapes: List[Shape] = []  # Eraser shapes (subtract from gas)
        
        # Display settings
        self.overlay_opacity = 0.5
        self.show_overlay = True
        
        # Existing mask (for verification mode)
        self.existing_mask: Optional[np.ndarray] = None
    
    def set_image(self, image: np.ndarray):
        """Set the image to display."""
        self.original_image = image
        self.update_display()
    
    def set_syringe_shapes(self, shapes: List[Shape]):
        """Set syringe shapes (from session)."""
        self.syringe_shapes = shapes
        self.update_display()
    
    def set_gas_shapes(self, shapes: List[Shape]):
        """Set gas shapes."""
        self.gas_shapes = shapes
        self.update_display()
    
    def set_eraser_shapes(self, shapes: List[Shape]):
        """Set eraser shapes."""
        self.eraser_shapes = shapes
        self.update_display()
    
    def clear_eraser_shapes(self):
        """Clear all eraser shapes."""
        self.eraser_shapes = []
        self.update_display()
    
    def set_existing_mask(self, mask: Optional[np.ndarray]):
        """Set existing mask for verification mode."""
        self.existing_mask = mask
        self.update_display()
    
    def clear_gas_shapes(self):
        """Clear all gas shapes."""
        self.gas_shapes = []
        self.update_display()
    
    def clear_syringe_shapes(self):
        """Clear all syringe shapes."""
        self.syringe_shapes.clear()
        self.update_display()
    
    def set_tool(self, tool: str):
        """Set the current drawing tool."""
        self.current_tool = tool
        self.cancel_current_drawing()
    
    def set_drawing_mode(self, is_syringe: bool):
        """Set whether we're drawing syringe or gas."""
        self.is_drawing_syringe = is_syringe
        self.cancel_current_drawing()
    
    def cancel_current_drawing(self):
        """Cancel any ongoing drawing operation."""
        self.current_points.clear()
        self.is_drawing = False
        self.start_point = None
        self.update_display()
    
    def image_to_widget_coords(self, img_x: int, img_y: int) -> QPoint:
        """Convert image coordinates to widget coordinates."""
        return QPoint(
            int(img_x * self.scale_factor) + self.offset.x(),
            int(img_y * self.scale_factor) + self.offset.y()
        )
    
    def widget_to_image_coords(self, widget_pos: QPoint) -> Tuple[int, int]:
        """Convert widget coordinates to image coordinates."""
        img_x = int((widget_pos.x() - self.offset.x()) / self.scale_factor)
        img_y = int((widget_pos.y() - self.offset.y()) / self.scale_factor)
        return (img_x, img_y)
    
    def is_valid_image_coord(self, x: int, y: int) -> bool:
        """Check if coordinates are within image bounds."""
        if self.original_image is None:
            return False
        h, w = self.original_image.shape[:2]
        return 0 <= x < w and 0 <= y < h
    
    def update_display(self):
        """Update the displayed image with overlays."""
        if self.original_image is None:
            return
        
        # Create display image (RGB)
        if len(self.original_image.shape) == 2:
            display = cv2.cvtColor(self.original_image, cv2.COLOR_GRAY2RGB)
        else:
            display = self.original_image.copy()
        
        h, w = display.shape[:2]
        
        if self.show_overlay:
            # Create overlay layer
            overlay = display.copy()
            
            # Draw existing mask if in verification mode
            if self.existing_mask is not None:
                # Syringe regions (value 100) - Blue
                syringe_region = (self.existing_mask == 100)
                overlay[syringe_region] = [59, 130, 246]  # Blue
                
                # Gas regions (value 255) - Amber/Orange
                gas_region = (self.existing_mask == 255)
                overlay[gas_region] = [245, 158, 11]  # Amber
            
            # Draw syringe shapes - Blue
            for shape in self.syringe_shapes:
                pts = shape.to_numpy()
                if len(pts) >= 3:
                    cv2.fillPoly(overlay, [pts], (59, 130, 246))
            
            # Draw gas shapes - Amber
            for shape in self.gas_shapes:
                pts = shape.to_numpy()
                if len(pts) >= 3:
                    cv2.fillPoly(overlay, [pts], (245, 158, 11))
                elif shape.shape_type == 'rectangle' and len(pts) == 2:
                    cv2.rectangle(overlay, tuple(pts[0]), tuple(pts[1]), (245, 158, 11), -1)
            
            # Draw eraser shapes - Dark red/maroon (shows as "erased" areas)
            for shape in self.eraser_shapes:
                pts = shape.to_numpy()
                if len(pts) >= 3:
                    cv2.fillPoly(overlay, [pts], (80, 40, 40))  # Dark color to show erasure
            
            # Blend overlay
            alpha = self.overlay_opacity
            display = cv2.addWeighted(overlay, alpha, display, 1 - alpha, 0)
        
        # Scale to fit widget
        widget_w, widget_h = self.width(), self.height()
        scale_w = widget_w / w
        scale_h = widget_h / h
        self.scale_factor = min(scale_w, scale_h)
        
        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)
        
        # Center the image
        self.offset = QPoint((widget_w - new_w) // 2, (widget_h - new_h) // 2)
        
        # Resize and convert to QPixmap
        display_resized = cv2.resize(display, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Convert BGR to RGB for Qt
        display_rgb = cv2.cvtColor(display_resized, cv2.COLOR_BGR2RGB)
        
        qimage = QImage(
            display_rgb.data, new_w, new_h, 
            new_w * 3, QImage.Format_RGB888
        )
        self.display_pixmap = QPixmap.fromImage(qimage)
        self.setPixmap(self.display_pixmap)
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event to draw current shape being drawn."""
        super().paintEvent(event)
        
        if self.display_pixmap is None:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set pen based on what we're drawing
        if self.is_drawing_syringe:
            pen = QPen(QColor(59, 130, 246, 220), 2)
            brush = QBrush(QColor(59, 130, 246, 80))
        else:
            pen = QPen(QColor(245, 158, 11, 220), 2)
            brush = QBrush(QColor(245, 158, 11, 80))
        
        painter.setPen(pen)
        
        # Draw current polygon/freehand points
        if self.current_tool in ('polygon', 'freehand') and len(self.current_points) > 0:
            polygon = QPolygon([self.image_to_widget_coords(x, y) for x, y in self.current_points])
            
            if len(self.current_points) >= 3:
                painter.setBrush(brush)
                painter.drawPolygon(polygon)
            else:
                painter.drawPolyline(polygon)
            
            # Draw vertices
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            for x, y in self.current_points:
                pt = self.image_to_widget_coords(x, y)
                painter.drawEllipse(pt, 5, 5)
        
        # Draw current rectangle
        elif self.current_tool == 'rectangle' and self.start_point and self.is_drawing:
            if len(self.current_points) > 0:
                x1, y1 = self.start_point
                x2, y2 = self.current_points[-1]
                p1 = self.image_to_widget_coords(x1, y1)
                p2 = self.image_to_widget_coords(x2, y2)
                painter.setBrush(brush)
                painter.drawRect(QRect(p1, p2))
        
        painter.end()
    
    def mousePressEvent(self, event):
        """Handle mouse press for drawing."""
        if self.original_image is None:
            return
        
        pos = event.pos()
        img_x, img_y = self.widget_to_image_coords(pos)
        
        if not self.is_valid_image_coord(img_x, img_y):
            return
        
        if event.button() == Qt.LeftButton:
            if self.current_tool == 'polygon':
                self.current_points.append((img_x, img_y))
                self.update()
            
            elif self.current_tool == 'freehand':
                self.is_drawing = True
                self.current_points = [(img_x, img_y)]
                self.update()
            
            elif self.current_tool == 'rectangle':
                self.is_drawing = True
                self.start_point = (img_x, img_y)
                self.current_points = [(img_x, img_y)]
                self.update()
        
        elif event.button() == Qt.RightButton:
            # Complete current shape
            self._complete_shape()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drawing and coordinates display."""
        pos = event.pos()
        img_x, img_y = self.widget_to_image_coords(pos)
        
        self.mouse_moved.emit(img_x, img_y)
        
        if self.original_image is None:
            return
        
        if self.is_drawing:
            if self.is_valid_image_coord(img_x, img_y):
                if self.current_tool == 'freehand':
                    # Add point with some distance threshold to avoid too many points
                    if len(self.current_points) > 0:
                        last_x, last_y = self.current_points[-1]
                        dist = ((img_x - last_x) ** 2 + (img_y - last_y) ** 2) ** 0.5
                        if dist > 3:  # Minimum distance between points
                            self.current_points.append((img_x, img_y))
                    else:
                        self.current_points.append((img_x, img_y))
                    self.update()
                
                elif self.current_tool == 'rectangle':
                    if len(self.current_points) > 1:
                        self.current_points[-1] = (img_x, img_y)
                    else:
                        self.current_points.append((img_x, img_y))
                    self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            if self.current_tool == 'freehand' and self.is_drawing:
                self._complete_shape()
            
            elif self.current_tool == 'rectangle' and self.is_drawing:
                self._complete_shape()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click to complete polygon."""
        if event.button() == Qt.LeftButton and self.current_tool == 'polygon':
            self._complete_shape()
    
    def _complete_shape(self):
        """Complete the current shape and emit signal."""
        if len(self.current_points) < 3 and self.current_tool != 'rectangle':
            self.cancel_current_drawing()
            return
        
        if self.current_tool == 'rectangle' and self.start_point and len(self.current_points) >= 1:
            # Convert rectangle to polygon (4 corners)
            x1, y1 = self.start_point
            x2, y2 = self.current_points[-1]
            self.current_points = [
                (min(x1, x2), min(y1, y2)),
                (max(x1, x2), min(y1, y2)),
                (max(x1, x2), max(y1, y2)),
                (min(x1, x2), max(y1, y2))
            ]
        
        if len(self.current_points) >= 3:
            shape = Shape(
                shape_type=self.current_tool,
                points=list(self.current_points)
            )
            self.shape_completed.emit(shape)
        
        self.cancel_current_drawing()
    
    def resizeEvent(self, event):
        """Handle resize to update display."""
        super().resizeEvent(event)
        self.update_display()


# =============================================================================
# MAIN WINDOW
# =============================================================================

class MethaneAnnotator(QMainWindow):
    """Main application window for the Methane Mask Annotator."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("METHANE MASK ANNOTATOR")
        self.setMinimumSize(1600, 1000)
        
        # Session state
        self.session = AnnotationSession()
        self.gas_shapes: List[Shape] = []  # Current image's gas shapes
        self.eraser_shapes: List[Shape] = []  # Current image's eraser shapes
        self.undo_stack = UndoStack()
        self.is_eraser_mode = False  # Track if we're in eraser mode
        self.has_unsaved_changes = False  # Track if user made changes to current image
        self._existing_overlay_visible = True  # Track overlay visibility state
        
        # Setup UI
        self._setup_ui()
        self._setup_shortcuts()
        
        # Try to load last session
        self._check_for_session()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # === HEADER ===
        header_layout = QHBoxLayout()
        title_label = QLabel("◆ METHANE MASK ANNOTATOR")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # === TOP: Folder selection ===
        folder_frame = QFrame()
        folder_frame.setObjectName("folderFrame")
        folder_layout = QVBoxLayout(folder_frame)
        folder_layout.setSpacing(8)
        
        # Images folder row
        images_row = QHBoxLayout()
        images_label = QLabel("📁 IMAGES:")
        images_label.setStyleSheet("font-weight: bold; color: #58a6ff; font-size: 18px;")
        images_row.addWidget(images_label)
        self.images_path_label = QLabel("Select folder...")
        self.images_path_label.setObjectName("pathLabel")
        self.images_path_label.setStyleSheet("color: #484f58; background: transparent;")
        images_row.addWidget(self.images_path_label, stretch=1)
        self.browse_images_btn = QPushButton("Browse")
        self.browse_images_btn.setFixedWidth(140)
        self.browse_images_btn.clicked.connect(self._browse_images_folder)
        images_row.addWidget(self.browse_images_btn)
        folder_layout.addLayout(images_row)
        
        # Masks folder row
        masks_row = QHBoxLayout()
        masks_label = QLabel("💾 MASKS:")
        masks_label.setStyleSheet("font-weight: bold; color: #3fb950; font-size: 18px;")
        masks_row.addWidget(masks_label)
        self.masks_path_label = QLabel("Select folder...")
        self.masks_path_label.setObjectName("pathLabel")
        self.masks_path_label.setStyleSheet("color: #484f58; background: transparent;")
        masks_row.addWidget(self.masks_path_label, stretch=1)
        self.browse_masks_btn = QPushButton("Browse")
        self.browse_masks_btn.setFixedWidth(140)
        self.browse_masks_btn.clicked.connect(self._browse_masks_folder)
        masks_row.addWidget(self.browse_masks_btn)
        folder_layout.addLayout(masks_row)
        
        main_layout.addWidget(folder_frame)
        
        # === NAVIGATION BAR ===
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(12, 8, 12, 8)
        nav_layout.setSpacing(12)
        
        self.prev_btn = QPushButton("◀  PREV")
        self.prev_btn.setObjectName("navBtn")
        self.prev_btn.setFixedWidth(140)
        self.prev_btn.clicked.connect(self._prev_image)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("NEXT  ▶")
        self.next_btn.setObjectName("navBtn")
        self.next_btn.setFixedWidth(140)
        self.next_btn.clicked.connect(self._next_image)
        nav_layout.addWidget(self.next_btn)
        
        # Separator
        sep1 = QLabel("│")
        sep1.setStyleSheet("color: #30363d; font-size: 20px;")
        nav_layout.addWidget(sep1)
        
        self.image_counter_label = QLabel("Image 0 of 0")
        self.image_counter_label.setObjectName("counterLabel")
        nav_layout.addWidget(self.image_counter_label)
        
        sep2 = QLabel("│")
        sep2.setStyleSheet("color: #30363d; font-size: 20px;")
        nav_layout.addWidget(sep2)
        
        self.current_image_label = QLabel("")
        self.current_image_label.setObjectName("imageNameLabel")
        nav_layout.addWidget(self.current_image_label)
        
        self.status_indicator = QLabel("")
        self.status_indicator.setStyleSheet("font-size: 18px; font-weight: bold;")
        nav_layout.addWidget(self.status_indicator)
        
        nav_layout.addStretch()
        
        # Filter dropdown
        filter_label = QLabel("FILTER:")
        filter_label.setStyleSheet("color: #8b949e; font-weight: bold; font-size: 16px;")
        nav_layout.addWidget(filter_label)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Not Annotated", "Annotated", "Skipped", "Review"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        nav_layout.addWidget(self.filter_combo)
        
        sep3 = QLabel("│")
        sep3.setStyleSheet("color: #30363d; font-size: 20px;")
        nav_layout.addWidget(sep3)
        
        self.stats_label = QLabel("Done: 0  │  Skipped: 0  │  Review: 0")
        self.stats_label.setObjectName("statsLabel")
        nav_layout.addWidget(self.stats_label)
        
        main_layout.addWidget(nav_frame)
        
        # === MAIN CONTENT: Canvas + Tools ===
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Canvas
        self.canvas = DrawingCanvas()
        self.canvas.shape_completed.connect(self._on_shape_completed)
        self.canvas.mouse_moved.connect(self._on_mouse_moved)
        content_splitter.addWidget(self.canvas)
        
        # Tools panel with scroll area
        tools_scroll = QScrollArea()
        tools_scroll.setWidgetResizable(True)
        tools_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tools_scroll.setMinimumWidth(450)
        tools_scroll.setMaximumWidth(550)
        
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setContentsMargins(8, 8, 8, 8)
        tools_layout.setSpacing(12)
        
        # Syringe mask section
        syringe_group = QGroupBox("SYRINGE MASK")
        syringe_group.setObjectName("syringeGroup")
        syringe_layout = QVBoxLayout(syringe_group)
        syringe_layout.setSpacing(10)
        
        syringe_info = QLabel("Draw syringe mask. New versions apply\nfrom current image forward.")
        syringe_info.setStyleSheet("color: #8b949e; font-size: 16px; line-height: 1.4;")
        syringe_info.setWordWrap(True)
        syringe_layout.addWidget(syringe_info)
        
        self.draw_syringe_btn = QPushButton("✏️  Draw New Syringe (from here)")
        self.draw_syringe_btn.setObjectName("syringeBtn")
        self.draw_syringe_btn.setCheckable(True)
        self.draw_syringe_btn.clicked.connect(self._toggle_syringe_mode)
        syringe_layout.addWidget(self.draw_syringe_btn)
        
        self.clear_syringe_btn = QPushButton("🗑️  Clear Current Syringe Version")
        self.clear_syringe_btn.clicked.connect(self._clear_current_syringe)
        syringe_layout.addWidget(self.clear_syringe_btn)
        
        self.syringe_status_label = QLabel("⚠ Status: Not defined")
        self.syringe_status_label.setObjectName("statusWarning")
        syringe_layout.addWidget(self.syringe_status_label)
        
        self.syringe_version_label = QLabel("")
        self.syringe_version_label.setStyleSheet("color: #8b949e; font-size: 14px;")
        syringe_layout.addWidget(self.syringe_version_label)
        
        tools_layout.addWidget(syringe_group)
        
        # Gas mask section
        gas_group = QGroupBox("GAS MASK")
        gas_group.setObjectName("gasGroup")
        gas_layout = QVBoxLayout(gas_group)
        gas_layout.setSpacing(10)
        
        gas_info = QLabel("Draw gas regions for current image.\nMultiple regions allowed.")
        gas_info.setStyleSheet("color: #8b949e; font-size: 16px; line-height: 1.4;")
        gas_info.setWordWrap(True)
        gas_layout.addWidget(gas_info)
        
        # Tool selection
        tools_label = QLabel("DRAWING TOOL:")
        tools_label.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 16px; margin-top: 4px;")
        gas_layout.addWidget(tools_label)
        
        self.tool_group = QButtonGroup(self)
        
        self.polygon_radio = QRadioButton("Polygon  (click vertices, right-click to finish)")
        self.polygon_radio.setChecked(True)
        self.tool_group.addButton(self.polygon_radio)
        gas_layout.addWidget(self.polygon_radio)
        
        self.freehand_radio = QRadioButton("Freehand  (hold & drag)")
        self.tool_group.addButton(self.freehand_radio)
        gas_layout.addWidget(self.freehand_radio)
        
        self.rectangle_radio = QRadioButton("Rectangle  (click & drag)")
        self.tool_group.addButton(self.rectangle_radio)
        gas_layout.addWidget(self.rectangle_radio)
        
        self.eraser_radio = QRadioButton("Eraser  (erase gas regions)")
        self.eraser_radio.setStyleSheet("color: #f87171;")  # Red tint for eraser
        self.tool_group.addButton(self.eraser_radio)
        gas_layout.addWidget(self.eraser_radio)
        
        self.tool_group.buttonClicked.connect(self._on_tool_changed)
        
        # Newly drawn gas actions
        drawn_label = QLabel("NEWLY DRAWN:")
        drawn_label.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 16px; margin-top: 8px;")
        gas_layout.addWidget(drawn_label)
        
        drawn_btns = QHBoxLayout()
        self.clear_drawn_gas_btn = QPushButton("🗑️ Gas")
        self.clear_drawn_gas_btn.setToolTip("Clear drawn gas shapes")
        self.clear_drawn_gas_btn.clicked.connect(self._clear_drawn_gas)
        drawn_btns.addWidget(self.clear_drawn_gas_btn)
        
        self.clear_eraser_btn = QPushButton("🗑️ Eraser")
        self.clear_eraser_btn.setToolTip("Clear eraser shapes")
        self.clear_eraser_btn.clicked.connect(self._clear_eraser)
        drawn_btns.addWidget(self.clear_eraser_btn)
        
        self.undo_btn = QPushButton("↩️")
        self.undo_btn.setToolTip("Undo (Ctrl+Z)")
        self.undo_btn.clicked.connect(self._undo)
        drawn_btns.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↪️")
        self.redo_btn.setToolTip("Redo (Ctrl+Y)")
        self.redo_btn.clicked.connect(self._redo)
        drawn_btns.addWidget(self.redo_btn)
        gas_layout.addLayout(drawn_btns)
        
        # Existing saved mask handling
        existing_label = QLabel("SAVED MASK FILE:")
        existing_label.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 16px; margin-top: 8px;")
        gas_layout.addWidget(existing_label)
        
        self.existing_mask_info = QLabel("No existing mask")
        self.existing_mask_info.setStyleSheet("color: #8b949e; font-size: 16px;")
        gas_layout.addWidget(self.existing_mask_info)
        
        existing_btns = QHBoxLayout()
        self.toggle_existing_btn = QPushButton("👁️ Hide")
        self.toggle_existing_btn.setToolTip("Toggle overlay visibility (file remains)")
        self.toggle_existing_btn.clicked.connect(self._toggle_existing_overlay)
        self.toggle_existing_btn.setEnabled(False)
        existing_btns.addWidget(self.toggle_existing_btn)
        
        self.clear_gas_only_btn = QPushButton("🧹 Clear Gas")
        self.clear_gas_only_btn.setToolTip("Remove gas from file, keep syringe")
        self.clear_gas_only_btn.clicked.connect(self._clear_gas_from_file)
        self.clear_gas_only_btn.setEnabled(False)
        existing_btns.addWidget(self.clear_gas_only_btn)
        
        self.delete_existing_btn = QPushButton("🗑️ Delete")
        self.delete_existing_btn.setToolTip("Delete entire mask file")
        self.delete_existing_btn.setObjectName("dangerBtn")
        self.delete_existing_btn.clicked.connect(self._delete_existing_mask)
        self.delete_existing_btn.setEnabled(False)
        existing_btns.addWidget(self.delete_existing_btn)
        gas_layout.addLayout(existing_btns)
        
        tools_layout.addWidget(gas_group)
        
        # Actions section
        actions_group = QGroupBox("ACTIONS")
        actions_group.setObjectName("actionsGroup")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(10)
        
        self.save_btn = QPushButton("💾  Save Mask")
        self.save_btn.clicked.connect(self._save_mask)
        actions_layout.addWidget(self.save_btn)
        
        self.save_next_btn = QPushButton("💾  Save & Next  →")
        self.save_next_btn.setObjectName("primaryBtn")
        self.save_next_btn.clicked.connect(self._save_and_next)
        actions_layout.addWidget(self.save_next_btn)
        
        skip_review_row = QHBoxLayout()
        self.skip_btn = QPushButton("⏭️  Skip")
        self.skip_btn.clicked.connect(self._skip_image)
        skip_review_row.addWidget(self.skip_btn)
        
        self.review_btn = QPushButton("🔖  Mark Review")
        self.review_btn.clicked.connect(self._mark_review)
        skip_review_row.addWidget(self.review_btn)
        actions_layout.addLayout(skip_review_row)
        
        tools_layout.addWidget(actions_group)
        
        # Settings section
        settings_group = QGroupBox("DISPLAY SETTINGS")
        settings_group.setObjectName("settingsGroup")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)
        
        opacity_label = QLabel("OVERLAY OPACITY:")
        opacity_label.setStyleSheet("color: #a78bfa; font-weight: bold; font-size: 16px;")
        settings_layout.addWidget(opacity_label)
        
        opacity_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("50%")
        self.opacity_label.setStyleSheet("color: #c9d1d9; font-weight: bold; min-width: 40px;")
        opacity_row.addWidget(self.opacity_label)
        settings_layout.addLayout(opacity_row)
        
        self.show_overlay_cb = QCheckBox("Show mask overlay")
        self.show_overlay_cb.setChecked(True)
        self.show_overlay_cb.stateChanged.connect(self._on_overlay_toggled)
        settings_layout.addWidget(self.show_overlay_cb)
        
        self.show_existing_cb = QCheckBox("Show existing masks (verification)")
        self.show_existing_cb.setChecked(True)
        self.show_existing_cb.stateChanged.connect(self._on_show_existing_changed)
        settings_layout.addWidget(self.show_existing_cb)
        
        tools_layout.addWidget(settings_group)
        
        # Spacer
        tools_layout.addStretch()
        
        # Session controls
        session_group = QGroupBox("SESSION")
        session_layout = QVBoxLayout(session_group)
        session_layout.setSpacing(8)
        
        self.new_session_btn = QPushButton("🔄  New Session")
        self.new_session_btn.clicked.connect(self._new_session)
        session_layout.addWidget(self.new_session_btn)
        
        tools_layout.addWidget(session_group)
        
        # Keyboard shortcuts info
        shortcuts_group = QGroupBox("KEYBOARD SHORTCUTS")
        shortcuts_layout = QVBoxLayout(shortcuts_group)
        shortcuts_layout.setSpacing(2)
        
        shortcuts = [
            ("←/→ or A/D", "Navigate images"),
            ("S", "Save mask"),
            ("Ctrl+S", "Save & Next"),
            ("1/2/3/4", "Poly/Free/Rect/Eraser"),
            ("Ctrl+Z/Y", "Undo/Redo"),
            ("X", "Skip image"),
            ("R", "Mark for review"),
            ("Space", "Toggle overlay"),
            ("Esc", "Cancel drawing"),
        ]
        
        for key, action in shortcuts:
            row = QHBoxLayout()
            key_label = QLabel(key)
            key_label.setStyleSheet("""
                background-color: #21262d; 
                color: #58a6ff; 
                padding: 6px 10px; 
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 15px;
                min-width: 100px;
            """)
            row.addWidget(key_label)
            action_label = QLabel(action)
            action_label.setStyleSheet("color: #8b949e; font-size: 15px;")
            row.addWidget(action_label)
            row.addStretch()
            shortcuts_layout.addLayout(row)
        
        tools_layout.addWidget(shortcuts_group)
        
        tools_scroll.setWidget(tools_widget)
        content_splitter.addWidget(tools_scroll)
        content_splitter.setSizes([1200, 520])
        
        main_layout.addWidget(content_splitter, stretch=1)
        
        # === STATUS BAR ===
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready — Select images and masks folders to begin")
        
        self.coord_label = QLabel("Pos: (—, —)")
        self.coord_label.setObjectName("coordLabel")
        self.statusBar.addPermanentWidget(self.coord_label)
        
        self.tool_label = QLabel("Tool: Polygon")
        self.tool_label.setStyleSheet("color: #fbbf24;")
        self.statusBar.addPermanentWidget(self.tool_label)
        
        self.session_status_label = QLabel("Session: Not saved")
        self.session_status_label.setStyleSheet("color: #8b949e;")
        self.statusBar.addPermanentWidget(self.session_status_label)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        from PyQt5.QtWidgets import QShortcut
        
        # Navigation
        QShortcut(QKeySequence(Qt.Key_Right), self, self._next_image)
        QShortcut(QKeySequence(Qt.Key_D), self, self._next_image)
        QShortcut(QKeySequence(Qt.Key_Left), self, self._prev_image)
        QShortcut(QKeySequence(Qt.Key_A), self, self._prev_image)
        
        # Save
        QShortcut(QKeySequence(Qt.Key_S), self, self._save_mask)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_and_next)
        
        # Tools
        QShortcut(QKeySequence(Qt.Key_1), self, lambda: self._select_tool('polygon'))
        QShortcut(QKeySequence(Qt.Key_2), self, lambda: self._select_tool('freehand'))
        QShortcut(QKeySequence(Qt.Key_3), self, lambda: self._select_tool('rectangle'))
        QShortcut(QKeySequence(Qt.Key_4), self, lambda: self._select_tool('eraser'))
        
        # Undo/Redo
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self._redo)
        
        # Cancel
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._cancel_drawing)
        
        # Clear drawn gas
        QShortcut(QKeySequence(Qt.Key_Delete), self, self._clear_drawn_gas)
        
        # Skip/Review
        QShortcut(QKeySequence(Qt.Key_X), self, self._skip_image)
        QShortcut(QKeySequence(Qt.Key_R), self, self._mark_review)
        
        # Toggle overlay
        QShortcut(QKeySequence(Qt.Key_Space), self, self._toggle_overlay)
    
    # =========================================================================
    # FOLDER MANAGEMENT
    # =========================================================================
    
    def _browse_images_folder(self):
        """Open folder browser for images."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Images Folder",
            self.session.images_folder or str(Path.home())
        )
        if folder:
            self.session.images_folder = folder
            self.images_path_label.setText(folder)
            self.images_path_label.setStyleSheet("color: #7ee787;")
            self._load_image_list()
    
    def _browse_masks_folder(self):
        """Open folder browser for masks output."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Masks Folder",
            self.session.masks_folder or str(Path.home())
        )
        if folder:
            self.session.masks_folder = folder
            self.masks_path_label.setText(folder)
            self.masks_path_label.setStyleSheet("color: #7ee787;")
            
            # Create folder if doesn't exist
            Path(folder).mkdir(parents=True, exist_ok=True)
            
            # Check for existing session
            self._check_for_session()
            self._update_stats()
    
    def _load_image_list(self, preserve_index: bool = False):
        """Load list of images from folder.
        
        Args:
            preserve_index: If True, keep current_index (for session restore).
                           If False, reset to 0 (for new folder selection).
        """
        if not self.session.images_folder:
            return
        
        folder = Path(self.session.images_folder)
        extensions = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}
        
        self.session.image_list = sorted([
            f.name for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ])
        
        if not preserve_index:
            self.session.current_index = 0
        else:
            # Clamp the preserved index to valid range
            max_index = len(self.session.image_list) - 1 if self.session.image_list else 0
            self.session.current_index = max(0, min(self.session.current_index, max_index))
        
        self._apply_filter()
        self._load_current_image()
        self._update_stats()
    
    def _load_current_image(self):
        """Load and display the current image."""
        if not self.session.image_list or not self.session.images_folder:
            return
        
        # Get filtered list
        filtered_list = self._get_filtered_list()
        if not filtered_list:
            self.canvas.set_image(np.zeros((480, 640), dtype=np.uint8))
            return
        
        # Clamp index
        self.session.current_index = max(0, min(self.session.current_index, len(filtered_list) - 1))
        
        image_name = filtered_list[self.session.current_index]
        image_path = Path(self.session.images_folder) / image_name
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            self.statusBar.showMessage(f"Error loading image: {image_name}")
            return
        
        # Update canvas
        self.canvas.set_image(image)
        
        # Get the syringe version that applies to this image
        # Use original index from full image list, not filtered index
        original_index = self.session.image_list.index(image_name) if image_name in self.session.image_list else 0
        syringe_shapes = self.session.get_syringe_for_index(original_index)
        self.canvas.set_syringe_shapes(syringe_shapes)
        
        # Clear gas and eraser shapes for new image
        self.gas_shapes.clear()
        self.eraser_shapes.clear()
        self.undo_stack.clear()
        self.has_unsaved_changes = False  # Reset change tracking
        self.canvas.set_gas_shapes(self.gas_shapes)
        self.canvas.set_eraser_shapes(self.eraser_shapes)
        
        # Load existing mask if exists and verification mode is on
        self._load_existing_mask(image_name)
        
        # Update UI
        self._update_navigation_ui(image_name, filtered_list)
        self._update_syringe_status()
        self._save_session()
    
    def _load_existing_mask(self, image_name: str):
        """Load existing mask for verification mode."""
        if not self.session.masks_folder:
            self.canvas.set_existing_mask(None)
            self._update_existing_mask_ui(False)
            return
        
        mask_path = Path(self.session.masks_folder) / image_name
        
        if mask_path.exists():
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if self.show_existing_cb.isChecked():
                self.canvas.set_existing_mask(mask)
            else:
                self.canvas.set_existing_mask(None)
            self._update_existing_mask_ui(True, mask)
        else:
            self.canvas.set_existing_mask(None)
            self._update_existing_mask_ui(False)
    
    def _update_existing_mask_ui(self, exists: bool, mask: Optional[np.ndarray] = None):
        """Update the existing mask info UI."""
        if exists and mask is not None:
            gas_pixels = np.sum(mask == 255)
            syringe_pixels = np.sum(mask == 100)
            self.existing_mask_info.setText(f"✓ Found: Gas={gas_pixels}px, Syringe={syringe_pixels}px")
            self.existing_mask_info.setStyleSheet("color: #3fb950; font-size: 16px;")
            self.toggle_existing_btn.setEnabled(True)
            self.toggle_existing_btn.setText("👁️ Hide")
            self._existing_overlay_visible = True
            self.clear_gas_only_btn.setEnabled(gas_pixels > 0)  # Only if has gas
            self.delete_existing_btn.setEnabled(True)
        else:
            # Check if file exists but overlay is cleared
            filtered_list = self._get_filtered_list()
            if filtered_list and self.session.current_index < len(filtered_list):
                image_name = filtered_list[self.session.current_index]
                if self._mask_exists(image_name):
                    self.existing_mask_info.setText("Overlay hidden (file exists)")
                    self.existing_mask_info.setStyleSheet("color: #d29922; font-size: 16px;")
                    self.toggle_existing_btn.setEnabled(True)  # Can toggle to show
                    self.toggle_existing_btn.setText("👁️ Show")
                    self._existing_overlay_visible = False
                    self.clear_gas_only_btn.setEnabled(True)  # Can still clear gas from file
                    self.delete_existing_btn.setEnabled(True)
                else:
                    self.existing_mask_info.setText("No saved mask file")
                    self.existing_mask_info.setStyleSheet("color: #8b949e; font-size: 16px;")
                    self.toggle_existing_btn.setEnabled(False)
                    self.toggle_existing_btn.setText("👁️ Hide")
                    self._existing_overlay_visible = True
                    self.clear_gas_only_btn.setEnabled(False)
                    self.delete_existing_btn.setEnabled(False)
            else:
                self.existing_mask_info.setText("No saved mask file")
                self.existing_mask_info.setStyleSheet("color: #8b949e; font-size: 16px;")
                self.toggle_existing_btn.setEnabled(False)
                self.toggle_existing_btn.setText("👁️ Hide")
                self._existing_overlay_visible = True
                self.clear_gas_only_btn.setEnabled(False)
                self.delete_existing_btn.setEnabled(False)
    
    def _clear_existing_mask(self):
        """Delete the existing mask file for current image."""
        filtered_list = self._get_filtered_list()
        if not filtered_list or not self.session.masks_folder:
            return
        
        image_name = filtered_list[self.session.current_index]
        mask_path = Path(self.session.masks_folder) / image_name
        
        reply = QMessageBox.question(
            self, "Delete Existing Mask",
            f"Delete the existing mask for {image_name}?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes and mask_path.exists():
            mask_path.unlink()
            self.canvas.set_existing_mask(None)
            self._update_existing_mask_ui(False)
            self._update_stats()
            self._update_navigation_ui(image_name, filtered_list)
            self.statusBar.showMessage(f"Deleted: {mask_path}")
    
    def _update_navigation_ui(self, image_name: str, filtered_list: List[str]):
        """Update navigation UI elements."""
        idx = self.session.current_index
        total = len(filtered_list)
        
        self.image_counter_label.setText(f"Image {idx + 1} of {total}")
        self.current_image_label.setText(image_name)
        
        # Update status indicator
        status = ""
        if image_name in self.session.skipped_images:
            status = "  ⏭️ SKIPPED"
            self.status_indicator.setStyleSheet("color: #d29922; font-size: 18px; font-weight: bold;")
        elif image_name in self.session.review_images:
            status = "  🔖 REVIEW"
            self.status_indicator.setStyleSheet("color: #a371f7; font-size: 18px; font-weight: bold;")
        elif self._mask_exists(image_name):
            status = "  ✓ SAVED"
            self.status_indicator.setStyleSheet("color: #3fb950; font-size: 18px; font-weight: bold;")
        else:
            self.status_indicator.setStyleSheet("")
        
        self.status_indicator.setText(status)
        
        # Update button states
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < total - 1)
    
    def _mask_exists(self, image_name: str) -> bool:
        """Check if mask exists for given image."""
        if not self.session.masks_folder:
            return False
        mask_path = Path(self.session.masks_folder) / image_name
        return mask_path.exists()
    
    def _update_stats(self):
        """Update the statistics display."""
        if not self.session.image_list:
            self.stats_label.setText("Done: 0  │  Skipped: 0  │  Review: 0")
            return
        
        done = sum(1 for img in self.session.image_list if self._mask_exists(img))
        skipped = len(self.session.skipped_images)
        review = len(self.session.review_images)
        
        self.stats_label.setText(f"Done: {done}  │  Skipped: {skipped}  │  Review: {review}")
    
    def _get_filtered_list(self) -> List[str]:
        """Get image list based on current filter."""
        if not self.session.image_list:
            return []
        
        filter_idx = self.filter_combo.currentIndex()
        
        if filter_idx == 0:  # All
            return self.session.image_list
        elif filter_idx == 1:  # Not Annotated
            return [img for img in self.session.image_list 
                    if not self._mask_exists(img)]
        elif filter_idx == 2:  # Annotated
            return [img for img in self.session.image_list 
                    if self._mask_exists(img)]
        elif filter_idx == 3:  # Skipped
            return [img for img in self.session.image_list 
                    if img in self.session.skipped_images]
        elif filter_idx == 4:  # Review
            return [img for img in self.session.image_list 
                    if img in self.session.review_images]
        
        return self.session.image_list
    
    def _apply_filter(self):
        """Apply the current filter and reload."""
        self.session.current_index = 0
        self._load_current_image()
    
    # =========================================================================
    # NAVIGATION
    # =========================================================================
    
    def _next_image(self):
        """Go to next image."""
        # Auto-save current mask before navigating (only if user made changes)
        if self.has_unsaved_changes and self.session.masks_folder and self.session.images_folder and self.canvas.original_image is not None:
            self._save_mask(silent=True)
        
        filtered_list = self._get_filtered_list()
        if self.session.current_index < len(filtered_list) - 1:
            self.session.current_index += 1
            self._load_current_image()
    
    def _prev_image(self):
        """Go to previous image."""
        # Auto-save current mask before navigating (only if user made changes)
        if self.has_unsaved_changes and self.session.masks_folder and self.session.images_folder and self.canvas.original_image is not None:
            self._save_mask(silent=True)
        
        if self.session.current_index > 0:
            self.session.current_index -= 1
            self._load_current_image()
    
    # =========================================================================
    # DRAWING
    # =========================================================================
    
    def _toggle_syringe_mode(self):
        """Toggle syringe drawing mode."""
        is_syringe = self.draw_syringe_btn.isChecked()
        self.canvas.set_drawing_mode(is_syringe)
        
        if is_syringe:
            self.statusBar.showMessage("🔵 SYRINGE MODE: Draw polygon, right-click or double-click to complete")
        else:
            self.statusBar.showMessage("🟠 GAS MODE: Draw mask regions")
    
    def _on_tool_changed(self, button):
        """Handle tool selection change."""
        self.is_eraser_mode = False
        
        if button == self.polygon_radio:
            self.canvas.set_tool('polygon')
            self.tool_label.setText("Tool: Polygon")
        elif button == self.freehand_radio:
            self.canvas.set_tool('freehand')
            self.tool_label.setText("Tool: Freehand")
        elif button == self.rectangle_radio:
            self.canvas.set_tool('rectangle')
            self.tool_label.setText("Tool: Rectangle")
        elif button == self.eraser_radio:
            self.canvas.set_tool('freehand')  # Eraser uses freehand drawing
            self.is_eraser_mode = True
            self.tool_label.setText("Tool: Eraser")
            self.tool_label.setStyleSheet("color: #f87171;")
    
    def _select_tool(self, tool: str):
        """Select tool by name."""
        self.is_eraser_mode = False
        self.tool_label.setStyleSheet("color: #fbbf24;")  # Reset to default color
        
        if tool == 'polygon':
            self.polygon_radio.setChecked(True)
        elif tool == 'freehand':
            self.freehand_radio.setChecked(True)
        elif tool == 'rectangle':
            self.rectangle_radio.setChecked(True)
        elif tool == 'eraser':
            self.eraser_radio.setChecked(True)
            self.is_eraser_mode = True
            self.tool_label.setStyleSheet("color: #f87171;")
            self.canvas.set_tool('freehand')  # Eraser uses freehand
            self.tool_label.setText("Tool: Eraser")
            return
            
        self.canvas.set_tool(tool)
        self.tool_label.setText(f"Tool: {tool.capitalize()}")
    
    def _on_shape_completed(self, shape: Shape):
        """Handle completed shape from canvas."""
        if self.canvas.is_drawing_syringe:
            # Get the original index in full image list
            original_index = self._get_original_index()
            
            # Get current syringe shapes for this index (if any) and add to them
            current_shapes = list(self.session.get_syringe_for_index(original_index))
            current_shapes.append(shape)
            
            # Create/update syringe version starting from original index
            self.session.add_syringe_version(original_index, current_shapes)
            self.canvas.set_syringe_shapes(current_shapes)
            self._update_syringe_status()
            self._save_session()
            self.statusBar.showMessage(f"🔵 Syringe shape added (version from image {original_index + 1})")
        else:
            if self.is_eraser_mode:
                # Add to eraser shapes
                self.eraser_shapes.append(shape)
                self.canvas.set_eraser_shapes(self.eraser_shapes)
                self.has_unsaved_changes = True
                self.statusBar.showMessage(f"🔴 Eraser shape added (total: {len(self.eraser_shapes)})")
            else:
                # Add to gas shapes
                self.undo_stack.push(self.gas_shapes)
                self.gas_shapes.append(shape)
                self.canvas.set_gas_shapes(self.gas_shapes)
                self.has_unsaved_changes = True
                self.statusBar.showMessage(f"🟠 Gas shape added (total: {len(self.gas_shapes)})")
    
    def _get_original_index(self) -> int:
        """Get the original index in the full image list for the current image."""
        filtered_list = self._get_filtered_list()
        if filtered_list and self.session.current_index < len(filtered_list):
            image_name = filtered_list[self.session.current_index]
            if image_name in self.session.image_list:
                return self.session.image_list.index(image_name)
        return 0
    
    def _update_syringe_status(self):
        """Update syringe status label."""
        original_index = self._get_original_index()
        current_shapes = self.session.get_syringe_for_index(original_index)
        
        if current_shapes:
            self.syringe_status_label.setText(f"✓ Active: {len(current_shapes)} shape(s)")
            self.syringe_status_label.setStyleSheet("color: #3fb950; font-weight: bold;")
        else:
            self.syringe_status_label.setText("⚠ No syringe for this image")
            self.syringe_status_label.setStyleSheet("color: #d29922; font-weight: bold;")
        
        # Show version info
        total_versions = len(self.session.syringe_versions)
        if total_versions > 0:
            # Find which version applies
            applicable_version = None
            for v in self.session.syringe_versions:
                if v.start_index <= original_index:
                    if applicable_version is None or v.start_index > applicable_version.start_index:
                        applicable_version = v
            
            if applicable_version:
                self.syringe_version_label.setText(
                    f"Version from image {applicable_version.start_index + 1} "
                    f"({total_versions} total version(s))"
                )
            else:
                self.syringe_version_label.setText(f"No version applies ({total_versions} defined)")
        else:
            self.syringe_version_label.setText("No versions defined yet")
    
    def _clear_current_syringe(self):
        """Clear the syringe version that applies to the current image."""
        original_index = self._get_original_index()
        current_shapes = self.session.get_syringe_for_index(original_index)
        
        if not current_shapes:
            self.statusBar.showMessage("No syringe version to clear for this image")
            return
        
        reply = QMessageBox.question(
            self, "Clear Syringe Version",
            f"Clear the syringe version that applies to image {original_index + 1}?\n\n"
            "This only affects images using this syringe version.\n"
            "Other versions remain unchanged.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.session.clear_current_syringe(original_index)
            # Reload syringe for current image
            new_shapes = self.session.get_syringe_for_index(original_index)
            self.canvas.set_syringe_shapes(new_shapes)
            self._update_syringe_status()
            self._save_session()
            self.statusBar.showMessage("Syringe version cleared")
    
    def _clear_drawn_gas(self):
        """Clear only the newly drawn gas shapes (not the saved mask file)."""
        if self.gas_shapes:
            self.undo_stack.push(self.gas_shapes)
            self.gas_shapes.clear()
            self.canvas.set_gas_shapes(self.gas_shapes)
            self.statusBar.showMessage("Drawn gas shapes cleared")
        else:
            self.statusBar.showMessage("No drawn gas shapes to clear")
    
    def _clear_eraser(self):
        """Clear eraser shapes."""
        if self.eraser_shapes:
            self.eraser_shapes.clear()
            self.canvas.clear_eraser_shapes()
            self.statusBar.showMessage("Eraser shapes cleared")
        else:
            self.statusBar.showMessage("No eraser shapes to clear")
    
    def _toggle_existing_overlay(self):
        """Toggle the existing mask overlay visibility (doesn't affect the file)."""
        filtered_list = self._get_filtered_list()
        if not filtered_list or not self.session.masks_folder:
            return
        
        image_name = filtered_list[self.session.current_index]
        mask_path = Path(self.session.masks_folder) / image_name
        
        if not mask_path.exists():
            return
        
        if self._existing_overlay_visible:
            # Hide the overlay
            self.canvas.set_existing_mask(None)
            self._existing_overlay_visible = False
            self.toggle_existing_btn.setText("👁️ Show")
            self.statusBar.showMessage("Existing mask overlay hidden (file still exists)")
        else:
            # Show the overlay
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is not None:
                self.canvas.set_existing_mask(mask)
            self._existing_overlay_visible = True
            self.toggle_existing_btn.setText("👁️ Hide")
            self.statusBar.showMessage("Existing mask overlay shown")
    
    def _clear_gas_from_file(self):
        """Remove only gas pixels from the saved mask file, keeping syringe."""
        filtered_list = self._get_filtered_list()
        if not filtered_list or not self.session.masks_folder:
            return
        
        image_name = filtered_list[self.session.current_index]
        mask_path = Path(self.session.masks_folder) / image_name
        
        if not mask_path.exists():
            self.statusBar.showMessage("No mask file to modify")
            return
        
        reply = QMessageBox.question(
            self, "Clear Gas from File",
            f"Remove gas regions from saved mask file?\n\n"
            f"File: {image_name}\n\n"
            "Syringe regions will be kept.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Load existing mask
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is not None:
                # Set gas pixels (255) to background (0), keep syringe (100)
                mask[mask == 255] = 0
                # Save modified mask
                cv2.imwrite(str(mask_path), mask)
                
                # Reload the mask display
                self._load_existing_mask(image_name)
                self.statusBar.showMessage(f"Gas cleared from {image_name} (syringe kept)")
    
    def _delete_existing_mask(self):
        """Delete the existing mask file for current image."""
        filtered_list = self._get_filtered_list()
        if not filtered_list or not self.session.masks_folder:
            return
        
        image_name = filtered_list[self.session.current_index]
        mask_path = Path(self.session.masks_folder) / image_name
        
        reply = QMessageBox.question(
            self, "Delete Mask File",
            f"Permanently delete the mask file for:\n{image_name}?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes and mask_path.exists():
            mask_path.unlink()
            self.canvas.set_existing_mask(None)
            self._update_existing_mask_ui(False)
            self._update_stats()
            self._update_navigation_ui(image_name, filtered_list)
            self.statusBar.showMessage(f"Deleted mask file: {mask_path.name}")
    
    def _cancel_drawing(self):
        """Cancel current drawing operation."""
        self.canvas.cancel_current_drawing()
        self.draw_syringe_btn.setChecked(False)
        self.canvas.set_drawing_mode(False)
        self.statusBar.showMessage("Drawing cancelled")
    
    def _undo(self):
        """Undo last gas shape action."""
        result = self.undo_stack.undo(self.gas_shapes)
        if result is not None:
            self.gas_shapes = result
            self.canvas.set_gas_shapes(self.gas_shapes)
            self.statusBar.showMessage("↩️ Undo")
    
    def _redo(self):
        """Redo last undone action."""
        result = self.undo_stack.redo(self.gas_shapes)
        if result is not None:
            self.gas_shapes = result
            self.canvas.set_gas_shapes(self.gas_shapes)
            self.statusBar.showMessage("↪️ Redo")
    
    # =========================================================================
    # MASK SAVING
    # =========================================================================
    
    def _save_mask(self, silent: bool = False):
        """Save the current mask.
        
        Args:
            silent: If True, skip confirmation dialogs (for auto-save)
        """
        if not self.session.masks_folder or not self.session.images_folder:
            if not silent:
                QMessageBox.warning(self, "Error", "Please select both images and masks folders first.")
            return
        
        if self.canvas.original_image is None:
            return
        
        filtered_list = self._get_filtered_list()
        if not filtered_list:
            return
        
        image_name = filtered_list[self.session.current_index]
        mask_path = Path(self.session.masks_folder) / image_name
        
        # Check if there's an existing mask and no changes were made
        if not silent and mask_path.exists() and not self.has_unsaved_changes:
            # No changes made - just inform user, no need to resave
            self.statusBar.showMessage("No changes to save")
            return
        
        h, w = self.canvas.original_image.shape[:2]
        
        # Start with existing mask if it exists (to preserve existing gas regions)
        if mask_path.exists():
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is None or mask.shape != (h, w):
                mask = np.zeros((h, w), dtype=np.uint8)
        else:
            mask = np.zeros((h, w), dtype=np.uint8)
        
        # Get syringe shapes for this image's index
        # We need to find the original index in the full image list
        original_index = self.session.image_list.index(image_name) if image_name in self.session.image_list else self.session.current_index
        syringe_shapes = self.session.get_syringe_for_index(original_index)
        
        # Draw syringe regions (value 100)
        # Only clear and redraw syringe if we have syringe shapes in the session
        # This preserves existing syringe masks from previous sessions or external sources
        if syringe_shapes:
            # Clear existing syringe regions and redraw from session shapes
            mask[mask == 100] = 0
            for shape in syringe_shapes:
                pts = shape.to_numpy()
                if len(pts) >= 3:
                    cv2.fillPoly(mask, [pts], 100)
        # If no syringe_shapes, preserve existing syringe pixels in the mask file
        
        # Add NEW gas regions (value 255) on top of existing ones
        for shape in self.gas_shapes:
            pts = shape.to_numpy()
            if len(pts) >= 3:
                cv2.fillPoly(mask, [pts], 255)
        
        # Apply eraser shapes (set to 0) - erases gas regions (existing + new)
        for shape in self.eraser_shapes:
            pts = shape.to_numpy()
            if len(pts) >= 3:
                cv2.fillPoly(mask, [pts], 0)
        
        # Save mask
        mask_path = Path(self.session.masks_folder) / image_name
        cv2.imwrite(str(mask_path), mask)
        
        # Remove from skipped/review lists
        self.session.skipped_images.discard(image_name)
        self.session.review_images.discard(image_name)
        
        self._update_stats()
        self._update_navigation_ui(image_name, filtered_list)
        self._load_existing_mask(image_name)  # Update existing mask display
        self._save_session()
        
        # Reset change tracking
        self.has_unsaved_changes = False
        
        self.statusBar.showMessage(f"💾 Saved: {mask_path}")
    
    def _save_and_next(self):
        """Save mask and go to next image."""
        self._save_mask()
        self._next_image()
    
    # =========================================================================
    # SKIP / REVIEW
    # =========================================================================
    
    def _skip_image(self):
        """Skip current image."""
        filtered_list = self._get_filtered_list()
        if not filtered_list:
            return
        
        image_name = filtered_list[self.session.current_index]
        self.session.skipped_images.add(image_name)
        self.session.review_images.discard(image_name)
        
        self._update_stats()
        self._update_navigation_ui(image_name, filtered_list)
        self._save_session()
        self._next_image()
    
    def _mark_review(self):
        """Mark current image for review."""
        filtered_list = self._get_filtered_list()
        if not filtered_list:
            return
        
        image_name = filtered_list[self.session.current_index]
        self.session.review_images.add(image_name)
        self.session.skipped_images.discard(image_name)
        
        self._update_stats()
        self._update_navigation_ui(image_name, filtered_list)
        self._save_session()
        self._next_image()
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def _get_session_path(self) -> Optional[Path]:
        """Get path to session file."""
        if not self.session.masks_folder:
            return None
        return Path(self.session.masks_folder) / "session.json"
    
    def _save_session(self):
        """Save session state to JSON file."""
        session_path = self._get_session_path()
        if session_path is None:
            return
        
        try:
            with open(session_path, 'w') as f:
                json.dump(self.session.to_dict(), f, indent=2)
            self.session_status_label.setText("Session: ✓ Saved")
            self.session_status_label.setStyleSheet("color: #3fb950;")
        except Exception as e:
            self.session_status_label.setText("Session: ✗ Error")
            self.session_status_label.setStyleSheet("color: #f85149;")
            print(f"Error saving session: {e}")
    
    def _load_session(self, session_path: Path):
        """Load session from JSON file."""
        try:
            with open(session_path, 'r') as f:
                data = json.load(f)
            
            self.session = AnnotationSession.from_dict(data)
            
            # Update UI
            if self.session.images_folder:
                self.images_path_label.setText(self.session.images_folder)
                self.images_path_label.setStyleSheet("color: #7ee787;")
            
            if self.session.masks_folder:
                self.masks_path_label.setText(self.session.masks_folder)
                self.masks_path_label.setStyleSheet("color: #7ee787;")
            
            self._update_syringe_status()
            self._load_image_list(preserve_index=True)  # Keep saved position
            
            self.session_status_label.setText("Session: ✓ Loaded")
            self.session_status_label.setStyleSheet("color: #3fb950;")
            self.statusBar.showMessage("✓ Session restored successfully")
            
        except Exception as e:
            print(f"Error loading session: {e}")
            self.statusBar.showMessage(f"Error loading session: {e}")
    
    def _check_for_session(self):
        """Check for existing session file and offer to load it."""
        session_path = self._get_session_path()
        if session_path is None or not session_path.exists():
            return
        
        reply = QMessageBox.question(
            self, "Existing Session Found",
            "A previous session was found. Would you like to restore it?\n\n"
            "This will restore:\n"
            "• Syringe mask\n"
            "• Current position\n"
            "• Skipped/review lists",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._load_session(session_path)
    
    def _new_session(self):
        """Start a new session."""
        reply = QMessageBox.question(
            self, "New Session",
            "Start a new session?\n\n"
            "This will clear:\n"
            "• Syringe mask\n"
            "• Progress tracking\n\n"
            "(Existing mask files will NOT be deleted)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Keep folder paths
            images_folder = self.session.images_folder
            masks_folder = self.session.masks_folder
            
            # Reset session
            self.session = AnnotationSession()
            self.session.images_folder = images_folder
            self.session.masks_folder = masks_folder
            
            self.gas_shapes.clear()
            self.undo_stack.clear()
            
            self._update_syringe_status()
            self._load_image_list()
            self._save_session()
            
            self.statusBar.showMessage("🔄 New session started")
    
    # =========================================================================
    # UI CALLBACKS
    # =========================================================================
    
    def _on_opacity_changed(self, value: int):
        """Handle opacity slider change."""
        self.opacity_label.setText(f"{value}%")
        self.canvas.overlay_opacity = value / 100.0
        self.canvas.update_display()
    
    def _on_overlay_toggled(self, state: int):
        """Handle overlay checkbox toggle."""
        self.canvas.show_overlay = (state == Qt.Checked)
        self.canvas.update_display()
    
    def _on_show_existing_changed(self, state: int):
        """Handle show existing masks checkbox toggle."""
        filtered_list = self._get_filtered_list()
        if filtered_list:
            image_name = filtered_list[self.session.current_index]
            self._load_existing_mask(image_name)
    
    def _toggle_overlay(self):
        """Toggle overlay visibility."""
        self.show_overlay_cb.setChecked(not self.show_overlay_cb.isChecked())
    
    def _on_mouse_moved(self, x: int, y: int):
        """Update coordinate display."""
        if self.canvas.original_image is not None:
            h, w = self.canvas.original_image.shape[:2]
            if 0 <= x < w and 0 <= y < h:
                self.coord_label.setText(f"Pos: ({x}, {y})")
            else:
                self.coord_label.setText("Pos: (—, —)")
        else:
            self.coord_label.setText("Pos: (—, —)")
    
    def closeEvent(self, event):
        """Handle window close - save session."""
        self._save_session()
        event.accept()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Apply custom stylesheet
    app.setStyleSheet(STYLE_SHEET)
    
    window = MethaneAnnotator()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
