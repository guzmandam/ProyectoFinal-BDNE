#!/usr/bin/env python3
"""
Script para ejecutar consultas del dashboard en PostgreSQL
Replica las mismas consultas de BigQuery pero adaptadas para PostgreSQL
Incluye tracking de tiempos y métricas de rendimiento
"""

import psycopg2
import pandas as pd
import time
import uuid
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import os
from contextlib import contextmanager

class PostgreSQLTracker:
    """Clase para rastrear consultas PostgreSQL y guardar métricas en CSV."""
    
    def __init__(self, csv_file: str = "./postgresql_queries_log.csv"):
        self.csv_file = Path(csv_file)
        self.fieldnames = [
            'query_id',
            'timestamp',
            'query_name',
            'query_text',
            'execution_time_seconds',
            'rows_returned',
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
    
    def execute_query(self, connection, query: str, query_name: str = "unknown") -> pd.DataFrame:
        """
        Ejecutar una consulta PostgreSQL y rastrear métricas.
        
        Args:
            connection: Conexión a PostgreSQL
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
            'query_name': query_name,
            'query_text': query.strip(),
            'execution_time_seconds': 0,
            'rows_returned': 0,
            'status': 'STARTED',
            'error_message': ''
        }
        
        try:
            print(f"🔍 Ejecutando consulta PostgreSQL [{query_id[:8]}]: {query_name}")
            
            # Ejecutar la consulta
            result_df = pd.read_sql_query(query, connection)
            
            # Calcular tiempo de ejecución
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Actualizar datos de la consulta
            query_data.update({
                'execution_time_seconds': round(execution_time, 3),
                'rows_returned': len(result_df),
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

class PostgreSQLDashboard:
    """Clase principal para ejecutar consultas del dashboard en PostgreSQL."""
    
    def __init__(self, connection_params: Dict[str, str]):
        self.connection_params = connection_params
        self.tracker = PostgreSQLTracker()
        self.results = {}
    
    @contextmanager
    def get_connection(self):
        """Context manager para manejar conexiones PostgreSQL."""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def resumen_ejecutivo(self) -> pd.DataFrame:
        """Consulta de resumen ejecutivo - KPIs principales."""
        query = """
        SELECT 
            SUM(s.total_amount) as total_revenue,
            COUNT(*) as total_transactions,
            AVG(s.total_amount) as avg_order_value,
            COUNT(DISTINCT CONCAT(c.first_name, ' ', c.last_name, ' - ', c.email)) as unique_customers
        FROM Sale s
        JOIN Customer c ON s.customer_id = c.customer_id
        WHERE s.sale_timestamp >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        with self.get_connection() as conn:
            return self.tracker.execute_query(conn, query, "resumen_ejecutivo")
    
    def ingresos_diarios(self) -> pd.DataFrame:
        """Consulta de ingresos diarios - últimos 30 días."""
        query = """
        SELECT 
            DATE(s.sale_timestamp) as sale_date,
            SUM(s.total_amount) as daily_revenue
        FROM Sale s
        WHERE s.sale_timestamp >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(s.sale_timestamp)
        ORDER BY sale_date
        """
        
        with self.get_connection() as conn:
            return self.tracker.execute_query(conn, query, "ingresos_diarios")
    
    def productos_principales(self) -> pd.DataFrame:
        """Consulta de top 10 productos por ingresos."""
        query = """
        SELECT 
            p.name as product_name,
            SUM(sl.line_total) as total_revenue
        FROM SaleLine sl
        JOIN Product p ON sl.product_id = p.product_id
        GROUP BY p.product_id, p.name
        ORDER BY total_revenue DESC
        LIMIT 10
        """
        
        with self.get_connection() as conn:
            return self.tracker.execute_query(conn, query, "productos_principales")
    
    def ventas_por_tienda(self) -> pd.DataFrame:
        """Consulta de ventas por tienda."""
        query = """
        SELECT 
            st.name as store_name,
            SUM(s.total_amount) as total_revenue,
            COUNT(*) as transaction_count
        FROM Sale s
        JOIN Store st ON s.store_id = st.store_id
        GROUP BY st.store_id, st.name
        ORDER BY total_revenue DESC
        """
        
        with self.get_connection() as conn:
            return self.tracker.execute_query(conn, query, "ventas_por_tienda")
    
    def ingresos_por_categoria(self) -> pd.DataFrame:
        """Consulta de ingresos por categoría de producto."""
        query = """
        SELECT 
            c.name as category,
            SUM(sl.line_total) as category_revenue
        FROM SaleLine sl
        JOIN Product p ON sl.product_id = p.product_id
        JOIN Category c ON p.category_id = c.category_id
        GROUP BY c.category_id, c.name
        ORDER BY category_revenue DESC
        """
        
        with self.get_connection() as conn:
            return self.tracker.execute_query(conn, query, "ingresos_por_categoria")
    
    def empleados_principales(self) -> pd.DataFrame:
        """Consulta de top empleados por ventas."""
        query = """
        SELECT 
            CONCAT(e.first_name, ' ', e.last_name) as employee_name,
            st.name as store_name,
            SUM(s.total_amount) as total_sales,
            COUNT(*) as transactions_handled,
            ROUND(AVG(s.total_amount), 2) as avg_sale_amount
        FROM Sale s
        JOIN Employee e ON s.employee_id = e.employee_id
        JOIN Store st ON s.store_id = st.store_id
        GROUP BY e.employee_id, e.first_name, e.last_name, st.name
        ORDER BY total_sales DESC
        LIMIT 10
        """
        
        with self.get_connection() as conn:
            return self.tracker.execute_query(conn, query, "empleados_principales")
    
    def rendimiento_tiendas(self) -> pd.DataFrame:
        """Consulta de rendimiento detallado por tienda."""
        query = """
        SELECT 
            st.name as store_name,
            SUM(s.total_amount) as total_revenue,
            COUNT(*) as total_transactions,
            COUNT(DISTINCT s.customer_id) as unique_customers,
            ROUND(AVG(s.total_amount), 2) as avg_transaction_value
        FROM Sale s
        JOIN Store st ON s.store_id = st.store_id
        GROUP BY st.store_id, st.name
        ORDER BY total_revenue DESC
        """
        
        with self.get_connection() as conn:
            return self.tracker.execute_query(conn, query, "rendimiento_tiendas")
    
    def ejecutar_todas_consultas(self) -> Dict[str, pd.DataFrame]:
        """Ejecutar todas las consultas del dashboard y retornar resultados."""
        print("\n🚀 EJECUTANDO CONSULTAS DEL DASHBOARD EN POSTGRESQL")
        print("=" * 60)
        
        consultas = [
            ("resumen_ejecutivo", self.resumen_ejecutivo),
            ("ingresos_diarios", self.ingresos_diarios),
            ("productos_principales", self.productos_principales),
            ("ventas_por_tienda", self.ventas_por_tienda),
            ("ingresos_por_categoria", self.ingresos_por_categoria),
            ("empleados_principales", self.empleados_principales),
            ("rendimiento_tiendas", self.rendimiento_tiendas),
        ]
        
        resultados = {}
        start_total = time.time()
        
        for nombre, funcion in consultas:
            try:
                resultado = funcion()
                resultados[nombre] = resultado
                print(f"📊 {nombre}: {len(resultado)} filas")
            except Exception as e:
                print(f"❌ Error en {nombre}: {e}")
                resultados[nombre] = pd.DataFrame()
        
        end_total = time.time()
        total_time = end_total - start_total
        
        print("\n" + "=" * 60)
        print(f"⏱️  Tiempo total de ejecución: {total_time:.3f}s")
        print(f"📁 Log guardado en: {self.tracker.csv_file}")
        print("=" * 60)
        
        return resultados
    
    def mostrar_estadisticas(self):
        """Mostrar estadísticas de las consultas ejecutadas."""
        if not self.tracker.csv_file.exists():
            print("❌ No hay datos de consultas disponibles")
            return
        
        try:
            df = pd.read_csv(self.tracker.csv_file)
            if df.empty:
                print("📊 No hay consultas registradas")
                return
            
            print("\n📊 ESTADÍSTICAS DE CONSULTAS POSTGRESQL")
            print("=" * 50)
            
            total_queries = len(df)
            successful = len(df[df['status'] == 'SUCCESS'])
            failed = len(df[df['status'] == 'ERROR'])
            
            print(f"Total de consultas: {total_queries}")
            print(f"Consultas exitosas: {successful}")
            print(f"Consultas fallidas: {failed}")
            
            if successful > 0:
                success_df = df[df['status'] == 'SUCCESS']
                print(f"Tiempo promedio: {success_df['execution_time_seconds'].mean():.3f}s")
                print(f"Tiempo total: {success_df['execution_time_seconds'].sum():.3f}s")
                print(f"Filas totales: {success_df['rows_returned'].sum():,}")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error mostrando estadísticas: {e}")

def main():
    """Función principal para ejecutar el script."""
    
    # Configuración de conexión PostgreSQL
    # Puedes modificar estos valores según tu configuración
    connection_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'commerce'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }
    
    print("🐘 DASHBOARD POSTGRESQL - CONSULTAS DE COMERCIO")
    print("=" * 60)
    print(f"Conectando a: {connection_params['host']}:{connection_params['port']}/{connection_params['database']}")
    print("=" * 60)
    
    try:
        # Crear instancia del dashboard
        dashboard = PostgreSQLDashboard(connection_params)
        
        # Ejecutar todas las consultas
        resultados = dashboard.ejecutar_todas_consultas()
        
        # Mostrar estadísticas
        dashboard.mostrar_estadisticas()
        
        # Mostrar algunos resultados de ejemplo
        print("\n📋 EJEMPLOS DE RESULTADOS:")
        print("-" * 30)
        
        if 'resumen_ejecutivo' in resultados and not resultados['resumen_ejecutivo'].empty:
            resumen = resultados['resumen_ejecutivo'].iloc[0]
            print(f"💰 Ingresos totales (30 días): ${resumen['total_revenue']:,.2f}")
            print(f"🛒 Transacciones totales: {resumen['total_transactions']:,}")
            print(f"📊 Valor promedio orden: ${resumen['avg_order_value']:.2f}")
            print(f"👥 Clientes únicos: {resumen['unique_customers']:,}")
        
        if 'productos_principales' in resultados and not resultados['productos_principales'].empty:
            print(f"\n🏆 Top 3 Productos:")
            top_products = resultados['productos_principales'].head(3)
            for i, (_, row) in enumerate(top_products.iterrows(), 1):
                print(f"   {i}. {row['product_name']}: ${row['total_revenue']:,.2f}")
        
        print(f"\n✅ Proceso completado. Revisa {dashboard.tracker.csv_file} para detalles.")
        
    except Exception as e:
        print(f"❌ Error ejecutando el dashboard: {e}")
        print("\n💡 Consejos:")
        print("1. Verifica que PostgreSQL esté ejecutándose")
        print("2. Confirma los parámetros de conexión")
        print("3. Asegúrate de que la base de datos 'commerce' exista")
        print("4. Verifica que las tablas estén creadas y con datos")

if __name__ == "__main__":
    main() 