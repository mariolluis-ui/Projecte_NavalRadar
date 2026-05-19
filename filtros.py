from dataclasses import dataclass, field

from barco import Barco


# Categorias que coinciden con Barco.tipo_nombre().
CATEGORIAS = [
    "Pasajeros",
    "Carga",
    "Petrolero",
    "Pesca",
    "Velero",
    "Recreo",
    "Remolcador",
    "Remolque",
    "Desconocido",
]


@dataclass
class Filtros:
    tipos: set[str] = field(default_factory=lambda: set(CATEGORIAS))
    texto_destino: str = ""
    texto_nombre: str = ""
    solo_en_movimiento: bool = False
    velocidad_min: float = 0.0
    velocidad_max: float = 100.0

    def aplica(self, barco: Barco) -> bool:
        """Devuelve True si el barco cumple todos los filtros activos."""
        if barco.tipo_nombre() not in self.tipos:
            return False

        if self.texto_destino and self.texto_destino.casefold() not in (barco.destino or "").casefold():
            return False

        if self.texto_nombre and self.texto_nombre.casefold() not in (barco.nombre or "").casefold():
            return False

        velocidad = float(barco.velocidad or 0.0)
        if self.solo_en_movimiento and velocidad < 0.5:
            return False

        minimo = min(self.velocidad_min, self.velocidad_max)
        maximo = max(self.velocidad_min, self.velocidad_max)
        return minimo <= velocidad <= maximo
