# SegLabel

A lightweight desktop tool for drawing precise binary segmentation masks on image datasets.
Built with PyQt5, it supports polygon, freehand, rectangle, and brush tools with full
undo/redo and session persistence.

## Features

- **Multiple drawing tools** — Polygon, freehand, rectangle, and brush
- **Eraser tools** — Brush eraser and polygon eraser to subtract regions
- **Multi-layer masks** — Separate layers for different annotation classes (pixel values 100 and 255)
- **Zoom & pan** — Up to 4× zoom with mouse wheel, pan with Space+drag
- **Undo/redo** — Per-layer undo stacks (Ctrl+Z / Ctrl+Y)
- **Session persistence** — Auto-saves progress to `session.json`, resumable across runs
- **Non-destructive saving** — Merges new annotations with existing masks on disk
- **Dark theme** with dynamic UI scaling for different screen resolutions

## Requirements

- Python 3.8+
- PyQt5 >= 5.15
- numpy >= 1.20
- opencv-python >= 4.5
- pillow >= 8.0

## Installation

```bash
git clone https://github.com/toqitahamid/SegLabel.git
cd SegLabel
pip install -r requirements_annotator.txt
```

## Usage

```bash
python mask_annotator.py
```

1. Open an image folder via **File → Open Images Folder**
2. Choose or create a masks output folder
3. Draw masks using the toolbar or keyboard shortcuts
4. Press **S** to save, or **Ctrl+S** to save and advance to the next image

## Output Format

Masks are saved as grayscale PNG files:

| Pixel value | Meaning |
|-------------|---------|
| `0` | Background / erased region |
| `100` | Secondary layer (persistent across images) |
| `255` | Primary annotation |

## Keyboard Shortcuts

### Drawing Tools
| Key | Action |
|-----|--------|
| `1` | Polygon |
| `2` | Freehand |
| `3` | Rectangle |
| `4` | Polygon eraser |
| `5` | Brush eraser |
| `[` / `]` | Decrease / increase brush size |

### Navigation & Saving
| Key | Action |
|-----|--------|
| `Right` / `D` | Next image |
| `Left` / `A` | Previous image |
| `S` | Save mask |
| `Ctrl+S` | Save & advance |

### View
| Key | Action |
|-----|--------|
| `Space` | Toggle mask overlay |
| `V` | Toggle existing mask overlay |
| `+` / `-` | Overlay opacity |
| Mouse wheel | Zoom |
| `Space` + drag | Pan |

### Editing
| Key | Action |
|-----|--------|
| `Ctrl+Z` / `Ctrl+Y` | Undo / redo |
| `C` | Clear primary shapes |
| `E` | Clear eraser shapes |
| `Q` | Clear primary layer from saved file |

### Secondary Layer
| Key | Action |
|-----|--------|
| `T` | Toggle secondary layer mode |
| `Shift+T` | Extend secondary layer |
| `Shift+Del` | Delete current secondary layer version |

## License

MIT — see [LICENSE](LICENSE) for details.
