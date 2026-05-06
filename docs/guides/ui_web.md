# UI Web - Sistema RAG Local

Interfaz gráfica web para el sistema RAG construida con **Streamlit**.

---

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip install streamlit
# O
pip install -r requirements.txt
```

### 2. Iniciar la API REST (en otra terminal)

```bash
python run_api.py
```

### 3. Iniciar la UI Web

```bash
# Opción recomendada: usar script
python run_ui.py

# O directamente con streamlit
streamlit run ui/app.py
```

### 4. Abrir en navegador

La UI se abrirá automáticamente en:
- **URL:** http://localhost:8501

---

## 📱 Características

### 💬 Pestaña: Consultar

- **Chat interactivo** con historial de conversación
- **Búsqueda en documentos** con RAG
- **Visualización de fuentes** utilizadas
- **Métricas de consulta**: latencia, número de fuentes
- **Parámetros configurables**: top_k, max_tokens

### 📁 Pestaña: Ingestar Documentos

- **Subida de archivos** PDF, TXT, DOCX
- **Ingesta desde directorio** (vía API)
- **Información de formatos** soportados
- **Feedback visual** del proceso

### 📈 Pestaña: Dashboard

- **Estadísticas en tiempo real**:
  - Consultas totales
  - Latencia promedio
  - Documentos indexados
  - Tiempo de actividad
- **Estado del sistema** (healthy/degraded/unhealthy)
- **Gráfico de rendimiento** histórico
- **Información técnica** del sistema

---

## ⚙️ Configuración

### Sidebar de Configuración

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| **API URL** | URL de la API REST | http://localhost:8000/api/v1 |
| **top_k** | Documentos a recuperar | 4 |
| **max_tokens** | Máximo tokens en respuesta | 512 |

### Variables de Entorno

```bash
# URL de la API (para producción)
export API_URL=http://tu-servidor.com:8000/api/v1

# Puerto de Streamlit
export STREAMLIT_SERVER_PORT=8501
```

---

## 🎨 Mejoras de UX Implementadas

### CLI Mejorada

| Mejora | Descripción |
|--------|-------------|
| **Emojis** | Feedback visual con emojis (🤖 🔍 📚 ✅ ❌) |
| **Word wrap** | Respuestas formateadas a 70 caracteres |
| **Comandos nuevos** | `count`, `clear` para mejor experiencia |
| **Help mejorado** | Ayuda con formato visual |
| **Mensajes de error** | Claros y descriptivos |

### UI Web

| Mejora | Descripción |
|--------|-------------|
| **Diseño responsive** | Funciona en desktop y móvil |
| **Chat histórico** | Mantiene conversación en sesión |
| **Fuentes expandibles** | Ver detalles de fuentes con accordion |
| **Métricas en vivo** | Dashboard actualizado en tiempo real |
| **Feedback de carga** | Spinners durante consultas |
| **Estilos personalizados** | CSS para mejor apariencia |

---

## 📊 Capturas de Pantalla

### Vista Principal (Consultar)

```
┌─────────────────────────────────────────────────────────────┐
│           🤖 Sistema RAG Local                               │
│     Consulta tus documentos con Inteligencia Artificial      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Usuario] ¿Qué es el cálculo diferencial?                   │
│                                                              │
│  [Asistente] El cálculo diferencial estudia las tasas...    │
│                                                              │
│  ⏱️ 2345ms  📚 4 fuentes  📝 mistral-7b                      │
│                                                              │
│  [📚 Ver fuentes detalladas (4)] ▼                          │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  💬 Escribe tu pregunta aquí...                  [Enviar]   │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Dashboard                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   150    │ │  2345ms  │ │   4843   │ │  2h 15m  │       │
│  │Consultas │ │ Latencia │ │Documentos│ │  Activo  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  🏥 Estado del Sistema: ✅ Saludable                         │
│                                                              │
│  ⏱️ Rendimiento Histórico                                   │
│  ╭────────────────────────────────────────────╮             │
│  │    ╱╲    ╱╲                                │             │
│  │   ╱  ╲  ╱  ╲   ╱╲                          │             │
│  │  ╱    ╲╱    ╲ ╱  ╲                         │             │
│  ╰────────────────────────────────────────────╯             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Solución de Problemas

### "Streamlit no está instalado"

```bash
pip install streamlit
# O
python run_ui.py  # Ofrece instalar automáticamente
```

### "API no disponible"

```bash
# Verifica que la API esté corriendo
python run_api.py

# O verifica la URL en el sidebar
http://localhost:8000/api/v1/health
```

### "Puerto 8501 ya está en uso"

```bash
# Usar otro puerto
streamlit run ui/app.py --server.port 8502

# O matar proceso existente
lsof -ti:8501 | xargs kill
```

### "La UI no carga en el navegador"

```bash
# Forzar apertura manual
# Abre en tu navegador: http://localhost:8501

# O deshabilitar headless
streamlit run ui/app.py --server.headless false
```

---

## 🎯 Comandos Útiles

### Desarrollo

```bash
# Con auto-recarga
streamlit run ui/app.py --server.headless false

# En modo producción
streamlit run ui/app.py --server.headless true --server.port 80
```

### Producción

```bash
# Con nginx reverse proxy
# Configurar /etc/nginx/sites-available/rag-ui

server {
    listen 80;
    server_name rag.tudominio.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📚 Recursos

- **Streamlit Docs:** https://docs.streamlit.io/
- **Componentes:** https://streamlit.io/gallery
- **Temas:** https://docs.streamlit.io/library/advanced-features/theming

---

**Versión:** 1.0.0  
**Última actualización:** 25 de marzo 2026
