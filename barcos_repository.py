import json
from pathlib import Path
from typing import Protocol


class BarcosRepository(Protocol):
    """Interfaz para persistir datos estaticos de barcos."""

    def cargar(self) -> dict[int, dict]:
        ...

    def guardar(self, datos_estaticos: dict[int, dict]):
        ...


class CacheBarcosRepository:
    """Repository JSON para la cache local de datos estaticos AIS."""

    def __init__(self, ruta_cache: str | Path):
        self.ruta_cache = Path(ruta_cache)

    def cargar(self) -> dict[int, dict]:
        if not self.ruta_cache.exists():
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

    def guardar(self, datos_estaticos: dict[int, dict]):
        self.ruta_cache.parent.mkdir(parents=True, exist_ok=True)
        contenido = {
            str(mmsi): datos
            for mmsi, datos in sorted(datos_estaticos.items())
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
