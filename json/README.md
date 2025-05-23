# Generador JSON Commerce-Minorista

Un script de Python que crea **únicamente** los artefactos de Document-DB para la demostración Commerce-Minorista, utilizando la misma semilla aleatoria determinística que el generador SQL.

## Descripción General

Esta herramienta genera documentos JSON estructurados para bases de datos orientadas a documentos (como MongoDB, CouchDB, etc.), creando dos colecciones principales con datos sintéticos realistas.

## Archivos Generados

El script genera los siguientes archivos en el directorio de trabajo:

| Archivo | Descripción |
|---------|-------------|
| `stores_catalog.json` | Colección de catálogo (tiendas, empleados, inventario) |
| `sales_docs.json` | Colección de ventas (encabezado de ventas + líneas embebidas) |

## Volúmenes de Datos Generados

Los siguientes volúmenes de datos se generan por defecto (configurables mediante constantes al inicio del archivo):

| Entidad | Cantidad | Notas |
|---------|----------|-------|
| Categorías | 10 | Categorías de productos |
| Productos | 100 | Artículos en venta |
| Tiendas | 5 | Ubicaciones físicas de tiendas |
| Empleados | 25 | Aproximadamente 5 por tienda |
| Clientes | 1000 | Base de datos de clientes |
| Ventas | 20000 | Transacciones de venta (~60k líneas de venta) |

## Estructura de Documentos

### Catálogo de Tiendas (`stores_catalog.json`)

Cada documento de tienda contiene:
- **Información de la tienda**: nombre y dirección
- **Empleados embebidos**: lista de empleados asignados a la tienda
- **Inventario embebido**: productos disponibles con cantidades y detalles del producto

```json
{
  "store_name": "Nombre de la Tienda",
  "address": "Dirección completa",
  "employees": [
    {
      "first_name": "Juan",
      "last_name": "Pérez",
      "position": "Cajero"
    }
  ],
  "inventory": [
    {
      "product": {
        "name": "Producto Ejemplo",
        "category": "Categoría",
        "price": 99.99
      },
      "quantity": 50
    }
  ]
}
```

### Documentos de Ventas (`sales_docs.json`)

Cada documento de venta contiene:
- **Información temporal**: timestamp de la transacción
- **Datos de la tienda**: información embebida de la tienda
- **Empleado**: datos del empleado que procesó la venta
- **Cliente**: información del cliente
- **Líneas de venta embebidas**: productos vendidos con cantidades y totales
- **Monto total**: total de la transacción

```json
{
  "timestamp": {
    "$date": "2024-03-15T14:30:25.000Z"
  },
  "store": {
    "name": "Tienda Central"
  },
  "employee": {
    "first_name": "María",
    "last_name": "González"
  },
  "customer": {
    "first_name": "Carlos",
    "last_name": "Rodríguez",
    "email": "carlos@email.com"
  },
  "lines": [
    {
      "product": {
        "name": "Producto A",
        "category": "Electrónicos",
        "price": 299.99
      },
      "quantity": 2,
      "line_total": 599.98
    }
  ],
  "total_amount": 599.98
}
```

## Uso

### Prerrequisitos

Instala los paquetes de Python requeridos:

```bash
pip install faker numpy jsonschema
```

### Ejecutar el Generador

```bash
python generator.py
```

Después de ejecutar, tendrás los archivos JSON en el mismo directorio, listos para importar en tu base de datos orientada a documentos.

## ¿Los documentos cumplen con el criterio JSON anidado >= 3 niveles?

Sí, los documentos cumplen plenamente con el criterio de “JSON anidado (≥ 3 niveles) sin PK/FK”.

| Colección                 | Ejemplo de jerarquía                                                                    | Niveles | Comentario                                                                                                                                                                               |
| ------------------------- | --------------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`stores_catalog.json`** | `Store` → `inventory[]` → `product{…}` *(dentro de cada producto aparece la categoría)* | **3**+  | El nodo raíz es la tienda; cada elemento de `inventory` contiene un objeto `product` embebido. Además hay un arreglo `employees`, pero no cuenta como nivel adicional obligatorio.       |
| **`sales_docs.json`**     | `Sale` → `lines[]` → `product{…}` *(con categoría incluida)*                            | **3**+  | Nodo raíz = venta. Cada venta tiene un arreglo `lines`; cada línea anida un objeto `product`. También se incrustan objetos `store`, `employee` y `customer`, aportando contexto sin FKs. |


No aparecen IDs de producto, cliente, etc.; solo descriptores legibles.

Con el parche de "$date" el campo timestamp ya se inserta como Date real en MongoDB, sin afectar la estructura.

Por tanto, la especificación de “≥ 3 niveles, todo embebido, cero claves foráneas” está cumplida para ambos JSON. 


## Configuración

Puedes modificar los volúmenes de datos editando las constantes al inicio de `generator.py`:

```python
CATEGORIES = 10
PRODUCTS   = 100
STORES     = 5
EMPLOYEES  = 25
CUSTOMERS  = 1000
SALES      = 20000
MIN_LINES  = 1
MAX_LINES  = 10
```

## Características Especiales

### Datos Realistas
- **Configuración regional española/mexicana** para nombres y direcciones
- **Nombres de productos realistas** generados con Faker
- **Distribución Zipf** para frecuencia de compras de clientes (más realista que distribución uniforme)
- **Rangos de fechas configurables** para transacciones

### Estructura Optimizada para Document-DB
- **Datos embebidos** para reducir la necesidad de joins
- **Desnormalización intencional** para mejorar el rendimiento de consultas
- **Formato UTF-8** con caracteres especiales preservados

### Validación
- **Verificación de integridad** de datos generados

## Compatibilidad

Los archivos JSON generados son compatibles con:
- **MongoDB** - Importación directa con `mongoimport`
- **CouchDB** - Documentos listos para inserción
- **Amazon DocumentDB** - Compatible con formato MongoDB
- **Azure Cosmos DB** - API de MongoDB
- **Cualquier base de datos orientada a documentos** que soporte JSON

## Diferencias con el Generador SQL

A diferencia del generador SQL que crea tablas relacionales normalizadas, este generador:
- Crea documentos **desnormalizados** con datos embebidos
- Optimiza para **consultas de lectura** típicas en bases de datos de documentos
- Utiliza la **misma semilla aleatoria** para consistencia entre ambos generadores 