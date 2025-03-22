from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import queue
import time

class CameraThread(QThread):
    
    """Signal to emit when a new frame is ready"""
    frame_ready = pyqtSignal(object) 
    
    def __init__(self, camera_control):
        
        """Initialize the camera thread"""
        super().__init__()
        self.camera_control = camera_control
        self.running = True
        self.frame_Hz = 60  # Fixed 60 Hz (1000ms/60 ≈ 16.67ms)

    def run(self):
        
        """Main thread loop"""
        while self.running:
            try:
                """Sleep for the appropriate amount of time to achieve the desired frame rate"""
                time.sleep(1/self.frame_Hz)
                
                """Get image from camera"""
                self.camera_control.get_image()
                image_data = self.camera_control.get_image_data()
                
                if image_data is not None:
                    self.frame_ready.emit(image_data)
                
            except Exception as e:
                print(f"Error in camera thread: {str(e)}")
                time.sleep(0.1)  # Sleep briefly on error to prevent tight loop
    
    def stop(self):
        
        """Stop the thread"""
        self.running = False
        self.wait()

class StreamCamera(QObject):
    
    """Signal to emit when a new frame is ready"""
    frame_ready = pyqtSignal() 
    
    def __init__(self, camera_control):
        
        """Initialize the camera and streaming components."""
        super().__init__()
        self.camera_control = camera_control
        self.camera = None
        self.streaming_queue = queue.Queue(maxsize=1)  # Buffer for frames
        self.camera_thread = None

    def start_stream(self):
        
        """Start capturing frames in a separate thread."""
        if self.camera_thread is None or not self.camera_thread.isRunning():
            self.camera_thread = CameraThread(self.camera_control)
            self.camera_thread.frame_ready.connect(self._handle_frame)
            self.camera_control.start_camera()
            self.camera_thread.start()
            print("StreamCamera.start_stream(): Camera stream started.")

    def _handle_frame(self, image_data):
       
        """Handle a new frame from the camera thread"""
        if not self.streaming_queue.full():
            self.streaming_queue.put(image_data)
            self.frame_ready.emit()

    def stop_stream(self):
        
        """Stop the frame capture thread."""
        try:
            if hasattr(self, 'camera_thread') and self.camera_thread is not None:
                if self.camera_thread.isRunning():
                    self.camera_thread.stop()
                self.camera_thread = None
            print("StreamCamera.stop_stream(): Camera stream stopped.")
            self.camera_control.stop_camera()
        except RuntimeError:
            # Ignore errors if the thread has already been deleted
            pass

    def get_latest_frame(self):
        
        """Retrieve the latest frame from the queue."""
        if not self.streaming_queue.empty():
            return self.streaming_queue.get()
        return None

    def cleanup(self):
        
        """Clean up resources before deletion"""
        self.stop_stream()
        """Clear the queue"""
        while not self.streaming_queue.empty():
            try:
                self.streaming_queue.get_nowait()
            except queue.Empty:
                break