# src/infrastructure/entrypoints/cli_adapter.py
# Propósito: Adaptador de línea de comandos (CLI) para interactuar con el sistema RAG.

from typing import List
from src.application.ports.rag_port import RagPort
from src.domain.models import Answer

class CLIAdapter:
    # Propósito: Actúa como el punto de entrada de la aplicación para comandos de usuario.
    def __init__(self, rag_service: RagPort):
        # Propósito: Inicializa el adaptador CLI inyectando el servicio RAG.
        self.rag_service = rag_service

    def run(self):
        # Propósito: Inicia el bucle principal de la CLI para procesar comandos como 'query' e 'ingest'.
        # Imprimir mensaje de bienvenida y comandos disponibles.
        # Bucle infinito para recibir comandos del usuario:
            # Leer la entrada del usuario.
            # Parsear la acción y los argumentos.
            # Si la acción es "query":
                # Si hay argumentos:
                    # Imprimir mensaje de consulta.
                    # Llamar a rag_service.query(args) para obtener una Answer.
                    # Imprimir la respuesta y los documentos fuente (si los hay).
                # Si no hay argumentos:
                    # Imprimir mensaje de uso correcto.
            # Si la acción es "ingest":
                # Si hay argumentos:
                    # Parsear las rutas de archivo.
                    # Imprimir mensaje de ingesta.
                    # Intentar llamar a rag_service.ingest_documents(file_paths).
                    # Imprimir los IDs de los documentos ingeridos o un mensaje de error.
                # Si no hay argumentos:
                    # Imprimir mensaje de uso correcto.
            # Si la acción es "exit":
                # Imprimir mensaje de despedida y salir del bucle.
            # Si la acción es desconocida:
                # Imprimir mensaje de comando desconocido.
        pass # Para indicar que el método está vacío de lógica
