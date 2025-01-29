import os
import csv
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
                             QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit,
                             QComboBox, QHBoxLayout)
from PyQt6.QtCore import Qt

# File storage location
DATA_DIR = r"C:\Users\User\OneDrive\Desktop\HomeExpense"
COLUMNS = ["Date", "Day", "Grocery", "Hotel", "Laundry", "College", "Bus", "Dewa", "Gas",
           "Etisalat", "Elife", "Petrol", "Misc", "Total (AED)", "Total (INR)"]
AED_TO_INR = 22.0  # Static conversion rate

def create_monthly_csv(year, month):
    """Creates a new CSV file for the given month if it doesn't exist."""
    month_name = datetime(year, month, 1).strftime('%B')
    file_path = os.path.join(DATA_DIR, f"{year}_{month_name}.csv")
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(COLUMNS)
            for day in range(1, 32):
                try:
                    date = datetime(year, month, day)
                    writer.writerow([date.strftime('%Y-%m-%d'), date.strftime('%A')] + [0] * (len(COLUMNS) - 2))
                except ValueError:
                    break
    return file_path

class HomeExpenseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Home Expense Tracker")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        
        # Year and Month Selection
        self.year_box = QComboBox()
        self.year_box.addItems([str(y) for y in range(2023, 2031)])
        self.month_box = QComboBox()
        self.month_box.addItems([datetime(2000, m, 1).strftime('%B') for m in range(1, 13)])
        
        # Buttons
        self.load_button = QPushButton("Load Expenses")
        self.load_button.clicked.connect(self.load_expenses)
        
        self.table = QTableWidget()
        
        # Layout
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Year:"))
        select_layout.addWidget(self.year_box)
        select_layout.addWidget(QLabel("Month:"))
        select_layout.addWidget(self.month_box)
        select_layout.addWidget(self.load_button)
        
        layout.addLayout(select_layout)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_expenses(self):
        """Loads the expenses for the selected month and year."""
        year = int(self.year_box.currentText())
        month = self.month_box.currentIndex() + 1
        file_path = create_monthly_csv(year, month)
        
        df = pd.read_csv(file_path, na_values=['-'])
        self.populate_table(df, file_path)
    
    def populate_table(self, df, file_path):
        """Populates the table with CSV data."""
        self.table.clear()
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)

        # Disconnect only if connected
        try:
            self.table.itemChanged.disconnect(self.save_changes)
        except TypeError:
            pass  # Ignore if not connected

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                if col > 1:  # Make expense fields editable
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)
        
        self.table.itemChanged.connect(lambda: self.save_changes(df, file_path))  # Reconnect signal
    
    def save_changes(self, df, file_path):
        """Saves changes made to the table."""
        self.table.blockSignals(True)  # Prevent recursive signals
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = self.table.item(row, col)
                if item:
                    try:
                        df.iloc[row, col] = float(item.text()) if col > 1 else item.text()
                    except ValueError:
                        df.iloc[row, col] = 0  # Convert invalid values to 0
        
        # Calculate total per row, ensuring safe numeric conversion
        for i in range(len(df)):
            try:
                numeric_values = pd.to_numeric(df.iloc[i, 2:-2], errors='coerce').fillna(0)  # Convert to float safely
                total_aed = numeric_values.sum()
                df.iloc[i, -2] = total_aed
                df.iloc[i, -1] = total_aed * AED_TO_INR
            except ValueError:
                continue
        
        # Ensure final row has correct column count
        total_row = ["TOTAL", "-"] + [pd.to_numeric(df.iloc[:, i], errors='coerce').fillna(0).sum() if i > 1 else "-" for i in range(len(COLUMNS))]
        total_row = total_row[:len(COLUMNS)]  # Ensure it matches column length
        df.loc[len(df)] = total_row  # Append total row

        # Save changes back to CSV
        df.to_csv(file_path, index=False)

        self.table.blockSignals(False)  # Re-enable signals

if __name__ == '__main__':
    app = QApplication([])
    window = HomeExpenseApp()
    window.show()
    app.exec()
