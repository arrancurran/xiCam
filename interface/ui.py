"""
Main UI module that defines the application window and custom widgets.
Handles layout, controls, and image display components using PyQt6.
Provides ROI drawing capabilities and histogram visualization.
"""

from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QSlider, QHBoxLayout, QSizePolicy, QSpinBox, QGroupBox, QVBoxLayout, QFormLayout, QToolBar, QStatusBar, QPushButton
from PyQt6.QtGui import QAction, QPainter
from PyQt6.QtCore import Qt
import qtawesome as qta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import json, os

class ImageLabel(QLabel):
    """
    Custom QLabel subclass for handling ROI drawing interactions.
    Manages mouse events and painting for region of interest selection.
    
    Called by:
    - interface/ui.py: Main UI creates ImageLabel for camera display
    - interface/ui_methods.py: UIMethods handles the mouse/paint events
    
    Example usage:
        image_container = ImageLabel()
        image_container.ui_methods = ui_methods  # Connect UI methods
        image_container.setPixmap(camera_frame)  # Display camera frame
        # ROI drawing handled automatically via mouse events
    """

    #    TODO: Should we move this to ui_methods?
    def __init__(self, parent=None):
        
        """Initialize the ImageLabel"""
        super().__init__(parent)
        self.setMouseTracking(True)
        self.ui_methods = None

    def mousePressEvent(self, event):
        
        """Handle mouse press events"""
        if self.ui_methods:
            self.ui_methods.handle_mouse_press(event)

    def mouseMoveEvent(self, event):
        
        """Handle mouse move events"""
        if self.ui_methods:
            self.ui_methods.handle_mouse_move(event)

    def mouseReleaseEvent(self, event):
        
        """Handle mouse release events"""
        if self.ui_methods:
            self.ui_methods.handle_mouse_release(event)

    def paintEvent(self, event):
        
        """Handle paint events"""
        super().paintEvent(event)
        if self.ui_methods:
            painter = QPainter(self)
            self.ui_methods.handle_paint(painter)
            painter.end()

class ui(QMainWindow):
    """
    Main application window class that manages the UI components.
    Handles UI initialization, status bar management, and UI customization.
    
    Called by:
    - app.py: Main application creates the ui instance
    - interface/ui_methods.py: UIMethods manages UI interactions
    """
    def __init__(self):
        
        """Initialize the main window"""
        super().__init__()
        self.ui_scaffolding = self.load_json('ui_scaffolding.json')
        
        """Initialize status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        """Create status bar labels"""
        for label_name, label_text in self.ui_scaffolding['status_bar']['labels'].items():
            label = QLabel()
            setattr(self, f"{label_name}_label", label)
            self.status_bar.addWidget(label)
            label.setText(label_text)
            
        """Build the rest of the UI"""
        self.build_ui()
        # self.apply_styles()  # Apply styling after UI is built

    def load_json(self, file_path):
        
        """Load settings from ui_settings.json"""
        with open(os.path.join('interface', file_path), 'r') as f:
            return json.load(f)

    # def apply_styles(self):
        
    #     """Apply styles to the UI"""
    #     with open(os.path.join('interface', "style.css"), "r") as f:
    #         self.setStyleSheet(f.read())
    
    def build_ui(self):
        
        """Main Window"""
        MainWindow_widget = QWidget(self)
        self.setCentralWidget(MainWindow_widget)
        MainWindow_layout = QHBoxLayout(MainWindow_widget)
        
        """Controls Container"""
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)

        """Camera Image Container"""
        self.image_container = ImageLabel(self)
        image_scaffolding = self.ui_scaffolding['image_display']
        self.image_container.setMinimumSize(image_scaffolding['min_width'], image_scaffolding['min_height'])
        self.image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        """ROI Group Box"""
        roi_group = QGroupBox("Region of Interest")
        roi_layout = QVBoxLayout()
        
        """Create a form layout for the ROI inputs"""
        roi_form_layout = QFormLayout()
        
        self.roi_width = QSpinBox()
        self.roi_height = QSpinBox()
        self.roi_offset_x = QSpinBox()
        self.roi_offset_y = QSpinBox()
        
        """Set fixed width for ROI inputs"""
        roi_input_width = self.ui_scaffolding['roi']['input_width']
        for spinbox in [self.roi_width, self.roi_height, self.roi_offset_x, self.roi_offset_y]:
            spinbox.setFixedWidth(roi_input_width)
        
        """Add ROI Controls to Form Layout"""
        roi_form_layout.addRow("Width:", self.roi_width)
        roi_form_layout.addRow("Height:", self.roi_height)
        roi_form_layout.addRow("Offset X:", self.roi_offset_x)
        roi_form_layout.addRow("Offset Y:", self.roi_offset_y)
        
        """Add the form layout to the main ROI layout"""
        roi_layout.addLayout(roi_form_layout)
        
        """Add buttons below ROI controls"""
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.apply_roi_button = QPushButton("Apply ROI")
        self.apply_roi_button.setFixedWidth(200)
        button_layout.addWidget(self.apply_roi_button)
        
        self.reset_roi_button = QPushButton("Reset ROI")
        self.reset_roi_button.setFixedWidth(200)
        button_layout.addWidget(self.reset_roi_button)
        
        """Add the button container to the ROI layout"""
        roi_layout.addWidget(button_container)
        
        roi_group.setLayout(roi_layout)
        
        """Right Column"""
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        
        """Histogram"""
        self.hist_figure = plt.figure()
        self.hist_display = FigureCanvas(self.hist_figure)
        self.hist_display.setFixedSize(512, 120)
        
        """Exposure Slider"""
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_label = QLabel()
        self.exposure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        """Add Widgets to Right Column"""
        right_layout.addWidget(self.hist_display)
        right_layout.addWidget(self.exposure_slider)
        right_layout.addWidget(self.exposure_label)
        right_layout.addStretch()
        
        """Set Size Policies"""
        self.image_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        roi_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        right_column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        """Add Columns to Controls Layout"""
        controls_layout.addWidget(roi_group)
        controls_layout.addWidget(right_column)
        
        """Add Sections to Main Layout with Proper Ratios"""
        MainWindow_layout.addWidget(self.image_container, 2)
        MainWindow_layout.addWidget(controls_container, 1)
        
        """Toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        """Add toolbar actions"""
        for action_name, action_data in self.ui_scaffolding['toolbar']['icons'].items():
            action_obj = QAction(qta.icon(action_data['icon']), action_name, self)
            action_obj.setToolTip(action_data['tooltip'])
            toolbar.addAction(action_obj)
            setattr(self, action_data['cmd'], action_obj)