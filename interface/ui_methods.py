from PyQt6.QtWidgets import QStyle
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtGui import QImage, QPixmap, QPainter
from utils import calc_img_hist, update_status
from .camera_controls.control_manager import CameraControlManager
from acquisitions.snapshot import Snapshot
from acquisitions.record_stream import RecordStream
from .draw_roi import DrawROI
from .status_bar.status_bar_manager import StatusBarManager
import qtawesome as qta
import numpy as np
import time

class UIMethods(QObject):
    
    def __init__(self, window, stream_camera):
        """Initialize UI methods with window and camera objects."""
        super().__init__()
        self.window = window
        # Set reference to ui_methods on window for status bar updates
        self.window.ui_methods = self
        self.stream_camera = stream_camera
        self.camera_control = self.stream_camera.camera_control
        self.snapshot = Snapshot(stream_camera, window)
        self.record_stream = RecordStream(stream_camera, window)
        self.draw_roi = DrawROI()
        
        # Initialize camera controls
        print("Initializing camera controls in UIMethods...")  # Debug print
        self.control_manager = CameraControlManager(self.camera_control, window)
        self.control_manager.initialize_controls()
        
        # Initialize status bar manager
        self.status_bar_manager = StatusBarManager(window, self.camera_control)
        self.status_bar_manager.initialize_items()  # Initialize all status bar items
        
        # Connect the Apply ROI button
        self.window.apply_roi_button.clicked.connect(self.handle_apply_roi)
        # Connect the Reset ROI button
        self.window.reset_roi_button.clicked.connect(self.handle_reset_roi)
        
        # Verify exposure control was initialized
        exposure_control = self.control_manager.get_control('exposure')
        if exposure_control:
            print("Exposure control initialized successfully")
        else:
            print("Warning: Exposure control not initialized")
        self.original_image_size = None

    def handle_mouse_press(self, event):
        """Handle mouse press events for ROI drawing."""
        self.draw_roi.mousePressEvent(event, self.window.image_container)

    def handle_mouse_move(self, event):
        """Handle mouse move events for ROI drawing."""
        self.draw_roi.mouseMoveEvent(event, self.window.image_container)

    def handle_mouse_release(self, event):
        """Handle mouse release events for ROI drawing."""
        self.draw_roi.mouseReleaseEvent(event, self.window.image_container)

    def handle_paint(self, painter):
        """Handle paint events for ROI drawing."""
        self.draw_roi.draw_rectangle(painter, self.window.image_container)
    
    def handle_snapshot(self):
        """Handle snapshot button click."""
        if self.snapshot.save_snapshot():
            # Update status bar to show success
            update_status("Snapshot Saved", duration=2000)
        else:
            # Update status bar to show failure
            update_status("Failed to Save Snapshot", duration=2000)
    
    def handle_recording(self):
        """Handle record button toggle."""
        if not hasattr(self.window.start_recording, 'is_recording'):
            self.window.start_recording.is_recording = False
            
        if not self.window.start_recording.is_recording:
            # Start recording
            if self.record_stream.start_recording():
                self.window.start_recording.is_recording = True
                self.window.start_recording.setIcon(qta.icon("fa5s.stop-circle", color='red'))
            else:
                update_status("Failed to Start Recording", duration=2000)
        else:
            # Stop recording
            self.record_stream.stop_recording()
            self.window.start_recording.is_recording = False
            self.window.start_recording.setIcon(qta.icon("fa5.dot-circle"))
            update_status("Recording Stopped", duration=2000)
    
    def update_ui_image(self):
        """Get the latest frame from the stream and update the UI image display."""
        np_image_data = self.stream_camera.get_latest_frame()
        if np_image_data is None:
            return
        
        # Update the main image display
        height, width = np_image_data.shape
        bytes_per_line = width
        image_data = QImage(np_image_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        image = QPixmap(image_data)
        
        # Get container size
        container_size = self.window.image_container.size()
        
        # Calculate scaling to fit the image while maintaining aspect ratio
        scaled_image = image.scaled(container_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Calculate the offset to center the image
        offset_x = (container_size.width() - scaled_image.width()) // 2
        offset_y = (container_size.height() - scaled_image.height()) // 2
        
        # Calculate the scale factors for both dimensions
        scale_factor_x = scaled_image.width() / width
        scale_factor_y = scaled_image.height() / height
        
        # Update the ROI drawing parameters
        self.draw_roi.update_scale_and_offset(
            scale_factor_x, scale_factor_y, 
            offset_x, offset_y,
            scaled_image.width(), scaled_image.height(),
            width, height
        )
        
        # Create a new pixmap for drawing
        final_image = QPixmap(container_size)
        final_image.fill(Qt.GlobalColor.transparent)
        
        # Draw the scaled image
        painter = QPainter(final_image)
        painter.drawPixmap(offset_x, offset_y, scaled_image)
        
        # Draw the ROI if any
        self.draw_roi.draw_rectangle(painter, self.window.image_container)
        painter.end()
        
        self.window.image_container.setPixmap(final_image)
        self.original_image_size = (width, height)

        # Update the histogram for all ROI sizes
        calc_img_hist(self.window, np_image_data)
    
    def handle_apply_roi(self):
        """Handle Apply ROI button click."""
        if self.draw_roi.current_rect:
            # Get the current rectangle coordinates
            rect = self.draw_roi.current_rect
            x = rect.x()
            y = rect.y()
            width = rect.width()
            height = rect.height()
            
            # Get current ROI offset
            current_offset_x = self.window.roi_offset_x.value()
            current_offset_y = self.window.roi_offset_y.value()
            
            # Add current offset to the new rectangle position
            new_offset_x = current_offset_x + x
            new_offset_y = current_offset_y + y
            
            # Update the ROI spinboxes
            self.window.roi_width.setValue(width)
            self.window.roi_height.setValue(height)
            self.window.roi_offset_x.setValue(new_offset_x)
            self.window.roi_offset_y.setValue(new_offset_y)
            
            # Update status bar
            self.status_bar_manager.update_on_control_change("roi")
            
            # Update status
            update_status("ROI Updated", duration=2000)
        else:
            update_status("No ROI Selected", duration=2000)
    
    def handle_reset_roi(self):
        """Handle Reset ROI button click."""
        try:
            # Update the ROI spinboxes to max values
            self.window.roi_offset_x.setValue(0)
            self.window.roi_offset_y.setValue(0)
            max_width = int(self.camera_control.call_camera_command("width_max", "get"))
            max_height = int(self.camera_control.call_camera_command("height_max", "get"))
            self.window.roi_width.setValue(max_width)
            self.window.roi_height.setValue(max_height)
            
            # Clear the current rectangle
            self.draw_roi.current_rect = None
            self.window.image_container.update()
            
            # Update status bar
            self.status_bar_manager.update_on_control_change("roi")
            
            # Update status
            update_status("ROI Reset to Full Frame", duration=2000)
        except Exception as e:
            print(f"Error resetting ROI: {str(e)}")
            update_status("Failed to Reset ROI", duration=2000)
    
    def cleanup(self):
        """Clean up resources."""
        self.control_manager.cleanup()

