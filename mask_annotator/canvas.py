"""
Drawing canvas widget for the Methane Mask Annotator.
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush, QPolygon

from .data_models import Shape


class DrawingCanvas(QLabel):
    """Custom canvas widget for drawing masks on images."""

    # Signals
    shape_completed = pyqtSignal(Shape)
    mouse_moved = pyqtSignal(int, int)
    zoom_changed = pyqtSignal(float)  # Emits current zoom level
    brush_radius_changed = pyqtSignal(int)  # Emits current brush radius

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

        # Zoom settings
        self.zoom_level = 1.0  # 1.0 = fit to window
        self.min_zoom = 0.25
        self.max_zoom = 4.0
        self.pan_offset = QPoint(0, 0)  # For panning when zoomed
        self.is_panning = False
        self.pan_start = QPoint(0, 0)
        self.is_space_pressed = False
        
        # Set focus policy to accept key events
        self.setFocusPolicy(Qt.StrongFocus)

        # Drawing state
        self.current_tool = "polygon"  # polygon, freehand, rectangle, brush
        self.is_drawing_syringe = False
        self.current_points: List[Tuple[int, int]] = []
        self.is_drawing = False
        self.start_point: Optional[Tuple[int, int]] = None

        # Brush eraser state
        self.brush_radius = 20  # Default brush radius in pixels
        self.min_brush_radius = 5
        self.max_brush_radius = 100
        self.is_brush_eraser = False  # Whether brush eraser mode is active
        self.brush_preview_pos: Optional[Tuple[int, int]] = None  # For cursor preview

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

    def set_brush_eraser(self, enabled: bool):
        """Enable or disable brush eraser mode."""
        self.is_brush_eraser = enabled
        if enabled:
            self.current_tool = 'brush'
        self.cancel_current_drawing()
        self.update()

    def increase_brush_radius(self, amount: int = 5):
        """Increase brush radius."""
        self.brush_radius = min(self.max_brush_radius, self.brush_radius + amount)
        self.brush_radius_changed.emit(self.brush_radius)
        self.update()

    def decrease_brush_radius(self, amount: int = 5):
        """Decrease brush radius."""
        self.brush_radius = max(self.min_brush_radius, self.brush_radius - amount)
        self.brush_radius_changed.emit(self.brush_radius)
        self.update()

    def cancel_current_drawing(self):
        """Cancel any ongoing drawing operation."""
        self.current_points.clear()
        self.is_drawing = False
        self.start_point = None
        self.update_display()

    def zoom_in(self):
        """Zoom in by 25%."""
        self.set_zoom(self.zoom_level * 1.25)

    def zoom_out(self):
        """Zoom out by 25%."""
        self.set_zoom(self.zoom_level / 1.25)

    def reset_zoom(self):
        """Reset zoom to fit window."""
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.zoom_changed.emit(self.zoom_level)
        self.update_display()

    def set_zoom(self, level: float):
        """Set zoom level."""
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, level))
        
        # Adjust pan offset to keep center in view
        if old_zoom != self.zoom_level:
            ratio = self.zoom_level / old_zoom
            center_x = self.width() // 2
            center_y = self.height() // 2
            self.pan_offset = QPoint(
                int((self.pan_offset.x() - center_x) * ratio + center_x),
                int((self.pan_offset.y() - center_y) * ratio + center_y)
            )
        
        self.zoom_changed.emit(self.zoom_level)
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
                overlay[syringe_region] = [246, 130, 59]  # Blue (BGR)

                # Gas regions (value 255) - Amber/Orange
                gas_region = (self.existing_mask == 255)
                overlay[gas_region] = [11, 158, 245]  # Amber (BGR)

            # Draw syringe shapes - Blue
            for shape in self.syringe_shapes:
                pts = shape.to_numpy()
                if len(pts) >= 3:
                    cv2.fillPoly(overlay, [pts], (246, 130, 59))

            # Draw gas shapes - Amber
            for shape in self.gas_shapes:
                pts = shape.to_numpy()
                if len(pts) >= 3:
                    cv2.fillPoly(overlay, [pts], (11, 158, 245))
                elif shape.shape_type == 'rectangle' and len(pts) == 2:
                    cv2.rectangle(overlay, tuple(pts[0]), tuple(pts[1]), (11, 158, 245), -1)

            # Draw eraser shapes - Dark red/maroon (shows as "erased" areas)
            for shape in self.eraser_shapes:
                if shape.shape_type == 'brush' and shape.radius is not None:
                    # Draw brush strokes as circles at each point
                    for pt in shape.points:
                        cv2.circle(overlay, pt, shape.radius, (40, 40, 80), -1)
                else:
                    pts = shape.to_numpy()
                    if len(pts) >= 3:
                        cv2.fillPoly(overlay, [pts], (40, 40, 80))  # Dark color to show erasure

            # Blend overlay
            alpha = self.overlay_opacity
            display = cv2.addWeighted(overlay, alpha, display, 1 - alpha, 0)

        # Scale to fit widget, then apply zoom
        widget_w, widget_h = self.width(), self.height()
        scale_w = widget_w / w
        scale_h = widget_h / h
        base_scale = min(scale_w, scale_h)
        self.scale_factor = base_scale * self.zoom_level

        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)

        # Center the image, then apply pan offset
        center_offset = QPoint((widget_w - new_w) // 2, (widget_h - new_h) // 2)
        self.offset = center_offset + self.pan_offset

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
            print(f"[DEBUG] paintEvent: Drawing {len(self.current_points)} points, tool={self.current_tool}, syringe={self.is_drawing_syringe}")
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

        # Draw current brush stroke being drawn
        elif self.current_tool == 'brush' and self.is_drawing and len(self.current_points) > 0:
            eraser_pen = QPen(QColor(248, 113, 113, 200), 2)
            eraser_brush = QBrush(QColor(248, 113, 113, 60))
            painter.setPen(eraser_pen)
            painter.setBrush(eraser_brush)
            scaled_radius = int(self.brush_radius * self.scale_factor)
            for pt in self.current_points:
                widget_pt = self.image_to_widget_coords(pt[0], pt[1])
                painter.drawEllipse(widget_pt, scaled_radius, scaled_radius)

        # Draw brush cursor preview (dashed red circle)
        if self.current_tool == 'brush' and self.is_brush_eraser and self.brush_preview_pos is not None:
            preview_pen = QPen(QColor(248, 113, 113, 220), 2, Qt.DashLine)
            painter.setPen(preview_pen)
            painter.setBrush(Qt.NoBrush)
            scaled_radius = int(self.brush_radius * self.scale_factor)
            widget_pt = self.image_to_widget_coords(self.brush_preview_pos[0], self.brush_preview_pos[1])
            painter.drawEllipse(widget_pt, scaled_radius, scaled_radius)

        painter.end()

    def mousePressEvent(self, event):
        """Handle mouse press for drawing and panning."""
        self.setFocus()  # Ensure we have focus for key events

        if self.original_image is None:
            print(f"[DEBUG] mousePressEvent: No image loaded")
            return

        pos = event.pos()

        # Panning logic (Space + Left Click OR Middle Click)
        if (self.is_space_pressed and event.button() == Qt.LeftButton) or event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.pan_start = pos
            if self.is_space_pressed:
                self.setCursor(Qt.ClosedHandCursor)
            return

        img_x, img_y = self.widget_to_image_coords(pos)

        if not self.is_valid_image_coord(img_x, img_y):
            print(f"[DEBUG] mousePressEvent: Invalid coords ({img_x}, {img_y}), image size: {self.original_image.shape[:2]}")
            return

        print(f"[DEBUG] mousePressEvent: tool={self.current_tool}, syringe_mode={self.is_drawing_syringe}, coords=({img_x}, {img_y})")

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

            elif self.current_tool == 'brush':
                self.is_drawing = True
                self.current_points = [(img_x, img_y)]
                self.update()

        elif event.button() == Qt.RightButton:
            # Complete current shape
            self._complete_shape()

    def mouseMoveEvent(self, event):
        """Handle mouse move for drawing, panning, and coordinates display."""
        pos = event.pos()
        img_x, img_y = self.widget_to_image_coords(pos)

        self.mouse_moved.emit(img_x, img_y)

        if self.original_image is None:
            return

        # Update brush preview position
        if self.current_tool == 'brush' and self.is_brush_eraser:
            if self.is_valid_image_coord(img_x, img_y):
                self.brush_preview_pos = (img_x, img_y)
            else:
                self.brush_preview_pos = None
            self.update()

        # Panning Update
        if self.is_panning:
            delta = pos - self.pan_start
            self.pan_offset += delta
            self.pan_start = pos
            self.update_display()
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

                elif self.current_tool == 'brush':
                    # Add point with spacing based on radius for smooth brush stroke
                    if len(self.current_points) > 0:
                        last_x, last_y = self.current_points[-1]
                        dist = ((img_x - last_x) ** 2 + (img_y - last_y) ** 2) ** 0.5
                        # Spacing is fraction of radius for smooth coverage
                        spacing = max(2, self.brush_radius // 3)
                        if dist >= spacing:
                            self.current_points.append((img_x, img_y))
                    else:
                        self.current_points.append((img_x, img_y))
                    self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        # End Panning
        if self.is_panning:
            if (self.is_space_pressed and event.button() == Qt.LeftButton) or event.button() == Qt.MiddleButton:
                self.is_panning = False
                if self.is_space_pressed:
                    self.setCursor(Qt.OpenHandCursor)
                return

        if event.button() == Qt.LeftButton:
            if self.current_tool == 'freehand' and self.is_drawing:
                self._complete_shape()

            elif self.current_tool == 'rectangle' and self.is_drawing:
                self._complete_shape()

            elif self.current_tool == 'brush' and self.is_drawing:
                self._complete_shape()

    def mouseDoubleClickEvent(self, event):
        """Handle double click to complete polygon."""
        if event.button() == Qt.LeftButton and self.current_tool == 'polygon':
            self._complete_shape()

    def _complete_shape(self):
        """Complete the current shape and emit signal."""
        # Brush shapes only need 1 point minimum
        if self.current_tool == 'brush':
            if len(self.current_points) >= 1:
                shape = Shape(
                    shape_type='brush',
                    points=list(self.current_points),
                    radius=self.brush_radius
                )
                self.shape_completed.emit(shape)
            self.cancel_current_drawing()
            return

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

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if self.original_image is None:
            return

        # Get scroll delta
        delta = event.angleDelta().y()
        
        if delta > 0:
            # Zoom in
            self.set_zoom(self.zoom_level * 1.1)
        elif delta < 0:
            # Zoom out
            self.set_zoom(self.zoom_level / 1.1)

    def enterEvent(self, event):
        """Set focus to canvas when mouse enters."""
        self.setFocus()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Reset state when mouse leaves."""
        self.is_space_pressed = False
        self.is_panning = False
        self.brush_preview_pos = None  # Clear brush preview
        self.setCursor(Qt.ArrowCursor)
        self.update()
        super().leaveEvent(event)

    def focusOutEvent(self, event):
        """Reset state when focus is lost."""
        self.is_space_pressed = False
        self.is_panning = False
        self.setCursor(Qt.ArrowCursor)
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        """Handle key press for spacebar panning."""
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.is_space_pressed = True
            self.setCursor(Qt.OpenHandCursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release for spacebar panning."""
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.is_space_pressed = False
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
        super().keyReleaseEvent(event)
