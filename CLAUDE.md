# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Methane Mask Annotator is a PyQt5 desktop application for creating binary masks for methane detection in FLIR thermal images.

## Project Structure

```
tools/
├── mask_annotator.py          # Entry point (thin wrapper)
├── mask_annotator/            # Main package
│   ├── __init__.py            # Package exports
│   ├── canvas.py              # DrawingCanvas widget
│   ├── data_models.py         # Shape, SyringeVersion, AnnotationSession
│   ├── main_window.py         # MethaneAnnotator window + main()
│   ├── undo_stack.py          # UndoStack class
│   └── styles.py              # UI scaling and stylesheet generation
└── requirements_annotator.txt # Dependencies
```

## Running the Application

```bash
python mask_annotator.py
```

Install dependencies:
```bash
pip install -r requirements_annotator.txt
```

## Architecture

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `data_models.py` | Shape, SyringeVersion, AnnotationSession dataclasses |
| `undo_stack.py` | Shape history management (undo/redo) |
| `styles.py` | Dark theme CSS with dynamic screen scaling |
| `canvas.py` | DrawingCanvas widget - renders images and handles mouse |
| `main_window.py` | MethaneAnnotator QMainWindow + application logic |

### Class Hierarchy

```
MethaneAnnotator (QMainWindow) - Main controller
├── DrawingCanvas (QLabel) - Renders images and handles drawing
├── AnnotationSession - Data model for session state
├── UndoStack - Shape history management (3 instances: gas, eraser, syringe)
├── Shape - Individual drawn shape data
└── SyringeVersion - Versioned syringe mask with start index
```

### Data Flow

1. **User Input** → DrawingCanvas emits `shape_completed` signal
2. **MethaneAnnotator** receives signal, updates shapes list and undo stack
3. **Save** → Shapes rendered to grayscale PNG mask (0=empty, 100=syringe, 255=gas)
4. **Session** → Auto-persists to `masks_folder/session.json`

### Three-Layer Shape System

- **Syringe shapes** (value 100): Persistent across images, supports versioning at any index
- **Gas shapes** (value 255): Per-image annotations
- **Eraser shapes** (value 0): Subtracts from gas regions only

## Important Patterns

### Syringe Versioning
Syringe masks can change at any image index. `AnnotationSession.get_syringe_for_index()` returns the applicable version for any image.

### Non-destructive Saving
When saving masks, existing gas regions (value 255) from disk are preserved and merged with new annotations.

### Dynamic UI Scaling
`get_ui_scale_factor()` in `styles.py` returns 0.6-1.4 based on screen resolution. All UI elements scale accordingly.

### Session Auto-Save
Session state persists to JSON automatically. Includes backward compatibility with legacy format.

## Key Keyboard Shortcuts

- **Drawing**: 1 (polygon), 2 (freehand), 3 (rectangle), 4 (eraser), 5 (brush eraser)
- **Brush Size**: [ (decrease), ] (increase)
- **Navigation**: Right/D (next), Left/A (prev)
- **Save**: S (save), Ctrl+S (save & next)
- **Syringe**: T (toggle mode), Shift+T (extend mode)
- **Clear**: C (gas shapes), E (eraser), Q (gas from file), Shift+Del (syringe version)
- **Undo**: Ctrl+Z/Ctrl+Y
- **Overlay**: Space (toggle), V (toggle existing), +/- (opacity)
