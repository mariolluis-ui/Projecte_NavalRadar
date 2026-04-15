import sys
import os
import folium
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generar_mapa(barcos=[]):
    mapa = folium.Map(
        location=[41.35, 2.16],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    for barco in barcos:
        folium.Marker(
            location=[barco["lat"], barco["lon"]],
            tooltip=barco["nombre"]
        ).add_to(mapa)

    ruta = os.path.join(BASE_DIR, "mapa.html")
    mapa.save(ruta)
    return ruta


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(BASE_DIR, "ventanamapa.ui"), self)

        ruta_mapa = generar_mapa()
        print("Cargando mapa desde:", ruta_mapa)

        self.webEngineView.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        self.webEngineView.setUrl(QUrl.fromLocalFile(ruta_mapa))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())