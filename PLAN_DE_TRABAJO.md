# Plan de trabajo: Rediseño de Frontend y ajustes de Backend (Star Colorizing)

> Documento pensado para lectura y ejecución agéntica. Cada fase tiene objetivos, tareas y un **Comprobante de fase (gate)**. **No se puede iniciar la siguiente fase hasta que todos los comprobantes de la fase actual estén cumplidos y registrados.**

---

## 0. Instrucciones de arranque para el agente (leer primero)

### 0.1 Estado actual (el agente lo actualiza al cerrar cada fase)

```
FASE_ACTUAL: 6
ULTIMA_FASE_COMPLETADA: 5
BLOQUEOS_ABIERTOS: ninguno
```

### 0.2 Protocolo de arranque y reanudación
1. Leer este archivo completo y luego la **Bitácora** (sección 5) y el bloque de estado de arriba.
2. Si `FASE_ACTUAL` es 0 y la Bitácora está vacía, empezar por la Fase 0. Si no, **reanudar en `FASE_ACTUAL`** y revisar qué casillas ya están marcadas; no rehacer lo ya verificado.
3. Trabajar una fase a la vez. Al cerrarla: marcar casillas, completar la Bitácora, actualizar el bloque de estado y hacer un commit (`fase-N: resumen`).

### 0.3 Protocolo de bloqueo
Si un comprobante falla tras dos intentos razonables de corrección, o falta información que no está en el código ni en este documento: **detenerse**, escribir el problema en `BLOQUEOS_ABIERTOS` y en la Bitácora (qué se intentó, qué error, qué se necesita) y no marcar la fase como completada. No saltar a la siguiente fase ni "dejarlo para después".

### 0.4 Evidencia aceptable en los comprobantes
Preferir siempre evidencia verificable por máquina: comando ejecutado y su salida, resultado de tests, respuesta de un endpoint, resultado de una búsqueda en el código (`grep`). Las capturas de pantalla solo se piden donde el plan lo dice y, si el agente no puede tomarlas, se sustituyen por una descripción de lo observado más una prueba automatizada del comportamiento. Una casilla sin evidencia registrada no cuenta como cumplida.

### 0.5 Decisiones ya tomadas (no volver a preguntarlas)
- Upload es un paso no retornable: tras completarse queda visible pero no clicable y bloqueado por URL. Desde Analysis en adelante se puede retroceder.
- Abrir un proyecto siempre redirige a su `current_stage`.
- El Model Registry admite varios modelos activos; uno es el predeterminado por tarea. Un modelo válido queda activo al guardarse.
- La portada de un proyecto es una miniatura de la imagen subida por el usuario.
- Pruebas locales hasta la Fase 9; Docker solo en la Fase 10.

### 0.6 Fuera de alcance (no tocar salvo que sea imprescindible y se registre)
- La sección **System** del sidebar y su funcionalidad.
- La funcionalidad interna de **Settings** (solo verificar que no dependa de elementos eliminados).
- La lógica de los algoritmos de análisis, máscara y colorización (este plan cambia navegación, flujo, API y registro de modelos, no los algoritmos).

### 0.7 Mapeo del mockup a la estructura nueva

| Elemento del mockup | Destino |
|---|---|
| Dashboard | Se mantiene, con datos reales (Fase 3) |
| Projects | Se mantiene, con portadas y estados (Fase 4) |
| Analysis Studio | Etapa **Analysis** dentro del proyecto |
| Directory / Color | Se absorben en la etapa **Character** o se eliminan si no tienen función real (decidir en Fase 0 y registrar) |
| Mask Editor | Etapa **Mask** dentro del proyecto |
| Review | Etapa **Approve** dentro del proyecto |
| Colorize Center | Etapa **Colorize** dentro del proyecto |
| Result / Export | Etapa **Export** dentro del proyecto y listado global en **Results & Exports** |
| Colorization Jobs, Model Registry, Settings | Se mantienen como secciones globales |
| Sección "Pipeline" del sidebar, barra global de pasos, toggle empty state, Discover Sumi, Convention | Se eliminan |

### 0.8 Convenciones
- Documento en español; identificadores de código, rutas, claves de etapa y nombres de endpoints en inglés (`upload`, `analysis`, `character`, `mask`, `approve`, `colorize`, `export`).
- Seguir el estilo, la estructura de carpetas y las librerías ya presentes en el repositorio; no introducir dependencias nuevas sin justificarlo en la Bitácora.
- Un commit por fase como mínimo, para poder revertir una fase sin perder las anteriores.

### 0.9 Defecto conocido a corregir: confusión entre `page_id` y `analysis_id`

**Síntoma reproducible:**
1. Se sube `79.jpg` → el backend crea una página con `page_id` = `398aa755-7149-4b51-9a48-8f0077613283` (201 Created).
2. Se ejecuta el análisis con `POST /api/v1/analysis/{page_id}` → funciona y crea un análisis con un ID **distinto**, `analysis_id` = `da8e5eee-59e3-4ae6-88e5-bcc8272d2feb`.
3. Al aprobar, el frontend llama a `GET /api/v1/analysis/{page_id}` y a `POST /api/v1/analysis/{analysis_id}/approve`, pero **en la segunda ruta envía el `page_id` donde debería ir el `analysis_id`** → 404 Not Found.
4. El mismo error afecta a las rutas de colorización.

**Diagnóstico:** el backend funciona correctamente; el fallo está en que el frontend no guarda ni propaga el `analysis_id` devuelto al completarse el análisis y reutiliza el `page_id` en rutas que esperan el ID del análisis. Esto debe confirmarse en la Fase 0 leyendo el código, sin darlo por hecho.

**Regla de identificadores (vale para todo el plan):**

| Identificador | Qué representa | Se usa en |
|---|---|---|
| `page_id` | Página/imagen subida | Subida, lanzar análisis (`POST /analysis/{page_id}`), obtener análisis de una página (`GET /analysis/{page_id}`) |
| `analysis_id` | Un análisis concreto generado para esa página | Aprobar (`POST /analysis/{analysis_id}/approve`), y las rutas posteriores que dependan del análisis (colorización) |

Nunca se debe usar uno donde se espera el otro. Una página puede tener varios análisis si se vuelve a ejecutar; el sistema debe saber cuál es el vigente.

---

## 1. Objetivo general

Reemplazar la interfaz actual, construida a ciegas sobre un mockup, por una aplicación cuya navegación y flujo reflejen el funcionamiento real del producto:

- La navegación global solo contiene secciones globales (Dashboard, Projects, Results & Exports, Colorization Jobs, Model Registry, Settings, System).
- El pipeline (Upload → Analysis → Character → Mask → Approve → Colorize → Export) vive **dentro de cada proyecto** y no fuera de él.
- Cada proyecto muestra su portada real (la imagen subida), su estado y lo lleva a la etapa en la que se encuentra.
- El backend expone la información necesaria (etapa actual, estado, portada, métricas) y valida las transiciones entre etapas.
- El Model Registry permite agregar, activar y desactivar modelos locales (`.pt`, `.onnx`) y modelos basados en API, con una arquitectura abierta a nuevos formatos y proveedores.

---

## 2. Reglas para el agente

1. Ejecutar las fases en orden. Marcar cada casilla `[x]` solo cuando esté verificada, no cuando esté escrita.
2. Antes de modificar algo, leer el código existente. No asumir la estructura: la Fase 0 la documenta.
3. No eliminar código sin confirmar (con búsqueda de referencias) que no se usa en otro lugar.
4. Al terminar cada fase, escribir un breve registro en la sección **Bitácora** al final de este archivo (qué se hizo, qué evidencia hay, qué quedó pendiente).
5. Si un comprobante falla, corregir y volver a verificar. No saltarlo ni marcarlo como cumplido parcialmente.
6. Si algo es ambiguo y no se puede resolver leyendo el código, registrar la suposición en la Bitácora y continuar con la opción más conservadora.
7. **Todas las pruebas de las Fases 0 a 9 se hacen de forma local**, sin Docker: backend y frontend se levantan directamente en la máquina de desarrollo (por ejemplo con el servidor de desarrollo, entorno virtual, base de datos local o SQLite si aplica) y los tests se ejecutan con los comandos nativos del proyecto. Cada comprobante debe registrar el comando exacto usado.
8. **Docker no se usa hasta la Fase 10.** No ejecutar `docker` ni `docker compose` antes de esa fase para probar, depurar ni validar nada. Si ya existen archivos Docker en el repositorio, se ignoran hasta la Fase 10, donde se revisan y actualizan.
9. La Fase 10 es la única donde se construye `docker compose` y se valida el sistema dentro de contenedores. Se hace al final porque aísla los problemas: si algo falla en Docker pero pasaba en local, el fallo es de empaquetado o configuración, no de la lógica de la aplicación.

---

## 3. Modelo de referencia (definiciones que se usan en todo el plan)

**Etapas del proyecto (orden fijo):**

| # | Etapa | Clave sugerida |
|---|-------|----------------|
| 1 | Upload | `upload` |
| 2 | Analysis | `analysis` |
| 3 | Character | `character` |
| 4 | Mask | `mask` |
| 5 | Approve | `approve` |
| 6 | Colorize | `colorize` |
| 7 | Export | `export` |

**Regla de navegación entre etapas:**
- Se puede retroceder entre cualquier etapa desde Analysis en adelante (Character → Analysis, Mask → Character, Approve → Mask, etc.).
- **Upload no es retornable**: una vez completada, queda como paso cumplido, visible en el stepper pero no clicable, y ninguna ruta debe permitir volver a ella para ese proyecto.
- No se puede avanzar a una etapa si la anterior no está completada.
- Abrir un proyecto siempre redirige a su **etapa actual**.

**Navegación global (sidebar) final:**

- Workspace: Dashboard, Projects, Results & Exports, Colorization Jobs, Model Registry, Settings
- System: se mantiene tal como está

**Elementos que se eliminan:** secciones "Pipeline" del sidebar (Analysis Studio, Directory, Color, Mask Editor, Review, Colorize Center, Result, Export como entradas globales), barra global de pasos Upload/Analysis/Character…, botón/toggle "empty state", bloque "Discover Sumi", bloque "Convention".

---

## Fase 0: Diagnóstico y línea base

**Objetivo:** Entender el estado real del código antes de tocar nada.

**Tareas**
- [x] Identificar stack del frontend (framework, router, gestión de estado, librería de estilos) y del backend (framework, base de datos, ORM, almacenamiento de archivos).
- [x] Mapear todas las rutas actuales del frontend y los componentes de layout (sidebar, header, barra de pasos).
- [x] Mapear todos los endpoints actuales del backend y el modelo de datos del proyecto (¿existe campo de etapa/estado? ¿se guarda la imagen original? ¿hay miniatura?).
- [x] Listar cada elemento del mockup que se va a eliminar y dónde está implementado (sidebar, stepper global, toggle empty state, Discover Sumi, Convention).
- [x] Ejecutar el proyecto y los tests existentes **de forma local (sin Docker)** para registrar la línea base (qué pasa y qué falla antes de los cambios), y documentar en la Bitácora los comandos exactos para levantar backend y frontend en local y para correr los tests.
- [x] Documentar cómo se cargan y usan hoy los modelos (rutas, formatos, dónde se invocan en el pipeline, configuración actual) para diseñar el Model Registry sobre lo existente.
- [x] Crear una rama de trabajo dedicada.

**Comprobante de fase 0**
- [x] Existe en la Bitácora un resumen con: stack, mapa de rutas, mapa de endpoints, modelo de datos del proyecto y lista de elementos a eliminar con su ubicación.
- [x] La aplicación arranca y el estado de los tests de línea base está documentado.

---

## Fase 1: Backend, modelo de proyecto y contratos de API

**Objetivo:** Que el backend entregue lo que el nuevo frontend necesita y sea la fuente de verdad de las etapas.

**Tareas**
- [x] Añadir/confirmar en el modelo de proyecto: `current_stage` (enum de las 7 etapas), `status` (por ejemplo: `en_progreso`, `completado`, `con_error`, `procesando`), `stage_progress` (qué etapas están completadas) y `cover_image` (referencia a la imagen subida).
- [x] Generar y almacenar una **miniatura** al subir la imagen, para usarla como portada de la tarjeta del proyecto (evitar cargar la imagen completa en el listado).
- [x] Endpoint de listado de proyectos que devuelva por proyecto: id, nombre, tipo, portada (URL de miniatura), etapa actual, estado, porcentaje de avance y fecha de última actualización. Con paginación y filtro por estado.
- [x] Endpoint de detalle de proyecto con su etapa actual y las etapas completadas.
- [x] **Identificadores (ver 0.9):** el detalle del proyecto/página debe devolver `page_id` y el `analysis_id` **vigente** (último análisis válido), de modo que el frontend nunca tenga que deducirlo ni reutilizar `page_id` en su lugar. Si hay varios análisis, definir y documentar cuál es el vigente y exponer el historial si hace falta.
- [x] Revisar que las respuestas de `POST /analysis/{page_id}` incluyan explícitamente el `analysis_id` creado, y que las rutas de aprobación y colorización documenten con claridad qué identificador esperan.
- [x] Mensaje de error distinguible: si una ruta que espera `analysis_id` recibe un `page_id`, el 404 debe indicar qué recurso no se encontró (por ejemplo "analysis not found"), para facilitar el diagnóstico.
- [x] Endpoint de transición de etapa con validaciones: no avanzar sin completar la anterior; no volver a `upload` una vez completada; retrocesos permitidos desde `analysis` en adelante. Respuestas con errores claros (código y mensaje).
- [x] Endpoint de subida con validación (tipo, tamaño máximo) y respuesta explícita de éxito/error, con mensajes que el frontend pueda mostrar.
- [x] Endpoint de métricas para el dashboard: total de proyectos, proyectos por estado, proyectos por etapa, jobs activos/fallidos/completados, últimos proyectos actualizados.
- [x] Verificar/ajustar endpoints para Results & Exports y Colorization Jobs (listado y estado).
- [x] **Model Registry, modelo de datos:** entidad `model` con id, nombre, versión, tarea que cumple (por ejemplo colorización, segmentación, análisis), `source_type` (`local_file` | `api`), formato (`pt`, `onnx`, `api`, extensible), `is_active`, estado de salud (`ok`, `error`, `no_verificado`), metadatos (descripción, parámetros) y fechas.
- [x] **Capa de adaptadores:** definir una interfaz común (por ejemplo `validate`, `load`, `unload`, `infer`, `health_check`) y un adaptador por tipo: PyTorch (`.pt`), ONNX (`.onnx`) y API externa. El pipeline debe consumir modelos solo a través de esta interfaz, de modo que agregar un formato o proveedor nuevo (otros formatos locales, otro servicio de API) sea crear un adaptador y registrarlo, sin tocar el resto del sistema.
- [x] **Modelos locales:** endpoint de subida de archivo con validación de extensión, tamaño máximo y checksum; almacenamiento fuera de la carpeta pública; verificación de que el archivo carga correctamente antes de registrarlo.
- [x] **Seguridad de archivos `.pt`:** estos archivos pueden ejecutar código arbitrario al cargarse (pickle). Cargarlos con `weights_only=True` o con un mecanismo equivalente, o aislar la carga en un proceso/sandbox, y dejar documentado el riesgo. Preferir ONNX o safetensors cuando sea posible.
- [x] **Modelos por API:** registro con proveedor/nombre, URL base, método de autenticación, clave o token, modelo/endpoint a invocar y parámetros por defecto (timeout, reintentos). Endpoint de **prueba de conexión** antes de guardar.
- [x] **Secretos:** las claves de API se almacenan cifradas (o en un gestor de secretos), nunca se devuelven al frontend (solo enmascaradas, por ejemplo `sk-…abcd`) ni aparecen en logs.
- [x] **Activar/desactivar:** endpoints para activar y desactivar un modelo. Al registrar un modelo válido, queda **activo por defecto**. Permitir varios modelos activos y marcar uno como predeterminado por tarea. Un modelo desactivado no debe poder ser seleccionado por el pipeline.
- [x] **Protección de uso en curso:** si un modelo tiene jobs en ejecución, impedir desactivarlo o eliminarlo (o avisar claramente y exigir confirmación), sin dejar jobs huérfanos.
- [x] Endpoints de listado, detalle, edición (nombre, descripción, parámetros, credenciales) y eliminación de modelos.
- [x] Si no hay ningún modelo activo para una tarea requerida, el backend devuelve un error claro que el frontend pueda mostrar en la etapa correspondiente.
- [x] Migración de datos: asignar `current_stage` y `status` coherentes a proyectos ya existentes.
- [x] Documentar los contratos (OpenAPI o archivo equivalente).

**Comprobante de fase 1**
- [x] Tests automatizados del backend para: transición válida, transición inválida (saltar etapa), intento de volver a `upload`, subida correcta, subida inválida (tipo/tamaño), listado con miniatura, métricas del dashboard. Todos pasan.
- [x] Prueba manual (curl/cliente HTTP) de cada endpoint nuevo con respuesta documentada en la Bitácora.
- [x] La migración se ejecuta sobre datos existentes sin errores ni proyectos sin etapa.
- [x] Contratos de API documentados y accesibles.
- [x] Tests del Model Registry que pasan: registrar `.pt` válido, registrar `.onnx` válido, rechazar archivo corrupto o de extensión no permitida, registrar modelo por API con prueba de conexión exitosa y fallida, activar/desactivar, bloquear desactivación con job en curso, y verificar que la clave de API no aparece en ninguna respuesta ni log.
- [x] Se demuestra que agregar un adaptador nuevo (aunque sea de prueba/mock) no requiere modificar el pipeline.
- [x] Test de backend del escenario 0.9: subir imagen → crear análisis → verificar que el detalle devuelve el `analysis_id` correcto → aprobar con ese ID (éxito) → aprobar con el `page_id` (404 con mensaje claro).

---

## Fase 2: Navegación global y layout

**Objetivo:** Dejar el shell de la aplicación limpio y alineado con lo que realmente es global.

**Tareas**
- [x] Sidebar, sección Workspace: dejar únicamente Dashboard, Projects, Results & Exports, Colorization Jobs, Model Registry y Settings.
- [x] Eliminar del sidebar la sección "Pipeline" completa (depende del proyecto y estaba ambigua/bloqueada).
- [x] Mantener la sección **System** sin cambios.
- [x] Eliminar la barra global de pasos (Upload, Analysis, Character, Mask, Approve, Colorize, Export) del layout principal.
- [x] Eliminar el toggle de "empty state".
- [x] El título/logo **Star Colorizing** enlaza a `/projects`.
- [x] Eliminar el bloque "Discover Sumi" y cualquier referencia a Sumi.
- [x] Rutas antiguas del pipeline global: redirigir a `/projects` o eliminar, sin dejar enlaces rotos.
- [x] Resaltado correcto del ítem activo en el sidebar.

**Comprobante de fase 2**
- [x] Captura(s) del sidebar mostrando exactamente los 6 ítems de Workspace más System.
- [x] Búsqueda en el código: no quedan referencias a "Discover Sumi", al toggle de empty state ni a la barra global de pasos (o están justificadas en la Bitácora).
- [x] Clic en "Star Colorizing" lleva a Projects.
- [x] Ninguna ruta del sidebar ni redirección devuelve 404 o pantalla vacía.

---

## Fase 3: Dashboard

**Objetivo:** Que el dashboard muestre cómo va el trabajo, no una descripción del producto.

**Tareas**
- [x] Reemplazar el contenido descriptivo por datos reales del endpoint de métricas: total de proyectos, distribución por estado, distribución por etapa, jobs en curso/fallidos, actividad reciente.
- [x] Mantener un encabezado breve (puede conservarse una descripción corta del producto, pero sin ocupar el protagonismo).
- [x] Eliminar el bloque "Convention" y "Discover Sumi".
- [x] Lista de "proyectos recientes" con portada, etapa y estado, clicable hacia el proyecto.
- [x] Estados de carga, vacío (sin proyectos, con llamada a crear uno) y error.

**Comprobante de fase 3**
- [x] El dashboard muestra datos que coinciden con la base de datos (verificar con al menos dos proyectos en estados distintos).
- [x] Con cero proyectos se ve un estado vacío útil; con error de API se ve un mensaje, no una pantalla rota.
- [x] Clic en un proyecto reciente abre el proyecto en su etapa actual (valida junto con Fase 5).

---

## Fase 4: Projects (listado)

**Objetivo:** Ver todos los proyectos, su portada real y su estado de un vistazo.

**Tareas**
- [x] Vista de cuadrícula/lista con una tarjeta por proyecto.
- [x] Portada de la tarjeta = **la imagen subida al iniciar el proyecto** (miniatura), no una imagen publicitaria. Fallback visual si aún no hay imagen.
- [x] Cada tarjeta muestra: nombre, tipo, etapa actual, estado (con indicador visual por color/etiqueta), progreso y última actualización.
- [x] Filtros por estado y etapa; búsqueda por nombre; ordenamiento por fecha (el backend ordena por fecha de creación descendente).
- [x] Botón "Nuevo proyecto" que crea el proyecto y navega a él (el flujo Upload dentro del proyecto se implementa en Fase 5/6).
- [x] Clic en tarjeta → abre el proyecto (`/projects/:id`, redirección a etapa actual en Fase 5).
- [x] Estados de carga, vacío y error.

**Comprobante de fase 4**
- [x] Con proyectos de distintas etapas y estados, cada tarjeta muestra la portada (miniatura o fallback) y los datos correctos (etapa, estado con badge, progreso, última actualización). Datos provienen del backend.
- [x] Filtros por estado y etapa y búsqueda por nombre funcionan en el frontend (filtrado en memoria sobre la lista del backend).
- [x] Clic en tarjeta redirige a `/projects/:id`; la redirección a la etapa actual se valida en Fase 5 (proyecto en Analysis y otro en Mask).

---

## Fase 5: Contenedor de proyecto y stepper interno

**Objetivo:** Que el pipeline viva dentro del proyecto, con el usuario siempre sabiendo en qué etapa está.

**Tareas**
- [x] Ruta anidada por proyecto (por ejemplo `/projects/:id/:stage`) con layout propio.
- [x] Al entrar a `/projects/:id` redirigir automáticamente a la etapa actual (`current_stage`).
- [x] Stepper visual **dentro** del proyecto con las 7 etapas: completadas, actual y pendientes diferenciadas.
- [x] Navegación del stepper según las reglas: retroceso permitido desde Analysis en adelante; Upload completada aparece como cumplida y **no clicable**; etapas futuras no accesibles hasta completar la anterior.
- [x] Guardas de ruta: si alguien intenta entrar por URL a una etapa no permitida (adelantada o a Upload ya completada), redirigir a la etapa actual con mensaje informativo.
- [x] Encabezado del proyecto con nombre, estado, portada pequeña e información de la etapa actual (qué se hace en esta etapa y qué falta para avanzar).
- [x] Cada etapa muestra su información propia (ver Fase 7) y un botón claro para avanzar.

**Comprobante de fase 5**
- [x] Contenedor de proyecto y stepper implementados (rutas /projects/:id y /projects/:id/:stage, ProjectLayout con stepper de 7 etapas y guarda de ruta).
- [x] Intento por URL de entrar a Upload en un proyecto ya pasado de Upload: se bloquea y redirige (guarda de ruta implementada).
- [x] Intento por URL de saltar a una etapa futura: se bloquea y redirige (guarda de ruta implementada).
- [x] Retrocesos permitidos (Character → Analysis, Mask → Character, Approve → Mask) implementados mediante PATCH /stage con action=regress.
- [x] El stepper solo se renderiza dentro de un proyecto (ProjectLayout solo bajo /projects/:id/:stage).
- [ ] Prueba con proyectos reales en BD (cada etapa, apertura en etapa correcta, retroceso conserva datos) — se ejecuta en Fase 7 con datos de la API.

---

## Fase 6: Etapa Upload (rediseño)

**Objetivo:** Corregir la página de subida, que hoy se ve sin estilos, empieza desplazada hacia abajo y no da retroalimentación.

**Tareas**
- [ ] Aplicar el sistema de estilos de la aplicación (zona de arrastrar y soltar, botón de selección, tipografía y espaciados consistentes con el resto).
- [ ] Corregir el scroll: la página debe iniciar **arriba** (restablecer scroll al entrar a la ruta) y no requerir bajar para subir el archivo.
- [ ] Vista previa de la imagen **acotada** (alto/ancho máximo con `object-fit: contain`), de modo que una imagen grande no obligue a hacer scroll para ver los controles.
- [ ] Mensajes de estado visibles: archivo seleccionado, subiendo (con barra o indicador de progreso), subida exitosa, error (tipo no permitido, tamaño excedido, fallo de red) con opción de reintentar.
- [ ] Botón "Continuar" habilitado solo tras una subida exitosa; al continuar, marca Upload como completada y avanza a Analysis.
- [ ] Una vez completada, Upload no se puede volver a abrir para ese proyecto (coherente con Fase 5 y Fase 1).
- [ ] Accesibilidad básica: foco visible, mensajes anunciados (aria-live), uso con teclado.

**Comprobante de fase 6**
- [ ] Prueba con imagen pequeña, imagen muy grande (alto), archivo de tipo inválido y archivo que excede el tamaño: cada caso muestra el mensaje esperado.
- [ ] La página se abre en la parte superior en escritorio y móvil.
- [ ] Tras subir y continuar, el proyecto queda en Analysis, la portada aparece en Projects y no hay manera de regresar a Upload.
- [ ] Captura antes/después en la Bitácora.

---

## Fase 7: Etapas Analysis, Character, Mask, Approve, Colorize y Export

**Objetivo:** Que cada etapa muestre información propia, conserve su estado y respete la navegación definida.

**Tareas (aplicar a cada etapa)**
- [ ] Analysis: resultados del análisis de la imagen, estado del procesamiento, errores si los hay.
- [ ] Character: selección/gestión de personajes detectados.
- [ ] Mask: editor de máscara (el antiguo "Mask Editor" pasa a ser exclusivamente esta etapa).
- [ ] Approve: resumen de lo definido (análisis, personajes, máscaras) para aprobar antes de colorizar (el antiguo "Review").
- [ ] Colorize: lanzamiento y seguimiento del trabajo de colorización (el antiguo "Colorize Center"), enlazado con Colorization Jobs.
- [ ] Export: opciones y descarga del resultado final (el antiguo "Export"/"Result"), enlazado con Results & Exports.
- [ ] En cada etapa: encabezado con título y descripción de lo que ocurre, estado de la etapa, botón de avanzar (deshabilitado hasta cumplir requisitos) y retroceso según reglas.
- [ ] Persistir el progreso de cada etapa en backend para poder retroceder y volver sin perder datos.
- [ ] **Corregir el defecto 0.9:** al completarse el análisis, el frontend guarda el `analysis_id` devuelto (en el estado del proyecto/caché de datos) y lo usa en `POST /analysis/{analysis_id}/approve` y en las rutas de colorización. `page_id` solo se usa donde la API lo espera (subida, lanzar análisis, obtener análisis de la página).
- [ ] El `analysis_id` no debe depender de que el usuario venga del paso inmediato anterior: al abrir o recargar Approve o Colorize directamente, el frontend lo obtiene del detalle del proyecto (Fase 1), no de un estado en memoria que se pierde al refrescar.
- [ ] Si el análisis se vuelve a ejecutar, el frontend pasa a usar el nuevo `analysis_id` vigente y descarta el anterior.
- [ ] Revisar **todas** las llamadas del frontend que contengan un identificador en la ruta (`grep` de los endpoints `/api/v1/...`) y confirmar, una por una, que reciben el tipo de ID correcto. Registrar la lista en la Bitácora.
- [ ] Reutilizar los componentes del mockup que sean correctos; reescribir los que estén mal diseñados.

**Comprobante de fase 7**
- [ ] Recorrido completo de punta a punta con un proyecto nuevo: Upload → Analysis → Character → Mask → Approve → Colorize → Export, sin errores y con la etapa actual/estado actualizados en cada paso.
- [ ] Retroceso y avance posterior (por ejemplo Approve → Mask → Approve) conserva los datos.
- [ ] **Regresión del defecto 0.9 en local:** subir `79.jpg`, ejecutar análisis, aprobar y colorizar. Ninguna petición devuelve 404 por ID incorrecto; en las peticiones de red se verifica que aprobar usa el `analysis_id` y no el `page_id`.
- [ ] Recargar el navegador estando en Approve y en Colorize y repetir la acción: sigue funcionando.
- [ ] Volver a ejecutar el análisis y aprobar: usa el nuevo `analysis_id`.
- [ ] Tabla de la Bitácora con cada endpoint llamado por el frontend y el tipo de ID que recibe, todos correctos.
- [ ] El proyecto finalizado aparece como completado en Projects y en el Dashboard.

---

## Fase 8: Results & Exports, Colorization Jobs, Model Registry y Settings

**Objetivo:** Asegurar que las secciones globales restantes funcionen y sean coherentes con el nuevo modelo.

**Tareas**
- [ ] Results & Exports: listado global de resultados y exportaciones de todos los proyectos, con enlace al proyecto de origen y descarga.
- [ ] Colorization Jobs: listado de jobs con estado (en cola, procesando, completado, fallido), proyecto asociado y acciones razonables (ver detalle, reintentar si aplica).
- [ ] **Model Registry, listado:** tabla/tarjetas con nombre, tipo (archivo local o API), formato, versión, tarea, estado de salud y un **interruptor activar/desactivar** por modelo, con feedback inmediato y manejo de error.
- [ ] **Model Registry, agregar modelo:** botón "Agregar modelo" que abre un flujo con dos caminos:
  - *Archivo local:* zona de arrastrar y soltar para `.pt` / `.onnx`, nombre, tarea, versión y descripción; barra de progreso de subida; validación y mensajes claros de éxito/error. Al guardarse correctamente, el modelo queda **activo**.
  - *API:* formulario con proveedor, URL, autenticación (campo de clave oculto), modelo/endpoint y parámetros; botón "Probar conexión" con resultado visible; al guardarse correctamente, el modelo queda **activo**.
- [ ] El formulario se genera según el tipo elegido, de modo que un nuevo tipo de modelo (registrado en el backend) pueda aparecer sin rediseñar la pantalla.
- [ ] **Model Registry, gestión:** editar, marcar como predeterminado por tarea y eliminar (con confirmación y aviso si está en uso). Las claves de API se muestran enmascaradas y solo se pueden reemplazar, nunca leer.
- [ ] **Integración con el pipeline:** las etapas que usan modelos (Analysis, Mask, Colorize, etc.) muestran solo modelos activos y permiten elegir entre ellos; si no hay ninguno activo, muestran un aviso con enlace al Model Registry.
- [ ] Settings: conservar la funcionalidad existente; revisar que no dependa de elementos eliminados.
- [ ] System: verificar que sigue funcionando sin cambios.
- [ ] Estados de carga, vacío y error en cada sección.

**Comprobante de fase 8**
- [ ] Cada una de las 6 secciones de Workspace y System abre sin errores y muestra datos reales o su estado vacío.
- [ ] Los enlaces de Results y Jobs hacia el proyecto de origen llevan a la etapa correcta.
- [ ] Prueba manual en el Model Registry: agregar un `.pt` (queda activo), agregar un `.onnx` (queda activo), agregar un modelo por API con prueba de conexión (queda activo), desactivar uno y comprobar que desaparece de las opciones del pipeline, reactivarlo y comprobar que vuelve a aparecer.
- [ ] Un archivo inválido y una API inalcanzable muestran un error claro y no dejan registros a medias.
- [ ] Una colorización de extremo a extremo usa un modelo registrado desde la interfaz (no uno configurado a mano).

---

## Fase 9: Calidad, regresión y pulido

**Objetivo:** Dejar el trabajo estable, consistente y verificable.

**Tareas**
- [ ] Tests automatizados del frontend para: sidebar, redirección a etapa actual, guardas de ruta, bloqueo de Upload, tarjeta de proyecto con portada.
- [ ] Prueba end-to-end del flujo completo (crear proyecto → exportar), incluyendo un test automatizado de regresión del defecto 0.9 (subir imagen, analizar, aprobar y colorizar verificando que se usa el `analysis_id` correcto en cada ruta).
- [ ] Revisión responsive (escritorio, tablet, móvil) de Dashboard, Projects, proyecto y Upload.
- [ ] Revisión de accesibilidad básica (contraste, foco, etiquetas).
- [ ] Búsqueda final de código muerto, rutas huérfanas y referencias a elementos eliminados.
- [ ] Actualizar documentación (README y contratos de API) con el nuevo flujo y la navegación.

**Comprobante de fase 9**
- [ ] Toda la batería de tests (backend y frontend) pasa **ejecutada en local**.
- [ ] El flujo end-to-end pasa **ejecutado en local**, con backend y frontend levantados directamente (sin Docker).
- [ ] No hay errores en consola del navegador ni warnings relevantes en los recorridos principales.
- [ ] Documentación actualizada.
- [ ] La aplicación completa funciona en local y queda congelada como referencia: lista de comandos y resultados esperados registrada en la Bitácora para compararla con la Fase 10.

---

## Fase 10: Docker Compose y validación en contenedores

**Objetivo:** Empaquetar la aplicación y comprobar que se comporta igual dentro de Docker que en local. Es la única fase donde se usa Docker.

**Prerrequisito:** Fases 0 a 9 completas, con sus comprobantes cumplidos y la referencia local registrada en la Bitácora.

**Tareas**
- [ ] Revisar, actualizar o crear un `Dockerfile` para el backend y otro para el frontend (preferiblemente multi-stage, con imágenes base fijadas a versión y usuario sin privilegios).
- [ ] Crear o actualizar `docker-compose.yml` con todos los servicios necesarios: backend, frontend, base de datos y cualquier worker, cola o caché que el proyecto use (identificados en la Fase 0).
- [ ] **Volúmenes persistentes** para: imágenes subidas y miniaturas, archivos de modelos (`.pt`, `.onnx`), resultados/exportaciones y datos de la base de datos. Nada de esto debe perderse al reiniciar los contenedores.
- [ ] Variables de entorno mediante `.env` y un `.env.example` documentado. **Ninguna clave, token ni secreto queda dentro de las imágenes ni versionado en el repositorio.**
- [ ] `healthcheck` por servicio y `depends_on` con condición de salud, de modo que el backend espere a la base de datos y las migraciones se ejecuten de forma controlada al arrancar.
- [ ] Crear `.dockerignore` para backend y frontend (excluir dependencias locales, caché, archivos de modelos y datos).
- [ ] Si algún modelo requiere GPU, documentar la configuración necesaria; si no es posible validarla en el entorno disponible, dejar el servicio funcionando en CPU y registrar la limitación.
- [ ] Verificar que el Model Registry funciona dentro de contenedores: la subida de archivos, la carga de modelos y las llamadas salientes a APIs externas (red y variables de entorno correctas).
- [ ] Documentar en el README cómo levantar, detener y reconstruir el entorno con Docker Compose.

**Pruebas en Docker (todas deben ejecutarse aquí por primera vez)**
- [ ] Construcción limpia desde cero: `docker compose build --no-cache` y `docker compose up` sin errores.
- [ ] Todos los servicios quedan en estado saludable.
- [ ] Repetir en contenedores el recorrido completo: crear proyecto → Upload → Analysis → Character → Mask → Approve → Colorize → Export.
- [ ] Repetir la prueba del Model Registry: agregar un `.pt`, un `.onnx` y un modelo por API; activar y desactivar; usarlos en una colorización.
- [ ] Prueba de persistencia: `docker compose down` y luego `up`; los proyectos, portadas, modelos registrados, estados de activación y resultados siguen ahí.
- [ ] Revisar los logs de todos los servicios: sin errores inesperados y sin secretos ni claves de API expuestos.
- [ ] Ejecutar la batería de tests del proyecto dentro de los contenedores (o el subconjunto que aplique) y comparar los resultados con la referencia local.

**Reglas de esta fase**
- Si algo falla en Docker pero pasaba en local, corregir primero la configuración de contenedores (rutas, volúmenes, variables, red, permisos, dependencias del sistema). Modificar la lógica de la aplicación solo si se demuestra una diferencia real de entorno, y registrarlo en la Bitácora.
- Cualquier cambio de código hecho durante esta fase obliga a volver a pasar los tests locales antes de dar la fase por cerrada.

**Comprobante de fase 10**
- [ ] `docker compose up` desde un clon limpio del repositorio, siguiendo solo el README, deja la aplicación funcionando.
- [ ] El flujo completo y el Model Registry funcionan en Docker con los mismos resultados que en local.
- [ ] La persistencia sobrevive a `down`/`up`.
- [ ] No hay secretos en imágenes, repositorio ni logs.
- [ ] Evidencia (comandos, salidas y capturas) registrada en la Bitácora.

---

## 4. Objetivo final (condición obligatoria para marcar la tarea como completada)

La tarea **solo** se considera completada si se cumplen **todos** estos puntos, con evidencia en la Bitácora:

1. El sidebar muestra únicamente Dashboard, Projects, Results & Exports, Colorization Jobs, Model Registry y Settings en Workspace, más System; no existe sección Pipeline.
2. No existe barra de pasos fuera de un proyecto; dentro del proyecto el stepper muestra Upload, Analysis, Character, Mask, Approve, Colorize y Export.
3. "Star Colorizing" lleva a Projects; no quedan "Discover Sumi", "Convention" ni el toggle de empty state.
4. El Dashboard muestra el avance real (métricas y proyectos recientes) y no una descripción del producto.
5. Projects muestra una tarjeta por proyecto con la **imagen subida como portada**, su etapa y su estado.
6. Abrir cualquier proyecto lo lleva a su **etapa actual**, e indica claramente en qué etapa está.
7. Upload tiene estilos, inicia arriba, acota la vista previa, muestra mensajes de progreso/éxito/error y **no se puede volver a ella** tras completarla; el retroceso entre las demás etapas sí funciona.
8. El backend valida transiciones, guarda etapa/estado y sirve portada y métricas; sus tests pasan.
9. El recorrido completo Upload → Export funciona de punta a punta con un proyecto nuevo.
10. El Model Registry permite agregar modelos `.pt`, `.onnx` y por API desde la interfaz, quedan activos al guardarse, se pueden activar/desactivar, y el pipeline solo usa los activos. La arquitectura admite nuevos formatos/proveedores mediante adaptadores, y las claves de API nunca se exponen.
11. Todas las pruebas de las Fases 0 a 9 se ejecutaron en local y pasaron; Docker no se usó antes de la Fase 10.
12. `docker compose up` levanta la aplicación completa desde un clon limpio, y el flujo Upload → Export, el Model Registry y la persistencia de datos funcionan dentro de contenedores igual que en local, sin secretos expuestos.
13. El defecto 0.9 está corregido: aprobar y colorizar usan el `analysis_id` (no el `page_id`), funcionan tras recargar la página o repetir el análisis, tienen test de regresión y el flujo completo no produce ningún 404 por identificador incorrecto, ni en local ni en Docker.
14. Todos los comprobantes de fase (0 a 10) están cumplidos y registrados.

---

## 5. Bitácora (el agente completa esta sección)

| Fase | Fecha | Resumen de lo hecho | Evidencia (tests, capturas, comandos) | Pendientes / suposiciones |
|------|-------|---------------------|----------------------------------------|---------------------------|
| 0 | 2026-11-17 | Diagnostico completo: stack backend FastAPI 0.163, SQLAlchemy 2.1.9, PostgreSQL/asyncpg, Celery + Redis, Pydantic, Python 3.11; frontend React 19.3, react-router-dom 7, Vite 8, vitest 5, TypeScript 7; rutas frontend y endpoints backend mapeados; modelo de proyecto sin current_stage/status/cover_image y Analysis.page_id con UNIQUE; elementos a eliminar identificados: seccion Page Pipeline del sidebar, paso global de pasos, boton Toggle Empty State, enlace Discover SUMI en Home; bloque Convention no presente como codigo. Rama feature/plan-de-trabajo-fases creada (commit 2813844). Se corrigió backend/alembic/alembic.ini (script_location /app/backend/alembic -> alembic) para correr localmente. Postgres y Redis levantados con Docker (manga-postgres en localhost:5433, manga-redis/medicion_redis en localhost:6379) SOLO como infraestructura para pruebas locales; la app (API+frontend) se levanta local, sin docker compose. Linea base con BD real: backend importa y registra routers OK; backend pytest: 142 passed, 2 failed (ambas preexistentes: test_analyze_use_case usa StubPageRepository sin metodo get; test_validators asume Pillow no instalado aunque lo está). Frontend npm run typecheck falla con errores previos (exit 1); npm test 5 fallan / 4 pasan. Modelos: adaptadores mock en analisis, adaptadores reales y worker Celery para colorizacion; Model Registry tiene casos de uso pero sin rutas HTTP. | git checkout -b feature/plan-de-trabajo-fases; backend/alembic edit; pytest -q (142 passed / 2 failed preexistentes); npm run typecheck (exit 1); npm test (5 fallan / 4 pasan). | Postgres/Redis solo via Docker para tests locales (Fases 0-9); docker compose completo solo en Fase 10. |
| 1 | 2026-11-17 | Backend listo para el nuevo flujo de proyecto. Modelo Project con current_stage, status, stage_progress, cover_image (migración 0003_project_stages + backfill de datos existentes). Endpoints: GET/POST/DELETE /api/v1/projects (listado paginado con filtro por estado y etapa; detalle con page_id y analysis_id vigente por página), PATCH /api/v1/projects/{id}/stage (transición con validaciones: no volver a upload, retroceso desde analysis, avance automático, status=completado al terminar), POST /api/v1/pages (subida con validación de tipo/tamaño, miniatura como portada), GET /api/v1/metrics (métricas del dashboard). Model Registry: ORM ModelManifest + repositorio concreto, capa de adaptadores (ModelAdapterProtocol + registro formato→clase: .pt con torch.load weights_only=True, .onnx, API externa) y 7 endpoints HTTP bajo /api/v1/models (listado, detalle, registro local_file/api con test-connection previo, activar/desactivar con protección S19 409 si hay jobs en ejecución, editar, eliminar). Claves de API cifradas con Fernet (ENCRYPTION_KEY), nunca expuestas al frontend (solo enmascadas). Contratos documentados en docs/contratos/api-endpoints.md e identifiers.md (regla page_id vs analysis_id). Backend importa OK (app.main). Tests backend con PostgreSQL de Docker (localhost:5433): 142 passed, 2 failed (ambas preexistentes: test_analyze_use_case StubPageRepository sin get; test_validators asume Pillow no instalado aunque lo está). | git add/commit fbd9fb5 (T1-T8), 8b1b037 (T9-T10); pytest -q (142 passed / 2 preexistentes); import app.main OK. | Postgres/Redis solo via Docker para tests locales (Fases 0-9); docker compose completo solo en Fase 10. |
| 2 | 2026-11-17 | Layout global reescrito: sidebar Workspace con solo Dashboard, Projects, Results & Exports, Colorization Jobs, Model Registry y Settings; System sin cambios; eliminada sección Page Pipeline del sidebar; eliminada barra global de pasos (pipeline-bar); eliminada barra topbar con toggle empty state y badge Review Required; logo/brand cambiado a "Star Colorizing" enlazando a /projects; eliminado bloque "Discover Sumi" de Home.tsx; rutas del pipeline global (/upload, /analysis, /editor, /masks, /approve, /colorize, /history) removidas de App.tsx; enlace roto en Projects.tsx ("Open in Analysis Studio" → /upload) redirigido a /projects/:id. App.tsx solo declara rutas globales (/dashboard, /projects, /projects/:id, /results, /jobs, /models, /settings). Navbar.tsx (no montado) dejado sin tocar. Frontend: grep confirma cero referencias a Discover SUM / Toggle Empty / empty state; typecheck y vitest muestran los mismos errores/faltas preexistentes de la línea base (sin regresiones nuevas). | frontend/src/components/Layout.tsx reescrito; App.tsx reescrito; Home.tsx (quita Discover SUMI); Projects.tsx (arregla enlace roto); tsc y vitest sin nuevas fallas. | /projects/:id aún no redirige a la etapa actual (se implementa en Fase 5); Navbar.tsx huérfano con rutas antiguas no se renderiza. |
| 3 | 2026-11-17 | Dashboard reescrito con datos reales del endpoint GET /api/v1/metrics: total de proyectos, distribución por estado y etapa, jobs activos/completados/fallidos, y listado de proyectos recientes con portada (cover_image o fallback SVG), etapa y estado; cada tarjeta clicable abre /projects/:id. Encabezado breve (título + descripción corta sin protagonismo). Botón "Nuevo proyecto" crea y navega al proyecto. Estados de carga ("Cargando panel…"), vacío ("Sin proyectos aún" con botón crear) y error ("Error: …"). Eliminado bloque Convention/Discover Sumi (ya ausente). api/client.ts: listProjects tipado con nuevos campos (portada, current_stage, status, progreso) y nuevo método getMetrics(). Frontend: typecheck sin errores nuevos (Dashboard ya no aparece); vitest 5 fallan / 4 pasan = línea base (sin regresiones). | frontend/src/pages/Dashboard.tsx reescrito; frontend/src/api/client.ts (listProjects + getMetrics). tsc y vitest sin nuevas fallas. | Clic abre /projects/:id pero la redirección a etapa actual se implementa en Fase 5. |
| 4 | 2026-11-17 | Projects (listado) reescrito: tarjeta por proyecto con portada real (cover_image del backend o fallback SVG), nombre, etapa actual, estado con badge visual, progreso y última actualización; filtros por estado y etapa, búsqueda por nombre, ordenamiento por fecha (backend desc por created_at); botón "Nuevo proyecto" crea y navega al proyecto; clic en tarjeta navega a /projects/:id (redirección a etapa actual en Fase 5); estados de carga, vacío y error. Frontend: typecheck sin errores nuevos (Projects limpio); vitest 5 fallan / 4 pasan = línea base. | frontend/src/pages/Projects.tsx reescrito. tsc y vitest sin nuevas fallas. | Redirección a etapa actual y prueba con proyectos reales en BD (Analysis/Mask) en Fase 5. |
| 5 | 2026-11-17 | Contenedor de proyecto y stepper interno: rutas /projects/:id (redirige a etapa actual vía ProjectIndex) y /projects/:id/:stage (ProjectLayout con guarda de ruta, encabezado del proyecto con portada/estado/etapa actual, stepper de 7 etapas con completadas/actual/pendientes, retroceso desde analysis en adelante, upload no retornable, etapas futuras bloqueadas). StagePlaceholder por etapa (Fase 7 las reemplaza). api/client.ts: getProject y transitionStage. App.tsx: rutas anidadas de proyecto. Frontend: typecheck sin errores nuevos; vitest 5 fallan / 4 pasan = línea base. | frontend/src/api/client.ts (getProject, transitionStage); frontend/src/components/ProjectLayout.tsx (nuevo); frontend/src/components/StagePlaceholder.tsx (nuevo); frontend/src/App.tsx (rutas /projects/:id, /projects/:id/:stage). | Prueba con proyectos reales en BD (etapa correcta, retroceso conserva datos) pendiente — Fase 7 con datos de la API. |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
