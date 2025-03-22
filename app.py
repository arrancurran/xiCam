import sys
from PyQt6.QtWidgets import QApplication
from interface.ui import ui
from interface.ui_methods import UIMethods
from instruments.xicam.cam_methods import CameraControl, CameraSequences
from acquisitions.stream_camera import StreamCamera
from utils.status import set_main_window

class microTool():
    def __init__(self):
        """UI Window"""
        self.app = QApplication(sys.argv)
        self.window = ui()
       
        """Camera Control"""
        self.camera_control = CameraControl()
        self.camera_sequences = CameraSequences(self.camera_control)
        self.camera_sequences.connect_camera()
        self.stream_camera = StreamCamera(self.camera_control)
       
        """UI Methods"""
        # Create UI Methods instance first
        self.ui_methods = UIMethods(self.window, self.stream_camera)
        
        # Connect UI methods to image container
        self.window.image_container.ui_methods = self.ui_methods
        
        # Set up status bar management
        set_main_window(self.window)
        
        # Then connect all signals
        self.window.start_stream.triggered.connect(self.stream_camera.start_stream)
        self.window.stop_stream.triggered.connect(self.stream_camera.stop_stream)
        self.window.snapshot.triggered.connect(self.ui_methods.handle_snapshot)
        self.window.start_recording.triggered.connect(self.ui_methods.handle_recording)
       
        """Connect the stream to update the image display"""
        self.stream_camera.frame_ready.connect(self.ui_methods.update_ui_image)
       
        """Connect the window close event to our cleanup method"""
        self.window.closeEvent = self.cleanup
    
    """Clean up resources before the application closes."""
    def cleanup(self, event):
        try:
            if hasattr(self, 'stream_camera'):
                self.stream_camera.cleanup()
            if hasattr(self, 'camera_sequences'):
                self.camera_sequences.disconnect_camera()
            event.accept()
            print("microTool.cleanup(): Resources cleaned up.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()
    
    def run(self):
        self.window.show()
        sys.exit(self.app.exec())
        
    def __del__(self):
        """Backup cleanup method, but closeEvent handler is the primary cleanup method"""
        try:
            if hasattr(self, 'stream_camera'):
                self.stream_camera.cleanup()
            if hasattr(self, 'camera_sequences'):
                self.camera_sequences.disconnect_camera()
            print("microTool.__del__(): Resources cleaned up.")
        except Exception as e:
            print(f"Error during __del__ cleanup: {e}")

if __name__ == "__main__":
    app = microTool()
    app.run()