# src/infrastructure/entrypoints/cli_adapter.py
# Propósito: Adaptador de línea de comandos (CLI) para interactuar con el sistema RAG.

import sys

from src.application.ports.rag_port import RAGPort


class CLIAdapter:
    """Adaptador CLI mejorado con feedback visual."""

    def __init__(self, rag_service: RAGPort):
        """Inicializa el adaptador CLI inyectando el servicio RAG."""
        self.rag_service = rag_service

    def _print_help(self) -> None:
        """Muestra ayuda de comandos."""
        print("\n" + "="*60)
        print("COMANDOS DISPONIBLES".center(60))
        print("="*60)
        print("  ingest-file <ruta>   : Ingesta un archivo (.pdf, .txt, .docx)")
        print("  ingest-dir <ruta>    : Ingesta documentos de un directorio")
        print("  query <pregunta>     : Ejecuta una consulta RAG")
        print("  count                : Muestra número de documentos")
        print("  help                 : Muestra esta ayuda")
        print("  clear                : Limpia la pantalla")
        print("  exit                 : Cierra la aplicación")
        print("="*60 + "\n")

    def _show_progress_bar(self, current: int, total: int, width: int = 40) -> None:
        """Muestra barra de progreso."""
        if total == 0:
            percent = 0.0
        else:
            percent = float(current / total)

        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)

        sys.stdout.write(f'\r[{bar}] {percent*100:.1f}%')
        sys.stdout.flush()

        if current >= total:
            print()  # Nueva línea al completar

    def run(self) -> None:
        """Inicia el bucle de comandos de la CLI."""
        print("\n" + "="*60)
        print("SISTEMA RAG LOCAL - CLI INTERACTIVA".center(60))
        print("="*60)
        print("\nEscribe 'help' para ver comandos disponibles")
        print("="*60 + "\n")

        while True:
            try:
                raw = input("🤖 rag> ").strip()
                if not raw:
                    continue

                parts = raw.split(maxsplit=1)
                command = parts[0].lower()
                arg = parts[1].strip() if len(parts) > 1 else ""

                if command == "help":
                    self._print_help()

                elif command in {"exit", "quit", "salir"}:
                    print("\n" + "="*60)
                    print("¡Hasta luego! Cerrando sistema RAG local.".center(60))
                    print("="*60 + "\n")
                    break

                elif command == "clear":
                    # Limpiar pantalla
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\n" + "="*60)
                    print("SISTEMA RAG LOCAL - CLI INTERACTIVA".center(60))
                    print("="*60 + "\n")

                elif command == "count":
                    try:
                        count = self.rag_service.get_document_count()
                        print(f"\n📊 Documentos en índice: {count}\n")
                    except Exception as e:
                        print(f"\n❌ Error: {e}\n")

                elif command == "ingest-file":
                    if not arg:
                        print("\n⚠️  Uso: ingest-file <ruta>\n")
                        continue

                    print(f"\n📥 Ingestando archivo: {arg}")
                    try:
                        self.rag_service.ingest_document(arg)
                        print("✅ ¡Archivo ingerido correctamente!\n")
                    except FileNotFoundError:
                        print(f"\n❌ Error: Archivo no encontrado: {arg}\n")
                    except Exception as exc:
                        print(f"\n❌ Error: {exc}\n")

                elif command == "ingest-dir":
                    if not arg:
                        print("\n⚠️  Uso: ingest-dir <ruta>\n")
                        continue

                    print(f"\n📂 Ingestando directorio: {arg}")
                    try:
                        self.rag_service.ingest_directory(arg)
                        print("✅ ¡Directorio ingerido correctamente!\n")
                    except FileNotFoundError:
                        print(f"\n❌ Error: Directorio no encontrado: {arg}\n")
                    except Exception as exc:
                        print(f"\n❌ Error: {exc}\n")

                elif command == "query":
                    if not arg:
                        print("\n⚠️  Uso: query <pregunta>\n")
                        continue

                    print(f"\n🔍 Consultando: {arg[:80]}{'...' if len(arg) > 80 else ''}")
                    print("-"*60)

                    try:
                        result = self.rag_service.ask(arg)

                        # Mostrar respuesta con formato
                        print("\n💬 RESPUESTA:\n")
                        answer = result.get('answer', '')

                        # Word wrap simple
                        words = answer.split()
                        line = ""
                        for word in words:
                            if len(line) + len(word) > 70:
                                print(f"  {line}")
                                line = word
                            else:
                                line += " " + word if line else word
                        if line:
                            print(f"  {line}")

                        # Mostrar fuentes
                        sources = result.get('source_documents', [])
                        if sources:
                            print(f"\n📚 FUENTES ({len(sources)}):")
                            print("-"*60)
                            seen = set()
                            for i, doc in enumerate(sources, 1):
                                source = doc.metadata.get('source', 'desconocido')
                                if source not in seen:
                                    page = doc.metadata.get('page', '')
                                    page_info = f" (pág. {page})" if page else ''
                                    print(f"  {i}. {source}{page_info}")
                                    seen.add(source)

                        print("\n" + "="*60 + "\n")

                    except Exception as exc:
                        print(f"\n❌ Error: {exc}\n")

                else:
                    print(f"\n⚠️  Comando desconocido: {command}")
                    print("Escribe 'help' para ver comandos disponibles.\n")

            except KeyboardInterrupt:
                print("\n\n" + "="*60)
                print("⚠️  Interrupción detectada. Escribe 'exit' para salir.".center(60))
                print("="*60 + "\n")
            except Exception as exc:
                print(f"\n❌ Error inesperado: {exc}\n")
