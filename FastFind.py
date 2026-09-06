# Copyright (C) 2026 Lixiod Technologies

import os
import sys
import time
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTableView, QLabel, QHeaderView, QAbstractItemView
)

# Background thread to index files without freezing the UI
class IndexerThread(QThread):
    # Signals to pass data back to the main UI thread
    data_indexed = pyqtSignal(list)
    status_update = pyqtSignal(str)

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path

    def run(self):
        self.status_update.emit("Indexing files...")
        start_time = time.time()
        file_list = []

        # Fast directory walking using os.walk
        for root, _, files in os.walk(self.root_path):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    stat = os.stat(full_path)
                    size_kb = f"{stat.st_size / 1024:.1f} KB"
                except (PermissionError, FileNotFoundError):
                    size_kb = "N/A"
                
                file_list.append((file, root, size_kb))

        elapsed_time = time.time() - start_time
        self.data_indexed.emit(file_list)
        self.status_update.emit(f"Indexed {len(file_list)} items in {elapsed_time:.2f} seconds.")


class FastFindApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastFind")
        self.resize(900, 600)

        # Main Layout Setup
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Search Bar Input
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type to search files...")
        self.search_bar.textChanged.connect(self.filter_results)
        layout.addWidget(self.search_bar)

        # Table View Setup
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_view)

        # Status Bar
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)

        # Data Model & Proxy Model for High-Speed Filtering
        self.source_model = QStandardItemModel(0, 3)
        self.source_model.setHorizontalHeaderLabels(["Name", "Path", "Size"])
        
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)  # Filter by file name

        self.table_view.setModel(self.proxy_model)

        # Start Indexing
        target_dir = "C:\\" if os.name == "nt" else os.path.expanduser("~")
        self.indexer = IndexerThread(target_dir)
        self.indexer.data_indexed.connect(self.populate_table)
        self.indexer.status_update.connect(self.status_label.setText)
        self.indexer.start()

    def populate_table(self, file_list):
        self.source_model.setRowCount(0)
        for name, path, size in file_list:
            item_name = QStandardItem(name)
            item_path = QStandardItem(path)
            item_size = QStandardItem(size)
            self.source_model.appendRow([item_name, item_path, item_size])

    def filter_results(self, text):
        # Dynamically updates the proxy model regex to instantly filter results
        self.proxy_model.setFilterFixedString(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FastFindApp()
    window.show()
    sys.exit(app.exec())
