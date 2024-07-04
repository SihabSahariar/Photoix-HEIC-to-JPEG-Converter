# Developer: Sihab Sahariar
# Problem: HEIC to JPEG Converter
# Solution: main.py
# Date: 04.07.2024 

import os
import tempfile
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import qdarkstyle
import configparser

from converter import convert_heic_to_jpeg, convert_heic_file 

class HEICViewer(QDialog):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("HEIC Viewer")
        self.setWindowIcon(QIcon("app_32.png"))
        self.image_label = QLabel()
        self.save_button = QPushButton("Save As")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.save_button)
        self.setLayout(self.layout)
        self.pixmap_raw = None
        self.load_image(image_path)
        self.save_button.clicked.connect(self.save_as)

    def load_image(self, image_path):
        self.pixmap_raw = QtGui.QPixmap(image_path)
        pixmap = self.pixmap_raw.scaled(self.image_label.size(), QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()

    def save_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image As", "", "JPEG Files (*.jpg);;All Files (*)")
        if file_path:
            if self.pixmap_raw:
                self.pixmap_raw.save(file_path, "JPG")
                QMessageBox.information(self, "Success", "Image saved successfully")

class ConversionThread(QtCore.QThread):
    update_output = QtCore.pyqtSignal(str)
    update_progress = QtCore.pyqtSignal(int, str)

    def __init__(self, path, remove, overwrite, recursive, move_path):
        super().__init__()
        self.path = path
        self.remove = remove
        self.overwrite = overwrite
        self.recursive = recursive
        self.move_path = move_path

    def run(self):
        if os.path.isdir(self.path):
            heic_files = [os.path.join(root, file) for root, _, files in os.walk(self.path) for file in files if file.lower().endswith(".heic")]
        elif os.path.isfile(self.path) and self.path.lower().endswith(".heic"):
            heic_files = [self.path]
        else:
            self.update_output.emit(f"Invalid path: {self.path}")
            return

        total_files = len(heic_files)
        if total_files == 0:
            self.update_output.emit("No HEIC files found")
            return

        start_time = time.time()
        for index, heic_file in enumerate(heic_files):
            output_text = f"Converting {heic_file}\n"
            self.update_output.emit(output_text)

            target_file = os.path.splitext(heic_file)[0] + ".jpg"
            if convert_heic_file(heic_file, target_file, self.overwrite, self.remove):
                if self.move_path:
                    new_location = os.path.join(self.move_path, os.path.basename(target_file))
                    os.rename(target_file, new_location)
                    target_file = new_location
                self.update_output.emit(f"Successfully converted {target_file}\n")

            progress = int(((index + 1) / total_files) * 100)
            elapsed_time = time.time() - start_time
            estimated_time = (elapsed_time / (index + 1)) * (total_files - (index + 1))
            self.update_progress.emit(progress, f"Estimated time remaining: {int(estimated_time)} seconds")

class HEICConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()




        self.setWindowTitle("Photoix HEIC to JPEG Converter")
        self.setGeometry(100, 100, 1000, 600)

        # Set App Icon
        self.setWindowIcon(QIcon("app_32.png"))


        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #555555;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QLineEdit {
                background-color: #3e3e3e;
                border: 1px solid #555555;
                padding: 5px;
            }
            QTextEdit {
                background-color: #3e3e3e;
                border: 1px solid #555555;
                padding: 5px;
            }
            QCheckBox {
                padding: 5px;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        self.left_layout = QVBoxLayout()
        self.layout.addLayout(self.left_layout)

        self.path_label = QLabel("File or Directory Path:")
        self.left_layout.addWidget(self.path_label)

        self.path_entry = QLineEdit()
        self.left_layout.addWidget(self.path_entry)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse)
        self.left_layout.addWidget(self.browse_button)

        self.remove_check = QCheckBox("Remove converted HEIC Files")
        self.left_layout.addWidget(self.remove_check)

        self.overwrite_check = QCheckBox("Overwrite existing JPEG files")
        self.left_layout.addWidget(self.overwrite_check)

        self.recursive_check = QCheckBox("Search subdirectories")
        self.recursive_check.setChecked(True)
        self.left_layout.addWidget(self.recursive_check)

        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.convert)
        self.left_layout.addWidget(self.convert_button)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.left_layout.addWidget(self.console_output)

        self.progress_bar = QProgressBar()
        self.left_layout.addWidget(self.progress_bar)

        self.label_total = QLabel("Total Files: 0")
        self.left_layout.addWidget(self.label_total)

        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.preview_file)
        self.layout.addWidget(self.file_list)

        self.create_menu()

        self.move_path = ""

        self.read_config_language()



    def create_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('Settings')
        about_menu = menubar.addMenu('About')

        move_action = QAction('Set Move Path', self)
        move_action.triggered.connect(self.set_move_path)
        settings_menu.addAction(move_action)

        language_action = QAction('Language', self)
        language_action.triggered.connect(self.show_language_dialog)
        settings_menu.addAction(language_action)

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        about_menu.addAction(about_action)


    def set_move_path(self):
        self.move_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if self.move_path:
            self.console_output.append(f"Set move path to: {self.move_path}")

    def show_about(self):
        QMessageBox.information(self, "About", "Developer: Sihab Sahariar\nEmail: sihabsahariarcse@gmail.com\nGithub: www.github.com/sihabsahariar")

    def browse(self):
        file_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.path_entry.setText(file_path)
        self.load_files(file_path)

    def load_files(self, directory):
        self.file_list.clear()
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".heic"):
                    file_path = os.path.join(root, file)
                    self.file_list.addItem(file_path)
        self.label_total.setText(f"Total Files: {self.file_list.count()}")

    def convert(self):
        path = self.path_entry.text()
        if not path:
            QMessageBox.warning(self, "Warning", "Please select a valid directory or file")
            return

        remove = self.remove_check.isChecked()
        overwrite = self.overwrite_check.isChecked()
        recursive = self.recursive_check.isChecked()

        self.convert_button.setEnabled(False)
        self.thread = ConversionThread(path, remove, overwrite, recursive, self.move_path)
        self.thread.update_output.connect(self.update_console)
        self.thread.update_progress.connect(self.update_progress)
        self.thread.finished.connect(self.conversion_finished)
        self.thread.start()

    def update_console(self, text):
        self.console_output.append(text)
        self.console_output.verticalScrollBar().setValue(self.console_output.verticalScrollBar().maximum())

    def update_progress(self, value, estimate_time):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{value}% - {estimate_time}")

    def conversion_finished(self):
        self.convert_button.setEnabled(True)
        self.update_console("Conversion finished.")
        QMessageBox.information(self, "Success", f"Conversion finished successfully\nFiles Moved to {self.move_path}")

    def preview_file(self, item):
        heic_path = item.text()
        tmp_file = tempfile.NamedTemporaryFile(delete=True, suffix=".jpg").name
        convert_heic_file(heic_path, tmp_file, overwrite=True, remove=False)
        self.image_viewer = HEICViewer(tmp_file)
        self.image_viewer.show()

    # Function to Read the Language from Config File
    def read_config_language(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        try:
            language = config['DEFAULT']['language']
            if language == 'English':
                self.setEnglish()
            else:
                self.setBangla()
        except Exception as e:
            QMessageBox.warning(self, 'Warning', f'Error reading language from config.ini: {e}')
            return

    # Function to set the Language in Config File
    def show_language_dialog(self):
        # Show a dialog to set the Language (English/French) value and save it in config.ini
        language, ok = QInputDialog.getItem(self, 'Language', 'Select the Language:', ['English', 'Bangla'], editable=False)
        if ok:
            # Save the threshold value in config.ini
            config = configparser.ConfigParser()
            config.read('config.ini')
            config['DEFAULT']['language'] = language

            with open('config.ini', 'w') as configfile:
                config.write(configfile)

            self.read_config_language()


    # Function to update all UI elements for English language
    def setEnglish(self):
        self.setWindowTitle("Photoix HEIC to JPEG Converter")
        self.path_label.setText("File or Directory Path:")
        self.browse_button.setText("Browse")
        self.remove_check.setText("Remove converted HEIC Files")
        self.overwrite_check.setText("Overwrite existing JPEG files")
        self.recursive_check.setText("Search subdirectories")
        self.convert_button.setText("Convert")
        self.label_total.setText("Total Files: 0")

        # Change the language of the menubar
        self.menuBar().actions()[0].setText('Settings')
        self.menuBar().actions()[1].setText('About')
        self.menuBar().actions()[0].menu().actions()[0].setText('Set Move Path')
        self.menuBar().actions()[0].menu().actions()[1].setText('Set Language')
        self.menuBar().actions()[1].menu().actions()[0].setText('About')

        # Set English Font test.ttf from "Fonts/en.tff"
        font = QFont()
        font.setFamily("Fonts/Nirmala.ttf")
        font.setPointSize(10)

        # Set English Font for all the UI elements
        for widget in self.findChildren(QWidget):
            widget.setFont(font)



    # Function to update all UI elements for Bangla language
    def setBangla(self):
        self.setWindowTitle("Photoix HEIC to JPEG Converter")
        self.path_label.setText("ফাইল বা ডিরেক্টরি পথ:")
        self.browse_button.setText("ব্রাউজ")
        self.remove_check.setText("প্রেরিত হওয়া HEIC ফাইলগুলি মুছুন")
        self.overwrite_check.setText("বিদ্যমান JPEG ফাইলগুলি ওভার রাইট করুন")
        self.recursive_check.setText("সাবডিরেক্টরি অনুসন্ধান করুন")
        self.convert_button.setText("রুপান্তর করুন")
        self.label_total.setText("মোট ফাইলগুলি: 0")

        # Change the language of the menubar
        self.menuBar().actions()[0].setText('সেটিংস')
        self.menuBar().actions()[1].setText('ডেভেলোপার সম্পর্কে')
        self.menuBar().actions()[0].menu().actions()[0].setText('মুভ পাথ সেট করুন')
        self.menuBar().actions()[0].menu().actions()[1].setText('ভাষা পরিবর্তন করুন')
        self.menuBar().actions()[1].menu().actions()[0].setText('ইনফর্মেশন')

        # Set Bangla Font test.ttf from "Fonts/bd.tff"
        font = QFont()
        font.setFamily("Fonts/Siyam Rupali ANSI.ttf")
        font.setPointSize(10)
        self.setFont(font)

        # Set Bangla Font for all the UI elements
        for widget in self.findChildren(QWidget):
            widget.setFont(font)

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = HEICConverterGUI()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
