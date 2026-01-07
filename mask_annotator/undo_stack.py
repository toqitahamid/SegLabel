"""
Undo/Redo system for shape operations.
"""

from typing import List, Optional

from .data_models import Shape


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
