import asyncio
import json
import os
import threading
from datetime import datetime

from ais_adapters import ActualizacionAIS, TIPOS_MENSAJE_AIS, adaptar_mensaje_ais
from exportador_csv import ARCHIVO_CSV, exportar
from gestor_barcos import GestorBarcos


URL_AIS = "wss://stream.aisstream.io/v0/stream"
BBOX_MEDITERRANEO = [[[40.0, 1.0], [42.0, 3.0]]]
INTERVALO = 5
TOLERANCIA_CAMBIO_BBOX = 0.0005
TIPOS_MENSAJE = TIPOS_MENSAJE_AIS


async def conectar(
    gestor: GestorBarcos,
    bbox: list = BBOX_MEDITERRANEO,
    con_resumen: bool = False,
):
    import websockets

    api_key = os.environ.get("AIS_API_KEY")
    if not api_key:
        raise ValueError("AIS_API_KEY no esta definida en el archivo .env")

    bbox = normalizar_bbox(bbox)
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


def normalizar_bbox(bbox: list) -> list:
    """Convierte un bbox al formato que espera AISStream.

    Formato final: [[[lat_sur, lon_oeste], [lat_norte, lon_este]]]
    """
    try:
        punto_a, punto_b = bbox[0]
        lat_a = float(punto_a[0])
        lon_a = float(punto_a[1])
        lat_b = float(punto_b[0])
        lon_b = float(punto_b[1])
    except (TypeError, ValueError, IndexError) as error:
        raise ValueError(f"Bounding box invalida: {bbox!r}") from error

    sur, norte = sorted((lat_a, lat_b))
    oeste, este = sorted((lon_a, lon_b))

    if sur < -90 or norte > 90 or oeste < -180 or este > 180:
        raise ValueError(f"Bounding box fuera de rango: {bbox!r}")
    if sur == norte or oeste == este:
        raise ValueError(f"Bounding box sin area: {bbox!r}")

    return [[[sur, oeste], [norte, este]]]


def bbox_ha_cambiado(nuevo_bbox: list, bbox_actual: list | None) -> bool:
    if bbox_actual is None:
        return True

    nuevo = normalizar_bbox(nuevo_bbox)
    actual = normalizar_bbox(bbox_actual)
    for nuevo_punto, actual_punto in zip(nuevo[0], actual[0]):
        for nuevo_valor, actual_valor in zip(nuevo_punto, actual_punto):
            if abs(nuevo_valor - actual_valor) > TOLERANCIA_CAMBIO_BBOX:
                return True
    return False


def describir_bbox(bbox: list) -> str:
    normalizado = normalizar_bbox(bbox)
    sw, ne = normalizado[0]
    return f"SW=({sw[0]:.4f}, {sw[1]:.4f}) NE=({ne[0]:.4f}, {ne[1]:.4f})"


async def _recibir(ws, gestor: GestorBarcos):
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[AISStream mensaje no JSON] {str(raw)[:200]}")
            continue

        actualizacion = adaptar_mensaje_ais(msg)
        if actualizacion:
            _aplicar_actualizacion(actualizacion, gestor)
        elif "error" in msg or "Error" in msg:
            print(f"[AISStream ERROR] {msg}")
        elif not msg.get("MessageType", ""):
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
    _aplicar_actualizacion(adaptar_mensaje_ais(_con_tipo_mensaje(msg, "PositionReport")), gestor)


def _procesar_posicion_clase_b(msg: dict, gestor: GestorBarcos, clave_mensaje: str):
    _aplicar_actualizacion(adaptar_mensaje_ais(_con_tipo_mensaje(msg, clave_mensaje)), gestor)


def _procesar_estatico(msg: dict, gestor: GestorBarcos):
    _aplicar_actualizacion(adaptar_mensaje_ais(_con_tipo_mensaje(msg, "ShipStaticData")), gestor)


def _procesar_static_data_report(msg: dict, gestor: GestorBarcos):
    _aplicar_actualizacion(adaptar_mensaje_ais(_con_tipo_mensaje(msg, "StaticDataReport")), gestor)


def _aplicar_actualizacion(actualizacion: ActualizacionAIS | None, gestor: GestorBarcos):
    if actualizacion is None:
        return
    if actualizacion.es_posicion:
        gestor.actualizar_posicion(
            actualizacion.mmsi,
            actualizacion.nombre,
            actualizacion.lat,
            actualizacion.lon,
            actualizacion.velocidad,
            actualizacion.tipo,
        )
    if actualizacion.es_estatico:
        gestor.actualizar_estatico(
            actualizacion.mmsi,
            actualizacion.nombre,
            actualizacion.tipo,
            actualizacion.destino,
            actualizacion.calado,
            actualizacion.imo,
        )


def _con_tipo_mensaje(msg: dict, tipo_mensaje: str) -> dict:
    if msg.get("MessageType") == tipo_mensaje:
        return msg
    copia = dict(msg)
    copia["MessageType"] = tipo_mensaje
    return copia


class ConexionAIS:
    """Maneja una conexion WebSocket en un hilo de fondo."""

    def __init__(self, gestor: GestorBarcos):
        self.gestor = gestor
        self._hilo: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._tarea: asyncio.Task | None = None
        self.bbox_actual: list | None = None

    def reiniciar(self, bbox: list) -> bool:
        bbox = normalizar_bbox(bbox)
        if not bbox_ha_cambiado(bbox, self.bbox_actual):
            print(f"Bbox sin cambios, se mantiene AISStream en {describir_bbox(bbox)}")
            return False

        self.detener()
        self.gestor.limpiar()
        self.bbox_actual = bbox
        print(f"Reiniciando AISStream con bbox {describir_bbox(bbox)}")
        self._hilo = threading.Thread(target=self._ejecutar, args=(bbox,), daemon=True)
        self._hilo.start()
        return True

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
