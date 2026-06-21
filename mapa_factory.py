import os
import folium


class MapaFactory:
    def __init__(self, base_dir: str, icon_b64: str):
        self.base_dir = base_dir
        self.icon_b64 = icon_b64

    def crear_mapa_mediterraneo(self) -> str:
        return self._construir_mapa(
            location=[41.35, 2.16],
            zoom_start=13,
            tiles="CartoDB positron",
        )

    def crear_mapa_oscuro(self) -> str:
        return self._construir_mapa(
            location=[41.35, 2.16],
            zoom_start=13,
            tiles="CartoDB dark_matter",
        )

    def _construir_mapa(self, location, zoom_start, tiles) -> str:
        mapa = folium.Map(location=location, zoom_start=zoom_start, tiles=tiles)
        map_name = mapa.get_name()

        js = self._generar_js(map_name)
        mapa.get_root().html.add_child(folium.Element(js))

        ruta = os.path.join(self.base_dir, "mapa.html")
        mapa.save(ruta)
        return ruta

    def _generar_js(self, map_name: str) -> str:
        return f"""
        <script>
        var iconoBase64 = "data:image/png;base64,{self.icon_b64}";
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