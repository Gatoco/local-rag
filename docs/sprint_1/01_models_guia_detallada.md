# SPRINT 1: Guía Detallada - Escribir `models.py`

## 📚 Índice
1. [¿Qué es models.py?](#qué-es-modelspy)
2. [Conceptos Base](#conceptos-base)
3. [Guía Paso a Paso](#guía-paso-a-paso)
4. [Análisis Línea por Línea](#análisis-línea-por-línea)
5. [Decisiones de Diseño](#decisiones-de-diseño)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Errores Comunes](#errores-comunes)

---

## ¿Qué es `models.py`?

`models.py` es el **corazón del dominio** (Domain-Driven Design). Aquí definimos los **tipos de datos puros** que representa el negocio.

### Analogía del Mundo Real

Imagina que estás constructing un edificio:
- **`models.py`**: Los planos arquitectónicos. Define QUÉ es un muro, QUÉ es una puerta.
- **El resto del código**: El proceso de construcción, materiales, trabajadores.

Si los planos están mal, todo lo demás se cae. Si están bien, cualquiera puede construir correctamente.

### ¿Por qué separar models?

```
❌ INCORRECTO:
- Todo mezclado en un archivo
- Cambios en la base de datos rompen la lógica
- No se entiende qué datos son realmente importantes

✅ CORRECTO (nuestro enfoque):
- models.py = Datos puros (independiente de tecnología)
- Adapters = ChromaDB, Ollama, etc.
- Si cambias de BD, models.py no se toca
```

---

## Conceptos Base

### 1. **Dataclasses**

Una `dataclass` es una forma de Python para crear clases de **datos simple y automático**.

```python
from dataclasses import dataclass

@dataclass
class Persona:
    nombre: str
    edad: int
```

**Sin dataclass**, sería así (incómodo):

```python
class Persona:
    def __init__(self, nombre: str, edad: int):
        self.nombre = nombre
        self.edad = edad
    
    def __repr__(self):
        return f"Persona(nombre={self.nombre}, edad={self.edad})"
    
    def __eq__(self, other):
        return self.nombre == other.nombre and self.edad == other.edad
```

**Con `@dataclass`, Python genera todo automáticamente.** Mucho más limpio.

### 2. **Type Hints (Anotaciones de Tipo)**

```python
nombre: str        # ← Esta variable es de tipo 'string' (texto)
edad: int          # ← Esta variable es de tipo 'entero'
scores: List[float]  # ← Una LISTA de números flotantes
```

**¿Por qué type hints?**
- IDE ayuda a autocompletar ✓
- Detecta errores antes de ejecutar ✓
- Código autodocumentado ✓
- Facilita debugging ✓

### 3. **`field()` y `default_factory`**

```python
from dataclasses import field, dataclass

@dataclass
class Ejemplo:
    nombre: str
    tags: List[str] = field(default_factory=list)
    #                        ↑
    #                 "Crea una lista vacía por defecto"
```

**¿Por qué `default_factory=list` en vez de `[]`?**

❌ **Incorrecto:**
```python
@dataclass
class Documento:
    metadatos: Dict = {}  # PELIGRO: Todos los documentos compartirían el mismo dict
```

```python
doc1 = Documento()
doc1.metadatos["autor"] = "Juan"

doc2 = Documento()
print(doc2.metadatos)  # {'autor': 'Juan'} ← ¡También tiene los datos de doc1!
```

✅ **Correcto:**
```python
@dataclass
class Documento:
    metadatos: Dict = field(default_factory=dict)  # Cada instancia obtiene su propio dict
```

```python
doc1 = Documento()
doc1.metadatos["autor"] = "Juan"

doc2 = Documento()
print(doc2.metadatos)  # {} ← Vacío, como debe ser
```

### 4. **Optional (Campos Opcionales)**

```python
from typing import Optional

@dataclass
class Usuario:
    nombre: str           # OBLIGATORIO
    email: Optional[str] = None  # OPCIONAL (puede ser None)
```

**Uso:**
```python
usuario1 = Usuario(nombre="Ana")  # ✓ Válido, email es None
usuario2 = Usuario(nombre="Bob", email="bob@example.com")  # ✓ Válido con email
```

---

## Guía Paso a Paso

### Paso 0: Preparar el Archivo

**Primero**, abre o crea el archivo:
```
src/domain/models.py
```

### Paso 1: Importaciones Necesarias

Escribe exactamente esto:

```python
# src/domain/models.py
# Propósito: Define los modelos de datos fundamentales del dominio RAG.
# Estos modelos representan la esencia del negocio: Documentos, Consultas, Respuestas.
# Son completamente independientes de tecnologías externas (BD, LLM, etc).

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
```

**Explicación de cada import:**

| Import | Qué es | Qué hace |
|--------|--------|----------|
| `List` | Type hint para listas | Indica "una lista de X" |
| `Dict` | Type hint para diccionarios | Indica "un diccionario con clave-valor" |
| `Any` | Type hint "cualquier tipo" | Para datos que pueden ser cualquier tipo |
| `Optional` | Type hint "puede ser None" | Para campos opcionales |
| `dataclass` | Decorador | Convierte la clase en una dataclass automáticament |
| `field` | Función auxiliar | Para configurar valores por defecto complejos |

**¿Por qué necesitamos estos imports?**
- Sin ellos, Python no entiende `List[int]`, `Optional[str]`, etc.
- Sin `dataclass` y `field`, tendríamos que escribir 50 líneas de código plumbing.

### Paso 2: Crear la clase `Document`

Escribe:

```python
@dataclass
class Document:
    """
    Representa un fragmento de contenido de texto con metadatos.
    
    Es el objeto fundamental que fluye por todo el sistema RAG:
    1. Se carga de un archivo
    2. Se divide en chunks
    3. Se genera su embedding
    4. Se almacena en ChromaDB
    5. Se retorna como fuente en respuestas
    """
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
```

**Análisis de cada línea:**

```python
@dataclass  # ← Decorador: "Python, haz this una dataclass"
class Document:  # ← Nombre: debe ser SINGULAR (un documento)
    """..."""  # ← Docstring: explica para qué sirve esta clase
    
    page_content: str  
    # ↑ ATRIBUTO 1
    # ├─ page_content: El nombre
    # ├─ : Separador
    # ├─ str: Tipo (siempre es un string de texto)
    # └─ OBLIGATORIO (sin valor por defecto)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    # ↑ ATRIBUTO 2
    # ├─ metadata: El nombre (plural porque es una colección)
    # ├─ Dict[str, Any]: Tipo = diccionario
    # │  ├─ str: Las claves son strings
    # │  └─ Any: Los valores pueden ser CUALQUIER cosa
    # ├─ = field(...): Valor por defecto
    # │  └─ default_factory=dict: Crea un {} vacío por cada instancia
    # └─ OPCIONAL (tiene valor por defecto)
    
    id: Optional[str] = None
    # ↑ ATRIBUTO 3
    # ├─ id: El nombre (identificador único del documento)
    # ├─ Optional[str]: Puede ser string o None
    # ├─ = None: Valor por defecto es None
    # └─ OPCIONAL (puede que no tenga ID al crear)
```

**¿Por qué estos atributos?**

| Atributo | Por qué existe | Ejemplo |
|----------|----------------|---------|
| `page_content` | El contenido real que queremos procesar | "Python es un lenguaje de programación..." |
| `metadata` | Información sobre el documento | `{"fuente": "wikipedia", "fecha": "2024-02-26"}` |
| `id` | Identificador único en la BD | `"doc_123_chunk_5"` |

### Paso 3: Crear la clase `Query`

Escribe:

```python
@dataclass
class Query:
    """
    Representa una consulta del usuario al sistema RAG.
    
    Es muy simple: solo contiene la pregunta en texto.
    El resto (embedding, búsqueda, etc) lo hace el sistema.
    """
    text: str
```

**Análisis:**

```python
@dataclass  # ← Dataclass (igual que Document)
class Query:  # ← SINGULAR: una sola consulta
    """..."""  # ← Docstring
    
    text: str  # ← Solo tiene un atributo: el texto de la pregunta
               # Tipo: string (texto)
               # OBLIGATORIO
```

**¿Por qué es tan simple?**
- Podría tener más (traducción automática, idioma detectado, usuario_id, etc)
- Pero la regla de oro: **mantener simple lo que es simple**
- Cuando necesitemos más, lo agregamos fácilmente

### Paso 4: Crear la clase `Answer`

Escribe:

```python
@dataclass
class Answer:
    """
    Representa la respuesta generada por el sistema RAG.
    
    Contiene:
    1. El texto de la respuesta
    2. Los documentos que usamos como fuente (trazabilidad)
    
    Esto permite al usuario saber EN QUÉ documentos se basó la IA.
    Es fundamental para confianza y auditoría.
    """
    text: str
    source_documents: List[Document] = field(default_factory=list)
```

**Análisis:**

```python
@dataclass
class Answer:
    """..."""
    
    text: str
    # ↑ El texto de la respuesta
    # Tipo: string
    # OBLIGATORIO
    
    source_documents: List[Document] = field(default_factory=list)
    # ↑ Lista de documentos que usamos
    # Type: List[Document]
    # ├─ List: Es una LISTA
    # ├─ [Document]: Cada elemento es un objeto Document
    # ├─ = field(default_factory=list): Por defecto, lista vacía
    # └─ OPCIONAL (puede que no tenemos documentos relevantes)
```

**¿Por qué `List[Document]`?**

```
Porque cada Answer se construye A PARTIR de un set de Documents.
Si quitamos los documentos fuente, pierden trazabilidad.

Ejemplo:

Pregunta: "¿Qué es machine learning?"

Answer retornado:
{
    text: "Machine Learning es un subcampo de la IA que permite...",
    source_documents: [
        Document(page_content="Machine Learning es...", metadata={...}),
        Document(page_content="En Machine Learning, los algoritmos...", metadata={...})
    ]
}

El usuario puede:
1. Leer la respuesta
2. Ver en qué documentos se basó
3. Confiar en la respuesta o investigar más
```

---

## Análisis Línea por Línea

Aquí está el archivo completo con comentarios explicativos detallados:

```python
# src/domain/models.py
# ═══════════════════════════════════════════════════════════════════════════
# PROPÓSITO: Define los MODELOS DE DATOS del dominio RAG.
#
# ¿Qué es esto?
# - Un "modelo de datos" es una estructura que representa información.
# - Por ejemplo, un Documento, una Consulta, una Respuesta.
#
# ¿Por qué existe?
# - El dominio (la lógica del negocio) necesita trabajar con conceptos claros.
# - No queremos que la "representación en BD" afecte la lógica.
# - ¿Cambias de BD? El modelo sigue siendo el mismo.
#
# ¿Por qué en `domain/` y no en `application/`?
# - Domain = Lógica de negocio PURA, sin dependencias externas.
# - Application = Cómo USE el dominio, agregando servicios.
# ═══════════════════════════════════════════════════════════════════════════

from typing import List, Dict, Any, Optional
# ↑ Importamos los "type hints" necesarios
# List: para listas, Dict: para diccionarios, Any: tipo flexible, Optional: nulo

from dataclasses import dataclass, field
# ↑ Importamos dataclass (conversor automático de código plumbing)
# ↑ Importamos field (para configurar valores por defecto complejos)


# ═══════════════════════════════════════════════════════════════════════════
# MODELO 1: Document
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
# ↑ DECORADOR: Transforma esta clase en una "dataclass"
# ↑ Esto genera automáticamente __init__, __repr__, __eq__, etc.
class Document:
    """
    Representa UN fragmento de contenido de texto con metadatos opcionales.
    
    En el contexto de RAG, un Document es:
    - Un trozo de texto (chunk) de un documento original
    - Puede tener metadatos: dónde viene, página, sección, etc.
    - Tiene un ID opcional para tracking en la BD vectorial
    
    Ciclo de vida de un Document:
    1. Se CARGA de un archivo (CSV, PDF, etc) vía DocumentLoaderPort
    2. Se DIVIDE en chunks (si es muy grande) vía split_documents()
    3. Se le genera un EMBEDDING (representación vectorial) vía EmbeddingPort
    4. Se ALMACENA en ChromaDB vía DocumentStorePort.add_documents()
    5. Se RETORNA como "fuente" en Answer cuando es relevante
    
    Ejemplo de uso:
    >>> doc = Document(
    ...     page_content="Python es un lenguaje de programación",
    ...     metadata={"source": "wikipedia", "page": 1},
    ...     id="doc_001"
    ... )
    >>> doc.page_content
    "Python es un lenguaje de programación"
    """
    
    page_content: str
    # ↑ ATRIBUTO 1: El contenido de texto
    # │
    # ├─ Nombre: "page_content"
    # │  └─ Sigue convención de LangChain (interoperabilidad)
    # │
    # ├─ Tipo: str (string = texto)
    # │  └─ Siempre es texto, nunca bytes ni números
    # │
    # └─ Valor por defecto: NINGUNO (OBLIGATORIO)
    #    └─ Si no proporcionas page_content, error al instanciar
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    # ↑ ATRIBUTO 2: Metadatos (información sobre el documento)
    # │
    # ├─ Nombre: "metadata" (plural porque es una colección)
    # │
    # ├─ Tipo: Dict[str, Any]
    # │  ├─ Dict: Es un DICCIONARIO (clave-valor)
    # │  ├─ [str, Any]: Claves son strings, valores son CUALQUIER tipo
    # │  └─ Ejemplo: {"fuente": "wikipedia", "pagina": 5, "valido": True}
    # │
    # └─ Valor por defecto: {}  (diccionario vacío)
    #    ├─ Se especifica con field(default_factory=dict)
    #    ├─ default_factory=dict: Crea un nuevo {} para cada instancia
    #    └─ Nota: NO usamos default={} porque sería compartido entre instancias
    
    id: Optional[str] = None
    # ↑ ATRIBUTO 3: Identificador único del documento (generado por BD)
    # │
    # ├─ Nombre: "id"
    # │
    # ├─ Tipo: Optional[str]
    # │  ├─ Optional: Puede ser str O None
    # │  ├─ str: Cuando sí tiene ID (ej: "doc_xyz_123")
    # │  └─ None: Cuando aún no se ha guardado en BD
    # │
    # └─ Valor por defecto: None (no tiene ID inicialmente)
    #    └─ Se asigna después de guardarlo en ChromaDB


# ═══════════════════════════════════════════════════════════════════════════
# MODELO 2: Query
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
# ↑ DECORADOR dataclass (igual que Document)
class Query:
    """
    Representa UNA CONSULTA (pregunta) del usuario al sistema RAG.
    
    Es deliberadamente sencilla porque:
    - La complejidad está en PROCESAR la query, no en representarla
    - Solo necesitamos el texto de la pregunta
    - El sistema decide cómo procesarla
    
    Ciclo de vida de una Query:
    1. Usuario escribe: "¿Cuál es el impacto financiero?"
    2. Se crea Query(text="¿Cuál es el impacto financiero?")
    3. RAGService.query() recibe esta Query
    4. Se genera embedding de la query
    5. Se buscan documentos similares
    6. Se retorna una Answer
    
    Ejemplo de uso:
    >>> query = Query(text="¿Qué es Python?")
    >>> query.text
    "¿Qué es Python?"
    """
    
    text: str
    # ↑ ATRIBUTO ÚNICO: El texto de la pregunta
    # │
    # ├─ Nombre: "text"
    # │
    # ├─ Tipo: str (siempre texto)
    # │
    # └─ Valor por defecto: NINGUNO (OBLIGATORIO)
    #    └─ Una query sin texto no tiene sentido


# ═══════════════════════════════════════════════════════════════════════════
# MODELO 3: Answer
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
# ↑ DECORADOR dataclass
class Answer:
    """
    Representa UNA RESPUESTA generada por el sistema RAG.
    
    Contiene dos partes clave:
    1. text: El contenido de la respuesta (generado por LLM)
    2. source_documents: Los documentos que sustentan esta respuesta
    
    ¿Por qué incluir source_documents?
    - TRAZABILIDAD: El usuario sabe en qué se basa la respuesta
    - AUDITORÍA: Podés verificar si la IA usó buenas fuentes
    - CONFIANZA: Las respuestas con fuentes son más creíbles
    - DEBUGGING: Si la respuesta es mala, puedes mirar qué documentos se usaron
    
    Ciclo de vida de una Answer:
    1. RAGService.query() recibe una Query
    2. Busca documentos similares
    3. Construye un prompt con esos documentos
    4. LLM genera respuesta
    5. Se crea Answer(text=respuesta_generada, source_documents=docs_usados)
    6. Se retorna al usuario con trazabilidad completa
    
    Ejemplo de uso:
    >>> doc1 = Document(page_content="Python es un lenguaje interpretado...")
    >>> answer = Answer(
    ...     text="Python es un lenguaje de programación interpretado y dinámico.",
    ...     source_documents=[doc1]
    ... )
    >>> answer.text
    "Python es un lenguaje de programación interpretado y dinámico."
    >>> len(answer.source_documents)
    1
    """
    
    text: str
    # ↑ ATRIBUTO 1: El texto de la respuesta
    # │
    # ├─ Nombre: "text"
    # │
    # ├─ Tipo: str (siempre texto)
    # │  └─ Generado por el LLM (Ollama, en nuestro caso)
    # │
    # └─ Valor por defecto: NINGUNO (OBLIGATORIO)
    #    └─ Una Answer sin respuesta no tiene sentido
    
    source_documents: List[Document] = field(default_factory=list)
    # ↑ ATRIBUTO 2: Los documentos que sustentan la respuesta
    # │
    # ├─ Nombre: "source_documents" (plural, es una lista)
    # │
    # ├─ Tipo: List[Document]
    # │  ├─ List: Es una Lista (colección ordenada)
    # │  └─ [Document]: Cada elemento es un objeto de clase Document
    # │
    # ├─ Valor por defecto: [] (lista vacía)
    # │  ├─ Se especifica con field(default_factory=list)
    # │  └─ default_factory=list: Crea una nueva [] para cada instancia
    # │
    # └─ ¿Por qué Optional implícitamente?
    #    └─ Porque la lista puede estar vacía (pero sigue siendo una lista)
```

---

## Decisiones de Diseño

### ¿Por qué Document, Query y Answer? (3 modelos, no más, no menos)

```
Document ← Representa el CONOCIMIENTO (los datos que ingests)
Query    ← Representa la PREGUNTA (lo que el usuario quiere saber)
Answer   ← Representa la RESPUESTA (lo que el sistema genera)

Cada una es una TRANSFORMACIÓN:
    Documentos → (+ Query) → Búsqueda → Contexto → (LLM) → Answer
```

### ¿Por qué no usar diccionarios simples?

❌ **Incorrecto:**
```python
# Sin modelos, todo es un dict anónimo
document = {"page_content": "...", "metadata": {}, "id": None}
query = {"text": "..."}
answer = {"text": "...", "source_documents": []}
```

**Problemas:**
- IDE no sabe qué campos tiene
- Errores de tipado no se detectan
- No hay validación
- Confuso: ¿qué significa cada dict?

✅ **Correcto:**
```python
document = Document(page_content="...", metadata={}, id=None)
query = Query(text="...")
answer = Answer(text="...", source_documents=[])
```

**Ventajas:**
- IDE autocompleta `document.page_content` ✓
- Python valida tipos ✓
- Código autodocumentado ✓
- Fácil de usar y leer ✓

### ¿Por qué metadata es un Dict[str, Any]?

Porque **no sabemos qué metadatos necesitaremos en el futuro**.

```
Hoy:
doc = Document(
    page_content="...",
    metadata={"fuente": "wikipedia"}
)

Mañana:
doc = Document(
    page_content="...",
    metadata={
        "fuente": "wikipedia",
        "fecha": "2024-02-26",
        "idioma": "es",
        "relevancia_score": 0.95,
        "section": "Introduction"
    }
)

Dict[str, Any] es lo suficientemente flexible para ambos casos.
```

### ¿Por qué id es Optional[str]?

Porque el ID viene **de la base de datos**, no del usuario.

```
Flujo:
1. Usuario crea Document(page_content="...")
   └─ id = None (aún no saved)

2. Se llama a DocumentStorePort.add_documents([document])
   └─ ChromaDB asigna un ID automático

3. El documento retornado tiene:
   document.id = "doc_xyz_123"  (ahora es str)
```

---

## Ejemplos de Uso

### Ejemplo 1: Crear un Document simple

```python
from src.domain.models import Document

# Crear un documento
doc = Document(
    page_content="Python es un lenguaje de programación interpretado."
)

print(doc.page_content)
# Output: Python es un lenguaje de programación interpretado.

print(doc.metadata)
# Output: {} (diccionario vacío, no especificamos metadata)

print(doc.id)
# Output: None (no tiene ID aún)
```

### Ejemplo 2: Crear un Document con metadatos

```python
doc = Document(
    page_content="El cambio climático es...",
    metadata={
        "fuente": "IPCC",
        "fecha": "2023-04-10",
        "tipo": "reporte_científico",
        "confiabilidad": 0.99
    },
    id="doc_scientific_001"
)

print(doc.metadata["fuente"])
# Output: IPCC

print(doc.metadata["confiabilidad"])
# Output: 0.99
```

### Ejemplo 3: Crear una Query

```python
from src.domain.models import Query

query = Query(text="¿Cuál es el impacto del cambio climático?")

print(query.text)
# Output: ¿Cuál es el impacto del cambio climático?
```

### Ejemplo 4: Crear una Answer con fuentes

```python
from src.domain.models import Document, Answer

# Crear documentos fuente
doc1 = Document(
    page_content="El cambio climático causa aumento de temperaturas...",
    metadata={"fuente": "IPCC"}
)
doc2 = Document(
    page_content="Los océanos absorben CO2 y se acidifican...",
    metadata={"fuente": "Nature"}
)

# Crear respuesta con esos documentos como fuente
answer = Answer(
    text="El cambio climático tiene múltiples impactos: aumento de temperaturas y acidificación oceánica.",
    source_documents=[doc1, doc2]
)

print(answer.text)
# Output: El cambio climático tiene múltiples impactos...

print(len(answer.source_documents))
# Output: 2

print(answer.source_documents[0].metadata)
# Output: {'fuente': 'IPCC'}
```

### Ejemplo 5: Iterar sobre source_documents

```python
answer = Answer(
    text="La respuesta es...",
    source_documents=[doc1, doc2, doc3]
)

# Iterar y mostrar cada fuente
for i, doc in enumerate(answer.source_documents, 1):
    print(f"Fuente {i}: {doc.page_content[:50]}...")
    print(f"  Metadatos: {doc.metadata}")
```

---

## Errores Comunes

### Error 1: Olvidar el `@dataclass`

❌ **Incorrecto:**
```python
class Document:  # ← Falta @dataclass
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

doc = Document("Hola")
# TypeError: __init__() takes 1 positional argument but 2 were given
```

✅ **Correcto:**
```python
@dataclass
class Document:
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

doc = Document("Hola")  # ✓ Funciona
```

### Error 2: Usar `=` en vez de `field()` para listas/dicts

❌ **Incorrecto:**
```python
@dataclass
class Answer:
    text: str
    source_documents: List[Document] = []  # ← PELIGRO

answer1 = Answer("Resp 1")
answer1.source_documents.append(doc1)

answer2 = Answer("Resp 2")
print(answer2.source_documents)
# Output: [doc1]  ← ¡Debería estar vacío!
```

Por qué: Python evalúa `[]` UNA SOLA VEZ, y todas las instancias la comparten.

✅ **Correcto:**
```python
@dataclass
class Answer:
    text: str
    source_documents: List[Document] = field(default_factory=list)

answer1 = Answer("Resp 1")
answer1.source_documents.append(doc1)

answer2 = Answer("Resp 2")
print(answer2.source_documents)
# Output: []  ← Correcto, está vacío
```

### Error 3: Olvificar imports

❌ **Incorrecto:**
```python
@dataclass
class Document:
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    # NameError: name 'Dict' is not defined
```

✅ **Correcto:**
```python
from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class Document:
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Error 4: Confundir `List` (type hint) con `list` (constructor)

❌ **Ambiguo:**
```python
from typing import List

source_documents: list = []  # ← type hint de nivel bajo, sin especificar qué contiene

# vs

source_documents: List = []  # ← type hint sin especificar qué contiene

# vs

source_documents: List[Document] = field(default_factory=list)  # ← Correcto, especifica contenido
```

✅ **Siempre especifica el contenido:**
```python
source_documents: List[Document] = field(default_factory=list)  # ← Clarísimo
```

---

## Resumen: Lo que acabas de aprender

| Concepto | Qué es | Por qué importa |
|----------|--------|-----------------|
| **models.py** | Definición de tipos de datos | Son la verdad fundamental del sistema |
| **@dataclass** | Decorador que genera __init__, etc | Evita escribir código boilerplate |
| **Type hints** | Anotaciones de tipo (str, List, etc) | IDE entiende el código, menos errores |
| **field()** | Configurador de defaults complejos | Evita compartir datos entre instancias |
| **Optional[T]** | Puede ser T o None | Representa campos opcionales |
| **List[T]** | Lista de elementos de tipo T | Especifica qué contiene la lista |
| **Dict[K, V]** | Diccionario con claves K y valores V | Representa datos estructurados flexibles |

---

## Próximos Pasos

Después de entender models.py completamente:

1. ✅ **Ahora**: Escribir el archivo `src/domain/models.py` completo
2. **Luego**: Documentar cada Port (interfaces que implementarán los adapters)
3. **Después**: Crear excepciones personalizadas
4. **Final Sprint 1**: Testing de los modelos

---

## Preguntas Frecuentes

**P: ¿Puedo agregar más atributos a los modelos?**
R: Sí, perfectamente. Ejemplo: agregar `Document.chunk_size` o `Query.idioma_original`. El diseño es extensible.

**P: ¿Qué pasa si metadata contiene tipos complejos?**
R: `Dict[str, Any]` lo permite. Puedes guardar listas, dicts anidados, objetos, etc. Aunque manténlo simple.

**P: ¿Por qué no usamos TypedDict en vez de Dict?**
R: TypedDict es más estricto, pero añade complejidad. Dict[str, Any] es flexible y suficiente ahora.

**P: ¿Estos modelos cambian con el tiempo?**
R: Sí, evolucionan. Pero LENTAMENTE. Cambios en models.py afectan TODO el sistema, así que son deliberados.

---

**Ahora sí, estás listo para escribir `models.py`. ¡Adelante!** 🚀
