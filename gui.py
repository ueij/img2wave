# gui.py

import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGroupBox, QLabel, QPushButton, QLineEdit, QFileDialog, 
    QMessageBox, QCheckBox, QComboBox, QSlider
)
from PySide6.QtCore import Qt, QObject, Signal, QRunnable, QThreadPool, QLocale
from PySide6.QtGui import QDoubleValidator, QIcon, QIntValidator, QImage, QPixmap

from image_processor import get_image_boundaries
from audio_generator import generate_wave


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

            top_env, bottom_env = get_image_boundaries(
                self.image_path,
                width=self.config["width"],
                height=self.config["height"],
                threshold=self.config["threshold"],
                grayscale_method=self.config["grayscale_method"],
                invert=self.config["invert"]
            )

            generate_wave(
                base_audio_path=self.audio_path,
                top_env=top_env,
                bottom_env=bottom_env,
                start_sec=self.start_sec,
                end_sec=self.end_sec,
                export_full=self.config.get("export_full", True),
                output_path=self.config["output_path"],
                smooth=self.config.get("smooth", True),
                normalize=self.config.get("normalize", False)
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
        
        self._cached_original_image = None
        self._cached_image_path = None
        self._cached_width = None
        self._cached_height = None
        self._cached_grayscale_method = None
        self._cached_gray_array = None

        self.PREVIEW_MAX_WIDTH = 280
        self.PREVIEW_MAX_HEIGHT = 160

        self._init_paths()
        self.init_ui()

    def _init_paths(self):
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(sys._MEIPASS)
            self.exe_dir = Path(sys.executable).parent
        else:
            self.app_dir = self.exe_dir = Path(__file__).parent
        
        self.default_output_path = str((self.exe_dir / "output.wav").resolve())
        
        self.default_config = {
            "width": 2048,
            "height": 512,
            "threshold": 128,
            "grayscale_method": "luminance_601",
            "invert": False,
            "smooth": True,
            "normalize": False,
            "export_full": True,
            "output_path": self.default_output_path
        }

    def init_ui(self):
        self.setWindowTitle("img2wave")

        icon_path = self.app_dir / "img2wave.ico"
        self.setWindowIcon(QIcon(str(icon_path)))
        
        container = QWidget()
        self.setCentralWidget(container)
        
        main_layout = self._create_vbox(margins=(10, 10, 10, 10))
        container.setLayout(main_layout)

        base_section_layout = self._create_hbox()
        self.audio_path_input = self._add_file_field(
            base_section_layout,
            "Base Audio:",
            "No audio selected...",
            "Select Base Audio",
            "All Supported Audio (*.aif *.aiff *.flac *.mp3 *.ogg *.wav);;"
            "AIFF Files (*.aif *.aiff);;"
            "FLAC Files (*.flac);;"
            "MP3 Files (*.mp3);;"
            "OGG Files (*.ogg);;"
            "WAV Files (*.wav);;"
            "All Files (*)"
        )

        self.gen_button = QPushButton("Generate Audio")
        self.gen_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_button.setObjectName("GenerateButton") 
        self.gen_button.clicked.connect(self.generate_audio)
        
        base_section_layout.addWidget(self.gen_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        main_layout.addLayout(base_section_layout)

        self.export_section = QGroupBox("EXPORT SETTINGS")
        self.export_section.setObjectName("ExportSection")
        export_section_layout = self._create_vbox(margins=(10, 10, 10, 10))
        self.export_section.setLayout(export_section_layout)

        output_row_layout = self._create_hbox()
        self.output_path_input = self._add_file_field(
            output_row_layout,
            "Output Path:",
            "output.wav",
            "Select Output Path",
            "WAV Files (*.wav)",
            is_save=True
        )
        self.output_path_input.setText(self.default_config["output_path"])

        export_options_layout = self._create_hbox()
        self.normalize_checkbox = self._create_checkbox("Normalize Output", self.default_config["normalize"])
        self.export_full_checkbox = self._create_checkbox("Export Full Song", self.default_config["export_full"])

        export_options_layout.addWidget(self.normalize_checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)
        export_options_layout.addWidget(self.export_full_checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)
        export_options_layout.addStretch()

        export_section_layout.addLayout(output_row_layout)
        export_section_layout.addLayout(export_options_layout)
        main_layout.addWidget(self.export_section)

        settings_container_layout = self._create_hbox()

        self.image_section = QGroupBox("IMAGE SETTINGS")
        self.image_section.setObjectName("ImageSection")
        image_section_layout = self._create_vbox(margins=(10, 10, 10, 10))
        self.image_section.setLayout(image_section_layout)

        source_row_layout = self._create_hbox()
        self.path_input = self._add_file_field(
            source_row_layout,
            "Image Source:",
            "No image selected...",
            "Select Image Source",
            "All Supported Images (*.bmp *.gif *.ico *.jpg *.jpeg *.png *.tif *.tiff *.webp);;"
            "BMP Files (*.bmp);;"
            "GIF Files (*.gif);;"
            "ICO Files (*.ico);;"
            "JPEG Files (*.jpg *.jpeg);;"
            "TIFF Files (*.tif *.tiff);;"
            "PNG Files (*.png);;"
            "WebP Files (*.webp);;"
            "All Files (*)"
        )
        image_section_layout.addLayout(source_row_layout)

        timing_row_layout = self._create_hbox()
        self.timing_text = QLabel("Segment Timing:")
        timing_row_layout.addWidget(self.timing_text, alignment=Qt.AlignmentFlag.AlignVCenter)

        duration_validator = QDoubleValidator(0.0, 999999.0, 6, self)
        duration_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        duration_validator.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

        self.start_input = self._create_input("2.0", "Start time (s)", 100, duration_validator)
        self.end_input = self._create_input("5.0", "End time (s)", 100, duration_validator)

        timing_row_layout.addWidget(self.start_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        timing_row_layout.addWidget(self.end_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        timing_row_layout.addStretch()
        image_section_layout.addLayout(timing_row_layout)

        dimensions_row_layout = self._create_hbox()
        int_validator = QIntValidator(1, 9999, self)

        resolution_label = QLabel("Resolution:")
        self.width_input = self._create_input(str(self.default_config["width"]), "Width (px)", 80, int_validator)
        self.height_input = self._create_input(str(self.default_config["height"]), "Height (px)", 80, int_validator)
        self.smooth_checkbox = self._create_checkbox("Interpolate", self.default_config["smooth"])
        self.invert_checkbox = self._create_checkbox("Invert Colors", self.default_config["invert"])

        dimensions_row_layout.addWidget(resolution_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        dimensions_row_layout.addWidget(self.width_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        dimensions_row_layout.addWidget(self.height_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        dimensions_row_layout.addWidget(self.smooth_checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)
        dimensions_row_layout.addWidget(self.invert_checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)
        dimensions_row_layout.addStretch()
        image_section_layout.addLayout(dimensions_row_layout)

        grayscale_row_layout = self._create_hbox()
        grayscale_label = QLabel("Grayscale Method:")
        self.grayscale_combo = QComboBox()

        grayscale_methods = {
            "luminance_601": "Luma 601",
            "luminance_709": "Luma 709",
            "average": "Average",
            "lightness": "Lightness"
        }
        for internal_key, display_name in grayscale_methods.items():
            self.grayscale_combo.addItem(display_name, internal_key)

        default_index = self.grayscale_combo.findData(self.default_config["grayscale_method"])
        if default_index != -1:
            self.grayscale_combo.setCurrentIndex(default_index)

        threshold_validator = QIntValidator(0, 255, self)
        self.threshold_input = self._create_input(str(self.default_config["threshold"]), "0-255", 50, threshold_validator)
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(self.default_config["threshold"])

        grayscale_row_layout.addWidget(grayscale_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        grayscale_row_layout.addWidget(self.grayscale_combo, alignment=Qt.AlignmentFlag.AlignVCenter)
        grayscale_row_layout.addWidget(QLabel("Threshold:"), alignment=Qt.AlignmentFlag.AlignVCenter)
        grayscale_row_layout.addWidget(self.threshold_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        grayscale_row_layout.addWidget(self.threshold_slider, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        image_section_layout.addLayout(grayscale_row_layout)

        settings_container_layout.addWidget(self.image_section, alignment=Qt.AlignmentFlag.AlignTop)

        self.preview_section = QGroupBox("IMAGE PREVIEW")
        self.preview_section.setObjectName("PreviewSection")
        self.preview_section.setFixedWidth(300)
        self.preview_section.setFixedHeight(220)

        preview_section_layout = self._create_vbox(margins=(10, 10, 10, 10))
        self.preview_section.setLayout(preview_section_layout)

        self.preview_label = QLabel("No image loaded.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"color: {self.TEXT_MUTED}; font-style: italic;")
        preview_section_layout.addWidget(self.preview_label)

        self.aspect_ratio_checkbox = self._create_checkbox("Preview Original Aspect Ratio", True)
        preview_section_layout.addWidget(self.aspect_ratio_checkbox, alignment=Qt.AlignmentFlag.AlignLeft)

        settings_container_layout.addWidget(self.preview_section)

        main_layout.addLayout(settings_container_layout)

        footer_layout = self._create_hbox()
        self.version_label = QLabel("v1.0.0")
        self.version_label.setObjectName("VersionText")
        self.author_label = QLabel("ueij")
        self.author_label.setObjectName("AuthorText")
        
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.author_label)

        main_layout.addLayout(footer_layout)
        main_layout.addStretch()

        self.path_input.textChanged.connect(self.update_preview)
        self.width_input.textChanged.connect(self.update_preview)
        self.height_input.textChanged.connect(self.update_preview)
        self.threshold_input.textChanged.connect(self.update_preview)
        self.grayscale_combo.currentIndexChanged.connect(self.update_preview)
        self.invert_checkbox.stateChanged.connect(self.update_preview)
        self.aspect_ratio_checkbox.stateChanged.connect(self.update_preview)

        self.threshold_slider.valueChanged.connect(self._sync_input_from_slider)
        self.threshold_input.textChanged.connect(self._sync_slider_from_input)

        self.apply_styles()

        self.setMinimumWidth(800)
        hint_height = self.centralWidget().layout().sizeHint().height()
        self.resize(800, hint_height)
        self.setFixedHeight(hint_height)

    def _create_hbox(self, margins=(0, 0, 0, 0), spacing=10):
        layout = QHBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout

    def _create_vbox(self, margins=(0, 0, 0, 0), spacing=10):
        layout = QVBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout

    def _add_file_field(self, layout, label_text, placeholder, browse_title, file_filter, is_save=False):
        label = QLabel(label_text)
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setReadOnly(True)
        
        button = QPushButton("Browse...")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setObjectName("BrowseButton")
        
        if is_save:
            button.clicked.connect(lambda: self._browse_save_file(browse_title, file_filter, line_edit))
        else:
            button.clicked.connect(lambda: self._browse_file(browse_title, file_filter, line_edit))
            
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(line_edit, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        return line_edit

    def _create_input(self, text, placeholder, width, validator=None):
        input_widget = QLineEdit(text)
        input_widget.setPlaceholderText(placeholder)
        input_widget.setFixedWidth(width)
        if validator:
            input_widget.setValidator(validator)
        return input_widget

    def _create_checkbox(self, text, checked_value):
        cb = QCheckBox(text)
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.setChecked(checked_value)
        return cb

    def _browse_file(self, title, filter_str, target_input):
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
        if file_path:
            target_input.setText(str(Path(file_path).resolve())) 

    def _browse_save_file(self, title, filter_str, target_input):
        start_path = target_input.text().strip() or str(self.exe_dir / "output.wav")
        file_path, _ = QFileDialog.getSaveFileName(self, title, start_path, filter_str)
        if file_path:
            target_input.setText(str(Path(file_path).resolve()))

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

        msg.exec()

    def set_ui_enabled(self, enabled):
        self.centralWidget().setEnabled(enabled)

    def _sync_input_from_slider(self, val):
        self.threshold_input.blockSignals(True)
        self.threshold_input.setText(str(val))
        self.threshold_input.blockSignals(False)
        self.update_preview()

    def _sync_slider_from_input(self, text):
        try:
            val = int(text.strip())
            if 0 <= val <= 255:
                self.threshold_slider.blockSignals(True)
                self.threshold_slider.setValue(val)
                self.threshold_slider.blockSignals(False)
        except ValueError:
            pass

    @staticmethod
    def _parse_num(text, cast_type, name):
        clean_text = text.strip()
        if not clean_text:
            raise ValueError(f"The {name} cannot be empty.")
        try:
            return cast_type(clean_text)
        except ValueError:
            type_name = "integer" if cast_type is int else "number"
            raise ValueError(f"The {name} must be a valid {type_name}.")
 
    def _parse_and_validate_inputs(self):
        try:
            audio_path = self.audio_path_input.text().strip()
            image_path = self.path_input.text().strip()
            output_path = self.output_path_input.text().strip()

            if not audio_path or not Path(audio_path).exists():
                raise ValueError("Please select a valid base audio file.")
            if not image_path or not Path(image_path).exists():
                raise ValueError("Please select a valid image source file.")
            if not output_path:
                raise ValueError("Please specify a valid output path.")

            start_sec = self._parse_num(self.start_input.text(), float, "start time")
            end_sec = self._parse_num(self.end_input.text(), float, "end time")
            if start_sec >= end_sec:
                raise ValueError("The start time must be less than the end time.")

            width_val = self._parse_num(self.width_input.text(), int, "width")
            height_val = self._parse_num(self.height_input.text(), int, "height")
            if not (1 <= width_val <= 9999) or not (1 <= height_val <= 9999):
                raise ValueError("The width and height must be between 1 and 9999.")

            threshold_val = self._parse_num(self.threshold_input.text(), int, "threshold")
            if not (0 <= threshold_val <= 255):
                raise ValueError("The threshold must be between 0 and 255.")

            parsed_data = {
                "audio_path": audio_path,
                "image_path": image_path,
                "output_path": output_path,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "width": width_val,
                "height": height_val,
                "threshold": threshold_val
            }
            return parsed_data, None
        except ValueError as e:
            return None, str(e)

    def update_preview(self):
        image_path = self.path_input.text().strip()
        if not image_path or not Path(image_path).exists():
            self.preview_label.setText("No image loaded.")
            self.preview_label.setStyleSheet(f"color: {self.TEXT_MUTED}; font-style: italic;")

            self._cached_original_image = None
            self._cached_image_path = None
            self._cached_width = None
            self._cached_height = None
            self._cached_grayscale_method = None
            self._cached_gray_array = None
            return

        try:
            width = int(self.width_input.text().strip())
            height = int(self.height_input.text().strip())
            threshold = int(self.threshold_input.text().strip())
            if not (1 <= width <= 9999) or not (1 <= height <= 9999) or not (0 <= threshold <= 255):
                raise ValueError
        except ValueError:
            self.preview_label.setText("Invalid settings.")
            self.preview_label.setStyleSheet(f"color: {self.TEXT_MUTED}; font-style: italic;")
            return

        grayscale_method = self.grayscale_combo.currentData()
        invert = self.invert_checkbox.isChecked()

        try:
            pixmap = self._generate_preview_pixmap(image_path, width, height, threshold, grayscale_method, invert)
            if pixmap:
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Preview error.")
        except Exception as e:
            print(f"Error calculating preview internally: {e}")
            self.preview_label.setText("Preview error.")

    def _get_or_create_gray_array(self, image_path, width, height, grayscale_method):
        if self._cached_image_path != image_path or self._cached_original_image is None:
            try:
                with Image.open(image_path) as img:
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img_rgba = img.convert('RGBA')
                        background = Image.new('RGBA', img_rgba.size, (255, 255, 255, 255))
                        img = Image.alpha_composite(background, img_rgba).convert('RGB')
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                    self._cached_original_image = img.copy()
                    self._cached_image_path = image_path
                    
                    self._cached_width = None
                    self._cached_height = None
                    self._cached_grayscale_method = None
                    self._cached_gray_array = None
            except Exception as e:
                print(f"Error loading image: {e}")
                self._cached_original_image = None
                self._cached_image_path = None
                return None, None

        if (self._cached_gray_array is None or
                self._cached_width != width or
                self._cached_height != height or
                self._cached_grayscale_method != grayscale_method):
            try:
                img_resized = self._cached_original_image.resize(
                    (width, height), 
                    resample=Image.Resampling.BILINEAR
                )
                
                if grayscale_method == "luminance_601":
                    img_gray = np.array(img_resized.convert('L'))
                else:
                    img_array = np.array(img_resized)
                    if grayscale_method == "luminance_709":
                        weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
                        img_gray = np.dot(img_array.astype(np.float32), weights).astype(np.uint8)
                    elif grayscale_method == "average":
                        img_gray = img_array.mean(axis=2, dtype=np.float32).astype(np.uint8)
                    elif grayscale_method == "lightness":
                        max_c = np.max(img_array, axis=2).astype(np.float32)
                        min_c = np.min(img_array, axis=2).astype(np.float32)
                        img_gray = ((max_c + min_c) * 0.5).astype(np.uint8)
                    else:
                        weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)
                        img_gray = np.dot(img_array.astype(np.float32), weights).astype(np.uint8)
                
                self._cached_gray_array = img_gray
                self._cached_width = width
                self._cached_height = height
                self._cached_grayscale_method = grayscale_method
                
            except Exception as e:
                print(f"Error rendering grayscale array: {e}")
                self._cached_gray_array = None
                return None, None
                
        return self._cached_gray_array, self._cached_original_image.size

    def _generate_preview_pixmap(self, image_path, width, height, threshold, grayscale_method, invert):
        clamped_threshold = max(0, min(255, int(threshold)))
        
        gray_array, original_size = self._get_or_create_gray_array(image_path, width, height, grayscale_method)
        if gray_array is None or original_size is None:
            return None

        if invert:
            binary_grid = gray_array >= clamped_threshold
        else:
            binary_grid = gray_array < clamped_threshold
            
        has_active = np.any(binary_grid, axis=0)
        first_y = np.argmax(binary_grid, axis=0)
        last_y = (height - 1) - np.argmax(binary_grid[::-1, :], axis=0)
        
        r_indices = np.arange(height)[:, None]
        filled_grid = has_active & (r_indices >= first_y) & (r_indices <= last_y)
        
        debug_fill = (~filled_grid).astype(np.uint8) * 255
        
        preview_pil = Image.fromarray(debug_fill)
        
        orig_width, orig_height = original_size

        if self.aspect_ratio_checkbox.isChecked():
            aspect_ratio = orig_width / orig_height
        else:
            aspect_ratio = width / height
            
        max_w, max_h = self.PREVIEW_MAX_WIDTH, self.PREVIEW_MAX_HEIGHT
        if max_w / max_h > aspect_ratio:
            preview_h = max_h
            preview_w = int(max_h * aspect_ratio)
        else:
            preview_w = max_w
            preview_h = int(max_w / aspect_ratio)
            
        preview_w = max(1, preview_w)
        preview_h = max(1, preview_h)
        
        preview_pil_resized = preview_pil.resize((preview_w, preview_h), resample=Image.Resampling.NEAREST)
        
        im_bytes = preview_pil_resized.tobytes()
        qimg = QImage(im_bytes, preview_w, preview_h, preview_w, QImage.Format.Format_Grayscale8)
        
        return QPixmap.fromImage(qimg.copy())

    def generate_audio(self):
        inputs, error_msg = self._parse_and_validate_inputs()
        if error_msg:
            self.show_message("Input Error", error_msg, "warning")
            return

        output_path = inputs["output_path"]
        if Path(output_path).exists():
            msg = QMessageBox(self)
            msg.setWindowTitle("Overwrite Warning")
            msg.setText("The output file already exists. Do you want to overwrite it?")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            reply = msg.exec()
            if reply == QMessageBox.StandardButton.No:
                return

        self.set_ui_enabled(False)

        run_config = self.default_config.copy()
        run_config.update({
            "output_path": output_path,
            "invert": self.invert_checkbox.isChecked(),
            "width": inputs["width"],
            "height": inputs["height"],
            "grayscale_method": self.grayscale_combo.currentData(),
            "threshold": inputs["threshold"],
            "smooth": self.smooth_checkbox.isChecked(),
            "normalize": self.normalize_checkbox.isChecked(),
            "export_full": self.export_full_checkbox.isChecked()
        })

        worker = AudioGeneratorWorker(
            inputs["audio_path"], 
            inputs["image_path"], 
            inputs["start_sec"], 
            inputs["end_sec"], 
            run_config
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

    def closeEvent(self, event):
        if self.thread_pool.activeThreadCount() > 0:
            reply = QMessageBox.warning(
                self, "Confirm Exit",
                "A generation task is currently running. If you exit, the application will wait for the task to finish cleanly. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.setEnabled(False)
                self.thread_pool.waitForDone()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QMessageBox {{ 
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
                margin-left: 1px;
            }}
            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
            }}

            QComboBox {{
                padding: 4px 8px;
                background-color: {self.INPUT_BG};
                color: {self.TEXT_MAIN};
                border: 1px solid {self.SECTION_BORDER};
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
                min-width: 50px;
            }}
            QComboBox:disabled {{
                color: {self.TEXT_DISABLED};
                background-color: {self.DISABLED_BG_DARK};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: none;
            }}
            QComboBox::down-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 1px solid {self.TEXT_MUTED};
                width: 0;
                height: 0;
                margin-right: 4px;
            }}
            QComboBox::down-arrow:on, QComboBox::down-arrow:hover {{
                border-top-color: {self.TEXT_MAIN};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.INPUT_BG};
                color: {self.TEXT_MAIN};
                border: 1px solid {self.SECTION_BORDER};
                selection-background-color: {self.ACCENT_BLUE};
                selection-color: {self.TEXT_MAIN};
            }}
            
            QGroupBox#ImageSection, QGroupBox#ExportSection, QGroupBox#PreviewSection {{
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

            QSlider::groove:horizontal {{
                border: 1px solid {self.SECTION_BORDER};
                height: 4px;
                background: {self.INPUT_BG};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.ACCENT_BLUE};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {self.TEXT_MAIN};
                border: 1px solid {self.SECTION_BORDER};
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {self.ACCENT_HOVER};
            }}

            QMessageBox QPushButton {{
                background-color: {self.SECTION_BORDER};
                color: {self.TEXT_MAIN};
                border: 1px solid {self.BROWSE_BORDER};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
                min-width: 50px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {self.BROWSE_HOVER};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {self.ACCENT_PRESS};
                border-color: transparent;
            }}
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageToWaveWindow()
    window.show()
    sys.exit(app.exec())