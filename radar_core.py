import json
import os

from exportador_csv import ARCHIVO_CSV, exportar
from gestor_barcos import GestorBarcos


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_BARCOS = os.path.join(BASE_DIR, "cache_barcos.json")
REFRESCO_MARCADORES_MS = 3000


def crear_gestor() -> GestorBarcos:
    return GestorBarcos(CACHE_BARCOS)


def preparar_barcos_mapa(barcos) -> str:
    return json.dumps([
        {
            "mmsi": barco.mmsi,
            "nombre": barco.nombre,
            "tipo": barco.tipo_nombre(),
            "tipo_codigo": barco.tipo,
            "velocidad": barco.velocidad,
            "destino": barco.destino,
            "calado": barco.calado,
            "lat": barco.lat,
            "lon": barco.lon,
        }
        for barco in barcos
    ])


def exportar_estado_barcos(gestor: GestorBarcos, barcos_visibles) -> dict:
    total_csv = exportar(gestor)
    con_tipo = sum(1 for barco in barcos_visibles if barco.tipo)
    sin_tipo = len(barcos_visibles) - con_tipo

    return {
        "total_csv": total_csv,
        "archivo_csv": ARCHIVO_CSV,
        "visibles": len(barcos_visibles),
        "con_tipo": con_tipo,
        "sin_tipo": sin_tipo,
    }


def lineas_barcos_con_tipo(barcos) -> list[str]:
    barcos_con_tipo = [barco for barco in barcos if barco.tipo]
    return [
        f"  {barco.mmsi} | {barco.nombre or '---'} | {barco.tipo_nombre()} ({barco.tipo})"
        for barco in sorted(barcos_con_tipo, key=lambda item: item.nombre or str(item.mmsi))
    ]
