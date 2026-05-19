import csv
import tempfile
import unittest
from pathlib import Path

from barco import Barco
from cliente_ais import _procesar_estatico, _procesar_posicion
from exportador_csv import exportar
from filtros import Filtros
from gestor_barcos import GestorBarcos


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


class FiltrosTests(unittest.TestCase):
    def test_filtra_por_nombre_destino_y_velocidad(self):
        barco = Barco(123, "Mediterrani", 41.0, 2.0, 8.0, destino="Barcelona")
        filtros = Filtros(texto_nombre="medi", texto_destino="bar", velocidad_min=5, velocidad_max=10)

        self.assertTrue(filtros.aplica(barco))

        filtros.velocidad_min = 9
        self.assertFalse(filtros.aplica(barco))


class ClienteAISTests(unittest.TestCase):
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
                    "TypeOfShipAndCargoType": "60",
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


class ExportadorTests(unittest.TestCase):
    def test_exporta_csv_en_ruta_indicada(self):
        gestor = GestorBarcos()
        gestor.actualizar_posicion(123, "CSV", 41.0, 2.0, 1.5)

        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "barcos.csv"
            total = exportar(gestor, ruta)

            self.assertEqual(total, 1)
            with ruta.open(encoding="utf-8", newline="") as archivo:
                filas = list(csv.reader(archivo))

        self.assertEqual(filas[1][0], "123")
        self.assertEqual(filas[1][1], "CSV")


if __name__ == "__main__":
    unittest.main()
