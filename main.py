import sys
import os
import json
import base64
import folium

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from dotenv import load_dotenv

from cliente_ais import ConexionAIS, BBOX_MEDITERRANEO, bbox_ha_cambiado
from radar_core import crear_gestor, preparar_barcos_mapa


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Coordenadas (lat, lon, zoom) de cada zona del combo Filtre_site
ZONAS_IMPORTANTES = {
    "Mar Mediterraneo": (38.0, 15.0, 6),
    "Canal de Suez": (30.5, 32.35, 10),
    "Canal de Panamá": (9.08, -79.68, 10),
    "Estrecho de Malaka": (2.5, 101.0, 7),
    "Estrecho de Ormuz": (26.5, 56.25, 8),
    "Mar de China": (15.0, 114.0, 5),
}


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
    window.bboxActual = null;

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
                iconAnchor: [tamanio[0] / 2, tamanio[1] / 2]
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

    function moverMapa(lat, lon, zoom) {{
        {map_name}.setView([lat, lon], zoom || {map_name}.getZoom());
        setTimeout(actualizarBbox, 300);
    }}

    function buscarPorMMSI(mmsi, lat, lon) {{
        {map_name}.setView([lat, lon], 15);
        setTimeout(actualizarBbox, 300);

        if (!capaMarcadores) return;

        capaMarcadores.eachLayer(function(layer) {{
            var pos = layer.getLatLng();
            if (Math.abs(pos.lat - lat) < 0.001 && Math.abs(pos.lng - lon) < 0.001) {{
                layer.openPopup();
            }}
        }});
    }}

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
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )

        self.FiltrosBarcos.currentTextChanged.connect(self.actualizar_marcadores)
        self.lineEdit.setPlaceholderText("Introduce el MMSI...")
        self.pushButton.clicked.connect(self.buscar_barco)

        # Combo de zonas importantes
        self.Filtro_site.currentTextChanged.connect(self.cambiar_zona)

        self.gestor = crear_gestor()
        self.conexion = ConexionAIS(self.gestor)
        self._bbox_actual = None

        ruta_mapa = generar_mapa_base()
        self.webEngineView.setUrl(QUrl.fromLocalFile(ruta_mapa))

        self.conexion.reiniciar(BBOX_MEDITERRANEO)
        self._bbox_actual = BBOX_MEDITERRANEO

        QTimer.singleShot(3000, self.actualizar_marcadores)

        self.timer_marcadores = QTimer()
        self.timer_marcadores.timeout.connect(self.actualizar_marcadores)
        self.timer_marcadores.start(10000)

        self.timer_bbox = QTimer()
        self.timer_bbox.timeout.connect(self._comprobar_bbox)
        self.timer_bbox.start(1500)

    def cambiar_zona(self, zona):
        datos = ZONAS_IMPORTANTES.get(zona)
        if datos:
            lat, lon, zoom = datos
            self.mover_a_zona(lat, lon, zoom)

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

    def mover_a_zona(self, lat, lon, zoom=11):
        self.webEngineView.page().runJavaScript(
            f"moverMapa({lat}, {lon}, {zoom});"
        )

    def actualizar_marcadores(self):
        barcos = self.gestor.con_posicion()
        filtro = self.FiltrosBarcos.currentText()

        if filtro != "Todos":
            barcos = [barco for barco in barcos if barco.tipo_nombre() == filtro]

        print(f"Actualizando {len(barcos)} barcos (filtro: {filtro})")

        barcos_json = preparar_barcos_mapa(barcos)
        self.webEngineView.page().runJavaScript(f"actualizarBarcos({barcos_json});")

    def buscar_barco(self):
        texto = self.lineEdit.text().strip()
        if not texto:
            return

        barcos = self.gestor.con_posicion()
        barco = next((b for b in barcos if str(b.mmsi) == texto), None)

        if barco:
            self.webEngineView.page().runJavaScript(
                f"buscarPorMMSI('{barco.mmsi}', {barco.lat}, {barco.lon});"
            )
        else:
            print(f"Barco con MMSI {texto} no encontrado")

    def closeEvent(self, event):
        self.conexion.detener()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())