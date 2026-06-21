from dataclasses import dataclass


# Mapa de codigos numericos AIS -> nombre legible del tipo de barco.
NOMBRE_TIPO = {
    0: "Desconocido",
    **{i: "Ala en tierra" for i in range(20, 30)},
    30: "Pesca",
    31: "Remolque",
    32: "Remolque",
    33: "Dragado",
    34: "Buceo",
    35: "Militar",
    36: "Velero",
    37: "Recreo",
    **{i: "Alta velocidad" for i in range(40, 50)},
    50: "Practico",
    51: "Rescate",
    52: "Remolcador",
    53: "Servicio portuario",
    54: "Anticontaminacion",
    55: "Autoridad",
    58: "Medico",
    59: "Especial",
    **{i: "Pasajeros" for i in range(60, 70)},
    **{i: "Carga" for i in range(70, 80)},
    **{i: "Petrolero" for i in range(80, 90)},
    **{i: "Otro" for i in range(90, 100)},
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
        if tipo:
            self.tipo = tipo
        if destino:
            self.destino = destino
        if calado:
            self.calado = calado
        if imo:
            self.imo = imo

    def tipo_nombre(self) -> str:
        if not self.tipo:
            return "Desconocido"
        return NOMBRE_TIPO.get(self.tipo, "Otro")

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
