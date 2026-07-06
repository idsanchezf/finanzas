# Guía de Despliegue — Finance Report

> **Última actualización**: 2026-06-17
> **Versión**: 1.0

---

## 1. Arquitectura de despliegue

```
┌─────────────────────────────────────────────────────────────┐
│                        Vercel (Hobby)                        │
│                  ┌───────────────────────┐                   │
│                  │   Next.js Frontend     │                   │
│                  │   Port: 3000 (ext:443)│                   │
│                  └───────────────────────┘                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS (REST + SSE)
┌─────────────────────────▼───────────────────────────────────┐
│              Oracle Cloud VM Ampere A1 (Always Free)         │
│              4 OCPU ARM · 24GB RAM · 200GB disco              │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Kubernetes (Oracle OKE)                    │ │
│  │                                                         │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │ │
│  │  │  API Gateway  │  │ Extract       │  │Classify     │ │ │
│  │  │  FastAPI:8000 │  │ Processor     │  │Worker       │ │ │
│  │  │  2-6 replicas │  │ 1-5 replicas  │  │1-3 replicas │ │ │
│  │  └───────────────┘  └───────────────┘  └─────────────┘ │ │
│  │                                                         │ │
│  │  ┌───────────────┐  ┌───────────────┐                   │ │
│  │  │ Notification  │  │   RabbitMQ    │                   │ │
│  │  │ Worker        │  │   :5672:15672 │                   │ │
│  │  │ 1 replica     │  │   1 replica   │                   │ │
│  │  └───────────────┘  └───────────────┘                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌──────────────────┐
│  Supabase     │  │   Upstash     │  │  Cloudflare R2   │
│  PostgreSQL 16│  │   Redis 7     │  │  Object Storage  │
│  500MB free   │  │   256MB free  │  │  10GB free       │
└───────────────┘  └───────────────┘  └──────────────────┘
```

---

## 2. Prerrequisitos

### 2.1 Cuentas de servicio requeridas

| Servicio | Cuenta | Free Tier | Propósito |
|----------|--------|-----------|-----------|
| **Oracle Cloud** | [signup.cloud.oracle.com](https://signup.cloud.oracle.com/) | Always Free: 4 OCPU ARM, 24GB RAM | Hosting del backend, workers, RabbitMQ |
| **Vercel** | [vercel.com](https://vercel.com/signup) | Hobby: 100GB bandwidth | Hosting frontend Next.js |
| **Supabase** | [supabase.com](https://supabase.com/dashboard/sign-in) | 500MB PostgreSQL | Base de datos |
| **Upstash** | [upstash.com](https://console.upstash.com/) | 256MB Redis | Cache |
| **Cloudflare R2** | [dash.cloudflare.com](https://dash.cloudflare.com/) | 10GB free | Object storage (extractos, reportes) |
| **Google AI** | [aistudio.google.com](https://aistudio.google.com/apikey) | 1,500 req/día gratis | API Gemini para IA |
| **Grafana Cloud** | [grafana.com](https://grafana.com/auth/sign-up/) | 10K métricas, 50GB logs | Observabilidad |

### 2.2 Herramientas locales

```bash
# CLI requeridas (instalar en máquina del operador)
docker --version          # >= 24.x
kubectl version --client  # >= 1.29
helm version              # >= 3.x
oci --version             # Oracle Cloud CLI
vercel --version          # Vercel CLI
gh --version              # GitHub CLI
```

### 2.3 Secrets de GitHub requeridos

| Secret | Descripción | Obtención |
|--------|-------------|-----------|
| `GITHUB_TOKEN` | Automático en Actions | N/A |
| `VERCEL_TOKEN` | Token de acceso Vercel | [Vercel Account Tokens](https://vercel.com/account/tokens) |
| `VERCEL_ORG_ID` | ID de organización Vercel | `.vercel/project.json` → `orgId` |
| `VERCEL_PROJECT_ID` | ID de proyecto Vercel | `.vercel/project.json` → `projectId` |
| `KUBE_CONFIG` | kubeconfig de OKE en base64 | `cat kubeconfig.yaml \| base64 -w0` |

Configurar en: **GitHub → Settings → Secrets and variables → Actions → New repository secret**

---

## 3. Configuración de infraestructura

### 3.1 Oracle Cloud VM + OKE

```bash
# 1. Crear VM Ampere A1
# Compute → Instances → Create instance
#   Name: finance-report-vm
#   Image: Ubuntu 22.04 LTS (ARM)
#   Shape: VM.Standard.A1.Flex (4 OCPU, 24GB RAM)
#   Boot volume: 200GB
#   SSH key: tu llave pública

# 2. Conectarse a la VM
ssh ubuntu@<VM_PUBLIC_IP>

# 3. Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# 4. Crear cluster OKE (Oracle Container Engine for Kubernetes)
oci ce cluster create \
  --name finance-report-cluster \
  --compartment-id <ocid_compartment> \
  --vcn-id <ocid_vcn> \
  --kubernetes-version v1.29 \
  --service-lb-subnet-ids '["<ocid_subnet>"]' \
  --endpoint-subnet-id <ocid_subnet> \
  --endpoint public

# 5. Obtener kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id <ocid_cluster> \
  --file kubeconfig.yaml \
  --region us-ashburn-1

# 6. Verificar conexión
export KUBECONFIG=kubeconfig.yaml
kubectl cluster-info
kubectl get nodes
```

### 3.2 Vercel (Frontend)

```bash
cd src/frontend

# Vincular proyecto
vercel link   # → crea .vercel/project.json

# Configurar variables de entorno en Vercel
vercel env add NEXT_PUBLIC_API_URL production
# Valor: https://api.financereport.app/api/v1
```

### 3.3 Supabase (PostgreSQL)

```bash
# 1. Crear proyecto en https://supabase.com/dashboard
# 2. Obtener connection string:
#    Settings → Database → Connection string → URI
#    Formato: postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres

# 3. Ejecutar migraciones
cd src/backend
alembic upgrade head
```

### 3.4 Upstash (Redis)

```bash
# 1. Crear base de datos Redis en https://console.upstash.com/
# 2. Obtener URL de conexión:
#    Formato: redis://default:<password>@<endpoint>.upstash.io:6379/0
```

---

## 4. Despliegue en Kubernetes (Oracle OKE)

### 4.1 Configurar secrets y configmaps

```bash
# IMPORTANTE: NUNCA subir valores reales al repositorio.
# Crear el secret con valores reales en el cluster:

kubectl create namespace finance-report

kubectl create secret generic finance-secrets \
  --namespace finance-report \
  --from-literal=DATABASE_URL='postgresql+asyncpg://postgres:<PASSWORD>@db.<REF>.supabase.co:5432/postgres' \
  --from-literal=DATABASE_URL_SYNC='postgresql://postgres:<PASSWORD>@db.<REF>.supabase.co:5432/postgres' \
  --from-literal=REDIS_URL='redis://default:<PASSWORD>@<ENDPOINT>.upstash.io:6379/0' \
  --from-literal=RABBITMQ_URL='amqp://guest:guest@rabbitmq:5672/' \
  --from-literal=GEMINI_API_KEY='<GEMINI_API_KEY>' \
  --from-literal=GROQ_API_KEY='<GROQ_API_KEY>' \
  --from-literal=R2_ACCESS_KEY='<R2_ACCESS_KEY>' \
  --from-literal=R2_SECRET_KEY='<R2_SECRET_KEY>' \
  --from-literal=GOOGLE_CLIENT_ID='<GOOGLE_CLIENT_ID>' \
  --from-literal=GOOGLE_CLIENT_SECRET='<GOOGLE_CLIENT_SECRET>' \
  --from-literal=JWT_SECRET='<GENERATE_RANDOM_256_BIT_SECRET>' \
  --from-literal=VAPID_PRIVATE_KEY='<VAPID_PRIVATE_KEY>' \
  --from-literal=RESEND_API_KEY='<RESEND_API_KEY>'

# Aplicar configmap (ya tiene valores no sensibles)
kubectl apply -f k8s/configmap.yaml
```

### 4.2 Aplicar manifiestos K8s

```bash
# Orden de despliegue:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/network-policy.yaml
kubectl apply -f k8s/pdb.yaml

# Infraestructura
kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml   # Solo si no usas Upstash

# Aplicación
kubectl apply -f k8s/deployment-backend.yaml
kubectl apply -f k8s/service-backend.yaml
kubectl apply -f k8s/frontend-service.yaml   # Si frontend corre en K8s
kubectl apply -f k8s/deployment-workers.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml

# Verificar despliegue
kubectl get all -n finance-report
kubectl get pods -n finance-report -w
```

### 4.3 Verificar el despliegue

```bash
# Ver logs de un pod específico
kubectl logs -f deployment/finance-backend -n finance-report

# Verificar health checks
kubectl port-forward svc/finance-backend-svc 8000:80 -n finance-report &
# En otra terminal:
curl http://localhost:8000/health
curl http://localhost:8000/health/ready

# Verificar ingress
kubectl get ingress -n finance-report
```

---

## 5. Despliegue del Frontend (Vercel)

### 5.1 Despliegue automático (GitHub Actions)

El frontend se despliega automáticamente al pushear a `main` gracias al workflow `cd.yml`. No se requiere acción manual.

### 5.2 Despliegue manual

```bash
cd src/frontend

# Desplegar a producción
vercel --prod

# Desplegar preview (feature branches)
vercel
```

---

## 6. Configuración de dominios y TLS

### 6.1 Dominio

```bash
# 1. Registrar dominio (ej. financereport.app)
# 2. Configurar DNS:
#    - api.financereport.app → IP pública de Oracle Cloud Load Balancer
#    - financereport.app → Vercel (CNAME: cname.vercel-dns.com)
```

### 6.2 Certificados TLS

**Backend (Oracle OKE):**

El ingress está configurado para usar `cert-manager` con Let's Encrypt:

```bash
# Instalar cert-manager en el cluster
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Crear ClusterIssuer para Let's Encrypt
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@financereport.app
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF

# Aplicar el ingress (cert-manager gestiona el certificado automáticamente)
kubectl apply -f k8s/ingress.yaml
```

**Frontend (Vercel):** TLS gestionado automáticamente por Vercel.

---

## 7. Rollback

### 7.1 Rollback de Backend

```bash
# Opción A: Rollback de deployment (última versión funcional)
kubectl rollout undo deployment/finance-backend -n finance-report

# Opción B: Rollback a revisión específica
kubectl rollout history deployment/finance-backend -n finance-report
kubectl rollout undo deployment/finance-backend -n finance-report --to-revision=3

# Verificar rollback
kubectl rollout status deployment/finance-backend -n finance-report
```

### 7.2 Rollback de Frontend (Vercel)

```bash
# Desde Vercel Dashboard: Deployments → seleccionar deployment → "Promote to Production"
# O desde CLI:
vercel rollback
```

---

## 8. Smoke Tests Post-Deploy

Ejecutar después de cada despliegue para verificar que los endpoints críticos funcionan:

```bash
# Linux/macOS
bash scripts/smoke-test.sh

# Windows PowerShell
pwsh scripts/smoke-test.ps1
```

Los smoke tests verifican:
- `GET /health` → 200 OK
- `GET /health/ready` → 200 OK
- `GET /docs` → 200 OK (Swagger UI accesible)
- `POST /api/v1/auth/login` → Responde (aunque falle sin credenciales válidas es esperado)
- `GET /api/v1/dashboard/summary` → 401 (requiere auth) — la API responde

---

## 9. Monitoreo y Observabilidad

### 9.1 Grafana Cloud

1. Crear cuenta en [grafana.com](https://grafana.com/auth/sign-up/)
2. Configurar el OpenTelemetry Collector (ya embebido en la app)
3. Importar dashboards desde `grafana/dashboards/`

```bash
# Verificar que métricas y traces fluyen:
# Las métricas de Prometheus están en /metrics si se configura
curl https://api.financereport.app/metrics
```

### 9.2 Logs

```bash
# Ver logs en tiempo real de todos los pods
kubectl logs -l app=finance-report -n finance-report --tail=100 -f

# Ver logs de un servicio específico
kubectl logs -f deployment/finance-backend -n finance-report
```

### 9.3 Alertas configuradas (Grafana Cloud)

| Alerta | Condición | Severidad |
|--------|-----------|-----------|
| High Error Rate | Errores 5xx > 5% en 5min | Critical |
| High Latency | p99 > 2s en 5min | Warning |
| Dead Letter Queue | Mensajes en DLQ > 10 | Critical |
| Pod Restarts | Restarts > 3 en 15min | Warning |
| High CPU | CPU > 80% sostenido | Warning |
| Database Down | Readiness probe falla | Critical |

---

## 10. Variables de entorno (producción)

Las siguientes variables deben configurarse en el entorno de producción:

### 10.1 Backend (K8s Secret + ConfigMap)

| Variable | Fuente | Descripción |
|----------|--------|-------------|
| `DATABASE_URL` | Secret | Conexión async a Supabase PostgreSQL |
| `DATABASE_URL_SYNC` | Secret | Conexión sync (migraciones) |
| `REDIS_URL` | Secret | Conexión a Upstash Redis |
| `RABBITMQ_URL` | Secret | Conexión a RabbitMQ interno |
| `GEMINI_API_KEY` | Secret | API key de Google Gemini |
| `R2_ACCESS_KEY` | Secret | Cloudflare R2 access key |
| `R2_SECRET_KEY` | Secret | Cloudflare R2 secret key |
| `GOOGLE_CLIENT_ID` | Secret | Google OAuth2 client ID |
| `GOOGLE_CLIENT_SECRET` | Secret | Google OAuth2 client secret |
| `JWT_SECRET` | Secret | Clave de firma JWT (mín 256 bits) |
| `VAPID_PRIVATE_KEY` | Secret | Web Push VAPID private key |
| `RESEND_API_KEY` | Secret | API key de Resend (email) |
| `CORS_ORIGINS` | ConfigMap | Orígenes CORS permitidos |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | ConfigMap | Endpoint Grafana Cloud OTLP |

### 10.2 Frontend (Vercel Environment Variables)

| Variable | Descripción |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL base de la API backend |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth2 client ID (público) |
| `NEXT_PUBLIC_VAPID_PUBLIC_KEY` | Web Push VAPID public key |

---

## 11. Consideraciones de seguridad

### 11.1 Gestión de secrets

- **NUNCA** commitear valores reales en `k8s/secrets.yaml`
- Usar `kubectl create secret` con `--from-literal` para producción
- Rotar `JWT_SECRET` cada 90 días
- Rotar API keys (`GEMINI_API_KEY`, `RESEND_API_KEY`) cada 180 días

### 11.2 Network Policies

Las Network Policies (`k8s/network-policy.yaml`) restringen el tráfico:
- Solo el ingress puede alcanzar el backend desde fuera
- Workers solo aceptan conexiones de RabbitMQ
- PostgreSQL y Redis solo aceptan conexiones desde los pods de la app

### 11.3 Escaneo de imágenes

Las imágenes Docker se escanean en CI (ver `ci.yml`). En producción se recomienda añadir:

```yaml
# En ci.yml, job build-docker, agregar después del build:
- name: Scan backend image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### 11.4 Secretos de Supabase

Supabase expone la API anónima por defecto. Para producción, se recomienda:
1. Deshabilitar la API REST de Supabase (Settings → API → Exposed schemas)
2. Usar solo la conexión directa PostgreSQL desde el backend
3. Configurar IP allowlist en Supabase para la IP del cluster OKE

---

## 12. Troubleshooting

### 12.1 Pods en CrashLoopBackOff

```bash
kubectl describe pod <pod-name> -n finance-report
kubectl logs <pod-name> -n finance-report --previous
```

### 12.2 Problemas de conexión a BD

```bash
# Verificar conectividad desde dentro del pod
kubectl exec -it deployment/finance-backend -n finance-report -- \
  python -c "import asyncpg; print('OK')"

# Verificar el secret
kubectl get secret finance-secrets -n finance-report -o yaml | grep DATABASE_URL
```

### 12.3 RabbitMQ inaccesible

```bash
# Verificar estado de RabbitMQ
kubectl get pods -n finance-report -l app=rabbitmq
kubectl logs deployment/rabbitmq -n finance-report

# Acceder a la UI de gestión
kubectl port-forward svc/rabbitmq 15672:15672 -n finance-report
# Abrir http://localhost:15672 (guest/guest)
```

### 12.4 Ingress no responde

```bash
kubectl get ingress -n finance-report
kubectl describe ingress finance-ingress -n finance-report
kubectl get svc -n ingress-nginx
```

---

## 13. Referencias

- [Oracle OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- [Vercel Documentation](https://vercel.com/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Architecture Decision Records](./architecture.md)
