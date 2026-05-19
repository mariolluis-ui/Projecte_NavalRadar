import asyncio
from dotenv import load_dotenv
from cliente_ais import conectar
from gestor_barcos import GestorBarcos

# Carga las variables del archivo .env (la API key)
load_dotenv()

# Creamos el gestor que guardará todos los barcos
gestor = GestorBarcos()

# Arrancamos la conexión en tiempo real
asyncio.run(conectar(gestor, con_resumen=True))

