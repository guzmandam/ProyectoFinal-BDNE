"""Dashboard de Comercio BigQuery - Panel Resumen Ejecutivo"""

import reflex as rx
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio

from rxconfig import config
from .query_tracker import query_tracker

# BigQuery Configuration
PROJECT = "proyectofinalbdne"
DATASET = "commerce_doc"

class DashboardState(rx.State):
    """Gestión del estado del dashboard."""
    
    # Estados de carga
    is_loading: bool = True
    last_updated: str = ""
    
    # KPIs del Resumen Ejecutivo
    total_revenue: float = 0.0
    total_transactions: int = 0
    avg_order_value: float = 0.0
    unique_customers: int = 0
    
    # Datos de gráficos - usando lista de diccionarios para gráficos Reflex
    daily_revenue_data: List[Dict[str, Any]] = []
    top_products_data: List[Dict[str, Any]] = []
    sales_by_store_data: List[Dict[str, Any]] = []
    category_revenue_data: List[Dict[str, Any]] = []
    
    # Datos de tablas
    top_employees: List[Dict[str, Any]] = []
    store_performance: List[Dict[str, Any]] = []
    
    def get_bq_client(self):
        """Inicializar cliente de BigQuery."""
        return bigquery.Client(project=PROJECT)
    
    @rx.event
    async def load_dashboard_data(self):
        """Cargar todos los datos del dashboard desde BigQuery."""
        self.is_loading = True
        yield
        
        try:
            client = self.get_bq_client()
            
            # Cargar KPIs del resumen ejecutivo
            await self.load_executive_summary(client)
            
            # Cargar datos de gráficos
            await self.load_charts_data(client)
            
            # Cargar datos de tablas
            await self.load_tables_data(client)
            
            self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Mostrar estadísticas de consultas
            # query_tracker.print_stats()
            
        except Exception as e:
            print(f"Error cargando datos del dashboard: {e}")
        finally:
            self.is_loading = False
            yield
    
    async def load_executive_summary(self, client):
        """Cargar KPIs del resumen ejecutivo."""
        
        try:
            # Ingresos Totales y Transacciones
            summary_query = f"""
            SELECT 
                SUM(total_amount) as total_revenue,
                COUNT(*) as total_transactions,
                AVG(total_amount) as avg_order_value,
                COUNT(DISTINCT CONCAT(customer.first_name, customer.last_name, customer.email)) as unique_customers
            FROM `{PROJECT}.{DATASET}.sales`
            WHERE DATE(TIMESTAMP(timestamp)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            
            result = client.query(summary_query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                self.total_revenue = float(row['total_revenue'] or 0)
                self.total_transactions = int(row['total_transactions'] or 0)
                self.avg_order_value = float(row['avg_order_value'] or 0)
                self.unique_customers = int(row['unique_customers'] or 0)
        except Exception as e:
            print(f"Error cargando resumen ejecutivo: {e}")
            # Establecer valores por defecto si la consulta falla
            self.total_revenue = 0.0
            self.total_transactions = 0
            self.avg_order_value = 0.0
            self.unique_customers = 0
    
    async def load_charts_data(self, client):
        """Cargar datos para gráficos."""
        
        try:
            # Gráfico de Ingresos Diarios - usando formato de timestamp ISO 8601 correcto
            daily_revenue_query = f"""
            SELECT 
                DATE(TIMESTAMP(timestamp)) as sale_date,
                SUM(total_amount) as daily_revenue
            FROM `{PROJECT}.{DATASET}.sales`
            WHERE DATE(TIMESTAMP(timestamp)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY sale_date
            ORDER BY sale_date
            """
            
            df_daily = client.query(daily_revenue_query).to_dataframe()
            if not df_daily.empty:
                # Convertir al formato esperado por los gráficos Reflex
                self.daily_revenue_data = [
                    {
                        "fecha": row['sale_date'].strftime('%d/%m'),
                        "ingresos": float(row['daily_revenue'])
                    }
                    for _, row in df_daily.iterrows()
                ]
            else:
                self.daily_revenue_data = []
        except Exception as e:
            print(f"Error cargando datos de ingresos diarios: {e}")
            self.daily_revenue_data = []
        
        try:
            # Gráfico de Productos Principales
            top_products_query = f"""
            SELECT 
                line.product.name as product_name,
                SUM(line.line_total) as total_revenue
            FROM `{PROJECT}.{DATASET}.sales`,
            UNNEST(lines) as line
            GROUP BY line.product.name
            ORDER BY total_revenue DESC
            LIMIT 10
            """
            
            df_products = client.query(top_products_query).to_dataframe()
            if not df_products.empty:
                self.top_products_data = [
                    {
                        "producto": row['product_name'][:20] + "..." if len(row['product_name']) > 20 else row['product_name'],
                        "ingresos": float(row['total_revenue'])
                    }
                    for _, row in df_products.iterrows()
                ]
            else:
                self.top_products_data = []
        except Exception as e:
            print(f"Error cargando datos de productos principales: {e}")
            self.top_products_data = []
        
        try:
            # Gráfico de Ventas por Tienda
            store_sales_query = f"""
            SELECT 
                store.name as store_name,
                SUM(total_amount) as total_revenue,
                COUNT(*) as transaction_count
            FROM `{PROJECT}.{DATASET}.sales`
            GROUP BY store.name
            ORDER BY total_revenue DESC
            """
            
            df_stores = client.query(store_sales_query).to_dataframe()
            if not df_stores.empty:
                self.sales_by_store_data = [
                    {
                        "tienda": row['store_name'],
                        "ingresos": float(row['total_revenue']),
                        "transacciones": int(row['transaction_count'])
                    }
                    for _, row in df_stores.iterrows()
                ]
            else:
                self.sales_by_store_data = []
        except Exception as e:
            print(f"Error cargando datos de ventas por tienda: {e}")
            self.sales_by_store_data = []
        
        try:
            # Gráfico de Ingresos por Categoría
            category_query = f"""
            SELECT 
                line.product.category as category,
                SUM(line.line_total) as category_revenue
            FROM `{PROJECT}.{DATASET}.sales`,
            UNNEST(lines) as line
            GROUP BY line.product.category
            ORDER BY category_revenue DESC
            """
            
            df_categories = client.query(category_query).to_dataframe()
            if not df_categories.empty:
                self.category_revenue_data = [
                    {
                        "categoria": row['category'],
                        "ingresos": float(row['category_revenue'])
                    }
                    for _, row in df_categories.iterrows()
                ]
            else:
                self.category_revenue_data = []
        except Exception as e:
            print(f"Error cargando datos de ingresos por categoría: {e}")
            self.category_revenue_data = []
    
    async def load_tables_data(self, client):
        """Cargar datos para tablas."""
        
        # Empleados Principales
        employees_query = f"""
        SELECT 
            CONCAT(employee.first_name, ' ', employee.last_name) as employee_name,
            store.name as store_name,
            SUM(total_amount) as total_sales,
            COUNT(*) as transactions_handled,
            ROUND(AVG(total_amount), 2) as avg_sale_amount
        FROM `{PROJECT}.{DATASET}.sales`
        GROUP BY employee.first_name, employee.last_name, store.name
        ORDER BY total_sales DESC
        LIMIT 10
        """
        
        df_employees = client.query(employees_query).to_dataframe()
        self.top_employees = df_employees.to_dict('records') if not df_employees.empty else []
        
        # Rendimiento de Tiendas
        store_perf_query = f"""
        SELECT 
            store.name as store_name,
            SUM(total_amount) as total_revenue,
            COUNT(*) as total_transactions,
            COUNT(DISTINCT CONCAT(customer.first_name, customer.last_name, customer.email)) as unique_customers,
            ROUND(AVG(total_amount), 2) as avg_transaction_value
        FROM `{PROJECT}.{DATASET}.sales`
        GROUP BY store.name
        ORDER BY total_revenue DESC
        """
        
        df_store_perf = client.query(store_perf_query).to_dataframe()
        self.store_performance = df_store_perf.to_dict('records') if not df_store_perf.empty else []


def kpi_card(title: str, value: str, subtitle: str = "", color: str = "blue") -> rx.Component:
    """Create a KPI card component."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("trending-up", size=20, color=color),
                rx.text(title, size="2", color="gray"),
                justify="between",
                width="100%",
            ),
            rx.text(value, size="6", weight="bold"),
            rx.text(subtitle, size="1", color="gray") if subtitle else rx.fragment(),
            spacing="1",
            align="start",
        ),
        width="100%",
        padding="4",
    )


def daily_revenue_chart() -> rx.Component:
    """Gráfico de línea de tendencia de ingresos diarios."""
    return rx.card(
        rx.vstack(
            rx.heading("Tendencia de Ingresos Diarios (Últimos 30 Días)", size="4", margin_bottom="2"),
            rx.cond(
                DashboardState.daily_revenue_data.length() > 0,
                rx.recharts.line_chart(
                    rx.recharts.line(
                        data_key="ingresos",
                        stroke=rx.color("blue", 9),
                        stroke_width=2,
                    ),
                    rx.recharts.x_axis(data_key="fecha"),
                    rx.recharts.y_axis(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.tooltip(),
                    data=DashboardState.daily_revenue_data,
                    width="100%",
                    height=300,
                ),
                rx.center(
                    rx.spinner(size="3"),
                    height="300px",
                    width="100%",
                ),
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def top_products_chart() -> rx.Component:
    """Gráfico de barras horizontales de productos principales."""
    return rx.card(
        rx.vstack(
            rx.heading("Top 10 Productos por Ingresos", size="4", margin_bottom="2"),
            rx.cond(
                DashboardState.top_products_data.length() > 0,
                rx.recharts.bar_chart(
                    rx.recharts.bar(
                        data_key="ingresos",
                        fill=rx.color("green", 9),
                    ),
                    rx.recharts.x_axis(type_="number"),
                    rx.recharts.y_axis(data_key="producto", type_="category", width=120),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.tooltip(),
                    data=DashboardState.top_products_data,
                    layout="vertical",
                    width="100%",
                    height=400,
                ),
                rx.center(
                    rx.spinner(size="3"),
                    height="400px",
                    width="100%",
                ),
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def sales_by_store_chart() -> rx.Component:
    """Gráfico circular de ventas por tienda."""
    return rx.card(
        rx.vstack(
            rx.heading("Distribución de Ingresos por Tienda", size="4", margin_bottom="2"),
            rx.cond(
                DashboardState.sales_by_store_data.length() > 0,
                rx.recharts.pie_chart(
                    rx.recharts.pie(
                        data=DashboardState.sales_by_store_data,
                        data_key="ingresos",
                        name_key="tienda",
                        cx="50%",
                        cy="50%",
                        fill=rx.color("purple", 9),
                    ),
                    rx.recharts.tooltip(),
                    rx.recharts.legend(),
                    width="100%",
                    height=400,
                ),
                rx.center(
                    rx.spinner(size="3"),
                    height="400px",
                    width="100%",
                ),
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def category_revenue_chart() -> rx.Component:
    """Gráfico de barras de ingresos por categoría."""
    return rx.card(
        rx.vstack(
            rx.heading("Ingresos por Categoría de Producto", size="4", margin_bottom="2"),
            rx.cond(
                DashboardState.category_revenue_data.length() > 0,
                rx.recharts.bar_chart(
                    rx.recharts.bar(
                        data_key="ingresos",
                        fill=rx.color("orange", 9),
                    ),
                    rx.recharts.x_axis(data_key="categoria"),
                    rx.recharts.y_axis(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.tooltip(),
                    data=DashboardState.category_revenue_data,
                    width="100%",
                    height=300,
                ),
                rx.center(
                    rx.spinner(size="3"),
                    height="300px",
                    width="100%",
                ),
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def employee_table() -> rx.Component:
    """Crear tabla de rendimiento de empleados."""
    return rx.card(
        rx.vstack(
            rx.heading("Empleados con Mejor Rendimiento", size="4"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Empleado"),
                        rx.table.column_header_cell("Tienda"),
                        rx.table.column_header_cell("Ventas Totales"),
                        rx.table.column_header_cell("Transacciones"),
                        rx.table.column_header_cell("Venta Promedio"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        DashboardState.top_employees,
                        lambda emp: rx.table.row(
                            rx.table.cell(emp["employee_name"]),
                            rx.table.cell(emp["store_name"]),
                            rx.table.cell(f"${emp['total_sales']:,.2f}"),
                            rx.table.cell(str(emp["transactions_handled"])),
                            rx.table.cell(f"${emp['avg_sale_amount']:,.2f}"),
                        ),
                    ),
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def store_table() -> rx.Component:
    """Crear tabla de rendimiento de tiendas."""
    return rx.card(
        rx.vstack(
            rx.heading("Rendimiento de Tiendas", size="4"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Tienda"),
                        rx.table.column_header_cell("Ingresos"),
                        rx.table.column_header_cell("Transacciones"),
                        rx.table.column_header_cell("Clientes"),
                        rx.table.column_header_cell("Transacción Promedio"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        DashboardState.store_performance,
                        lambda store: rx.table.row(
                            rx.table.cell(store["store_name"]),
                            rx.table.cell(f"${store['total_revenue']:,.2f}"),
                            rx.table.cell(str(store["total_transactions"])),
                            rx.table.cell(str(store["unique_customers"])),
                            rx.table.cell(f"${store['avg_transaction_value']:,.2f}"),
                        ),
                    ),
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
        padding="4",
    )


def dashboard() -> rx.Component:
    """Componente principal del dashboard."""
    return rx.container(
        rx.vstack(
            # Encabezado
            rx.hstack(
                rx.heading("Dashboard de Comercio - Resumen Ejecutivo", size="8"),
                rx.spacer(),
                rx.hstack(
                    rx.text(f"Última actualización: {DashboardState.last_updated}", size="2", color="gray"),
                    rx.button(
                        rx.icon("refresh-cw", size=16),
                        "Actualizar",
                        on_click=DashboardState.load_dashboard_data,
                        loading=DashboardState.is_loading,
                        size="2",
                    ),
                    spacing="3",
                ),
                justify="between",
                align="center",
                width="100%",
                margin_bottom="6",
            ),
            
            # Tarjetas KPI
            rx.grid(
                kpi_card(
                    "Ingresos Totales (30 días)",
                    f"${DashboardState.total_revenue:,.2f}",
                    "Últimos 30 días",
                    "green"
                ),
                kpi_card(
                    "Transacciones Totales",
                    f"{DashboardState.total_transactions:,}",
                    "Últimos 30 días",
                    "blue"
                ),
                kpi_card(
                    "Valor Promedio de Orden",
                    f"${DashboardState.avg_order_value:.2f}",
                    "Por transacción",
                    "purple"
                ),
                kpi_card(
                    "Clientes Únicos",
                    f"{DashboardState.unique_customers:,}",
                    "Últimos 30 días",
                    "orange"
                ),
                columns="4",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            
            # Fila de Gráficos 1
            rx.grid(
                daily_revenue_chart(),
                category_revenue_chart(),
                columns="2",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            
            # Fila de Gráficos 2
            rx.grid(
                top_products_chart(),
                sales_by_store_chart(),
                columns="2",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            
            # Tablas
            rx.grid(
                employee_table(),
                store_table(),
                columns="2",
                spacing="4",
                width="100%",
            ),
            
            spacing="4",
            width="100%",
        ),
        max_width="1400px",
        padding="6",
        on_mount=DashboardState.load_dashboard_data,
    )


def index() -> rx.Component:
    """Página principal."""
    return rx.fragment(
        rx.color_mode.button(position="top-right"),
        dashboard(),
    )


app = rx.App()
app.add_page(index, route="/")
