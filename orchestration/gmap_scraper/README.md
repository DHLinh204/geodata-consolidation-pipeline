# gmap_scraper

Dagster orchestration project for the Geodata Consolidation Pipeline. Automates the data ingestion → transformation workflow for Google Maps geocoding data.

## Workflow Overview

The pipeline consists of 2 automated assets:

1. **fetch_geocode_data** - Ingests geocoding data (with incremental loading)
   - Reads **only NEW addresses** from PostgreSQL `raw.wards` table (not already processed)
   - Calls Google Maps Geocode API via dlt
   - Loads results into `staging.geocode_results`
   - Tracks state internally to avoid reprocessing the same addresses

2. **run_dbt_transform** - Transforms & consolidates data (depends on asset 1)
   - Runs dbt models to consolidate geocoding results
   - Creates `dwh.geocode_consolidated` table
   - Executes dbt tests for data quality

## Getting started

1. Activate virtual environment:

```bash
source ../../.venv/bin/activate
```

2. Install dependencies:

```bash
pip install -e ".[dev]"
```

3. Start Dagster UI:

```bash
dagster dev
```

4. Open http://localhost:3000 in your browser

## Using the Assets

### Manual Run (via Dagster UI)

- Navigate to **Assets** tab
- Click **Materialize** button on any asset or use **Materialize all** to run the full pipeline
- `fetch_geocode_data` must complete first before `run_dbt_transform` can run (dependency enforced)

### Monitor Execution

- View asset lineage and dependencies in the **Lineage** tab
- Check logs and execution details in **Events** tab
- See run history in **Runs** tab

## Incremental Geocoding

The pipeline supports **incremental data loading** - it only geocodes addresses that haven't been processed yet, avoiding redundant API calls.

### How It Works

1. **State Tracking**: dlt maintains internal state tracking the `last_processed_ward_id`
2. **Only New Wards**: Each run queries only wards with `id > last_processed_ward_id`
3. **Batch Processing**: Processes wards in configurable batches (default: 50 per run)
4. **Automatic Resume**: If a run fails, the next run picks up from where it left off

### Manual Geocoding Run

You can also manually trigger geocoding without Dagster:

```bash
# From project root
cd ingestion/dlthub

# Activate venv
source ../../.venv/bin/activate

# Run incremental geocoding
python main.py
```

Output example:

```
============================================================
Starting incremental geocoding pipeline
Last processed ward ID: 150
============================================================
Processing batch of 50 wards
[151] Geocoding: Ward Name Here
✓ [Ward 151] Completed successfully
...
============================================================
Incremental geocoding completed!
Total processed: 50
Total failed: 0
Last processed ward ID: 200
============================================================
```

## Development

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Unit testing

Tests are in the `gmap_scraper_tests` directory and you can run tests using `pytest`:

```bash
pytest gmap_scraper_tests
```

### Schedules and sensors

If you want to enable Dagster [Schedules](https://docs.dagster.io/guides/automate/schedules/) or [Sensors](https://docs.dagster.io/guides/automate/sensors/) for your jobs, the [Dagster Daemon](https://docs.dagster.io/guides/deploy/execution/dagster-daemon) process must be running. This is done automatically when you run `dagster dev`.

Once your Dagster Daemon is running, you can start turning on schedules and sensors for your jobs.

## Deploy on Dagster+

The easiest way to deploy your Dagster project is to use Dagster+.

Check out the [Dagster+ documentation](https://docs.dagster.io/dagster-plus/) to learn more.
