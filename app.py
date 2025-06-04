import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QProgressBar, QLabel, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from imageio_ffmpeg import get_ffmpeg_exe


class HLSConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎥 Video to HLS Converter")
        self.setMinimumSize(500, 350)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Video to HLS Converter")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        self.instruction_label = QLabel("Choose conversion mode:")
        self.instruction_label.setFont(QFont("Arial", 11))
        self.layout.addWidget(self.instruction_label)

        self.single_button = QPushButton("Convert Single File")
        self.single_button.setMinimumHeight(40)
        self.single_button.clicked.connect(self.convert_single_file)
        self.layout.addWidget(self.single_button)

        self.folder_button = QPushButton("Convert Entire Folder")
        self.folder_button.setMinimumHeight(40)
        self.folder_button.clicked.connect(self.convert_folder)
        self.layout.addWidget(self.folder_button)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: green;")
        self.layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress)

        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(self.layout)

    def get_ffmpeg_path(self):
        ffmpeg_original = get_ffmpeg_exe()
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, os.path.basename(ffmpeg_original))
        return ffmpeg_original

    def convert_single_file(self):
        input_file, _ = QFileDialog.getOpenFileName(self, "Select Video File")
        if not input_file:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_dir:
            return

        self.run_ffmpeg_batch([input_file], output_dir, single_file=True)

    def convert_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with Video Files")
        if not folder_path:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_dir:
            return

        video_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
        ]

        if not video_files:
            QMessageBox.information(self, "No Videos", "No supported video files found in the folder.")
            return

        self.run_ffmpeg_batch(video_files, output_dir)

    def run_ffmpeg_batch(self, input_files, output_dir, single_file=False):
        total = len(input_files)
        self.progress.setMaximum(total)
        self.progress.setValue(0)

        ffmpeg_path = self.get_ffmpeg_path()

        for idx, input_file in enumerate(input_files, start=1):
            base_name = os.path.splitext(os.path.basename(input_file))[0]

            if single_file:
                target_folder = output_dir
            else:
                target_folder = os.path.join(output_dir, base_name)
                os.makedirs(target_folder, exist_ok=True)

            output_path = os.path.join(target_folder, f"{base_name}.m3u8")
            self.status_label.setText(f"Converting: {base_name}")
            QApplication.processEvents()

            try:
                subprocess.run([
                    ffmpeg_path,
                    "-i", input_file,
                    "-codec:", "copy",
                    "-start_number", "0",
                    "-hls_time", "10",
                    "-hls_list_size", "0",
                    "-f", "hls",
                    output_path
                ], check=True)

            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Error", f"Failed to convert {input_file}:\n{str(e)}")
                continue

            self.progress.setValue(idx)
            QApplication.processEvents()

        self.status_label.setText("All conversions completed.")
        QMessageBox.information(self, "Done", "All conversions completed.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HLSConverter()
    window.show()
    sys.exit(app.exec_())
