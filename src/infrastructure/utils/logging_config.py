"""
Configuración de logging estructurado para el sistema RAG.

Proporciona:
- Logs en formato JSON para producción
- Logs legibles para desarrollo
- Rotación de archivos automática
- Niveles de log configurables
"""

import logging
import sys
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para terminal."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    json_format: bool = False,
    log_dir: str = "./logs"
) -> None:
    """
    Configura el sistema de logging para la aplicación.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo de log (opcional, rota automáticamente)
        json_format: Usar formato JSON para producción
        log_dir: Directorio para archivos de log
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Limpiar handlers existentes
    root_logger.handlers.clear()

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if json_format:
        console_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Handler para archivo (si se especifica)
    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Rotación por tamaño (10 MB)
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_path / log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        if json_format:
            file_formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "function": "%(funcName)s", '
                '"line": %(lineno)d, "message": "%(message)s"}'
            )
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Capturar warnings de terceros
    logging.captureWarnings(True)

    # Logs de inicialización
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configurado: nivel={level}, archivo={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con nombre específico.

    Args:
        name: Nombre del logger (usualmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Logger por defecto para imports
logger = get_logger(__name__)
