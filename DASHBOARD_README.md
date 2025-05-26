# Commerce Analytics Dashboard

A comprehensive executive summary dashboard built with Reflex that connects to BigQuery to display real-time commerce analytics.

## Features

### Executive Summary Panel
- **Total Revenue** (Last 30 days)
- **Total Transactions** 
- **Average Order Value**
- **Unique Customers**

### Interactive Charts
- **Daily Revenue Trend** - Line chart showing revenue over time
- **Top Products by Revenue** - Horizontal bar chart of best-selling products
- **Revenue Distribution by Store** - Pie chart showing store performance
- **Revenue by Product Category** - Bar chart of category performance

### Data Tables
- **Top Performing Employees** - Sales performance by employee
- **Store Performance** - Comprehensive store metrics

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This dashboard now uses Reflex's native chart components instead of Plotly, resulting in:
- Smaller bundle size (no heavy Plotly dependency)
- Better performance and faster loading
- Native integration with Reflex's reactive system
- Consistent styling with Reflex design tokens

### 2. Google Cloud Authentication

You have several options for authentication:

#### Option A: Service Account Key (Recommended for Development)
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

#### Option B: Application Default Credentials
```bash
gcloud auth application-default login
```

#### Option C: For Production (Google Cloud Run, Compute Engine, etc.)
The application will automatically use the service account attached to the compute resource.

### 3. Verify BigQuery Access

Make sure your authentication has access to:
- Project: `proyectofinalbdne`
- Dataset: `commerce_doc`
- Tables: `sales`, `stores`

### 4. Run the Dashboard

```bash
cd pablito
reflex run
```

The dashboard will be available at `http://localhost:3000`

## BigQuery Schema

### Sales Table (`proyectofinalbdne.commerce_doc.sales`)
```sql
- timestamp: STRING
- store: RECORD
  - name: STRING
- employee: RECORD
  - first_name: STRING
  - last_name: STRING
- customer: RECORD
  - first_name: STRING
  - last_name: STRING
  - email: STRING
- lines: RECORD (REPEATED)
  - product: RECORD
    - name: STRING
    - category: STRING
    - price: NUMERIC
  - quantity: INT64
  - line_total: NUMERIC
- total_amount: NUMERIC
```

### Stores Table (`proyectofinalbdne.commerce_doc.stores`)
```sql
- store_name: STRING
- address: STRING
- employees: RECORD (REPEATED)
  - first_name: STRING
  - last_name: STRING
  - position: STRING
- inventory: RECORD (REPEATED)
  - product: RECORD
    - name: STRING
    - category: STRING
    - price: NUMERIC
  - quantity: INT64
```

## Key Queries Used

### Executive Summary KPIs
```sql
SELECT 
    SUM(total_amount) as total_revenue,
    COUNT(*) as total_transactions,
    AVG(total_amount) as avg_order_value,
    COUNT(DISTINCT CONCAT(customer.first_name, customer.last_name, customer.email)) as unique_customers
FROM `proyectofinalbdne.commerce_doc.sales`
WHERE PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
```

### Daily Revenue Trend
```sql
SELECT 
    DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', timestamp)) as sale_date,
    SUM(total_amount) as daily_revenue
FROM `proyectofinalbdne.commerce_doc.sales`
WHERE PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY sale_date
ORDER BY sale_date
```

### Top Products
```sql
SELECT 
    line.product.name as product_name,
    SUM(line.line_total) as total_revenue
FROM `proyectofinalbdne.commerce_doc.sales`,
UNNEST(lines) as line
GROUP BY line.product.name
ORDER BY total_revenue DESC
LIMIT 10
```

## Dashboard Components

### KPI Cards
- Color-coded metric cards with icons
- Real-time data updates
- Responsive design

### Charts
- Built with Reflex's native recharts components
- Optimized for performance and bundle size
- Seamless integration with Reflex state
- Responsive and mobile-friendly
- Professional styling with Reflex design system

### Data Tables
- Sortable columns
- Clean, readable format
- Real-time data

## Troubleshooting

### Authentication Issues
```bash
# Check if you're authenticated
gcloud auth list

# Re-authenticate if needed
gcloud auth application-default login
```

### BigQuery Access Issues
```bash
# Test BigQuery access
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM `proyectofinalbdne.commerce_doc.sales`'
```

### Dependencies Issues
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Development

### Adding New Charts
1. Add the chart data to `DashboardState`
2. Create the BigQuery query in `load_charts_data()`
3. Add the chart component to the dashboard layout

### Adding New KPIs
1. Add the metric to `DashboardState`
2. Create the query in `load_executive_summary()`
3. Add a new KPI card to the dashboard

### Customizing Styling
- Modify colors in `pablito/config.py`
- Adjust chart layouts in the Plotly configurations
- Update card styling in the component functions

## Performance Considerations

- Queries are optimized for the last 30 days by default
- Data is cached in the state until manual refresh
- Consider implementing automatic refresh for production use
- BigQuery costs are based on data processed - queries are optimized to minimize scanning

## Next Steps

1. **Add Real-time Updates**: Implement automatic refresh every 5 minutes
2. **Add Filters**: Date range selectors, store filters, category filters
3. **Add More Charts**: Customer segmentation, inventory analysis, time-based patterns
4. **Add Export Features**: PDF reports, CSV downloads
5. **Add Alerts**: Set up notifications for key metrics
6. **Mobile Optimization**: Improve responsive design for mobile devices 