from cliente_ais import BBOX_MEDITERRANEO, ConexionAIS
from filtros import Filtros
from gestor_barcos import GestorBarcos
from radar_core import crear_gestor, exportar_estado_barcos, preparar_barcos_mapa


class RadarAISFacade:
    """Facade de alto nivel para usar el radar sin conocer sus piezas internas."""

    def __init__(
        self,
        gestor: GestorBarcos | None = None,
        conexion: ConexionAIS | None = None,
        filtros: Filtros | None = None,
    ):
        self.gestor = gestor or crear_gestor()
        self.conexion = conexion or ConexionAIS(self.gestor)
        self.filtros = filtros or Filtros()

    def iniciar(self, bbox: list = BBOX_MEDITERRANEO) -> bool:
        return self.conexion.reiniciar(bbox)

    def cambiar_bbox(self, bbox: list) -> bool:
        return self.conexion.reiniciar(bbox)

    def detener(self):
        self.conexion.detener()

    def aplicar_filtros(self, filtros: Filtros):
        self.filtros = filtros

    def barcos_visibles(self):
        return self.gestor.filtrar(self.filtros)

    def barcos_mapa_json(self) -> str:
        return preparar_barcos_mapa(self.barcos_visibles())

    def exportar_estado(self) -> dict:
        barcos = self.barcos_visibles()
        return exportar_estado_barcos(self.gestor, barcos)
