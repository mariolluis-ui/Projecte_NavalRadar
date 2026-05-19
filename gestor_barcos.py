from threading import RLock

from barco import Barco
from filtros import Filtros


class GestorBarcos:
    """Guarda y actualiza barcos por MMSI de forma segura entre hilos."""

    def __init__(self):
        self.barcos: dict[int, Barco] = {}
        self._lock = RLock()

    def actualizar_posicion(
        self,
        mmsi: int,
        nombre: str,
        lat: float,
        lon: float,
        velocidad: float,
        tipo: int = 0,
    ):
        with self._lock:
            barco = self.barcos.get(mmsi)
            if barco is None:
                barco = Barco(mmsi=mmsi, nombre=nombre, lat=lat, lon=lon, velocidad=velocidad)
                self.barcos[mmsi] = barco
            else:
                barco.actualizar_posicion(lat, lon, velocidad)
                if nombre and not barco.nombre:
                    barco.nombre = nombre

            if tipo and not barco.tipo:
                barco.tipo = tipo

    def actualizar_estatico(
        self,
        mmsi: int,
        nombre: str,
        tipo: int,
        destino: str | None,
        calado: float | None,
        imo: int | None,
    ):
        with self._lock:
            barco = self.barcos.get(mmsi)
            if barco is None:
                barco = Barco(mmsi=mmsi, nombre=nombre)
                self.barcos[mmsi] = barco

            barco.actualizar_estatico(tipo, destino, calado, imo)
            if nombre:
                barco.nombre = nombre

    def todos(self) -> list[Barco]:
        with self._lock:
            return list(self.barcos.values())

    def con_posicion(self) -> list[Barco]:
        return [barco for barco in self.todos() if barco.tiene_posicion()]

    def filtrar(self, filtros: Filtros) -> list[Barco]:
        return [barco for barco in self.con_posicion() if filtros.aplica(barco)]

    def cantidad(self) -> int:
        with self._lock:
            return len(self.barcos)

    def limpiar(self):
        with self._lock:
            self.barcos.clear()
