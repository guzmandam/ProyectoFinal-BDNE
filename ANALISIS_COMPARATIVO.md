# 📊 Informe Analítico: Comparativa de Rendimiento SQL, NoSQL y Grafos

## 1. Introducción

Este informe presenta un análisis comparativo del rendimiento de diversas tecnologías de bases de datos —PostgreSQL (como representante SQL), MongoDB (NoSQL Documental), BigQuery (Data Warehouse en la nube) y Neo4j (Base de Datos de Grafos)— en diferentes escenarios de un dominio de comercio minorista. El objetivo es evaluar la eficiencia de cada sistema en tareas clave como la ingesta masiva de datos y la ejecución de consultas analíticas y de grafos complejas.

Los datos y métricas presentados se basan en los benchmarks realizados a lo largo de este proyecto, cuyos resultados se encuentran en los archivos `ingest_times.csv`, `bigquery_queries_log.csv`, `postgresql_queries_log.csv` y `graph_times.csv`.

## 2. Análisis de Ingesta de Datos

La ingesta de datos es un proceso crítico para cualquier sistema. En esta sección, comparamos los tiempos de carga para un dataset de ~20,000 ventas y un catálogo de tiendas.

**Resultados de Ingesta (`ingest_times.csv`):**

| Paso de Ingesta        | Tecnología      | Duración (segundos) |
| ---------------------- | --------------- | ------------------- |
| SQL Puro               | PostgreSQL      | 2.945               |
| JSON a Relacional      | PostgreSQL      | 123.088             |
| Catálogo (Documentos)  | MongoDB         | 0.067               |
| Ventas (Documentos)    | MongoDB         | 1.194               |

**Total MongoDB (Catálogo + Ventas): 0.067 + 1.194 = 1.261 segundos**

### 2.1. Discusión de Resultados de Ingesta

*   **PostgreSQL (SQL Puro):**
    *   **Rendimiento:** 2.945 segundos. Este método, utilizando `INSERT` en un bucle, metodo tradicional de ingesta de datos.
    *   **Pros:** Muy rápido para datos estructurados y limpios, atomicidad garantizada por transacciones SQL.
    *   **Contras:** Requiere una transformación previa de los datos al formato tabular esperado. Menos flexible si la estructura de los datos de origen es variable.

*   **PostgreSQL (JSON a Relacional):**
    *   **Rendimiento:** 123.088 segundos. Este es, con diferencia, el método más lento. El proceso implica leer documentos JSON, parsearlos, transformar la estructura anidada en múltiples tablas relacionales (manejando IDs y relaciones), y luego realizar inserciones o cargas `COPY`.
    *   **Pros:** Permite ingestar datos JSON directamente y adaptarlos a un esquema relacional existente.
    *   **Contras:** El overhead de parseo y transformación JSON en Python antes de la carga es significativo. Las inserciones individuales o incluso `COPY` por tabla pueden ser menos eficientes que una carga masiva única. La complejidad del script de transformación también es un factor.

*   **MongoDB (Documentos Nativos):**
    *   **Rendimiento:** Catálogo en 0.067s y Ventas en 1.194s, sumando un total de 1.261 segundos. MongoDB brilla en la ingesta de documentos JSON nativos.
    *   **Pros:** Extremadamente rápido para datos que ya están en formato JSON o similar. No requiere transformación de esquema (schema-on-read o esquema flexible). `insert_many` es muy eficiente para cargas por lotes.
    *   **Contras:** Si se necesitan garantías transaccionales complejas a través de múltiples "colecciones" (equivalentes a tablas), puede ser más complicado de manejar que en SQL tradicional, aunque MongoDB ha mejorado mucho en este aspecto.

### 2.2. Conclusiones de Ingesta

*   **MongoDB es el ganador claro para la ingesta de datos en formato de documento (JSON)**, ofreciendo una velocidad y flexibilidad superiores cuando los datos se ajustan naturalmente a este modelo.
*   **PostgreSQL con SQL puro y `COPY` es muy eficiente si los datos ya están transformados y listos para un esquema relacional.** Es una opción robusta para ETLs tradicionales.
*   **Transformar JSON a un esquema relacional complejo en tiempo de ingesta con Python y luego cargar en PostgreSQL es el enfoque menos performante.** Si este es un requisito frecuente, se deberían considerar herramientas ETL optimizadas o realizar la transformación en una etapa previa más eficiente.

## 3. Análisis de Consultas Analíticas (OLAP)

Se comparó el rendimiento de PostgreSQL y BigQuery para un conjunto de 7 consultas analíticas típicas de un dashboard de comercio.

**Metodología:**
*   Para **PostgreSQL**, se registraron los tiempos de ejecución de consultas SQL contra una base de datos local (`commerce`) poblada con los datos del proyecto.
*   Para **BigQuery**, se consultó un dataset equivalente (`commerce_doc`) utilizando su motor SQL. Se consideraron tanto el tiempo de ejecución como los bytes procesados, un factor clave en el costo de BigQuery.

**Datos de `postgresql_queries_log.csv` (Promedios de varias ejecuciones):**

| Query Name (PostgreSQL) | Avg. Execution Time (s) |
| ----------------------- | ------------------------- |
| resumen_ejecutivo       | 0.263                     |
| ingresos_diarios        | 0.004                     |
| productos_principales   | 0.076                     |
| ventas_por_tienda       | 0.013                     |
| ingresos_por_categoria  | 0.060                     |
| empleados_principales   | 0.034                     |
| rendimiento_tiendas     | 0.021                     |
| **Promedio General (PostgreSQL)** | **~0.067 s**              |

**Datos de `bigquery_queries_log.csv` (Promedios de varias ejecuciones, excluyendo outliers y errores):**
*Nota: El cálculo exacto de promedios requiere agrupar por tipo de consulta y filtrar. Aquí se presentará una estimación basada en los datos adjuntos.*

Analizando `bigquery_queries_log.csv`:
- `resumen_ejecutivo`: Tiempos varían (e.g., 3.4s, 19.3s, 3.1s, 2.2s, 4.1s, 7.7s, 1.8s, 14.1s, 1.5s, 1.8s). Un promedio podría estar alrededor de **~5-7s**. Bytes procesados: 1.63 MB.
- `ingresos_diarios`: Tiempos más consistentes (e.g., 1.46s, 1.34s, 1.09s, 1.23s, 1.21s, 1.5s, 1.09s, 1.37s, 0.97s, 1.23s, 1.03s, 1.45s). Promedio: **~1.2s**. Bytes procesados: 740 KB.
- `productos_principales`: Tiempos consistentes (e.g., 0.79s, 1.04s, 0.89s, 0.75s, 0.81s, 1.13s, 1.15s, 0.77s). Promedio: **~0.9s**. Bytes procesados: 0 bytes (probablemente por caché o tipo de consulta).

| Query Type (BigQuery)        | Avg. Execution Time (s) (Estimado) | Avg. Bytes Processed (Estimado) |
| ---------------------------- | ------------------------------------ | ------------------------------- |
| Resumen Ejecutivo            | 5.5                                  | 1.63 MB                         |
| Ingresos Diarios             | 1.2                                  | 0.74 MB                         |
| Productos Principales        | 0.9                                  | ~0 MB (posiblemente optimizado) |
| **Promedio General (BigQuery)** | **~2.5 s (sin ponderar por frecuencia)** |                                 |

### 3.1. Discusión de Resultados OLAP

*   **PostgreSQL:**
    *   **Rendimiento:** Consistentemente muy rápido para todas las consultas analíticas, con tiempos promedio inferiores a 0.1 segundos para la mayoría. El promedio general es de aproximadamente 0.067 segundos. Esto se debe a que el dataset, aunque considerable para una demostración (~20k ventas), es manejable para un RDBMS bien indexado y optimizado como PostgreSQL corriendo localmente o en una infraestructura adecuada.
    *   **Pros:** Excelente rendimiento para datasets de tamaño pequeño a mediano, bajo costo (si es auto-gestionado), madurez y robustez del motor SQL, ricas funcionalidades analíticas SQL.
    *   **Contras:** La escalabilidad para datasets masivos (Terabytes/Petabytes) requeriría soluciones de clusterización (ej. Citus) o arquitecturas distribuidas, lo cual incrementa la complejidad de gestión. El rendimiento puede degradarse si los índices no son óptimos o si el hardware es limitado.

*   **BigQuery:**
    *   **Rendimiento:** Los tiempos de ejecución son notablemente más altos que PostgreSQL para este tamaño de dataset (ej. ~1-7 segundos vs <0.1 segundos). Sin embargo, BigQuery está diseñado para escanear y procesar Terabytes o Petabytes de datos de manera eficiente. Su arquitectura masivamente paralela (MPP) introduce una cierta latencia base, pero escala de manera casi lineal con volúmenes de datos mucho mayores.
    *   **Bytes Procesados:** Es una métrica crucial. BigQuery factura por los datos escaneados. Aunque para este dataset los volúmenes son pequeños (KB/MB), en escenarios reales esto puede ser significativo. Las optimizaciones como el particionamiento y clustering son vitales para controlar costos.
    *   **Pros:** Escalabilidad masiva para análisis de Big Data, modelo serverless (sin gestión de infraestructura), SQL estándar potente, integración con el ecosistema Google Cloud. Bueno para consultas ad-hoc sobre grandes volúmenes.
    *   **Contras:** Costo variable basado en datos procesados y almacenamiento. Puede tener mayor latencia para consultas sobre datasets pequeños en comparación con sistemas OLTP/OLAP tradicionales optimizados para ello. Requiere optimización de consultas y esquemas para controlar costos.

### 3.2. Conclusiones OLAP

*   Para el **tamaño de dataset actual y el tipo de consultas realizadas, PostgreSQL es significativamente más rápido y costo-efectivo.**
*   **BigQuery muestra su verdadero potencial con datasets mucho más grandes**, donde su capacidad de paralelización masiva supera las limitaciones de un RDBMS tradicional. Su modelo de precios y la latencia observada en datasets pequeños lo hacen menos ideal si la mayoría de las consultas son sobre volúmenes de datos modestos y se requiere baja latencia.
*   La elección depende del **volumen de datos, la necesidad de escalabilidad, el presupuesto y la infraestructura existente.** Para dashboards departamentales o analíticas sobre GBs de datos, PostgreSQL puede ser suficiente. Para data lakes empresariales con TBs/PBs, BigQuery es una opción mucho más adecuada.

## 4. Análisis de Consultas de Grafos

Se comparó el rendimiento de Neo4j (una base de datos de grafos nativa) y PostgreSQL (usando JOINs para simular traversals de grafos) para consultas que exploran relaciones.

**Resultados de Benchmarks de Grafos (`graph_times.csv`):**

| Consulta                           | Tecnología | Duración (segundos) |
| ---------------------------------- | ---------- | ------------------- |
| SQL Query (Path Complejo)          | PostgreSQL | 0.070               |
| Cypher Full Path (Equivalente SQL) | Neo4j      | 0.035               |
| Cypher Customer-to-Product         | Neo4j      | 0.149               |
| Cypher Customer Sales Simple       | Neo4j      | 0.290               |

### 4.1. Discusión de Resultados de Grafos

*   **Consulta de Path Complejo (PostgreSQL vs. Neo4j):**
    *   **PostgreSQL (SQL con JOINs):** 0.070 segundos. Realiza la tarea uniendo múltiples tablas (Customer, Sale, SaleLine, Product, Category). Para este nivel de complejidad y tamaño de datos, el optimizador de PostgreSQL es eficiente.
    *   **Neo4j (Cypher Full Path):** 0.035 segundos. Neo4j es **aproximadamente 2 veces más rápido** para esta consulta. Esto demuestra la eficiencia del traversal nativo de grafos ("index-free adjacency"), donde las relaciones son punteros directos, evitando la sobrecarga de múltiples JOINs y búsquedas en índices.
    *   **Observación:** A medida que la profundidad y complejidad del path aumentan, la ventaja de Neo4j tiende a crecer exponencialmente.

*   **Consultas Específicas de Neo4j:**
    *   **Customer-to-Product (Diversidad de Productos):** 0.149 segundos. Esta consulta (encontrar clientes por el número de productos *únicos* comprados) es más lenta que el "full path" simple en Neo4j y también más lenta que la consulta SQL compleja en PostgreSQL. El `COUNT(DISTINCT p)` puede añadir sobrecarga.
    *   **Customer Sales Simple (Resumen de Ventas):** 0.290 segundos. Esta es la consulta más lenta en Neo4j de las probadas. Aunque solo implica `(Customer)-[:PLACED]->(Sale)`, la agregación `SUM(s.total)` y `COUNT(s)` sobre un número potencialmente grande de ventas por cliente puede ser menos optimizada en Neo4j para este tipo de agregación simple en comparación con cómo un RDBMS manejaría sumas y conteos sobre columnas indexadas.
    *   **Importante:** El rendimiento de estas consultas en Neo4j también depende de la modelización del grafo y los índices aplicados (aunque Neo4j se beneficia de la adyacencia libre de índice, los índices en propiedades de nodos siguen siendo importantes para encontrar los puntos de inicio del traversal).

### 4.2. Conclusiones de Grafos

*   **Neo4j sobresale en consultas que implican traversals de múltiples saltos (multi-hop) a través de relaciones complejas.** Su capacidad para navegar estas relaciones de manera nativa es una ventaja significativa sobre las bases de datos relacionales que deben recurrir a costosos JOINs. Para la consulta de "path completo", Neo4j fue claramente superior.
*   **PostgreSQL puede ser sorprendentemente competitivo para consultas de grafos de complejidad moderada en datasets no masivos**, especialmente si las tablas están bien indexadas y las uniones no son excesivamente profundas.
*   **Para algunas consultas agregativas simples, incluso si involucran relaciones, PostgreSQL puede superar a Neo4j.** Las bases de datos relacionales están altamente optimizadas para operaciones de agregación sobre conjuntos de datos. Neo4j está más optimizado para la navegación de patrones y la conectividad.
*   **La elección de la tecnología de grafos depende del caso de uso principal:**
    *   **Neo4j es ideal para:** Sistemas de recomendación, detección de fraude, análisis de redes sociales, gestión de identidades y accesos, donde la exploración de relaciones y patrones complejos es fundamental.
    *   **PostgreSQL puede ser suficiente si:** Las consultas de grafos son secundarias, no muy complejas, o el volumen de datos relacionales es el principal impulsor y se prefiere mantener una única tecnología. Extensiones como Apache AGE pueden mejorar las capacidades de grafo en PostgreSQL.

## 5. Conclusiones Generales

Este proyecto ha demostrado que **no existe una "mejor" base de datos para todos los escenarios.** La elección óptima depende críticamente de:

1.  **Modelo de Datos:**
    *   **Relacional (PostgreSQL):** Ideal para datos bien estructurados con relaciones claras y necesidad de consistencia fuerte (ACID).
    *   **Documental (MongoDB):** Excelente para datos semi-estructurados, jerárquicos (JSON), donde la flexibilidad del esquema y la velocidad de desarrollo son clave.
    *   **Grafos (Neo4j):** Superior cuando las relaciones entre los datos son tan importantes como los datos mismos, y se necesitan consultas de conectividad y patrones.
    *   **Almacén de Datos Columnar (BigQuery):** Diseñado para analíticas sobre grandes volúmenes de datos, a menudo con esquemas de estrella o copo de nieve.

2.  **Carga de Trabajo (Workload):**
    *   **Ingesta Rápida de JSON:** MongoDB destaca.
    *   **Ingesta Masiva SQL Optimizada:** PostgreSQL es muy eficiente.
    *   **Consultas OLAP sobre Datos Masivos:** BigQuery es el líder.
    *   **Consultas OLAP sobre Datos Medianos/Pequeños (Baja Latencia):** PostgreSQL es muy performante.
    *   **Consultas de Traversal Profundo y Patrones de Grafo:** Neo4j es el especialista.

3.  **Escalabilidad y Costo:**
    *   **PostgreSQL y MongoDB (Auto-gestionados):** Costo inicial de hardware/VMs, pero control sobre los gastos operativos. La escalabilidad horizontal puede requerir esfuerzo adicional.
    *   **BigQuery:** Modelo serverless con pago por uso (almacenamiento y datos procesados). Alta escalabilidad, pero los costos pueden crecer si no se optimiza.
    *   **Neo4j:** Opciones open-source y comerciales. La escalabilidad en clústeres es una característica de las versiones enterprise.

4.  **Complejidad y Ecosistema:**
    *   **SQL (PostgreSQL, BigQuery):** Lenguaje maduro, ampliamente conocido, gran cantidad de herramientas y talento disponible.
    *   **MongoDB (NoSQL):** API y herramientas específicas, pero con una curva de aprendizaje manejable para desarrolladores familiarizados con JSON.
    *   **Neo4j (Cypher):** Lenguaje de consulta de grafos potente y declarativo, pero menos extendido que SQL. Requiere un cambio de paradigma en la modelización.

## 6. Recomendaciones Clave

*   **Para aplicaciones transaccionales estándar con datos estructurados:** **PostgreSQL** sigue siendo una opción robusta, confiable y performante.
    *   *Considerar si:* Necesitas integridad referencial fuerte, transacciones ACID complejas y un ecosistema SQL maduro.

*   **Para ingesta rápida de datos JSON, catálogos de productos, perfiles de usuario, o donde la flexibilidad del esquema es primordial:** **MongoDB** es una excelente elección.
    *   *Considerar si:* Tus datos son inherentemente jerárquicos, evolucionan rápidamente o necesitas un time-to-market rápido.

*   **Para análisis de Big Data, Business Intelligence sobre grandes volúmenes, o cuando necesitas un data warehouse serverless y escalable:** **BigQuery** (o equivalentes como Snowflake, Redshift) es la solución.
    *   *Considerar si:* Trabajas con terabytes/petabytes de datos, necesitas alta concurrencia para consultas analíticas y prefieres un modelo de pago por uso.

*   **Para casos de uso donde las relaciones, la conectividad y los patrones son centrales (motores de recomendación, redes sociales, detección de fraude):** **Neo4j** ofrece un rendimiento y expresividad superiores.
    *   *Considerar si:* Las consultas "quién conoce a quién", "camino más corto", "patrones de influencia" son frecuentes y críticas.

*   **Arquitecturas Híbridas (Polyglot Persistence):** En muchos sistemas complejos del mundo real, la mejor solución implica usar **múltiples bases de datos especializadas** para diferentes tareas. Por ejemplo, PostgreSQL para el sistema transaccional core, MongoDB para el catálogo de productos y logs, Neo4j para recomendaciones, y BigQuery para analíticas offline a gran escala.

*   **Benchmarking Continuo:** Los resultados de rendimiento pueden variar según la versión del software, la configuración del hardware, la estructura específica de los datos y las optimizaciones aplicadas. Es crucial realizar benchmarks en el propio entorno y con datos representativos antes de tomar decisiones finales de arquitectura.

---