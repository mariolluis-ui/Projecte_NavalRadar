from dataclasses import dataclass
from typing import Optional


@dataclass
class Zona:
    nombre: str
    lat: float
    lon: float
    zoom: int


class ZonaFactory:

    _ZONAS = {
        "Mar Mediterraneo": (38.0, 15.0, 6),
        "Canal de Suez": (30.5, 32.35, 10),
        "Canal de Panamá": (9.08, -79.68, 10),
        "Estrecho de Malaka": (2.5, 101.0, 7),
        "Estrecho de Ormuz": (26.5, 56.25, 8),
        "Mar de China": (15.0, 114.0, 5),
    }

    @classmethod
    def crear(cls, nombre: str) -> Optional[Zona]:
        datos = cls._ZONAS.get(nombre)
        if datos is None:
            return None
        lat, lon, zoom = datos
        return Zona(nombre=nombre, lat=lat, lon=lon, zoom=zoom)

    @classmethod
    def nombres_disponibles(cls):
        return list(cls._ZONAS.keys())