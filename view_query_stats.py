#!/usr/bin/env python3
"""
Script para ver estadísticas de consultas BigQuery
Muestra información detallada del archivo CSV de tracking
"""

import pandas as pd
from pathlib import Path
import sys

def view_query_stats(csv_file: str = "bigquery_queries_log.csv"):
    """Ver estadísticas detalladas de las consultas BigQuery."""
    
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"❌ No se encontró el archivo {csv_file}")
        print("Ejecuta el dashboard primero para generar datos de consultas.")
        return
    
    try:
        df = pd.read_csv(csv_path)
        
        if df.empty:
            print("📊 El archivo de consultas está vacío")
            return
        
        print("\n" + "="*80)
        print("📊 REPORTE DETALLADO DE CONSULTAS BIGQUERY")
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
            print(f"   Bytes procesados: {success_df['bytes_processed'].sum():,}")
            print(f"   Promedio filas por consulta: {success_df['rows_returned'].mean():.1f}")
        
        # Consultas por tipo
        print(f"\n🔍 CONSULTAS POR TIPO:")
        query_types = df['query_text'].str.extract(r'-- (\w+)')[0].value_counts()
        for query_type, count in query_types.items():
            avg_time = df[df['query_text'].str.contains(f'-- {query_type}', na=False)]['execution_time_seconds'].mean()
            print(f"   {query_type}: {count} consultas (promedio: {avg_time:.3f}s)")
        
        # Últimas consultas
        print(f"\n🕐 ÚLTIMAS 5 CONSULTAS:")
        recent = df.tail(5)[['timestamp', 'query_text', 'execution_time_seconds', 'rows_returned', 'status']]
        for _, row in recent.iterrows():
            query_name = row['query_text'].split('\n')[0].replace('-- ', '')
            status_icon = "✅" if row['status'] == 'SUCCESS' else "❌"
            print(f"   {status_icon} {row['timestamp'][:19]} | {query_name} | {row['execution_time_seconds']:.3f}s | {row['rows_returned']} filas")
        
        # Errores si los hay
        if failed > 0:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            error_df = df[df['status'] == 'ERROR']
            for _, row in error_df.iterrows():
                query_name = row['query_text'].split('\n')[0].replace('-- ', '')
                print(f"   {row['timestamp'][:19]} | {query_name} | {row['error_message']}")
        
        print("\n" + "="*80)
        print(f"📁 Archivo CSV: {csv_path.absolute()}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error leyendo el archivo CSV: {e}")

def export_summary(csv_file: str = "bigquery_queries_log.csv", output_file: str = "query_summary.txt"):
    """Exportar resumen de consultas a un archivo de texto."""
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"❌ No se encontró el archivo {csv_file}")
        return
    
    try:
        df = pd.read_csv(csv_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE DE CONSULTAS BIGQUERY\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"Total de consultas: {len(df)}\n")
            f.write(f"Consultas exitosas: {len(df[df['status'] == 'SUCCESS'])}\n")
            f.write(f"Consultas fallidas: {len(df[df['status'] == 'ERROR'])}\n\n")
            
            if len(df[df['status'] == 'SUCCESS']) > 0:
                success_df = df[df['status'] == 'SUCCESS']
                f.write(f"Tiempo promedio: {success_df['execution_time_seconds'].mean():.3f}s\n")
                f.write(f"Tiempo total: {success_df['execution_time_seconds'].sum():.3f}s\n")
                f.write(f"Filas totales: {success_df['rows_returned'].sum():,}\n")
                f.write(f"Bytes procesados: {success_df['bytes_processed'].sum():,}\n\n")
            
            f.write("DETALLE DE CONSULTAS:\n")
            f.write("-" * 30 + "\n")
            for _, row in df.iterrows():
                query_name = row['query_text'].split('\n')[0].replace('-- ', '')
                f.write(f"{row['timestamp']} | {query_name} | {row['execution_time_seconds']:.3f}s | {row['status']}\n")
        
        print(f"✅ Resumen exportado a: {output_file}")
        
    except Exception as e:
        print(f"❌ Error exportando resumen: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "export":
            export_summary()
        else:
            view_query_stats(sys.argv[1])
    else:
        view_query_stats() 