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
"""

from .data_models import Shape, SyringeVersion, AnnotationSession
from .undo_stack import UndoStack
from .canvas import DrawingCanvas
from .main_window import MethaneAnnotator, main

__all__ = [
    'Shape',
    'SyringeVersion',
    'AnnotationSession',
    'UndoStack',
    'DrawingCanvas',
    'MethaneAnnotator',
    'main',
]
