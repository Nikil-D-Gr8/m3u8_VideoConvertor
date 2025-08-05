import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QProgressBar, QLabel, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from imageio_ffmpeg import get_ffmpeg_exe


class ConversionThread(QThread):
    progress_update = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_files, output_dir, single_file, ffmpeg_path):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.single_file = single_file
        self.ffmpeg_path = ffmpeg_path

    def run(self):
        total = len(self.input_files)

        resolutions = {
            "240p": (426, 240, "400k"),
            "360p": (640, 360, "800k"),
            "720p": (1280, 720, "1400k"),
            "1080p": (1920, 1080, "3000k")
        }

        for idx, input_file in enumerate(self.input_files, start=1):
            base_name = os.path.splitext(os.path.basename(input_file))[0]

            if self.single_file:
                target_folder = self.output_dir
            else:
                target_folder = os.path.join(self.output_dir, base_name)
                os.makedirs(target_folder, exist_ok=True)

            playlist_paths = []

            try:
                for res, (w, h, bitrate) in resolutions.items():
                    out_name = f"{res}.m3u8"
                    out_path = os.path.join(target_folder, out_name)
                    playlist_paths.append(out_name)

                    subprocess.run([
                        self.ffmpeg_path,
                        "-i", input_file,
                        "-vf", f"scale=w={w}:h={h}",
                        "-c:v", "libx264",
                        "-b:v", bitrate,
                        "-c:a", "aac",
                        "-strict", "-2",
                        "-hls_time", "10",
                        "-hls_playlist_type", "vod",
                        "-f", "hls",
                        out_path
                    ], check=True)

                master_path = os.path.join(target_folder, f"index.m3u8")
                with open(master_path, 'w') as master:
                    master.write("#EXTM3U\n")
                    for res, (w, h, bitrate) in resolutions.items():
                        resolution_str = f"{w}x{h}"
                        master.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bitrate.strip('k')}000,RESOLUTION={resolution_str}\n")
                        master.write(f"{res}.m3u8\n")

                self.progress_update.emit(idx, base_name)

            except subprocess.CalledProcessError as e:
                self.error.emit(f"Failed to convert {input_file}: {str(e)}")

        self.finished.emit()


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

        self.start_conversion([input_file], output_dir, True)

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

        self.start_conversion(video_files, output_dir, False)

    def start_conversion(self, input_files, output_dir, single_file):
        self.progress.setMaximum(len(input_files))
        self.progress.setValue(0)
        self.status_label.setText("Starting conversion...")

        ffmpeg_path = self.get_ffmpeg_path()
        self.thread = ConversionThread(input_files, output_dir, single_file, ffmpeg_path)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.finished.connect(self.conversion_finished)
        self.thread.error.connect(self.show_error)
        self.thread.start()

    def update_progress(self, val, name):
        self.progress.setValue(val)
        self.status_label.setText(f"Converted: {name}")

    def conversion_finished(self):
        self.status_label.setText("All conversions completed.")
        QMessageBox.information(self, "Done", "All conversions completed.")

    def show_error(self, msg):
        QMessageBox.critical(self, "Error", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HLSConverter()
    window.show()
    sys.exit(app.exec_())