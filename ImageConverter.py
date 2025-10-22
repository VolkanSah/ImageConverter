# Image Converter (WebP to JPG/PNG)
# Copyright Volkan Sah & Gemini 2.5 Flash!
# https://github.com/VolkanSah/ImageConverter/

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFileDialog, QLineEdit, QCheckBox, QLabel, 
    QTabWidget, QMessageBox, QGroupBox, QRadioButton, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PIL import Image
from pathlib import Path

# --- Konvertierungslogik in einen Thread ausgelagert ---

class ConversionWorker(QThread):
    """
    Klasse, um die zeitaufwendige Konvertierung in einem separaten Thread
    auszuführen, damit die UI nicht einfriert (Non-Blocking UI).
    """
    conversion_finished = Signal(int, int) # Erfolgreich, Total
    log_message = Signal(str)

    def __init__(self, file_paths, target_format, jpg_quality=100):
        super().__init__()
        self.file_paths = file_paths
        self.target_format = target_format
        self.jpg_quality = jpg_quality
        self.output_folder = Path.home() / "WebP_Converted" # Standardordner

    def webp_to_png(self, input_path, output_path):
        """Verlustfrei WebP → PNG mit max Kompression (PIL-Methode)."""
        img = Image.open(input_path)
        img.save(output_path, 'PNG', compress_level=9)

    def webp_to_jpg(self, input_path, output_path):
        """WebP → JPG mit optionalem weißen Hintergrund für Transparenz."""
        img = Image.open(input_path)
        
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            
            if img.mode == 'RGBA':
                # Fügt das Bild mit Alphakanal als Maske auf dem Hintergrund ein
                background.paste(img, mask=img.split()[-1])
            else:
                 background.paste(img)
            img = background
        
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Speichern mit konfigurierbarer Qualität (vom UI-Eingabefeld)
        img.save(output_path, 'JPEG', quality=self.jpg_quality, subsampling=0)

    def run(self):
        """Die Haupt-Konvertierungsschleife im Thread."""
        self.output_folder.mkdir(exist_ok=True)
        successful_conversions = 0
        total_files = len(self.file_paths)
        
        self.log_message.emit(f"Starte Konvertierung von {total_files} Dateien nach {self.target_format}...")
        self.log_message.emit(f"Zielordner: {self.output_folder}")

        converter_func = self.webp_to_png if self.target_format == 'PNG' else self.webp_to_jpg

        for input_path_str in self.file_paths:
            input_path = Path(input_path_str)
            if input_path.suffix.lower() != '.webp':
                self.log_message.emit(f"Skipping: {input_path.name} (Not WebP)")
                continue

            try:
                # Neuen Output-Pfad generieren
                output_suffix = '.' + self.target_format.lower()
                output_path = self.output_folder / (input_path.stem + output_suffix)

                converter_func(input_path, output_path)
                successful_conversions += 1
                self.log_message.emit(f"✓ {input_path.name} -> {output_path.name}")

            except Exception as e:
                self.log_message.emit(f"❌ Fehler bei {input_path.name}: {e}")

        self.log_message.emit("--- Konvertierung abgeschlossen ---")
        self.conversion_finished.emit(successful_conversions, total_files)

# --- Haupt-UI-Klasse ---

class WebPConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 WebP Batch Converter 🖼️")
        self.setGeometry(100, 100, 700, 500)
        
        # Interner Speicher für die Dateipfade
        self.file_paths = [] 
        self.worker = None

        self._setup_ui()

    def _setup_ui(self):
        # Zentrales Widget und Layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # 1. Datei-Auswahl
        file_group = QGroupBox("1. WebP-Dateien auswählen")
        file_layout = QHBoxLayout()
        
        self.file_list_edit = QLineEdit("No files selected")
        self.file_list_edit.setReadOnly(True)
        
        select_button = QPushButton("Dateien wählen...")
        select_button.clicked.connect(self.select_files)
        
        file_layout.addWidget(self.file_list_edit)
        file_layout.addWidget(select_button)
        file_group.setLayout(file_layout)
        
        main_layout.addWidget(file_group)

        # 2. Optionen
        options_group = QGroupBox("2. Ausgabeformat & Optionen")
        options_layout = QHBoxLayout()
        
        # Format-Radio Buttons
        format_group = QGroupBox("Zielformat")
        format_layout = QVBoxLayout()
        self.png_radio = QRadioButton("PNG (Verlustfrei, Transparenz erhalten)")
        self.jpg_radio = QRadioButton("JPG (Beste Qualität, Transparenz zu Weiß)")
        self.png_radio.setChecked(True)
        format_layout.addWidget(self.png_radio)
        format_layout.addWidget(self.jpg_radio)
        format_group.setLayout(format_layout)

        # JPG-Optionen
        jpg_options_group = QGroupBox("JPG-Einstellungen (Wenn gewählt)")
        jpg_options_layout = QHBoxLayout()
        jpg_options_layout.addWidget(QLabel("Qualität (1-100):"))
        self.jpg_quality_spinbox = QSpinBox()
        self.jpg_quality_spinbox.setRange(1, 100)
        self.jpg_quality_spinbox.setValue(100)
        jpg_options_layout.addWidget(self.jpg_quality_spinbox)
        jpg_options_group.setLayout(jpg_options_layout)

        options_layout.addWidget(format_group)
        options_layout.addWidget(jpg_options_group)
        options_layout.addStretch(1) # Stretch fügt leeren Raum hinzu
        options_group.setLayout(options_layout)
        
        main_layout.addWidget(options_group)

        # 3. Konvertieren Button
        self.convert_button = QPushButton("3. STARTE KONVERTIERUNG")
        self.convert_button.setFixedHeight(50)
        self.convert_button.setStyleSheet("font-size: 18px; font-weight: bold; background-color: #2ECC71; color: white;")
        self.convert_button.clicked.connect(self.start_conversion)
        main_layout.addWidget(self.convert_button)

        # 4. Log
        log_group = QGroupBox("Log / Ausgabe")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        main_layout.addWidget(log_group)
        
        self.setCentralWidget(central_widget)

    def select_files(self):
        """Öffnet den Dateidialog zur Auswahl mehrerer WebP-Dateien."""
        # Dateidialog öffnen, nur .webp erlauben
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "WebP-Dateien auswählen", 
            "", 
            "WebP Files (*.webp)"
        )
        
        if files:
            self.file_paths = files
            self.file_list_edit.setText(f"{len(files)} Dateien ausgewählt.")
            self.log_text.append(f"Ausgewählt: {len(files)} WebP-Dateien.")
        else:
            self.file_paths = []
            self.file_list_edit.setText("No files selected")

    def start_conversion(self):
        """Startet den Konvertierungsprozess im Hintergrund-Thread."""
        if not self.file_paths:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie zuerst WebP-Dateien aus.")
            return
        
        # Format bestimmen
        target_format = 'PNG' if self.png_radio.isChecked() else 'JPG'
        
        # JPG Qualität holen
        jpg_quality = self.jpg_quality_spinbox.value()

        # Konvertierungsthread initialisieren und starten
        self.convert_button.setEnabled(False) # Deaktiviert den Button während der Konvertierung
        self.convert_button.setText("Konvertiert... Bitte warten...")
        
        self.worker = ConversionWorker(self.file_paths, target_format, jpg_quality)
        self.worker.log_message.connect(self.log_text.append)
        self.worker.conversion_finished.connect(self.conversion_finished)
        self.worker.start()

    def conversion_finished(self, successful, total):
        """Wird aufgerufen, wenn der Konvertierungsthread fertig ist."""
        self.convert_button.setEnabled(True)
        self.convert_button.setText("3. STARTE KONVERTIERUNG")
        
        # Log-Nachricht
        if successful == total and successful > 0:
            msg = f"✅ Alle {successful} Dateien erfolgreich konvertiert! (Zielordner: ~/WebP_Converted)"
            QMessageBox.information(self, "Erfolg", msg)
        elif successful > 0:
             msg = f"⚠️ {successful} von {total} Dateien erfolgreich konvertiert. Ergebnisse im Ordner ~/WebP_Converted"
             QMessageBox.warning(self, "Teilweise erfolgreich", msg)
        else:
             msg = "❌ Konvertierung fehlgeschlagen oder keine WebP-Dateien gefunden."
             QMessageBox.critical(self, "Fehler", msg)
             
        self.log_text.append(msg)
        
        # Zurücksetzen für neue Konvertierung
        self.file_paths = []
        self.file_list_edit.setText("No files selected")


# --- Anwendung starten ---

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebPConverterApp()
    window.show()
    sys.exit(app.exec())
