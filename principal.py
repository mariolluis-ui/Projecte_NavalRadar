import asyncio

from dotenv import load_dotenv

from cliente_ais import conectar
from radar_core import crear_gestor

load_dotenv()

gestor = crear_gestor()

asyncio.run(conectar(gestor, con_resumen=True))
