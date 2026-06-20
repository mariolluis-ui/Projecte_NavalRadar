import json
from pathlib import Path
from threading import RLock

from barco import Barco
from filtros import Filtros


class GestorBarcos:
    """Guarda y actualiza barcos por MMSI de forma segura entre hilos."""

    def __init__(self, ruta_cache: str | Path | None = None):
        self.barcos: dict[int, Barco] = {}
        self.ruta_cache = Path(ruta_cache) if ruta_cache else None
        self._datos_estaticos: dict[int, dict] = self._cargar_cache()
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

            datos_estaticos = self._datos_estaticos.get(mmsi)
            if datos_estaticos and not barco.tipo:
                barco.actualizar_estatico(
                    datos_estaticos.get("tipo", 0),
                    datos_estaticos.get("destino"),
                    datos_estaticos.get("calado"),
                    datos_estaticos.get("imo"),
                )
                if datos_estaticos.get("nombre") and not barco.nombre:
                    barco.nombre = datos_estaticos["nombre"]

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
            datos_estaticos = self._datos_estaticos.setdefault(
                mmsi,
                {"nombre": None, "tipo": 0, "destino": None, "calado": None, "imo": None},
            )
            antes = datos_estaticos.copy()
            if nombre:
                datos_estaticos["nombre"] = nombre
            if tipo:
                datos_estaticos["tipo"] = tipo
            if destino:
                datos_estaticos["destino"] = destino
            if calado:
                datos_estaticos["calado"] = calado
            if imo:
                datos_estaticos["imo"] = imo

            barco = self.barcos.get(mmsi)
            if barco is None:
                barco = Barco(mmsi=mmsi, nombre=nombre)
                self.barcos[mmsi] = barco

            barco.actualizar_estatico(
                datos_estaticos.get("tipo", 0),
                datos_estaticos.get("destino"),
                datos_estaticos.get("calado"),
                datos_estaticos.get("imo"),
            )
            if nombre:
                barco.nombre = nombre

            if datos_estaticos != antes:
                self._guardar_cache()

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

    def _cargar_cache(self) -> dict[int, dict]:
        if not self.ruta_cache or not self.ruta_cache.exists():
            return {}

        try:
            contenido = json.loads(self.ruta_cache.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        datos: dict[int, dict] = {}
        for mmsi_texto, valores in contenido.items():
            try:
                mmsi = int(mmsi_texto)
            except (TypeError, ValueError):
                continue
            if not isinstance(valores, dict):
                continue

            datos[mmsi] = {
                "nombre": valores.get("nombre") or None,
                "tipo": _a_int(valores.get("tipo"), 0),
                "destino": valores.get("destino") or None,
                "calado": _a_float(valores.get("calado")),
                "imo": _a_int(valores.get("imo")),
            }
        return datos

    def _guardar_cache(self):
        if not self.ruta_cache:
            return

        self.ruta_cache.parent.mkdir(parents=True, exist_ok=True)
        contenido = {
            str(mmsi): datos
            for mmsi, datos in sorted(self._datos_estaticos.items())
            if datos.get("tipo") or datos.get("destino") or datos.get("calado") or datos.get("imo")
        }
        self.ruta_cache.write_text(
            json.dumps(contenido, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _a_int(valor, defecto=None):
    if valor in (None, ""):
        return defecto
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _a_float(valor, defecto=None):
    if valor in (None, ""):
        return defecto
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto
