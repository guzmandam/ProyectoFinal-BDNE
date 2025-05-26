#!/usr/bin/env python3
"""
Script de demostración para el sistema PostgreSQL
Muestra cómo usar las consultas y comparar con BigQuery
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar los módulos
sys.path.append(str(Path(__file__).parent))

from postgres_dashboard_queries import PostgreSQLDashboard
from view_postgres_stats import view_postgres_stats, compare_with_bigquery

def demo_postgres_dashboard():
    """Demostración completa del sistema PostgreSQL."""
    
    print("🎯 DEMOSTRACIÓN DEL SISTEMA POSTGRESQL")
    print("=" * 60)
    
    # Configuración de ejemplo (modifica según tu entorno)
    connection_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'commerce'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    }
    
    print("📋 CONFIGURACIÓN:")
    print(f"   Host: {connection_params['host']}")
    print(f"   Puerto: {connection_params['port']}")
    print(f"   Base de datos: {connection_params['database']}")
    print(f"   Usuario: {connection_params['user']}")
    print("=" * 60)
    
    try:
        # Paso 1: Ejecutar consultas del dashboard
        print("\n🚀 PASO 1: EJECUTANDO CONSULTAS DEL DASHBOARD")
        print("-" * 50)
        
        dashboard = PostgreSQLDashboard(connection_params)
        resultados = dashboard.ejecutar_todas_consultas()
        
        # Paso 2: Mostrar estadísticas
        print("\n📊 PASO 2: ANÁLISIS DE ESTADÍSTICAS")
        print("-" * 50)
        
        dashboard.mostrar_estadisticas()
        
        # Paso 3: Mostrar resultados detallados
        print("\n📋 PASO 3: RESULTADOS DETALLADOS")
        print("-" * 50)
        
        for nombre, df in resultados.items():
            if not df.empty:
                print(f"\n🔍 {nombre.upper()}:")
                print(f"   Filas: {len(df)}")
                print(f"   Columnas: {list(df.columns)}")
                
                # Mostrar primeras filas para algunas consultas
                if nombre in ['resumen_ejecutivo', 'productos_principales']:
                    print("   Primeras filas:")
                    for i, (_, row) in enumerate(df.head(3).iterrows()):
                        print(f"     {i+1}. {dict(row)}")
        
        # Paso 4: Estadísticas avanzadas
        print("\n📈 PASO 4: ESTADÍSTICAS AVANZADAS")
        print("-" * 50)
        
        view_postgres_stats()
        
        # Paso 5: Comparación con BigQuery (si existe)
        print("\n⚖️  PASO 5: COMPARACIÓN CON BIGQUERY")
        print("-" * 50)
        
        bigquery_csv = Path("./bigquery_queries_log.csv")
        if bigquery_csv.exists():
            print("✅ Archivo BigQuery encontrado, comparando...")
            compare_with_bigquery()
        else:
            print("ℹ️  No se encontró archivo BigQuery para comparar")
            print("   Ejecuta el dashboard Reflex primero para generar datos BigQuery")
        
        # Paso 6: Recomendaciones
        print("\n💡 PASO 6: RECOMENDACIONES")
        print("-" * 50)
        
        print("✅ Sistema PostgreSQL configurado correctamente")
        print("📁 Archivos generados:")
        print("   - postgresql_queries_log.csv (log de consultas)")
        
        if Path("postgres_query_summary.txt").exists():
            print("   - postgres_query_summary.txt (resumen exportado)")
        
        print("\n🔧 Próximos pasos:")
        print("1. Revisar los logs CSV para análisis detallado")
        print("2. Optimizar consultas lentas si es necesario")
        print("3. Configurar monitoreo automático")
        print("4. Comparar rendimiento con BigQuery")
        
        print("\n🎉 ¡Demostración completada exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en la demostración: {e}")
        print("\n🔧 Soluciones posibles:")
        print("1. Verificar que PostgreSQL esté ejecutándose")
        print("2. Confirmar parámetros de conexión")
        print("3. Asegurar que la base de datos 'commerce' exista")
        print("4. Verificar que las tablas estén creadas con datos")
        print("5. Instalar dependencias: pip install psycopg2-binary pandas")

def quick_test():
    """Prueba rápida de conectividad."""
    
    print("🔍 PRUEBA RÁPIDA DE CONECTIVIDAD")
    print("=" * 40)
    
    connection_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'commerce'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    }
    
    try:
        dashboard = PostgreSQLDashboard(connection_params)
        
        # Probar solo una consulta simple
        print("🔍 Probando consulta de resumen ejecutivo...")
        resultado = dashboard.resumen_ejecutivo()
        
        if not resultado.empty:
            print("✅ Conexión exitosa!")
            print(f"📊 Datos obtenidos: {len(resultado)} filas")
            print(f"📁 Log guardado en: {dashboard.tracker.csv_file}")
        else:
            print("⚠️  Conexión exitosa pero sin datos")
            
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        demo_postgres_dashboard() 