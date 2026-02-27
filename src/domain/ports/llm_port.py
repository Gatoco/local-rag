# src/domain/ports/llm_port.py
# Propósito: Define el puerto de salida para la interacción con un modelo de lenguaje grande (LLM).

from abc import ABC, abstractmethod

class LLMPort(ABC):
    # Propósito: Interfaz para interactuar con un LLM.
    @abstractmethod
    def generate_answer(self, prompt: str) -> str:
        # Propósito: Genera una respuesta basada en un prompt dado.
        pass
