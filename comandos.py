from abc import ABC, abstractmethod
from radar_core import preparar_barcos_mapa


class Comando(ABC):
    """Interfaz común para cualquier acción ejecutable desde la interfaz."""

    @abstractmethod
    def ejecutar(self):
        ...


class ComandoBuscarBarco(Comando):
    def __init__(self, ventana, mmsi: str):
        self.ventana = ventana
        self.mmsi = mmsi

    def ejecutar(self):
        barcos = self.ventana.gestor.con_posicion()
        barco = next((b for b in barcos if str(b.mmsi) == self.mmsi), None)

        if barco:
            self.ventana.webEngineView.page().runJavaScript(
                f"buscarPorMMSI('{barco.mmsi}', {barco.lat}, {barco.lon});"
            )
        else:
            print(f"Barco con MMSI {self.mmsi} no encontrado")


class ComandoCambiarZona(Comando):
    def __init__(self, ventana, zona):
        self.ventana = ventana
        self.zona = zona

    def ejecutar(self):
        if self.zona is None:
            return
        self.ventana.webEngineView.page().runJavaScript(
            f"moverMapa({self.zona.lat}, {self.zona.lon}, {self.zona.zoom});"
        )


class ComandoActualizarMarcadores(Comando):
    def __init__(self, ventana):
        self.ventana = ventana

    def ejecutar(self):
        barcos = self.ventana.gestor.con_posicion()
        filtro = self.ventana.FiltrosBarcos.currentText()

        if filtro != "Todos":
            barcos = [b for b in barcos if b.tipo_nombre() == filtro]

        print(f"Actualizando {len(barcos)} barcos (filtro: {filtro})")

        barcos_json = preparar_barcos_mapa(barcos)
        self.ventana.webEngineView.page().runJavaScript(f"actualizarBarcos({barcos_json});")