import asyncio
import json
import os
import threading
from datetime import datetime

from exportador_csv import ARCHIVO_CSV, exportar
from gestor_barcos import GestorBarcos


URL_AIS = "wss://stream.aisstream.io/v0/stream"
BBOX_MEDITERRANEO = [[[40.0, 1.0], [42.0, 3.0]]]
INTERVALO = 5
TIPOS_MENSAJE = [
    "PositionReport",
    "StandardClassBPositionReport",
    "ExtendedClassBPositionReport",
    "ShipStaticData",
    "StaticDataReport",
]


async def conectar(
    gestor: GestorBarcos,
    bbox: list = BBOX_MEDITERRANEO,
    con_resumen: bool = False,
):
    import websockets

    api_key = os.environ.get("AIS_API_KEY")
    if not api_key:
        raise ValueError("AIS_API_KEY no esta definida en el archivo .env")

    suscripcion = {
        "APIKey": api_key,
        "BoundingBoxes": bbox,
        "FilterMessageTypes": TIPOS_MENSAJE,
    }

    sw, ne = bbox[0]
    ancho = abs(ne[1] - sw[1])
    alto = abs(ne[0] - sw[0])
    print(f"Conectando a AISStream... bbox ~{ancho:.1f} x {alto:.1f} grados")

    try:
        async with websockets.connect(URL_AIS, ping_interval=20, ping_timeout=20) as ws:
            await ws.send(json.dumps(suscripcion))
            print("Suscrito.")
            tareas = [_recibir(ws, gestor)]
            if con_resumen:
                tareas.append(_ciclo_resumen(gestor))
            await asyncio.gather(*tareas)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        print(f"Error en la conexion AIS: {type(error).__name__}: {error}")
        raise


async def _recibir(ws, gestor: GestorBarcos):
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[AISStream mensaje no JSON] {str(raw)[:200]}")
            continue

        tipo = msg.get("MessageType", "")
        if tipo == "PositionReport":
            _procesar_posicion(msg, gestor)
        elif tipo == "StandardClassBPositionReport":
            _procesar_posicion_clase_b(msg, gestor, "StandardClassBPositionReport")
        elif tipo == "ExtendedClassBPositionReport":
            _procesar_posicion_clase_b(msg, gestor, "ExtendedClassBPositionReport")
        elif tipo == "ShipStaticData":
            _procesar_estatico(msg, gestor)
        elif tipo == "StaticDataReport":
            _procesar_static_data_report(msg, gestor)
        elif "error" in msg or "Error" in msg:
            print(f"[AISStream ERROR] {msg}")
        elif not tipo:
            print(f"[AISStream mensaje desconocido] {str(msg)[:200]}")


async def _ciclo_resumen(gestor: GestorBarcos):
    while True:
        await asyncio.sleep(INTERVALO)
        _mostrar_resumen(gestor)
        total = exportar(gestor)
        hora = datetime.now().strftime("%H:%M:%S")
        print(f"\n  CSV guardado -> {ARCHIVO_CSV}  ({total} barcos)  [{hora}]")
        print("-" * 80)


def _mostrar_resumen(gestor: GestorBarcos):
    barcos = gestor.con_posicion()
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 80)
    print(f"  RADAR DE BARCOS  |  {len(barcos)} barcos activos  |  {gestor.cantidad()} registrados en total")
    print(f"  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print("=" * 80)
    print(f"  {'MMSI':<12} {'NOMBRE':<22} {'LAT':>8}  {'LON':>9}  {'VEL':>6}  TIPO / DESTINO")
    print("-" * 80)
    for barco in sorted(barcos, key=lambda item: item.nombre or ""):
        extra = ""
        if barco.destino:
            extra += f"  ->  {barco.destino}"
        if barco.calado:
            extra += f"  (calado {barco.calado}m)"
        print(
            f"  {barco.mmsi:<12} {(barco.nombre or '---'):<22} "
            f"{barco.lat:>8.4f}  {barco.lon:>9.4f}  {str(barco.velocidad):>5}kn  "
            f"{barco.tipo_nombre()}{extra}"
        )


def _procesar_posicion(msg: dict, gestor: GestorBarcos):
    meta = msg.get("MetaData", {})
    interior = msg.get("Message", {}).get("PositionReport", {})

    mmsi = _primer_int(meta, "MMSI", defecto=_a_int(interior.get("UserID")))
    lat = _primer_float(meta, "latitude", "Latitude", defecto=_a_float(interior.get("Latitude")))
    lon = _primer_float(meta, "longitude", "Longitude", defecto=_a_float(interior.get("Longitude")))
    velocidad = _a_float(interior.get("Sog"), defecto=0.0)
    nombre = str(meta.get("ShipName", "")).strip()
    tipo = _primer_int(meta, "ShipType", "Type", "TypeOfShipAndCargoType", defecto=0)

    if mmsi is not None and lat is not None and lon is not None:
        gestor.actualizar_posicion(mmsi, nombre, lat, lon, velocidad, tipo)


def _procesar_posicion_clase_b(msg: dict, gestor: GestorBarcos, clave_mensaje: str):
    meta = msg.get("MetaData", {})
    interior = msg.get("Message", {}).get(clave_mensaje, {})

    mmsi = _primer_int(meta, "MMSI", defecto=_a_int(interior.get("UserID")))
    lat = _primer_float(meta, "latitude", "Latitude", defecto=_a_float(interior.get("Latitude")))
    lon = _primer_float(meta, "longitude", "Longitude", defecto=_a_float(interior.get("Longitude")))
    velocidad = _a_float(interior.get("Sog"), defecto=0.0)
    nombre = str(interior.get("Name", meta.get("ShipName", ""))).strip()
    tipo = _primer_int(interior, "Type", "ShipType", "TypeOfShipAndCargoType", defecto=0)

    if mmsi is not None and lat is not None and lon is not None:
        gestor.actualizar_posicion(mmsi, nombre, lat, lon, velocidad, tipo)


def _procesar_estatico(msg: dict, gestor: GestorBarcos):
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
    destino = str(interior.get("Destination", "")).strip()
    calado = _a_float(interior.get("MaximumStaticDraught"))
    imo = _a_int(interior.get("ImoNumber"))

    if mmsi is not None:
        gestor.actualizar_estatico(mmsi, nombre, tipo, destino, calado, imo)


def _procesar_static_data_report(msg: dict, gestor: GestorBarcos):
    meta = msg.get("MetaData", {})
    interior = msg.get("Message", {}).get("StaticDataReport", {})
    report_a = interior.get("ReportA", {}) or {}
    report_b = interior.get("ReportB", {}) or {}

    mmsi = _primer_int(meta, "MMSI", defecto=_a_int(interior.get("UserID")))
    nombre = str(report_a.get("Name", meta.get("ShipName", ""))).strip()
    tipo = _primer_int(report_b, "ShipType", "Type", "TypeOfShipAndCargoType", defecto=0)

    if mmsi is not None:
        gestor.actualizar_estatico(mmsi, nombre, tipo, destino=None, calado=None, imo=None)


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


class ConexionAIS:
    """Maneja una conexion WebSocket en un hilo de fondo."""

    def __init__(self, gestor: GestorBarcos):
        self.gestor = gestor
        self._hilo: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._tarea: asyncio.Task | None = None

    def reiniciar(self, bbox: list):
        self.detener()
        self.gestor.limpiar()
        self._hilo = threading.Thread(target=self._ejecutar, args=(bbox,), daemon=True)
        self._hilo.start()

    def detener(self):
        if self._loop and self._tarea and not self._tarea.done() and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._tarea.cancel)
        if self._hilo and self._hilo.is_alive():
            self._hilo.join(timeout=2)

    def _ejecutar(self, bbox: list):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._tarea = self._loop.create_task(conectar(self.gestor, bbox))
        try:
            self._loop.run_until_complete(self._tarea)
        except asyncio.CancelledError:
            pass
        finally:
            self._loop.close()
