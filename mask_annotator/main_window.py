"""
Main window for the Methane Mask Annotator application.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QCheckBox, QRadioButton,
    QButtonGroup, QGroupBox, QStatusBar, QComboBox, QSplitter,
    QFrame, QMessageBox, QSizePolicy, QScrollArea, QShortcut
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

from .data_models import Shape, AnnotationSession
from .undo_stack import UndoStack
from .canvas import DrawingCanvas
from . import styles


class MethaneAnnotator(QMainWindow):
    """Main application window for the Methane Mask Annotator."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("METHANE MASK ANNOTATOR")

        # Get screen size for dynamic scaling
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            # Set minimum size to 75% of screen, capped at reasonable values
            min_w = min(max(int(geom.width() * 0.75), 900), 1600)
            min_h = min(max(int(geom.height() * 0.75), 600), 1000)
            self.setMinimumSize(min_w, min_h)
        else:
            self.setMinimumSize(1200, 700)

        # Session state
        self.session = AnnotationSession()
        self.gas_shapes: List[Shape] = []  # Current image's gas shapes
        self.eraser_shapes: List[Shape] = []  # Current image's eraser shapes
        self.undo_stack = UndoStack()  # For gas shapes
        self.eraser_undo_stack = UndoStack()  # For eraser shapes
        self.syringe_undo_stack = UndoStack()  # For syringe shapes
        self.is_eraser_mode = False  # Track if we're in eraser mode
        self.has_unsaved_changes = False  # Track if user made changes to current image
        self._existing_overlay_visible = True  # Track overlay visibility state
        self._mask_backup: Optional[Tuple[str, np.ndarray]] = None  # For undo of clear gas from file

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
        # Scale margins and spacing based on UI scale
        scale = styles.UI_SCALE
        s = lambda v: max(1, int(v * scale))  # Helper for scaling
        main_layout.setContentsMargins(s(6), s(6), s(6), s(6))
        main_layout.setSpacing(s(5))

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
        folder_layout.setSpacing(s(4))

        # Images folder row
        images_row = QHBoxLayout()
        images_label = QLabel("📁 IMAGES:")
        images_label.setStyleSheet(f"font-weight: bold; color: #58a6ff; font-size: {s(11)}px;")
        images_row.addWidget(images_label)
        self.images_path_label = QLabel("Select folder...")
        self.images_path_label.setObjectName("pathLabel")
        self.images_path_label.setStyleSheet("color: #484f58; background: transparent;")
        images_row.addWidget(self.images_path_label, stretch=1)
        self.browse_images_btn = QPushButton("Browse")
        self.browse_images_btn.setFixedWidth(s(80))
        self.browse_images_btn.clicked.connect(self._browse_images_folder)
        images_row.addWidget(self.browse_images_btn)
        folder_layout.addLayout(images_row)

        # Masks folder row
        masks_row = QHBoxLayout()
        masks_label = QLabel("💾 MASKS:")
        masks_label.setStyleSheet(f"font-weight: bold; color: #3fb950; font-size: {s(11)}px;")
        masks_row.addWidget(masks_label)
        self.masks_path_label = QLabel("Select folder...")
        self.masks_path_label.setObjectName("pathLabel")
        self.masks_path_label.setStyleSheet("color: #484f58; background: transparent;")
        masks_row.addWidget(self.masks_path_label, stretch=1)
        self.browse_masks_btn = QPushButton("Browse")
        self.browse_masks_btn.setFixedWidth(s(80))
        self.browse_masks_btn.clicked.connect(self._browse_masks_folder)
        masks_row.addWidget(self.browse_masks_btn)
        folder_layout.addLayout(masks_row)

        main_layout.addWidget(folder_frame)

        # === NAVIGATION BAR ===
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(s(6), s(4), s(6), s(4))
        nav_layout.setSpacing(s(6))

        self.prev_btn = QPushButton("◀ PREV")
        self.prev_btn.setObjectName("navBtn")
        self.prev_btn.setFixedWidth(s(80))
        self.prev_btn.clicked.connect(self._prev_image)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("NEXT ▶")
        self.next_btn.setObjectName("navBtn")
        self.next_btn.setFixedWidth(s(80))
        self.next_btn.clicked.connect(self._next_image)
        nav_layout.addWidget(self.next_btn)

        # Separator
        sep1 = QLabel("│")
        sep1.setStyleSheet(f"color: #30363d; font-size: {s(12)}px;")
        nav_layout.addWidget(sep1)

        self.image_counter_label = QLabel("Image 0 of 0")
        self.image_counter_label.setObjectName("counterLabel")
        nav_layout.addWidget(self.image_counter_label)

        sep2 = QLabel("│")
        sep2.setStyleSheet(f"color: #30363d; font-size: {s(12)}px;")
        nav_layout.addWidget(sep2)

        self.current_image_label = QLabel("")
        self.current_image_label.setObjectName("imageNameLabel")
        nav_layout.addWidget(self.current_image_label)

        self.status_indicator = QLabel("")
        self.status_indicator.setStyleSheet(f"font-size: {s(11)}px; font-weight: bold;")
        nav_layout.addWidget(self.status_indicator)

        nav_layout.addStretch()

        # Filter dropdown
        filter_label = QLabel("FILTER:")
        filter_label.setStyleSheet(f"color: #8b949e; font-weight: bold; font-size: {s(10)}px;")
        nav_layout.addWidget(filter_label)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Not Annotated", "Annotated", "Skipped", "Review"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        nav_layout.addWidget(self.filter_combo)

        sep3 = QLabel("│")
        sep3.setStyleSheet(f"color: #30363d; font-size: {s(12)}px;")
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
        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        content_splitter.addWidget(self.canvas)

        # Tools panel with scroll area - resizable via splitter
        tools_scroll = QScrollArea()
        tools_scroll.setWidgetResizable(True)
        tools_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tools_scroll.setMinimumWidth(s(200))  # Minimum width when dragged smaller
        # No maximum width - allows dragging to expand

        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setContentsMargins(s(4), s(4), s(4), s(4))
        tools_layout.setSpacing(s(6))

        # Syringe mask section
        syringe_group = QGroupBox("SYRINGE MASK")
        syringe_group.setObjectName("syringeGroup")
        syringe_layout = QVBoxLayout(syringe_group)
        syringe_layout.setSpacing(s(5))

        syringe_info = QLabel("Draw syringe mask. New versions apply\nfrom current image forward.")
        syringe_info.setStyleSheet(f"color: #8b949e; font-size: {s(10)}px; line-height: 1.4;")
        syringe_info.setWordWrap(True)
        syringe_layout.addWidget(syringe_info)

        # Syringe drawing tool selection
        syringe_tools_label = QLabel("SYRINGE TOOL:")
        syringe_tools_label.setStyleSheet(f"color: #60a5fa; font-weight: bold; font-size: {s(10)}px; margin-top: {s(2)}px;")
        syringe_layout.addWidget(syringe_tools_label)

        self.syringe_tool_group = QButtonGroup(self)

        self.syringe_polygon_radio = QRadioButton("Polygon")
        self.syringe_polygon_radio.setChecked(True)
        self.syringe_tool_group.addButton(self.syringe_polygon_radio)
        syringe_layout.addWidget(self.syringe_polygon_radio)

        self.syringe_freehand_radio = QRadioButton("Freehand")
        self.syringe_tool_group.addButton(self.syringe_freehand_radio)
        syringe_layout.addWidget(self.syringe_freehand_radio)

        self.syringe_rectangle_radio = QRadioButton("Rectangle")
        self.syringe_tool_group.addButton(self.syringe_rectangle_radio)
        syringe_layout.addWidget(self.syringe_rectangle_radio)

        self.syringe_tool_group.buttonClicked.connect(self._on_syringe_tool_changed)

        # Syringe action buttons
        syringe_actions_label = QLabel("ACTIONS:")
        syringe_actions_label.setStyleSheet(f"color: #60a5fa; font-weight: bold; font-size: {s(10)}px; margin-top: {s(4)}px;")
        syringe_layout.addWidget(syringe_actions_label)

        self.draw_syringe_btn = QPushButton("✏️  Draw New Syringe (from here)")
        self.draw_syringe_btn.setObjectName("syringeBtn")
        self.draw_syringe_btn.setCheckable(True)
        self.draw_syringe_btn.setToolTip("Start fresh syringe mask from this image onward")
        self.draw_syringe_btn.clicked.connect(self._toggle_syringe_mode)
        syringe_layout.addWidget(self.draw_syringe_btn)

        self.extend_syringe_btn = QPushButton("➕  Extend Current Syringe")
        self.extend_syringe_btn.setObjectName("syringeBtn")
        self.extend_syringe_btn.setCheckable(True)
        self.extend_syringe_btn.setToolTip("Add new area to the existing syringe mask")
        self.extend_syringe_btn.clicked.connect(self._toggle_extend_syringe_mode)
        syringe_layout.addWidget(self.extend_syringe_btn)

        self.clear_syringe_btn = QPushButton("🗑️  Clear Current Syringe Version")
        self.clear_syringe_btn.clicked.connect(self._clear_current_syringe)
        syringe_layout.addWidget(self.clear_syringe_btn)

        self.syringe_status_label = QLabel("⚠ Status: Not defined")
        self.syringe_status_label.setObjectName("statusWarning")
        syringe_layout.addWidget(self.syringe_status_label)

        self.syringe_version_label = QLabel("")
        self.syringe_version_label.setStyleSheet(f"color: #8b949e; font-size: {s(9)}px;")
        syringe_layout.addWidget(self.syringe_version_label)

        tools_layout.addWidget(syringe_group)

        # Gas mask section
        gas_group = QGroupBox("GAS MASK")
        gas_group.setObjectName("gasGroup")
        gas_layout = QVBoxLayout(gas_group)
        gas_layout.setSpacing(s(5))

        gas_info = QLabel("Draw gas regions for current image.\nMultiple regions allowed.")
        gas_info.setStyleSheet(f"color: #8b949e; font-size: {s(10)}px; line-height: 1.4;")
        gas_info.setWordWrap(True)
        gas_layout.addWidget(gas_info)

        # Tool selection
        tools_label = QLabel("DRAWING TOOL:")
        tools_label.setStyleSheet(f"color: #fbbf24; font-weight: bold; font-size: {s(10)}px; margin-top: {s(2)}px;")
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
        drawn_label.setStyleSheet(f"color: #fbbf24; font-weight: bold; font-size: {s(10)}px; margin-top: {s(4)}px;")
        gas_layout.addWidget(drawn_label)

        drawn_btns = QHBoxLayout()
        self.clear_drawn_gas_btn = QPushButton("🗑️")
        self.clear_drawn_gas_btn.setToolTip("Clear drawn gas shapes (C)")
        self.clear_drawn_gas_btn.clicked.connect(self._clear_drawn_gas)
        drawn_btns.addWidget(self.clear_drawn_gas_btn)

        self.clear_eraser_btn = QPushButton("🧹")
        self.clear_eraser_btn.setToolTip("Clear eraser shapes (E)")
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
        existing_label.setStyleSheet(f"color: #fbbf24; font-weight: bold; font-size: {s(10)}px; margin-top: {s(4)}px;")
        gas_layout.addWidget(existing_label)

        self.existing_mask_info = QLabel("No existing mask")
        self.existing_mask_info.setStyleSheet(f"color: #8b949e; font-size: {s(10)}px;")
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
        actions_layout.setSpacing(s(5))

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
        settings_layout.setSpacing(s(5))

        opacity_label = QLabel("OVERLAY OPACITY:")
        opacity_label.setStyleSheet(f"color: #a78bfa; font-weight: bold; font-size: {s(10)}px;")
        settings_layout.addWidget(opacity_label)

        opacity_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("50%")
        self.opacity_label.setStyleSheet(f"color: #c9d1d9; font-weight: bold; min-width: {s(25)}px;")
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

        # Zoom controls
        zoom_label = QLabel("ZOOM:")
        zoom_label.setStyleSheet(f"color: #a78bfa; font-weight: bold; font-size: {s(10)}px; margin-top: {s(4)}px;")
        settings_layout.addWidget(zoom_label)

        zoom_row = QHBoxLayout()
        self.zoom_out_btn = QPushButton("➖")
        self.zoom_out_btn.setFixedWidth(s(32))
        self.zoom_out_btn.setToolTip("Zoom Out (Scroll Down)")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        zoom_row.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet(f"color: #c9d1d9; font-weight: bold; min-width: {s(45)}px; text-align: center;")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_row.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("➕")
        self.zoom_in_btn.setFixedWidth(s(32))
        self.zoom_in_btn.setToolTip("Zoom In (Scroll Up)")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_row.addWidget(self.zoom_in_btn)

        self.zoom_reset_btn = QPushButton("🔄")
        self.zoom_reset_btn.setFixedWidth(s(32))
        self.zoom_reset_btn.setToolTip("Reset Zoom (Fit to Window)")
        self.zoom_reset_btn.clicked.connect(self._zoom_reset)
        zoom_row.addWidget(self.zoom_reset_btn)

        zoom_row.addStretch()
        settings_layout.addLayout(zoom_row)

        zoom_hint = QLabel("Use mouse wheel to zoom")
        zoom_hint.setStyleSheet(f"color: #6e7681; font-size: {s(9)}px;")
        settings_layout.addWidget(zoom_hint)

        tools_layout.addWidget(settings_group)

        # Spacer
        tools_layout.addStretch()

        # Session controls
        session_group = QGroupBox("SESSION")
        session_layout = QVBoxLayout(session_group)
        session_layout.setSpacing(s(4))

        self.new_session_btn = QPushButton("🔄  New Session")
        self.new_session_btn.clicked.connect(self._new_session)
        session_layout.addWidget(self.new_session_btn)

        tools_layout.addWidget(session_group)

        # Keyboard shortcuts info
        shortcuts_group = QGroupBox("KEYBOARD SHORTCUTS")
        shortcuts_layout = QVBoxLayout(shortcuts_group)
        shortcuts_layout.setSpacing(1)

        shortcuts = [
            ("←/→ A/D", "Navigate"),
            ("S", "Save"),
            ("Ctrl+S", "Save & Next"),
            ("1/2/3/4", "Tools"),
            ("T", "New syringe"),
            ("Shift+T", "Extend syringe"),
            ("Ctrl+Z/Y", "Undo/Redo"),
            ("C/E", "Clear gas/eraser"),
            ("V", "Toggle mask"),
            ("Q", "Clear gas file"),
            ("+/-", "Opacity"),
            ("Scroll", "Zoom"),
            ("Ctrl+0", "Reset zoom"),
            ("X/R", "Skip/Review"),
            ("Tab", "Toggle overlay"),
            ("Esc", "Cancel"),
        ]

        for key, action in shortcuts:
            row = QHBoxLayout()
            key_label = QLabel(key)
            key_label.setStyleSheet(f"""
                background-color: #21262d;
                color: #58a6ff;
                padding: {s(3)}px {s(5)}px;
                border-radius: {s(2)}px;
                font-family: 'Consolas', monospace;
                font-size: {s(10)}px;
                min-width: {s(60)}px;
            """)
            row.addWidget(key_label)
            action_label = QLabel(action)
            action_label.setStyleSheet(f"color: #8b949e; font-size: {s(10)}px;")
            row.addWidget(action_label)
            row.addStretch()
            shortcuts_layout.addLayout(row)

        tools_layout.addWidget(shortcuts_group)

        tools_scroll.setWidget(tools_widget)
        content_splitter.addWidget(tools_scroll)
        content_splitter.setSizes([s(750), s(300)])

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
        QShortcut(QKeySequence(Qt.Key_C), self, self._clear_drawn_gas)

        # Skip/Review
        QShortcut(QKeySequence(Qt.Key_X), self, self._skip_image)
        QShortcut(QKeySequence(Qt.Key_R), self, self._mark_review)

        # Toggle overlay
        QShortcut(QKeySequence(Qt.Key_Tab), self, self._toggle_overlay)

        # === NEW SHORTCUTS ===

        # Toggle syringe mode
        QShortcut(QKeySequence(Qt.Key_T), self, self._toggle_syringe_shortcut)

        # Toggle extend syringe mode
        QShortcut(QKeySequence("Shift+T"), self, self._toggle_extend_syringe_shortcut)

        # Clear current syringe version
        QShortcut(QKeySequence("Shift+Delete"), self, self._clear_current_syringe)

        # Clear eraser shapes
        QShortcut(QKeySequence(Qt.Key_E), self, self._clear_eraser)

        # Toggle existing mask overlay
        QShortcut(QKeySequence(Qt.Key_V), self, self._toggle_existing_overlay)

        # Clear gas from saved file (keep syringe) - Q is easier than Ctrl+Delete
        QShortcut(QKeySequence(Qt.Key_Q), self, self._clear_gas_from_file)

        # Delete entire mask file
        QShortcut(QKeySequence("Ctrl+Shift+Delete"), self, self._delete_existing_mask)

        # Opacity controls
        QShortcut(QKeySequence(Qt.Key_Plus), self, self._increase_opacity)
        QShortcut(QKeySequence(Qt.Key_Equal), self, self._increase_opacity)  # For keyboards without numpad
        QShortcut(QKeySequence(Qt.Key_Minus), self, self._decrease_opacity)

        # Zoom controls
        QShortcut(QKeySequence("Ctrl++"), self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self, self._zoom_in)  # For keyboards without numpad
        QShortcut(QKeySequence("Ctrl+-"), self, self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self._zoom_reset)

    def _toggle_syringe_shortcut(self):
        """Toggle syringe mode via keyboard shortcut."""
        self.draw_syringe_btn.setChecked(not self.draw_syringe_btn.isChecked())
        self._toggle_syringe_mode()

    def _toggle_extend_syringe_shortcut(self):
        """Toggle extend syringe mode via keyboard shortcut."""
        self.extend_syringe_btn.setChecked(not self.extend_syringe_btn.isChecked())
        self._toggle_extend_syringe_mode()

    def _increase_opacity(self):
        """Increase overlay opacity by 10%."""
        current = self.opacity_slider.value()
        self.opacity_slider.setValue(min(100, current + 10))

    def _decrease_opacity(self):
        """Decrease overlay opacity by 10%."""
        current = self.opacity_slider.value()
        self.opacity_slider.setValue(max(0, current - 10))

    def _zoom_in(self):
        """Zoom in the canvas."""
        self.canvas.zoom_in()

    def _zoom_out(self):
        """Zoom out the canvas."""
        self.canvas.zoom_out()

    def _zoom_reset(self):
        """Reset zoom to fit window."""
        self.canvas.reset_zoom()

    def _on_zoom_changed(self, zoom_level: float):
        """Handle zoom level change from canvas."""
        percentage = int(zoom_level * 100)
        self.zoom_label.setText(f"{percentage}%")

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
        self.eraser_undo_stack.clear()
        self.syringe_undo_stack.clear()
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
        """Toggle syringe drawing mode (creates new version from current image)."""
        is_syringe = self.draw_syringe_btn.isChecked()

        # Mutually exclusive with extend mode
        if is_syringe:
            self.extend_syringe_btn.setChecked(False)

        self.canvas.set_drawing_mode(is_syringe)
        self._apply_syringe_tool()

        if is_syringe:
            tool_name = self._get_syringe_tool_name()
            self.statusBar.showMessage(f"🔵 SYRINGE MODE (New Version): Draw {tool_name}, right-click or double-click to complete")
        else:
            self.statusBar.showMessage("🟠 GAS MODE: Draw mask regions")

    def _toggle_extend_syringe_mode(self):
        """Toggle extend syringe mode (adds to existing syringe mask)."""
        is_extending = self.extend_syringe_btn.isChecked()

        # Check if there's an existing syringe to extend
        if is_extending:
            original_index = self._get_original_index()
            current_shapes = self.session.get_syringe_for_index(original_index)
            
            # Also check if there's a syringe in the saved mask file
            has_syringe_in_file = False
            file_mask = None
            
            if not current_shapes and self.session.masks_folder:
                filtered_list = self._get_filtered_list()
                if filtered_list and self.session.current_index < len(filtered_list):
                    image_name = filtered_list[self.session.current_index]
                    mask_path = Path(self.session.masks_folder) / image_name
                    if mask_path.exists():
                        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
                        if mask is not None and np.any(mask == 100):
                            has_syringe_in_file = True
                            file_mask = mask
            
            if not current_shapes and not has_syringe_in_file:
                QMessageBox.warning(
                    self, "No Syringe to Extend",
                    "There is no existing syringe mask for this image.\n\n"
                    "Use 'Draw New Syringe' first to create one."
                )
                self.extend_syringe_btn.setChecked(False)
                return
            
            # If syringe is only in file (not session), IMPORT it into session
            if not current_shapes and has_syringe_in_file and file_mask is not None:
                try:
                    # Extract syringe pixels (value 100)
                    syringe_mask = np.zeros_like(file_mask)
                    syringe_mask[file_mask == 100] = 255
                    
                    # Find contours
                    contours, _ = cv2.findContours(syringe_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    imported_shapes = []
                    for cnt in contours:
                        # Simplify contour significantly to reduce points
                        epsilon = 0.001 * cv2.arcLength(cnt, True)
                        approx = cv2.approxPolyDP(cnt, epsilon, True)
                        
                        points = [(int(p[0][0]), int(p[0][1])) for p in approx]
                        if len(points) >= 3:
                            imported_shapes.append(Shape(shape_type='polygon', points=points))
                    
                    if imported_shapes:
                        # Add to session
                        self.session.add_syringe_version(original_index, imported_shapes)
                        self.canvas.set_syringe_shapes(imported_shapes)
                        self._save_session()
                        self.statusBar.showMessage(f"✅ Imported {len(imported_shapes)} existing syringe shapes from file into session.")
                    else:
                        self.statusBar.showMessage("⚠ Could not extract shapes from file mask.")
                        
                except Exception as e:
                    print(f"Error importing syringe shapes: {e}")
                    self.statusBar.showMessage("⚠ Error importing syringe shapes from file.")

        # Mutually exclusive with new syringe mode
        if is_extending:
            self.draw_syringe_btn.setChecked(False)

        self.canvas.set_drawing_mode(is_extending)
        self._apply_syringe_tool()

        if is_extending:
            tool_name = self._get_syringe_tool_name()
            self.statusBar.showMessage(f"🔵 EXTEND SYRINGE: Draw {tool_name} to add new area to existing mask")
        else:
            self.statusBar.showMessage("🟠 GAS MODE: Draw mask regions")

    def _on_syringe_tool_changed(self, button):
        """Handle syringe tool selection change."""
        self._apply_syringe_tool()
        
        # Auto-enable syringe mode if not already active
        if not self.draw_syringe_btn.isChecked() and not self.extend_syringe_btn.isChecked():
            # Default to "Draw New Syringe" mode
            self.draw_syringe_btn.setChecked(True)
            self._toggle_syringe_mode()
            
        tool_name = self._get_syringe_tool_name()
        self.statusBar.showMessage(f"🔵 Syringe tool: {tool_name}")

    def _get_syringe_tool_name(self) -> str:
        """Get the name of the currently selected syringe tool."""
        if self.syringe_polygon_radio.isChecked():
            return "Polygon"
        elif self.syringe_freehand_radio.isChecked():
            return "Freehand"
        elif self.syringe_rectangle_radio.isChecked():
            return "Rectangle"
        return "Polygon"

    def _apply_syringe_tool(self):
        """Apply the currently selected syringe tool to the canvas."""
        if self.syringe_polygon_radio.isChecked():
            self.canvas.set_tool('polygon')
        elif self.syringe_freehand_radio.isChecked():
            self.canvas.set_tool('freehand')
        elif self.syringe_rectangle_radio.isChecked():
            self.canvas.set_tool('rectangle')

    def _on_tool_changed(self, button):
        """Handle tool selection change."""
        self.is_eraser_mode = False

        # If drawing syringe, switch back to gas mode automatically
        if self.draw_syringe_btn.isChecked() or self.extend_syringe_btn.isChecked():
            self.draw_syringe_btn.setChecked(False)
            self.extend_syringe_btn.setChecked(False)
            self.canvas.set_drawing_mode(False)
            self.statusBar.showMessage("🟠 GAS MODE: Switched to gas tools")

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

            # Push current state to syringe undo stack before modifying
            self.syringe_undo_stack.push(current_shapes)

            current_shapes.append(shape)

            # Create/update syringe version starting from original index
            self.session.add_syringe_version(original_index, current_shapes)
            self.canvas.set_syringe_shapes(current_shapes)
            self._update_syringe_status()
            self._save_session()
            
            # Auto-turn off syringe drawing mode after completing a shape
            self.draw_syringe_btn.setChecked(False)
            self.extend_syringe_btn.setChecked(False)
            self.canvas.set_drawing_mode(False)
            
            # Auto-save to mask file immediately
            self.has_unsaved_changes = True
            self._save_mask(silent=True)
            
            # Show clear feedback
            self.statusBar.showMessage(f"✅ Syringe shape added and saved! ({len(current_shapes)} total shapes)")
        else:
            if self.is_eraser_mode:
                # Push current state to eraser undo stack before modifying
                self.eraser_undo_stack.push(self.eraser_shapes)
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

        # Load existing mask
        original_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if original_mask is not None:
            # Save backup for undo
            self._mask_backup = (image_name, original_mask.copy())

            # Clear gas (set gas pixels 255 to background 0, keep syringe 100)
            modified_mask = original_mask.copy()
            modified_mask[modified_mask == 255] = 0

            # Save modified mask
            cv2.imwrite(str(mask_path), modified_mask)

            # Reload the mask display
            self._load_existing_mask(image_name)
            self.statusBar.showMessage(f"Gas cleared from {image_name} (Ctrl+Z to undo)")

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
        """Undo last shape action (gas, eraser, or syringe)."""
        # Try gas undo first
        result = self.undo_stack.undo(self.gas_shapes)
        if result is not None:
            self.gas_shapes = result
            self.canvas.set_gas_shapes(self.gas_shapes)
            self.statusBar.showMessage("↩️ Undo gas shape")
            return

        # Try eraser undo
        result = self.eraser_undo_stack.undo(self.eraser_shapes)
        if result is not None:
            self.eraser_shapes = result
            self.canvas.set_eraser_shapes(self.eraser_shapes)
            self.statusBar.showMessage("↩️ Undo eraser shape")
            return

        # Try syringe undo
        original_index = self._get_original_index()
        current_syringe = list(self.session.get_syringe_for_index(original_index))
        result = self.syringe_undo_stack.undo(current_syringe)
        if result is not None:
            self.session.add_syringe_version(original_index, result)
            self.canvas.set_syringe_shapes(result)
            self._update_syringe_status()
            self._save_session()
            self.statusBar.showMessage("↩️ Undo syringe shape")
            return

        # Try mask backup restore (for Q key clear gas undo)
        if self._mask_backup is not None:
            backup_image_name, backup_mask = self._mask_backup
            filtered_list = self._get_filtered_list()
            if filtered_list:
                current_image_name = filtered_list[self.session.current_index]
                if current_image_name == backup_image_name:
                    # Restore the backup mask
                    mask_path = Path(self.session.masks_folder) / backup_image_name
                    cv2.imwrite(str(mask_path), backup_mask)
                    self._mask_backup = None
                    self._load_existing_mask(backup_image_name)
                    self.statusBar.showMessage("↩️ Undo: Restored gas mask")
                    return

        self.statusBar.showMessage("Nothing to undo")

    def _redo(self):
        """Redo last undone action (gas, eraser, or syringe)."""
        # Try gas redo first
        result = self.undo_stack.redo(self.gas_shapes)
        if result is not None:
            self.gas_shapes = result
            self.canvas.set_gas_shapes(self.gas_shapes)
            self.statusBar.showMessage("↪️ Redo gas shape")
            return

        # Try eraser redo
        result = self.eraser_undo_stack.redo(self.eraser_shapes)
        if result is not None:
            self.eraser_shapes = result
            self.canvas.set_eraser_shapes(self.eraser_shapes)
            self.statusBar.showMessage("↪️ Redo eraser shape")
            return

        # Try syringe redo
        original_index = self._get_original_index()
        current_syringe = list(self.session.get_syringe_for_index(original_index))
        result = self.syringe_undo_stack.redo(current_syringe)
        if result is not None:
            self.session.add_syringe_version(original_index, result)
            self.canvas.set_syringe_shapes(result)
            self._update_syringe_status()
            self._save_session()
            self.statusBar.showMessage("↪️ Redo syringe shape")
            return

        self.statusBar.showMessage("Nothing to redo")

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

        # Read session to get timestamp
        try:
            with open(session_path, 'r') as f:
                data = json.load(f)

            last_saved = data.get('last_saved', None)
            if last_saved:
                try:
                    saved_time = datetime.fromisoformat(last_saved)
                    time_str = saved_time.strftime('%Y-%m-%d %H:%M:%S')
                    # Calculate age
                    age = datetime.now() - saved_time
                    if age.days > 0:
                        age_str = f"{age.days} day(s) ago"
                    elif age.seconds >= 3600:
                        age_str = f"{age.seconds // 3600} hour(s) ago"
                    else:
                        age_str = f"{age.seconds // 60} minute(s) ago"
                except Exception:
                    time_str = "Unknown"
                    age_str = ""
            else:
                time_str = "Unknown (old session format)"
                age_str = "possibly very old"

            current_image = data.get('current_index', 0) + 1
            total_skipped = len(data.get('skipped_images', []))
            total_review = len(data.get('review_images', []))

        except Exception:
            time_str = "Unknown"
            age_str = ""
            current_image = 1
            total_skipped = 0
            total_review = 0

        reply = QMessageBox.question(
            self, "Existing Session Found",
            f"A previous session was found.\n\n"
            f"📅 Last saved: {time_str}\n"
            f"⏰ Age: {age_str}\n"
            f"📍 Position: Image {current_image}\n"
            f"⏭️ Skipped: {total_skipped}\n"
            f"🔖 Review: {total_review}\n\n"
            "Would you like to restore this session?",
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

    # Get screen-based scale factor
    styles.UI_SCALE = styles.get_ui_scale_factor()
    print(f"UI Scale Factor: {styles.UI_SCALE} (based on screen resolution)")

    # Apply dynamically scaled stylesheet
    app.setStyleSheet(styles.generate_scaled_stylesheet(styles.UI_SCALE))

    window = MethaneAnnotator()
    window.show()

    sys.exit(app.exec_())
