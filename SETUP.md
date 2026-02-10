# Setup and Installation Guide

Complete setup instructions for the Geodata Consolidation Pipeline.

## Table of Contents

1. Prerequisites
2. Initial Setup
3. Environment Configuration
4. Database Setup
5. Dependency Installation
6. Verification
7. Running the Pipeline
8. Troubleshooting

## Prerequisites

Before starting, ensure you have the following installed:

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)
- git (version control)

### System Requirements

- Minimum 4GB RAM
- 10GB free disk space
- Network access to Google Maps API
- PostgreSQL server accessible from your machine

## Initial Setup

### Step 1: Clone or Navigate to Project

If you do not have the project yet:

```bash
git clone <repository_url>
cd geodata-consolidation-pipeline
```

Or navigate to the existing project:

```bash
cd /path/to/geodata-consolidation-pipeline
```

### Step 2: Create Virtual Environment

Python virtual environments isolate project dependencies from system Python:

```bash
python3 -m venv .venv
```

### Step 3: Activate Virtual Environment

On Linux/macOS:

```bash
source .venv/bin/activate
```

On Windows:

```cmd
.venv\Scripts\activate
```

You should see (.venv) appear in your terminal prompt, indicating the virtual environment is active.

## Environment Configuration

### Step 1: Create .env File

The project uses a .env file for configuration. A template file should exist in the repository:

```bash
# Copy the template if it exists
cp .env.example .env

# Or create a new one
touch .env
```

### Step 2: Configure Environment Variables

Edit the .env file with your specific settings:

```bash
nano .env  # or use your preferred editor
```

Add or modify the following variables:

```env
# PostgreSQL Connection Settings
POSTGRES_USER=postgres
POSTGRES_HOST=localhost
POSTGRES_PASSWORD_PROJECT_CRAWL=your_secure_password
POSTGRES_PORT_PROJECT_CRAWL=5433
POSTGRES_DB_PROJECT_CRAWL=gmap_scraper

# Google Maps API Key (for incremental geocoding)
GOOGLE_MAPS_API_KEY=your_google_maps_geocode_api_key
```

### Step 3: Secure .env File

Ensure the .env file is never committed to version control:

```bash
# Verify .env is in .gitignore
grep ".env" .gitignore
```

### Environment Variables Reference

| Variable                        | Purpose                 | Example               |
| ------------------------------- | ----------------------- | --------------------- |
| POSTGRES_USER                   | Database user           | postgres              |
| POSTGRES_HOST                   | Database server address | localhost             |
| POSTGRES_PASSWORD_PROJECT_CRAWL | Database password       | secure_password_123   |
| POSTGRES_PORT_PROJECT_CRAWL     | Database port           | 5433                  |
| POSTGRES_DB_PROJECT_CRAWL       | Database name           | gmap_scraper          |
| GOOGLE_MAPS_API_KEY             | Google Maps API key     | AIzaSyDxxxxxxxxxxxxxx |

## Database Setup

### Step 1: Install PostgreSQL

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

On macOS (using Homebrew):

```bash
brew install postgresql
```

On Windows: Download and install from https://www.postgresql.org/download/windows/

### Step 2: Start PostgreSQL Service

On Linux:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
```

On macOS:

```bash
brew services start postgresql
```

On Windows: PostgreSQL service starts automatically during installation.

### Step 3: Create Database

Connect to PostgreSQL as the default user:

```bash
sudo -u postgres psql
```

Or on systems without sudo:

```bash
psql -U postgres
```

Create the required database:

```sql
CREATE DATABASE gmap_scraper;
```

Exit psql:

```sql
\q
```

### Step 4: Verify Connection

Test the connection with your configured credentials:

```bash
psql -h localhost -p 5433 -U postgres -d gmap_scraper
```

You should see a psql prompt:

```
postgres=#
```

Exit psql by typing `\q`

### Step 5: Create Database Schemas

Once connected to the database, create the required schemas:

```bash
psql -h localhost -p 5433 -U postgres -d gmap_scraper << EOF
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS stagging;
CREATE SCHEMA IF NOT EXISTS dwh;
\q
EOF
```

Verify schemas were created:

```bash
psql -h localhost -p 5433 -U postgres -d gmap_scraper -c "\dn"
```

You should see:

```
List of schemas
-----------+----------
 Name      | Owner
-----------+----------
 dwh       | postgres
 public    | postgres
 raw       | postgres
 stagging  | postgres
(4 rows)
```

## Dependency Installation

### Step 1: Verify Virtual Environment

Make sure the virtual environment is activated:

```bash
which python  # Should show path inside .venv/bin/
```

### Step 2: Install Root Dependencies

From the project root directory:

```bash
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Orchestration Dependencies

Navigate to the orchestration module and install:

```bash
cd orchestration/gmap_scraper
pip install -e ".[dev]"
```

This installs:

- Dagster and related packages
- dlt (data loading tool)
- dbt-core (data transformation)
- PostgreSQL drivers (psycopg2)
- Testing frameworks (pytest)

### Step 4: Install Transformation Dependencies

From the project root:

```bash
cd transformations
pip install dbt-postgres
```

### Step 5: Verify Installation

Test all major packages are installed:

```bash
python -c "import dagster; import dlt; import dbt.version; print('All packages installed successfully')"
```

Expected output:

```
All packages installed successfully
```

### Step 6: Configure dbt Profile

dbt needs a profiles.yml file to know how to connect to the database. Create it:

First, find your dbt profiles directory:

```bash
# On Linux/macOS
echo ~/.dbt

# On Windows
echo %APPDATA%\.dbt
```

Create profiles.yml:

```bash
mkdir -p ~/.dbt/
cat > ~/.dbt/profiles.yml << 'EOF'
geoscrape:
  outputs:
    dev:
      type: postgres
      host: localhost
      user: postgres
      password: your_password_here
      port: 5433
      dbname: gmap_scraper
      schema: dwh
      threads: 4
      keepalives_idle: 0
  target: dev
EOF
```

Replace "your_password_here" with your actual PostgreSQL password.

## Verification

### Step 1: Test PostgreSQL Connection

```bash
psql -h localhost -p 5433 -U postgres -d gmap_scraper -c "SELECT version();"
```

Expected output: PostgreSQL version information

### Step 2: Test Dagster

From orchestration/gmap_scraper directory:

```bash
python -c "from gmap_scraper.definitions import defs; print('Dagster definitions loaded:', len(defs.assets), 'assets')"
```

Expected output:

```
Dagster definitions loaded: 2 assets
```

### Step 3: Test dbt Connection

From transformations directory:

```bash
dbt debug
```

Expected output:

```
Connection test: [OK]
```

### Step 4: Verify Python Environment

```bash
pip list | grep -E "dagster|dbt|dlt|psycopg2"
```

This should show installed versions of major packages.

## Running the Pipeline

### Step 1: Start Dagster Development Server

Navigate to orchestration directory:

```bash
cd orchestration/gmap_scraper
```

Start the development server:

```bash
dagster dev
```

Expected output:

```
Watching for changes...
Workspace loaded
Started Dagster UI at http://localhost:3000
```

### Step 2: Open Dagster UI

Open your web browser and navigate to:

```
http://localhost:3000
```

### Step 3: Import Test Data (Optional)

In a new terminal, with virtual environment activated:

```bash
curl -X POST http://localhost:8000/wards/import \
  -H "Content-Type: application/json" \
  -d '[{"name": "Test Ward", "district": "Test District", "city": "Test City"}]'
```

### Step 4: Run Pipeline

In the Dagster UI:

1. Navigate to the Assets tab
2. Click the "Materialize" button
3. Select "Materialize all"
4. Monitor execution in the Runs tab

### Step 5: Verify Results

Query the results in PostgreSQL:

```bash
psql -h localhost -p 5433 -U postgres -d gmap_scraper << EOF
SELECT COUNT(*) as total_records FROM dwh.geocode_consolidated;
SELECT * FROM dwh.geocode_consolidated LIMIT 5;
\q
EOF
```

## Troubleshooting

### Issue: Python version incompatible

Error message: "Python 3.8+ required"

Solution: Check Python version:

```bash
python3 --version
```

If you have an older version, install Python 3.8 or later from https://www.python.org/

### Issue: PostgreSQL Connection Refused

Error message: "could not translate host name postgres"

Solutions:

1. Verify PostgreSQL is running:

   ```bash
   pg_isready -h localhost -p 5433
   ```

2. Check database credentials in .env file

3. Ensure PostgreSQL is listening on the configured port:

   ```bash
   sudo netstat -lt | grep 5433
   ```

4. Restart PostgreSQL service:
   ```bash
   sudo systemctl restart postgresql
   ```

### Issue: "Module not found" errors

Error: "ModuleNotFoundError: No module named 'dagster'"

Solutions:

1. Ensure virtual environment is activated:

   ```bash
   which python  # Should show .venv path
   ```

2. Reinstall dependencies:

   ```bash
   cd orchestration/gmap_scraper
   pip install -e ".[dev]"
   ```

3. Check pip list for installed packages:
   ```bash
   pip list | grep dagster
   ```

### Issue: dbt debug fails

Error: "Connection test: ERROR"

Solutions:

1. Verify dbt profiles.yml exists and is correctly configured:

   ```bash
   cat ~/.dbt/profiles.yml
   ```

2. Test PostgreSQL connection directly:

   ```bash
   psql -h localhost -p 5433 -U postgres -d gmap_scraper
   ```

3. Check database credentials match PostgreSQL configuration

### Issue: Dagster assets not loading

Error: "No assets found"

Solutions:

1. Verify assets.py file exists:

   ```bash
   ls orchestration/gmap_scraper/gmap_scraper/assets.py
   ```

2. Check for Python syntax errors:

   ```bash
   python -m py_compile orchestration/gmap_scraper/gmap_scraper/assets.py
   ```

3. Restart Dagster UI and refresh browser

### Issue: Google Maps API key invalid

Error: "Invalid API key"

Solutions:

1. Verify API key is set in .env:

   ```bash
   grep "^key=" .env
   ```

2. Test API key validity:

   ```bash
   curl "https://maps.gtelmaps.vn/api/google/geocode/v1/search?address=Berlin&apikey=YOUR_KEY"
   ```

3. Check API key has geocoding enabled in Google Cloud Console

4. Verify rate limits have not been exceeded

### Issue: Disk space full

Error: "No space left on device"

Solutions:

1. Check available disk space:

   ```bash
   df -h
   ```

2. Clean unused artifacts:

   ```bash
   rm -rf orchestration/gmap_scraper/.dagster
   rm -rf transformations/target
   rm -rf orchestration/gmap_scraper/build
   ```

3. Rotate or archive old logs:
   ```bash
   find logs/ -type f -name "*.log" -mtime +30 -delete
   ```

## Next Steps

After successful setup:

1. Import sample address data via FastAPI endpoint
2. Run the pipeline in Dagster
3. Query results in PostgreSQL
4. Customize assets and models for your use case
5. Set up monitoring and alerting

## Additional Resources

- Dagster Documentation: https://docs.dagster.io/
- dbt Documentation: https://docs.getdbt.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Python Virtual Environments: https://docs.python.org/3/tutorial/venv.html

## Getting Help

If you encounter issues not covered in this guide:

1. Check the logs in the logs/ directory
2. Review Dagster UI event logs
3. Check dbt compilation logs in transformations/target/compiled
4. Enable debug logging for more detailed information

## Version Information

- Created: February 2026
- Tested with: Python 3.8-3.12, PostgreSQL 12-14, Dagster 1.5+, dbt 1.4+

## Maintenance

Regular maintenance tasks:

- Review and rotate API keys quarterly
- Update dependencies monthly
- Archive logs monthly
- Monitor database growth and optimize as needed
- Test backup and recovery procedures quarterly
