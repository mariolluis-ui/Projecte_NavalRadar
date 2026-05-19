import sys
import os
import json
import base64
import folium
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401  (necesario para que loadUi encuentre la clase)
from PyQt6.QtWebEngineCore import QWebEngineSettings
from dotenv import load_dotenv
from gestor_barcos import GestorBarcos
from cliente_ais import ConexionAIS, BBOX_MEDITERRANEO
from filtros import Filtros

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_icon_base64():
    with open(os.path.join(BASE_DIR, "custom_icon.png"), "rb") as f:
        return base64.b64encode(f.read()).decode()


def generar_mapa_base():
    mapa = folium.Map(
        location=[41.35, 2.16],
        zoom_start=13,
        tiles="CartoDB positron",
    )

    map_name = mapa.get_name()
    icon_b64 = get_icon_base64()

    js = f"""
    <script>
    var iconoBase64 = "data:image/png;base64,{icon_b64}";
    var capaMarcadores = null;
    window.ultimosBarcos = [];

    function getTamanioIcono(zoom) {{
        if (zoom >= 15) return [48, 48];
        if (zoom >= 13) return [32, 32];
        if (zoom >= 11) return [24, 24];
        return [16, 16];
    }}

    function escaparHtml(valor) {{
        return String(valor || '').replace(/[&<>"']/g, function(c) {{
            return {{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}}[c];
        }});
    }}

    function actualizarBarcos(barcos) {{
        window.ultimosBarcos = barcos;

        if (!capaMarcadores) {{
            capaMarcadores = L.layerGroup().addTo({map_name});
        }}

        capaMarcadores.clearLayers();
        var zoom = {map_name}.getZoom();
        var tamanio = getTamanioIcono(zoom);

        barcos.forEach(function(barco) {{
            var icono = L.icon({{
                iconUrl: iconoBase64,
                iconSize: tamanio,
                iconAnchor: [tamanio[0]/2, tamanio[1]/2]
            }});

            var popupContent =
                '<div style="font-family: Arial; min-width: 180px;">' +
                '<h4 style="margin:0 0 8px 0;">' + escaparHtml(barco.nombre || 'Desconocido') + '</h4>' +
                '<b>MMSI:</b> ' + barco.mmsi + '<br>' +
                '<b>Tipo:</b> ' + escaparHtml(barco.tipo || '---') + '<br>' +
                '<b>Velocidad:</b> ' + barco.velocidad + ' nudos<br>' +
                '<b>Destino:</b> ' + escaparHtml(barco.destino || '---') + '<br>' +
                '<b>Calado:</b> ' + (barco.calado || '---') + '<br>' +
                '</div>';

            L.marker([barco.lat, barco.lon], {{icon: icono}})
                .bindPopup(popupContent)
                .bindTooltip(escaparHtml(barco.nombre || String(barco.mmsi)))
                .addTo(capaMarcadores);
        }});
    }}

    // Guarda el bbox actualmente visible en una variable global que Python lee con runJavaScript
    function actualizarBbox() {{
        if (typeof {map_name} === 'undefined') return;
        var bounds = {map_name}.getBounds();
        window.bboxActual = [[[
            bounds.getSouth(),
            bounds.getWest()
        ], [
            bounds.getNorth(),
            bounds.getEast()
        ]]];
    }}

    // Folium crea el mapa al final del HTML, así que esperamos a 'load'
    // para registrar los handlers (si no, {map_name} aún no existe)
    function _initRadar() {{
        {map_name}.on('zoomend', function() {{
            actualizarBarcos(window.ultimosBarcos);
            actualizarBbox();
        }});
        {map_name}.on('moveend', actualizarBbox);
        actualizarBbox();
    }}

    if (document.readyState === 'complete') {{
        _initRadar();
    }} else {{
        window.addEventListener('load', _initRadar);
    }}
    </script>
    """

    mapa.get_root().html.add_child(folium.Element(js))

    ruta = os.path.join(BASE_DIR, "mapa.html")
    mapa.save(ruta)
    return ruta


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(BASE_DIR, "ventanamapa.ui"), self)

        self.webEngineView.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        # Estado compartido entre AIS, mapa y filtros
        self.gestor = GestorBarcos()
        self.filtros = Filtros()
        self.conexion = ConexionAIS(self.gestor)
        self._bbox_actual = None
        self._bbox_pendiente = None

        # Carga el mapa base
        ruta_mapa = generar_mapa_base()
        self.webEngineView.setUrl(QUrl.fromLocalFile(ruta_mapa))

        # Arranque inicial con un bbox por defecto
        self.conexion.reiniciar(BBOX_MEDITERRANEO)
        self._bbox_actual = BBOX_MEDITERRANEO

        # Refresca los marcadores cada 10 segundos
        QTimer.singleShot(3000, self.actualizar_marcadores)
        self.timer_marcadores = QTimer()
        self.timer_marcadores.timeout.connect(self.actualizar_marcadores)
        self.timer_marcadores.start(10000)

        # Comprueba cada 2s si el bbox visible del mapa ha cambiado
        self.timer_bbox = QTimer()
        self.timer_bbox.timeout.connect(self._comprobar_bbox)
        self.timer_bbox.start(2000)

        # Evita reconectar varias veces seguidas mientras el usuario mueve el mapa
        self.timer_reconexion_bbox = QTimer()
        self.timer_reconexion_bbox.setSingleShot(True)
        self.timer_reconexion_bbox.timeout.connect(self._aplicar_bbox_pendiente)

    def _comprobar_bbox(self):
        # Le pide al JS el bbox actualmente visible
        self.webEngineView.page().runJavaScript(
            "JSON.stringify(window.bboxActual || null)",
            self._on_bbox_recibido,
        )

    def _on_bbox_recibido(self, bbox_json):
        if not bbox_json or bbox_json == "null":
            return
        try:
            nuevo_bbox = json.loads(bbox_json)
        except Exception as e:
            print("Error parseando bbox:", e)
            return
        if nuevo_bbox != self._bbox_actual:
            print("Nuevo bbox:", nuevo_bbox)
            self._bbox_pendiente = nuevo_bbox
            self.timer_reconexion_bbox.start(800)

    def _aplicar_bbox_pendiente(self):
        if self._bbox_pendiente and self._bbox_pendiente != self._bbox_actual:
            self._bbox_actual = self._bbox_pendiente
            self.conexion.reiniciar(self._bbox_actual)
        self._bbox_pendiente = None

    def actualizar_marcadores(self):
        # Aplica los filtros activos antes de pintar el mapa
        barcos = self.gestor.filtrar(self.filtros)
        print(f"Pintando {len(barcos)} barcos en el mapa")

        barcos_json = json.dumps([{
            "mmsi": b.mmsi,
            "nombre": b.nombre,
            "tipo": b.tipo_nombre(),
            "velocidad": b.velocidad,
            "destino": b.destino,
            "calado": b.calado,
            "lat": b.lat,
            "lon": b.lon,
        } for b in barcos])

        self.webEngineView.page().runJavaScript(f"actualizarBarcos({barcos_json});")

    def closeEvent(self, event):
        self.conexion.detener()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
