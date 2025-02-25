#-*- encoding: utf-8 -*-

import sys
import os
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, 
    QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QMenuBar, 
    QMenu, QFrame, QSizePolicy, QMessageBox, QFileDialog, QDialog,
    QCalendarWidget, QProgressBar
)
from PySide6.QtCore import (
    Qt, __version__, QSettings, QDate, QSize, QUrl, QTimer
)
from PySide6.QtGui import (
    QKeySequence, QPixmap, QPainter, QPageSize, QPageLayout
)
from PySide6.QtPrintSupport import (
    QPrinter, QPrintDialog, QPrintPreviewDialog
)
from PIL import Image, ImageDraw, ImageFont
import tempfile

# Add at the top of the file with other imports
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class PrintHandler:
    def __init__(self, parent):
        self.parent = parent
    
    def print_preview(self):
        # Create printer with fixed A4 Landscape settings
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPageLayout.Landscape)
        printer.setPageSize(QPageSize(QPageSize.A4))
        
        # Create and show preview dialog with native dialogs disabled
        preview = QPrintPreviewDialog(printer, self.parent)
        preview.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  # Custom window flags
        preview.paintRequested.connect(self.parent.handle_paint_request)
        preview.setWindowTitle("Print Preview")  # Custom title
        
        # Set options for all print dialogs in the preview
        for dialog in preview.findChildren(QPrintDialog):
            dialog.setOption(QPrintDialog.PrintToFile)
        
        preview.exec()

from PySide6.QtCore import QSettings

# Add this after the imports
app_name = "CarForm"
organization_name = "amaterasuqbb"
QSettings.setDefaultFormat(QSettings.IniFormat)
QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, ".")

class FieldGroup(QFrame):
    def __init__(self, base_label: str, count: int):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.fields = []
        self.visible_count = 1
        
        # Calculate label width for alignment
        max_label_width = max(len(f"{base_label}{i+1 if i > 0 else ''}:") for i in range(count))
        
        for i in range(count):
            container = QWidget()
            item_layout = QHBoxLayout(container)
            item_layout.setSpacing(5)
            item_layout.setContentsMargins(0, 0, 0, 0)
            
            label = QLabel(f"{base_label}{i+1 if i > 0 else ''}:")
            # Set fixed width for labels to align fields
            label.setMinimumWidth(100)
            
            field = QLineEdit()
            field.setMinimumWidth(200)  # Set minimum width for consistent sizing
            add_btn = QPushButton("Add")
            remove_btn = QPushButton("Remove")
            
            # Set size policies
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            add_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            remove_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            # Set fixed sizes for buttons
            add_btn.setFixedWidth(60)
            remove_btn.setFixedWidth(60)
            
            # Set fixed heights
            field.setFixedHeight(25)
            add_btn.setFixedHeight(25)
            remove_btn.setFixedHeight(25)
            
            # Disable remove button for the first item
            if i == 0:
                remove_btn.setEnabled(False)
            
            item_layout.addWidget(label)
            item_layout.addWidget(field)
            item_layout.addWidget(add_btn)
            item_layout.addWidget(remove_btn)
            
            self.layout.addWidget(container)
            self.fields.append((container, field, item_layout))
            
            add_btn.clicked.connect(lambda checked, idx=i: self.add_field(idx))
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_field(idx))
            
            # Hide all fields except the first one initially
            if i > 0:
                container.hide()

    def add_field(self, index):
        if index < len(self.fields) - 1:
            self.visible_count += 1
            self.fields[index + 1][0].show()
            self.updateGeometry()
            self.parent().parent().adjustSize()

    def remove_field(self, index):
        if index == 0:
            return
            
        if index < len(self.fields):
            self.visible_count -= 1
            self.fields[index][0].hide()
            self.updateGeometry()
            self.parent().parent().adjustSize()

    def sizeHint(self):
        height = sum(field[0].sizeHint().height() for field in self.fields if field[0].isVisible())
        return self.layout.sizeHint()

class CarForm(QMainWindow):
    def __init__(self):
        super().__init__()
        # Fix icon loading
        icon = QPixmap(resource_path("CarForm_amaterasuqbb_icon.ico"))
        self.setWindowIcon(icon)
        
        # Rest of your initialization code...
        QApplication.setOrganizationName(organization_name)
        QApplication.setApplicationName(app_name)
        
        # Only enable close button, disable minimize
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint  # Only enable close button
        )
        
        self.setWindowTitle("CarForm")
        self.setMinimumWidth(500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.create_menu_bar()
        
        # Registration form
        form_box = QFrame()
        form_box.setFrameStyle(QFrame.StyledPanel)
        form_layout = QGridLayout()
        form_layout.setSpacing(5)
        form_layout.setContentsMargins(5, 5, 5, 5)
        
        placeholders = {
            "Registration number:": "富士山 300 り 8888",
            "Model number:": "AA100A-1001001",
            "Travel distance:": "0",
            "Checked year:": "20250101",
            "Checked month:": "01",
            "Checked day:": "01",
            "Maintained year:": "20250202",
            "Maintained month:": "02",
            "Maintained day:": "02"
        }
        
        self.form_fields = {}
        for i, (label_text, placeholder) in enumerate(placeholders.items()):
            label = QLabel(label_text)
            label.setMinimumWidth(100)  # Set fixed width for labels
            
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setFixedHeight(25)
            field.setMinimumWidth(200)  # Set minimum width for consistent sizing
            
            # Set up automatic conversion for the field
            self.setup_form_field(field)
            
            self.form_fields[label_text] = field
            if "year" in label_text.lower():
                field_container = QWidget()
                field_layout = QHBoxLayout(field_container)
                field_layout.setContentsMargins(0, 0, 0, 0)
                field_layout.setSpacing(5)
                
                calendar_btn = QPushButton("📅")  # Calendar emoji as button text
                calendar_btn.setFixedWidth(30)
                calendar_btn.setFixedHeight(25)
                
                auto_fill = QPushButton("Auto fill")
                auto_fill.setFixedHeight(25)
                auto_fill.setFixedWidth(60)
                
                field_layout.addWidget(field)
                field_layout.addWidget(calendar_btn)
                field_layout.addWidget(auto_fill)
                
                form_layout.addWidget(label, i, 0)
                form_layout.addWidget(field_container, i, 1)
                
                # Connect calendar button
                if "Checked" in label_text:
                    calendar_btn.clicked.connect(
                        lambda _, f=field: self.show_calendar_dialog(
                            f,
                            self.form_fields["Checked month:"],
                            self.form_fields["Checked day:"]
                        )
                    )
                    auto_fill.clicked.connect(lambda _, f=field: self.auto_fill_checked_date(f))
                else:  # Maintained
                    calendar_btn.clicked.connect(
                        lambda _, f=field: self.show_calendar_dialog(
                            f,
                            self.form_fields["Maintained month:"],
                            self.form_fields["Maintained day:"]
                        )
                    )
                    auto_fill.clicked.connect(lambda _, f=field: self.auto_fill_maintained_date(f))
            else:
                form_layout.addWidget(label, i, 0)
                form_layout.addWidget(field, i, 1)
        
        form_box.setLayout(form_layout)
        layout.addWidget(form_box)
        
        self.looked_items = FieldGroup("Looked items", 9)
        self.parts_replacement = FieldGroup("Parts replacement", 5)
        layout.addWidget(self.looked_items)
        layout.addWidget(self.parts_replacement)
        
        # Apply conversion to FieldGroup fields
        for container, field, _ in self.looked_items.fields:
            self.setup_form_field(field)
        
        for container, field, _ in self.parts_replacement.fields:
            self.setup_form_field(field)
        
        print_btn = QPushButton("Print")
        print_btn.setFixedHeight(25)
        layout.addWidget(print_btn)
        
        print_btn.clicked.connect(self.print_to_pdf)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = file_menu.addAction("New")
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        
        save_action = file_menu.addAction("Save")
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        
        print_action = file_menu.addAction("Print")
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.triggered.connect(self.print_to_pdf)
        
        pref_action = file_menu.addAction("Preference")
        pref_action.setShortcut(QKeySequence("Ctrl+,"))
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        
        # Update file menu connections
        new_action.triggered.connect(self.show_new_confirmation)
        save_action.triggered.connect(self.save_file)
        exit_action.triggered.connect(self.show_exit_confirmation)
        pref_action.triggered.connect(self.show_preferences)

        # View menu
        view_menu = menubar.addMenu("View")
        
        # Reset pane action with proper shortcut setup
        reset_pane_action = view_menu.addAction("Reset pane")
        reset_pane_action.setShortcut("Ctrl+D")  # Changed from QKeySequence to string
        reset_pane_action.triggered.connect(self.center_window)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

    def show_new_confirmation(self):
        """ New Creation Confirmation Dialog """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("New")
        msg_box.setText("Do you want to save changes before creating a new form?")
        msg_box.setIcon(QMessageBox.Question)
        
        save_button = msg_box.addButton("Save", QMessageBox.AcceptRole)
        discard_button = msg_box.addButton("Don't Save", QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(save_button)
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == save_button:
            self.save_file()
            # Don't reset form if save was cancelled or failed
        elif clicked_button == discard_button:
            self.reset_form()
        # Do nothing if Cancel was clicked, allowing user to continue editing

    def show_exit_confirmation(self):
        """Confirmation dialog when exiting the application"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Exit")
        msg_box.setText("Do you want to save changes before exiting?")
        msg_box.setIcon(QMessageBox.Question)
        
        save_button = msg_box.addButton("Save", QMessageBox.AcceptRole)
        discard_button = msg_box.addButton("Don't Save", QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(save_button)
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == save_button:
            # Only close if save was successful
            if self.save_file():
                self.close()
        elif clicked_button == discard_button:
            self.close()
        # Do nothing if Cancel was clicked, allowing user to continue editing

    def check_all_fields_filled(self):
        """Check if all visible fields are filled"""
        # Check main form fields
        for field in self.form_fields.values():
            if not field.text().strip():
                return False
        
        # Check looked items
        for container, field, _ in self.looked_items.fields:
            if container.isVisible() and not field.text().strip():
                return False
        
        # Check parts replacement
        for container, field, _ in self.parts_replacement.fields:
            if container.isVisible() and not field.text().strip():
                return False
        
        return True

    def export_csv(self, file_name):
        """Export form data to CSV with Japanese text support"""
        try:
            # Prepare headers
            headers = ['Item', 'Value']
            
            # Collect all data
            rows = []
            
            # Add preference fields first (A13-B13)
            settings = QSettings()
            preference_fields = [
                ("Business name", settings.value("business_name", "")),
                ("Address", settings.value("address", "")),
                ("Telephone number", settings.value("phone_number", "")),
                ("Cellphone number", settings.value("cellphone_number", ""))
            ]
            rows.extend(preference_fields)
            
            # Add main form fields
            for label, field in self.form_fields.items():
                rows.append([label.strip(':'), field.text()])
            
            # Add looked items
            for i, (container, field, _) in enumerate(self.looked_items.fields):
                if container.isVisible():
                    label = f"Looked item{i+1 if i > 0 else ''}"
                    rows.append([label, field.text()])
            
            # Add parts replacement
            for i, (container, field, _) in enumerate(self.parts_replacement.fields):
                if container.isVisible():
                    label = f"Parts replacement{i+1 if i > 0 else ''}"
                    rows.append([label, field.text()])
            
            # Write CSV file
            import csv
            with open(file_name, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                # Write header
                writer.writerow(headers)
                # Write data rows
                writer.writerows(rows)
                
            QMessageBox.information(
                self,
                "Success",
                "Data exported successfully."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Export failed: {str(e)}"
            )

    def save_file(self):
        """Save File"""
        if not self.check_all_fields_filled():
            QMessageBox.warning(self, "Warning", "Please fill in all fields before saving.")
            return False

        # Generate timestamp-based filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        default_filename = f"CarForm_{timestamp}.csv"
        
        # Get the desktop path
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        full_path = os.path.join(desktop, default_filename)

        # Create file dialog with PySide6 style
        file_dialog = QFileDialog(self)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog)  # Force PySide6 dialog
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)  # Set to Save mode
        file_dialog.setDefaultSuffix("csv")  # Set default suffix
        file_dialog.setNameFilter("CSV Files (*.csv);;All Files (*)")  # Set filters
        file_dialog.setDirectory(desktop)  # Set initial directory
        file_dialog.selectFile(default_filename)  # Set default filename

        if file_dialog.exec() == QFileDialog.Accepted:
            file_name = file_dialog.selectedFiles()[0]
            if not file_name.lower().endswith('.csv'):
                file_name += '.csv'
            return self.export_csv(file_name)
        return False

    def save_form_data(self, file_name):
        """ Save form data """
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                # Save form fields
                for label, field in self.form_fields.items():
                    f.write(f"{label}: {field.text()}\n")
                
                # Save looked items
                for container, field, _ in self.looked_items.fields:
                    if container.isVisible():
                        f.write(f"Looked item: {field.text()}\n")
                
                # Save parts replacement
                for container, field, _ in self.parts_replacement.fields:
                    if container.isVisible():
                        f.write(f"Parts replacement: {field.text()}\n")
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def reset_form(self):
        """ Reset Form """
        # Clear all form fields
        for field in self.form_fields.values():
            field.clear()
        
        # Reset looked items
        for container, field, _ in self.looked_items.fields:
            field.clear()  # Clear the field content
            if container != self.looked_items.fields[0][0]:  # If not the first container
                container.hide()  # Hide additional containers
        self.looked_items.visible_count = 1
        
        # Reset parts replacement
        for container, field, _ in self.parts_replacement.fields:
            field.clear()  # Clear the field content
            if container != self.parts_replacement.fields[0][0]:  # If not the first container
                container.hide()  # Hide additional containers
        self.parts_replacement.visible_count = 1
        
        # Adjust window size after clearing
        self.adjustSize()

    def print_form(self):
        print("Printing form...")

    def auto_fill_checked_date(self, year_field):
        """Auto fill checked date fields"""
        try:
            full_date = year_field.text()
            if len(full_date) == 8:  # Format: YYYYMMDD
                year = full_date[:4]
                month = full_date[4:6]
                day = full_date[6:]
                
                # Update fields
                year_field.setText(year)
                self.form_fields["Checked month:"].setText(month)
                self.form_fields["Checked day:"].setText(day)
        except Exception as e:
            QMessageBox.warning(self, "Warning", "Invalid date format. Please use YYYYMMDD format.")

    def auto_fill_maintained_date(self, year_field):
        """Auto fill maintained date fields"""
        try:
            full_date = year_field.text()
            if len(full_date) == 8:  # Format: YYYYMMDD
                year = full_date[:4]
                month = full_date[4:6]
                day = full_date[6:]
                
                # Update fields
                year_field.setText(year)
                self.form_fields["Maintained month:"].setText(month)
                self.form_fields["Maintained day:"].setText(day)
        except Exception as e:
            QMessageBox.warning(self, "Warning", "Invalid date format. Please use YYYYMMDD format.")

    def show_about_dialog(self):
        """Show About dialog similar to winver"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        dialog.setWindowTitle("About CarForm")
        dialog.setFixedSize(600, 700)  # Increased height to show all content
        
        # Create layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Top image (CarForm logo)
        top_image_label = QLabel()
        # Fix logo path loading
        if self.detect_system_theme():
            logo_path = QPixmap(resource_path("Darkmode_CarForm_logo.png"))
        else:
            logo_path = QPixmap(resource_path("Lightmode_CarForm_logo.png"))
            
        top_pixmap = QPixmap(logo_path)
        top_pixmap = top_pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        top_image_label.setPixmap(top_pixmap)
        top_image_label.setAlignment(Qt.AlignCenter)  # Keep image centered

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        
        # Text container widget for left alignment
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setSpacing(10)
        text_layout.setContentsMargins(40, 0, 40, 0)  # Add left and right margins
        
        # Product name without stylesheet
        product_name = QLabel("amaterasuqbb CarForm")
        product_name.setAlignment(Qt.AlignLeft)
        
        # Version info without stylesheet
        version_info = QLabel("Version 1.0.0")
        version_info.setAlignment(Qt.AlignLeft)
        
        # Add Python and Qt version info
        python_version = QLabel(f"Running on Python {sys.version.split()[0]}")
        python_version.setAlignment(Qt.AlignLeft)

        qt_version = QLabel(f"Qt Version: {__version__}")
        qt_version.setAlignment(Qt.AlignLeft)

        # Add license information with clickable link
        license_text = (
            "This file is part of CarForm.\n\n"
            "CarForm is free software; you can redistribute it and/or modify it under the terms "
            "of the GNU Lesser General Public License as published by the Free Software Foundation; "
            "either version 3 of the License, or any later version.\n\n"
            "CarForm is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; "
            "without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. "
            "See the GNU General Public License for more details.\n\n"
            "You should have received a copy of the GNU General Public License along with CarForm. "
            "If not, see <a href='https://www.gnu.org/licenses/'>https://www.gnu.org/licenses/</a>\n\n"
            "Copyright (C) amaterasuqbb, amaterasu-qbb, amaterasu_qbb, amaterasu.qbb\n"
            "Permission is granted to copy, distribute and/or modify this document "
            "under the terms of the GNU Lesser General Public License, Version 3 "
            "or any later version published by the Free Software Foundation; "
            "with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts. "
            "A copy of the license is included in the section entitled \"GNU "
            "Lesser General Public License\"."
        )

        license_info = QLabel(license_text)
        license_info.setAlignment(Qt.AlignLeft)
        license_info.setWordWrap(True)  # Enable word wrapping
        license_info.setTextFormat(Qt.RichText)  # Enable rich text
        license_info.setOpenExternalLinks(True)  # Enable clickable links

        # Add text widgets to text container
        text_layout.addWidget(product_name)
        text_layout.addWidget(version_info)
        text_layout.addWidget(python_version)
        text_layout.addWidget(qt_version)
        text_layout.addWidget(license_info)
        
        # Bottom images container
        bottom_images_container = QWidget()
        bottom_images_layout = QHBoxLayout(bottom_images_container)
        bottom_images_layout.setAlignment(Qt.AlignCenter)
        bottom_images_layout.setSpacing(20)  # Space between images
        
        # GPL license image
        gpl_label = QLabel()
        # Fix GPL logo loading
        gpl_pixmap = QPixmap(resource_path("lgplv3-with-text-154x68.png"))
        gpl_pixmap = gpl_pixmap.scaled(200, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        gpl_label.setPixmap(gpl_pixmap)
        gpl_label.setAlignment(Qt.AlignCenter)
        
        # PySide logo
        pyside_label = QLabel()
        # Fix PySide logo loading
        pyside_pixmap = QPixmap(resource_path("PySideLogo1.png"))
        pyside_pixmap = pyside_pixmap.scaled(200, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pyside_label.setPixmap(pyside_pixmap)
        pyside_label.setAlignment(Qt.AlignCenter)
        
        # Add images to container
        bottom_images_layout.addWidget(gpl_label)
        bottom_images_layout.addWidget(pyside_label)
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.setFixedWidth(100)
        ok_button.setFixedHeight(30)
        ok_button.clicked.connect(dialog.accept)
        
        # Button container for alignment
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        
        # Add widgets to main layout
        layout.addWidget(top_image_label)
        layout.addWidget(line)
        layout.addWidget(text_container)  # Add the text container
        layout.addWidget(bottom_images_container)  # Add container instead of single image
        layout.addStretch()
        layout.addWidget(button_container)
        
        # Show dialog
        dialog.exec()

    def detect_system_theme(self):
        """Detect if system is using dark mode"""
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            ) as key:
                return not winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
        except:
            return False  # Default to light mode if detection fails

    def center_window(self):
        """Center the window on the screen and reset size"""
        # Reset window size to minimum
        self.resize(self.minimumWidth(), self.minimumHeight())
        
        # Adjust size based on content
        self.adjustSize()
        
        # Get the current screen geometry
        screen = QApplication.primaryScreen().geometry()
        # Get the window geometry
        window_geometry = self.frameGeometry()
        # Calculate center point
        center_point = screen.center()
        # Move window's center point to screen's center point
        window_geometry.moveCenter(center_point)
        # Move window to new position
        self.move(window_geometry.topLeft())

    def convert_fullwidth_to_halfwidth(self, text):
        """Convert full-width numerics, alphabets and spaces to half-width while preserving other characters"""
        # Full-width to half-width mapping for numbers, alphabets (upper and lower) and space
        fw_chars = ('０１２３４５６７８９' +  # Numbers
                   'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ' +  # Lowercase
                   'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ' +  # Uppercase
                   '　')  # Full-width space
        hw_chars = ('0123456789' +  # Numbers
                   'abcdefghijklmnopqrstuvwxyz' +  # Lowercase
                   'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +  # Uppercase
                   ' ')  # Half-width space
        
        # Create translation table
        fw_to_hw = str.maketrans(fw_chars, hw_chars)
        return text.translate(fw_to_hw)

    def setup_form_field(self, field):
        """Set up form field with character conversion"""
        def on_text_changed():
            cursor_pos = field.cursorPosition()
            text = field.text()
            new_text = self.convert_fullwidth_to_halfwidth(text)
            if new_text != text:
                field.setText(new_text)
                field.setCursorPosition(cursor_pos)
        
        field.textChanged.connect(on_text_changed)

    def show_calendar_dialog(self, year_field, month_field, day_field):
        """Show calendar dialog and update date fields"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date")
        layout = QVBoxLayout(dialog)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        
        # Set current date from fields if they exist
        try:
            year = int(year_field.text() if year_field.text() else calendar.selectedDate().year())
            month = int(month_field.text() if month_field.text() else calendar.selectedDate().month())
            day = int(day_field.text() if day_field.text() else calendar.selectedDate().day())
            calendar.setSelectedDate(QDate(year, month, day))
        except ValueError:
            pass  # Use default date if conversion fails
        
        layout.addWidget(calendar)
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)
        
        if dialog.exec() == QDialog.Accepted:
            selected_date = calendar.selectedDate()

            # Update year field with four-digit year
            year_field.setText(f"{selected_date.year()}")  # Convert year to string
            month_field.setText(f"{selected_date.month():02d}")  # Zero-padded month
            day_field.setText(f"{selected_date.day():02d}")  # Zero-padded day

    def show_preferences(self):
        """Show preferences dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.setFixedSize(500, 400)
        
        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 20)  # Remove side margins for menu bar
        
        # Add menu bar
        menubar = QMenuBar()
        edit_menu = menubar.addMenu("Edit")
        restore_action = edit_menu.addAction("Restore Default Settings")
        restore_action.triggered.connect(self.restore_default_settings)
        main_layout.addWidget(menubar)
        
        # Content layout
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Business name and Address section
        general_group = QFrame()
        general_group.setFrameStyle(QFrame.StyledPanel)
        general_layout = QVBoxLayout(general_group)
        
        general_label = QLabel("Business name and Address")
        general_label.setStyleSheet("font-weight: bold;")
        general_layout.addWidget(general_label)
        
        # Business name field
        business_name_layout = QHBoxLayout()
        business_name_label = QLabel("Business name:")
        self.business_name_field = QLineEdit()  # Rename from save_location_field
        
        business_name_layout.addWidget(business_name_label)
        business_name_layout.addWidget(self.business_name_field)
        general_layout.addLayout(business_name_layout)
        
        # Add Address field
        address_layout = QHBoxLayout()
        address_label = QLabel("Address:")
        self.address_field = QLineEdit()
        
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_field)
        general_layout.addLayout(address_layout)
        
        # Add to content layout
        layout.addWidget(general_group)
        
        # Phone number section
        phone_group = QFrame()
        phone_group.setFrameStyle(QFrame.StyledPanel)
        phone_layout = QVBoxLayout(phone_group)
        
        phone_label = QLabel("Phone number")
        phone_label.setStyleSheet("font-weight: bold;")
        phone_layout.addWidget(phone_label)
        
        # Telephone number field
        tel_layout = QHBoxLayout()
        tel_label = QLabel("Telephone number:")
        self.tel_field = QLineEdit()
        
        tel_layout.addWidget(tel_label)
        tel_layout.addWidget(self.tel_field)
        phone_layout.addLayout(tel_layout)
        
        # Cellphone number field
        cel_layout = QHBoxLayout()
        cel_label = QLabel("Cellphone number:")
        self.cel_field = QLineEdit()
        
        cel_layout.addWidget(cel_label)
        cel_layout.addWidget(self.cel_field)
        phone_layout.addLayout(cel_layout)
        
        # Add to content layout
        layout.addWidget(phone_group)
        layout.addStretch()
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 0, 20, 0)  # Add side margins
        
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        # Make buttons fill the width equally
        save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        cancel_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set minimum height
        save_button.setFixedHeight(30)
        cancel_button.setFixedHeight(30)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addWidget(button_container)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        
        # Connect buttons
        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # Load saved preferences
        self.load_preferences()
        
        if dialog.exec() == QDialog.Accepted:
            self.save_preferences()

    def restore_default_settings(self):
        """Restore default settings"""
        reply = QMessageBox.question(
            self, 
            "Restore Defaults",
            "Are you sure you want to restore default settings?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear all preference fields
            self.business_name_field.clear()
            self.address_field.clear()
            self.tel_field.clear()
            self.cel_field.clear()
            
            # Clear settings in QSettings
            settings = QSettings()
            settings.remove("business_name")
            settings.remove("address")
            settings.remove("phone_number")
            settings.remove("cellphone_number")
            
            # Show confirmation
            QMessageBox.information(
                self,
                "Settings Restored",
                "All settings have been restored to defaults."
            )

    def save_preferences(self):
        """Save preferences"""
        settings = QSettings()
        settings.setValue("business_name", self.business_name_field.text())
        settings.setValue("address", self.address_field.text())
        settings.setValue("phone_number", self.tel_field.text())
        settings.setValue("cellphone_number", self.cel_field.text())
        
        # Show save confirmation
        QMessageBox.information(
            self,
            "Settings Saved",
            "Your preferences have been saved successfully.")

    def browse_save_location(self):
        """Open directory browser for default save location"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Save Location",
            self.save_location_field.text() or os.path.expanduser("~")
        )
        if directory:
            self.save_location_field.setText(directory)

    def load_preferences(self):
        """Load saved preferences"""
        settings = QSettings()
        business_name = settings.value("business_name", "")
        address = settings.value("address", "")
        self.business_name_field.setText(business_name)
        self.address_field.setText(address)
        phone_number = settings.value("phone_number", "")
        self.tel_field.setText(phone_number)
        cellphone_number = settings.value("cellphone_number", "")
        self.cel_field.setText(cellphone_number)

    def save_preferences(self):
        """Save preferences"""
        settings = QSettings()
        settings.setValue("business_name", self.business_name_field.text())
        settings.setValue("address", self.address_field.text())
        settings.setValue("phone_number", self.tel_field.text())
        settings.setValue("cellphone_number", self.cel_field.text())


    def print_to_pdf(self):
        """Print form data to PDF"""
        handler = PrintHandler(self)
        handler.print_preview()

    def handle_paint_request(self, printer):
        """Handle the print preview paint request"""
        temp_file = None
        try:
            # Create blank A4 image (3508 x 2480 pixels for 300 DPI)
            width = 3508  # A4 width at 300 DPI
            height = 2480  # A4 height at 300 DPI
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)

            # Set up font
            font_path = "msgothic.ttc"  # Japanese font
            font = ImageFont.truetype(font_path, 32)

            # Define text positions for main form fields
            form_coordinates = {
                "Registration number:": (2910, 130),
                "Model number:": (2910, 235),
                "Travel distance:": (2970, 2305),
                "Checked year:": (2970, 2115),
                "Checked month:": (3120, 2115),
                "Checked day:": (3230, 2115),
                "Maintained year:": (2970, 2210),
                "Maintained month:": (3120, 2210),
                "Maintained day:": (3230, 2210)
            }

            # Add form field values
            for label, coord in form_coordinates.items():
                if label in self.form_fields:
                    text = self.form_fields[label].text()
                    draw.text(coord, text, fill="black", font=font)

            # Add looked items
            looked_items_coordinates = [
                (2800, 541), (2800, 597), (2800, 654), (2800, 710),
                (2800, 765), (2800, 820), (2800, 876), (2800, 933), (2800, 990)
            ]
            for i, (container, field, _) in enumerate(self.looked_items.fields):
                if container.isVisible() and i < len(looked_items_coordinates):
                    draw.text(looked_items_coordinates[i], field.text(), fill="black", font=font)

            # Add parts replacement
            parts_coordinates = [
                (2800, 1373), (2800, 1430), (2800, 1486), (2800, 1543), (2800, 1598)
            ]
            for i, (container, field, _) in enumerate(self.parts_replacement.fields):
                if container.isVisible() and i < len(parts_coordinates):
                    draw.text(parts_coordinates[i], field.text(), fill="black", font=font)

            # Add business information
            settings = QSettings()
            business_info = {
                "business_name": (1515, 2183),
                "address": (1515, 2232),
                "phone_number": (1515, 2282),
                "cellphone_number": (1815, 2282)
            }
            for key, coord in business_info.items():
                text = settings.value(key, "")
                draw.text(coord, text, fill="black", font=font)

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            image.save(temp_file.name)
            temp_file.close()

            # Draw to printer
            pixmap = QPixmap(temp_file.name)
            page_rect = printer.pageRect(QPrinter.DevicePixel)
            page_size = QSize(int(page_rect.width()), int(page_rect.height()))
            
            scaled_pixmap = pixmap.scaled(
                page_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            painter = QPainter()
            if painter.begin(printer):
                try:
                    painter.drawPixmap(0, 0, scaled_pixmap)
                finally:
                    painter.end()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print: {str(e)}")
        finally:
            if temp_file:
                try:
                    painter = None
                    scaled_pixmap = None
                    pixmap = None
                    os.unlink(temp_file.name)
                except:
                    pass

if __name__ == '__main__':
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    window = CarForm()
    window.show()
    sys.exit(app.exec())