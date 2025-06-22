import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTextEdit, QMessageBox, QProgressBar, QFileDialog,
                            QTabWidget, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from command import Command
from audible_api import AudibleAPI
import asyncio
import threading

class WorkerThread(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            if asyncio.iscoroutinefunction(self.func):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.func(*self.args, **self.kwargs))
                loop.close()
            else:
                result = self.func(*self.args, **self.kwargs)
            self.finished.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))

class AudibleExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cmd = Command()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Audible Bookmark Extractor')
        self.setMinimumSize(800, 600)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Authentication tab
        auth_tab = QWidget()
        auth_layout = QVBoxLayout(auth_tab)
        
        # Audible Authentication
        auth_group = QWidget()
        auth_group_layout = QVBoxLayout(auth_group)
        
        auth_label = QLabel("Audible Authentication")
        auth_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        auth_group_layout.addWidget(auth_label)
        
        auth_button = QPushButton("Authenticate with Audible")
        auth_button.clicked.connect(self.authenticate_audible)
        auth_group_layout.addWidget(auth_button)
        
        # Readwise Authentication
        readwise_group = QWidget()
        readwise_layout = QVBoxLayout(readwise_group)
        
        readwise_label = QLabel("Readwise Authentication")
        readwise_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        readwise_layout.addWidget(readwise_label)
        
        self.readwise_token = QLineEdit()
        self.readwise_token.setPlaceholderText("Enter your Readwise token")
        readwise_layout.addWidget(self.readwise_token)
        
        readwise_button = QPushButton("Authenticate with Readwise")
        readwise_button.clicked.connect(self.authenticate_readwise)
        readwise_layout.addWidget(readwise_button)
        
        auth_layout.addWidget(auth_group)
        auth_layout.addWidget(readwise_group)
        auth_layout.addStretch()
        
        # Books tab
        books_tab = QWidget()
        books_layout = QVBoxLayout(books_tab)
        
        refresh_button = QPushButton("Refresh Book List")
        refresh_button.clicked.connect(self.refresh_books)
        books_layout.addWidget(refresh_button)
        
        self.book_combo = QComboBox()
        books_layout.addWidget(self.book_combo)
        
        download_button = QPushButton("Download Selected Book")
        download_button.clicked.connect(self.download_book)
        books_layout.addWidget(download_button)
        
        # Export tab
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        
        export_label = QLabel("Export Options")
        export_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        export_layout.addWidget(export_label)
        
        export_to_excel = QPushButton("Export to Excel")
        export_to_excel.clicked.connect(self.export_to_excel)
        export_layout.addWidget(export_to_excel)
        
        export_to_readwise = QPushButton("Export to Readwise")
        export_to_readwise.clicked.connect(self.export_to_readwise)
        export_layout.addWidget(export_to_readwise)
        
        # Add tabs to tab widget
        tabs.addTab(auth_tab, "Authentication")
        tabs.addTab(books_tab, "Books")
        tabs.addTab(export_tab, "Export")
        
        # Status bar for feedback
        self.statusBar().showMessage('Ready')
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def authenticate_audible(self):
        self.worker = WorkerThread(self.cmd.audible_obj.authenticate if self.cmd.audible_obj else AudibleAPI.authenticate)
        self.worker.finished.connect(self.handle_audible_auth_success)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, 'Error', str(msg)))
        self.worker.start()
        self.statusBar().showMessage('Authenticating with Audible...')

    def handle_audible_auth_success(self, result):
        if not self.cmd.audible_obj:
            self.cmd.audible_obj = result
        self.statusBar().showMessage('Audible authentication successful')

    def authenticate_readwise(self):
        token = self.readwise_token.text()
        if not token:
            QMessageBox.warning(self, 'Warning', 'Please enter your Readwise token')
            return
            
        # Save token to file
        with open('readwise_token.json', 'w') as f:
            json.dump({'token': token}, f)
        self.statusBar().showMessage('Readwise token saved')

    def refresh_books(self):
        if not self.cmd.audible_obj:
            QMessageBox.warning(self, 'Warning', 'Please authenticate with Audible first')
            return
        
        self.worker = WorkerThread(self.cmd.audible_obj.get_book_selection)
        self.worker.finished.connect(self.update_book_list)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, 'Error', str(msg)))
        self.worker.start()
        self.statusBar().showMessage('Refreshing book list...')

    def update_book_list(self, books):
        self.book_combo.clear()
        try:
            books_list = books if isinstance(books, list) else json.loads(books)
            for book in books_list:
                self.book_combo.addItem(book.get('title', 'Unknown'), book.get('asin', ''))
        except Exception as e:
            QMessageBox.warning(self, 'Warning', f'Failed to parse book list: {str(e)}')
        self.statusBar().showMessage('Book list updated')

    def download_book(self):
        if not self.cmd.audible_obj:
            QMessageBox.warning(self, 'Warning', 'Please authenticate with Audible first')
            return
            
        if self.book_combo.currentData():
            self.worker = WorkerThread(
                self.cmd.audible_obj.cmd_download_books,
                asin=self.book_combo.currentData()
            )
            self.worker.finished.connect(lambda: self.statusBar().showMessage('Download complete'))
            self.worker.error.connect(lambda msg: QMessageBox.critical(self, 'Error', str(msg)))
            self.worker.start()
            self.statusBar().showMessage('Downloading book...')
        else:
            QMessageBox.warning(self, 'Warning', 'Please select a book first')

    def export_to_excel(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")
        if file_name:
            self.worker = WorkerThread(self.cmd.export_to_excel, file_name)
            self.worker.finished.connect(lambda: self.statusBar().showMessage('Export complete'))
            self.worker.error.connect(lambda msg: QMessageBox.critical(self, 'Error', msg))
            self.worker.start()
            self.statusBar().showMessage('Exporting to Excel...')

    def export_to_readwise(self):
        if not self.cmd.readwise_obj:
            QMessageBox.warning(self, 'Warning', 'Please authenticate with Readwise first')
            return
            
        if not self.cmd.audible_obj:
            QMessageBox.warning(self, 'Warning', 'Please authenticate with Audible first')
            return
            
        self.worker = WorkerThread(self.cmd.readwise_obj.cmd_post_highlights)
        self.worker.finished.connect(lambda: self.statusBar().showMessage('Export to Readwise complete'))
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, 'Error', str(msg)))
        self.worker.start()
        self.statusBar().showMessage('Exporting to Readwise...')

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern style
    window = AudibleExtractorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 