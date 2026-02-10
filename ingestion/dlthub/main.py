import dlt
from dlt.sources.rest_api import rest_api_source
import os
from dotenv import load_dotenv
from pathlib import Path
import psycopg2
import logging
from typing import Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

required_vars = [
    'POSTGRES_HOST', 'POSTGRES_DB_PROJECT_CRAWL', 'POSTGRES_USER',
    'POSTGRES_PASSWORD_PROJECT_CRAWL', 'POSTGRES_PORT_PROJECT_CRAWL',
    'GOOGLE_MAPS_API_KEY'
]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing environment variables: {', '.join(missing)}")

db_url = (f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD_PROJECT_CRAWL')}"
          f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT_PROJECT_CRAWL')}"
          f"/{os.getenv('POSTGRES_DB_PROJECT_CRAWL')}")

pipeline = dlt.pipeline(
    pipeline_name="gmap_geocode",
    destination=dlt.destinations.postgres(db_url),
    dataset_name="stagging" 
)


def _get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_DB_PROJECT_CRAWL'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD_PROJECT_CRAWL'),
        port=int(os.getenv('POSTGRES_PORT_PROJECT_CRAWL'))
    )


def _init_ingestion_state_table():
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.ingestion_state (
                key VARCHAR(255) PRIMARY KEY,
                value INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        logger.info("Ingestion state table initialized")
    except Exception as e:
        logger.error(f"Error initializing state table: {str(e)}")
        raise
    finally:
        if conn:
            cur.close()
            conn.close()


def get_last_processed_ward_id() -> int:
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT value FROM raw.ingestion_state WHERE key = 'last_processed_ward_id' LIMIT 1"
        )
        result = cur.fetchone()
        cur.close()
        
        return result[0] if result else 0
    except Exception as e:
        logger.warning(f"Could not retrieve last processed ward ID: {str(e)}, starting from 0")
        return 0
    finally:
        if conn:
            conn.close()


def update_last_processed_ward_id(ward_id: int):
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        
        # UPSERT: Insert or update
        cur.execute("""
            INSERT INTO raw.ingestion_state (key, value, updated_at)
            VALUES ('last_processed_ward_id', %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = %s, updated_at = NOW();
        """, (ward_id, ward_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating last processed ward ID: {str(e)}")
        raise
    finally:
        if conn:
            cur.close()
            conn.close()


def get_unprocessed_wards(batch_size: int = 50) -> list:

    last_id = get_last_processed_ward_id()
    
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        
        # (WHERE id > last_id)
        cur.execute(
            "SELECT id, name FROM raw.wards WHERE id > %s ORDER BY id LIMIT %s",
            (last_id, batch_size)
        )
        wards = cur.fetchall()
        cur.close()
        
        return wards
    except Exception as e:
        logger.error(f"Error fetching unprocessed wards: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()


def geocode_address(address: str) -> dict:
    """Fetch geocode data from Google Maps API"""
    return rest_api_source({
        "client": {"base_url": "https://maps.gtelmaps.vn/api/google/geocode/v1/search"},
        "resources": [{
            "name": "geocode_results",
            "endpoint": {
                "path": "",
                "params": {
                    "address": address,
                    "apikey": os.getenv('GOOGLE_MAPS_API_KEY')
                }
            }
        }]
    })


def run_incremental_geocoding(batch_size: int = 50):

    _init_ingestion_state_table()
    
    total_processed = 0
    total_failed = 0
    
    logger.info("Starting incremental geocoding pipeline")
    logger.info(f"Last processed ward ID: {get_last_processed_ward_id()}")
    
    while True:
        wards = get_unprocessed_wards(batch_size=batch_size)
        
        if not wards:
            logger.info("No more unprocessed wards found")
            break
        
        logger.info(f"Processing batch of {len(wards)} wards")
        
        for ward_id, address_name in wards:
            try:
                logger.info(f"[{ward_id}] Geocoding: {address_name}")
                
                data = geocode_address(address_name)
                load_info = pipeline.run(data)
                
                update_last_processed_ward_id(ward_id)
                total_processed += 1
                
                logger.info(f"[Ward {ward_id}] Completed successfully")
                
            except Exception as e:
                total_failed += 1
                logger.error(f"[Ward {ward_id}] Failed: {str(e)}")
                continue
    
    logger.info("")
    logger.info("Incremental geocoding completed!")
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Total failed: {total_failed}")
    logger.info(f"Last processed ward ID: {get_last_processed_ward_id()}")


if __name__ == "__main__":
    run_incremental_geocoding(batch_size=50)