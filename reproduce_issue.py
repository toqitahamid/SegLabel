
import sys
import unittest
from PyQt5.QtWidgets import QApplication
from mask_annotator.main_window import MethaneAnnotator

class TestSyringeMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create app if needed
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.window = MethaneAnnotator()
        
    def test_syringe_tool_selection_does_not_enable_mode(self):
        # Initial state
        self.assertFalse(self.window.canvas.is_drawing_syringe, "Should start in Gas mode")
        
        # Click Syringe Polygon Radio Button
        print("\nClicking Syringe Polygon Radio Button...")
        self.window.syringe_polygon_radio.click()
        
        # Check if mode changed
        self.assertFalse(self.window.canvas.is_drawing_syringe, 
                        "Selecting Syringe Polygon tool should NOT automatically enable draw mode (based on current code reading)")
        
        # Check status bar message (which might be misleading)
        status_msg = self.window.statusBar.currentMessage()
        print(f"Status Bar says: {status_msg}")
        # Expecting something like "🔵 Syringe tool: Polygon" despite beig in Gas mode (Orange)
        
    def test_draw_button_enables_mode(self):
        # Click Draw New Syringe
        print("\nClicking Draw New Syringe Button...")
        self.window.draw_syringe_btn.click()
        
        self.assertTrue(self.window.canvas.is_drawing_syringe, "Button should enable Syringe mode")
        
if __name__ == '__main__':
    unittest.main()
