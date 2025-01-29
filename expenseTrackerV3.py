import os
import csv
import threading
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, 
                             QLineEdit, QComboBox, QHBoxLayout, QGridLayout, QFileDialog)
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
        self.expense_fields = {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Home Expense Tracker")
        self.setGeometry(200, 100, 600, 700)
        self.layout = QVBoxLayout()
        
        # Year, Month, and Day Selection
        date_layout = QHBoxLayout()
        self.year_box = QComboBox()
        self.year_box.addItems([str(y) for y in range(2023, 2031)])
        
        self.month_box = QComboBox()
        self.month_box.addItems([datetime(2000, m, 1).strftime('%B') for m in range(1, 13)])

        self.day_box = QComboBox()
        self.day_box.addItems([str(d) for d in range(1, 32)])

        self.load_button = QPushButton("Load Expenses")
        self.load_button.clicked.connect(self.load_expenses)
        
        date_layout.addWidget(QLabel("Year:"))
        date_layout.addWidget(self.year_box)
        date_layout.addWidget(QLabel("Month:"))
        date_layout.addWidget(self.month_box)
        date_layout.addWidget(QLabel("Day:"))
        date_layout.addWidget(self.day_box)
        date_layout.addWidget(self.load_button)
        
        self.layout.addLayout(date_layout)

        # Expense Form Layout
        self.grid_layout = QGridLayout()
        row = 0
        self.expense_fields = {}
        
        for col in COLUMNS[2:-2]:  # Ignore Date, Day, and Total columns
            label = QLabel(f"{col}:")
            field = QLineEdit()
            field.setPlaceholderText("Enter amount")
            self.expense_fields[col] = field
            self.grid_layout.addWidget(label, row, 0)
            self.grid_layout.addWidget(field, row, 1)
            row += 1
        
        self.layout.addLayout(self.grid_layout)
        
        # Save Button and Total Labels
        self.save_button = QPushButton("Save Expenses")
        self.save_button.clicked.connect(self.save_expenses)
        self.layout.addWidget(self.save_button)

        self.total_label = QLabel("Total (AED): 0 | Total (INR): 0")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        self.layout.addWidget(self.total_label)

        # Monthly Expense Label
        self.monthly_total_label = QLabel("Monthly Expense (AED): 0")
        self.monthly_total_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        self.layout.addWidget(self.monthly_total_label)

        # Button to show expense graph
        self.graph_button = QPushButton("Show Expense Graph")
        self.graph_button.clicked.connect(self.show_expense_graph)
        self.layout.addWidget(self.graph_button)

        # Button to save expense graph
        self.save_graph_button = QPushButton("Save Graph")
        self.save_graph_button.clicked.connect(self.save_expense_graph)
        self.layout.addWidget(self.save_graph_button)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

    def load_expenses(self):
        """Loads the expenses for the selected year, month, and day."""
        year = int(self.year_box.currentText())
        month = self.month_box.currentIndex() + 1
        day = int(self.day_box.currentText())
        file_path = create_monthly_csv(year, month)

        # Load CSV data
        df = pd.read_csv(file_path, na_values=['-'])

        # Get selected date
        selected_date = f"{year}-{month:02d}-{day:02d}"

        if selected_date in df["Date"].values:
            latest_entry = df[df["Date"] == selected_date].iloc[0]
            for col in self.expense_fields:
                value = latest_entry[col] if col in latest_entry and pd.notna(latest_entry[col]) else ""
                self.expense_fields[col].setText(str(value))

            # Update total labels
            self.update_totals(float(latest_entry["Total (AED)"]), float(latest_entry["Total (INR)"]))

        # Update monthly total
        if "Total (AED)" in df.columns:
            monthly_total = df["Total (AED)"].sum() - (df["Total (AED)"].sum())/2
            self.monthly_total_label.setText(f"Monthly Expense (AED): {monthly_total:.2f}")

    def save_expenses(self):
        year = int(self.year_box.currentText())
        month = self.month_box.currentIndex() + 1
        day = int(self.day_box.currentText())
        file_path = create_monthly_csv(year, month)

        # Read existing data
        df = pd.read_csv(file_path)

        # Get selected date
        selected_date = f"{year}-{month:02d}-{day:02d}"
        selected_day_name = datetime(year, month, day).strftime('%A')

        # Collect expense data
        expense_data = [selected_date, selected_day_name]
        for col in COLUMNS[2:-2]:
            value = self.expense_fields[col].text().strip()
            try:
                expense_data.append(float(value) if value else 0)
            except ValueError:
                expense_data.append(0)  # Default to 0 if invalid input

        # Calculate totals for the entered row
        total_aed = sum(expense_data[2:])
        total_inr = total_aed * AED_TO_INR
        expense_data.append(total_aed)
        expense_data.append(total_inr)

        # Update existing row for the selected date instead of deleting it
        if selected_date in df["Date"].values:
            df.loc[df["Date"] == selected_date, COLUMNS[2:]] = expense_data[2:]
        else:
            df.loc[len(df)] = expense_data  # Append new row if the date does not exist

        # Ensure "TOTAL" is removed before recalculating
        df = df[df["Date"] != "TOTAL"]

        # Calculate total row values correctly
        total_values = [df[col].sum() if col in df.columns and col not in ["Date", "Day"] else "-" for col in COLUMNS]
        new_total_row = ["TOTAL", "-"] + total_values[2:]

        # Append "TOTAL" at the bottom
        df.loc[len(df)] = new_total_row

        # Save in a separate thread to avoid UI freezing
        threading.Thread(target=self.save_file, args=(df, file_path), daemon=True).start()

        # Update UI
        self.update_totals(total_aed, total_inr)
        self.status_label.setText(f"Saved! Total (AED): {total_aed:.2f} | Total (INR): {total_inr:.2f}")

    def show_expense_graph(self):
        """Generates and displays the bar graph of daily expenses for the selected month."""
        year = int(self.year_box.currentText())
        month = self.month_box.currentIndex() + 1
        file_path = create_monthly_csv(year, month)

        df = pd.read_csv(file_path)
        df = df[df["Date"] != "TOTAL"]  # Remove TOTAL row if exists

        plt.figure(figsize=(10, 5))
        plt.bar(df["Date"], df["Total (AED)"].astype(float), color='blue')
        plt.xlabel("Date")
        plt.ylabel("Total Expense (AED)")
        plt.title(f"Daily Expenses for {self.month_box.currentText()} {year}")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()
    
    def save_file(self, df, file_path):
        """Save the DataFrame to CSV."""
        df.to_csv(file_path, index=False)

    def update_totals(self, total_aed=0, total_inr=0):
        """Updates the total display."""
        self.total_label.setText(f"Total (AED): {total_aed:.2f} | Total (INR): {total_inr:.2f}")

    def save_expense_graph(self):
        """Saves the expense graph as an image."""
        year = int(self.year_box.currentText())
        month = self.month_box.currentIndex() + 1
        file_path = create_monthly_csv(year, month)

        df = pd.read_csv(file_path)
        df = df[df["Date"] != "TOTAL"]

        plt.figure(figsize=(10, 5))
        plt.bar(df["Date"], df["Total (AED)"].astype(float), color='blue')
        plt.xlabel("Date")
        plt.ylabel("Total Expense (AED)")
        plt.title(f"Daily Expenses for {self.month_box.currentText()} {year}")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "PNG Files (*.png);;JPEG Files (*.jpg)")
        if save_path:
            plt.savefig(save_path)
            self.status_label.setText(f"Graph saved to {save_path}")
        plt.close()

if __name__ == '__main__':
    app = QApplication([])
    window = HomeExpenseApp()
    window.show()
    app.exec()
