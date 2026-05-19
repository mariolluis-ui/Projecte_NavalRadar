import csv
from datetime import datetime
from pathlib import Path

from gestor_barcos import GestorBarcos


ARCHIVO_CSV = "barcos.csv"
CABECERAS = [
    "MMSI",
    "Nombre",
    "Latitud",
    "Longitud",
    "Velocidad (nudos)",
    "Tipo",
    "Destino",
    "Calado (m)",
    "IMO",
    "Ultima actualizacion",
]


def exportar(gestor: GestorBarcos, ruta: str | Path = ARCHIVO_CSV) -> int:
    barcos = sorted(gestor.con_posicion(), key=lambda barco: barco.mmsi)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with Path(ruta).open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(CABECERAS)
        for barco in barcos:
            writer.writerow([
                barco.mmsi,
                barco.nombre or "",
                round(barco.lat, 5),
                round(barco.lon, 5),
                barco.velocidad,
                barco.tipo_nombre(),
                barco.destino or "",
                barco.calado or "",
                barco.imo or "",
                ahora,
            ])

    return len(barcos)
