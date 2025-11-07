import sys
import os
import random
from datetime import datetime
import requests
import folium

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer

# -------------------------
# OSRM route function
# -------------------------
def get_osrm_route(start, end):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
        data = requests.get(url).json()
        coords = data['routes'][0]['geometry']['coordinates']
        return [[c[1], c[0]] for c in coords]
    except:
        return None

# -------------------------
# Map generation with simulated dustbin values
# -------------------------
def generate_map_file(filename="map.html"):
    base_station = [16.705, 74.243]
    locations = [
        "Mahalaxmi Temple", "Rankala Lake", "Govt. College of Engineering",
        "City Railway Station", "Chhatrapati Shahu Stadium", "New Palace"
    ]
    bins = [
        [16.6950, 74.2375, random.randint(60, 95)],
        [16.7045, 74.2425, random.randint(60, 95)],
        [16.7055, 74.2460, random.randint(60, 95)],
        [16.7100, 74.2600, random.randint(60, 95)],
        [16.7200, 74.2470, random.randint(60, 95)],
        [16.7050, 74.2550, random.randint(60, 95)]
    ]

    m = folium.Map(location=base_station, zoom_start=14)
    overloaded_bins = [b for b in bins if b[2] >= 80]

    for b, name in zip(bins, locations):
        color = "red" if b[2] >= 80 else "green"
        folium.Marker(
            [b[0], b[1]],
            popup=f"{name}<br>Fill: {b[2]}%",
            icon=folium.Icon(color=color)
        ).add_to(m)

    if overloaded_bins:
        order = [base_station] + overloaded_bins
        full_route = []

        for i in range(len(order)-1):
            seg = get_osrm_route(order[i], order[i+1])
            if seg:
                if full_route and full_route[-1] == seg[0]:
                    full_route.extend(seg[1:])
                else:
                    full_route.extend(seg)
            else:
                full_route.extend([order[i][:2], order[i+1][:2]])

        if full_route:
            folium.PolyLine(full_route, color="blue", weight=5).add_to(m)
            for idx, p in enumerate(order):
                folium.Marker(
                    p[:2],
                    icon=folium.DivIcon(html=f'<div style="font-size:12px; color:blue;"><b>{idx+1}</b></div>')
                ).add_to(m)
    else:
        folium.Marker(
            base_station[:2],
            popup="✅ No overloaded bins.",
            icon=folium.Icon(color="green", icon="ok")
        ).add_to(m)

    # Add timestamp
    folium.Marker(
        base_station,
        popup=f"🕒 Last updated: {datetime.now().strftime('%d %b %Y %H:%M:%S')}",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    path = os.path.abspath(filename)
    m.save(path)
    return path

# -------------------------
# PyQt App
# -------------------------
def run_app():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Smart Dustbin - Route Map")
    window.resize(1000, 650)

    view = QWebEngineView()
    layout = QVBoxLayout()
    layout.addWidget(view)

    refresh_btn = QPushButton("🔄 Refresh Map")
    layout.addWidget(refresh_btn)

    container = QWidget()
    container.setLayout(layout)
    window.setCentralWidget(container)
    window.show()

    def update_and_load():
        file_path = generate_map_file("map.html")
        view.load(QUrl.fromLocalFile(file_path))
        view.reload()

    refresh_btn.clicked.connect(update_and_load)
    update_and_load()

    timer = QTimer()
    timer.timeout.connect(update_and_load)
    timer.start(20000)

    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()