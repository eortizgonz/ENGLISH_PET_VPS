## 1. Migrar el backend de SQLite a PostgreSQL real

Hoy la aplicación tiene preparación para PostgreSQL, pero el runtime sigue funcionando con SQLite.

Debe quedar así:

**Desarrollo**
 `SQLite` opcional.

**Producción**
 `PostgreSQL obligatorio`.

La aplicación debe leer una variable:

```
DATABASE_URL=postgresql://usuario:password@host:5432/petquest
```

y todos los módulos deben utilizar PostgreSQL:

-  usuarios; 
-  alumnos; 
-  profesores; 
-  colegios; 
-  ejercicios; 
-  resultados; 
-  progreso; 
-  errores; 
-  Writing; 
-  Speaking; 
-  consentimientos; 
-  licencias; 
-  auditoría; 
-  sesiones; 
-  reportes. 

La aplicación debe negarse a arrancar en producción si detecta SQLite.

**Resultado esperado:**

```
database_engine: postgres
```

production\_database\_ok: true

---

# 2. Cambiar el servidor actual por un backend de producción

El servidor Python actual sirve para desarrollo, pero yo no lo usaría como arquitectura comercial definitiva.

Recomiendo:

```
FRONTEND PET QUEST
```

        ↓

     HTTPS

        ↓

    FastAPI

        ↓

 PostgreSQL

        ↓

 Redis / Cache

        ↓

 Object Storage

Y ejecutar FastAPI mediante:

```
Gunicorn/Uvicorn
```

detrás de:

```
Nginx / Caddy / Cloud Load Balancer
```

Esto mejora:

-  concurrencia; 
-  estabilidad; 
-  seguridad; 
-  logging; 
-  escalabilidad; 
-  recuperación ante errores. 

---

# 3. Eliminar las cuentas DEMO automáticas en producción

Actualmente existen cuentas conocidas de prueba.

Eso debe permanecer únicamente en:

```
DEV
```

TEST

STAGING

Nunca en:

```
PRODUCTION
```

Crear una variable:

```
PETQUEST_SEED_DEMO_DATA=false
```

Y además hacer que el backend verifique al iniciar:

> Si existe una cuenta demo conocida en producción → bloquear el arranque.

Eso evita un riesgo de seguridad serio.

---

# 4. Configurar un sistema real de creación de usuarios

Debe existir un flujo completo.

### Alumno

No necesariamente debería registrarse solo.

Para colegios recomiendo:

```
Colegio
```

   ↓

crea profesor

   ↓

profesor crea/invita alumno

   ↓

padre/tutor autoriza

   ↓

cuenta activa

Para venta directa B2C:

```
Padre
```

 ↓

crea cuenta

 ↓

crea perfil hijo

 ↓

acepta consentimiento

 ↓

alumno comienza

---

# 5. Implementar correo electrónico real

Actualmente debe configurarse un proveedor SMTP o API transaccional.

Ejemplos:

-  Amazon SES 
-  SendGrid 
-  Postmark 
-  Mailgun 
-  Resend 

Debe soportar:

-  verificar correo; 
-  recuperar contraseña; 
-  cambiar contraseña; 
-  invitación profesor; 
-  invitación tutor; 
-  consentimiento parental; 
-  alertas de seguridad; 
-  confirmación de eliminación de datos. 

Nunca enviar emails directamente de forma improvisada desde el servidor principal.

---

# 6. Implementar dominio y HTTPS real

Por ejemplo:

```
app.petquest.com
```

o el dominio comercial elegido.

Debe existir:

```
HTTPS
```

TLS 1.2+

HSTS

secure cookies

HttpOnly

SameSite

Y toda petición HTTP debe redireccionarse automáticamente a HTTPS.

---

# 7. Corregir CSP y hardening web

Actualmente hay configuraciones permisivas como:

```
'unsafe-inline'
```

Lo ideal es migrar scripts y estilos inline hacia archivos propios.

Después usar CSP mediante:

```
script-src 'self'
```

style-src 'self'

o nonces/hashes cuando sea estrictamente necesario.

Además implementar:

-  HSTS; 
-  frame protection; 
-  MIME protection; 
-  Referrer-Policy; 
-  Permissions-Policy; 
-  rate limiting; 
-  tamaño máximo de requests; 
-  sanitización de inputs; 
-  protección XSS; 
-  protección SQL injection; 
-  control estricto de CORS. 

---

# 8. Seguridad multi-colegio

Esto es crítico.

La arquitectura debe tener un identificador:

```
tenant_id
```

por colegio.

Ejemplo:

```
Colegio A
```

tenant\_id = 1001

```
Colegio B
```

tenant\_id = 1002

Un profesor del colegio A jamás puede consultar:

```
/student/tenant_1002
```

aunque conozca el ID.

Toda consulta debe validar:

```
user.tenant_id == resource.tenant_id
```

Esto debe aplicarse en el backend, no solamente esconder botones en la pantalla.

---

# 9. Mejorar la gestión de roles

Recomiendo:

| RolAcceso         |                       |
| ----------------- | --------------------- |
| Student           | Solo su aprendizaje   |
| Guardian          | Solo hijos asociados  |
| Teacher           | Alumnos de sus clases |
| School Admin      | Colegio completo      |
| Platform Support  | Soporte limitado      |
| Platform Admin    | Administración global |
| Academic Reviewer | Contenido             |
| Content Author    | Crear contenido       |

No debe existir un único administrador con acceso indiscriminado para todo.

---

# 10. Producir audio Listening profesional

Este es uno de los trabajos más importantes.

Los MP3 actuales deben reemplazarse por grabaciones finales.

Necesitamos:

-  hablantes humanos; 
-  inglés británico; 
-  hombres; 
-  mujeres; 
-  jóvenes; 
-  adultos; 
-  diferentes velocidades naturales; 
-  diálogos; 
-  entrevistas; 
-  anuncios; 
-  monólogos. 

Cada audio debe tener registro:

```
audio_id
```

exercise\_id

speaker

accent

duration

rights

review\_status

production\_ready

Ejemplo:

```
LIST-P3-0001
```

Speaker: British Female

Duration: 01:42

Rights: Cleared

Academic QA: Approved

Production: Yes

---

# 11. Aumentar enormemente el banco de preguntas

La estructura actual es correcta, pero un solo conjunto de 32 Reading + 25 Listening no alcanza.

Para primera versión comercial recomiendo mínimo:

### Reading

**480 preguntas**

equivalentes a:

15 simulacros × 32.

### Listening

**375 preguntas**

15 × 25.

### Writing

100 prompts aproximadamente:

-  40 emails; 
-  30 articles; 
-  30 stories. 

### Speaking

mínimo:

-  50 bancos Part 1; 
-  40 fotografías Part 2; 
-  40 escenarios Part 3; 
-  50 temas Part 4. 

No deben mostrarse siempre en el mismo orden.

---

# 12. Crear un gestor profesional de preguntas

Actualmente el banco debería convertirse en contenido administrable.

Cada pregunta debería contener:

```
item_id
```

skill

part

level

question

options

correct\_answer

explanation

difficulty

topic

grammar

vocabulary

status

author

reviewer

version

Por ejemplo:

```
PET-R6-00142
```

Skill: Reading

Part: 6

Level: B1

Topic: Travel

Answer: although

Difficulty: Medium

Status: Approved

---

# 13. Implementar flujo de aprobación académica

Ninguna pregunta debería publicarse directamente.

Usaría:

```
DRAFT
```

 ↓

ACADEMIC REVIEW 1

 ↓

ACADEMIC REVIEW 2

 ↓

TECHNICAL QA

 ↓

PILOT

 ↓

APPROVED

Solo:

```
APPROVED
```

puede aparecer en exámenes comerciales.

---

# 14. Mejorar Writing con análisis real de errores

Writing ya tiene una buena base.

Pero debe analizar de manera más profunda:

```
Yesterday I go to school.
```

Debe producir:

**Error detectado**

Past Simple.

**Texto escrito**

`go`

**Corrección**

`went`

**Explicación**

Después de "yesterday" normalmente utilizamos pasado.

**Ejercicio de refuerzo**

```
Last Saturday I ___ to the park.
```

Y guardar:

```
student_id
```

grammar\_point=past\_simple

error\_count=4

mastery=42%

---

# 15. Crear el Error Intelligence Engine central

No debe existir solamente para Writing.

Debe funcionar en:

-  Reading; 
-  Writing; 
-  Listening; 
-  Speaking; 
-  Grammar; 
-  Vocabulary. 

Modelo:

```
Respuesta
```

   ↓

Detectar error

   ↓

Clasificar error

   ↓

Determinar causa

   ↓

Explicar

   ↓

Crear microejercicio

   ↓

Reevaluar

   ↓

Actualizar dominio

Ejemplo:

```
Listening
```

Part 2

Error: detail recognition

Topic: dates

Repeated: 5

Mastery: 38%

Entonces la app genera automáticamente ejercicios de fechas.

---

# 16. Speaking necesita guardar audio

Cada ejercicio oral debería guardar:

```
audio_recording
```

transcription

duration

attempt\_number

task

student\_id

Preferiblemente en Object Storage, no dentro de PostgreSQL.

Ejemplo:

```
S3-compatible storage
```

y PostgreSQL guarda solamente la URL segura.

---

# 17. Separar Speaking automático de evaluación humana

Debe quedar claramente:

### AI Feedback

Puede analizar:

-  longitud; 
-  vocabulary; 
-  connectors; 
-  fluency proxy; 
-  grammar; 
-  completion. 

### Teacher/Examiner Feedback

Evalúa:

-  pronunciation; 
-  intelligibility; 
-  discourse management; 
-  interactive communication; 
-  overall performance. 

No mezclar ambos.

---

# 18. Crear Speaking Part 3 con interacción real

Debe existir:

### Modo individual

Alumno + AI Partner.

### Modo colegio

Alumno A + Alumno B.

Pantalla:

```
Sofia               Lucas
```

🎤                   🎤

        TASK

Which activity would be best

for the school trip?

La aplicación graba ambos.

Después:

```
Teacher Review
```

---

# 19. Mejorar el sistema de progreso

No quiero solamente:

```
Reading 82%
```

Quiero:

```
Reading 82%
```

Part 1       94%

Part 2       87%

Part 3       72%

Part 4       80%

Part 5       79%

Part 6       68%

Y debajo:

### Debilidades

-  prepositions; 
-  phrasal verbs; 
-  inference; 
-  past simple. 

### Recomendación

> Practica Reading Part 6 durante tres sesiones.

Esto vuelve útil la información.

---

# 20. Crear un PET Readiness transparente

Mientras no exista calibración externa, mantenerlo como:

> indicador interno.

Yo lo calcularía aproximadamente:

```
Reading      25%
```

Writing      25%

Listening    25%

Speaking     25%

pero dentro de cada skill incluir:

-  dificultad; 
-  consistencia; 
-  últimos resultados; 
-  simulacros; 
-  errores recurrentes; 
-  tiempo. 

No calcularlo simplemente como promedio histórico.

---

# 21. Crear dos tipos de examen

## Practice Mode

Permite:

-  pista; 
-  explicación; 
-  repetir; 
-  escuchar más lentamente; 
-  Milo; 
-  revisar error. 

## Exam Mode

Debe parecerse muchísimo al PET:

-  sin pistas; 
-  sin explicaciones; 
-  tiempo; 
-  máximo 2 Listening; 
-  navegación restringida según experiencia definida; 
-  resultados al terminar. 

Esto es indispensable.

---

# 22. El simulacro debe cronometrar correctamente

Tiempos vigentes:

### Reading

45 minutos.

### Writing

45 minutos.

### Listening

aprox. 30 minutos.

### Speaking

aproximadamente 10–12 minutos por pareja.

La plataforma debe registrar además:

```
started_at
```

finished\_at

time\_spent

timeout

---

# 23. Implementar recuperación de examen

Si Internet se cae:

```
Pregunta 21
```

        ↓

autosave

        ↓

Internet cae

        ↓

usuario vuelve

        ↓

Resume exam

        ↓

Pregunta 21

Nunca perder todo un examen.

---

# 24. PWA y offline

Como aplicación educativa esto puede ser una ventaja enorme.

Dejar disponible offline:

-  lecciones descargadas; 
-  Reading; 
-  Grammar; 
-  Vocabulary; 
-  ejercicios básicos. 

Sin conexión podrían almacenarse respuestas temporalmente en:

```
IndexedDB
```

y sincronizar después.

---

# 25. Implementar backups reales

No solamente copiar la base.

Recomiendo:

```
Daily incremental
```

Weekly full

Monthly archive

y almacenamiento fuera del servidor.

Además realizar prueba real:

```
Backup
```

 ↓

Nueva DB vacía

 ↓

Restore

 ↓

Comparar datos

 ↓

PASS

---

# 26. Observabilidad

La app debe indicar automáticamente cuando algo falla.

Implementar:

### Logs

-  login; 
-  API errors; 
-  database; 
-  audio upload; 
-  email; 
-  consent; 
-  failed authorization. 

### Métricas

-  request latency; 
-  error rate; 
-  active users; 
-  DB connections; 
-  CPU; 
-  memory. 

### Alertas

Por ejemplo:

> Error rate >5%

enviar alerta al equipo.

---

# 27. QA automatizado único

Eliminar o archivar tests antiguos V12, V17, V40 etc. que ya no representan el sistema actual.

Crear una sola suite:

```
PETQUEST_RELEASE_GATE
```

Que ejecute:

```
Frontend
```

Backend

Database

Authentication

Roles

Privacy

Academic structure

Exam timings

Listening

Writing

Speaking

PWA

Security

Email

Backup

Performance

Resultado final:

```
213 tests
```

213 PASS

0 FAIL

0 BLOCKED

Entonces:

```
RELEASE_ALLOWED=true
```

---

# 28. Crear ambientes separados

Necesitamos:

```
DEV
```

Para programadores.

```
STAGING
```

Replica producción.

```
PRODUCTION
```

Clientes reales.

Jamás probar código directamente con alumnos reales.

Flujo:

```
DEV
```

 ↓

automated tests

 ↓

STAGING

 ↓

QA

 ↓

approval

 ↓

PRODUCTION

---

# 29. Realizar pruebas con niños

Para mí esto es obligatorio.

Primera ronda:

**10 niños.**

Después:

**30 niños.**

Comprobar:

-  entienden la navegación; 
-  encuentran los botones; 
-  comprenden a Milo; 
-  entienden feedback; 
-  pueden usar Listening; 
-  microphone funciona; 
-  no se frustran; 
-  quieren continuar. 

Registrar cada problema.

---

# 30. Realizar piloto académico

Después:

**100+ alumnos.**

Comparar:

```
PET Quest performance
```

vs.

external standardized/mock performance

Y posteriormente alumnos que realmente hagan Cambridge cuando sea posible.

Eso permitirá calibrar:

```
Readiness
```

---

# 31. Probar dispositivos reales

Crear una matriz:

| SistemaNavegadorEstado |        |      |
| ---------------------- | ------ | ---- |
| Windows 11             | Chrome | PASS |
| Windows 11             | Edge   | PASS |
| macOS                  | Safari | PASS |
| macOS                  | Chrome | PASS |
| iPad                   | Safari | PASS |
| iPhone                 | Safari | PASS |
| Android                | Chrome | PASS |

Especialmente probar:

-  microphone; 
-  recording; 
-  playback; 
-  permissions; 
-  touch; 
-  keyboard; 
-  orientation. 

---

# 32. Pentest externo

Antes de almacenar información de niños:

realizar auditoría de seguridad independiente.

Especialmente:

-  IDOR; 
-  XSS; 
-  SQL injection; 
-  privilege escalation; 
-  session hijacking; 
-  broken authentication; 
-  tenant isolation; 
-  password reset; 
-  API enumeration; 
-  file upload vulnerabilities. 

Cualquier vulnerabilidad alta/crítica:

```
RELEASE BLOCKED
```

---

# 33. Legal y privacidad

Antes de vender:

Crear y revisar legalmente:

-  Privacy Policy; 
-  Terms of Service; 
-  Child Privacy; 
-  Guardian Consent; 
-  Cookie Policy; 
-  Data Processing Agreement; 
-  School Agreement; 
-  Retention Policy; 
-  Data Deletion Process; 
-  AI disclosure; 
-  voice recording consent. 

Especialmente importante porque existen menores y grabaciones.

---

# 34. Flujo final que debe tener PET Quest

Cuando todo esté terminado, debería funcionar aproximadamente así:

```
PADRE / COLEGIO
```

      ↓

REGISTRO

      ↓

CONSENTIMIENTO

      ↓

CREAR ALUMNO

      ↓

DIAGNÓSTICO

      ↓

NIVEL ACTUAL

      ↓

PLAN PERSONALIZADO

      ↓

LECCIÓN

      ↓

PRÁCTICA

      ↓

ERROR

      ↓

EXPLICACIÓN

      ↓

REFUERZO

      ↓

DOMINIO

      ↓

MOCK EXAM

      ↓

ANÁLISIS

      ↓

NUEVO PLAN

      ↓

FINAL MOCK

Ese ciclo debe ser el **corazón del producto**.

---

# Orden exacto de trabajo

Yo lo ejecutaría en este orden:

| OrdenTrabajoPrioridad |                          |       |
| --------------------- | ------------------------ | ----- |
| 1                     | PostgreSQL real          | 🔴 P0 |
| 2                     | Backend production-grade | 🔴 P0 |
| 3                     | Desactivar demos         | 🔴 P0 |
| 4                     | Roles + multi-tenant     | 🔴 P0 |
| 5                     | SMTP                     | 🔴 P0 |
| 6                     | HTTPS + seguridad        | 🔴 P0 |
| 7                     | Audio humano             | 🔴 P0 |
| 8                     | Banco de preguntas       | 🔴 P0 |
| 9                     | QA académico             | 🔴 P0 |
| 10                    | Error Intelligence       | 🟠 P1 |
| 11                    | Speaking completo        | 🟠 P1 |
| 12                    | Backup/restore           | 🔴 P0 |
| 13                    | QA único                 | 🔴 P0 |
| 14                    | Device testing           | 🔴 P0 |
| 15                    | Pentest                  | 🔴 P0 |
| 16                    | Legal menores            | 🔴 P0 |
| 17                    | Piloto 30 niños          | 🔴 P0 |
| 18                    | Correcciones UX          | 🔴 P0 |
| 19                    | Piloto 100+              | 🟠 P1 |
| 20                    | Calibración              | 🟠 P1 |
| 21                    | Commercial Release 1.0   | 🟢    |

## Cuándo considero que está realmente operativa

Yo exigiría que el release gate muestre:

```
ACADEMIC               PASS
```

DATABASE               PASS

SECURITY               PASS

MULTI-TENANT           PASS

PRIVACY                PASS

EMAIL                  PASS

AUDIO                   PASS

BACKUP/RESTORE          PASS

DEVICE MATRIX           PASS

LOAD TEST               PASS

PENTEST                 PASS

PILOT                   PASS

CRITICAL ISSUES           0

HIGH ISSUES               0

Entonces sí cambiaría:

# `COMMERCIAL_RELEASE = BLOCKED`

por:

# `COMMERCIAL_RELEASE = APPROVED`

La prioridad inmediata es **hacerla operativa y estable, no seguir agregándole funciones**. V42 ya tiene suficiente producto; ahora necesita convertirse de una aplicación funcional en un **SaaS educativo de producción**.