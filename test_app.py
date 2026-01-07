"""Test that the app can fully initialize."""
import sys
from PyQt5.QtWidgets import QApplication

# Initialize Qt first (required before creating widgets)
app = QApplication(sys.argv)

# Now test the full import and initialization chain
from mask_annotator import styles
from mask_annotator.main_window import MethaneAnnotator

# Set up styles like main() does
styles.UI_SCALE = styles.get_ui_scale_factor()
app.setStyleSheet(styles.generate_scaled_stylesheet(styles.UI_SCALE))

# Create the main window (this tests all UI setup)
window = MethaneAnnotator()

# Verify key components exist
assert window.canvas is not None, "Canvas not created"
assert window.session is not None, "Session not created"
assert window.undo_stack is not None, "Undo stack not created"
assert window.gas_shapes == [], "Gas shapes not initialized"
assert window.eraser_shapes == [], "Eraser shapes not initialized"

# Verify UI elements
assert window.prev_btn is not None, "Prev button missing"
assert window.next_btn is not None, "Next button missing"
assert window.save_btn is not None, "Save button missing"
assert window.draw_syringe_btn is not None, "Syringe button missing"

# Test that shortcuts were set up (indirectly via button connections)
assert window.polygon_radio.isChecked(), "Default tool not set"

print("All integration tests passed!")
print(f"UI Scale: {styles.UI_SCALE}")
print("Window created successfully - app is ready to run")

# Clean up without showing
window.close()
app.quit()
