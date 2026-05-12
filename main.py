import sys
import os
import json
import base64
import asyncio
import threading
import folium
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from dotenv import load_dotenv
from gestor_barcos import GestorBarcos
from cliente_ais import conectar, BBOX_MEDITERRANEO

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_icon_base64():
    with open(os.path.join(BASE_DIR, "custom_icon.png"), "rb") as f:
        return base64.b64encode(f.read()).decode()


def generar_mapa_base():
    mapa = folium.Map(
        location=[41.35, 2.16],
        zoom_start=13,
        tiles="CartoDB positron"
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
                '<h4 style="margin:0 0 8px 0;">' + (barco.nombre || 'Desconocido') + '</h4>' +
                '<b>MMSI:</b> ' + barco.mmsi + '<br>' +
                '<b>Tipo:</b> ' + (barco.tipo || '---') + '<br>' +
                '<b>Velocidad:</b> ' + barco.velocidad + ' nudos<br>' +
                '<b>Destino:</b> ' + (barco.destino || '---') + '<br>' +
                '<b>Calado:</b> ' + (barco.calado || '---') + '<br>' +
                '</div>';

            L.marker([barco.lat, barco.lon], {{icon: icono}})
                .bindPopup(popupContent)
                .bindTooltip(barco.nombre || String(barco.mmsi))
                .addTo(capaMarcadores);
        }});
    }}

    function buscarPorMMSI(mmsi, lat, lon) {{
        {map_name}.setView([lat, lon], 15);
        capaMarcadores.eachLayer(function(layer) {{
            var pos = layer.getLatLng();
            if (Math.abs(pos.lat - lat) < 0.001 && Math.abs(pos.lng - lon) < 0.001) {{
                layer.openPopup();
            }}
        }});
    }}

    function enviarBbox() {{
        var bounds = {map_name}.getBounds();
        var bbox = [[[
            bounds.getSouth(),
            bounds.getWest()
        ], [
            bounds.getNorth(),
            bounds.getEast()
        ]]];
        window.location.hash = JSON.stringify(bbox);
    }}

    {map_name}.on('zoomend', function() {{
        actualizarBarcos(window.ultimosBarcos);
        enviarBbox();
    }});

    {map_name}.on('moveend', enviarBbox);
    </script>
    """

    mapa.get_root().html.add_child(folium.Element(js))
    ruta = os.path.join(BASE_DIR, "mapa.html")
    mapa.save(ruta)
    return ruta


def arrancar_websocket(gestor, bbox=None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(conectar(gestor, bbox or BBOX_MEDITERRANEO))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(BASE_DIR, "ventanamapa.ui"), self)

        self.webEngineView.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        self.FiltrosBarcos.currentTextChanged.connect(self.actualizar_marcadores)
        self.pushButton.clicked.connect(self.buscar_barco)

        self.gestor = GestorBarcos()

        self.hilo = threading.Thread(
            target=arrancar_websocket,
            args=(self.gestor,),
            daemon=True
        )
        self.hilo.start()

        ruta_mapa = generar_mapa_base()
        self.webEngineView.setUrl(QUrl.fromLocalFile(ruta_mapa))
        self.webEngineView.urlChanged.connect(self.on_url_changed)

        QTimer.singleShot(3000, self.actualizar_marcadores)
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_marcadores)
        self.timer.start(10000)

    def on_url_changed(self, url):
        fragment = url.fragment()
        if fragment:
            try:
                nuevo_bbox = json.loads(fragment)
                print("Nuevo bbox:", nuevo_bbox)
                self.reiniciar_websocket(nuevo_bbox)
            except Exception as e:
                print("Error parseando bbox:", e)

    def reiniciar_websocket(self, bbox):
        self.hilo = threading.Thread(
            target=arrancar_websocket,
            args=(self.gestor, bbox),
            daemon=True
        )
        self.hilo.start()

    def actualizar_marcadores(self):
        barcos = self.gestor.con_posicion()
        filtro = self.FiltrosBarcos.currentText()

        if filtro != "Todos":
            barcos = [b for b in barcos if b.tipo_nombre() == filtro]

        print(f"Actualizando {len(barcos)} barcos (filtro: {filtro})")

        barcos_json = json.dumps([{
            "mmsi": b.mmsi,
            "nombre": b.nombre,
            "tipo": b.tipo_nombre() if hasattr(b, 'tipo_nombre') else str(b.tipo),
            "velocidad": b.velocidad,
            "destino": b.destino,
            "calado": b.calado,
            "lat": b.lat,
            "lon": b.lon
        } for b in barcos])

        self.webEngineView.page().runJavaScript(f"actualizarBarcos({barcos_json});")

    def buscar_barco(self):
        mmsi_buscado = self.lineEdit.text().strip()
        if not mmsi_buscado:
            return

        barcos = self.gestor.con_posicion()
        barco = next((b for b in barcos if str(b.mmsi) == mmsi_buscado), None)

        if barco:
            self.webEngineView.page().runJavaScript(
                f"buscarPorMMSI('{barco.mmsi}', {barco.lat}, {barco.lon});"
            )
        else:
            print(f"Barco con MMSI {mmsi_buscado} no encontrado")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())