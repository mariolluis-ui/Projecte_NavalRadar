from dataclasses import dataclass


# Mapa de codigos numericos AIS -> nombre legible del tipo de barco.
NOMBRE_TIPO = {
    0: "Desconocido",
    30: "Pesca",
    31: "Remolque",
    36: "Velero",
    37: "Recreo",
    52: "Remolcador",
    **{i: "Pasajeros" for i in range(60, 70)},
    **{i: "Carga" for i in range(70, 80)},
    **{i: "Petrolero" for i in range(80, 90)},
}


@dataclass
class Barco:
    """Representa el ultimo estado conocido de un barco AIS."""

    mmsi: int
    nombre: str
    lat: float | None = None
    lon: float | None = None
    velocidad: float = 0.0
    tipo: int = 0
    destino: str | None = None
    calado: float | None = None
    imo: int | None = None

    def actualizar_posicion(self, lat: float, lon: float, velocidad: float):
        self.lat = lat
        self.lon = lon
        self.velocidad = velocidad

    def actualizar_estatico(
        self,
        tipo: int = 0,
        destino: str | None = None,
        calado: float | None = None,
        imo: int | None = None,
    ):
        self.tipo = tipo or 0
        self.destino = destino or None
        self.calado = calado or None
        self.imo = imo or None

    def tipo_nombre(self) -> str:
        return NOMBRE_TIPO.get(self.tipo, f"Tipo {self.tipo}")

    def tiene_posicion(self) -> bool:
        return self.lat is not None and self.lon is not None

    def __repr__(self):
        lat = f"{self.lat:>9.4f}" if self.lat is not None else "      ---"
        lon = f"{self.lon:>9.4f}" if self.lon is not None else "      ---"
        linea = (
            f"  {self.mmsi} | {self.nombre or '---':<20} | "
            f"lat={lat}  lon={lon} | "
            f"{str(self.velocidad):>5} nudos | {self.tipo_nombre()}"
        )
        if self.destino:
            linea += f" | -> {self.destino}"
        if self.calado:
            linea += f" | calado {self.calado}m"
        return linea
