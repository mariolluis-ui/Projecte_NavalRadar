import sys
import os
import json
import base64

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from dotenv import load_dotenv

from cliente_ais import ConexionAIS, BBOX_MEDITERRANEO, bbox_ha_cambiado
from radar_core import crear_gestor
from zonas import ZonaFactory
from mapa_factory import MapaFactory
from comandos import ComandoBuscarBarco, ComandoCambiarZona, ComandoActualizarMarcadores


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(BASE_DIR, "ventanamapa.ui"), self)

        self.webEngineView.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )

        self.FiltrosBarcos.currentTextChanged.connect(self._on_filtro_cambiado)
        self.lineEdit.setPlaceholderText("Introduce el MMSI...")
        self.pushButton.clicked.connect(self._on_buscar_clicado)

        self.Filtro_site.currentTextChanged.connect(self._on_zona_cambiada)

        self.gestor = crear_gestor()
        self.conexion = ConexionAIS(self.gestor)
        self._bbox_actual = None

        icon_b64 = self._get_icon_base64()
        fabrica_mapa = MapaFactory(BASE_DIR, icon_b64)
        ruta_mapa = fabrica_mapa.crear_mapa_mediterraneo()
        self.webEngineView.setUrl(QUrl.fromLocalFile(ruta_mapa))

        self.conexion.reiniciar(BBOX_MEDITERRANEO)
        self._bbox_actual = BBOX_MEDITERRANEO

        QTimer.singleShot(3000, self._on_filtro_cambiado)

        self.timer_marcadores = QTimer()
        self.timer_marcadores.timeout.connect(self._on_filtro_cambiado)
        self.timer_marcadores.start(10000)

        self.timer_bbox = QTimer()
        self.timer_bbox.timeout.connect(self._comprobar_bbox)
        self.timer_bbox.start(1500)

    def _get_icon_base64(self):
        with open(os.path.join(BASE_DIR, "custom_icon.png"), "rb") as f:
            return base64.b64encode(f.read()).decode()

    # --- Cada acción de la UI crea su Comando y lo ejecuta ---

    def _on_filtro_cambiado(self, _texto=None):
        ComandoActualizarMarcadores(self).ejecutar()

    def _on_buscar_clicado(self):
        texto = self.lineEdit.text().strip()
        if texto:
            ComandoBuscarBarco(self, texto).ejecutar()

    def _on_zona_cambiada(self, nombre_zona):
        zona = ZonaFactory.crear(nombre_zona)
        ComandoCambiarZona(self, zona).ejecutar()

    # --- Resto de lógica (bbox dinámico) ---

    def _comprobar_bbox(self):
        self.webEngineView.page().runJavaScript(
            "JSON.stringify(window.bboxActual || null)",
            self._on_bbox_recibido,
        )

    def _on_bbox_recibido(self, bbox_json):
        if not bbox_json or bbox_json == "null":
            return

        try:
            nuevo_bbox = json.loads(bbox_json)
        except Exception as error:
            print("Error parseando bbox:", error)
            return

        try:
            if bbox_ha_cambiado(nuevo_bbox, self._bbox_actual):
                print("Nuevo bbox recibido desde el mapa:", nuevo_bbox)
                reiniciado = self.conexion.reiniciar(nuevo_bbox)
                if reiniciado:
                    self._bbox_actual = nuevo_bbox
        except ValueError as error:
            print("Bbox invalido:", error)

    def closeEvent(self, event):
        self.conexion.detener()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())