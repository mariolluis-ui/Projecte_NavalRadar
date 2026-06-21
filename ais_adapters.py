from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ActualizacionAIS:
    """Datos AIS normalizados para que el resto del programa no dependa del JSON original."""

    mmsi: int
    nombre: str = ""
    lat: float | None = None
    lon: float | None = None
    velocidad: float = 0.0
    tipo: int = 0
    destino: str | None = None
    calado: float | None = None
    imo: int | None = None
    es_posicion: bool = False
    es_estatico: bool = False


class MensajeAISAdapter(Protocol):
    """Interfaz comun para adaptar mensajes AISStream a ActualizacionAIS."""

    tipo_mensaje: str

    def adaptar(self, msg: dict) -> ActualizacionAIS | None:
        ...


class PositionReportAdapter:
    tipo_mensaje = "PositionReport"

    def adaptar(self, msg: dict) -> ActualizacionAIS | None:
        meta = msg.get("MetaData", {})
        interior = msg.get("Message", {}).get("PositionReport", {})

        mmsi = _primer_int(meta, "MMSI", defecto=_a_int(interior.get("UserID")))
        lat = _primer_float(meta, "latitude", "Latitude", defecto=_a_float(interior.get("Latitude")))
        lon = _primer_float(meta, "longitude", "Longitude", defecto=_a_float(interior.get("Longitude")))
        velocidad = _a_float(interior.get("Sog"), defecto=0.0)
        nombre = str(meta.get("ShipName", "")).strip()
        tipo = _primer_int(meta, "ShipType", "Type", "TypeOfShipAndCargoType", defecto=0)

        if mmsi is None or lat is None or lon is None:
            return None

        return ActualizacionAIS(
            mmsi=mmsi,
            nombre=nombre,
            lat=lat,
            lon=lon,
            velocidad=velocidad,
            tipo=tipo,
            es_posicion=True,
        )


class ClassBPositionReportAdapter:
    def __init__(self, tipo_mensaje: str):
        self.tipo_mensaje = tipo_mensaje

    def adaptar(self, msg: dict) -> ActualizacionAIS | None:
        meta = msg.get("MetaData", {})
        interior = msg.get("Message", {}).get(self.tipo_mensaje, {})

        mmsi = _primer_int(meta, "MMSI", defecto=_a_int(interior.get("UserID")))
        lat = _primer_float(meta, "latitude", "Latitude", defecto=_a_float(interior.get("Latitude")))
        lon = _primer_float(meta, "longitude", "Longitude", defecto=_a_float(interior.get("Longitude")))
        velocidad = _a_float(interior.get("Sog"), defecto=0.0)
        nombre = str(interior.get("Name", meta.get("ShipName", ""))).strip()
        tipo = _primer_int(interior, "Type", "ShipType", "TypeOfShipAndCargoType", defecto=0)

        if mmsi is None or lat is None or lon is None:
            return None

        return ActualizacionAIS(
            mmsi=mmsi,
            nombre=nombre,
            lat=lat,
            lon=lon,
            velocidad=velocidad,
            tipo=tipo,
            es_posicion=True,
        )


class ShipStaticDataAdapter:
    tipo_mensaje = "ShipStaticData"

    def adaptar(self, msg: dict) -> ActualizacionAIS | None:
        meta = msg.get("MetaData", {})
        interior = msg.get("Message", {}).get("ShipStaticData", {})

        mmsi = _a_int(meta.get("MMSI"))
        nombre = str(interior.get("Name", meta.get("ShipName", ""))).strip()
        tipo = _primer_int(
            interior,
            "Type",
            "TypeOfShipAndCargoType",
            "ShipType",
            "ShipAndCargoType",
            defecto=0,
        )
        destino = str(interior.get("Destination", "")).strip() or None
        calado = _a_float(interior.get("MaximumStaticDraught"))
        imo = _a_int(interior.get("ImoNumber"))

        if mmsi is None:
            return None

        return ActualizacionAIS(
            mmsi=mmsi,
            nombre=nombre,
            tipo=tipo,
            destino=destino,
            calado=calado,
            imo=imo,
            es_estatico=True,
        )


class StaticDataReportAdapter:
    tipo_mensaje = "StaticDataReport"

    def adaptar(self, msg: dict) -> ActualizacionAIS | None:
        meta = msg.get("MetaData", {})
        interior = msg.get("Message", {}).get("StaticDataReport", {})
        report_a = interior.get("ReportA", {}) or {}
        report_b = interior.get("ReportB", {}) or {}

        mmsi = _primer_int(meta, "MMSI", defecto=_a_int(interior.get("UserID")))
        nombre = str(report_a.get("Name", meta.get("ShipName", ""))).strip()
        tipo = _primer_int(report_b, "ShipType", "Type", "TypeOfShipAndCargoType", defecto=0)

        if mmsi is None:
            return None

        return ActualizacionAIS(
            mmsi=mmsi,
            nombre=nombre,
            tipo=tipo,
            es_estatico=True,
        )


ADAPTADORES_MENSAJES: dict[str, MensajeAISAdapter] = {
    "PositionReport": PositionReportAdapter(),
    "StandardClassBPositionReport": ClassBPositionReportAdapter("StandardClassBPositionReport"),
    "ExtendedClassBPositionReport": ClassBPositionReportAdapter("ExtendedClassBPositionReport"),
    "ShipStaticData": ShipStaticDataAdapter(),
    "StaticDataReport": StaticDataReportAdapter(),
}
TIPOS_MENSAJE_AIS = list(ADAPTADORES_MENSAJES)


def adaptar_mensaje_ais(msg: dict) -> ActualizacionAIS | None:
    adapter = ADAPTADORES_MENSAJES.get(msg.get("MessageType", ""))
    if adapter is None:
        return None
    return adapter.adaptar(msg)


def _a_float(valor, defecto=None):
    if valor in (None, ""):
        return defecto
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def _a_int(valor, defecto=None):
    if valor in (None, ""):
        return defecto
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _primer_int(datos: dict, *claves: str, defecto=None):
    for clave in claves:
        valor = _a_int(datos.get(clave), defecto=None)
        if valor is not None:
            return valor
    return defecto


def _primer_float(datos: dict, *claves: str, defecto=None):
    for clave in claves:
        valor = _a_float(datos.get(clave), defecto=None)
        if valor is not None:
            return valor
    return defecto
