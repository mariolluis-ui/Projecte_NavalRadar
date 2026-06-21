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
    "Codigo tipo AIS",
    "Tipo",
    "Estado tipo",
    "Destino",
    "Calado (m)",
    "IMO",
    "Ultima actualizacion",
]


def exportar(gestor: GestorBarcos, ruta: str | Path = ARCHIVO_CSV) -> int:
    barcos = sorted(gestor.todos(), key=lambda barco: barco.mmsi)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with Path(ruta).open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(CABECERAS)
        for barco in barcos:
            writer.writerow([
                barco.mmsi,
                barco.nombre or "",
                round(barco.lat, 5) if barco.lat is not None else "",
                round(barco.lon, 5) if barco.lon is not None else "",
                barco.velocidad,
                barco.tipo or "",
                barco.tipo_nombre(),
                "Con tipo" if barco.tipo else "Esperando AIS",
                barco.destino or "",
                barco.calado or "",
                barco.imo or "",
                ahora,
            ])

    return len(barcos)
