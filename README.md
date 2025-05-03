# 📱 Mobile Tracer Tool

A professional desktop GUI tool to trace mobile numbers globally, built using **Python**, **PyQt5**, and **Folium**. This tool helps identify the **country**, **carrier**, **state**, **city**, and **coordinates** of any mobile number (especially detailed support for Indian numbers).



---

## 🔍 Features

- ✅ Trace phone numbers globally using `phonenumbers` and OpenCage API
- 🏙️ Accurate state and city info for Indian numbers via prefix mapping
- 🌐 Interactive map visualization (OpenStreetMap, Terrain, Toner, etc.)
- 🚩 Country flag display based on phone number region
- 🧵 Multithreaded background processing (no UI freeze)
- 🕵️ History tab with search and export options
- 🌙 Dark mode toggle for better UI comfort

---

## 🛠️ Technologies Used

- Python 3.x
- PyQt5 (for GUI)
- PyQtWebEngine (for map rendering)
- phonenumbers (number parsing and carrier lookup)
- Folium (map creation)
- requests (HTTP requests)
- JSON (for Indian prefix data)

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/mobile-tracer-tool.git
cd mobile-tracer-tool
```
Install dependencies:-
```bash
pip install -r requirements.txt
```
Add your OpenCage API Key
Open main.py File and replace with your Opencage API Key
```bash
OPENCAGE_API_KEY = "YOUR_OPENCAGE_API_KEY"
```
 Running the Application:-
 ```bash
python main.py

 
