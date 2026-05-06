# Seguridad y Deployment - Sistema RAG Local

Guía completa para desplegar el sistema RAG de forma segura en producción.

---

## 🔐 **SEGURIDAD**

### Autenticación JWT

La API ahora requiere autenticación JWT para todos los endpoints (excepto `/health`).

#### 1. Obtener Token

```bash
curl -X POST http://localhost:8000/api/v1/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 2. Usar Token en Requests

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{"question": "¿Qué es RAG?"}'
```

#### 3. Usuarios por Defecto

| Usuario | Contraseña | Rol | Permisos |
|---------|------------|-----|----------|
| `admin` | `admin123` | admin | Todos los endpoints |
| `user` | `user123` | user | Solo consultas |

**⚠️ IMPORTANTE:** Cambia las contraseñas en producción!

```bash
# En tu archivo .env
ADMIN_PASSWORD=tu-password-seguro-admin
USER_PASSWORD=tu-password-seguro-user
```

---

### Rate Limiting

La API incluye rate limiting para prevenir abusos:

| Límite | Valor |
|--------|-------|
| Requests por minuto | 60 |
| Requests por hora | 1000 |
| Burst (por segundo) | 10 |

**Headers de Rate Limit:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1647382800
```

**Respuesta 429 (Too Many Requests):**
```json
{
  "detail": "Demasiadas solicitudes",
  "error": "rate_limit_exceeded",
  "retry_after": "1647382800"
}
```

---

## 🐳 **DOCKER**

### Build Manual

```bash
# Construir imagen
docker build -t local-rag .

# Ejecutar contenedor
docker run -d \
  -p 8000:8000 \
  -p 8501:8501 \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/models:/app/models \
  -e JWT_SECRET_KEY=tu-secret-key \
  -e ADMIN_PASSWORD=tu-admin-password \
  local-rag
```

### Docker Compose (Recomendado)

```bash
# 1. Configurar variables de entorno
cp .env.example .env

# Editar .env con tus valores
nano .env

# 2. Iniciar todos los servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f

# 4. Detener
docker-compose down

# 5. Detener y eliminar volúmenes (¡cuidado!)
docker-compose down -v
```

### Servicios Incluidos

| Servicio | Puerto | Propósito |
|----------|--------|-----------|
| `rag-api` | 8000 | API REST |
| `rag-ui` | 8501 | UI Web (Streamlit) |
| `redis` | 6379 | Caché (opcional) |
| `backup` | - | Backup automático |

---

## 🔒 **HTTPS/TLS**

### Opción 1: Reverse Proxy con Nginx

```nginx
# /etc/nginx/sites-available/rag-api
server {
    listen 80;
    server_name rag.tudominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name rag.tudominio.com;
    
    # Certificados SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/rag.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rag.tudominio.com/privkey.pem;
    
    # Configuración SSL segura
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Proxy a la API
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Proxy a la UI
    location /ui {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Obtener certificado SSL (Let's Encrypt):**
```bash
sudo apt install certbot
sudo certbot certonly --standalone -d rag.tudominio.com
```

### Opción 2: Traefik (con Docker)

```yaml
# docker-compose.yml (agregar)
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=tu@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - rag-network
```

---

## 💾 **BACKUP AUTOMÁTICO**

### Configuración

El servicio de backup crea copias automáticas cada hora:

```yaml
# docker-compose.yml
backup:
  image: alpine:latest
  volumes:
    - ./chroma_db:/source/chroma_db
    - ./backups:/backup
  environment:
    - BACKUP_INTERVAL=3600  # 1 hora
```

### Comandos de Backup

```bash
# Backup manual
docker-compose exec backup tar -czf /backup/manual_backup.tar.gz -C /source chroma_db

# Listar backups
ls -lh backups/

# Restaurar backup
tar -xzf backups/chroma_db_20240325_120000.tar.gz -C ./

# Eliminar backups antiguos (más de 30 días)
find backups/ -name "*.tar.gz" -mtime +30 -delete
```

### Backup Remoto (S3, GCS, etc.)

```bash
#!/bin/bash
# backup-remote.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="chroma_db_${TIMESTAMP}.tar.gz"

# Crear backup
tar -czf /tmp/${BACKUP_FILE} -C ./ chroma_db

# Subir a S3
aws s3 cp /tmp/${BACKUP_FILE} s3://tu-bucket/backups/${BACKUP_FILE}

# Subir a Google Cloud Storage
gsutil cp /tmp/${BACKUP_FILE} gs://tu-bucket/backups/${BACKUP_FILE}

# Limpiar
rm /tmp/${BACKUP_FILE}
```

**Cron job (cada 6 horas):**
```bash
# crontab -e
0 */6 * * * /path/to/backup-remote.sh
```

---

## 🚀 **DEPLOYMENT EN PRODUCCIÓN**

### Checklist Pre-Deployment

- [ ] Cambiar `JWT_SECRET_KEY` (usar valor aleatorio)
- [ ] Cambiar contraseñas de admin y user
- [ ] Configurar HTTPS/TLS
- [ ] Configurar firewall (solo puertos 80, 443)
- [ ] Configurar backup automático
- [ ] Configurar monitoreo (logs, métricas)
- [ ] Probar autenticación
- [ ] Probar rate limiting
- [ ] Documentar IPs de whitelist

### Generar JWT_SECRET_KEY Seguro

```bash
# Opción 1: OpenSSL
openssl rand -hex 32

# Opción 2: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opción 3: /dev/urandom
head -c 32 /dev/urandom | base64
```

### Variables de Entorno para Producción

```bash
# .env de producción
JWT_SECRET_KEY=7f8a9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
ADMIN_PASSWORD=SuperSeguro123!
USER_PASSWORD=UsuarioSeguro456!

# Rate limiting más estricto
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500

# Whitelist de IPs (oficina, VPN)
RATE_LIMIT_WHITELIST=192.168.1.0/24,10.0.0.0/8
```

### Monitoreo

```bash
# Ver logs en tiempo real
docker-compose logs -f rag-api

# Ver métricas de contenedores
docker stats

# Health check manual
curl http://localhost:8000/api/v1/health

# Ver usuarios conectados
docker-compose exec rag-api cat logs/rag.log | grep "authenticated"
```

---

## 📊 **MÉTRICAS DE SEGURIDAD**

### Endpoints de Monitoreo

| Endpoint | Descripción | Auth Requerida |
|----------|-------------|----------------|
| `GET /api/v1/health` | Estado del sistema | ❌ |
| `GET /api/v1/metrics` | Métricas de rendimiento | ✅ |
| `GET /api/v1/me` | Usuario actual | ✅ |
| `POST /api/v1/token` | Obtener token | ❌ |

### Logs de Seguridad

Los siguientes eventos se loguean:

```
2026-03-25 10:30:45 | INFO | Auth | User admin authenticated successfully
2026-03-25 10:31:02 | WARNING | RateLimiter | Rate limit excedido para ip:192.168.1.100
2026-03-25 10:32:15 | WARNING | Auth | Failed login attempt for user admin
2026-03-25 10:33:00 | INFO | Auth | Token refreshed for user user
```

---

## 🎯 **COMPARATIVA: ANTES VS DESPUÉS**

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Autenticación** | ❌ Ninguna | ✅ JWT |
| **Rate Limiting** | ❌ Ninguno | ✅ 60 req/min |
| **HTTPS** | ❌ HTTP plano | ✅ TLS 1.2/1.3 |
| **Backup** | ❌ Manual | ✅ Automático |
| **Docker** | ❌ No disponible | ✅ Docker Compose |
| **Monitoreo** | ❌ Básico | ✅ Logs + Health |
| **Producción** | ❌ No seguro | ✅ Enterprise-ready |

---

## ⚠️ **ADVERTENCIAS DE SEGURIDAD**

### NUNCA Hacer Esto en Producción

```bash
# ❌ NO usar el JWT_SECRET_KEY por defecto
JWT_SECRET_KEY=tu-secret-key-cambia-en-produccion

# ❌ NO usar contraseñas por defecto
ADMIN_PASSWORD=admin123

# ❌ NO exponer la API sin HTTPS
http://tu-servidor.com:8000

# ❌ NO permitir todos los orígenes CORS
allow_origins=["*"]

# ❌ NO loguear tokens o contraseñas
logger.info(f"Token: {token}")  # ¡MAL!
```

### SIEMPRE Hacer Esto en Producción

```bash
# ✅ USAR valores aleatorios seguros
JWT_SECRET_KEY=$(openssl rand -hex 32)

# ✅ USAR contraseñas fuertes
ADMIN_PASSWORD=$(openssl rand -base64 16)

# ✅ USAR HTTPS siempre
https://rag.tudominio.com

# ✅ Configurar CORS correctamente
allow_origins=["https://tudominio.com"]

# ✅ Rotar tokens regularmente
JWT_ACCESS_TOKEN_MINUTES=30  # 30 minutos
```

---

**Versión:** 1.0.0  
**Última actualización:** 25 de marzo 2026  
**Estado:** ✅ Production-ready
