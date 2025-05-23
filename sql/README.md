# Generador SQL Commerce-Minorista

Un script de Python que genera DDL (Lenguaje de Definición de Datos) e INSERTs de datos sintéticos para el esquema de base de datos Commerce-Minorista.

## Descripción General

Esta herramienta genera un archivo SQL completo llamado `commerce_load.sql` que contiene:
- **Declaraciones CREATE TABLE** con claves primarias, claves foráneas e índices básicos
- **Declaraciones INSERT por lotes** (≤1000 filas por declaración para rendimiento óptimo)

## Volúmenes de Datos Generados

Los siguientes volúmenes de datos se generan por defecto (configurables mediante constantes al inicio del archivo):

| Entidad | Cantidad | Notas |
|---------|----------|-------|
| Categorías | 10 | Categorías de productos |
| Productos | 100 | Artículos en venta |
| Tiendas | 5 | Ubicaciones físicas de tiendas |
| Empleados | 25 | Aproximadamente 5 por tienda |
| Clientes | 1000 | Base de datos de clientes |
| Ventas | 20000 | Transacciones de venta (~60000 líneas de venta) |

## Esquema de Base de Datos

El esquema generado incluye las siguientes tablas:

- **Category** - Categorías de productos
- **Product** - Artículos con precios y relaciones de categoría
- **Store** - Ubicaciones físicas de tiendas
- **Employee** - Miembros del personal asignados a tiendas
- **Customer** - Información de clientes
- **Inventory** - Niveles de stock de productos por tienda
- **Sale** - Transacciones de venta
- **SaleLine** - Artículos individuales dentro de cada venta

## Uso

### Prerrequisitos

Asegúrate de tener los paquetes de Python requeridos instalados:

```bash
pip install numpy faker
```

### Ejecutar el Generador

```bash
python generator.py
```

Después de ejecutar, tendrás `commerce_load.sql` en el mismo directorio, listo para alimentar a Progress SQL (o cualquier motor ANSI-SQL con ajustes menores).

## Configuración

Puedes modificar los volúmenes de datos editando las constantes al inicio de `generator.py`:

```python
CATEGORIES = 10
PRODUCTS = 100
STORES = 5
EMPLOYEES = 25
CUSTOMERS = 1000
SALES = 20000
```

## Salida

El archivo SQL generado contiene:
1. **Sección DDL** - Todas las declaraciones de creación de tablas con relaciones apropiadas
2. **Sección de Datos** - Declaraciones INSERT por lotes para todos los datos generados

El script utiliza datos sintéticos realistas generados con la librería Faker, incluyendo:
- Configuración regional española/mexicana para nombres y direcciones
- Nombres de productos y precios realistas
- Rangos de fechas apropiados para transacciones de venta
- Distribución Zipf para frecuencia de compras de clientes (más realista que distribución uniforme)

## Compatibilidad

El SQL generado es compatible con:
- Progress SQL
- La mayoría de bases de datos compatibles con ANSI-SQL (con ajustes menores si es necesario) 