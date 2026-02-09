import subprocess
import os
from pathlib import Path
from dagster import asset, Output, In, AssetExecutionContext


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INGESTION_PATH = PROJECT_ROOT / "ingestion" / "dlthub"
DBT_PROJECT_PATH = PROJECT_ROOT / "transformations"


@asset(description="Fetch geocode data from Google Maps API using dlt")
def fetch_geocode_data(context: AssetExecutionContext) -> Output:

    context.log.info(f"Starting geocode data fetch from {INGESTION_PATH}")
    
    # .env
    env = os.environ.copy()
    env['PYTHONPATH'] = str(INGESTION_PATH)
    
    try:
        result = subprocess.run(
            ["python", str(INGESTION_PATH / "main.py")],
            cwd=str(INGESTION_PATH),
            env=env,
            capture_output=True,
            text=True,
            timeout=600  
        )
        
        if result.returncode != 0:
            context.log.error(f"dlthub script failed:\n{result.stderr}")
            raise RuntimeError(f"Geocode fetch failed: {result.stderr}")
        
        context.log.info(f"Geocode fetch completed:\n{result.stdout}")
        
        return Output(
            value={"status": "completed", "output": result.stdout},
            metadata={
                "stdout": result.stdout,
                "return_code": result.returncode
            }
        )
    
    except subprocess.TimeoutExpired:
        context.log.error("Geocode fetch timed out after 10 minutes")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during geocode fetch: {str(e)}")
        raise


@asset(description="Run dbt transformations", deps=[fetch_geocode_data])
def run_dbt_transform(context: AssetExecutionContext) -> Output:

    context.log.info(f"Starting dbt transformations from {DBT_PROJECT_PATH}")
    
    env = os.environ.copy()
    
    try:
        # run dbt
        result = subprocess.run(
            ["dbt", "run", "--project-dir", str(DBT_PROJECT_PATH)],
            cwd=str(DBT_PROJECT_PATH),
            env=env,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            context.log.error(f"dbt run failed:\n{result.stderr}")
            raise RuntimeError(f"dbt transformation failed: {result.stderr}")
        
        context.log.info(f"dbt transformation completed:\n{result.stdout}")
        
        test_result = subprocess.run(
            ["dbt", "test", "--project-dir", str(DBT_PROJECT_PATH)],
            cwd=str(DBT_PROJECT_PATH),
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        test_output = f"Tests: {test_result.stdout}" if test_result.returncode == 0 else f"Test warnings: {test_result.stderr}"
        context.log.info(test_output)
        
        return Output(
            value={"status": "completed", "output": result.stdout},
            metadata={
                "dbt_run_stdout": result.stdout,
                "dbt_test_output": test_output,
                "return_code": result.returncode
            }
        )
    
    except subprocess.TimeoutExpired:
        context.log.error("dbt transformation timed out after 10 minutes")
        raise
    except Exception as e:
        context.log.error(f"Unexpected error during dbt transformation: {str(e)}")
        raise
