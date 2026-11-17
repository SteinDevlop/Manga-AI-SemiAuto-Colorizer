# Arquitectura de software --- Manga Colorizer

## Documento arc42

  -----------------------------------------------------------------------
  Campo                               Valor
  ----------------------------------- -----------------------------------
  Estado                              Borrador para revisión
                                      arquitectónica

  Versión                             0.1.0

  Fecha                               15 de noviembre de 2026

  Idioma                              Español

  Estilo arquitectónico               Monolito modular + workers
                                      asíncronos + motor de IA
                                      desacoplado

  Despliegue objetivo                 Aplicación web ejecutada localmente

  Audiencia                           Desarrollo, ML/IA, UX y validación
                                      técnica
  -----------------------------------------------------------------------

> **Propósito:** definir una arquitectura inicial verificable para una
> aplicación local que recibe páginas de manga en blanco y negro,
> analiza viñetas y personajes, solicita al usuario una configuración
> cromática por personaje y genera una versión coloreada conservando el
> line art, la composición y la consistencia visual.
>
> **Alcance de este documento:** arquitectura de software y sus
> decisiones. No afirma que la calidad final esté garantizada ni
> prescribe un único modelo de IA. Los modelos concretos deben
> seleccionarse mediante pruebas reproducibles.

------------------------------------------------------------------------

# 1. Introducción y objetivos

## 1.1 Resumen

Manga Colorizer es una aplicación web local de colorización generativa
de manga. El usuario importa una imagen o página, el sistema detecta
viñetas, localiza y agrupa apariciones de personajes, propone atributos
visuales y presenta un editor para que el usuario confirme o corrija
colores de piel, cabello, ojos, vestimenta y accesorios. Solo después de
la aprobación se ejecuta la colorización.

La solución debe permitir sustituir modelos de detección, segmentación y
generación sin reescribir la lógica principal del producto. También debe
conservar los resultados, parámetros, versiones de modelos y
configuraciones para poder reproducir y comparar ejecuciones.

## 1.2 Objetivos de negocio y producto

  -----------------------------------------------------------------------
  ID                                  Objetivo
  ----------------------------------- -----------------------------------
  OBJ-01                              Permitir colorizar una página de
                                      manga desde una interfaz web local.

  OBJ-02                              Detectar personajes y sus
                                      apariciones antes de generar
                                      colores.

  OBJ-03                              Permitir que el usuario confirme y
                                      edite una paleta por personaje.

  OBJ-04                              Mantener la identidad cromática de
                                      un personaje entre viñetas y
                                      páginas.

  OBJ-05                              Preservar tanto como sea posible el
                                      line art, las expresiones y la
                                      composición original.

  OBJ-06                              Permitir cambiar o comparar modelos
                                      de IA mediante adaptadores.

  OBJ-07                              Mantener imágenes, proyectos y
                                      modelos en almacenamiento local,
                                      sin depender de servicios cloud en
                                      ejecución normal.

  OBJ-08                              Registrar resultados y parámetros
                                      para evaluación experimental.
  -----------------------------------------------------------------------

## 1.3 Objetivos de calidad

  -----------------------------------------------------------------------
  Prioridad               Atributo                Escenario de calidad
  ----------------------- ----------------------- -----------------------
  Muy alta                Fidelidad visual        La salida conserva
                                                  trazos, composición,
                                                  expresiones y geometría
                                                  de la entrada.

  Muy alta                Control del usuario     Ninguna colorización
                                                  comienza sin aprobación
                                                  de las configuraciones
                                                  requeridas.

  Muy alta                Consistencia            Las apariciones
                                                  asociadas a una misma
                                                  identidad reutilizan
                                                  sus atributos
                                                  cromáticos
                                                  persistentes.

  Alta                    Modificabilidad         Se puede sustituir un
                                                  modelo de IA
                                                  implementando su
                                                  adaptador, sin cambiar
                                                  los casos de uso.

  Alta                    Reproducibilidad        Cada ejecución registra
                                                  versión de modelo,
                                                  configuración,
                                                  referencias y
                                                  parámetros.

  Alta                    Privacidad local        Los archivos no salen
                                                  del equipo en el modo
                                                  local predeterminado.

  Media-alta              Usabilidad              El usuario puede
                                                  corregir identidades,
                                                  paletas y máscaras
                                                  propuestas por la IA.

  Media                   Rendimiento             Las tareas largas no
                                                  bloquean las peticiones
                                                  HTTP ni la interfaz.

  Media                   Recuperación            Los trabajos fallidos
                                                  pueden inspeccionarse
                                                  y, cuando sea seguro,
                                                  reintentarse.
  -----------------------------------------------------------------------

## 1.4 No objetivos de la primera versión

-   Entrenar un modelo fundacional desde cero.
-   Garantizar la reconstrucción exacta de colores oficiales
    desconocidos a partir de una imagen monocromática.
-   Resolver automáticamente todos los casos de oclusión, diseños
    cambiantes o personajes visualmente similares.
-   Ofrecer colaboración multiusuario o despliegue distribuido.
-   Implementar un editor profesional de ilustración raster/vectorial.
-   Hacer scraping de manga o incorporar material protegido sin
    licencia.
-   Ejecutar múltiples modelos generativos grandes simultáneamente en
    una única GPU.

## 1.5 Usuarios y actores

  -----------------------------------------------------------------------
  Actor                               Necesidad
  ----------------------------------- -----------------------------------
  Usuario final                       Importar manga, revisar personajes,
                                      elegir colores y obtener imágenes
                                      coloreadas.

  Desarrollador                       Mantener API, módulos,
                                      almacenamiento y despliegue.

  Ingeniero ML                        Entrenar, evaluar, versionar y
                                      sustituir modelos.

  Evaluador                           Comparar salidas mediante métricas
                                      y revisión humana.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 2. Restricciones arquitectónicas

## 2.1 Restricciones técnicas

1.  La aplicación debe poder ejecutarse en un equipo local.
2.  La inferencia debe poder utilizar GPU NVIDIA/CUDA cuando esté
    disponible; la arquitectura no debe asumir que siempre existe.
3.  La API no debe ejecutar inferencia pesada dentro del ciclo de una
    petición HTTP.
4.  Los modelos y pesos se descargan o instalan previamente; el uso
    normal debe poder funcionar sin conexión.
5.  El primer despliegue está orientado a un solo usuario y una sola
    máquina.
6.  Las tareas GPU deben limitarse para evitar cargas concurrentes que
    excedan la VRAM.
7.  Los archivos originales y generados se almacenan en disco local;
    PostgreSQL conserva metadatos y relaciones.
8.  Redis se utiliza como broker/infraestructura de cola, no como
    almacenamiento permanente de resultados.
9.  Los datos de entrenamiento deben contar con permisos y licencias
    compatibles con su uso.

## 2.2 Restricciones de diseño

-   Arquitectura de monolito modular para la lógica de negocio.
-   Separación de procesos para API, worker CPU y worker GPU.
-   Contratos explícitos entre casos de uso y motor de IA.
-   Persistencia relacional para proyectos, páginas, personajes, paletas
    y trabajos.
-   Almacenamiento de archivos separado de la base de datos.
-   La aprobación humana es una transición de estado explícita y
    auditable.
-   Los modelos de IA se integran mediante interfaces/adaptadores.

## 2.3 Supuestos por validar

  --------------------------------------------------------------------------
  ID                      Supuesto                   Validación necesaria
  ----------------------- -------------------------- -----------------------
  AS-01                   El equipo objetivo dispone Benchmark de modelos
                          de recursos suficientes    con resolución y VRAM
                          para inferencia local.     objetivo.

  AS-02                   Se pueden obtener datos de Auditoría de licencias
                          entrenamiento/evaluación   y procedencia.
                          con licencia adecuada.     

  AS-03                   Los modelos existentes     Evaluación comparativa
                          pueden producir un         con un conjunto fijo.
                          baseline útil.             

  AS-04                   La detección y agrupación  Medir precisión de
                          de personajes es           detección y matching;
                          suficientemente útil con   incorporar corrección
                          modelos preentrenados.     manual.

  AS-05                   Las máscaras pueden        Experimentos de
                          condicionar la generación  conditioning y
                          sin degradar el resultado. evaluación visual.
  --------------------------------------------------------------------------

------------------------------------------------------------------------

# 3. Contexto y alcance

## 3.1 Contexto del sistema

Manga Colorizer es una aplicación local con una interfaz web y procesos
backend que coordinan análisis y generación. El usuario proporciona la
imagen y las decisiones cromáticas; los modelos proponen detecciones y
producen resultados.

``` mermaid
flowchart LR
    U[Usuario] -->|Carga página / edita paleta| UI[Frontend web]
    UI <-->|REST / WebSocket| API[Backend API]
    API --> DB[(PostgreSQL)]
    API --> FS[(Almacenamiento local)]
    API --> Q[(Redis / cola)]
    Q --> CPU[Worker CPU]
    Q --> GPU[Worker GPU]
    CPU --> FS
    GPU --> FS
    CPU --> DB
    GPU --> DB
    GPU -->|Adaptadores| AI[Modelos de IA locales]
    ML[Ingeniero ML] -->|Modelos, pesos y evaluación| AI
```

## 3.2 Interfaces externas

  -----------------------------------------------------------------------
  Interfaz          Dirección         Propósito         Tecnología
  ----------------- ----------------- ----------------- -----------------
  UI ↔ API          Bidireccional     Operaciones de    HTTP REST
                                      proyecto, carga,  
                                      revisión y        
                                      generación        

  UI ↔ API          API → UI          Progreso y        WebSocket;
                                      notificaciones de polling como
                                      trabajos          fallback

  API → PostgreSQL  Bidireccional     Metadatos y       SQLAlchemy / SQL
                                      estados           

  API → Redis       API → cola        Encolar tareas    Celery

  Worker →          Bidireccional     Leer entradas y   Sistema de
  almacenamiento                      escribir          archivos
                                      artefactos        

  Worker → modelos  Worker → IA       Inferencia        PyTorch /
                                                        adaptadores

  Herramientas ML → Bidireccional     Versionado y      Archivos y
  artefactos                          evaluación        manifiestos
                                                        locales
  -----------------------------------------------------------------------

## 3.3 Alcance funcional

Incluido: - Gestión local de proyectos. - Carga y validación de
imágenes. - Análisis de página y detección de paneles. - Detección y
agrupación de personajes. - Revisión manual de identidades. -
Configuración de atributos y paletas. - Gestión de máscaras y
correcciones. - Aprobación explícita antes de colorizar. - Generación,
seguimiento, cancelación y descarga. - Historial de ejecuciones y
configuración reproducible.

Fuera del alcance inicial: - Cuentas remotas, multi-tenancy y
sincronización cloud. - Edición avanzada de cada píxel. - Generación de
capítulos completos con memoria narrativa automática. - Entrenamiento
distribuido.

------------------------------------------------------------------------

# 4. Estrategia de solución

## 4.1 Estrategia general

La solución usa un **monolito modular** para la lógica de negocio y tres
procesos de ejecución:

1.  **API:** valida solicitudes, ejecuta casos de uso, persiste estados
    y publica trabajos.
2.  **Worker CPU:** realiza operaciones que no requieren GPU, como
    normalización, detección de paneles y tareas auxiliares.
3.  **Worker GPU:** mantiene los modelos cargados y ejecuta
    segmentación/inferencia que requiere GPU, con concurrencia
    controlada.

El motor de IA se organiza como una biblioteca desacoplada. No se
convierte inicialmente en un microservicio de red: el worker GPU lo
invoca mediante interfaces Python. Si en el futuro se requieren varias
máquinas, se podrá extraer detrás de una API interna sin cambiar los
casos de uso.

## 4.2 Principios arquitectónicos

-   **Human-in-the-loop:** la IA propone; el usuario confirma las
    decisiones cromáticas.
-   **Separación de responsabilidades:** API y workers no contienen
    lógica específica de un modelo.
-   **Ports and adapters:** cada modelo implementa un contrato estable.
-   **Idempotencia:** reintentar una tarea no debe duplicar artefactos
    ni corromper el estado.
-   **Trazabilidad:** cada salida está vinculada a su entrada, paleta,
    versión de modelo y parámetros.
-   **Persistencia de artefactos:** guardar originales, máscaras,
    previews y resultados con referencias estables.
-   **Corrección antes de automatización:** permitir editar identidades,
    atributos y máscaras.
-   **Privacidad por defecto:** no transmitir archivos a servicios
    externos.

## 4.3 Flujo principal

``` mermaid
flowchart TD
    A[Usuario carga página] --> B[Validar archivo y crear Page]
    B --> C[Encolar análisis]
    C --> D[Detectar paneles y personajes]
    D --> E[Extraer apariciones y máscaras]
    E --> F[Agrupar identidades]
    F --> G[Guardar análisis y propuestas]
    G --> H[Usuario revisa personajes]
    H --> I{¿Identidades correctas?}
    I -- No --> J[Editar / fusionar / separar]
    J --> H
    I -- Sí --> K[Editar paletas y atributos]
    K --> L[Revisar máscaras si es necesario]
    L --> M{¿Configuración aprobada?}
    M -- No --> K
    M -- Sí --> N[Crear ColorizationJob]
    N --> O[Generar imagen condicionada]
    O --> P[Refinamiento y reconstrucción]
    P --> Q[Guardar resultado y métricas]
    Q --> R[Mostrar / descargar]
```

------------------------------------------------------------------------

# 5. Vista de bloques de construcción

## 5.1 Nivel 1: contenedores lógicos

``` mermaid
flowchart TB
    subgraph Client["Cliente local"]
      FE[Frontend React + TypeScript]
    end

    subgraph Backend["Backend"]
      API[FastAPI]
      APP[Casos de uso / dominio]
      DB[(PostgreSQL)]
      REDIS[(Redis)]
      STORE[(Storage local)]
    end

    subgraph Workers["Procesamiento asíncrono"]
      CW[Worker CPU]
      GW[Worker GPU]
    end

    subgraph Engine["AI Engine"]
      DET[Detection adapters]
      SEG[Segmentation adapters]
      ID[Identity matching]
      COND[Color conditioning]
      GEN[Generative models]
      REF[Refinement / upscaling]
    end

    FE <-->|REST + WebSocket| API
    API --> APP
    APP <--> DB
    APP <--> STORE
    APP --> REDIS
    REDIS --> CW
    REDIS --> GW
    CW <--> STORE
    GW <--> STORE
    GW --> DET
    GW --> SEG
    GW --> ID
    GW --> COND
    GW --> GEN
    GW --> REF
    DET --> SEG --> ID
    ID --> COND --> GEN --> REF
```

## 5.2 Nivel 2: módulos del backend

  ---------------------------------------------------------------------------
  Módulo                      Responsabilidades       No debe hacer
  --------------------------- ----------------------- -----------------------
  `projects`                  Crear, consultar y      Ejecutar modelos.
                              eliminar proyectos;     
                              organizar páginas.      

  `assets`                    Validar archivos,       Decidir colores.
                              calcular hashes,        
                              administrar artefactos. 

  `page_analysis`             Orquestar análisis de   Implementar
                              página y paneles.       internamente cada
                                                      detector.

  `character_analysis`        Gestionar detecciones,  Confirmar identidades
                              apariciones y           sin intervención cuando
                              agrupación de           hay ambigüedad.
                              identidades.            

  `character_configuration`   Administrar atributos,  Ejecutar inferencia
                              paletas y aprobación.   generativa.

  `character_memory`          Persistir referencias,  Ser fuente de verdad
                              embeddings y atributos  para cambios de
                              estables.               vestuario por escena.

  `colorization`              Validar precondiciones, Acoplarse a una
                              crear trabajos y        arquitectura concreta
                              orquestar el pipeline.  de modelo.

  `model_registry`            Registrar modelos,      Descargar pesos
                              versiones, capacidades  arbitrarios sin
                              y disponibilidad.       validación.

  `jobs`                      Estados, progreso,      Guardar binarios
                              cancelación y           grandes en PostgreSQL.
                              reintentos.             

  `evaluation`                Métricas, resultados    Alterar resultados
                              comparativos y          originales.
                              feedback.               
  ---------------------------------------------------------------------------

## 5.3 Organización de carpetas propuesta

``` text
manga-colorizer/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── websocket/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── modules/
│   │   │   ├── projects/
│   │   │   ├── assets/
│   │   │   ├── page_analysis/
│   │   │   ├── character_analysis/
│   │   │   ├── character_configuration/
│   │   │   ├── character_memory/
│   │   │   ├── colorization/
│   │   │   ├── model_registry/
│   │   │   ├── jobs/
│   │   │   └── evaluation/
│   │   ├── application/
│   │   │   ├── use_cases/
│   │   │   ├── dto/
│   │   │   └── ports/
│   │   ├── infrastructure/
│   │   │   ├── database/
│   │   │   ├── repositories/
│   │   │   ├── storage/
│   │   │   └── queue/
│   │   └── workers/
│   │       ├── celery_app.py
│   │       └── tasks/
│   ├── alembic/
│   └── tests/
├── ai_engine/
│   ├── contracts/
│   ├── registry/
│   ├── detection/
│   ├── segmentation/
│   ├── identity/
│   ├── conditioning/
│   ├── colorization/
│   ├── refinement/
│   ├── evaluation/
│   └── adapters/
├── frontend/
├── data/
│   ├── originals/
│   ├── intermediates/
│   ├── masks/
│   ├── references/
│   ├── results/
│   └── manifests/
├── datasets/
├── experiments/
├── docker/
├── docker-compose.yml
└── docs/
    └── architecture/
```

La estructura es una guía inicial. Los módulos deben permanecer pequeños
y con dependencias explícitas; no se deben crear capas o directorios
vacíos solo por cumplir una plantilla.

## 5.4 Contrato del motor de IA

El dominio invoca capacidades, no clases concretas de modelos. Ejemplo
conceptual:

``` python
from typing import Protocol

class CharacterDetector(Protocol):
    def detect(self, page_path: str) -> list["CharacterDetection"]:
        ...

class CharacterMatcher(Protocol):
    def group(
        self,
        appearances: list["CharacterAppearanceInput"]
    ) -> list["CharacterIdentityProposal"]:
        ...

class Segmenter(Protocol):
    def segment(
        self,
        image_path: str,
        regions: list["RegionRequest"]
    ) -> list["MaskArtifact"]:
        ...

class ColorizationEngine(Protocol):
    def colorize(
        self,
        request: "ColorizationRequest"
    ) -> "ColorizationResult":
        ...
```

Los tipos de entrada y salida deben ser DTO/dataclasses versionados. Las
rutas de archivos se resuelven a través de un servicio de
almacenamiento, no mediante rutas absolutas asumidas por el modelo.

------------------------------------------------------------------------

# 6. Vista de ejecución

## 6.1 Procesos y responsabilidades

  -----------------------------------------------------------------------
  Proceso                 Responsabilidad         Recursos
  ----------------------- ----------------------- -----------------------
  Frontend                Interacción y           CPU / navegador
                          visualización           

  API                     HTTP, validación, casos CPU / RAM
                          de uso                  

  Worker CPU              Hashes, normalización,  CPU / RAM
                          paneles y operaciones   
                          auxiliares              

  Worker GPU              Detección, segmentación GPU / VRAM
                          e inferencia pesada     

  PostgreSQL              Metadatos y estados     Disco / RAM
                          persistentes            

  Redis                   Broker y mensajes       RAM
                          temporales              

  Storage                 Imágenes, máscaras,     Disco
                          pesos y resultados      
  -----------------------------------------------------------------------

## 6.2 Secuencia: análisis de página

``` mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Q as Redis/Celery
    participant W as Worker
    participant AI as AI Engine
    participant FS as Storage

    U->>FE: Selecciona imagen
    FE->>API: POST /pages
    API->>API: Validar MIME, tamaño y dimensiones
    API->>FS: Guardar original
    API->>DB: Crear Page(status=ANALYSIS_PENDING)
    API->>Q: Encolar analyze_page(page_id)
    API-->>FE: 202 Accepted + page_id
    Q->>W: Ejecutar análisis
    W->>FS: Leer original
    W->>AI: Detectar paneles/personajes
    AI-->>W: Detecciones y máscaras
    W->>FS: Guardar artefactos
    W->>DB: Guardar paneles, apariciones y propuestas
    W->>DB: Page(status=REVIEW_REQUIRED)
    FE-->>U: Mostrar personajes detectados
```

## 6.3 Secuencia: aprobación y colorización

``` mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Q as Redis/Celery
    participant GPU as Worker GPU
    participant AI as Colorization Engine
    participant FS as Storage

    U->>FE: Edita identidad, atributos y paleta
    FE->>API: PATCH/PUT configuración
    API->>DB: Persistir cambios
    U->>FE: Aprobar configuración
    FE->>API: POST /analysis/{id}/approve
    API->>DB: Validar personajes y configuración
    API->>DB: Marcar análisis como APPROVED
    U->>FE: Solicitar colorización
    FE->>API: POST /colorizations
    API->>DB: Validar aprobación y crear job
    API->>Q: Encolar job
    API-->>FE: 202 Accepted + job_id
    Q->>GPU: Ejecutar colorización
    GPU->>FS: Leer original, máscaras y referencias
    GPU->>AI: Inferencia condicionada
    AI-->>GPU: Imagen generada
    GPU->>FS: Guardar resultado
    GPU->>DB: Marcar job COMPLETED
    FE-->>U: Mostrar resultado
```

## 6.4 Estados de análisis y trabajos

Los estados de análisis y de colorización se mantienen separados.

``` mermaid
stateDiagram-v2
    [*] --> UPLOADED
    UPLOADED --> ANALYSIS_PENDING
    ANALYSIS_PENDING --> ANALYZING
    ANALYZING --> REVIEW_REQUIRED
    ANALYZING --> ANALYSIS_FAILED
    ANALYSIS_FAILED --> ANALYSIS_PENDING: Reintentar
    REVIEW_REQUIRED --> EDITING
    EDITING --> REVIEW_REQUIRED
    REVIEW_REQUIRED --> APPROVED
    APPROVED --> [*]
```

``` mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> PREPROCESSING
    PREPROCESSING --> COLORIZING
    COLORIZING --> REFINING
    REFINING --> COMPLETED
    PENDING --> CANCELLED
    PREPROCESSING --> FAILED
    COLORIZING --> FAILED
    REFINING --> FAILED
    FAILED --> PENDING: Reintento explícito
```

Los estados pueden ampliarse con etapas internas sin cambiar los estados
públicos expuestos al frontend.

## 6.5 Concurrencia GPU

-   Configurar inicialmente un único worker GPU y concurrencia efectiva
    igual a 1 para modelos grandes.
-   Cargar el modelo una vez al iniciar el worker y mantenerlo residente
    si la VRAM lo permite.
-   Limitar tamaño de lote y resolución según el perfil de hardware.
-   Aplicar timeout y cancelación cooperativa entre etapas.
-   Evitar que workers CPU carguen accidentalmente modelos pesados.
-   Registrar VRAM disponible, duración, resolución y modelo en cada
    ejecución.
-   Permitir perfiles de inferencia: rápido, equilibrado y alta calidad.

------------------------------------------------------------------------

# 7. Vista de despliegue

## 7.1 Despliegue local inicial

``` mermaid
flowchart TB
    subgraph Host["Equipo del usuario"]
      Browser["Navegador<br/>localhost:5173"]
      subgraph Compose["Docker Compose / procesos locales"]
        FE["Frontend<br/>:5173"]
        API["FastAPI<br/>:8000"]
        PG[("PostgreSQL<br/>:5432")]
        R[("Redis<br/>:6379")]
        CPU["Worker CPU"]
      end
      GPU["Worker GPU<br/>Host o contenedor CUDA"]
      FS[("Volúmenes locales")]
      MODELS[("Modelos y pesos")]
    end
    Browser --> FE
    FE --> API
    API <--> PG
    API <--> R
    API <--> FS
    R --> CPU
    R --> GPU
    CPU <--> FS
    GPU <--> FS
    GPU --> MODELS
```

## 7.2 Puertos

  Servicio       Puerto Exposición
  ------------ -------- --------------------
  Frontend         5173 Solo localhost
  FastAPI          8000 Solo localhost
  PostgreSQL       5432 Red interna/local
  Redis            6379 Red interna/local
  Worker CPU        --- Sin puerto público
  Worker GPU        --- Sin puerto público

No es obligatorio publicar los puertos de PostgreSQL y Redis al host. En
el despliegue predeterminado deben ser accesibles solo por la red
privada de la aplicación.

## 7.3 Persistencia y copias

-   PostgreSQL: volumen persistente para metadatos.
-   Storage: directorios persistentes para originales y resultados.
-   Modelos: directorio separado, de solo lectura para workers cuando
    sea viable.
-   Configuración: archivo `.env` local excluido de Git.
-   Backups: exportación de base de datos y copia de
    manifiestos/artefactos.
-   Limpieza: política configurable para temporales, nunca borrar
    originales o resultados sin confirmación.

## 7.4 Compatibilidad GPU

Docker Compose puede administrar API, base de datos, Redis y workers
CPU. La ejecución del worker GPU debe validar previamente drivers, CUDA,
PyTorch y compatibilidad del runtime de contenedores. Si esa combinación
complica el entorno, el worker GPU puede ejecutarse en el host y
conectarse al broker local.

------------------------------------------------------------------------

# 8. Conceptos transversales

## 8.1 Seguridad y privacidad

Aunque sea una aplicación local, debe aplicar controles básicos:

-   Aceptar formatos permitidos y verificar el contenido real del
    archivo, no solo la extensión.
-   Limitar tamaño, dimensiones y número de píxeles para prevenir
    agotamiento de memoria.
-   Generar nombres internos de archivo; no utilizar directamente
    nombres proporcionados por el usuario como rutas.
-   Evitar path traversal y sobrescrituras accidentales.
-   No ejecutar archivos subidos ni cargar checkpoints arbitrarios sin
    validación.
-   No exponer Redis, PostgreSQL o directorios de almacenamiento.
-   Mantener logs sin contenido sensible ni rutas privadas innecesarias.
-   Deshabilitar telemetría externa por defecto.
-   Validar licencias y procedencia de pesos y datasets.
-   Si posteriormente se añade acceso remoto, incorporar autenticación,
    autorización, CSRF donde corresponda, límites de solicitudes y TLS.

## 8.2 Manejo de archivos y artefactos

Cada artefacto tendrá: - Identificador interno. - Tipo: original, panel,
máscara, referencia, preview o resultado. - Hash SHA-256. - Formato,
dimensiones y tamaño. - Página y trabajo relacionados. - Fecha de
creación. - Versión del pipeline que lo produjo.

Los archivos binarios no se almacenan como blobs en PostgreSQL salvo que
exista una justificación concreta.

## 8.3 Observabilidad y trazabilidad

Registrar: - `job_id`, `project_id`, `page_id` y `analysis_id`. -
Modelo, versión, checkpoint y configuración. - Semilla cuando el modelo
la soporte. - Resolución de entrada y salida. - Tiempo por etapa. - Uso
de memoria y VRAM cuando esté disponible. - Estado, error normalizado y
número de reintentos. - Métricas y feedback de evaluación.

Los logs deben ser estructurados y correlacionables por `job_id`.

## 8.4 Versionado de modelos

El registro de modelos debe incluir: - Nombre y familia del modelo. -
Versión/checkpoint. - Hash de pesos. - Licencia y fuente. - Capacidades
(detección, segmentación, colorización, upscale). - Requisitos de
hardware. - Parámetros soportados. - Estado: disponible, experimental,
deshabilitado.

Una ejecución debe apuntar a una versión inmutable del modelo o a un
manifiesto con hashes verificables.

## 8.5 Consistencia de personajes

Separar tres niveles de información:

1.  **Identidad estable:** rasgos persistentes como cabello habitual,
    color de ojos y rasgos distintivos.
2.  **Apariencia de escena:** ropa, accesorios, estado físico o cambios
    temporales.
3.  **Condición de generación:** paleta y máscaras concretas que se
    aplican a una página o conjunto de viñetas.

No asumir que el vestuario es permanente. Un personaje puede cambiar de
ropa sin convertirse en otra identidad.

## 8.6 Human-in-the-loop

El sistema debe: - Marcar confianza de detecciones y matching. - Señalar
identidades ambiguas. - Permitir renombrar, fusionar y separar
identidades. - Permitir editar paletas y atributos. - Permitir corregir
o reemplazar máscaras. - Registrar quién/qué aprobó la configuración. -
Bloquear la generación si faltan decisiones obligatorias.

------------------------------------------------------------------------

# 9. Decisiones arquitectónicas

## ADR-001 --- Monolito modular en lugar de microservicios

**Estado:** Aceptada para la primera versión.

**Contexto:** el proyecto es local, inicialmente monousuario y tiene una
complejidad dominante en el procesamiento de IA.

**Decisión:** FastAPI organiza módulos de dominio en un único backend.
Los workers se ejecutan como procesos independientes.

**Consecuencias positivas:** - Menor complejidad operativa. - Tipos y
contratos compartidos. - Depuración más sencilla. - Menos latencia y
menos infraestructura.

**Consecuencias negativas:** - Hay que proteger límites entre módulos. -
Un despliegue del backend afecta a todos los módulos API. - La
escalabilidad horizontal no es el objetivo inicial.

## ADR-002 --- Procesamiento asíncrono con Celery y Redis

**Estado:** Aceptada, pendiente de prototipo de recuperación.

**Contexto:** la inferencia puede durar segundos o minutos y no debe
bloquear HTTP.

**Decisión:** API crea trabajos persistentes y los encola. Workers
procesan tareas.

**Consecuencias:** se requieren estados persistentes, idempotencia,
timeouts y reconciliación de tareas que queden en estados intermedios.

## ADR-003 --- PostgreSQL para metadatos y filesystem para imágenes

**Estado:** Aceptada.

**Contexto:** las imágenes y máscaras son archivos grandes; las
relaciones entre proyectos, páginas, personajes y trabajos son
estructuradas.

**Decisión:** PostgreSQL almacena metadatos y el filesystem local
almacena binarios.

**Consecuencias:** deben existir referencias estables, backups
coordinados y una estrategia para limpiar archivos huérfanos.

## ADR-004 --- Motor de IA desacoplado mediante interfaces

**Estado:** Aceptada.

**Contexto:** se compararán diferentes modelos y arquitecturas durante
la investigación.

**Decisión:** casos de uso dependen de contratos, no de implementaciones
concretas.

**Consecuencias:** se requiere normalizar formatos, capacidades,
parámetros y errores de cada adaptador.

## ADR-005 --- Aprobación humana obligatoria antes de generar

**Estado:** Aceptada como requisito funcional.

**Contexto:** una imagen monocromática no revela de forma fiable los
colores originales.

**Decisión:** análisis y configuración son etapas previas; el usuario
aprueba identidades, atributos y paletas antes de la generación.

**Consecuencias:** hay más interacción, pero se mejora el control
creativo y se reduce la posibilidad de resultados cromáticamente no
deseados.

## ADR-006 --- Un worker GPU inicialmente

**Estado:** Aceptada para el primer despliegue.

**Contexto:** modelos generativos grandes compiten por VRAM.

**Decisión:** un proceso GPU con concurrencia limitada y modelos
residentes.

**Consecuencias:** menor throughput, pero menor riesgo de OOM y uso más
predecible de memoria. Se revisará tras benchmarks.

## ADR-007 --- No asumir un modelo único para detección, identidad y colorización

**Estado:** Aceptada.

**Contexto:** son tareas distintas y pueden requerir modelos
especializados.

**Decisión:** utilizar adaptadores independientes para detección,
segmentación, matching y generación.

**Consecuencias:** pipeline más modular, con más artefactos intermedios
y necesidad de medir errores acumulados.

------------------------------------------------------------------------

# 10. Requisitos de calidad y escenarios de validación

## 10.1 Fidelidad visual

**Escenario:** un usuario entrega una página con trazos finos, tramas y
texto.

**Respuesta esperada:** el sistema genera una versión coloreada sin
alterar deliberadamente la geometría, las expresiones, el texto o la
composición.

**Validación:** - Comparación de bordes/line art. - SSIM y LPIPS como
métricas complementarias. - Inspección visual de una muestra fija. -
Conteo de artefactos y deformaciones.

No se fija un umbral numérico hasta tener un baseline y un conjunto de
evaluación representativo.

## 10.2 Consistencia de personajes

**Escenario:** el mismo personaje aparece en varias viñetas.

**Respuesta esperada:** sus atributos estables se mantienen y las
variaciones de vestuario se gestionan por escena.

**Validación:** - Revisar agrupación de apariciones. - Medir errores de
identidad y matching. - Comparar colores en regiones equivalentes. -
Pruebas con personajes similares y cambios de vestuario.

## 10.3 Control humano

**Escenario:** el usuario modifica cabello y ojos y todavía no ha
aprobado la configuración.

**Respuesta esperada:** la API rechaza el inicio de colorización con un
error de precondición claro.

**Validación:** test de integración que intenta crear un trabajo sin
aprobación y comprueba que no se encola ninguna tarea.

## 10.4 Rendimiento y recursos

**Escenario:** el usuario envía una página de alta resolución.

**Respuesta esperada:** la API responde rápidamente con un identificador
de trabajo; el procesamiento continúa en background y el frontend recibe
actualizaciones.

**Validación:** - Tiempo de respuesta HTTP. - Duración por etapa. - VRAM
máxima. - Uso de RAM. - Tiempo total por resolución y perfil de calidad.

## 10.5 Recuperación

**Escenario:** el worker falla durante la generación.

**Respuesta esperada:** el trabajo queda marcado como fallido o
recuperable; no se publica un resultado incompleto como final.

**Validación:** - Simular caída del worker. - Reiniciar broker/worker. -
Verificar reconciliación de estados. - Verificar idempotencia de
reintentos.

------------------------------------------------------------------------

# 11. Riesgos y deuda técnica

  -----------------------------------------------------------------------
  Riesgo                  Impacto                 Mitigación
  ----------------------- ----------------------- -----------------------
  Identidades mal         Alto                    Confianza, revisión
  agrupadas                                       manual, merge/split y
                                                  matching especializado.

  Máscaras imprecisas     Alto                    Editor de corrección y
                                                  validación visual.

  Modelo cambia line art  Alto                    Conditioning
                                                  estructural,
                                                  comparación de bordes y
                                                  postprocesamiento.

  Inconsistencia          Alto                    Memoria de personaje,
  cromática                                       paletas persistentes y
                                                  referencias.

  VRAM insuficiente       Alto                    Perfiles de resolución,
                                                  cuantización cuando sea
                                                  compatible y worker
                                                  único.

  Dataset con licencia    Alto                    Registro de procedencia
  inadecuada                                      y revisión de
                                                  licencias.

  Fuga de datos entre     Alto                    Separar por
  train/test                                      obra/capítulo, no por
                                                  recorte aleatorio.

  Cola y DB quedan        Medio-alto              Estados persistentes,
  desincronizadas                                 outbox/reconciliación e
                                                  idempotencia.

  Dependencia de un       Medio-alto              Adaptadores y baseline
  modelo experimental                             alternativo.

  Almacenamiento crece    Medio                   Cuotas, limpieza de
  sin control                                     temporales y política
                                                  de retención
                                                  configurable.
  -----------------------------------------------------------------------

## 11.1 Riesgos específicos de IA

-   Los modelos pueden inventar detalles que no están presentes en el
    line art.
-   Un VLM puede describir incorrectamente rasgos o colores.
-   Los embeddings visuales pueden confundir personajes con diseños
    parecidos.
-   La segmentación puede incluir regiones de fondo o excluir detalles
    finos.
-   Una paleta correcta no garantiza que el generador la respete.
-   La consistencia entre páginas requiere contexto y referencias, no
    solo procesar cada imagen de forma aislada.

La aplicación debe presentar las propuestas de IA como sugerencias
editables, no como hechos confirmados.

------------------------------------------------------------------------

# 12. Glosario

  -----------------------------------------------------------------------
  Término                             Definición
  ----------------------------------- -----------------------------------
  Line art                            Trazos y contornos originales del
                                      manga.

  Panel / viñeta                      Región individual de una página
                                      narrativa.

  Character detection                 Localización de una aparición de
                                      personaje.

  Character identity matching         Estimación de qué apariciones
                                      corresponden al mismo personaje.

  Character appearance                Una aparición concreta de un
                                      personaje en una viñeta.

  Palette                             Conjunto de colores definidos para
                                      atributos o regiones.

  Mask                                Imagen o mapa que delimita una
                                      región de interés.

  Conditioning                        Información que guía al modelo
                                      generativo.

  Inference                           Ejecución del modelo para producir
                                      una salida.

  Worker                              Proceso que ejecuta tareas
                                      asíncronas.

  Artifact                            Archivo producido o utilizado por
                                      una etapa del pipeline.

  LoRA                                Técnica de adaptación eficiente de
                                      modelos preentrenados.

  Human-in-the-loop                   Intervención del usuario para
                                      validar o corregir decisiones de
                                      IA.

  Baseline                            Modelo o método inicial usado como
                                      referencia experimental.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 13. Lista de validación arquitectónica

Esta lista debe utilizarse en la revisión del diseño y antes de comenzar
la implementación.

## Arquitectura y límites

-   [ ] La API no ejecuta inferencia pesada dentro de las peticiones
    HTTP.
-   [ ] Los módulos de dominio no importan directamente implementaciones
    de modelos.
-   [ ] Los workers se comunican mediante tareas con identificadores y
    DTO versionados.
-   [ ] El motor de IA puede sustituir un adaptador sin cambiar casos de
    uso.
-   [ ] Los procesos CPU y GPU tienen responsabilidades explícitas.

## Análisis y personajes

-   [ ] Cada detección pertenece a una página y, cuando aplique, a una
    viñeta.
-   [ ] Cada aparición puede asociarse a una identidad o quedar sin
    resolver.
-   [ ] El usuario puede fusionar y separar identidades.
-   [ ] La confianza de detección/matching se conserva.
-   [ ] Las máscaras se almacenan como artefactos versionados.
-   [ ] Se distinguen atributos estables y atributos por escena.

## Configuración y aprobación

-   [ ] La paleta admite colores base, sombras y luces cuando el modelo
    los soporte.
-   [ ] Los atributos desconocidos se marcan como pendientes, no se
    inventan como certeza.
-   [ ] El usuario puede editar piel, cabello, ojos, vestimenta y
    accesorios.
-   [ ] El usuario puede corregir máscaras o solicitar una nueva
    segmentación.
-   [ ] La aprobación queda persistida y asociada a una versión de
    configuración.
-   [ ] No se puede crear un trabajo de colorización sin aprobación
    válida.

## Procesamiento

-   [ ] Los trabajos son asíncronos y tienen estados persistentes.
-   [ ] Los reintentos son idempotentes.
-   [ ] Se controlan timeout, cancelación y errores.
-   [ ] El worker GPU limita la concurrencia.
-   [ ] Los artefactos incompletos no se publican como resultados
    finales.
-   [ ] Se registra la versión exacta del modelo y los parámetros.

## Operación local

-   [ ] PostgreSQL y Redis no están expuestos innecesariamente.
-   [ ] Los archivos se validan por contenido, tamaño y dimensiones.
-   [ ] Las rutas se generan de forma segura.
-   [ ] Los datos persisten tras reiniciar los contenedores.
-   [ ] Existe una estrategia de backup y limpieza.
-   [ ] El modo normal no requiere enviar imágenes a servicios externos.

## Evaluación

-   [ ] Existe un conjunto fijo de páginas de prueba con permisos
    adecuados.
-   [ ] La partición de evaluación evita fuga por obra/capítulo.
-   [ ] Se miden calidad perceptual, fidelidad estructural y
    consistencia.
-   [ ] Se realiza evaluación humana.
-   [ ] Los resultados de cada experimento son reproducibles.

------------------------------------------------------------------------

# 14. Próximos pasos recomendados

Orden sugerido de implementación:

1.  **Cerrar decisiones de producto y hardware:** GPU objetivo,
    resoluciones, formatos, tamaño máximo y tiempos aceptables.
2.  **Crear el esqueleto del backend:** FastAPI, PostgreSQL, SQLAlchemy,
    Alembic, Redis y Celery.
3.  **Definir entidades y contratos:** Project, Page, Panel, Character,
    CharacterAppearance, Palette, MaskArtifact, Analysis y
    ColorizationJob.
4.  **Implementar carga y almacenamiento:** validación, hash,
    persistencia y descarga.
5.  **Implementar pipeline de análisis:** paneles, detección, matching y
    máscaras con adaptadores reemplazables.
6.  **Construir el editor de personajes:** corrección de identidad,
    atributos, paletas y máscaras.
7.  **Implementar aprobación y bloqueo:** pruebas que garanticen que no
    se colorea antes de aprobar.
8.  **Integrar un baseline de colorización:** primero inferencia,
    después fine-tuning.
9.  **Medir y comparar:** calidad, fidelidad, consistencia, VRAM y
    latencia.
10. **Optimizar y empaquetar:** Docker Compose, worker GPU y
    funcionamiento offline.

## Decisiones pendientes para la revisión

  -----------------------------------------------------------------------
  Pregunta                            Decisión por tomar
  ----------------------------------- -----------------------------------
  GPU objetivo                        Modelo exacto, VRAM y
                                      compatibilidad CUDA.

  Resolución                          Procesamiento de página completa o
                                      por viñetas/tileado.

  Alcance de proyecto                 Una imagen, capítulo o colección de
                                      capítulos.

  Persistencia                        Política de retención de
                                      originales, temporales y
                                      resultados.

  Modelo inicial                      Baseline a reproducir y licencia de
                                      uso.

  Corrección de máscaras              Editor manual en MVP o solo
                                      resegmentación.

  Interfaz de progreso                WebSocket, polling o ambos.

  Distribución                        Solo ejecución desde código o
                                      instalador local.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

**Fin del documento.**

Este documento describe una arquitectura propuesta, no una
implementación existente. Las decisiones marcadas como pendientes deben
validarse con prototipos, pruebas de hardware y evaluación de modelos
antes de congelar contratos o comprometerse con una arquitectura de
inferencia concreta.
