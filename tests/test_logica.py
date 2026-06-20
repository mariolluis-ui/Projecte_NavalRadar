import csv
import tempfile
import unittest
from pathlib import Path

from barco import Barco
from cliente_ais import (
    _procesar_estatico,
    _procesar_posicion,
    _procesar_static_data_report,
    bbox_ha_cambiado,
    describir_bbox,
    normalizar_bbox,
)
from exportador_csv import exportar
from filtros import Filtros
from gestor_barcos import GestorBarcos
from radar_core import lineas_barcos_con_tipo, preparar_barcos_mapa


class BarcoTests(unittest.TestCase):
    def test_barco_sin_posicion_no_cuenta_como_visible(self):
        barco = Barco(123456789, "SIN POS")

        self.assertFalse(barco.tiene_posicion())

        barco.actualizar_posicion(41.35, 2.16, 12.5)

        self.assertTrue(barco.tiene_posicion())


class GestorTests(unittest.TestCase):
    def test_actualiza_posicion_y_datos_estaticos_del_mismo_mmsi(self):
        gestor = GestorBarcos()

        gestor.actualizar_posicion(123, "BARCO UNO", 41.0, 2.0, 10.0)
        gestor.actualizar_estatico(123, "BARCO UNO", 70, "BCN", 7.2, 9876543)

        barco = gestor.con_posicion()[0]
        self.assertEqual(barco.tipo_nombre(), "Carga")
        self.assertEqual(barco.destino, "BCN")
        self.assertEqual(barco.calado, 7.2)

    def test_conserva_datos_estaticos_tras_limpiar_posiciones(self):
        gestor = GestorBarcos()

        gestor.actualizar_estatico(123, "BARCO UNO", 70, "BCN", 7.2, 9876543)
        gestor.limpiar()
        gestor.actualizar_posicion(123, "BARCO UNO", 41.0, 2.0, 10.0)

        barco = gestor.con_posicion()[0]
        self.assertEqual(barco.tipo, 70)
        self.assertEqual(barco.tipo_nombre(), "Carga")

    def test_recupera_tipo_desde_cache_persistente(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta_cache = Path(tmp) / "cache_barcos.json"
            gestor = GestorBarcos(ruta_cache)
            gestor.actualizar_estatico(123, "BARCO UNO", 70, "BCN", 7.2, 9876543)

            gestor_nuevo = GestorBarcos(ruta_cache)
            gestor_nuevo.actualizar_posicion(123, "BARCO UNO", 41.0, 2.0, 10.0)

            barco = gestor_nuevo.con_posicion()[0]

        self.assertEqual(barco.tipo, 70)
        self.assertEqual(barco.tipo_nombre(), "Carga")


class FiltrosTests(unittest.TestCase):
    def test_filtra_por_nombre_destino_y_velocidad(self):
        barco = Barco(123, "Mediterrani", 41.0, 2.0, 8.0, destino="Barcelona")
        filtros = Filtros(texto_nombre="medi", texto_destino="bar", velocidad_min=5, velocidad_max=10)

        self.assertTrue(filtros.aplica(barco))

        filtros.velocidad_min = 9
        self.assertFalse(filtros.aplica(barco))


class ClienteAISTests(unittest.TestCase):
    def test_normaliza_bbox_para_aisstream(self):
        bbox = [[[42.0, 3.0], [40.0, 1.0]]]

        self.assertEqual(normalizar_bbox(bbox), [[[40.0, 1.0], [42.0, 3.0]]])

    def test_detecta_cambio_real_de_bbox(self):
        actual = [[[40.0, 1.0], [42.0, 3.0]]]
        casi_igual = [[[40.0001, 1.0], [42.0, 3.0]]]
        diferente = [[[35.8, -6.2], [36.4, -4.8]]]

        self.assertFalse(bbox_ha_cambiado(casi_igual, actual))
        self.assertTrue(bbox_ha_cambiado(diferente, actual))

    def test_describe_bbox_para_logs(self):
        self.assertEqual(
            describir_bbox([[[35.8, -6.2], [36.4, -4.8]]]),
            "SW=(35.8000, -6.2000) NE=(36.4000, -4.8000)",
        )

    def test_procesa_mensajes_ais_minimos(self):
        gestor = GestorBarcos()
        posicion = {
            "MessageType": "PositionReport",
            "MetaData": {"MMSI": "123", "ShipName": " TEST ", "latitude": "41.1", "longitude": "2.2"},
            "Message": {"PositionReport": {"Sog": "3.5"}},
        }
        estatico = {
            "MessageType": "ShipStaticData",
            "MetaData": {"MMSI": "123"},
            "Message": {
                "ShipStaticData": {
                    "Name": "TEST",
                    "Type": "60",
                    "Destination": "PALMA",
                    "MaximumStaticDraught": "5.5",
                    "ImoNumber": "987",
                }
            },
        }

        _procesar_posicion(posicion, gestor)
        _procesar_estatico(estatico, gestor)

        barco = gestor.con_posicion()[0]
        self.assertEqual(barco.mmsi, 123)
        self.assertEqual(barco.tipo_nombre(), "Pasajeros")
        self.assertEqual(barco.destino, "PALMA")

    def test_procesa_tipo_desde_static_data_report_clase_b(self):
        gestor = GestorBarcos()
        posicion = {
            "MessageType": "PositionReport",
            "MetaData": {"MMSI": "456", "ShipName": "VELA", "latitude": 41.2, "longitude": 2.3},
            "Message": {"PositionReport": {"Sog": 4.0}},
        }
        estatico = {
            "MessageType": "StaticDataReport",
            "MetaData": {"MMSI": "456"},
            "Message": {
                "StaticDataReport": {
                    "UserID": 456,
                    "ReportA": {"Name": "VELA"},
                    "ReportB": {"ShipType": 36},
                }
            },
        }

        _procesar_posicion(posicion, gestor)
        _procesar_static_data_report(estatico, gestor)

        barco = gestor.con_posicion()[0]
        self.assertEqual(barco.tipo, 36)
        self.assertEqual(barco.tipo_nombre(), "Velero")

    def test_static_data_report_sin_report_b_no_borra_tipo_previo(self):
        gestor = GestorBarcos()
        gestor.actualizar_posicion(456, "VELA", 41.2, 2.3, 4.0)
        gestor.actualizar_estatico(456, "VELA", 36, None, None, None)
        estatico_solo_nombre = {
            "MessageType": "StaticDataReport",
            "MetaData": {"MMSI": "456"},
            "Message": {
                "StaticDataReport": {
                    "UserID": 456,
                    "ReportA": {"Name": "VELA NUEVA"},
                    "ReportB": {},
                }
            },
        }

        _procesar_static_data_report(estatico_solo_nombre, gestor)

        barco = gestor.con_posicion()[0]
        self.assertEqual(barco.tipo, 36)
        self.assertEqual(barco.nombre, "VELA NUEVA")


class ExportadorTests(unittest.TestCase):
    def test_exporta_csv_con_barcos_con_y_sin_tipo(self):
        gestor = GestorBarcos()
        gestor.actualizar_posicion(123, "CSV", 41.0, 2.0, 1.5)
        gestor.actualizar_estatico(456, "ESTATICO", 70, "BCN", 7.0, 999)

        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "barcos.csv"
            total = exportar(gestor, ruta)

            self.assertEqual(total, 2)
            with ruta.open(encoding="utf-8", newline="") as archivo:
                filas = list(csv.reader(archivo))

        self.assertEqual(filas[1][0], "123")
        self.assertEqual(filas[1][1], "CSV")
        self.assertEqual(filas[1][7], "Esperando AIS")
        self.assertEqual(filas[2][0], "456")
        self.assertEqual(filas[2][5], "70")
        self.assertEqual(filas[2][7], "Con tipo")


class RadarCoreTests(unittest.TestCase):
    def test_prepara_barcos_para_mapa_con_codigo_tipo(self):
        barco = Barco(123, "MAPA", 41.0, 2.0, 1.5, tipo=70)

        datos = preparar_barcos_mapa([barco])

        self.assertIn('"tipo": "Carga"', datos)
        self.assertIn('"tipo_codigo": 70', datos)

    def test_lineas_barcos_con_tipo_ignora_desconocidos(self):
        con_tipo = Barco(456, "CARGA", tipo=70)
        sin_tipo = Barco(123, "SIN TIPO")

        lineas = lineas_barcos_con_tipo([sin_tipo, con_tipo])

        self.assertEqual(lineas, ["  456 | CARGA | Carga (70)"])


if __name__ == "__main__":
    unittest.main()
