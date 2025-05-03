import os
import sys
import json
import requests
import phonenumbers
from datetime import datetime
from phonenumbers import geocoder, carrier
from PyQt5.QtCore import Qt, QUrl, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFileDialog, QCheckBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium

# Configuration
OPENCAGE_API_KEY = "4c462d585f0646c4bfbe906073ec6701"
FLAG_URL_TEMPLATE = "https://flagcdn.com/64x48/{code}.png"
MAP_FILE = os.path.abspath("trace_map.html")

# Load Indian prefix mappings
prefix_file = os.path.join(os.path.dirname(__file__), 'india_prefixes.json')
with open(prefix_file, 'r', encoding='utf-8') as f:
    INDIA_PREFIXES = json.load(f)

# Thread signals
class WorkerSignals(QObject):
    result = pyqtSignal(dict)
    error = pyqtSignal(str)

class TraceWorker(QRunnable):
    def __init__(self, number, zoom, style):
        super().__init__()
        self.signals = WorkerSignals()
        self.number = number
        self.zoom = zoom
        self.style = style

    @pyqtSlot()
    def run(self):
        try:
            parsed = phonenumbers.parse(self.number)
            country = geocoder.description_for_number(parsed, "en")
            sim = carrier.name_for_number(parsed, "en")
            national = str(parsed.national_number)
            prefix = national[:3]

            state, city = "", ""
            if parsed.country_code == 91 and prefix in INDIA_PREFIXES:
                city, state = INDIA_PREFIXES[prefix]

            location_query = f"{city or country}, {state}".strip(', ')
            coords = self.get_coordinates(location_query)

            lat, lon = coords if coords else ("", "")
            if coords:
                self.create_map(float(lat), float(lon))
            self.signals.result.emit({
                "number": self.number, "country": country, "carrier": sim,
                "state": state, "city": city, "lat": lat, "lon": lon,
                "country_code": parsed.country_code
            })
        except Exception as e:
            self.signals.error.emit(str(e))

    def get_coordinates(self, location):
        try:
            response = requests.get(
                f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={OPENCAGE_API_KEY}"
            )
            data = response.json()
            if data["results"]:
                geo = data["results"][0]["geometry"]
                return geo["lat"], geo["lng"]
        except:
            return None
        return None

    def create_map(self, lat, lon):
        m = folium.Map(location=[lat, lon], zoom_start=self.zoom, tiles=self.style)
        folium.Marker([lat, lon], popup="Phone Location").add_to(m)
        m.save(MAP_FILE)

class MobileTracerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mobile Tracer Tool")
        self.setGeometry(100, 100, 800, 600)
        self.history = []
        self.thread_pool = QThreadPool()
        self.init_ui()

    def init_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self.build_tracer_tab(), "Tracer")
        tabs.addTab(self.build_history_tab(), "History")
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(tabs)

    def build_tracer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Mobile # (+Country Code):"))
        self.input = QLineEdit()
        input_layout.addWidget(self.input)
        layout.addLayout(input_layout)

        option_layout = QHBoxLayout()
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(map(str, range(3, 18)))
        self.zoom_combo.setCurrentText("6")
        self.style_combo = QComboBox()
        self.style_combo.addItems(["OpenStreetMap", "Stamen Toner", "Stamen Terrain", "CartoDB positron"])
        option_layout.addWidget(QLabel("Zoom:"))
        option_layout.addWidget(self.zoom_combo)
        option_layout.addWidget(QLabel("Style:"))
        option_layout.addWidget(self.style_combo)
        layout.addLayout(option_layout)

        button_layout = QHBoxLayout()
        trace_btn = QPushButton("Trace")
        trace_btn.clicked.connect(self.start_trace)
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_history)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_history)
        button_layout.addWidget(trace_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(clear_btn)
        layout.addLayout(button_layout)

        self.flag_label = QLabel()
        self.flag_label.setFixedSize(64, 48)
        layout.addWidget(self.flag_label)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        self.dark_toggle = QCheckBox("Dark Mode")
        self.dark_toggle.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_toggle)

        return tab

    def build_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Time", "Number", "Country", "Carrier", "State", "City", "Lat", "Lon"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        return tab

    def start_trace(self):
        number = self.input.text().strip()
        if not number:
            QMessageBox.warning(self, "Input Error", "Please enter a mobile number.")
            return

        zoom = int(self.zoom_combo.currentText())
        style = self.style_combo.currentText()

        worker = TraceWorker(number, zoom, style)
        worker.signals.result.connect(self.display_result)
        worker.signals.error.connect(self.show_error)
        self.output.setText("Tracing in progress...")
        self.thread_pool.start(worker)

    def display_result(self, data):
        txt = "".join(f"{k.capitalize()}: {v}\n" for k, v in data.items() if k != 'country_code')
        self.output.setText(txt)

        if data["lat"] and data["lon"]:
            self.map_view.load(QUrl.fromLocalFile(MAP_FILE))
        else:
            self.map_view.setHtml("<h3 style='color:red;'>Location not found</h3>")

        self.show_flag(data["country_code"])
        entry = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **data}
        self.history.append(entry)
        self.refresh_history_table()

    def show_error(self, msg):
        self.output.setText(f"Error: {msg}")
        QMessageBox.critical(self, "Trace Error", msg)

    def show_flag(self, country_code):
        regions = phonenumbers.phonenumberutil.COUNTRY_CODE_TO_REGION_CODE.get(country_code, [])
        if not regions:
            self.flag_label.clear()
            return
        code = regions[0].lower()
        try:
            img = requests.get(FLAG_URL_TEMPLATE.format(code=code)).content
            pix = QPixmap()
            pix.loadFromData(img)
            self.flag_label.setPixmap(pix)
        except:
            self.flag_label.clear()

    def refresh_history_table(self):
        self.table.setRowCount(len(self.history))
        for r, entry in enumerate(self.history):
            for c, key in enumerate(["time", "number", "country", "carrier", "state", "city", "lat", "lon"]):
                self.table.setItem(r, c, QTableWidgetItem(str(entry.get(key, ""))))

    def export_history(self):
        if not self.history:
            QMessageBox.information(self, "Export", "No history to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save History", "", "JSON Files (*.json)")
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4)
            QMessageBox.information(self, "Export", "History exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def clear_history(self):
        self.history.clear()
        self.refresh_history_table()
        self.output.clear()
        self.map_view.setHtml("")
        self.flag_label.clear()

    def toggle_dark_mode(self, state):
        if state == Qt.Checked:
            self.setStyleSheet("QWidget { background-color: #2e2e2e; color: white; }")
        else:
            self.setStyleSheet("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MobileTracerApp()
    window.show()
    sys.exit(app.exec_())
