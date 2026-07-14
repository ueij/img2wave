import sys
import time
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, QObject, Signal, QRunnable, QThreadPool, QLocale
from PySide6.QtGui import QDoubleValidator, QIcon

from image_processor import get_image_boundaries
from audio_generator import generate_wave_on_base_stereo


class WorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)


class AudioGeneratorWorker(QRunnable):
    def __init__(self, audio_path, image_path, start_sec, end_sec, config):
        super().__init__()
        self.audio_path = audio_path
        self.image_path = image_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.config = config
        self.signals = WorkerSignals()

    def run(self):
        try:
            start_time = time.perf_counter()

            top_env_L, bottom_env_L = get_image_boundaries(
                self.image_path,
                width=self.config["width"],
                height=self.config["height"],
                threshold=self.config["threshold"],
                grayscale_method=self.config["grayscale_method"],
                invert=self.config["invert"]
            )

            top_env_R, bottom_env_R = top_env_L, bottom_env_L
            start_R, end_R = self.start_sec, self.end_sec

            generate_wave_on_base_stereo(
                base_audio_path=self.audio_path,
                top_env_L=top_env_L, bottom_env_L=bottom_env_L, start_L=self.start_sec, end_L=self.end_sec,
                top_env_R=top_env_R, bottom_env_R=bottom_env_R, start_R=start_R, end_R=end_R,
                export_full_song=True,
                link_stereo=True,
                output_path=self.config["output_path"]
            )
            
            elapsed_time = time.perf_counter() - start_time
            print(f"Generation completed in {elapsed_time:.4f} seconds.")

            output_abs_path = str(Path(self.config["output_path"]).resolve())
            result_str = f"{output_abs_path}|{elapsed_time:.4f}"
            self.signals.finished.emit(result_str)

        except Exception as e:
            self.signals.error.emit(str(e))


class ImageToWaveWindow(QMainWindow):
    BG_MAIN = "rgb(24, 24, 24)"
    INPUT_BG = "rgb(36, 36, 36)"
    TEXT_MAIN = "white"
    TEXT_MUTED = "gray"
    TEXT_DISABLED = "gray"
    ACCENT_BLUE = "rgb(74, 164, 234)"
    ACCENT_HOVER = "rgb(100, 180, 240)"
    ACCENT_PRESS = "rgb(42, 136, 200)"
    SECTION_BORDER = "rgb(48, 48, 48)"
    SECTION_BG = "rgba(48, 48, 48, 0.04)"
    BROWSE_BORDER = "rgb(60, 60, 65)"
    BROWSE_HOVER = "rgb(65, 65, 70)"
    DISABLED_BG_DARK = "rgb(28, 28, 28)"
    DISABLED_BG_LIGHT = "rgb(50, 50, 50)"

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()
        self._init_paths()
        self.init_ui()

    def _init_paths(self):
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(sys._MEIPASS)
            self.exe_dir = Path(sys.argv[0]).parent
        else:
            self.app_dir = self.exe_dir = Path(__file__).parent
        
        self.default_output_path = str((self.exe_dir / "output.wav").resolve())
        
        self.default_config = {
            "width": 2048,
            "height": 512,
            "threshold": 128,
            "grayscale_method": "luminance_601",
            "invert": False,
            "output_path": self.default_output_path
        }

    def init_ui(self):
        self.setWindowTitle("img2wave")

        icon_path = self.app_dir / "img2wave.ico"
        self.setWindowIcon(QIcon(str(icon_path)))
        
        container = QWidget()
        self.setCentralWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10) 

        files_layout = QVBoxLayout()
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(10)

        top_row_layout = QHBoxLayout()
        top_row_layout.setContentsMargins(0, 0, 0, 0) 
        top_row_layout.setSpacing(10) 
        
        audio_label, self.audio_path_input, self.audio_browse_button = self._create_file_field(
            "Base Audio:", "No audio selected..."
        )
        
        self.gen_button = QPushButton("Generate Audio")
        self.gen_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_button.setObjectName("GenerateButton") 
        
        top_row_layout.addWidget(audio_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_row_layout.addWidget(self.audio_path_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_row_layout.addWidget(self.audio_browse_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_row_layout.addWidget(self.gen_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        output_row_layout = QHBoxLayout()
        output_row_layout.setContentsMargins(0, 0, 0, 0)
        output_row_layout.setSpacing(10)

        output_label, self.output_path_input, self.output_browse_button = self._create_file_field(
            "Output Path:", "output.wav"
        )
        self.output_path_input.setReadOnly(False)
        self.output_path_input.setText(self.default_config["output_path"])

        output_row_layout.addWidget(output_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        output_row_layout.addWidget(self.output_path_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        output_row_layout.addWidget(self.output_browse_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        files_layout.addLayout(top_row_layout)
        files_layout.addLayout(output_row_layout)
        
        self.top_section = QGroupBox("IMAGE SETTINGS")
        self.top_section.setObjectName("TopSection")

        top_section_layout = QVBoxLayout(self.top_section)
        top_section_layout.setContentsMargins(10, 10, 10, 10) 
        top_section_layout.setSpacing(10) 

        source_row_layout = QHBoxLayout()
        source_row_layout.setContentsMargins(0, 0, 0, 0) 
        source_row_layout.setSpacing(10) 
        
        img_label, self.path_input, self.browse_button = self._create_file_field(
            "Image Source:", "No image selected..."
        )
        
        source_row_layout.addWidget(img_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        source_row_layout.addWidget(self.path_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        source_row_layout.addWidget(self.browse_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        top_section_layout.addLayout(source_row_layout)

        timing_row_layout = QHBoxLayout()
        timing_row_layout.setContentsMargins(0, 0, 0, 0) 
        timing_row_layout.setSpacing(10)
        
        self.timing_text = QLabel("Segment Timing:")
        timing_row_layout.addWidget(self.timing_text, alignment=Qt.AlignmentFlag.AlignVCenter)

        duration_validator = QDoubleValidator(0.0, 999999.0, 6, self)
        duration_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        duration_validator.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

        self.start_input = QLineEdit("2.0")
        self.start_input.setPlaceholderText("Start time (s)")
        self.start_input.setFixedWidth(100)
        self.start_input.setValidator(duration_validator)
        timing_row_layout.addWidget(self.start_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.end_input = QLineEdit("5.0")
        self.end_input.setPlaceholderText("End time (s)")
        self.end_input.setFixedWidth(100)
        self.end_input.setValidator(duration_validator)
        timing_row_layout.addWidget(self.end_input, alignment=Qt.AlignmentFlag.AlignVCenter)

        # --- Add the checkbox here ---
        self.invert_checkbox = QCheckBox("Invert Colors")
        self.invert_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        # Apply the default config state to the UI element
        self.invert_checkbox.setChecked(self.default_config["invert"]) 
        timing_row_layout.addWidget(self.invert_checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)

        timing_row_layout.addStretch()
        top_section_layout.addLayout(timing_row_layout)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.version_label = QLabel("v0.3.2")
        self.version_label.setObjectName("VersionText")
        
        self.author_label = QLabel("ueij")
        self.author_label.setObjectName("AuthorText")
        
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.author_label)

        main_layout.addLayout(files_layout)
        main_layout.addWidget(self.top_section)
        main_layout.addLayout(footer_layout)
        main_layout.addStretch()

        self.setup_connections()
        self.apply_styles()

        self.setMinimumWidth(500)
        hint_height = self.centralWidget().layout().sizeHint().height()
        self.resize(550, hint_height)
        self.setFixedHeight(hint_height)

    def _create_file_field(self, label_text, placeholder):
        label = QLabel(label_text)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setReadOnly(True)
        
        button = QPushButton("Browse...")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setObjectName("BrowseButton")
        
        return label, line_edit, button

    def setup_connections(self):
        self.audio_browse_button.clicked.connect(
            lambda: self._browse_file(
                "Select Base Audio", 
                "Audio Files (*.mp3 *.ogg *.wav);;All Files (*)", 
                self.audio_path_input
            )
        )

        self.output_browse_button.clicked.connect(
            lambda: self._browse_save_file(
                "Select Output Path",
                "WAV Files (*.wav)",
                self.output_path_input
            )
        )

        self.browse_button.clicked.connect(
            lambda: self._browse_file(
                "Select Image Source", 
                "Image Files (*.jpg *.jpeg *.png *.webp);;All Files (*)", 
                self.path_input
            )
        )
        self.gen_button.clicked.connect(self.generate_audio)

    def _browse_file(self, title, filter_str, target_input):
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
        if file_path:
            target_input.setText(str(Path(file_path).resolve())) 

    def _browse_save_file(self, title, filter_str, target_input):
        default_path = target_input.text().strip()
        file_path, _ = QFileDialog.getSaveFileName(self, title, default_path, filter_str)
        if file_path:
            target_input.setText(str(Path(file_path).resolve()))

    def _apply_dialog_style(self, dialog):
        dialog.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.BG_MAIN};
            }}
            QLabel {{
                color: {self.TEXT_MAIN};
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton {{
                background-color: {self.SECTION_BORDER};
                color: {self.TEXT_MAIN};
                border: 1px solid {self.BROWSE_BORDER};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
                min-width: 50px;
            }}
            QPushButton:hover {{
                background-color: {self.BROWSE_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {self.ACCENT_PRESS};
                border-color: transparent;
            }}
        """)

    def show_message(self, title, text, icon_type="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        
        if icon_type == "warning":
            msg.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == "error":
            msg.setIcon(QMessageBox.Icon.Critical)
        else:
            msg.setIcon(QMessageBox.Icon.Information)

        self._apply_dialog_style(msg)
        msg.exec()

    def set_ui_enabled(self, enabled):
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLineEdit, QCheckBox)):
                widget.setEnabled(enabled)
 
    def generate_audio(self):
        audio_path = self.audio_path_input.text().strip()
        image_path = self.path_input.text().strip()
        start_text = self.start_input.text().strip()
        end_text = self.end_input.text().strip()
        output_path = self.output_path_input.text().strip()

        if not audio_path or not Path(audio_path).exists():
            self.show_message("Input Error", "Please select a valid base audio file.", "warning")
            return

        if not image_path or not Path(image_path).exists():
            self.show_message("Input Error", "Please select a valid image source file.", "warning")
            return

        if not output_path:
            self.show_message("Input Error", "Please specify a valid output path.", "warning")
            return

        if not start_text or not end_text:
            self.show_message("Input Error", "The start and end times cannot be left empty.", "warning")
            return

        try:
            start_sec = float(start_text)
            end_sec = float(end_text)
        except ValueError:
            self.show_message("Input Error", "The start and end times must be valid numbers.", "warning")
            return

        if start_sec >= end_sec:
            self.show_message("Input Error", "The start time must be less than the end time.", "warning")
            return

        if Path(output_path).exists():
            msg = QMessageBox(self)
            msg.setWindowTitle("Overwrite Warning")
            msg.setText("The output file already exists. Do you want to overwrite it?")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            self._apply_dialog_style(msg)
            
            reply = msg.exec()
            if reply == QMessageBox.StandardButton.No:
                return

        self.set_ui_enabled(False)

        run_config = self.default_config.copy()
        run_config["output_path"] = output_path
        run_config["invert"] = self.invert_checkbox.isChecked() # <-- Dynamically assign the state here

        worker = AudioGeneratorWorker(
            audio_path, image_path, start_sec, end_sec, run_config
        )
        worker.signals.finished.connect(self.on_generation_success)
        worker.signals.error.connect(self.on_generation_failed)
        
        self.thread_pool.start(worker)

    def on_generation_success(self, result_data):
        self.set_ui_enabled(True)
        file_path, elapsed_time = result_data.split("|")
        self.show_message(
            "Generation Success", 
            f"Audio generation completed in: {elapsed_time} seconds\n\nSaved to:\n{file_path}",
            "info"
        )

    def on_generation_failed(self, error_message):
        self.set_ui_enabled(True)
        self.show_message(
            "Processing Error", 
            f"An error occurred during calculation:\n\n{error_message}", 
            "error"
        )

    def apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{ 
                background-color: {self.BG_MAIN}; 
            }}
            
            QLabel {{
                color: {self.TEXT_MAIN}; 
                font-size: 12px; 
                font-weight: 500;
            }}
            QLabel#VersionText {{
                color: {self.TEXT_MUTED};
                font-size: 12px;
                font-weight: 600;
            }}
            QLabel#AuthorText {{
                color: {self.TEXT_MUTED};
                font-size: 12px;
                font-weight: 500;
                letter-spacing: 2px;
            }}

            QPushButton, QLineEdit {{
                font-size: 12px;
                font-weight: 500;   
                border-radius: 4px;
            }}
            
            QPushButton {{
                padding: 4px 8px;
                border: 1px solid transparent; 
            }}
            
            QLineEdit {{
                padding: 4px 4px;
                background-color: {self.INPUT_BG};
                color: {self.TEXT_MAIN};
                border: 1px solid {self.SECTION_BORDER};
            }}
            QLineEdit:disabled {{
                color: {self.TEXT_DISABLED};
                background-color: {self.DISABLED_BG_DARK};
            }}
            
            QPushButton#GenerateButton {{
                background-color: {self.ACCENT_BLUE};
                color: {self.TEXT_MAIN};
                font-weight: 600;
            }}
            QPushButton#GenerateButton:hover {{
                background-color: {self.ACCENT_HOVER};
            }}
            QPushButton#GenerateButton:pressed {{
                background-color: {self.ACCENT_PRESS};
            }}
            QPushButton#GenerateButton:disabled {{
                background-color: {self.DISABLED_BG_LIGHT};
                color: {self.TEXT_DISABLED};
            }}
            
            QPushButton#BrowseButton {{
                background-color: {self.SECTION_BORDER};
                color: {self.TEXT_MAIN};
                border: 1px solid {self.BROWSE_BORDER};
            }}
            QPushButton#BrowseButton:hover {{
                background-color: {self.BROWSE_HOVER};
            }}
            QPushButton#BrowseButton:disabled {{
                background-color: {self.DISABLED_BG_DARK};
                color: {self.TEXT_DISABLED};
                border: 1px solid transparent;
            }}

            QCheckBox {{
                color: {self.TEXT_MAIN};
                font-size: 12px;
                font-weight: 500;
                margin-left: 4px;
            }}
            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
            }}
            
            QGroupBox#TopSection {{
                font-size: 12px;
                font-weight: 600;
                margin-top: 12px;
                border-radius: 8px;
                border: 1px solid {self.SECTION_BORDER}; 
                background-color: {self.SECTION_BG};
                color: {self.SECTION_BORDER}; 
            }}
            QGroupBox::title {{
                color: {self.TEXT_MUTED};
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 2px;
            }}
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageToWaveWindow()
    window.show()
    sys.exit(app.exec())