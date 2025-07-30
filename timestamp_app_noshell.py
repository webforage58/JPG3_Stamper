#!/usr/bin/env python3
"""
SOLUTION: Use Pillow for robust image manipulation.
This avoids ffmpeg's complex filter syntax entirely.
"""
import os
import sys
import datetime
import re
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QFileDialog, QTextEdit, 
                             QProgressBar, QMessageBox, QGroupBox, QCheckBox, QLineEdit, QTabWidget)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QThread, Signal
from PIL import Image, ImageDraw, ImageFont

# Colors
COLORS = {
    "primary": "#2C3E50",
    "secondary": "#3498DB",
    "accent": "#E74C3C",
    "background": "#ECF0F1",
    "success": "#2ECC71",
    "text_light": "#FFFFFF",
}

class PillowWorker(QThread):
    """Thread for running Pillow image processing."""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, source_path, dest_path, timestamp_dt, font_size, position, dual_stamp):
        super().__init__()
        self.source_path = source_path
        self.dest_path = dest_path
        self.timestamp_dt = timestamp_dt
        self.font_size = font_size
        self.position = position
        self.dual_stamp = dual_stamp

    def run(self):
        try:
            self.add_timestamp_with_pillow()
            self.finished.emit(True, f"Processed: {os.path.basename(self.source_path)}")
        except Exception as e:
            self.finished.emit(False, f"Error processing {os.path.basename(self.source_path)}: {e}")

    def add_timestamp_with_pillow(self):
        """Adds timestamp to an image using Pillow."""
        with Image.open(self.source_path) as img:
            draw = ImageDraw.Draw(img)
            
            try:
                # Use a common system font, with a fallback
                font = ImageFont.truetype("Arial.ttf", self.font_size)
            except IOError:
                font = ImageFont.load_default()

            formatted_date = self.timestamp_dt.strftime("%Y-%m-%d")
            formatted_time = self.timestamp_dt.strftime("%H:%M:%S")

            # Calculate text size and position
            def get_text_position(text, y_offset):
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = self.position - text_width - 10 # 10px padding from the edge
                y = img.height - text_height - y_offset
                return (x, y)

            # Draw time and date
            if self.dual_stamp:
                time_pos = get_text_position(formatted_time, self.font_size + 20)
                date_pos = get_text_position(formatted_date, 10)
                draw.text(time_pos, formatted_time, font=font, fill="white")
                draw.text(date_pos, formatted_date, font=font, fill="white")
            else:
                date_pos = get_text_position(formatted_date, 10)
                draw.text(date_pos, formatted_date, font=font, fill="white")

            img.save(self.dest_path, "JPEG")

class TimestampApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("JPG Timestamper (Pillow Edition)")
        self.setMinimumSize(1100, 900)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # ... (UI setup remains largely the same) ...
        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_widget.setStyleSheet(f"background-color: {COLORS['primary']}; border-radius: 5px;")
        
        title_label = QLabel("JPG Timestamper (Pillow Edition)")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_light']};")
        
        self.status_indicator = QLabel("Ready")
        self.status_indicator.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; padding: 5px 10px; background-color: rgba(255,255,255,0.2); border-radius: 3px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        main_layout.addWidget(header_widget)
        
        # Config Tab
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        folder_group = QGroupBox("Folder Selection")
        folder_layout = QVBoxLayout(folder_group)
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source Folder:"))
        self.source_path_input = QLineEdit("/Users/johnhuberd/Downloads/timelapse")
        self.source_path_input.setReadOnly(True)
        source_button = QPushButton("Browse...")
        source_button.clicked.connect(self.select_source_folder)
        source_layout.addWidget(self.source_path_input, 1)
        source_layout.addWidget(source_button)
        folder_layout.addLayout(source_layout)
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Destination Folder:"))
        self.dest_path_input = QLineEdit("/Users/johnhuberd/Downloads/timelapse/stamped_images")
        self.dest_path_input.setReadOnly(True)
        dest_button = QPushButton("Browse...")
        dest_button.clicked.connect(self.select_dest_folder)
        dest_layout.addWidget(self.dest_path_input, 1)
        dest_layout.addWidget(dest_button)
        folder_layout.addLayout(dest_layout)
        config_layout.addWidget(folder_group)
        
        timestamp_group = QGroupBox("Timestamp Options")
        timestamp_layout = QVBoxLayout(timestamp_group)
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font Size:"))
        self.font_size_dropdown = QComboBox()
        self.font_size_dropdown.addItems(["Small", "Medium", "Large"])
        self.font_size_dropdown.setCurrentIndex(1)
        font_size_layout.addWidget(self.font_size_dropdown)
        timestamp_layout.addLayout(font_size_layout)
        
        self.dual_timestamp_checkbox = QCheckBox("Show time above date")
        self.dual_timestamp_checkbox.setChecked(True)
        timestamp_layout.addWidget(self.dual_timestamp_checkbox)
        config_layout.addWidget(timestamp_group)
        config_layout.addStretch()

        # Process Tab
        process_tab = QWidget()
        process_layout = QVBoxLayout(process_tab)
        self.stamp_button = QPushButton("Stamp JPGs with Pillow")
        self.stamp_button.clicked.connect(self.stamp_jpgs)
        process_layout.addWidget(self.stamp_button)
        process_layout.addStretch()

        self.tabs = QTabWidget()
        self.tabs.addTab(config_tab, "Configuration")
        self.tabs.addTab(process_tab, "Process")

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.progress_bar = QProgressBar()

        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log_text)

        self.worker = None
        self.all_jpg_files = []
        self.current_file_index = 0

        os.makedirs(self.source_path_input.text(), exist_ok=True)
        os.makedirs(self.dest_path_input.text(), exist_ok=True)

    def log(self, message):
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()

    def select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder", self.source_path_input.text())
        if folder:
            self.source_path_input.setText(folder)

    def select_dest_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder", self.dest_path_input.text())
        if folder:
            self.dest_path_input.setText(folder)
            os.makedirs(folder, exist_ok=True)

    def get_font_size(self):
        index = self.font_size_dropdown.currentIndex()
        return 24 if index == 0 else 48 if index == 1 else 72

    def stamp_jpgs(self):
        source_dir = self.source_path_input.text()
        if not os.path.isdir(source_dir):
            QMessageBox.warning(self, "Error", f"Source directory '{source_dir}' does not exist")
            return

        self.all_jpg_files = [f for f in os.listdir(source_dir) 
                            if f.lower().endswith('.jpg') and not f.startswith('._')]
        
        if not self.all_jpg_files:
            QMessageBox.warning(self, "Error", "No JPG files found.")
            return

        self.current_file_index = 0
        self.progress_bar.setRange(0, len(self.all_jpg_files))
        self.stamp_button.setEnabled(False)
        self.log("🚀 Starting timestamp process with Pillow...")
        self.process_next_jpg()

    def process_next_jpg(self):
        if self.current_file_index >= len(self.all_jpg_files):
            self.log("🎉 All images processed successfully!")
            self.stamp_button.setEnabled(True)
            self.status_indicator.setText("Complete")
            return

        img_file = self.all_jpg_files[self.current_file_index]
        source_path = os.path.join(self.source_path_input.text(), img_file)
        dest_path = os.path.join(self.dest_path_input.text(), f"stamped_{img_file}")

        dt_object = self.get_timestamp(source_path)
        if not dt_object:
            self.log(f"Skipping {img_file} - could not determine timestamp.")
            self.current_file_index += 1
            self.process_next_jpg()
            return

        font_size = self.get_font_size()
        # Using image width for positioning
        with Image.open(source_path) as img:
            position = img.width

        self.worker = PillowWorker(source_path, dest_path, dt_object, font_size, position, self.dual_timestamp_checkbox.isChecked())
        self.worker.finished.connect(self.on_file_processed)
        self.worker.start()

    def get_timestamp(self, file_path):
        """Extract timestamp from EXIF data using Pillow."""
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    # EXIF tag 36867 corresponds to DateTimeOriginal
                    timestamp_str = exif_data.get(36867)
                    if timestamp_str:
                        return datetime.datetime.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')
        except (AttributeError, KeyError, IndexError, ValueError) as e:
            self.log(f"Could not read EXIF data for {os.path.basename(file_path)}: {e}")
        
        # Fallback to filename parsing, then file modification time
        filename = os.path.basename(file_path)
        match = re.search(r'(\d{8})_(\d{6})', filename)
        if match:
            try:
                return datetime.datetime.strptime(f"{match.group(1)}_{match.group(2)}", '%Y%m%d_%H%M%S')
            except ValueError:
                pass
        try:
            mod_time = os.path.getmtime(file_path)
            return datetime.datetime.fromtimestamp(mod_time)
        except OSError:
            return None

    def on_file_processed(self, success, message):
        self.progress_bar.setValue(self.current_file_index + 1)
        self.log(message)
        if not success:
            self.status_indicator.setText("Error")
        self.current_file_index += 1
        self.process_next_jpg()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimestampApp()
    window.show()
    sys.exit(app.exec())
