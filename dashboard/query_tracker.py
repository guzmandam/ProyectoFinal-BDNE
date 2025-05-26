"""
Módulo para rastrear consultas de BigQuery
Registra timestamp, tiempo de ejecución e ID único para cada consulta
"""

import csv
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import pandas as pd
from google.cloud import bigquery

class BigQueryTracker:
    """Clase para rastrear consultas de BigQuery y guardar métricas en CSV."""
    
    def __init__(self, csv_file: str = "./bigquery_queries_log.csv"):
        self.csv_file = Path(csv_file)
        self.fieldnames = [
            'query_id',
            'timestamp',
            'query_text',
            'execution_time_seconds',
            'rows_returned',
            'bytes_processed',
            'status',
            'error_message'
        ]
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Crear el archivo CSV con headers si no existe."""
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def _log_query(self, query_data: Dict[str, Any]):
        """Escribir una entrada de consulta al archivo CSV."""
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(query_data)
    
    def execute_query(self, client: bigquery.Client, query: str, query_name: str = "unknown") -> pd.DataFrame:
        """
        Ejecutar una consulta de BigQuery y rastrear métricas.
        
        Args:
            client: Cliente de BigQuery
            query: Consulta SQL a ejecutar
            query_name: Nombre descriptivo de la consulta
            
        Returns:
            DataFrame con los resultados de la consulta
        """
        query_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        start_time = time.time()
        
        query_data = {
            'query_id': query_id,
            'timestamp': timestamp,
            'query_text': f"-- {query_name}\n{query.strip()}",
            'execution_time_seconds': 0,
            'rows_returned': 0,
            'bytes_processed': 0,
            'status': 'STARTED',
            'error_message': ''
        }
        
        try:
            print(f"🔍 Ejecutando consulta [{query_id[:8]}]: {query_name}")
            
            # Ejecutar la consulta
            job = client.query(query)
            result_df = job.to_dataframe()
            
            # Calcular tiempo de ejecución
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Actualizar datos de la consulta
            query_data.update({
                'execution_time_seconds': round(execution_time, 3),
                'rows_returned': len(result_df),
                'bytes_processed': job.total_bytes_processed or 0,
                'status': 'SUCCESS'
            })
            
            print(f"✅ Consulta completada [{query_id[:8]}]: {execution_time:.3f}s, {len(result_df)} filas")
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            query_data.update({
                'execution_time_seconds': round(execution_time, 3),
                'status': 'ERROR',
                'error_message': str(e)
            })
            
            print(f"❌ Error en consulta [{query_id[:8]}]: {str(e)}")
            result_df = pd.DataFrame()  # DataFrame vacío en caso de error
        
        finally:
            # Registrar en CSV
            self._log_query(query_data)
        
        return result_df
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de las consultas ejecutadas."""
        if not self.csv_file.exists():
            return {}
        
        try:
            df = pd.read_csv(self.csv_file)
            if df.empty:
                return {}
            
            stats = {
                'total_queries': len(df),
                'successful_queries': len(df[df['status'] == 'SUCCESS']),
                'failed_queries': len(df[df['status'] == 'ERROR']),
                'avg_execution_time': df['execution_time_seconds'].mean(),
                'total_execution_time': df['execution_time_seconds'].sum(),
                'total_rows_returned': df['rows_returned'].sum(),
                'total_bytes_processed': df['bytes_processed'].sum(),
                'last_query_time': df['timestamp'].iloc[-1] if len(df) > 0 else None
            }
            
            return stats
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def print_stats(self):
        """Imprimir estadísticas de consultas en consola."""
        stats = self.get_query_stats()
        if not stats:
            print("📊 No hay estadísticas de consultas disponibles")
            return
        
        print("\n📊 ESTADÍSTICAS DE CONSULTAS BIGQUERY")
        print("=" * 50)
        print(f"Total de consultas: {stats['total_queries']}")
        print(f"Consultas exitosas: {stats['successful_queries']}")
        print(f"Consultas fallidas: {stats['failed_queries']}")
        print(f"Tiempo promedio: {stats['avg_execution_time']:.3f}s")
        print(f"Tiempo total: {stats['total_execution_time']:.3f}s")
        print(f"Filas totales: {stats['total_rows_returned']:,}")
        print(f"Bytes procesados: {stats['total_bytes_processed']:,}")
        print(f"Última consulta: {stats['last_query_time']}")
        print("=" * 50)

# Instancia global del tracker
query_tracker = BigQueryTracker() 