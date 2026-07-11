import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from image_processor import get_image_boundaries
from audio_generator import generate_wave_on_base_stereo

class ImageToSoundWindow(QMainWindow):
    BG_MAIN = "rgb(24, 24, 24)"
    ACCENT_BLUE = "rgb(74, 164, 234)"
    ACCENT_HOVER = "rgb(100, 180, 240)"
    ACCENT_PRESS = "rgb(42, 136, 200)"
    SECTION_BORDER = "rgb(48, 48, 48)"
    SECTION_BG = "rgba(48, 48, 48, 0.04)"
    INPUT_BG = "rgb(36, 36, 36)" 

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Image to Sound")
        
        container = QWidget()
        self.setCentralWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10) 

        top_row_layout = QHBoxLayout()
        top_row_layout.setContentsMargins(0, 0, 0, 0) 
        top_row_layout.setSpacing(10) 
        
        self.top_text = QLabel("Base Audio:")
        top_row_layout.addWidget(self.top_text, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.audio_path_input = QLineEdit()
        self.audio_path_input.setPlaceholderText("No audio selected...")
        self.audio_path_input.setReadOnly(True)
        top_row_layout.addWidget(self.audio_path_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.audio_browse_button = QPushButton("Browse...")
        self.audio_browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.audio_browse_button.setObjectName("BrowseButton") 
        top_row_layout.addWidget(self.audio_browse_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.gen_button = QPushButton("Generate Audio")
        self.gen_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_button.setObjectName("GenerateButton") 
        top_row_layout.addWidget(self.gen_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.top_section = QGroupBox("IMAGE SETTINGS")
        self.top_section.setObjectName("TopSection")

        top_section_layout = QVBoxLayout(self.top_section)
        top_section_layout.setContentsMargins(10, 10, 10, 10) 
        top_section_layout.setSpacing(10) 

        source_row_layout = QHBoxLayout()
        source_row_layout.setContentsMargins(0, 0, 0, 0) 
        source_row_layout.setSpacing(10) 
        
        self.img_source_text = QLabel("Image Source:")
        source_row_layout.addWidget(self.img_source_text, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("No image selected...")
        self.path_input.setReadOnly(True) 
        source_row_layout.addWidget(self.path_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setObjectName("BrowseButton") 
        source_row_layout.addWidget(self.browse_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        top_section_layout.addLayout(source_row_layout)

        timing_row_layout = QHBoxLayout()
        timing_row_layout.setContentsMargins(0, 0, 0, 0) 
        timing_row_layout.setSpacing(10)
        
        self.timing_text = QLabel("Segment Timing:")
        timing_row_layout.addWidget(self.timing_text, alignment=Qt.AlignmentFlag.AlignVCenter)
        timing_row_layout.addStretch()

        # Input Validator allowing up to 999999.999999 (6 whole digits, 6 decimals)
        duration_validator = QDoubleValidator(0.0, 999999.0, 6, self)
        duration_validator.setNotation(QDoubleValidator.Notation.StandardNotation)

        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Start (s)")
        self.start_input.setFixedWidth(100)
        self.start_input.setValidator(duration_validator)
        timing_row_layout.addWidget(self.start_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("End (s)")
        self.end_input.setFixedWidth(100)
        self.end_input.setValidator(duration_validator)
        timing_row_layout.addWidget(self.end_input, alignment=Qt.AlignmentFlag.AlignVCenter)

        top_section_layout.addLayout(timing_row_layout)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.version_label = QLabel("v0.2.0")
        self.version_label.setObjectName("FooterText")
        
        self.author_label = QLabel("ueij")
        self.author_label.setObjectName("FooterText")
        
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.author_label)

        main_layout.addLayout(top_row_layout)
        main_layout.addWidget(self.top_section)
        main_layout.addLayout(footer_layout)
        main_layout.addStretch()

        self.setup_connections()
        self.apply_styles()

        self.setMinimumWidth(450)
        hint_height = self.centralWidget().layout().sizeHint().height()
        self.resize(550, hint_height)
        self.setFixedHeight(hint_height)

    def setup_connections(self):
        self.audio_browse_button.clicked.connect(self.browse_audio)
        self.browse_button.clicked.connect(self.browse_image)
        self.gen_button.clicked.connect(self.generate_audio)

    def browse_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Base Audio", "", "Audio Files (*.mp3 *.wav *.ogg)")
        if file_path:
            self.audio_path_input.setText(file_path)

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image Source", "", "Image Files (*.png *.jpg *.jpeg *.webp)")
        if file_path:
            self.path_input.setText(file_path)

    def show_native_message(self, title: str, text: str, icon_type: str = "info"):
        """
        Displays a native OS dialog on Windows using the Win32 API.
        Falls back to a styled PySide QMessageBox on other operating systems.
        """
        if sys.platform == "win32":
            import ctypes
            # Define Windows API flags
            # MB_OK = 0x00000000
            flags = 0x00000000 
            
            if icon_type == "info":
                flags |= 0x00000040  # MB_ICONINFORMATION
            elif icon_type == "warning":
                flags |= 0x00000030  # MB_ICONWARNING
            elif icon_type == "error":
                flags |= 0x00000010  # MB_ICONERROR
                
            hwnd = int(self.winId()) if self else 0
            ctypes.windll.user32.MessageBoxW(hwnd, text, title, flags)
        else:
            # Fallback for macOS / Linux
            msg = QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setText(text)
            if icon_type == "info":
                msg.setIcon(QMessageBox.Icon.Information)
            elif icon_type == "warning":
                msg.setIcon(QMessageBox.Icon.Warning)
            elif icon_type == "error":
                msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()

    def generate_audio(self):
        audio_path = self.audio_path_input.text().strip()
        image_path = self.path_input.text().strip()
        start_text = self.start_input.text().strip()
        end_text = self.end_input.text().strip()

        if not audio_path or not os.path.exists(audio_path):
            self.show_native_message("Input Error", "Please select a valid base audio file first.", "warning")
            return

        if not image_path or not os.path.exists(image_path):
            self.show_native_message("Input Error", "Please select a valid image source file first.", "warning")
            return

        try:
            start_sec = float(start_text) if start_text else 2.0
            end_sec = float(end_text) if end_text else 5.0
        except ValueError:
            self.show_native_message("Input Error", "Start and End times must be valid numbers.", "warning")
            return

        if start_sec >= end_sec:
            self.show_native_message("Input Error", "Start time must be less than end time.", "warning")
            return

        # Defaults for future options
        width = 2048
        height = 512
        threshold = 128
        grayscale_method = "luminance_601"
        invert = False
        output_path = "output.wav"

        try:
            print("Processing image boundaries...")
            top_env_L, bottom_env_L = get_image_boundaries(
                image_path,
                width=width,
                height=height,
                threshold=threshold,
                grayscale_method=grayscale_method,
                invert=invert
            )

            top_env_R, bottom_env_R = top_env_L, bottom_env_L
            start_R, end_R = start_sec, end_sec

            print("Modulating base audio...")
            generate_wave_on_base_stereo(
                base_audio_path=audio_path,
                top_env_L=top_env_L, bottom_env_L=bottom_env_L, start_L=start_sec, end_L=end_sec,
                top_env_R=top_env_R, bottom_env_R=bottom_env_R, start_R=start_R, end_R=end_R,
                export_full_song=True,
                link_stereo=True,
                output_path=output_path
            )

            self.show_native_message(
                "Success", 
                f"Audio generation complete!\n\nSaved to:\n{os.path.abspath(output_path)}", 
                "info"
            )

        except Exception as e:
            self.show_native_message(
                "Processing Error", 
                f"An error occurred during calculation:\n\n{str(e)}", 
                "error"
            )

    def apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{ 
                background-color: {self.BG_MAIN}; 
            }}
            
            QLabel {{
                color: white; 
                font-size: 14px; 
                font-weight: 600;
            }}
            
            QLabel#FooterText {{
                color: grey;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            
            QLineEdit, QPushButton {{
                font-size: 12px;
                font-weight: 600;
                padding: 2px 6px;
                height: 18px;                 
                border-radius: 4px;
                border: 1px solid transparent; 
            }}
            
            QLineEdit {{
                background-color: {self.INPUT_BG};
                color: white;
                border: 1px solid {self.SECTION_BORDER};
            }}
            
            QPushButton#GenerateButton {{
                background-color: {self.ACCENT_BLUE};
                color: white;
                font-weight: 600;
            }}
            QPushButton#GenerateButton:hover {{
                background-color: {self.ACCENT_HOVER};
            }}
            QPushButton#GenerateButton:pressed {{
                background-color: {self.ACCENT_PRESS};
            }}
            
            QPushButton#BrowseButton {{
                background-color: {self.SECTION_BORDER};
                color: white;
                border: 1px solid rgb(60, 60, 65);
            }}
            QPushButton#BrowseButton:hover {{
                background-color: rgb(65, 65, 70);
            }}
            
            QGroupBox#TopSection {{
                font-size: 14px;
                font-weight: 600;
                margin-top: 16px;
                border-radius: 8px;
                border: 1px solid {self.SECTION_BORDER}; 
                background-color: {self.SECTION_BG};
                color: {self.SECTION_BORDER}; 
            }}
            QGroupBox::title {{
                color: gray;
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 4px;
            }}
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageToSoundWindow()
    window.show()
    sys.exit(app.exec())