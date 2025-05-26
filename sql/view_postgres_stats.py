#!/usr/bin/env python3
"""
Script para ver estadísticas de consultas PostgreSQL
Muestra información detallada del archivo CSV de tracking
"""

import pandas as pd
from pathlib import Path
import sys

def view_postgres_stats(csv_file: str = "postgresql_queries_log.csv"):
    """Ver estadísticas detalladas de las consultas PostgreSQL."""
    
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"❌ No se encontró el archivo {csv_file}")
        print("Ejecuta postgres_dashboard_queries.py primero para generar datos de consultas.")
        return
    
    try:
        df = pd.read_csv(csv_path)
        
        if df.empty:
            print("📊 El archivo de consultas está vacío")
            return
        
        print("\n" + "="*80)
        print("🐘 REPORTE DETALLADO DE CONSULTAS POSTGRESQL")
        print("="*80)
        
        # Estadísticas generales
        total_queries = len(df)
        successful = len(df[df['status'] == 'SUCCESS'])
        failed = len(df[df['status'] == 'ERROR'])
        
        print(f"\n📈 RESUMEN GENERAL:")
        print(f"   Total de consultas: {total_queries}")
        print(f"   Consultas exitosas: {successful} ({successful/total_queries*100:.1f}%)")
        print(f"   Consultas fallidas: {failed} ({failed/total_queries*100:.1f}%)")
        
        if successful > 0:
            success_df = df[df['status'] == 'SUCCESS']
            
            print(f"\n⏱️  TIEMPOS DE EJECUCIÓN:")
            print(f"   Tiempo promedio: {success_df['execution_time_seconds'].mean():.3f}s")
            print(f"   Tiempo mínimo: {success_df['execution_time_seconds'].min():.3f}s")
            print(f"   Tiempo máximo: {success_df['execution_time_seconds'].max():.3f}s")
            print(f"   Tiempo total: {success_df['execution_time_seconds'].sum():.3f}s")
            
            print(f"\n📊 DATOS PROCESADOS:")
            print(f"   Filas totales: {success_df['rows_returned'].sum():,}")
            print(f"   Promedio filas por consulta: {success_df['rows_returned'].mean():.1f}")
        
        # Consultas por tipo
        print(f"\n🔍 CONSULTAS POR TIPO:")
        query_types = df['query_name'].value_counts()
        for query_type, count in query_types.items():
            avg_time = df[df['query_name'] == query_type]['execution_time_seconds'].mean()
            avg_rows = df[df['query_name'] == query_type]['rows_returned'].mean()
            print(f"   {query_type}: {count} consultas (promedio: {avg_time:.3f}s, {avg_rows:.1f} filas)")
        
        # Consultas más lentas
        print(f"\n🐌 TOP 5 CONSULTAS MÁS LENTAS:")
        slowest = df[df['status'] == 'SUCCESS'].nlargest(5, 'execution_time_seconds')
        for _, row in slowest.iterrows():
            print(f"   {row['query_name']}: {row['execution_time_seconds']:.3f}s | {row['rows_returned']} filas | {row['timestamp'][:19]}")
        
        # Consultas más rápidas
        print(f"\n⚡ TOP 5 CONSULTAS MÁS RÁPIDAS:")
        fastest = df[df['status'] == 'SUCCESS'].nsmallest(5, 'execution_time_seconds')
        for _, row in fastest.iterrows():
            print(f"   {row['query_name']}: {row['execution_time_seconds']:.3f}s | {row['rows_returned']} filas | {row['timestamp'][:19]}")
        
        # Últimas consultas
        print(f"\n🕐 ÚLTIMAS 5 CONSULTAS:")
        recent = df.tail(5)[['timestamp', 'query_name', 'execution_time_seconds', 'rows_returned', 'status']]
        for _, row in recent.iterrows():
            status_icon = "✅" if row['status'] == 'SUCCESS' else "❌"
            print(f"   {status_icon} {row['timestamp'][:19]} | {row['query_name']} | {row['execution_time_seconds']:.3f}s | {row['rows_returned']} filas")
        
        # Errores si los hay
        if failed > 0:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            error_df = df[df['status'] == 'ERROR']
            for _, row in error_df.iterrows():
                print(f"   {row['timestamp'][:19]} | {row['query_name']} | {row['error_message']}")
        
        # Comparación de rendimiento por consulta
        if successful > 0:
            print(f"\n📊 RENDIMIENTO POR TIPO DE CONSULTA:")
            performance_stats = success_df.groupby('query_name').agg({
                'execution_time_seconds': ['count', 'mean', 'min', 'max'],
                'rows_returned': ['mean', 'sum']
            }).round(3)
            
            for query_name in performance_stats.index:
                stats = performance_stats.loc[query_name]
                print(f"   {query_name}:")
                print(f"     Ejecuciones: {stats[('execution_time_seconds', 'count')]}")
                print(f"     Tiempo promedio: {stats[('execution_time_seconds', 'mean')]}s")
                print(f"     Rango: {stats[('execution_time_seconds', 'min')]}s - {stats[('execution_time_seconds', 'max')]}s")
                print(f"     Filas promedio: {stats[('rows_returned', 'mean')]:.1f}")
        
        print("\n" + "="*80)
        print(f"📁 Archivo CSV: {csv_path.absolute()}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error leyendo el archivo CSV: {e}")

def export_postgres_summary(csv_file: str = "postgresql_queries_log.csv", output_file: str = "postgres_query_summary.txt"):
    """Exportar resumen de consultas PostgreSQL a un archivo de texto."""
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"❌ No se encontró el archivo {csv_file}")
        return
    
    try:
        df = pd.read_csv(csv_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE DE CONSULTAS POSTGRESQL\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"Total de consultas: {len(df)}\n")
            f.write(f"Consultas exitosas: {len(df[df['status'] == 'SUCCESS'])}\n")
            f.write(f"Consultas fallidas: {len(df[df['status'] == 'ERROR'])}\n\n")
            
            if len(df[df['status'] == 'SUCCESS']) > 0:
                success_df = df[df['status'] == 'SUCCESS']
                f.write(f"Tiempo promedio: {success_df['execution_time_seconds'].mean():.3f}s\n")
                f.write(f"Tiempo total: {success_df['execution_time_seconds'].sum():.3f}s\n")
                f.write(f"Filas totales: {success_df['rows_returned'].sum():,}\n\n")
            
            f.write("RENDIMIENTO POR TIPO DE CONSULTA:\n")
            f.write("-" * 40 + "\n")
            
            if len(df[df['status'] == 'SUCCESS']) > 0:
                performance_stats = success_df.groupby('query_name').agg({
                    'execution_time_seconds': ['count', 'mean', 'min', 'max'],
                    'rows_returned': ['mean', 'sum']
                }).round(3)
                
                for query_name in performance_stats.index:
                    stats = performance_stats.loc[query_name]
                    f.write(f"\n{query_name}:\n")
                    f.write(f"  Ejecuciones: {stats[('execution_time_seconds', 'count')]}\n")
                    f.write(f"  Tiempo promedio: {stats[('execution_time_seconds', 'mean')]}s\n")
                    f.write(f"  Rango: {stats[('execution_time_seconds', 'min')]}s - {stats[('execution_time_seconds', 'max')]}s\n")
                    f.write(f"  Filas promedio: {stats[('rows_returned', 'mean')]:.1f}\n")
            
            f.write("\nDETALLE DE CONSULTAS:\n")
            f.write("-" * 30 + "\n")
            for _, row in df.iterrows():
                f.write(f"{row['timestamp']} | {row['query_name']} | {row['execution_time_seconds']:.3f}s | {row['status']}\n")
        
        print(f"✅ Resumen PostgreSQL exportado a: {output_file}")
        
    except Exception as e:
        print(f"❌ Error exportando resumen: {e}")

def compare_with_bigquery(postgres_csv: str = "postgresql_queries_log.csv", bigquery_csv: str = "bigquery_queries_log.csv"):
    """Comparar rendimiento entre PostgreSQL y BigQuery."""
    
    postgres_path = Path(postgres_csv)
    bigquery_path = Path(bigquery_csv)
    
    if not postgres_path.exists():
        print(f"❌ No se encontró el archivo PostgreSQL: {postgres_csv}")
        return
    
    if not bigquery_path.exists():
        print(f"❌ No se encontró el archivo BigQuery: {bigquery_csv}")
        return
    
    try:
        df_pg = pd.read_csv(postgres_path)
        df_bq = pd.read_csv(bigquery_path)
        
        print("\n" + "="*80)
        print("⚖️  COMPARACIÓN POSTGRESQL vs BIGQUERY")
        print("="*80)
        
        # Estadísticas generales
        pg_success = df_pg[df_pg['status'] == 'SUCCESS']
        bq_success = df_bq[df_bq['status'] == 'SUCCESS']
        
        if len(pg_success) > 0 and len(bq_success) > 0:
            print(f"\n📊 TIEMPOS DE EJECUCIÓN:")
            print(f"   PostgreSQL promedio: {pg_success['execution_time_seconds'].mean():.3f}s")
            print(f"   BigQuery promedio: {bq_success['execution_time_seconds'].mean():.3f}s")
            
            ratio = pg_success['execution_time_seconds'].mean() / bq_success['execution_time_seconds'].mean()
            if ratio > 1:
                print(f"   🐘 PostgreSQL es {ratio:.1f}x más lento que BigQuery")
            else:
                print(f"   🐘 PostgreSQL es {1/ratio:.1f}x más rápido que BigQuery")
            
            print(f"\n📈 FILAS PROCESADAS:")
            print(f"   PostgreSQL total: {pg_success['rows_returned'].sum():,}")
            print(f"   BigQuery total: {bq_success['rows_returned'].sum():,}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Error comparando archivos: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "export":
            export_postgres_summary()
        elif sys.argv[1] == "compare":
            compare_with_bigquery()
        else:
            view_postgres_stats(sys.argv[1])
    else:
        view_postgres_stats() 