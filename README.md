# Geodata Consolidation Pipeline

A comprehensive data pipeline for consolidating geographic data from Google Maps, featuring automated ingestion, orchestration, and transformation workflows.

## Overview

The Geodata Consolidation Pipeline is an end-to-end solution that:

- Ingests address data from multiple sources
- Geocodes addresses using Google Maps API
- Orchestrates complex data workflows using Dagster
- Transforms raw data into a clean data warehouse using dbt
- Provides REST APIs for data import and management

## Project Structure
```
geodata-consolidation-pipeline/
├── ingestion/                      # Data ingestion layer
│   ├── dlthub/                     # dlt-based API ingestion
│   │   └── main.py                 # Google Maps API integration
│   └── fastapi/                    # REST API for data import
│       └── main.py                 # FastAPI endpoints
│
├── orchestration/                  # Workflow orchestration
│   └── gmap_scraper/               # Dagster project
│       ├── gmap_scraper/
│       │   ├── assets.py           # Automated assets
│       │   ├── definitions.py      # Dagster definitions
│       │   └── __init__.py
│       ├── gmap_scraper_tests/     # Unit tests
│       ├── setup.py                # Package configuration
│       └── README.md               # Orchestration docs
│
├── transformations/                # Data transformation
│   ├── dbt_project.yml             # dbt configuration
│   ├── models/                     # dbt SQL models
│   │   ├── geocode_consolidated.sql
│   │   └── sources.yml
│   ├── macros/                     # dbt macro library
│   ├── tests/                      # dbt tests
│   └── README.md                   # Transformation docs
│
├── logs/                           # Application logs
├── .env                            # Environment variables
├── .venv/                          # Python virtual environment
└── SETUP.md                        # Setup and installation guide
```

## Technology Stack

- **Python 3.8+** - Primary language
- **Dagster** - Workflow orchestration and monitoring
- **dbt** - Data transformation
- **PostgreSQL** - Data storage
- **dlt** - Declarative data loading
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM for database operations

## System Architecture

The pipeline follows a three-layer architecture:

### 1. Ingestion Layer

Responsible for collecting and importing data:

- **FastAPI Module**: Provides REST endpoints for importing ward/address data
- **dlthub Module**: Fetches geocoding data from Google Maps Geocode API using dlt
- **Output**: Raw data stored in PostgreSQL `raw` schema

### 2. Orchestration Layer

Manages workflow execution and dependencies:

- **Dagster Assets**: Two primary assets automate the entire pipeline
  - `fetch_geocode_data`: Executes ingestion and loads data to staging
  - `run_dbt_transform`: Executes data transformation models
- **Dependency Management**: Asset 2 automatically depends on Asset 1
- **Monitoring**: Web-based UI for execution tracking and analysis

### 3. Transformation Layer

Consolidates and cleans data:

- **dbt Models**: SQL-based transformations for data consolidation
- **Output**: Clean, analysis-ready data in PostgreSQL `dwh` schema
- **Data Quality**: Automated tests ensure data integrity

## Data Flow

```
Ward Import (FastAPI)
    |
    v
raw.wards (PostgreSQL)
    |
    v
fetch_geocode_data (Dagster Asset 1)
    |
    v
stagging.geocode_results (PostgreSQL)
    |
    v
run_dbt_transform (Dagster Asset 2)
    |
    v
dwh.geocode_consolidated (PostgreSQL)
```

## Database Schema

### Raw Schema

Contains imported address data:

```sql
raw.wards
  - id (Primary Key)
  - name
  - district
  - city
```

### Staging Schema

Contains geocoding results from Google Maps API:

```sql
stagging.geocode_results
stagging.geocode_results__address_components
stagging.geocode_results__types
stagging.geocode_results__navigation_points
```

### DWH Schema

Contains consolidated and cleaned data:

```sql
dwh.geocode_consolidated
  - geocode_results_id
  - formatted_address
  - geometry__location__lat
  - geometry__location__lng
  - address_components_text
  - location_types
  - navigation_points
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL server (version 12+)
- Virtual environment (recommended)

### Quick Start

1. Clone the repository and navigate to the project directory

2. Set up the virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Configure environment variables by editing `.env`:

   ```bash
   POSTGRES_USER=postgres
   POSTGRES_HOST=localhost
   POSTGRES_PASSWORD_PROJECT_CRAWL=your_password
   POSTGRES_PORT_PROJECT_CRAWL=5433
   POSTGRES_DB_PROJECT_CRAWL=gmap_scraper
   key=YOUR_GOOGLE_MAPS_API_KEY
   ```

4. Install dependencies:

   ```bash
   cd orchestration/gmap_scraper
   pip install -e ".[dev]"
   ```

5. Start Dagster UI:

   ```bash
   dagster dev
   ```

6. Open http://localhost:3000 in your browser

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Usage

### Import Ward Data

Use the FastAPI endpoint to import address data:

```bash
curl -X POST http://localhost:8000/wards/import \
  -H "Content-Type: application/json" \
  -d '[{"name": "Ward Name", "district": "District", "city": "City"}]'
```

### Run Pipeline

In the Dagster UI:

1. Navigate to the Assets tab
2. Click the "Materialize all" button
3. Monitor execution in the Runs tab

### Query Results

```sql
SELECT
  geocode_results_id,
  formatted_address,
  geometry__location__lat,
  geometry__location__lng,
  address_components_text
FROM dwh.geocode_consolidated
LIMIT 10;
```

## Configuration

### Environment Variables

All sensitive configuration is managed via `.env` file:

- `POSTGRES_USER`: Database user
- `POSTGRES_HOST`: Database host address
- `POSTGRES_PASSWORD_PROJECT_CRAWL`: Database password
- `POSTGRES_PORT_PROJECT_CRAWL`: Database port
- `POSTGRES_DB_PROJECT_CRAWL`: Database name
- `key`: Google Maps Geocode API key

Do not commit `.env` to version control.

### Dagster Configuration

Dagster configuration is managed in `orchestration/gmap_scraper/`:

- `setup.py`: Python package dependencies
- `definitions.py`: Dagster definitions and asset loading
- `assets.py`: Asset definitions and execution logic

### dbt Configuration

dbt configuration is in `transformations/`:

- `dbt_project.yml`: Project-level settings
- `profiles.yml`: Database connections (auto-generated)
- `models/`: SQL transformation models
- `tests/`: Data quality tests

## Project Components

### Ingestion Module

- **Location**: `ingestion/`
- **Components**: FastAPI REST API, dlt data loader
- **Outputs**: Raw data in PostgreSQL

### Orchestration Module

- **Location**: `orchestration/gmap_scraper/`
- **Type**: Dagster project
- **Features**: Asset-based workflows, dependency management, Web UI
- **Outputs**: Execution logs, run history, lineage visualization

### Transformation Module

- **Location**: `transformations/`
- **Type**: dbt project
- **Models**: SQL-based transformations
- **Outputs**: Clean data warehouse tables

## Troubleshooting

### PostgreSQL Connection Fails

Verify connection parameters in `.env` and ensure PostgreSQL is running:

```bash
psql -h localhost -p 5433 -U postgres -d gmap_scraper
```

### Dagster Not Starting

Ensure all dependencies are installed:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

### dbt Transformation Fails

Check dbt logs in `transformations/logs/` and verify database connection:

```bash
cd transformations
dbt debug
```

## Development

### Running Tests

Unit tests for the orchestration layer:

```bash
cd orchestration/gmap_scraper
pytest gmap_scraper_tests/
```

### Adding New Assets

Define new assets in `orchestration/gmap_scraper/gmap_scraper/assets.py`:

```python
from dagster import asset

@asset
def my_asset(context):
    context.log.info("Processing data")
    return {"result": "data"}
```

### Adding New dbt Models

Create SQL files in `transformations/models/`:

```sql
{{ config(materialized = 'table') }}

SELECT * FROM {{ source('staging', 'table_name') }}
```

## Performance Considerations

- Google Maps API rate limits: Implement batching for large datasets
- Database indexing: Indexes on geocode_results_id, formatted_address, geometry coordinates
- Staging to production: Batch transformations during off-peak hours
- Dagster memory: Monitor asset memory usage for large datasets

## Security Best Practices

- Environment Variables: Never commit `.env` to version control
- API Keys: Rotate Google Maps API key periodically
- Database Credentials: Use strong passwords, rotate regularly
- Access Control: Restrict database access to authorized users
- Logs: Monitor logs for suspicious activity

## Maintenance

### Regular Tasks

- Review Dagster execution logs weekly
- Monitor database growth and optimize queries
- Validate data quality metrics monthly
- Update dependencies quarterly

### Backup Strategy

- PostgreSQL automated backups
- dbt model version control via Git
- Dagster configuration in version control

## Support and Documentation

- Dagster Documentation: https://docs.dagster.io/
- dbt Documentation: https://docs.getdbt.com/
- Google Maps API: https://developers.google.com/maps
- PostgreSQL Documentation: https://www.postgresql.org/docs/

## License

Proprietary - Internal Use Only

## Version

Current Version: 1.0.0
Last Updated: February 2026

## Contributing

For contributions, please follow the existing code structure and run tests before submitting changes.

## Contact

For questions or support, contact the data engineering team.
